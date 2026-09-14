#!/usr/bin/env python3
"""BTC-FEE-PRESSURE-001 V0.4 boundary-normalization source gate. No market outcomes."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import sys

LAB = "BTC-FEE-PRESSURE-001"
GATE = "BFP-SOURCE-REMEDIATION-V0.4"
SOURCE = "https://mempool.space"
SOURCE_RUN_ID = "34880810011"
SOURCE_HEAD = "41fbbd23bbf0de3bc39965c9532c57febacb4a53"
START_TS = 1609459200
END_TS = 1735689599
START_DAY = dt.date(2021, 1, 1)
END_DAY = dt.date(2024, 12, 31)
SHARD_COUNT = 4
ROOT = pathlib.Path(os.environ.get("BFP_V03_CHUNKS_ROOT", "v03_chunks"))
OUT = pathlib.Path(os.environ.get("BFP_OUT", "btc_fee_pressure_source_remediation_v04_final"))
OUT.mkdir(parents=True, exist_ok=True)

verdict = None
failures = []
manifest_paths = sorted(ROOT.rglob("chunk_manifest.json"))
manifests = []

if len(manifest_paths) != SHARD_COUNT:
    verdict = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    failures.append({"reason": "expected_four_chunk_manifests", "found": len(manifest_paths)})

for mp in manifest_paths:
    try:
        m = json.loads(mp.read_text())
        m["_path"] = str(mp)
        manifests.append(m)
    except Exception as e:
        verdict = verdict or "DATA_FAILURE"
        failures.append({"reason": "manifest_decode", "path": str(mp), "type": type(e).__name__, "message": str(e)})

# Freeze lineage to the exact V0.3 source run/artifacts.
idxs = sorted(m.get("shard_index") for m in manifests if isinstance(m.get("shard_index"), int))
if idxs != list(range(SHARD_COUNT)):
    verdict = verdict or "PROVENANCE_FAILURE"
    failures.append({"reason": "shard_identity", "observed": idxs})

for m in manifests:
    if m.get("lab") != LAB:
        verdict = verdict or "PROVENANCE_FAILURE"
        failures.append({"reason": "lab_lineage", "value": m.get("lab")})
    if m.get("gate") != "BFP-SOURCE-REMEDIATION-V0.3":
        verdict = verdict or "PROVENANCE_FAILURE"
        failures.append({"reason": "gate_lineage", "value": m.get("gate")})
    if str(m.get("run_id")) != SOURCE_RUN_ID:
        verdict = verdict or "PROVENANCE_FAILURE"
        failures.append({"reason": "run_lineage", "value": m.get("run_id")})
    if m.get("source") != SOURCE:
        verdict = verdict or "PROVENANCE_FAILURE"
        failures.append({"reason": "source_lineage", "value": m.get("source")})
    if m.get("start_timestamp") != START_TS or m.get("end_timestamp") != END_TS:
        verdict = verdict or "PROVENANCE_FAILURE"
        failures.append({"reason": "timestamp_window_lineage", "shard": m.get("shard_index")})
    if m.get("verdict") != "CHUNK_PASS":
        verdict = verdict or "PROVENANCE_FAILURE"
        failures.append({"reason": "source_chunk_not_pass", "shard": m.get("shard_index"), "value": m.get("verdict")})
    fw = m.get("firewall") or {}
    if any(bool(fw.get(k)) for k in (
        "btc_price_values_opened", "eth_price_values_opened", "returns_computed", "pnl_computed",
        "performance_statistics_computed", "access_2025", "access_2026", "live_trading",
        "exchange_mutation", "discovery"
    )):
        verdict = verdict or "PROVENANCE_FAILURE"
        failures.append({"reason": "source_firewall_violation", "shard": m.get("shard_index")})

starts = {m.get("start_height") for m in manifests}
ends = {m.get("end_height") for m in manifests}
if len(starts) != 1 or len(ends) != 1 or None in starts or None in ends:
    verdict = verdict or "PROVENANCE_FAILURE"
    failures.append({"reason": "raw_height_bounds_inconsistent", "starts": sorted(str(x) for x in starts), "ends": sorted(str(x) for x in ends)})
raw_start_h = next(iter(starts)) if len(starts) == 1 else None
raw_end_h = next(iter(ends)) if len(ends) == 1 else None

pairs = sorted((m.get("shard_index"), pathlib.Path(m["_path"])) for m in manifests if isinstance(m.get("shard_index"), int))
requested = []
requested_sources = []
for idx, mp in pairs:
    rp = mp.parent / "requested_heights.json"
    if not rp.exists():
        verdict = verdict or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failures.append({"reason": "missing_requested_heights", "shard": idx})
        continue
    try:
        vals = json.loads(rp.read_text())
        if not isinstance(vals, list) or not all(isinstance(x, int) for x in vals):
            raise ValueError("requested_heights_schema")
        requested.extend(vals)
        requested_sources.append({"shard_index": idx, "count": len(vals), "sha256": hashlib.sha256(rp.read_bytes()).hexdigest()})
    except Exception as e:
        verdict = verdict or "DATA_FAILURE"
        failures.append({"reason": "requested_heights_decode", "shard": idx, "message": str(e)})

expected = list(range(raw_end_h, raw_start_h - 1, -10)) if isinstance(raw_start_h, int) and isinstance(raw_end_h, int) else []
if requested != expected:
    verdict = verdict or "PROVENANCE_FAILURE"
    failures.append({"reason": "requested_height_sequence_mismatch", "observed": len(requested), "expected": len(expected)})

blocks = {}
conflicts = []
duplicate_same_hash = 0
malformed = []
for idx, mp in pairs:
    bp = mp.parent / "block_index.jsonl"
    if not bp.exists():
        verdict = verdict or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failures.append({"reason": "missing_block_index", "shard": idx})
        continue
    for line_no, line in enumerate(bp.read_text().splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
            h = row.get("height")
            bid = row.get("id")
            ts = row.get("timestamp")
            fees = row.get("totalFees")
            if not isinstance(h, int) or not isinstance(bid, str) or len(bid) != 64 or not isinstance(ts, int):
                raise ValueError("identity_or_timestamp")
            f = float(fees)
            if not math.isfinite(f) or f < 0:
                raise ValueError("fees")
            row = {"height": h, "id": bid, "timestamp": ts, "totalFees": f}
            prev = blocks.get(h)
            if prev is not None:
                if prev["id"] != bid:
                    conflicts.append({"height": h, "a": prev["id"], "b": bid})
                else:
                    duplicate_same_hash += 1
            else:
                blocks[h] = row
        except Exception as e:
            malformed.append({"shard": idx, "line": line_no, "reason": str(e)})

if conflicts:
    verdict = verdict or "PROVENANCE_FAILURE"
    failures.append({"reason": "hash_conflicts", "count": len(conflicts)})
if malformed:
    verdict = verdict or "DATA_FAILURE"
    failures.append({"reason": "malformed_rows", "count": len(malformed)})

raw_missing_heights = []
if isinstance(raw_start_h, int) and isinstance(raw_end_h, int):
    raw_missing_heights = [h for h in range(raw_start_h, raw_end_h + 1) if h not in blocks]
if raw_missing_heights:
    verdict = verdict or "PROVENANCE_FAILURE"
    failures.append({"reason": "raw_height_coverage", "count": len(raw_missing_heights)})

in_window = {h: row for h, row in blocks.items() if START_TS <= row["timestamp"] <= END_TS}
normalized_start_h = min(in_window) if in_window else None
normalized_end_h = max(in_window) if in_window else None

outside_context = []
illegal_outside = []
for h, row in sorted(blocks.items()):
    if START_TS <= row["timestamp"] <= END_TS:
        continue
    rec = {
        "height": h,
        "timestamp": row["timestamp"],
        "date": dt.datetime.fromtimestamp(row["timestamp"], tz=dt.timezone.utc).date().isoformat(),
    }
    outside_context.append(rec)
    if isinstance(normalized_start_h, int) and isinstance(normalized_end_h, int) and normalized_start_h <= h <= normalized_end_h:
        illegal_outside.append(rec)

if not in_window:
    verdict = verdict or "INSUFFICIENT_SAMPLE"
    failures.append({"reason": "no_in_window_blocks"})
if illegal_outside:
    verdict = verdict or "PROVENANCE_FAILURE"
    failures.append({"reason": "outside_block_inside_normalized_interval", "count": len(illegal_outside)})

normalized_missing_heights = []
if isinstance(normalized_start_h, int) and isinstance(normalized_end_h, int):
    normalized_missing_heights = [h for h in range(normalized_start_h, normalized_end_h + 1) if h not in blocks]
if normalized_missing_heights:
    verdict = verdict or "PROVENANCE_FAILURE"
    failures.append({"reason": "normalized_height_coverage", "count": len(normalized_missing_heights)})

# Aggregate only canonical in-window timestamps.
daily = {}
for h, row in sorted(in_window.items()):
    day = dt.datetime.fromtimestamp(row["timestamp"], tz=dt.timezone.utc).date().isoformat()
    daily[day] = daily.get(day, 0.0) + row["totalFees"]

missing_days = []
d = START_DAY
while d <= END_DAY:
    if d.isoformat() not in daily:
        missing_days.append(d.isoformat())
    d += dt.timedelta(days=1)

if verdict is None:
    if missing_days:
        verdict = "INSUFFICIENT_SAMPLE"
    elif len(daily) < 1400:
        verdict = "INSUFFICIENT_SAMPLE"
    else:
        verdict = "SOURCE_DATA_PASS"

(OUT / "daily_fee_totals.json").write_text(json.dumps(daily, sort_keys=True, separators=(",", ":")) + "\n")
(OUT / "normalized_boundary_context.json").write_text(json.dumps({
    "raw_start_height": raw_start_h,
    "raw_end_height": raw_end_h,
    "normalized_start_height": normalized_start_h,
    "normalized_end_height": normalized_end_h,
    "outside_context": outside_context,
    "illegal_outside": illegal_outside,
}, sort_keys=True, indent=2) + "\n")

manifest = {
    "lab": LAB,
    "gate": GATE,
    "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    "verdict": verdict,
    "source": SOURCE,
    "source_reuse": True,
    "source_run_id": SOURCE_RUN_ID,
    "source_head": SOURCE_HEAD,
    "start_timestamp": START_TS,
    "end_timestamp": END_TS,
    "raw_start_height": raw_start_h,
    "raw_end_height": raw_end_h,
    "normalized_start_height": normalized_start_h,
    "normalized_end_height": normalized_end_h,
    "chunk_count": len(manifests),
    "requested_height_count": len(requested),
    "expected_request_height_count": len(expected),
    "requested_sources": requested_sources,
    "blocks": len(blocks),
    "in_window_blocks": len(in_window),
    "duplicate_same_hash_count": duplicate_same_hash,
    "hash_conflict_count": len(conflicts),
    "hash_conflicts": conflicts[:100],
    "raw_missing_height_count": len(raw_missing_heights),
    "raw_missing_height_sample": raw_missing_heights[:100],
    "normalized_missing_height_count": len(normalized_missing_heights),
    "normalized_missing_height_sample": normalized_missing_heights[:100],
    "outside_context_count": len(outside_context),
    "outside_context": outside_context[:100],
    "illegal_outside_count": len(illegal_outside),
    "illegal_outside": illegal_outside[:100],
    "malformed_count": len(malformed),
    "malformed": malformed[:100],
    "daily_observations": len(daily),
    "first_day": min(daily, default=None),
    "last_day": max(daily, default=None),
    "missing_day_count": len(missing_days),
    "missing_days": missing_days,
    "failures": failures,
    "firewall": {
        "btc_price_values_opened": False,
        "eth_price_values_opened": False,
        "returns_computed": False,
        "pnl_computed": False,
        "performance_statistics_computed": False,
        "access_2025": False,
        "access_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
        "discovery": False,
    },
}
mb = json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
(OUT / "manifest.json").write_bytes(mb)
(OUT / "manifest.sha256").write_text(hashlib.sha256(mb).hexdigest() + "  manifest.json\n")
(OUT / "verdict.txt").write_text(verdict + "\n")
print(json.dumps({
    k: manifest[k] for k in (
        "run_id", "verdict", "raw_start_height", "raw_end_height",
        "normalized_start_height", "normalized_end_height", "blocks", "in_window_blocks",
        "raw_missing_height_count", "normalized_missing_height_count", "outside_context_count",
        "illegal_outside_count", "malformed_count", "daily_observations", "first_day",
        "last_day", "missing_day_count"
    )
}, sort_keys=True))
print("MANIFEST_SHA256", hashlib.sha256(mb).hexdigest())
sys.exit(0)

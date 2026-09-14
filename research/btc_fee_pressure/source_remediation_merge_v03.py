#!/usr/bin/env python3
"""BTC-FEE-PRESSURE-001 V0.3 source-only shard merge gate. No market outcomes."""
from __future__ import annotations
import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import sys

LAB = "BTC-FEE-PRESSURE-001"
GATE = "BFP-SOURCE-REMEDIATION-V0.3"
START_TS = 1609459200
END_TS = 1735689599
START_DAY = dt.date(2021, 1, 1)
END_DAY = dt.date(2024, 12, 31)
SHARD_COUNT = 4
ROOT = pathlib.Path(os.environ.get("BFP_CHUNKS_ROOT", "v03_chunks"))
OUT = pathlib.Path(os.environ.get("BFP_OUT", "btc_fee_pressure_source_remediation_v03_final"))
OUT.mkdir(parents=True, exist_ok=True)

manifest_paths = sorted(ROOT.rglob("chunk_manifest.json"))
manifests = []
verdict = None
transport = []
if len(manifest_paths) != SHARD_COUNT:
    verdict = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    transport.append({"reason": "expected_four_chunk_manifests", "found": len(manifest_paths)})

for mp in manifest_paths:
    try:
        obj = json.loads(mp.read_text())
        obj["_path"] = str(mp)
        manifests.append(obj)
    except Exception as e:
        verdict = verdict or "DATA_FAILURE"
        transport.append({"path": str(mp), "reason": type(e).__name__, "message": str(e)})

idxs = sorted(m.get("shard_index") for m in manifests if isinstance(m.get("shard_index"), int))
if idxs != list(range(SHARD_COUNT)):
    verdict = verdict or "PROVENANCE_FAILURE"
failures = [m.get("verdict") for m in manifests if m.get("verdict") != "CHUNK_PASS"]
if failures:
    if any(v == "SOURCE_AUTH_BLOCKED" for v in failures):
        verdict = verdict or "SOURCE_AUTH_BLOCKED"
    elif any(v == "SOURCE_ACQUISITION_TECHNICAL_FAILURE" for v in failures):
        verdict = verdict or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    elif any(v == "PROVENANCE_FAILURE" for v in failures):
        verdict = verdict or "PROVENANCE_FAILURE"
    else:
        verdict = verdict or "DATA_FAILURE"

starts = {m.get("start_height") for m in manifests}
ends = {m.get("end_height") for m in manifests}
if len(starts) != 1 or len(ends) != 1 or None in starts or None in ends:
    verdict = verdict or "PROVENANCE_FAILURE"
start_h = next(iter(starts)) if len(starts) == 1 else None
end_h = next(iter(ends)) if len(ends) == 1 else None

pairs = sorted((m["shard_index"], pathlib.Path(m["_path"])) for m in manifests if isinstance(m.get("shard_index"), int))
requested = []
requested_sources = []
for idx, mp in pairs:
    rp = mp.parent / "requested_heights.json"
    if not rp.exists():
        verdict = verdict or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        transport.append({"reason": "missing_requested_heights", "path": str(rp)})
        continue
    vals = json.loads(rp.read_text())
    requested.extend(vals)
    requested_sources.append({"shard_index": idx, "count": len(vals), "sha256": hashlib.sha256(rp.read_bytes()).hexdigest()})

expected = list(range(end_h, start_h - 1, -10)) if isinstance(start_h, int) and isinstance(end_h, int) else []
if requested != expected:
    verdict = verdict or "PROVENANCE_FAILURE"

blocks = {}
conflicts = []
duplicate_same_hash = 0
for idx, mp in pairs:
    bp = mp.parent / "block_index.jsonl"
    if not bp.exists():
        verdict = verdict or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        transport.append({"reason": "missing_block_index", "path": str(bp)})
        continue
    for line in bp.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        h = row.get("height")
        if not isinstance(h, int):
            verdict = verdict or "DATA_FAILURE"
            continue
        prev = blocks.get(h)
        if prev is not None:
            if prev.get("id") != row.get("id"):
                conflicts.append({"height": h, "a": prev.get("id"), "b": row.get("id")})
            else:
                duplicate_same_hash += 1
        else:
            blocks[h] = row
if conflicts:
    verdict = verdict or "PROVENANCE_FAILURE"

missing_heights = []
malformed = []
outside = []
daily = {}
if isinstance(start_h, int) and isinstance(end_h, int):
    missing_heights = [h for h in range(start_h, end_h + 1) if h not in blocks]
for h, row in sorted(blocks.items()):
    try:
        if row.get("height") != h or not isinstance(row.get("id"), str) or len(row["id"]) != 64:
            raise ValueError("identity")
        stamp = dt.datetime.fromtimestamp(int(row["timestamp"]), tz=dt.timezone.utc)
        day = stamp.date()
        if not (START_DAY <= day <= END_DAY):
            outside.append({"height": h, "date": day.isoformat()})
            continue
        fees = float(row["totalFees"])
        if not math.isfinite(fees) or fees < 0:
            raise ValueError("fees")
        daily[day.isoformat()] = daily.get(day.isoformat(), 0.0) + fees
    except Exception as e:
        malformed.append({"height": h, "reason": str(e)})

missing_days = []
d = START_DAY
while d <= END_DAY:
    if d.isoformat() not in daily:
        missing_days.append(d.isoformat())
    d += dt.timedelta(days=1)

if verdict is None:
    if outside or missing_heights:
        verdict = "PROVENANCE_FAILURE"
    elif malformed:
        verdict = "DATA_FAILURE"
    elif len(daily) < 1400:
        verdict = "INSUFFICIENT_SAMPLE"
    else:
        verdict = "SOURCE_DATA_PASS"

(OUT / "daily_fee_totals.json").write_text(json.dumps(daily, sort_keys=True, separators=(",", ":")) + "\n")
(OUT / "chunk_manifest_sha256.json").write_text(json.dumps({
    str(m["shard_index"]): hashlib.sha256(pathlib.Path(m["_path"]).read_bytes()).hexdigest()
    for m in manifests if isinstance(m.get("shard_index"), int)
}, sort_keys=True, indent=2) + "\n")

manifest = {
    "lab": LAB, "gate": GATE, "run_id": os.environ.get("GITHUB_RUN_ID", "local"),
    "verdict": verdict, "source": "https://mempool.space",
    "start_timestamp": START_TS, "end_timestamp": END_TS,
    "start_height": start_h, "end_height": end_h,
    "chunk_count": len(manifests), "requested_height_count": len(requested),
    "expected_request_height_count": len(expected), "requested_sources": requested_sources,
    "blocks": len(blocks), "duplicate_same_hash_count": duplicate_same_hash,
    "hash_conflict_count": len(conflicts), "hash_conflicts": conflicts[:100],
    "missing_height_count": len(missing_heights), "missing_height_sample": missing_heights[:100],
    "daily_observations": len(daily), "first_day": min(daily, default=None), "last_day": max(daily, default=None),
    "missing_day_count": len(missing_days), "missing_days": missing_days,
    "malformed_count": len(malformed), "malformed": malformed[:100],
    "outside_count": len(outside), "outside": outside[:100],
    "transport_failures": transport,
    "firewall": {
        "btc_price_values_opened": False, "eth_price_values_opened": False,
        "returns_computed": False, "pnl_computed": False,
        "performance_statistics_computed": False, "access_2025": False,
        "access_2026": False, "live_trading": False,
        "exchange_mutation": False, "discovery": False
    }
}
mb = json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
(OUT / "manifest.json").write_bytes(mb)
(OUT / "manifest.sha256").write_text(hashlib.sha256(mb).hexdigest() + "  manifest.json\n")
(OUT / "verdict.txt").write_text(verdict + "\n")
print(json.dumps({k: manifest[k] for k in (
    "run_id", "verdict", "start_height", "end_height", "chunk_count",
    "requested_height_count", "expected_request_height_count", "blocks",
    "missing_height_count", "daily_observations", "first_day", "last_day",
    "missing_day_count", "malformed_count", "outside_count"
)}, sort_keys=True))
print("MANIFEST_SHA256", hashlib.sha256(mb).hexdigest())
sys.exit(0)

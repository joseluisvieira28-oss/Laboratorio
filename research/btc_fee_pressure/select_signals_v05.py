#!/usr/bin/env python3
"""Outcome-blind selector for BTC-FEE-PRESSURE-001 Discovery V0.5."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import pathlib
import sys

LAB = "BTC-FEE-PRESSURE-001"
MVE = "BFP-TOTALFEES-7D-001"
SOURCE_RUN = "34886378068"
SOURCE_HEAD = "945b57823fb91e767fd42c79ed2d362fce85d19f"
SOURCE_MANIFEST_SHA256 = "4af2e98ac18aaf28686f7f80580ece5a7a34461f20e1955ad562e0a7328c9093"
START_DAY = dt.date(2021, 1, 1)
END_DAY = dt.date(2024, 12, 31)
LATEST_SIGNAL = dt.date(2024, 12, 23)
LOOKBACK = 90
P = 0.80
ROOT = pathlib.Path(os.environ.get("BFP_SOURCE_ROOT", "source_v04"))
OUT = pathlib.Path(os.environ.get("BFP_SELECTION_OUT", "bfp_v05_selection"))
OUT.mkdir(parents=True, exist_ok=True)


def fail(kind: str, reason: str):
    (OUT / "preoutcome_status.json").write_text(json.dumps({
        "lab": LAB, "mve": MVE, "status": kind, "reason": reason,
        "market_outcomes_opened": False, "access_2025": False, "access_2026": False,
    }, sort_keys=True, indent=2) + "\n")
    print(json.dumps({"status": kind, "reason": reason}, sort_keys=True))
    raise SystemExit(0)


def type7(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("empty percentile input")
    xs = sorted(values)
    h = (len(xs) - 1) * p
    lo = math.floor(h)
    hi = math.ceil(h)
    if lo == hi:
        return float(xs[lo])
    w = h - lo
    return float(xs[lo] * (1.0 - w) + xs[hi] * w)


manifests = list(ROOT.rglob("manifest.json"))
# The source artifact contains exactly one V0.4 manifest. Ignore no other JSON by filename.
source_manifest = None
source_manifest_path = None
for pth in manifests:
    try:
        obj = json.loads(pth.read_text())
    except Exception:
        continue
    if obj.get("lab") == LAB and obj.get("gate") == "BFP-SOURCE-REMEDIATION-V0.4":
        if source_manifest is not None:
            fail("PROVENANCE_FAILURE", "multiple_v04_source_manifests")
        source_manifest = obj
        source_manifest_path = pth

if source_manifest is None or source_manifest_path is None:
    fail("TECHNICAL_FAILURE_PREOUTCOME", "v04_source_manifest_not_found")
actual_manifest_sha = hashlib.sha256(source_manifest_path.read_bytes()).hexdigest()
if actual_manifest_sha != SOURCE_MANIFEST_SHA256:
    fail("PROVENANCE_FAILURE", f"source_manifest_sha_mismatch:{actual_manifest_sha}")

checks = {
    "verdict": source_manifest.get("verdict") == "SOURCE_DATA_PASS",
    "source_run": str(source_manifest.get("run_id")) == SOURCE_RUN,
    "source_head": source_manifest.get("source_head") == "41fbbd23bbf0de3bc39965c9532c57febacb4a53",
    "coverage": source_manifest.get("daily_observations") == 1461,
    "first_day": source_manifest.get("first_day") == "2021-01-01",
    "last_day": source_manifest.get("last_day") == "2024-12-31",
    "missing_days": source_manifest.get("missing_day_count") == 0,
    "missing_heights": source_manifest.get("normalized_missing_height_count") == 0,
    "illegal_outside": source_manifest.get("illegal_outside_count") == 0,
    "malformed": source_manifest.get("malformed_count") == 0,
}
if not all(checks.values()):
    fail("PROVENANCE_FAILURE", "source_binding_failed:" + json.dumps(checks, sort_keys=True))
fw = source_manifest.get("firewall") or {}
if any(bool(v) for v in fw.values()):
    fail("PROVENANCE_FAILURE", "source_firewall_not_clean")

fee_paths = list(ROOT.rglob("daily_fee_totals.json"))
if len(fee_paths) != 1:
    fail("TECHNICAL_FAILURE_PREOUTCOME", f"daily_fee_totals_count:{len(fee_paths)}")
try:
    raw = json.loads(fee_paths[0].read_text())
except Exception as e:
    fail("DATA_FAILURE", f"fee_json_decode:{type(e).__name__}")

series: list[tuple[dt.date, float]] = []
for k, v in raw.items():
    try:
        d = dt.date.fromisoformat(k)
        x = float(v)
        if not math.isfinite(x) or x < 0:
            raise ValueError("nonfinite_or_negative")
        series.append((d, x))
    except Exception as e:
        fail("DATA_FAILURE", f"fee_row:{k}:{e}")
series.sort()
if len(series) != 1461 or series[0][0] != START_DAY or series[-1][0] != END_DAY:
    fail("DATA_FAILURE", "fee_coverage_mismatch")
for i in range(1, len(series)):
    if series[i][0] != series[i-1][0] + dt.timedelta(days=1):
        fail("DATA_FAILURE", f"noncontiguous_fee_days:{series[i-1][0]}->{series[i][0]}")

candidate_count = 0
suppressed_overlap = 0
accepted = []
last_exit: dt.date | None = None
for i in range(LOOKBACK, len(series)):
    day, fee = series[i]
    if day > LATEST_SIGNAL:
        break
    prior = [series[j][1] for j in range(i - LOOKBACK, i)]
    if len(prior) != LOOKBACK:
        fail("DATA_FAILURE", "lookback_length")
    threshold = type7(prior, P)
    if fee <= threshold:
        continue
    candidate_count += 1
    entry = day + dt.timedelta(days=1)
    exit_day = day + dt.timedelta(days=8)
    if entry.year >= 2025 or exit_day.year >= 2025 or exit_day > END_DAY:
        fail("PROVENANCE_FAILURE", f"protected_period_candidate:{day}")
    if last_exit is not None and entry < last_exit:
        suppressed_overlap += 1
        continue
    accepted.append({
        "signal_day": day.isoformat(),
        "entry_day": entry.isoformat(),
        "exit_day": exit_day.isoformat(),
        "fee_value": fee,
        "p80_type7_prior90": threshold,
    })
    last_exit = exit_day

selected_bytes = json.dumps(accepted, sort_keys=True, separators=(",", ":")).encode() + b"\n"
selected_sha = hashlib.sha256(selected_bytes).hexdigest()
(OUT / "selected_trades.json").write_bytes(selected_bytes)
(OUT / "selected_trades.sha256").write_text(selected_sha + "  selected_trades.json\n")

manifest = {
    "lab": LAB,
    "mve": MVE,
    "stage": "OUTCOME_BLIND_SELECTION_FROZEN",
    "source_run": SOURCE_RUN,
    "source_tested_head": SOURCE_HEAD,
    "source_manifest_sha256": SOURCE_MANIFEST_SHA256,
    "fee_file_sha256": hashlib.sha256(fee_paths[0].read_bytes()).hexdigest(),
    "lookback_days": LOOKBACK,
    "percentile": P,
    "percentile_method": "Hyndman-Fan Type 7 linear",
    "comparison": "fee_t > p80(prior90), strict",
    "direction": "LONG",
    "entry_offset_days": 1,
    "exit_offset_days": 8,
    "hold_calendar_days": 7,
    "overlap_rule": "accept iff entry >= previous accepted exit",
    "latest_signal_day": LATEST_SIGNAL.isoformat(),
    "candidate_signal_count": candidate_count,
    "accepted_trade_count": len(accepted),
    "suppressed_overlap_count": suppressed_overlap,
    "first_accepted_signal": accepted[0]["signal_day"] if accepted else None,
    "last_accepted_signal": accepted[-1]["signal_day"] if accepted else None,
    "selected_trades_sha256": selected_sha,
    "market_outcomes_opened": False,
    "btc_price_values_opened": False,
    "returns_computed": False,
    "pnl_computed": False,
    "access_2025": False,
    "access_2026": False,
    "live_trading": False,
    "exchange_mutation": False,
}
mb = json.dumps(manifest, sort_keys=True, indent=2).encode() + b"\n"
(OUT / "selection_manifest.json").write_bytes(mb)
(OUT / "selection_manifest.sha256").write_text(hashlib.sha256(mb).hexdigest() + "  selection_manifest.json\n")
(OUT / "preoutcome_status.json").write_text(json.dumps({
    "status": "SELECTION_PASS", "accepted_trade_count": len(accepted),
    "selected_trades_sha256": selected_sha, "market_outcomes_opened": False,
}, sort_keys=True, indent=2) + "\n")
print(json.dumps({
    "status": "SELECTION_PASS", "candidate_signal_count": candidate_count,
    "accepted_trade_count": len(accepted), "suppressed_overlap_count": suppressed_overlap,
    "selected_trades_sha256": selected_sha,
}, sort_keys=True))
sys.exit(0)

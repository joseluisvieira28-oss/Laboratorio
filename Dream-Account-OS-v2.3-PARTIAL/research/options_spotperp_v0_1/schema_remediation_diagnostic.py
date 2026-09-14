#!/usr/bin/env python3
"""OPTIONS-SPOTPERP-001 outcome-blind schema remediation diagnostic.

Reads only source-audit raw pages/receipts from the frozen 2021-04-01..2024-12-31
window. It classifies invalid `iv` and `mark_price` observations and measures whether
they occur inside the frozen structural eligibility envelope. It computes NO skew,
NO signal aggregation, NO forward return, NO PnL, and does not access 2025/2026.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

UTC = dt.timezone.utc
START = dt.datetime(2021, 4, 1, tzinfo=UTC)
END = dt.datetime(2025, 1, 1, tzinfo=UTC)


def parse_instrument(name: str) -> tuple[dt.datetime, float, str]:
    parts = name.split("-")
    if len(parts) != 4 or parts[0] != "BTC" or parts[3] not in {"C", "P"}:
        raise ValueError(name)
    expiry = dt.datetime.strptime(parts[1].upper(), "%d%b%y").replace(hour=8, tzinfo=UTC)
    strike = float(parts[2])
    if not math.isfinite(strike) or strike <= 0:
        raise ValueError(name)
    return expiry, strike, parts[3]


def classify_numeric(row: dict[str, Any], field: str) -> str:
    if field not in row:
        return "missing"
    value = row.get(field)
    if value is None:
        return "null"
    if value == "":
        return "empty"
    try:
        x = float(value)
    except Exception:
        return "non_numeric"
    if not math.isfinite(x):
        return "non_finite"
    if x == 0:
        return "zero"
    if x < 0:
        return "negative"
    return "valid_positive"


def structurally_eligible(row: dict[str, Any], ts: int) -> bool:
    try:
        expiry, strike, side = parse_instrument(str(row.get("instrument_name", "")))
        index_price = float(row["index_price"])
        if not math.isfinite(index_price) or index_price <= 0:
            return False
        t = dt.datetime.fromtimestamp(ts / 1000, tz=UTC)
        dte = (expiry - t).total_seconds() / 86400.0
        if dte < 30 or dte > 120:
            return False
        ratio = strike / index_price
        if side == "C":
            return 1.05 <= ratio <= 1.20
        return 0.80 <= ratio <= 0.95
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    root = Path(args.root)

    manifest = json.loads((root / "source_manifest.json").read_text(encoding="utf-8"))
    report = json.loads((root / "source_audit_report.json").read_text(encoding="utf-8"))

    if manifest.get("holdout_accessed") is not False or manifest.get("locked_2026_accessed") is not False:
        raise SystemExit("FAIL-CLOSED: locked years were accessed")
    if report.get("outcome_metrics_computed") is not False:
        raise SystemExit("FAIL-CLOSED: outcome metrics were computed")

    counts = {
        "iv": Counter(),
        "mark_price": Counter(),
        "iv_structurally_eligible": Counter(),
        "mark_price_structurally_eligible": Counter(),
    }
    totals = Counter()

    for entry in manifest.get("raw_pages", []):
        p = root / "raw" / entry["page"]
        obj = json.loads(gzip.decompress(p.read_bytes()).decode("utf-8"))
        trades = obj.get("result", {}).get("trades", [])
        for row in trades:
            totals["trades"] += 1
            ts = int(row["timestamp"])
            if ts < int(START.timestamp() * 1000) or ts >= int(END.timestamp() * 1000):
                raise SystemExit("FAIL-CLOSED: timestamp outside frozen discovery window")
            eligible = structurally_eligible(row, ts)
            if eligible:
                totals["structurally_eligible"] += 1
            for field in ("iv", "mark_price"):
                cls = classify_numeric(row, field)
                counts[field][cls] += 1
                if eligible:
                    counts[f"{field}_structurally_eligible"][cls] += 1

    audit = report.get("audit", {})
    iv_bad = totals["trades"] - counts["iv"]["valid_positive"]
    mark_bad = totals["trades"] - counts["mark_price"]["valid_positive"]
    iv_bad_eligible = totals["structurally_eligible"] - counts["iv_structurally_eligible"]["valid_positive"]
    mark_bad_eligible = totals["structurally_eligible"] - counts["mark_price_structurally_eligible"]["valid_positive"]

    receipt = {
        "lab_id": "OPTIONS-SPOTPERP-001",
        "version": "V0.1",
        "stage": "SOURCE_SCHEMA_REMEDIATION_DIAGNOSTIC",
        "status": "DIAGNOSTIC_COMPLETE",
        "frozen_window": {"start": "2021-04-01", "end": "2024-12-31"},
        "governance": {
            "skew_values_computed": False,
            "signals_computed": False,
            "forward_returns_computed": False,
            "pnl_computed": False,
            "holdout_2025_accessed": False,
            "year_2026_accessed": False,
        },
        "totals": dict(totals),
        "field_classification": {k: dict(v) for k, v in counts.items()},
        "invalid_summary": {
            "iv_invalid_all": iv_bad,
            "iv_invalid_structurally_eligible": iv_bad_eligible,
            "mark_price_invalid_all": mark_bad,
            "mark_price_invalid_structurally_eligible": mark_bad_eligible,
        },
        "source_audit_context": {
            "source_status": report.get("status"),
            "valid_signal_coverage_days": audit.get("valid_signal_coverage_days"),
            "min_required_valid_days": audit.get("min_required_valid_days"),
            "eligible_trade_count_reported": audit.get("eligible_trade_count"),
            "missing_or_invalid_iv_after_parse_reported": audit.get("missing_or_invalid_iv_after_parse"),
        },
        "interpretation_flags": {
            "mark_price_not_in_frozen_signal_definition": True,
            "mark_price_hard_zero_rule_is_gate_scope_mismatch_candidate": mark_bad > 0,
            "iv_hard_zero_rule_is_gate_scope_mismatch_candidate": (
                iv_bad > 0
                and report.get("status") == "SOURCE_AUDIT_PASS"
                and int(audit.get("valid_signal_coverage_days") or 0) >= int(audit.get("min_required_valid_days") or 10**9)
            ),
        },
        "terminal_classification": "GATE_IMPLEMENTATION_DEFECT_CANDIDATE",
        "next_step": "Independent pre-outcome review of gate semantics. Do not open Discovery until a frozen amendment is explicitly authorized.",
    }

    out = root / "schema_remediation_diagnostic_receipt.json"
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

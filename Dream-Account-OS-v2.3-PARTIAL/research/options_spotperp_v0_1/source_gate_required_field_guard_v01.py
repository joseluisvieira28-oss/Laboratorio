#!/usr/bin/env python3
"""OPTIONS-SPOTPERP-001 — outcome-blind required-field presence guard V0.1.

This guard resolves a source-audit implementation detail before any Discovery
outcome is opened. The canonical authority lists timestamp, instrument_name,
trade IV, index_price, mark_price and taker direction as required public trade
fields. The operational checklist also requires trade_id for duplicate auditing.
Trade amount/contracts are optional when present.

The guard verifies raw-page hashes from the frozen full acquisition and requires
all mandatory FIELD KEYS to be present on every raw trade row. It deliberately
does not require mark_price > 0 because mark_price is not a frozen signal input;
non-finite/non-positive mark values are counted as diagnostics. IV/index value
eligibility remains governed by the frozen source/eligibility rules.

NO skew, signal, return, PnL, regression or 2025/2026 data is computed/accessed.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
from pathlib import Path
from typing import Any

import source_audit_gate as base

REQUIRED_FIELD_KEYS = (
    "timestamp",
    "trade_id",
    "instrument_name",
    "iv",
    "index_price",
    "mark_price",
    "direction",
)


def audit_required_fields(root: Path) -> dict[str, Any]:
    manifest_path = root / "source_manifest.json"
    if not manifest_path.exists():
        raise RuntimeError("missing source_manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("probe_mode") is not False:
        raise RuntimeError("full non-probe raw acquisition required")
    if manifest.get("source_fetch_complete") is not True:
        raise RuntimeError("raw acquisition incomplete")
    if manifest.get("holdout_accessed") is not False or manifest.get("locked_2026_accessed") is not False:
        raise RuntimeError("FAIL-CLOSED holdout/2026 flag")

    missing = {key: 0 for key in REQUIRED_FIELD_KEYS}
    rows = 0
    mark_value_invalid = 0
    amount_present = 0
    amount_invalid_when_present = 0

    for entry in manifest.get("raw_pages", []):
        p = root / "raw" / str(entry["page"])
        if not p.exists():
            raise RuntimeError(f"missing raw page: {p.name}")
        if base.sha256_file(p) != entry.get("sha256"):
            raise RuntimeError(f"raw page hash mismatch: {p.name}")
        obj = json.loads(gzip.decompress(p.read_bytes()).decode("utf-8"))
        trades = obj.get("result", {}).get("trades")
        if not isinstance(trades, list):
            raise RuntimeError(f"invalid trades payload: {p.name}")
        for row in trades:
            rows += 1
            if not isinstance(row, dict):
                raise RuntimeError(f"non-object trade row: {p.name}")
            for key in REQUIRED_FIELD_KEYS:
                if key not in row:
                    missing[key] += 1
            if "mark_price" in row:
                try:
                    v = float(row["mark_price"])
                    if not math.isfinite(v) or v <= 0:
                        raise ValueError
                except Exception:
                    mark_value_invalid += 1
            if "amount" in row and row.get("amount") not in (None, ""):
                amount_present += 1
                try:
                    v = float(row["amount"])
                    if not math.isfinite(v) or v <= 0:
                        raise ValueError
                except Exception:
                    amount_invalid_when_present += 1

    missing_total = sum(missing.values())
    result = {
        "lab_id": base.LAB_ID,
        "version": base.VERSION,
        "stage": "SOURCE_AUDIT_REQUIRED_FIELD_PRESENCE_GUARD",
        "raw_rows": rows,
        "required_field_keys": list(REQUIRED_FIELD_KEYS),
        "missing_required_field_keys": missing,
        "missing_required_field_key_total": missing_total,
        "required_field_presence_pass": missing_total == 0,
        "mark_price_nonfinite_or_nonpositive_diagnostic": mark_value_invalid,
        "amount_present_rows": amount_present,
        "amount_invalid_when_present": amount_invalid_when_present,
        "skew_values_computed": False,
        "signals_computed": False,
        "forward_returns_computed": False,
        "pnl_computed": False,
        "holdout_2025_accessed": False,
        "year_2026_accessed": False,
    }
    out = root / "source_gate_required_field_guard_receipt.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="source_audit_data")
    args = ap.parse_args()
    try:
        x = audit_required_fields(Path(args.input).resolve())
    except Exception as exc:
        print(f"SOURCE_REQUIRED_FIELD_GUARD_BLOCKED: {exc}")
        return 2
    print("SOURCE_REQUIRED_FIELD_PRESENCE_PASS" if x["required_field_presence_pass"] else "SOURCE_REQUIRED_FIELD_PRESENCE_BLOCKED")
    print(json.dumps(x, sort_keys=True))
    return 0 if x["required_field_presence_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

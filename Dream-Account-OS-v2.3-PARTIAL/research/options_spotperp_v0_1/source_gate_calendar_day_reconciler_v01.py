#!/usr/bin/env python3
"""
OPTIONS-SPOTPERP-001 V0.1 — exact calendar-day source-gate reconciler.

Outcome-blind implementation correction. The frozen protocol defines DTE as
30–120 CALENDAR DAYS inclusive. The original source_audit.py represented expiry
as 00:00 UTC and used fractional elapsed days, which can conservatively exclude
trades whose expiry date is exactly 30 calendar days after the trade date.

This reconciler operates only on already-acquired frozen-window raw source bytes,
re-verifies their hashes/provenance, recomputes ONLY eligibility coverage using
calendar-date differences, audits the exact 2021-04-01..2024-12-31 BTC price-file
cutoff when the canonical coverage gate passes, and writes a final source-gate
receipt. It computes NO skew, signal, forward return, PnL, regression or outcome.
Annual source-coverage counts are diagnostics only and do not alter the frozen
>=500 total-valid-day decision rule. Daily eligible call/put instrument counts are
persisted as a separate hashed outcome-blind audit artifact.
"""

from __future__ import annotations

import datetime as dt
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import source_audit_gate as base
from source_audit_gate_authority_reconciled_v01 import reclassify_raw_audit

UTC = dt.timezone.utc
MIN_DTE = 30
MAX_DTE = 120
CALL_MIN, CALL_MAX = 1.05, 1.20
PUT_MIN, PUT_MAX = 0.80, 0.95
MIN_SIDE = 5
MIN_VALID_DAYS = 500
SOURCE_START = dt.date(2021, 4, 1)
SOURCE_END_EXCLUSIVE = dt.date(2025, 1, 1)
DAILY_COVERAGE_FILE = "source_gate_calendar_day_daily_coverage.json"


def source_calendar_days_by_year() -> dict[str, int]:
    out: dict[str, int] = defaultdict(int)
    d = SOURCE_START
    while d < SOURCE_END_EXCLUSIVE:
        out[str(d.year)] += 1
        d += dt.timedelta(days=1)
    return dict(out)


def canonical_calendar_day_coverage(root: Path) -> dict[str, Any]:
    manifest = json.loads((root / "source_manifest.json").read_text(encoding="utf-8"))
    if manifest.get("probe_mode") is not False:
        raise RuntimeError("full non-probe raw acquisition required")
    if manifest.get("source_fetch_complete") is not True:
        raise RuntimeError("raw acquisition incomplete")
    if manifest.get("holdout_accessed") is not False or manifest.get("locked_2026_accessed") is not False:
        raise RuntimeError("FAIL-CLOSED holdout/2026 flag")

    calls: dict[str, set[str]] = defaultdict(set)
    puts: dict[str, set[str]] = defaultdict(set)
    counters = {
        "raw_rows": 0,
        "iv_rejected": 0,
        "index_price_rejected": 0,
        "dte_rejected": 0,
        "moneyness_rejected": 0,
        "eligible_trade_rows": 0,
    }

    for entry in manifest.get("raw_pages", []):
        path = root / "raw" / entry["page"]
        if not path.exists():
            raise RuntimeError(f"missing raw page: {path.name}")
        if base.sha256_file(path) != entry.get("sha256"):
            raise RuntimeError(f"raw page hash mismatch: {path.name}")
        obj = json.loads(gzip.decompress(path.read_bytes()).decode("utf-8"))
        rows = obj.get("result", {}).get("trades")
        if not isinstance(rows, list):
            raise RuntimeError(f"invalid trades payload: {path.name}")

        for row in rows:
            counters["raw_rows"] += 1
            if not isinstance(row, dict):
                raise RuntimeError(f"non-object trade row: {path.name}")
            try:
                ts = int(row["timestamp"])
                trade_time = dt.datetime.fromtimestamp(ts / 1000, tz=UTC)
                expiry, strike, side = base.parse_name(str(row["instrument_name"]))
            except Exception as exc:
                raise RuntimeError(f"structural row parse failure in {path.name}: {exc}") from exc

            if trade_time.date() < SOURCE_START or trade_time.date() >= SOURCE_END_EXCLUSIVE:
                raise RuntimeError(f"trade outside frozen source window: {trade_time.isoformat()}")

            try:
                iv = float(row["iv"])
                if not math.isfinite(iv) or iv <= 0:
                    raise ValueError
            except Exception:
                counters["iv_rejected"] += 1
                continue

            try:
                index_price = float(row["index_price"])
                if not math.isfinite(index_price) or index_price <= 0:
                    raise ValueError
            except Exception:
                counters["index_price_rejected"] += 1
                continue

            # Frozen authority: 30–120 CALENDAR DAYS inclusive.
            dte_calendar_days = (expiry - trade_time.date()).days
            if not (MIN_DTE <= dte_calendar_days <= MAX_DTE):
                counters["dte_rejected"] += 1
                continue

            m = strike / index_price
            day = trade_time.date().isoformat()
            if side == "C" and CALL_MIN <= m <= CALL_MAX:
                calls[day].add(str(row["instrument_name"]))
                counters["eligible_trade_rows"] += 1
            elif side == "P" and PUT_MIN <= m <= PUT_MAX:
                puts[day].add(str(row["instrument_name"]))
                counters["eligible_trade_rows"] += 1
            else:
                counters["moneyness_rejected"] += 1

    daily_rows: list[dict[str, Any]] = []
    d = SOURCE_START
    while d < SOURCE_END_EXCLUSIVE:
        day = d.isoformat()
        call_n = len(calls.get(day, set()))
        put_n = len(puts.get(day, set()))
        daily_rows.append({
            "date": day,
            "distinct_eligible_calls": call_n,
            "distinct_eligible_puts": put_n,
            "valid_min_5_each_side": call_n >= MIN_SIDE and put_n >= MIN_SIDE,
        })
        d += dt.timedelta(days=1)

    daily_path = root / DAILY_COVERAGE_FILE
    daily_payload = {
        "lab_id": base.LAB_ID,
        "version": base.VERSION,
        "stage": "SOURCE_AUDIT_DAILY_ELIGIBLE_INSTRUMENT_COVERAGE_ONLY",
        "source_start": SOURCE_START.isoformat(),
        "source_end_inclusive": (SOURCE_END_EXCLUSIVE - dt.timedelta(days=1)).isoformat(),
        "dte_definition": "calendar_date_difference_days",
        "dte_min_inclusive": MIN_DTE,
        "dte_max_inclusive": MAX_DTE,
        "call_strike_over_index": [CALL_MIN, CALL_MAX],
        "put_strike_over_index": [PUT_MIN, PUT_MAX],
        "min_distinct_instruments_per_side": MIN_SIDE,
        "rows": daily_rows,
        "skew_values_computed": False,
        "signals_computed": False,
        "forward_returns_computed": False,
        "pnl_computed": False,
        "holdout_2025_accessed": False,
        "year_2026_accessed": False,
    }
    daily_path.write_text(json.dumps(daily_payload, indent=2, sort_keys=True), encoding="utf-8")

    valid_days = [row["date"] for row in daily_rows if row["valid_min_5_each_side"]]
    valid_days_by_year: dict[str, int] = defaultdict(int)
    for day in valid_days:
        valid_days_by_year[day[:4]] += 1
    calendar_days_by_year = source_calendar_days_by_year()
    coverage_ratio_by_year = {
        year: round(valid_days_by_year.get(year, 0) / days, 6)
        for year, days in calendar_days_by_year.items()
    }

    return {
        **counters,
        "dte_definition": "calendar_date_difference_days",
        "dte_min_inclusive": MIN_DTE,
        "dte_max_inclusive": MAX_DTE,
        "min_distinct_instruments_per_side": MIN_SIDE,
        "valid_signal_coverage_days": len(valid_days),
        "min_required_valid_days": MIN_VALID_DAYS,
        "coverage_pass": len(valid_days) >= MIN_VALID_DAYS,
        "calendar_days_by_year": calendar_days_by_year,
        "valid_signal_coverage_days_by_year": {
            year: valid_days_by_year.get(year, 0) for year in calendar_days_by_year
        },
        "coverage_ratio_by_year": coverage_ratio_by_year,
        "annual_coverage_is_diagnostic_only": True,
        "daily_coverage_artifact": DAILY_COVERAGE_FILE,
        "daily_coverage_rows": len(daily_rows),
        "daily_coverage_sha256": base.sha256_file(daily_path),
        "daily_coverage_contains_outcomes": False,
        "valid_days_first_10": valid_days[:10],
        "valid_days_last_10": valid_days[-10:],
        "skew_values_computed": False,
        "signals_computed": False,
        "forward_returns_computed": False,
        "pnl_computed": False,
    }


def write_receipt(root: Path, status: str, structural: dict[str, Any], coverage: dict[str, Any], btc: dict[str, Any] | None, btc_manifest: list[dict[str, Any]], detail: str | None) -> Path:
    binding = base.protocol_binding(Path(__file__).resolve().parent / "PROTOCOL.json")
    receipt = {
        "lab_id": base.LAB_ID,
        "version": base.VERSION,
        "stage": "FINAL_SOURCE_DATA_GATE_CALENDAR_DAY_RECONCILED",
        "status": status,
        "authority": binding,
        "deribit_structural_audit": structural,
        "calendar_day_coverage_audit": coverage,
        "btc_price_audit": btc,
        "btc_price_raw_archives": btc_manifest,
        "detail": detail,
        "skew_values_computed": False,
        "signals_computed": False,
        "forward_returns_computed": False,
        "pnl_computed": False,
        "holdout_2025_accessed": False,
        "year_2026_accessed": False,
    }
    path = root / "source_gate_calendar_day_reconciled_receipt.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
    return path


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default="source_audit_data")
    args = ap.parse_args()
    root = Path(args.input).resolve()
    btc = None
    btc_manifest: list[dict[str, Any]] = []
    try:
        raw = base.audit_deribit_raw(root, False)
        structural = reclassify_raw_audit(raw)
        if structural.get("schema_and_provenance_pass") is not True:
            p = write_receipt(root, "SOURCE_AUDIT_BLOCKED", structural, {}, None, [], "structural/provenance gate failed")
            print(f"SOURCE_AUDIT_BLOCKED: {p}")
            return 2

        coverage = canonical_calendar_day_coverage(root)
        if coverage["coverage_pass"] is not True:
            p = write_receipt(root, "SOURCE_AUDIT_BLOCKED", structural, coverage, None, [], "canonical calendar-day coverage below frozen minimum")
            print(f"SOURCE_AUDIT_BLOCKED: {p}")
            return 2

        btc, btc_manifest = base.audit_binance(root, False)
        if btc.get("exact_discovery_cutoff_verified") is not True:
            p = write_receipt(root, "SOURCE_AUDIT_BLOCKED", structural, coverage, btc, btc_manifest, "exact BTC price cutoff gate failed")
            print(f"SOURCE_AUDIT_BLOCKED: {p}")
            return 2

        p = write_receipt(root, "SOURCE_AUDIT_PASS", structural, coverage, btc, btc_manifest, None)
        print(f"SOURCE_AUDIT_PASS: {p}")
        print("NO SKEW / NO SIGNALS / NO RETURNS / NO PNL / NO 2025/2026")
        return 0
    except base.EnvBlocked as exc:
        # A network block can only occur in the BTC archive audit at this stage.
        structural = locals().get("structural", {})
        coverage = locals().get("coverage", {})
        p = write_receipt(root, "EXECUTION_ENVIRONMENT_BLOCKED", structural, coverage, btc, btc_manifest, str(exc))
        print(f"EXECUTION_ENVIRONMENT_BLOCKED: {p}")
        return 12
    except Exception as exc:
        structural = locals().get("structural", {})
        coverage = locals().get("coverage", {})
        p = write_receipt(root, "SOURCE_AUDIT_BLOCKED", structural, coverage, btc, btc_manifest, str(exc))
        print(f"SOURCE_AUDIT_BLOCKED: {p}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

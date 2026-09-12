"""Outcome-blind diagnostic for the Cross-Venue Funding & Basis provenance gate.

This script does NOT relax or replace the frozen V0.1 gate. It reuses the exact V0.1
public fetchers and timestamp audit logic, then writes diagnostics even when the common
full-month intersection is empty. Economic values are never summarized or printed.
"""

from __future__ import annotations

import calendar
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cross_venue_funding_basis_provenance_shakedown_v01 as v1

LAB_ID = v1.LAB_ID
DIAGNOSTIC_ID = "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_DIAGNOSTIC_V02"


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def month_keys(start_year: int = 2023, start_month: int = 1, end_year: int = 2025, end_month: int = 12) -> list[str]:
    out: list[str] = []
    year, month = start_year, start_month
    while (year, month) <= (end_year, end_month):
        out.append(f"{year:04d}-{month:02d}")
        month += 1
        if month == 13:
            month = 1
            year += 1
    return out


def utc_iso(ts_ms: int | None) -> str | None:
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def compact_series(audit: dict[str, Any]) -> dict[str, Any]:
    eligible = list(audit["full_months_timestamp_eligible"])
    return {
        "series_id": audit["series_id"],
        "venue": audit["venue"],
        "instrument": audit["instrument"],
        "record_count": audit["record_count"],
        "unique_timestamp_count": audit["unique_timestamp_count"],
        "first_timestamp_ms": audit["first_timestamp_ms"],
        "first_timestamp_utc": utc_iso(audit["first_timestamp_ms"]),
        "last_timestamp_ms": audit["last_timestamp_ms"],
        "last_timestamp_utc": utc_iso(audit["last_timestamp_ms"]),
        "duplicate_timestamp_count": audit["duplicate_timestamp_count"],
        "conflicting_duplicate_timestamp_count": len(audit["conflicting_duplicate_timestamps"]),
        "max_gap_ms": audit["max_gap_ms"],
        "large_gap_count": audit["large_gap_count"],
        "interval_histogram_ms": audit["interval_histogram_ms"],
        "eligible_full_month_count": len(eligible),
        "first_eligible_full_month": eligible[0] if eligible else None,
        "last_eligible_full_month": eligible[-1] if eligible else None,
        "eligible_full_months": eligible,
        "canonical_raw_records_sha256": audit["canonical_raw_records_sha256"],
        "economic_fields_summarized": False,
    }


def month_failure_reason(audit: dict[str, Any], month: str, expected_max_gap_ms: int) -> dict[str, Any]:
    d = audit["month_diagnostics"].get(month)
    if d is None:
        return {
            "present": False,
            "eligible": False,
            "record_count": 0,
            "first_timestamp_ms": None,
            "last_timestamp_ms": None,
            "max_gap_ms": None,
            "reason": "NO_RECORDS_IN_MONTH",
        }

    year, mon = map(int, month.split("-"))
    month_start = datetime(year, mon, 1, tzinfo=timezone.utc)
    days = calendar.monthrange(year, mon)[1]
    month_end = datetime(year, mon, days, 23, 59, 59, 999000, tzinfo=timezone.utc)
    month_start_ms = int(month_start.timestamp() * 1000)
    month_end_ms = int(month_end.timestamp() * 1000)

    starts_in_time = (d["first_timestamp_ms"] - month_start_ms) <= expected_max_gap_ms
    ends_in_time = (month_end_ms - d["last_timestamp_ms"]) < expected_max_gap_ms
    no_large_gap = d["max_gap_ms"] is None or d["max_gap_ms"] <= expected_max_gap_ms
    eligible = bool(d["full_month_coverage_by_timestamp_only"])

    reasons: list[str] = []
    if not starts_in_time:
        reasons.append("LATE_MONTH_START")
    if not ends_in_time:
        reasons.append("EARLY_MONTH_END")
    if not no_large_gap:
        reasons.append("INTRA_MONTH_GAP_EXCEEDS_EXPECTED_MAX")
    if not reasons and not eligible:
        reasons.append("UNCLASSIFIED_TIMESTAMP_COVERAGE_FAILURE")

    return {
        "present": True,
        "eligible": eligible,
        "record_count": d["record_count"],
        "first_timestamp_ms": d["first_timestamp_ms"],
        "last_timestamp_ms": d["last_timestamp_ms"],
        "max_gap_ms": d["max_gap_ms"],
        "reason": "PASS" if eligible else "+".join(reasons),
    }


def build_diagnostic() -> dict[str, Any]:
    if not v1.AUDIT_END_MS < v1.LOCKED_2026_START_MS:
        raise v1.ProvenanceFailure("diagnostic boundary reaches locked 2026")

    raw = {
        "BINANCE_BTCUSDT": v1.fetch_binance_funding("BTCUSDT", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "BINANCE_ETHUSDT": v1.fetch_binance_funding("ETHUSDT", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "HYPERLIQUID_BTC": v1.fetch_hyperliquid_funding("BTC", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "HYPERLIQUID_ETH": v1.fetch_hyperliquid_funding("ETH", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
    }
    specs = {
        "BINANCE_BTCUSDT": v1.SeriesSpec("BINANCE_BTCUSDT", "BINANCE_USDM", "BTCUSDT", 8 * 60 * 60 * 1000),
        "BINANCE_ETHUSDT": v1.SeriesSpec("BINANCE_ETHUSDT", "BINANCE_USDM", "ETHUSDT", 8 * 60 * 60 * 1000),
        "HYPERLIQUID_BTC": v1.SeriesSpec("HYPERLIQUID_BTC", "HYPERLIQUID", "BTC", 60 * 60 * 1000),
        "HYPERLIQUID_ETH": v1.SeriesSpec("HYPERLIQUID_ETH", "HYPERLIQUID", "ETH", 60 * 60 * 1000),
    }
    ts_fields = {
        "BINANCE_BTCUSDT": "fundingTime",
        "BINANCE_ETHUSDT": "fundingTime",
        "HYPERLIQUID_BTC": "time",
        "HYPERLIQUID_ETH": "time",
    }
    audits = {sid: v1.audit_series(specs[sid], raw[sid], ts_fields[sid]) for sid in sorted(raw)}

    eligible_sets = {sid: set(audits[sid]["full_months_timestamp_eligible"]) for sid in audits}
    common = sorted(set.intersection(*(eligible_sets[sid] for sid in sorted(eligible_sets))))

    coverage_matrix: dict[str, Any] = {}
    for month in month_keys():
        series_rows = {
            sid: month_failure_reason(audits[sid], month, specs[sid].expected_max_gap_ms)
            for sid in sorted(audits)
        }
        eligible_ids = [sid for sid, row in series_rows.items() if row["eligible"]]
        coverage_matrix[month] = {
            "eligible_series_count": len(eligible_ids),
            "eligible_series": eligible_ids,
            "all_four_eligible": len(eligible_ids) == 4,
            "series": series_rows,
        }

    locked_leaks = any((a["last_timestamp_ms"] or 0) >= v1.LOCKED_2026_START_MS for a in audits.values())
    conflicts = sum(len(a["conflicting_duplicate_timestamps"]) for a in audits.values())

    diagnostic = {
        "schema_version": "0.2",
        "lab_id": LAB_ID,
        "diagnostic_id": DIAGNOSTIC_ID,
        "classification": "PROVENANCE_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "DIAGNOSTIC_COMPLETE" if not locked_leaks else "FAIL_LOCKED_DATA_BOUNDARY",
        "audit_start_ms": v1.AUDIT_START_MS,
        "audit_end_ms": v1.AUDIT_END_MS,
        "locked_2026_start_ms": v1.LOCKED_2026_START_MS,
        "locked_2026_accessed": locked_leaks,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "v01_coverage_rule_changed": False,
        "conflicting_duplicate_timestamp_count": conflicts,
        "series": {sid: compact_series(audits[sid]) for sid in sorted(audits)},
        "common_eligible_full_month_count": len(common),
        "common_eligible_full_months": common,
        "month_timestamp_coverage_matrix": coverage_matrix,
        "decision": "V01_STILL_BLOCKED_NO_COMMON_FULL_MONTH" if not common else "V01_MAY_BE_RERUN_UNCHANGED",
    }
    diagnostic["diagnostic_sha256"] = sha256_json(diagnostic)
    return diagnostic


def main() -> None:
    output = Path(os.environ.get(
        "PREFREEZE_PROVENANCE_DIAGNOSTIC",
        "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_DIAGNOSTIC_V02_RECEIPT.json",
    ))
    d = build_diagnostic()
    output.write_text(json.dumps(d, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "lab_id": d["lab_id"],
        "diagnostic_id": d["diagnostic_id"],
        "status": d["status"],
        "locked_2026_accessed": d["locked_2026_accessed"],
        "carry_computed": d["carry_computed"],
        "pnl_computed": d["pnl_computed"],
        "common_eligible_full_month_count": d["common_eligible_full_month_count"],
        "decision": d["decision"],
        "diagnostic_sha256": d["diagnostic_sha256"],
    }, sort_keys=True))

    for sid, s in d["series"].items():
        print(json.dumps({
            "series_id": sid,
            "record_count": s["record_count"],
            "first_timestamp_utc": s["first_timestamp_utc"],
            "last_timestamp_utc": s["last_timestamp_utc"],
            "large_gap_count": s["large_gap_count"],
            "max_gap_ms": s["max_gap_ms"],
            "eligible_full_month_count": s["eligible_full_month_count"],
            "first_eligible_full_month": s["first_eligible_full_month"],
            "last_eligible_full_month": s["last_eligible_full_month"],
            "raw_sha256": s["canonical_raw_records_sha256"],
        }, sort_keys=True))

    if d["locked_2026_accessed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

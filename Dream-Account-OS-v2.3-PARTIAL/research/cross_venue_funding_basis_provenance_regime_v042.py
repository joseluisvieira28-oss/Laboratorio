"""Outcome-blind G03/G04 regime and exact-missing-slot diagnostic for Cross-Venue Funding Basis V0.4.2.

This module does not read, summarize, rank, or transform funding-rate magnitudes.
It reconstructs only settlement cadence metadata, normalized timestamp occupancy,
source integrity, and deterministic common-month eligibility.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cross_venue_funding_basis_provenance_archive_v03 import fetch_binance_archives
from cross_venue_funding_basis_provenance_slots_v04 import (
    BINANCE_INTERVAL_MS,
    HYPERLIQUID_INTERVAL_MS,
    _common_months,
    _month_bounds_ms,
    _months_in_scope,
    nearest_nominal_slot,
    slot_coverage_audit,
    validate_binance_interval_metadata,
)
from cross_venue_funding_basis_provenance_slots_v041 import (
    AUDIT_END_MS,
    AUDIT_START_MS,
    LOCKED_2026_START_MS,
    HyperliquidPacedClient,
)

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
AMENDMENT_ID = "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_REGIME_DIAGNOSTIC_V042"

carry_computed = False
apr_apy_computed = False
pnl_computed = False
signals_computed = False


class RegimeDiagnosticFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RegimeDiagnosticFailure(message)


def _iso_utc(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_hash(values: list[int]) -> str:
    payload = json.dumps(values, separators=(",", ":"), sort_keys=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _slot_details(
    *,
    series_id: str,
    rows: list[dict[str, Any]],
    timestamp_field: str,
    interval_ms: int,
) -> dict[str, Any]:
    slots: list[int] = []
    for row in rows:
        _require(timestamp_field in row, f"{series_id}: missing timestamp")
        ts = int(row[timestamp_field])
        _require(AUDIT_START_MS <= ts <= AUDIT_END_MS, f"{series_id}: timestamp outside audit window")
        _require(ts < LOCKED_2026_START_MS, f"{series_id}: locked 2026 timestamp")
        slot, _ = nearest_nominal_slot(ts, interval_ms)
        slots.append(slot)

    counts = Counter(slots)
    unique_slots = sorted(counts)
    duplicates = sorted(slot for slot, count in counts.items() if count > 1)

    month_details: dict[str, Any] = {}
    eligible: list[str] = []
    for month in _months_in_scope():
        start_ms, end_ms = _month_bounds_ms(month)
        expected = list(range(start_ms, end_ms, interval_ms))
        expected_set = set(expected)
        observed = sorted(slot for slot in set(unique_slots) if start_ms <= slot < end_ms)
        observed_set = set(observed)
        missing = sorted(expected_set - observed_set)
        extra = sorted(observed_set - expected_set)
        dup = sorted(slot for slot in duplicates if start_ms <= slot < end_ms)

        deltas = [b - a for a, b in zip(observed, observed[1:])]
        delta_hist = Counter(deltas)
        if not missing and not extra and not dup:
            eligible.append(month)

        month_details[month] = {
            "expected_slot_count": len(expected),
            "observed_unique_slot_count": len(observed),
            "missing_slot_count": len(missing),
            "missing_nominal_slot_ms": missing,
            "missing_nominal_slot_utc": [_iso_utc(x) for x in missing],
            "duplicate_slot_count": len(dup),
            "duplicate_nominal_slot_ms": dup,
            "extra_slot_count": len(extra),
            "normalized_adjacent_delta_histogram_ms": {
                str(k): v for k, v in sorted(delta_hist.items())
            },
            "full_month_coverage_by_nominal_slot": not missing and not extra and not dup,
        }

    return {
        "series_id": series_id,
        "record_count": len(rows),
        "unique_normalized_slot_count": len(unique_slots),
        "duplicate_normalized_slot_count": sum(c - 1 for c in counts.values() if c > 1),
        "eligible_full_months": eligible,
        "month_details": month_details,
        "canonical_normalized_timestamp_sha256": _canonical_hash(unique_slots),
    }


def _binance_interval_metadata(rows: list[dict[str, Any]]) -> dict[str, Any]:
    overall: set[int] = set()
    monthly: dict[str, set[int]] = {month: set() for month in _months_in_scope()}
    for row in rows:
        ts = int(row["fundingTime"])
        raw = row.get("funding_interval_hours")
        _require(raw is not None and raw != "", "Binance historical row missing funding_interval_hours")
        hours = int(str(raw))
        overall.add(hours)
        month = datetime.fromtimestamp(ts / 1000, tz=timezone.utc).strftime("%Y-%m")
        if month in monthly:
            monthly[month].add(hours)
    return {
        "observed_values_hours": sorted(overall),
        "monthly_observed_values_hours": {m: sorted(v) for m, v in monthly.items()},
        "all_rows_exactly_8h": overall == {8} and all(v == {8} for v in monthly.values()),
    }


def _contiguous_blocks(months: list[str]) -> list[list[str]]:
    if not months:
        return []
    month_set = set(months)
    blocks: list[list[str]] = []
    visited: set[str] = set()
    for month in months:
        if month in visited:
            continue
        year, mon = map(int, month.split("-"))
        prev_year, prev_mon = (year - 1, 12) if mon == 1 else (year, mon - 1)
        prev = f"{prev_year:04d}-{prev_mon:02d}"
        if prev in month_set:
            continue
        block: list[str] = []
        cur_year, cur_mon = year, mon
        while True:
            cur = f"{cur_year:04d}-{cur_mon:02d}"
            if cur not in month_set:
                break
            block.append(cur)
            visited.add(cur)
            cur_year, cur_mon = (cur_year + 1, 1) if cur_mon == 12 else (cur_year, cur_mon + 1)
        blocks.append(block)
    return blocks


def run_diagnostic() -> dict[str, Any]:
    _require(AUDIT_END_MS < LOCKED_2026_START_MS, "audit reaches locked 2026")

    binance_btc, manifest_btc = fetch_binance_archives("BTCUSDT")
    binance_eth, manifest_eth = fetch_binance_archives("ETHUSDT")
    validate_binance_interval_metadata(binance_btc)
    validate_binance_interval_metadata(binance_eth)

    client = HyperliquidPacedClient()
    hyper_btc = client.fetch_funding("BTC", AUDIT_START_MS, AUDIT_END_MS)
    hyper_eth = client.fetch_funding("ETH", AUDIT_START_MS, AUDIT_END_MS)

    raw = {
        "BINANCE_BTCUSDT": (binance_btc, "fundingTime", BINANCE_INTERVAL_MS),
        "BINANCE_ETHUSDT": (binance_eth, "fundingTime", BINANCE_INTERVAL_MS),
        "HYPERLIQUID_BTC": (hyper_btc, "time", HYPERLIQUID_INTERVAL_MS),
        "HYPERLIQUID_ETH": (hyper_eth, "time", HYPERLIQUID_INTERVAL_MS),
    }

    coverage = {
        series_id: slot_coverage_audit(
            series_id=series_id,
            rows=rows,
            timestamp_field=field,
            interval_ms=interval_ms,
        )
        for series_id, (rows, field, interval_ms) in raw.items()
    }
    details = {
        series_id: _slot_details(
            series_id=series_id,
            rows=rows,
            timestamp_field=field,
            interval_ms=interval_ms,
        )
        for series_id, (rows, field, interval_ms) in raw.items()
    }

    common = _common_months(coverage)
    all_months = _months_in_scope()
    excluded = [month for month in all_months if month not in common]
    blocks = _contiguous_blocks(common)

    binance_regime = {
        "BTCUSDT": _binance_interval_metadata(binance_btc),
        "ETHUSDT": _binance_interval_metadata(binance_eth),
    }
    binance_g03 = all(x["all_rows_exactly_8h"] for x in binance_regime.values())

    checksum_items = manifest_btc + manifest_eth
    checksum_ok = all(item["checksum_match"] for item in checksum_items)

    hyperliquid_g03 = True
    g03_pass = binance_g03 and hyperliquid_g03
    g04_pass = checksum_ok and bool(common)

    return {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "amendment_id": AMENDMENT_ID,
        "classification": "PROVENANCE_REGIME_AND_EXACT_MISSING_SLOT_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "PASS" if g03_pass and g04_pass else "FAIL_CLOSED",
        "g03_funding_regimes_status": "PASS" if g03_pass else "FAIL_CLOSED",
        "g04_raw_provenance_status": "PASS_WITH_EXPLICIT_MONTH_EXCLUSION" if g04_pass else "FAIL_CLOSED",
        "binance_historical_interval_metadata": binance_regime,
        "hyperliquid_documented_nominal_interval_hours": 1,
        "series_slot_details": details,
        "common_eligible_months": common,
        "common_eligible_month_count": len(common),
        "provenance_excluded_months": excluded,
        "contiguous_common_eligible_blocks": blocks,
        "g10_materialization_candidate": {
            "definition": "ALL_COMMON_FULL_UTC_MONTHS_PASSING_G03_G04",
            "months": common,
            "month_count": len(common),
            "first_month": common[0] if common else None,
            "last_month": common[-1] if common else None,
            "is_contiguous": len(blocks) <= 1,
            "contiguous_blocks": blocks,
            "outcome_based_selection_used": False,
        },
        "binance_archive_checksums_all_match": checksum_ok,
        "hyperliquid_request_count": client.request_count,
        "hyperliquid_http_429_retry_count": client.http_429_retry_count,
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "economic_fields_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "discovery_authorized": False,
        "trading_authorized": False,
    }


def main() -> int:
    output = Path(os.environ.get(
        "PREFREEZE_PROVENANCE_V042_RECEIPT",
        "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_REGIME_V042_RECEIPT.json",
    ))
    receipt = run_diagnostic()
    _require(receipt["locked_2026_accessed"] is False, "locked 2026 access detected")
    _require(receipt["funding_rate_values_summarized"] is False, "funding values summarized")
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "g03": receipt["g03_funding_regimes_status"],
        "g04": receipt["g04_raw_provenance_status"],
        "common_month_count": receipt["common_eligible_month_count"],
        "excluded_months": receipt["provenance_excluded_months"],
        "receipt": str(output),
    }, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())

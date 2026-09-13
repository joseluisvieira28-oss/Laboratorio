"""Outcome-blind funding-slot provenance normalization for Cross-Venue Funding & Basis V0.4.

This amendment corrects timestamp semantics only. Raw venue timestamps may arrive a few
milliseconds/seconds after the nominal funding boundary; V0.1's exact raw max-gap rule
therefore mislabeled complete event sequences as incomplete.

V0.4 maps every event to its unique nearest nominal funding slot (Binance 8h,
Hyperliquid 1h) and requires exact slot occupancy: every expected slot must exist exactly
once. Missing slots remain failures. Economic rate values are never summarized or used
for coverage, selection, ranking, or any trading decision.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cross_venue_funding_basis_provenance_shakedown_v01 import (
    AUDIT_END_MS,
    AUDIT_START_MS,
    LOCKED_2026_START_MS,
    canonical_bytes,
    fetch_hyperliquid_funding,
)
from cross_venue_funding_basis_provenance_archive_v03 import fetch_binance_archives

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
NORMALIZATION_ID = "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_SLOT_NORMALIZATION_V04"
BINANCE_INTERVAL_MS = 8 * 60 * 60 * 1000
HYPERLIQUID_INTERVAL_MS = 60 * 60 * 1000

carry_computed = False
apr_apy_computed = False
pnl_computed = False
signals_computed = False


class SlotNormalizationFailure(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise SlotNormalizationFailure(message)


def nearest_nominal_slot(timestamp_ms: int, interval_ms: int) -> tuple[int, int]:
    """Return (slot_ms, signed_jitter_ms) using a unique nearest-slot assignment."""
    _require(interval_ms > 0, "interval must be positive")
    slot = ((int(timestamp_ms) + interval_ms // 2) // interval_ms) * interval_ms
    jitter = int(timestamp_ms) - slot
    _require(abs(jitter) < interval_ms // 2, "timestamp is ambiguous between nominal slots")
    return slot, jitter


def _month_bounds_ms(month: str) -> tuple[int, int]:
    year, mon = map(int, month.split("-"))
    start = datetime(year, mon, 1, tzinfo=timezone.utc)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def _months_in_scope() -> list[str]:
    months: list[str] = []
    year, month = 2023, 1
    while (year, month) <= (2025, 12):
        months.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def validate_binance_interval_metadata(rows: list[dict[str, Any]]) -> None:
    """Fail closed if Binance archive metadata contradicts the frozen 8h cadence."""
    _require(bool(rows), "empty Binance series")
    for row in rows:
        raw = row.get("funding_interval_hours")
        _require(raw is not None and raw != "", "Binance archive missing funding_interval_hours")
        try:
            hours = int(str(raw))
        except ValueError as exc:
            raise SlotNormalizationFailure(f"invalid funding_interval_hours: {raw!r}") from exc
        _require(hours == 8, f"Binance interval metadata drifted from frozen 8h cadence: {hours}")


def slot_coverage_audit(*, series_id: str, rows: list[dict[str, Any]], timestamp_field: str, interval_ms: int) -> dict[str, Any]:
    _require(bool(rows), f"{series_id}: empty series")
    slots: list[int] = []
    jitters: list[int] = []
    for row in rows:
        _require(timestamp_field in row, f"{series_id}: missing timestamp field")
        ts = int(row[timestamp_field])
        _require(AUDIT_START_MS <= ts <= AUDIT_END_MS, f"{series_id}: timestamp outside frozen audit scope")
        _require(ts < LOCKED_2026_START_MS, f"{series_id}: locked 2026 timestamp")
        slot, jitter = nearest_nominal_slot(ts, interval_ms)
        _require(AUDIT_START_MS <= slot < LOCKED_2026_START_MS, f"{series_id}: normalized slot outside frozen scope")
        slots.append(slot)
        jitters.append(jitter)

    counts = Counter(slots)
    duplicate_slots = sorted(slot for slot, count in counts.items() if count > 1)
    unique_slots = sorted(counts)
    slot_set = set(unique_slots)

    month_diagnostics: dict[str, Any] = {}
    eligible_months: list[str] = []
    for month in _months_in_scope():
        start_ms, end_ms = _month_bounds_ms(month)
        expected = list(range(start_ms, end_ms, interval_ms))
        expected_set = set(expected)
        observed_set = {slot for slot in slot_set if start_ms <= slot < end_ms}
        missing = sorted(expected_set - observed_set)
        extra = sorted(observed_set - expected_set)
        duplicate_in_month = [slot for slot in duplicate_slots if start_ms <= slot < end_ms]
        eligible = not missing and not extra and not duplicate_in_month
        if eligible:
            eligible_months.append(month)
        month_jitters = [jitter for slot, jitter in zip(slots, jitters) if start_ms <= slot < end_ms]
        month_diagnostics[month] = {
            "expected_slot_count": len(expected),
            "observed_unique_slot_count": len(observed_set),
            "missing_slot_count": len(missing),
            "duplicate_slot_count": len(duplicate_in_month),
            "extra_slot_count": len(extra),
            "max_abs_slot_jitter_ms": max((abs(jitter) for jitter in month_jitters), default=None),
            "full_month_coverage_by_nominal_slot": eligible,
        }

    canonical_slot_sha256 = hashlib.sha256(canonical_bytes(unique_slots)).hexdigest()
    return {
        "series_id": series_id,
        "record_count": len(rows),
        "unique_normalized_slot_count": len(unique_slots),
        "duplicate_normalized_slot_count": sum(count - 1 for count in counts.values() if count > 1),
        "first_normalized_slot_ms": unique_slots[0],
        "last_normalized_slot_ms": unique_slots[-1],
        "max_abs_slot_jitter_ms": max(abs(jitter) for jitter in jitters),
        "eligible_full_months": eligible_months,
        "month_diagnostics": month_diagnostics,
        "canonical_normalized_slot_sha256": canonical_slot_sha256,
        "economic_fields_summarized": False,
    }


def _common_months(audits: dict[str, dict[str, Any]]) -> list[str]:
    expected_ids = {"BINANCE_BTCUSDT", "BINANCE_ETHUSDT", "HYPERLIQUID_BTC", "HYPERLIQUID_ETH"}
    _require(set(audits) == expected_ids, "unexpected series set")
    month_sets = [set(audits[series_id]["eligible_full_months"]) for series_id in sorted(expected_ids)]
    return sorted(set.intersection(*month_sets))


def run_diagnostic() -> dict[str, Any]:
    _require(AUDIT_END_MS < LOCKED_2026_START_MS, "audit reaches locked 2026")

    binance_btc, manifest_btc = fetch_binance_archives("BTCUSDT")
    binance_eth, manifest_eth = fetch_binance_archives("ETHUSDT")
    validate_binance_interval_metadata(binance_btc)
    validate_binance_interval_metadata(binance_eth)
    hyper_btc = fetch_hyperliquid_funding("BTC", AUDIT_START_MS, AUDIT_END_MS)
    hyper_eth = fetch_hyperliquid_funding("ETH", AUDIT_START_MS, AUDIT_END_MS)

    audits = {
        "BINANCE_BTCUSDT": slot_coverage_audit(series_id="BINANCE_BTCUSDT", rows=binance_btc, timestamp_field="fundingTime", interval_ms=BINANCE_INTERVAL_MS),
        "BINANCE_ETHUSDT": slot_coverage_audit(series_id="BINANCE_ETHUSDT", rows=binance_eth, timestamp_field="fundingTime", interval_ms=BINANCE_INTERVAL_MS),
        "HYPERLIQUID_BTC": slot_coverage_audit(series_id="HYPERLIQUID_BTC", rows=hyper_btc, timestamp_field="time", interval_ms=HYPERLIQUID_INTERVAL_MS),
        "HYPERLIQUID_ETH": slot_coverage_audit(series_id="HYPERLIQUID_ETH", rows=hyper_eth, timestamp_field="time", interval_ms=HYPERLIQUID_INTERVAL_MS),
    }
    common = _common_months(audits)
    checksums = manifest_btc + manifest_eth
    checksum_ok = all(item["checksum_match"] for item in checksums)

    return {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "normalization_id": NORMALIZATION_ID,
        "classification": "PROVENANCE_SLOT_NORMALIZATION_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "PASS",
        "technical_route_status": "PASS_BINANCE_ARCHIVE_CHECKSUM_VERIFIED",
        "slot_coverage_gate_status": "PASS" if common else "FAIL_CLOSED_NO_COMMON_FULL_UTC_MONTH",
        "audit_start_ms": AUDIT_START_MS,
        "audit_end_ms": AUDIT_END_MS,
        "locked_2026_start_ms": LOCKED_2026_START_MS,
        "binance_nominal_interval_ms": BINANCE_INTERVAL_MS,
        "hyperliquid_nominal_interval_ms": HYPERLIQUID_INTERVAL_MS,
        "binance_interval_metadata_validated_8h": True,
        "binance_archive_checksums_all_match": checksum_ok,
        "series_slot_audits": audits,
        "common_eligible_months": common,
        "common_full_month_count": len(common),
        "first_common_full_month": common[0] if common else None,
        "last_common_full_month": common[-1] if common else None,
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
        "normalization_rule": "UNIQUE_NEAREST_NOMINAL_FUNDING_SLOT_EXACT_MONTHLY_SLOT_OCCUPANCY"
    }


def main() -> int:
    receipt_path = Path(os.environ.get("PREFREEZE_PROVENANCE_SLOT_V04_RECEIPT", "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_SLOT_V04_RECEIPT.json"))
    receipt = run_diagnostic()
    _require(receipt["locked_2026_accessed"] is False, "locked 2026 access detected")
    _require(receipt["binance_archive_checksums_all_match"] is True, "Binance checksum failure")
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "slot_coverage_gate_status": receipt["slot_coverage_gate_status"],
        "common_full_month_count": receipt["common_full_month_count"],
        "first_common_full_month": receipt["first_common_full_month"],
        "last_common_full_month": receipt["last_common_full_month"],
        "receipt": str(receipt_path),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

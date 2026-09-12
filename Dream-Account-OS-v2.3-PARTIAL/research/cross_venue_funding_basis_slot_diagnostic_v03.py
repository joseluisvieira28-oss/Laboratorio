"""Outcome-blind slot-occupancy diagnostic for Cross-Venue Funding & Basis Lab V0.1.

This diagnostic does not alter the frozen V0.1 gate. It reuses the V0.1 public fetchers,
looks only at timestamps, and maps each timestamp to its mathematically nearest scheduled
funding slot. It reports missing slots, slot collisions, timestamp offsets, and common
full-month slot coverage. It never summarizes funding values or computes carry/PnL.
"""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cross_venue_funding_basis_provenance_shakedown_v01 as v1

DIAGNOSTIC_ID = "CROSS_VENUE_FUNDING_BASIS_SLOT_DIAGNOSTIC_V03"

SERIES = {
    "BINANCE_BTCUSDT": {"cadence_ms": 8 * 60 * 60 * 1000, "timestamp_field": "fundingTime"},
    "BINANCE_ETHUSDT": {"cadence_ms": 8 * 60 * 60 * 1000, "timestamp_field": "fundingTime"},
    "HYPERLIQUID_BTC": {"cadence_ms": 60 * 60 * 1000, "timestamp_field": "time"},
    "HYPERLIQUID_ETH": {"cadence_ms": 60 * 60 * 1000, "timestamp_field": "time"},
}


def sha256_json(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def utc_iso(ts_ms: int | None) -> str | None:
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def month_bounds(month: str) -> tuple[int, int]:
    year, mon = map(int, month.split("-"))
    start = datetime(year, mon, 1, tzinfo=timezone.utc)
    if mon == 12:
        end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
    else:
        end = datetime(year, mon + 1, 1, tzinfo=timezone.utc)
    return int(start.timestamp() * 1000), int(end.timestamp() * 1000)


def month_keys() -> list[str]:
    out: list[str] = []
    year, mon = 2023, 1
    while (year, mon) <= (2025, 12):
        out.append(f"{year:04d}-{mon:02d}")
        mon += 1
        if mon == 13:
            mon = 1
            year += 1
    return out


def nearest_slot(ts_ms: int, cadence_ms: int) -> tuple[int, int, bool]:
    """Return (slot_ms, signed_offset_ms, ambiguous_halfway_mapping)."""
    lower = (ts_ms // cadence_ms) * cadence_ms
    upper = lower + cadence_ms
    dl = ts_ms - lower
    du = upper - ts_ms
    ambiguous = dl == du
    slot = lower if dl <= du else upper
    return slot, ts_ms - slot, ambiguous


def diagnose_timestamps(series_id: str, timestamps: list[int]) -> dict[str, Any]:
    if series_id not in SERIES:
        raise v1.ProvenanceFailure("unexpected series id")
    cadence_ms = int(SERIES[series_id]["cadence_ms"])
    if any(ts < v1.AUDIT_START_MS or ts > v1.AUDIT_END_MS for ts in timestamps):
        raise v1.ProvenanceFailure(f"{series_id}: timestamp outside frozen boundary")
    if any(ts >= v1.LOCKED_2026_START_MS for ts in timestamps):
        raise v1.ProvenanceFailure(f"{series_id}: locked 2026 timestamp detected")

    timestamps = sorted(int(ts) for ts in timestamps)
    timestamp_counts = Counter(timestamps)
    raw_duplicate_count = sum(c - 1 for c in timestamp_counts.values() if c > 1)

    mapped: list[tuple[int, int, int, bool]] = []
    for ts in timestamps:
        slot, offset, ambiguous = nearest_slot(ts, cadence_ms)
        mapped.append((ts, slot, offset, ambiguous))

    slot_counts = Counter(slot for _, slot, _, _ in mapped)
    abs_offsets = sorted(abs(offset) for _, _, offset, _ in mapped)

    def quantile(q: float) -> int | None:
        if not abs_offsets:
            return None
        idx = min(len(abs_offsets) - 1, int(round((len(abs_offsets) - 1) * q)))
        return abs_offsets[idx]

    months: dict[str, Any] = {}
    complete_months: list[str] = []
    for month in month_keys():
        start_ms, end_ms = month_bounds(month)
        expected_slots = list(range(start_ms, end_ms, cadence_ms))
        expected_set = set(expected_slots)

        month_mapped = [row for row in mapped if start_ms <= row[0] < end_ms]
        observed_slots = [slot for _, slot, _, _ in month_mapped if start_ms <= slot < end_ms]
        observed_slot_counts = Counter(observed_slots)
        observed_set = set(observed_slots)

        missing_slots = sorted(expected_set - observed_set)
        collision_slots = sorted(slot for slot, count in observed_slot_counts.items() if count > 1)
        boundary_mapped_out = [
            {"timestamp_ms": ts, "mapped_slot_ms": slot}
            for ts, slot, _, _ in month_mapped
            if not (start_ms <= slot < end_ms)
        ]
        ambiguous_count = sum(1 for _, _, _, ambiguous in month_mapped if ambiguous)
        month_abs_offsets = [abs(offset) for _, slot, offset, _ in month_mapped if start_ms <= slot < end_ms]

        complete = (
            len(missing_slots) == 0
            and len(collision_slots) == 0
            and len(boundary_mapped_out) == 0
            and ambiguous_count == 0
            and len(month_mapped) == len(expected_slots)
        )
        if complete:
            complete_months.append(month)

        months[month] = {
            "expected_slot_count": len(expected_slots),
            "raw_record_count": len(month_mapped),
            "unique_observed_slot_count": len(observed_set),
            "missing_slot_count": len(missing_slots),
            "collision_slot_count": len(collision_slots),
            "boundary_mapped_out_count": len(boundary_mapped_out),
            "ambiguous_mapping_count": ambiguous_count,
            "max_abs_offset_ms": max(month_abs_offsets) if month_abs_offsets else None,
            "complete_by_unique_slot_occupancy": complete,
            "missing_slots_first_20_utc": [utc_iso(x) for x in missing_slots[:20]],
            "collision_slots_first_20_utc": [utc_iso(x) for x in collision_slots[:20]],
        }

    return {
        "series_id": series_id,
        "cadence_ms": cadence_ms,
        "record_count": len(timestamps),
        "unique_timestamp_count": len(timestamp_counts),
        "raw_duplicate_timestamp_count": raw_duplicate_count,
        "first_timestamp_utc": utc_iso(timestamps[0]) if timestamps else None,
        "last_timestamp_utc": utc_iso(timestamps[-1]) if timestamps else None,
        "timestamp_sha256": sha256_json(timestamps),
        "slot_collision_count_total": sum(c - 1 for c in slot_counts.values() if c > 1),
        "ambiguous_mapping_count_total": sum(1 for _, _, _, a in mapped if a),
        "max_abs_offset_ms": max(abs_offsets) if abs_offsets else None,
        "p50_abs_offset_ms": quantile(0.50),
        "p95_abs_offset_ms": quantile(0.95),
        "p99_abs_offset_ms": quantile(0.99),
        "complete_full_month_count": len(complete_months),
        "complete_full_months": complete_months,
        "months": months,
        "economic_fields_summarized": False,
    }


def build_diagnostic() -> dict[str, Any]:
    if not v1.AUDIT_END_MS < v1.LOCKED_2026_START_MS:
        raise v1.ProvenanceFailure("frozen audit boundary reaches locked 2026")

    raw = {
        "BINANCE_BTCUSDT": v1.fetch_binance_funding("BTCUSDT", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "BINANCE_ETHUSDT": v1.fetch_binance_funding("ETHUSDT", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "HYPERLIQUID_BTC": v1.fetch_hyperliquid_funding("BTC", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
        "HYPERLIQUID_ETH": v1.fetch_hyperliquid_funding("ETH", v1.AUDIT_START_MS, v1.AUDIT_END_MS),
    }

    diagnostics: dict[str, Any] = {}
    for sid in sorted(raw):
        field = str(SERIES[sid]["timestamp_field"])
        timestamps = [int(row[field]) for row in raw[sid]]
        diagnostics[sid] = diagnose_timestamps(sid, timestamps)

    month_sets = [set(diagnostics[sid]["complete_full_months"]) for sid in sorted(diagnostics)]
    common = sorted(set.intersection(*month_sets))

    receipt = {
        "schema_version": "0.3",
        "lab_id": v1.LAB_ID,
        "diagnostic_id": DIAGNOSTIC_ID,
        "classification": "SLOT_OCCUPANCY_PROVENANCE_DIAGNOSTIC_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "DIAGNOSTIC_COMPLETE",
        "mapping_rule": "NEAREST_SCHEDULED_SLOT_UNIQUE_OCCUPANCY_NO_ECONOMIC_VALUES",
        "mapping_ambiguity_rule": "EXACT_HALF_CADENCE_IS_AMBIGUOUS_AND_FAILS_MONTH",
        "v01_changed": False,
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "series": diagnostics,
        "common_complete_full_month_count": len(common),
        "common_complete_full_months": common,
        "decision": "SLOT_COVERAGE_EXISTS_REVIEW_BEFORE_V01_AMENDMENT" if common else "NO_COMMON_COMPLETE_SLOT_MONTH",
    }
    receipt["diagnostic_sha256"] = sha256_json(receipt)
    return receipt


def main() -> None:
    output = Path(os.environ.get(
        "PREFREEZE_SLOT_DIAGNOSTIC_RECEIPT",
        "CROSS_VENUE_FUNDING_BASIS_SLOT_DIAGNOSTIC_V03_RECEIPT.json",
    ))
    receipt = build_diagnostic()
    output.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": receipt["status"],
        "classification": receipt["classification"],
        "locked_2026_accessed": receipt["locked_2026_accessed"],
        "carry_computed": receipt["carry_computed"],
        "pnl_computed": receipt["pnl_computed"],
        "common_complete_full_month_count": receipt["common_complete_full_month_count"],
        "common_complete_full_months": receipt["common_complete_full_months"],
        "decision": receipt["decision"],
        "diagnostic_sha256": receipt["diagnostic_sha256"],
    }, sort_keys=True))

    for sid, d in receipt["series"].items():
        print(json.dumps({
            "series_id": sid,
            "record_count": d["record_count"],
            "complete_full_month_count": d["complete_full_month_count"],
            "max_abs_offset_ms": d["max_abs_offset_ms"],
            "p99_abs_offset_ms": d["p99_abs_offset_ms"],
            "slot_collision_count_total": d["slot_collision_count_total"],
            "ambiguous_mapping_count_total": d["ambiguous_mapping_count_total"],
        }, sort_keys=True))


if __name__ == "__main__":
    main()

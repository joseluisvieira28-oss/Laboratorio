from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))

MODULE_PATH = RESEARCH / "cross_venue_funding_basis_provenance_slots_v04.py"
SPEC = importlib.util.spec_from_file_location("cvfb_slots_v04", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_nearest_slot_absorbs_small_timestamp_jitter_without_changing_slot():
    hour = mod.HYPERLIQUID_INTERVAL_MS
    base = 1704067200000
    assert mod.nearest_nominal_slot(base + 93, hour) == (base, 93)
    assert mod.nearest_nominal_slot(base - 250, hour) == (base, -250)


def test_nearest_slot_fails_if_assignment_is_ambiguous():
    hour = mod.HYPERLIQUID_INTERVAL_MS
    base = 1704067200000
    with pytest.raises(mod.SlotNormalizationFailure):
        mod.nearest_nominal_slot(base + hour // 2, hour)


def test_binance_interval_metadata_is_frozen_at_eight_hours():
    mod.validate_binance_interval_metadata([
        {"funding_interval_hours": "8"},
        {"funding_interval_hours": 8},
    ])
    with pytest.raises(mod.SlotNormalizationFailure):
        mod.validate_binance_interval_metadata([{"funding_interval_hours": "4"}])


def test_complete_hourly_month_passes_despite_positive_jitter():
    start, end = mod._month_bounds_ms("2024-01")
    rows = []
    slot = start
    while slot < end:
        rows.append({"time": slot + 137})
        slot += mod.HYPERLIQUID_INTERVAL_MS
    audit = mod.slot_coverage_audit(
        series_id="HYPERLIQUID_BTC",
        rows=rows,
        timestamp_field="time",
        interval_ms=mod.HYPERLIQUID_INTERVAL_MS,
    )
    assert "2024-01" in audit["eligible_full_months"]
    diag = audit["month_diagnostics"]["2024-01"]
    assert diag["missing_slot_count"] == 0
    assert diag["duplicate_slot_count"] == 0
    assert diag["observed_unique_slot_count"] == 31 * 24
    assert diag["max_abs_slot_jitter_ms"] == 137


def test_missing_slot_remains_fail_closed_after_normalization():
    start, end = mod._month_bounds_ms("2024-01")
    rows = []
    slot = start
    i = 0
    while slot < end:
        if i != 100:
            rows.append({"time": slot + 211})
        slot += mod.HYPERLIQUID_INTERVAL_MS
        i += 1
    audit = mod.slot_coverage_audit(
        series_id="HYPERLIQUID_BTC",
        rows=rows,
        timestamp_field="time",
        interval_ms=mod.HYPERLIQUID_INTERVAL_MS,
    )
    assert "2024-01" not in audit["eligible_full_months"]
    assert audit["month_diagnostics"]["2024-01"]["missing_slot_count"] == 1


def test_duplicate_slot_remains_fail_closed():
    start, end = mod._month_bounds_ms("2024-01")
    rows = []
    slot = start
    while slot < end:
        rows.append({"time": slot + 100})
        slot += mod.HYPERLIQUID_INTERVAL_MS
    rows.append({"time": start + 200})
    audit = mod.slot_coverage_audit(
        series_id="HYPERLIQUID_BTC",
        rows=rows,
        timestamp_field="time",
        interval_ms=mod.HYPERLIQUID_INTERVAL_MS,
    )
    assert "2024-01" not in audit["eligible_full_months"]
    assert audit["month_diagnostics"]["2024-01"]["duplicate_slot_count"] == 1


def test_complete_binance_month_requires_exact_three_slots_per_day():
    start, end = mod._month_bounds_ms("2024-02")
    rows = []
    slot = start
    while slot < end:
        rows.append({"fundingTime": slot + 26, "funding_interval_hours": "8"})
        slot += mod.BINANCE_INTERVAL_MS
    audit = mod.slot_coverage_audit(
        series_id="BINANCE_BTCUSDT",
        rows=rows,
        timestamp_field="fundingTime",
        interval_ms=mod.BINANCE_INTERVAL_MS,
    )
    assert "2024-02" in audit["eligible_full_months"]
    assert audit["month_diagnostics"]["2024-02"]["expected_slot_count"] == 29 * 3


def test_common_month_intersection_does_not_use_economic_values():
    audits = {
        "BINANCE_BTCUSDT": {"eligible_full_months": ["2024-01", "2024-02"]},
        "BINANCE_ETHUSDT": {"eligible_full_months": ["2024-01", "2024-02"]},
        "HYPERLIQUID_BTC": {"eligible_full_months": ["2024-02"]},
        "HYPERLIQUID_ETH": {"eligible_full_months": ["2024-02"]},
    }
    assert mod._common_months(audits) == ["2024-02"]

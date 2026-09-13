from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.mve_cpi_family_01_validation_runner_v01 import (
    daily_object,
    evaluate_asset,
    event_times_utc_ms,
    load_active_authorization,
    normalize_binance_timestamp_ms,
)
from decimal import Decimal


VALIDATION_IDS = [
    "US_CPI_2025-01-15", "US_CPI_2025-02-12", "US_CPI_2025-03-12",
    "US_CPI_2025-04-10", "US_CPI_2025-05-13", "US_CPI_2025-06-11",
    "US_CPI_2025-07-15", "US_CPI_2025-08-12",
]


def test_preparation_is_inert_without_active_authorization(tmp_path: Path):
    missing = tmp_path / "missing_authorization.json"
    with pytest.raises(PermissionError):
        load_active_authorization(missing)

    inactive = tmp_path / "inactive_authorization.json"
    inactive.write_text(json.dumps({
        "document_type": "MVE_CPI_FAMILY_01_DATA_ACCESS_AUTHORIZATION_V01",
        "status": "TEMPLATE_NOT_AUTHORIZED",
        "authorization_active": False,
        "hypothesis_id": "MVE-CPI-FAMILY-01",
    }), encoding="utf-8")
    with pytest.raises(PermissionError):
        load_active_authorization(inactive)


def test_2025_new_york_dst_conversion_is_explicit():
    jan_entry, _ = event_times_utc_ms("2025-01-15")
    jul_entry, _ = event_times_utc_ms("2025-07-15")
    assert jan_entry == 1736947860000  # 13:31 UTC, EST
    assert jul_entry == 1752582660000  # 12:31 UTC, EDT


def test_microsecond_binance_timestamps_normalize_to_ms():
    assert normalize_binance_timestamp_ms(1736947860000000) == 1736947860000
    assert normalize_binance_timestamp_ms(1736947860000) == 1736947860000
    with pytest.raises(RuntimeError):
        normalize_binance_timestamp_ms(1736947860000001)


def test_scope_blocks_other_years_and_symbols_without_network():
    obj = daily_object("BTCUSDT", "US_CPI_2025-01-15", VALIDATION_IDS)
    assert obj["archive_url"].endswith("/BTCUSDT/1m/BTCUSDT-1m-2025-01-15.zip")
    with pytest.raises(PermissionError):
        daily_object("SOLUSDT", "US_CPI_2025-01-15", VALIDATION_IDS)
    with pytest.raises(PermissionError):
        daily_object("BTCUSDT", "US_CPI_2024-12-11", VALIDATION_IDS)
    with pytest.raises(PermissionError):
        daily_object("BTCUSDT", "US_CPI_2026-01-13", VALIDATION_IDS)


def test_low_n_mve_pass_rule_is_exactly_five_of_seven_plus_positive_economics():
    passing = evaluate_asset([
        Decimal("20"), Decimal("20"), Decimal("20"), Decimal("20"), Decimal("20"),
        Decimal("-1"), Decimal("-1"),
    ])
    assert passing["criteria"]["mean_aligned_net_bps_gt_0"] is True
    assert passing["criteria"]["median_aligned_gross_bps_gt_0"] is True
    assert passing["criteria"]["positive_aligned_gross_events_gte_5_of_7"] is True
    assert passing["pass"] is True

    too_few_positive = evaluate_asset([
        Decimal("100"), Decimal("100"), Decimal("100"), Decimal("100"),
        Decimal("-1"), Decimal("-1"), Decimal("-1"),
    ])
    assert too_few_positive["positive_aligned_gross_event_count"] == 4
    assert too_few_positive["pass"] is False

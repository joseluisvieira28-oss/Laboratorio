from __future__ import annotations

from decimal import Decimal
from math import comb

from research.news_shock_lab_v03a_discovery_runner_v01 import (
    EXPECTED_PERMUTATIONS,
    daily_object,
    event_times_utc_ms,
    exact_fixed_count_p_value,
    evaluate_asset,
    validate_authority_chain,
)


def test_authority_chain_is_current_and_discovery_only():
    _, pre, auth = validate_authority_chain()
    assert pre["cohorts"]["discovery"]["event_count"] == 27
    assert auth["authorized_scope"]["event_count"] == 27
    assert auth["still_locked"]["2025_01_through_2025_08_validation_market_data"] is True
    assert auth["still_locked"]["2026_all_market_data"] is True


def test_exact_frozen_permutation_cardinality():
    assert comb(21, 11) == EXPECTED_PERMUTATIONS == 352716


def test_new_york_dst_conversion_is_frozen_and_correct():
    entry, exit_ = event_times_utc_ms("2022-02-10")
    assert entry == 1644499860000  # 13:31 UTC, EST
    assert exit_ == 1644500700000  # 13:45 UTC
    entry, exit_ = event_times_utc_ms("2024-08-14")
    assert entry == 1723638660000  # 12:31 UTC, EDT
    assert exit_ == 1723639500000  # 12:45 UTC


def test_daily_object_blocks_protected_year_and_alt_symbol():
    obj = daily_object("BTCUSDT", "2024-09-11")
    assert obj["archive_url"].endswith("/BTCUSDT/1m/BTCUSDT-1m-2024-09-11.zip")
    try:
        daily_object("BTCUSDT", "2025-01-15")
    except PermissionError:
        pass
    else:
        raise AssertionError("2025 archive construction must be blocked")
    try:
        daily_object("SOLUSDT", "2024-09-11")
    except PermissionError:
        pass
    else:
        raise AssertionError("alternate asset must be blocked")


def test_exact_permutation_small_known_case():
    gross = [Decimal("3"), Decimal("1"), Decimal("-2")]
    signs = [1, -1, -1]
    result = exact_fixed_count_p_value(gross, signs, hotter_count=1, expected_permutations=3)
    assert result["assignment_count"] == 3
    assert result["p_value"] == Decimal("1")


def test_asset_survival_requires_all_four_frozen_criteria():
    signs = [1] * 11 + [-1] * 10
    gross = [Decimal("-40")] * 11 + [Decimal("40")] * 10
    result = evaluate_asset(gross, signs)
    assert result["criteria"]["mean_aligned_net_bps_gt_0"] is True
    assert result["criteria"]["median_aligned_gross_bps_gt_0"] is True
    assert result["criteria"]["every_leave_one_out_mean_aligned_net_bps_gt_0"] is True
    assert result["criteria"]["exact_one_sided_p_lte_0_05"] is True
    assert result["pass"] is True

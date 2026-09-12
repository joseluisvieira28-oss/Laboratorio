from __future__ import annotations

import importlib.util
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))
MODULE = RESEARCH / "cross_venue_funding_basis_discovery_run01_rate_screen_v01.py"
SPEC = importlib.util.spec_from_file_location("cvfb_discovery_run01", MODULE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_frozen_round_trip_fee_is_exact():
    assert mod.TOTAL_ROUND_TRIP_FEE == Decimal("0.00190")


def test_primary_funding_signs_long_binance_short_hyperliquid():
    b = [{"fundingRate": "0.001"}, {"fundingRate": "-0.0002"}]
    h = [{"fundingRate": "0.0015"}, {"fundingRate": "0.0001"}]
    out = mod.compute_asset_screen(b, h, Decimal("0"))
    assert Decimal(out["binance_long_funding_component"]) == Decimal("-0.0008")
    assert Decimal(out["hyperliquid_short_funding_component"]) == Decimal("0.0016")
    assert Decimal(out["gross_primary_funding_carry"]) == Decimal("0.0008")


def test_opportunity_cost_uses_strictly_prior_observation():
    obs = [
        (date(2024, 8, 30), Decimal("5.00")),
        (date(2024, 9, 2), Decimal("1.00")),
    ]
    value, days = mod.opportunity_cost(
        obs,
        start=date(2024, 9, 1),
        end_exclusive=date(2024, 9, 3),
        capital=Decimal("1.50"),
    )
    expected = Decimal("1.50") * Decimal("0.05") / Decimal("365") * Decimal("2")
    assert days == 2
    assert value == expected


def test_opportunity_cost_fails_without_prior_observation():
    obs = [(date(2024, 9, 1), Decimal("5"))]
    try:
        mod.opportunity_cost(obs, start=date(2024, 9, 1), end_exclusive=date(2024, 9, 2))
    except mod.DiscoveryFailure:
        pass
    else:
        raise AssertionError("must fail closed without strictly prior benchmark observation")


def test_rate_screen_is_not_full_mechanism_classification():
    out = mod.compute_asset_screen(
        [{"fundingRate": "0"}],
        [{"fundingRate": "0.10"}],
        Decimal("0"),
    )
    assert out["net_positive"] is True
    assert "REPLICATION_SUPPORTS_MECHANISM" not in out
    assert "edge" not in out


def test_expected_months_are_frozen_2024_09_through_2025_12():
    assert mod.EXPECTED_MONTHS[0] == "2024-09"
    assert mod.EXPECTED_MONTHS[-1] == "2025-12"
    assert len(mod.EXPECTED_MONTHS) == 16


def test_window_cannot_reach_2026_market_data():
    assert mod.END_MS < mod.v1.LOCKED_2026_START_MS
    assert mod.END_DATE_EXCLUSIVE == date(2026, 1, 1)


def test_filter_window_rejects_empty_data():
    try:
        mod.filter_window([], "time")
    except mod.DiscoveryFailure:
        pass
    else:
        raise AssertionError("empty Discovery window must fail closed")

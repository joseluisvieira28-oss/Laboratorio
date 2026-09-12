from __future__ import annotations

import importlib.util
import sys
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
if str(RESEARCH) not in sys.path:
    sys.path.insert(0, str(RESEARCH))
MODULE = RESEARCH / "cross_venue_funding_basis_discovery_run02_basis_component_v01.py"
SPEC = importlib.util.spec_from_file_location("cvfb_run02", MODULE)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def test_frozen_boundaries_stay_before_2026():
    assert mod.ENTRY_MS == 1725148800000
    assert mod.EXIT_OPEN_MS == 1767222000000
    assert mod.EXIT_END_MS == 1767225599999
    assert mod.EXIT_END_MS < mod.LOCKED_2026_MS


def test_equal_base_quantity_normalization_is_symmetric():
    out = mod.compute_basis_component(
        Decimal("100"), Decimal("110"), Decimal("102"), Decimal("108")
    )
    q = Decimal(out["equal_base_quantity"])
    assert q == Decimal("2") / Decimal("202")
    assert Decimal(out["total_entry_notional"]) == Decimal("2")
    assert Decimal(out["normalized_immobilized_capital"]) == Decimal("1.50")


def test_basis_component_signs_long_binance_short_hyperliquid():
    out = mod.compute_basis_component(
        Decimal("100"), Decimal("110"), Decimal("100"), Decimal("105")
    )
    assert Decimal(out["binance_long_price_pnl"]) > 0
    assert Decimal(out["hyperliquid_short_price_pnl"]) < 0
    assert Decimal(out["cross_venue_basis_price_component"]) > 0


def test_common_market_move_cancels_when_venues_move_identically():
    out = mod.compute_basis_component(
        Decimal("100"), Decimal("120"), Decimal("100"), Decimal("120")
    )
    assert Decimal(out["cross_venue_basis_price_component"]) == Decimal("0")


def test_nonpositive_boundary_price_fails_closed():
    try:
        mod.compute_basis_component(Decimal("0"), Decimal("1"), Decimal("1"), Decimal("1"))
    except mod.DiscoveryFailure:
        pass
    else:
        raise AssertionError("nonpositive price must fail closed")


def test_run02_does_not_embed_full_mechanism_label_in_component():
    out = mod.compute_basis_component(
        Decimal("100"), Decimal("90"), Decimal("100"), Decimal("110")
    )
    assert "REPLICATION_SUPPORTS_MECHANISM" not in out
    assert "REPLICATION_FAILS_MECHANISM" not in out
    assert "edge" not in out

from __future__ import annotations

import copy
import json
import sys
from decimal import Decimal
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
sys.path.insert(0, str(RESEARCH))

import cross_venue_funding_basis_prefreeze_v01 as pf  # noqa: E402


def _load(name: str):
    return json.loads((RESEARCH / name).read_text(encoding="utf-8"))


def test_full_prefreeze_files_pass_and_keep_discovery_blocked():
    receipt = pf.validate_prefreeze_files(RESEARCH)
    assert receipt["status"] == pf.PASS_LABEL
    assert receipt["discovery"] == "BLOCKED"
    assert receipt["edge"] == "UNPROVEN"
    assert receipt["market_outcomes_evaluated"] is False


def test_scope_is_exactly_btc_eth_and_orientation_is_fixed():
    authority = _load("CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_AUTHORITY_V01.json")
    assert authority["asset_scope_frozen"] == ["BTC", "ETH"]
    assert authority["primary_candidate_orientation_frozen"] == "LONG_BINANCE_PERP_SHORT_HYPERLIQUID_PERP"
    assert authority["venues"]["binance"]["role_in_primary_baseline"] == "LONG_PERPETUAL"
    assert authority["venues"]["hyperliquid"]["role_in_primary_baseline"] == "SHORT_PERPETUAL"
    assert authority["symmetric_reverse_orientation"] == "DIAGNOSTIC_CONTROL_ONLY_NOT_ELIGIBLE_TO_RESCUE_PRIMARY"


def test_positive_funding_long_pays_and_short_receives_without_annualization():
    long_cf = pf.funding_cashflow(
        venue="BINANCE_USDM",
        side="LONG",
        funding_rate=Decimal("0.0001"),
        funding_notional=Decimal("100000"),
    )
    short_cf = pf.funding_cashflow(
        venue="HYPERLIQUID",
        side="SHORT",
        funding_rate=Decimal("0.0001"),
        funding_notional=Decimal("100000"),
    )
    assert long_cf.cashflow == Decimal("-10.0000")
    assert short_cf.cashflow == Decimal("10.0000")


def test_basis_pnl_uses_both_legs_and_equal_base_quantity():
    pnl = pf.consolidated_basis_pnl(
        base_quantity=Decimal("1"),
        binance_entry=Decimal("100"),
        binance_exit=Decimal("110"),
        hyperliquid_entry=Decimal("101"),
        hyperliquid_exit=Decimal("108"),
    )
    assert pnl == Decimal("3")


def test_common_window_start_is_coverage_only_and_never_2026():
    months = {
        "BINANCE_BTCUSDT": ["2023-11", "2023-12", "2026-01"],
        "BINANCE_ETHUSDT": ["2023-11", "2023-12", "2026-01"],
        "HYPERLIQUID_BTC": ["2023-12", "2026-01"],
        "HYPERLIQUID_ETH": ["2023-12", "2026-01"],
    }
    assert pf.deterministic_common_window_start(months) == "2023-12"


def test_2026_lock_violation_fails_closed():
    contract = _load("CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_CONTRACT_V01.json")
    bad = copy.deepcopy(contract)
    bad["data_partition_policy"]["locked_2026_market_data"] = "ALLOW"
    with pytest.raises(pf.PreFreezeViolation):
        pf.validate_contract(bad)


def test_discovery_authorization_violation_fails_closed():
    contract = _load("CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_CONTRACT_V01.json")
    bad = copy.deepcopy(contract)
    for gate in bad["pre_freeze_gates"]:
        if gate["gate"] == "G12_DISCOVERY_AUTHORIZATION":
            gate["status"] = "PASS"
    with pytest.raises(pf.PreFreezeViolation):
        pf.validate_contract(bad)


def test_maker_fill_cannot_be_guaranteed():
    contract = _load("CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_CONTRACT_V01.json")
    bad = copy.deepcopy(contract)
    bad["execution_cost_policy"]["maker_fill_guarantee"] = True
    with pytest.raises(pf.PreFreezeViolation):
        pf.validate_contract(bad)


def test_cross_venue_margin_netting_is_forbidden():
    contract = _load("CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_CONTRACT_V01.json")
    bad = copy.deepcopy(contract)
    bad["ledger_model"]["cross_venue_profit_netting_for_liquidation"] = True
    with pytest.raises(pf.PreFreezeViolation):
        pf.validate_contract(bad)


def test_instant_collateral_transfer_is_forbidden():
    contract = _load("CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_CONTRACT_V01.json")
    bad = copy.deepcopy(contract)
    bad["ledger_model"]["instantaneous_collateral_transfer"] = True
    with pytest.raises(pf.PreFreezeViolation):
        pf.validate_contract(bad)


def test_source_inventory_contains_primary_official_funding_sources_and_no_outcomes():
    matrix = _load("CROSS_VENUE_FUNDING_BASIS_LAB_SOURCE_PROVENANCE_MATRIX_V01.json")
    pf.validate_source_matrix(matrix)
    ids = {item["source_id"] for item in matrix["sources"]}
    assert "BINANCE_USDM_FUNDING_RATE_HISTORY" in ids
    assert "HYPERLIQUID_FUNDING_HISTORY" in ids
    assert matrix["economic_outcomes_inspected"] is False


def test_authority_forbids_trading_mutation_and_outcome_metrics():
    authority = _load("CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_AUTHORITY_V01.json")
    pf.validate_authority(authority)
    assert authority["paper_trading_authorized"] is False
    assert authority["live_trading_authorized"] is False
    assert authority["exchange_mutation_authorized"] is False
    assert "APR_or_APY_of_this_lab_dataset" in authority["forbidden_outputs_during_pre_freeze"]
    assert "best_threshold" in authority["forbidden_outputs_during_pre_freeze"]


def test_bad_scope_fails_closed():
    authority = _load("CROSS_VENUE_FUNDING_BASIS_LAB_PREFREEZE_AUTHORITY_V01.json")
    bad = copy.deepcopy(authority)
    bad["asset_scope_frozen"].append("SOL")
    with pytest.raises(pf.PreFreezeViolation):
        pf.validate_authority(bad)

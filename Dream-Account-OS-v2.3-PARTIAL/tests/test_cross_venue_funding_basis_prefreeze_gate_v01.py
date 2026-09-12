from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
MODULE_PATH = RESEARCH / "cross_venue_funding_basis_prefreeze_gate_v01.py"
SPEC = importlib.util.spec_from_file_location("cvfb_gate", MODULE_PATH)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


def base_policy():
    return json.loads((RESEARCH / "CROSS_VENUE_FUNDING_BASIS_LAB_COST_CAPITAL_EXECUTION_FREEZE_V01.json").read_text(encoding="utf-8"))


def valid_receipt():
    series = {}
    for sid in ("BINANCE_BTCUSDT", "BINANCE_ETHUSDT", "HYPERLIQUID_BTC", "HYPERLIQUID_ETH"):
        series[sid] = {"conflicting_duplicate_timestamps": []}
    return {
        "lab_id": mod.LAB_ID,
        "classification": "PROVENANCE_ONLY_NOT_ECONOMIC_DISCOVERY",
        "status": "PASS",
        "locked_2026_accessed": False,
        "mexc_accessed": False,
        "authenticated_account_data_used": False,
        "exchange_mutation_used": False,
        "funding_rate_values_summarized": False,
        "carry_computed": False,
        "apr_apy_computed": False,
        "pnl_computed": False,
        "signals_computed": False,
        "series": series,
        "replication_window_provenance_only": {
            "first_common_full_month": "2024-01",
            "last_common_full_month": "2025-12"
        },
    }


def test_policy_validates_without_outcomes():
    mod.validate_policy(base_policy())


def test_fee_baseline_is_taker_and_discount_free():
    p = base_policy()["G06_FEES"]
    assert p["primary_order_style"] == "TAKER"
    assert p["discounts_assumed"] is False
    assert p["maker_rebate_assumed"] is False


def test_execution_claim_is_fail_closed():
    p = base_policy()["G07_EXECUTION_DATA"]
    assert p["historical_executable_pnl_authorized"] is False
    assert p["status"] == "UNOBSERVABLE_HISTORICALLY_FOR_EXECUTABLE_RETURN_CLAIM"


def test_margin_is_venue_separate_and_no_magic_topup():
    p = base_policy()["G08_MARGIN_CAPITAL"]
    assert p["primary_leverage_per_venue"] == "2.0x"
    assert p["cross_venue_profit_netting_for_liquidation"] is False
    assert p["instantaneous_cross_venue_transfer"] is False
    assert p["emergency_cross_venue_topup_in_primary_baseline"] is False


def test_opportunity_cost_is_frozen_without_lookahead():
    p = base_policy()["G09_OPPORTUNITY_COST"]
    assert p["benchmark_series"] == "DGS3MO"
    assert p["day_count"] == "ACT_365"
    assert p["benchmark_switch_after_outcomes"] is False


def test_missing_provenance_keeps_discovery_blocked():
    out = mod.evaluate(RESEARCH, None)
    assert out["status"] == "DISCOVERY_BLOCKED_PREFREEZE_INCOMPLETE"
    assert out["discovery_authorized"] is False
    assert "G03_FUNDING_REGIMES" in out["blockers"]
    assert "G04_RAW_PROVENANCE" in out["blockers"]
    assert "G10_REPLICATION_PARTITION_MATERIALIZED" in out["blockers"]


def test_valid_provenance_only_makes_lab_ready_to_request_not_authorized(tmp_path):
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(valid_receipt()), encoding="utf-8")
    out = mod.evaluate(RESEARCH, receipt_path)
    assert out["status"] == "READY_TO_REQUEST_SEPARATE_DISCOVERY_AUTHORIZATION"
    assert out["discovery_authorized"] is False
    assert out["blockers"] == []
    assert out["replication_window_provenance_only"]["first_common_full_month"] == "2024-01"


def test_receipt_with_2026_window_fails_closed(tmp_path):
    r = valid_receipt()
    r["replication_window_provenance_only"]["last_common_full_month"] = "2026-01"
    p = tmp_path / "receipt.json"
    p.write_text(json.dumps(r), encoding="utf-8")
    with pytest.raises(mod.GateViolation):
        mod.evaluate(RESEARCH, p)


def test_receipt_with_outcome_summary_fails_closed(tmp_path):
    r = valid_receipt()
    r["carry_computed"] = True
    p = tmp_path / "receipt.json"
    p.write_text(json.dumps(r), encoding="utf-8")
    with pytest.raises(mod.GateViolation):
        mod.evaluate(RESEARCH, p)


def test_receipt_with_mexc_access_fails_closed(tmp_path):
    r = valid_receipt()
    r["mexc_accessed"] = True
    p = tmp_path / "receipt.json"
    p.write_text(json.dumps(r), encoding="utf-8")
    with pytest.raises(mod.GateViolation):
        mod.evaluate(RESEARCH, p)


def test_leverage_sensitivity_cannot_rescue_primary():
    p = base_policy()["G08_MARGIN_CAPITAL"]
    assert p["diagnostic_leverage_sensitivities"] == ["1.0x", "3.0x"]
    assert p["sensitivity_cannot_replace_primary"] is True

"""Outcome-blind final pre-freeze gate engine for Cross-Venue Funding & Basis Lab V0.1.

This module never computes funding carry, APR/APY, PnL, rankings, thresholds, or signals.
It determines whether the laboratory is READY TO REQUEST a separate Discovery authorization.
It does not itself authorize Discovery or trading.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

LAB_ID = "CROSS_VENUE_FUNDING_BASIS_LAB_V01"
EDGE_STATUS = "UNPROVEN"
LOCKED_2026 = True
MEXC_2025_LOCKED = True

class GateViolation(RuntimeError):
    pass


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GateViolation(message)


def _load(path: Path) -> Mapping[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    _require(isinstance(value, dict), f"expected JSON object: {path}")
    return value


def _fingerprint(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def validate_policy(policy: Mapping[str, Any]) -> None:
    _require(policy.get("lab_id") == LAB_ID, "wrong lab id")
    _require(policy.get("phase") == "PRE_FREEZE", "wrong phase")
    _require(policy.get("economic_outcomes_inspected") is False, "economic outcomes were inspected")
    _require(policy.get("edge_status") == EDGE_STATUS, "edge status drift")
    _require(policy.get("discovery_authorized") is False, "Discovery cannot be pre-authorized")
    _require(policy.get("trading_authorized") is False, "trading cannot be authorized")

    g06 = policy["G06_FEES"]
    _require(g06["primary_order_style"] == "TAKER", "primary fees must be taker")
    _require(g06["discounts_assumed"] is False, "discounts forbidden")
    _require(g06["maker_rebate_assumed"] is False, "maker rebates forbidden in baseline")
    _require(g06["binance_usdm_conservative_taker_rate_decimal"] == "0.00050", "Binance conservative fee drift")
    _require(g06["hyperliquid_perps_conservative_taker_rate_decimal"] == "0.00045", "Hyperliquid conservative fee drift")
    _require("BLOCKED" in g06["historical_exactness_rule"].upper(), "historical fee exactness must block executable claim")

    g07 = policy["G07_EXECUTION_DATA"]
    _require(g07["status"] == "UNOBSERVABLE_HISTORICALLY_FOR_EXECUTABLE_RETURN_CLAIM", "G07 must remain fail-closed")
    _require(g07["historical_executable_pnl_authorized"] is False, "historical executable PnL opened")
    forbidden = set(g07["forbidden"])
    _require("MID_PRICE_FILL" in forbidden and "GUARANTEED_MAKER_FILL" in forbidden, "execution guard missing")

    g08 = policy["G08_MARGIN_CAPITAL"]
    _require(g08["primary_leverage_per_venue"] == "2.0x", "primary leverage drift")
    _require(g08["diagnostic_leverage_sensitivities"] == ["1.0x", "3.0x"], "leverage sensitivities drift")
    _require(g08["sensitivity_cannot_replace_primary"] is True, "sensitivity could rescue primary")
    _require(g08["cross_venue_profit_netting_for_liquidation"] is False, "cross-venue margin netting opened")
    _require(g08["instantaneous_cross_venue_transfer"] is False, "instant transfer opened")
    _require(g08["emergency_cross_venue_topup_in_primary_baseline"] is False, "emergency topup opened")
    _require(g08["opening_initial_collateral_fraction_of_leg_notional"] == "0.50", "initial collateral drift")
    _require(g08["additional_prefunded_reserve_fraction_of_leg_notional"] == "0.25", "reserve drift")

    g09 = policy["G09_OPPORTUNITY_COST"]
    _require(g09["benchmark_series"] == "DGS3MO", "benchmark series drift")
    _require(g09["day_count"] == "ACT_365", "day count drift")
    _require(g09["benchmark_switch_after_outcomes"] is False, "benchmark switching opened")
    _require("Never" in g09["timestamp_rule"] or "never" in g09["timestamp_rule"], "look-ahead guard missing")

    g10 = policy["G10_REPLICATION_PARTITION_POLICY"]
    _require(g10["locked_2026"] is True, "2026 lock missing")
    _require(g10["mexc_2025_out_of_scope_and_locked"] is True, "MEXC lock missing")
    _require(g10["same_window_for_btc_and_eth"] is True, "symbol-specific window selection opened")
    _require(g10["outcome_dependent_exclusion_forbidden"] is True, "outcome-dependent exclusions opened")
    _require(g10["classification"] == "ADVERSARIAL_REPLICATION_ONLY_NOT_INDEPENDENT_CONFIRMATION", "replication classification drift")


def validate_provenance_receipt(receipt: Mapping[str, Any]) -> dict[str, Any]:
    _require(receipt.get("lab_id") == LAB_ID, "provenance receipt wrong lab")
    _require(receipt.get("classification") == "PROVENANCE_ONLY_NOT_ECONOMIC_DISCOVERY", "receipt is not provenance-only")
    _require(receipt.get("status") == "PASS", "provenance receipt did not PASS")
    _require(receipt.get("locked_2026_accessed") is False, "receipt accessed locked 2026")
    _require(receipt.get("mexc_accessed") is False, "receipt accessed MEXC")
    _require(receipt.get("authenticated_account_data_used") is False, "receipt used authenticated data")
    _require(receipt.get("exchange_mutation_used") is False, "receipt used exchange mutation")
    for key in ("funding_rate_values_summarized", "carry_computed", "apr_apy_computed", "pnl_computed", "signals_computed"):
        _require(receipt.get(key) is False, f"outcome boundary violated: {key}")
    window = receipt.get("replication_window_provenance_only", {})
    first = window.get("first_common_full_month")
    last = window.get("last_common_full_month")
    _require(isinstance(first, str) and isinstance(last, str), "replication window missing")
    _require(int(last[:4]) <= 2025, "replication window leaks into locked 2026")
    series = receipt.get("series", {})
    expected = {"BINANCE_BTCUSDT", "BINANCE_ETHUSDT", "HYPERLIQUID_BTC", "HYPERLIQUID_ETH"}
    _require(set(series) == expected, "provenance series scope drift")
    _require(all(not s.get("conflicting_duplicate_timestamps") for s in series.values()), "conflicting duplicate timestamps")
    return {"first_common_full_month": first, "last_common_full_month": last}


def evaluate(root: Path, provenance_receipt_path: Path | None = None) -> dict[str, Any]:
    policy_path = root / "CROSS_VENUE_FUNDING_BASIS_LAB_COST_CAPITAL_EXECUTION_FREEZE_V01.json"
    policy = _load(policy_path)
    validate_policy(policy)

    gate_states: dict[str, str] = {
        "G06_FEES": "PASS_POLICY_EXECUTABLE_CLAIM_BLOCKED_WITHOUT_DATE_MATCHED_FEE_PROVENANCE",
        "G07_EXECUTION_DATA": "UNOBSERVABLE_HISTORICALLY_FOR_EXECUTABLE_RETURN_CLAIM",
        "G08_MARGIN_CAPITAL": "PASS_SPEC_EXECUTABLE_LIQUIDATION_EXACTNESS_REQUIRES_DATE_MATCHED_MARGIN_PROVENANCE",
        "G09_OPPORTUNITY_COST": "PASS",
        "G10_REPLICATION_PARTITION_RULE": "PASS_RULE_WINDOW_NOT_YET_MATERIALIZED",
    }
    blockers: list[str] = []
    replication_window = None

    if provenance_receipt_path is None or not provenance_receipt_path.exists():
        gate_states["G03_FUNDING_REGIMES"] = "BLOCKED_PENDING_OUTCOME_BLIND_PROVENANCE_RECEIPT"
        gate_states["G04_RAW_PROVENANCE"] = "BLOCKED_PENDING_OUTCOME_BLIND_PROVENANCE_RECEIPT"
        gate_states["G10_REPLICATION_PARTITION_MATERIALIZED"] = "BLOCKED_PENDING_G03_G04"
        blockers.extend(["G03_FUNDING_REGIMES", "G04_RAW_PROVENANCE", "G10_REPLICATION_PARTITION_MATERIALIZED"])
    else:
        receipt = _load(provenance_receipt_path)
        replication_window = validate_provenance_receipt(receipt)
        gate_states["G03_FUNDING_REGIMES"] = "PASS_OBSERVED_SETTLEMENT_INTERVAL_AUDIT"
        gate_states["G04_RAW_PROVENANCE"] = "PASS_HASHED_COVERAGE_AUDIT"
        gate_states["G10_REPLICATION_PARTITION_MATERIALIZED"] = "PASS_PROVENANCE_ONLY_WINDOW_FROZEN"

    ready = not blockers
    status = "READY_TO_REQUEST_SEPARATE_DISCOVERY_AUTHORIZATION" if ready else "DISCOVERY_BLOCKED_PREFREEZE_INCOMPLETE"
    result = {
        "schema_version": "0.1",
        "lab_id": LAB_ID,
        "phase": "PRE_FREEZE",
        "status": status,
        "edge_status": EDGE_STATUS,
        "discovery_authorized": False,
        "paper_trading_authorized": False,
        "live_trading_authorized": False,
        "historical_executable_return_claim_authorized": False,
        "historical_mechanism_replication_classification": "ADVERSARIAL_REPLICATION_ONLY",
        "locked_2026": LOCKED_2026,
        "mexc_2025_locked": MEXC_2025_LOCKED,
        "economic_outcomes_inspected_by_gate_engine": False,
        "gate_states": gate_states,
        "blockers": blockers,
        "replication_window_provenance_only": replication_window,
        "policy_fingerprint": _fingerprint(policy),
        "next_action": "OBTAIN_OUTCOME_BLIND_G03_G04_PROVENANCE_RECEIPT" if blockers else "REQUEST_SEPARATE_DISCOVERY_AUTHORIZATION",
    }
    return result


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    candidate = here / "CROSS_VENUE_FUNDING_BASIS_PROVENANCE_SHAKEDOWN_V01_RECEIPT.json"
    result = evaluate(here, candidate if candidate.exists() else None)
    print(json.dumps(result, sort_keys=True))

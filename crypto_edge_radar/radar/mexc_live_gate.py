from __future__ import annotations

import json
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from typing import Any

EXECUTION_TOKEN = "CRYPTO_LAB_LIVE_EXECUTION_V0_2"
REQUIRED_STRATEGY = "ETF-CME-INSTFLOW-001"
REQUIRED_SYMBOL = "BTC_USDT"
CURRENT_PLACE_ORDER_PATH = "/api/v1/private/order/create"


class LiveExecutionGateError(RuntimeError):
    pass


def _load(path: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise LiveExecutionGateError(f"JSON object required: {path}")
    return payload


def _parse_utc(value: Any, field: str) -> datetime:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception as exc:
        raise LiveExecutionGateError(f"invalid {field}") from exc
    if dt.tzinfo is None:
        raise LiveExecutionGateError(f"{field} must be timezone-aware")
    return dt.astimezone(timezone.utc)


def _positive_float(value: Any, field: str) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError) as exc:
        raise LiveExecutionGateError(f"invalid {field}") from exc
    if not isfinite(out) or out <= 0:
        raise LiveExecutionGateError(f"invalid {field}")
    return out


def validate_futures_short_execution(
    *,
    authority_path: str,
    preflight_path: str,
    signal_path: str,
    risk_state_path: str,
    kill_switch_path: str = "KILL_SWITCH",
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now_utc = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    authority = _load(authority_path)
    preflight = _load(preflight_path)
    signal = _load(signal_path)
    risk_state = _load(risk_state_path)
    blockers: list[str] = []

    if Path(kill_switch_path).exists():
        blockers.append("KILL_SWITCH_PRESENT")

    # Candidate-specific immutable authority.
    if authority.get("status") != "ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY":
        blockers.append("ACTIVE_CANDIDATE_SPECIFIC_AUTHORITY_ABSENT")
    if authority.get("strategy_id") != REQUIRED_STRATEGY:
        blockers.append("AUTHORITY_STRATEGY_MISMATCH")
    if authority.get("exchange") != "MEXC":
        blockers.append("AUTHORITY_EXCHANGE_MISMATCH")
    if authority.get("contract") != REQUIRED_SYMBOL:
        blockers.append("AUTHORITY_CONTRACT_MISMATCH")
    if authority.get("direction") != "SHORT":
        blockers.append("FUTURES_EXECUTOR_ONLY_ACCEPTS_FROZEN_SHORT_DIRECTION")
    if authority.get("margin_mode") != "ISOLATED":
        blockers.append("AUTHORITY_MARGIN_NOT_ISOLATED")
    if authority.get("leverage") != 1:
        blockers.append("AUTHORITY_LEVERAGE_NOT_1X")
    if authority.get("auto_margin_add") != "OFF_REQUIRED":
        blockers.append("AUTHORITY_AUTO_MARGIN_ADD_NOT_OFF_REQUIRED")
    if authority.get("order_type") != "MARKET":
        blockers.append("AUTHORITY_ORDER_TYPE_NOT_MARKET")
    if authority.get("position_mode") != 1:
        blockers.append("AUTHORITY_POSITION_MODE_NOT_HEDGE")
    if authority.get("late_chase_allowed") is not False:
        blockers.append("AUTHORITY_LATE_CHASE_NOT_FORBIDDEN")
    if authority.get("max_simultaneous_positions") != 1:
        blockers.append("AUTHORITY_ONE_POSITION_CONSTRAINT_MISSING")
    if authority.get("api_place_order_path") != CURRENT_PLACE_ORDER_PATH:
        blockers.append("AUTHORITY_API_SCHEMA_NOT_CURRENT")
    if (
        authority.get("auto_margin_enforcement_mode")
        != "POST_FILL_IMMEDIATE_OFF__EMERGENCY_FLATTEN_IF_NOT_VERIFIED"
    ):
        blockers.append("AUTO_MARGIN_ENFORCEMENT_MODE_NOT_FROZEN")
    if authority.get("implementation_mapping_review_status") != "ACCEPTED_PRE_ORDER":
        blockers.append("IMPLEMENTATION_MAPPING_REVIEW_NOT_ACCEPTED")

    # Canonical signal identity and source health.
    signal_key = signal.get("immutable_signal_key")
    if not signal_key or signal_key != authority.get("signal_identity"):
        blockers.append("SIGNAL_IDENTITY_MISMATCH")
    if signal.get("strategy_id") != REQUIRED_STRATEGY:
        blockers.append("SIGNAL_STRATEGY_MISMATCH")
    if signal.get("signal_direction") != "SHORT":
        blockers.append("SIGNAL_DIRECTION_NOT_SHORT")
    if signal.get("canonical") is not True:
        blockers.append("SIGNAL_NOT_CANONICAL")
    if signal.get("source_healthy") is not True:
        blockers.append("SIGNAL_SOURCE_NOT_HEALTHY")
    if signal.get("radar_motor_healthy") is not True:
        blockers.append("RADAR_MOTOR_NOT_HEALTHY")
    if signal.get("information_safe_time_passed") is not True:
        blockers.append("INFORMATION_SAFE_TIME_NOT_PASSED")

    # Exchange authenticated preflight must be healthy, fresh and candidate-feasible.
    if preflight.get("pass") is not True or preflight.get("status") != "PASS":
        blockers.append("AUTHENTICATED_EXCHANGE_PREFLIGHT_NOT_PASS")
    candidate = (
        (preflight.get("candidate_feasibility") or {}).get(REQUIRED_STRATEGY) or {}
    )
    if candidate.get("pass") is not True:
        blockers.append("CANDIDATE_CAPITAL_FEASIBILITY_NOT_PASS")

    max_preflight_age = float(authority.get("max_preflight_age_seconds", 60))
    try:
        preflight_at = _parse_utc(preflight.get("checked_at_utc"), "preflight.checked_at_utc")
        if (now_utc - preflight_at).total_seconds() > max_preflight_age:
            blockers.append("AUTHENTICATED_PREFLIGHT_STALE")
        if preflight_at > now_utc:
            blockers.append("AUTHENTICATED_PREFLIGHT_FROM_FUTURE")
    except LiveExecutionGateError:
        blockers.append("AUTHENTICATED_PREFLIGHT_TIME_INVALID")

    checks = preflight.get("checks") or {}
    if ((checks.get("positions") or {}).get("open_position_count")) != 0:
        blockers.append("OPEN_FUTURES_POSITION_PRESENT")
    if ((checks.get("orders") or {}).get("open_order_count")) != 0:
        blockers.append("OPEN_FUTURES_ORDER_PRESENT")
    if not (checks.get("clock") or {}).get("pass"):
        blockers.append("CLOCK_PREFLIGHT_NOT_PASS")

    # Account-level risk firewall from AUTO_EXECUTION_CONTROL_CONTRACT_V1.
    if risk_state.get("status") != "PASS":
        blockers.append("ACCOUNT_RISK_STATE_NOT_PASS")
    max_risk_age = float(authority.get("max_risk_state_age_seconds", 60))
    try:
        risk_at = _parse_utc(risk_state.get("as_of_utc"), "risk_state.as_of_utc")
        if (now_utc - risk_at).total_seconds() > max_risk_age:
            blockers.append("ACCOUNT_RISK_STATE_STALE")
        if risk_at > now_utc:
            blockers.append("ACCOUNT_RISK_STATE_FROM_FUTURE")
    except LiveExecutionGateError:
        blockers.append("ACCOUNT_RISK_STATE_TIME_INVALID")

    planned_fraction = float(
        authority.get("max_initial_isolated_margin_fraction_of_equity", -1)
    )
    max_concurrent = float(
        authority.get("max_concurrent_planned_risk_fraction_equity", -1)
    )
    daily_stop = float(authority.get("daily_stop_fraction_equity", -1))
    weekly_stop = float(authority.get("weekly_stop_fraction_equity", -1))
    daily_loss = float(risk_state.get("daily_realized_loss_fraction_equity", 999))
    weekly_loss = float(risk_state.get("weekly_realized_loss_fraction_equity", 999))
    concurrent_before = float(
        risk_state.get("concurrent_planned_risk_fraction_equity", 999)
    )
    if planned_fraction != 0.001:
        blockers.append("ETF_VALIDATION_RISK_FRACTION_NOT_FROZEN_0_001")
    if max_concurrent != 0.003:
        blockers.append("GLOBAL_CONCURRENT_RISK_LIMIT_NOT_FROZEN_0_003")
    if daily_stop != 0.003:
        blockers.append("GLOBAL_DAILY_STOP_NOT_FROZEN_0_003")
    if weekly_stop != 0.0075:
        blockers.append("GLOBAL_WEEKLY_STOP_NOT_FROZEN_0_0075")
    if daily_loss >= daily_stop:
        blockers.append("DAILY_HALT_ACTIVE")
    if weekly_loss >= weekly_stop:
        blockers.append("WEEKLY_HALT_ACTIVE")
    if concurrent_before + planned_fraction > max_concurrent + 1e-12:
        blockers.append("MAX_CONCURRENT_PLANNED_RISK_EXCEEDED")
    if int(risk_state.get("open_micro_live_positions", 999)) != 0:
        blockers.append("MICRO_LIVE_POSITION_ALREADY_OPEN")

    # Quantity and venue minimum against the frozen 0.1% validation budget.
    try:
        contract = checks.get("contract") or {}
        equity = _positive_float((checks.get("account") or {}).get("equity_usdt"), "equity")
        contract_size = _positive_float(contract.get("contract_size_base"), "contract_size")
        reference_price = _positive_float(contract.get("reference_price"), "reference_price")
        min_vol = _positive_float(contract.get("min_contract_volume"), "min_contract_volume")
        vol_step = _positive_float(contract.get("contract_volume_step"), "contract_volume_step")
        volume_contracts = int(authority.get("volume_contracts"))
        if volume_contracts < min_vol:
            blockers.append("ORDER_VOLUME_BELOW_VENUE_MINIMUM")
        step_units = (volume_contracts - min_vol) / vol_step
        if abs(step_units - round(step_units)) > 1e-9:
            blockers.append("ORDER_VOLUME_NOT_ON_VENUE_STEP")
        requested_notional = volume_contracts * contract_size * reference_price
        max_notional = equity * planned_fraction
        venue_min = _positive_float(
            contract.get("minimum_executable_notional_estimate_usdt"),
            "minimum_executable_notional_estimate_usdt",
        )
        if venue_min > max_notional:
            blockers.append("VENUE_MINIMUM_EXCEEDS_AUTHORITY_RISK_BUDGET")
        if requested_notional > max_notional + 1e-12:
            blockers.append("REQUESTED_NOTIONAL_EXCEEDS_AUTHORITY_RISK_BUDGET")
    except Exception:
        requested_notional = None
        max_notional = None
        venue_min = None
        blockers.append("ORDER_SIZE_OR_RISK_BUDGET_INVALID")

    # Frozen execution-friction envelope.
    try:
        friction_budget = float(authority.get("friction_budget_bps"))
        projected_rt = float(authority.get("projected_round_trip_bps"))
        effective_taker = float(
            (checks.get("fees") or {}).get(
                "effective_taker_fee_bps_for_execution_model"
            )
        )
        if friction_budget != 20.0:
            blockers.append("ETF_STRESS20_FRICTION_BUDGET_NOT_FROZEN")
        if projected_rt < 2.0 * effective_taker:
            blockers.append("PROJECTED_FRICTION_BELOW_FEE_FLOOR")
        if projected_rt > friction_budget:
            blockers.append("PROJECTED_FRICTION_EXCEEDS_STRESS20")
    except (TypeError, ValueError):
        projected_rt = None
        effective_taker = None
        blockers.append("EXECUTION_FRICTION_NOT_FROZEN")

    # Exact timing and no-chase.
    try:
        target = _parse_utc(authority.get("entry_target_utc"), "entry_target_utc")
        exit_target = _parse_utc(authority.get("exit_target_utc"), "exit_target_utc")
        if abs((exit_target - target).total_seconds() - 7 * 24 * 3600) > 1e-9:
            blockers.append("EXIT_TARGET_NOT_EXACTLY_PLUS_7D")
        max_late_seconds = float(authority.get("max_late_seconds"))
        seconds_from_target = (now_utc - target).total_seconds()
        if seconds_from_target < -60:
            blockers.append("ENTRY_WINDOW_NOT_ARMED")
        elif seconds_from_target > max_late_seconds:
            blockers.append("STALE_SIGNAL_NO_CHASE")
    except Exception:
        exit_target = None
        seconds_from_target = None
        blockers.append("ENTRY_OR_EXIT_WINDOW_INVALID")

    reference_entry = authority.get("reference_entry_price")
    try:
        reference_entry = _positive_float(reference_entry, "reference_entry_price")
    except LiveExecutionGateError:
        reference_entry = None
        blockers.append("REFERENCE_ENTRY_PRICE_NOT_FROZEN")

    duplicate_key = authority.get("duplicate_protection_key")
    if not duplicate_key or not isinstance(duplicate_key, str):
        blockers.append("DUPLICATE_PROTECTION_KEY_MISSING")

    return {
        "gate_id": "MEXC_ETF_CME_SHORT_MICROLIVE_GATE_V0.2",
        "checked_at_utc": now_utc.isoformat().replace("+00:00", "Z"),
        "pass": len(blockers) == 0,
        "blockers": blockers,
        "strategy_id": REQUIRED_STRATEGY,
        "symbol": REQUIRED_SYMBOL,
        "signal_identity": signal_key,
        "minimum_notional_usdt": venue_min,
        "requested_notional_usdt": requested_notional,
        "maximum_authorized_notional_usdt": max_notional,
        "projected_round_trip_bps": projected_rt,
        "effective_taker_fee_bps": effective_taker,
        "reference_entry_price": reference_entry,
        "entry_seconds_from_target": seconds_from_target,
        "exit_target_utc": exit_target.isoformat().replace("+00:00","Z") if exit_target else None,
        "order_side_semantics": "3=OPEN_SHORT; 2=CLOSE_SHORT",
        "api_place_order_path": CURRENT_PLACE_ORDER_PATH,
        "order_type": "MARKET",
        "margin_mode": "ISOLATED",
        "leverage": 1,
        "position_mode": "HEDGE",
        "exchange_mutation_performed": False,
        "order_created": False,
    }


__all__ = [
    "EXECUTION_TOKEN",
    "LiveExecutionGateError",
    "validate_futures_short_execution",
]

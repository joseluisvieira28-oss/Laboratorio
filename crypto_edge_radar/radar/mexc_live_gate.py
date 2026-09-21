from __future__ import annotations

import json
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from typing import Any

EXECUTION_TOKEN = "CRYPTO_LAB_LIVE_EXECUTION_V0_1"
REQUIRED_STRATEGY = "ETF-CME-INSTFLOW-001"
REQUIRED_SYMBOL = "BTC_USDT"


class LiveExecutionGateError(RuntimeError):
    pass


def _load(path: str) -> dict[str, Any]:
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload,dict):
        raise LiveExecutionGateError(f"JSON object required: {path}")
    return payload


def validate_futures_short_execution(
    *,
    authority_path: str,
    preflight_path: str,
    signal_path: str,
    kill_switch_path: str = "KILL_SWITCH",
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    now_utc = now_utc or datetime.now(timezone.utc)
    authority=_load(authority_path)
    preflight=_load(preflight_path)
    signal=_load(signal_path)
    blockers=[]

    if Path(kill_switch_path).exists():
        blockers.append("KILL_SWITCH_PRESENT")

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
    if authority.get("late_chase_allowed") is not False:
        blockers.append("AUTHORITY_LATE_CHASE_NOT_FORBIDDEN")
    if authority.get("max_simultaneous_positions") != 1:
        blockers.append("AUTHORITY_ONE_POSITION_CONSTRAINT_MISSING")

    signal_key=signal.get("immutable_signal_key")
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

    if preflight.get("pass") is not True or preflight.get("status") != "PASS":
        blockers.append("AUTHENTICATED_PREFLIGHT_NOT_PASS")
    checks=preflight.get("checks") or {}
    if ((checks.get("positions") or {}).get("open_position_count")) != 0:
        blockers.append("OPEN_POSITION_PRESENT")
    if ((checks.get("orders") or {}).get("open_order_count")) != 0:
        blockers.append("OPEN_ORDER_PRESENT")
    if not (checks.get("clock") or {}).get("pass"):
        blockers.append("CLOCK_PREFLIGHT_NOT_PASS")

    min_notional=(checks.get("contract") or {}).get("minimum_executable_notional_estimate_usdt")
    equity=(checks.get("account") or {}).get("equity_usdt")
    max_fraction=authority.get("max_initial_isolated_margin_fraction_of_equity")
    try:
        min_notional=float(min_notional)
        equity=float(equity)
        max_fraction=float(max_fraction)
        if not all(isfinite(v) and v>0 for v in (min_notional,equity,max_fraction)):
            raise ValueError
        max_notional=equity*max_fraction
        if min_notional > max_notional:
            blockers.append("VENUE_MINIMUM_EXCEEDS_AUTHORITY_RISK_BUDGET")
    except (TypeError,ValueError):
        max_notional=None
        blockers.append("RISK_BUDGET_INPUT_INVALID")

    entry_raw=authority.get("entry_target_utc")
    max_late_seconds=authority.get("max_late_seconds")
    try:
        target=datetime.fromisoformat(str(entry_raw).replace("Z","+00:00"))
        late=(now_utc-target).total_seconds()
        if late < -60:
            blockers.append("ENTRY_WINDOW_NOT_ARMED")
        elif late > float(max_late_seconds):
            blockers.append("STALE_SIGNAL_NO_CHASE")
    except Exception:
        blockers.append("ENTRY_WINDOW_INVALID")

    duplicate_key=authority.get("duplicate_protection_key")
    if not duplicate_key:
        blockers.append("DUPLICATE_PROTECTION_KEY_MISSING")

    fees=checks.get("fees") or {}
    effective_taker=fees.get("effective_taker_fee_bps_for_execution_model")
    if effective_taker is None:
        blockers.append("EFFECTIVE_API_TAKER_FEE_NOT_FROZEN")

    return {
        "gate_id":"MEXC_ETF_CME_SHORT_MICROLIVE_GATE_V0.1",
        "checked_at_utc":now_utc.isoformat().replace("+00:00","Z"),
        "pass":len(blockers)==0,
        "blockers":blockers,
        "strategy_id":REQUIRED_STRATEGY,
        "symbol":REQUIRED_SYMBOL,
        "signal_identity":signal_key,
        "minimum_notional_usdt":min_notional if isinstance(min_notional,float) else None,
        "maximum_authorized_notional_usdt":max_notional,
        "order_side_semantics":"3=OPEN_SHORT; 2=CLOSE_SHORT",
        "order_type":"MARKET",
        "margin_mode":"ISOLATED",
        "leverage":1,
        "exchange_mutation_performed":False,
        "order_created":False,
    }


__all__=["EXECUTION_TOKEN","LiveExecutionGateError","validate_futures_short_execution"]

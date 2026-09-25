from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

EXECUTION_TOKEN="CRYPTO_LAB_TIER2_MICROLIVE_V0_3"
REQUIRED_STRATEGY="OPTIONS-SPOTPERP-001-V2.1"
REQUIRED_SYMBOL="BTCUSDT"
REQUIRED_TRANSLATION="POSITIVE_SIGNAL_TO_MEXC_SPOT_BTCUSDT_LONG_V0.1"

class SpotTier2GateError(RuntimeError): pass

def _load(path:str)->dict[str,Any]:
    out=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(out,dict): raise SpotTier2GateError(f"JSON object required: {path}")
    return out

def _utc(v:Any,field:str)->datetime:
    try: dt=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    except Exception as exc: raise SpotTier2GateError(f"invalid {field}") from exc
    if dt.tzinfo is None: raise SpotTier2GateError(f"{field} must be timezone-aware")
    return dt.astimezone(timezone.utc)

def validate_options_long_spot_execution(*,authority_path:str,preflight_path:str,signal_path:str,risk_state_path:str,kill_switch_path:str="KILL_SWITCH",now_utc:datetime|None=None)->dict[str,Any]:
    now=(now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    a=_load(authority_path); p=_load(preflight_path); s=_load(signal_path); r=_load(risk_state_path)
    blockers=[]
    if Path(kill_switch_path).exists(): blockers.append("KILL_SWITCH_PRESENT")
    if a.get("status")!="ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY": blockers.append("ACTIVE_CANDIDATE_SPECIFIC_AUTHORITY_ABSENT")
    if a.get("policy_id")!="TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24": blockers.append("TIER2_POLICY_BINDING_MISSING")
    if a.get("strategy_id")!=REQUIRED_STRATEGY: blockers.append("AUTHORITY_STRATEGY_MISMATCH")
    if a.get("exchange")!="MEXC_SPOT": blockers.append("AUTHORITY_EXCHANGE_MISMATCH")
    if a.get("symbol")!=REQUIRED_SYMBOL: blockers.append("AUTHORITY_SYMBOL_MISMATCH")
    if a.get("direction")!="LONG": blockers.append("AUTHORITY_DIRECTION_NOT_LONG")
    if a.get("execution_translation")!=REQUIRED_TRANSLATION: blockers.append("EXECUTION_TRANSLATION_NOT_FROZEN")
    if a.get("leverage")!=1: blockers.append("AUTHORITY_LEVERAGE_NOT_1X")
    if a.get("margin_mode")!="SPOT_UNLEVERED": blockers.append("AUTHORITY_NOT_UNLEVERED_SPOT")
    if a.get("max_simultaneous_positions")!=1: blockers.append("AUTHORITY_ONE_POSITION_CONSTRAINT_MISSING")
    if a.get("late_chase_allowed") is not False: blockers.append("AUTHORITY_LATE_CHASE_NOT_FORBIDDEN")
    if float(a.get("max_late_seconds",-1))!=30.0: blockers.append("EXECUTION_TRANSLATION_MAX_LATE_NOT_FROZEN_30S")

    max_quote=float(a.get("max_quote_order_qty_usdt",-1))
    quote_qty=float(a.get("quote_order_qty_usdt",-1))
    daily=float(a.get("daily_realized_loss_kill_usdt",-1)); weekly=float(a.get("rolling_7d_realized_loss_kill_usdt",-1))
    if abs(max_quote-10.0)>1e-12: blockers.append("MAX_NOTIONAL_NOT_FROZEN_10_USDT")
    if not (0<quote_qty<=max_quote): blockers.append("QUOTE_ORDER_QTY_OUTSIDE_10_USDT_CAP")
    if abs(daily-2.0)>1e-12: blockers.append("DAILY_KILL_NOT_FROZEN_2_USDT")
    if abs(weekly-5.0)>1e-12: blockers.append("WEEKLY_KILL_NOT_FROZEN_5_USDT")

    key=s.get("immutable_signal_key")
    if not key or key!=a.get("signal_identity"): blockers.append("SIGNAL_IDENTITY_MISMATCH")
    if s.get("strategy_id")!=REQUIRED_STRATEGY: blockers.append("SIGNAL_STRATEGY_MISMATCH")
    if s.get("signal_direction")!="LONG": blockers.append("SIGNAL_DIRECTION_NOT_LONG")
    if s.get("canonical") is not True: blockers.append("SIGNAL_NOT_CANONICAL")
    if s.get("source_healthy") is not True: blockers.append("SIGNAL_SOURCE_NOT_HEALTHY")
    if s.get("radar_motor_healthy") is not True: blockers.append("RADAR_MOTOR_NOT_HEALTHY")
    if s.get("information_safe_time_passed") is not True: blockers.append("INFORMATION_SAFE_TIME_NOT_PASSED")

    if p.get("pass") is not True or p.get("status")!="PASS": blockers.append("SPOT_AUTHENTICATED_PREFLIGHT_NOT_PASS")
    cand=((p.get("candidate_feasibility") or {}).get("OPTIONS-SPOTPERP-001-V2.1-LONG") or {})
    if cand.get("pass") is not True: blockers.append("SPOT_CAPITAL_OR_PERMISSION_FEASIBILITY_NOT_PASS")
    try:
        age=(now-_utc(p.get("checked_at_utc"),"preflight.checked_at_utc")).total_seconds()
        if age>float(a.get("max_preflight_age_seconds",60)): blockers.append("SPOT_PREFLIGHT_STALE")
        if age<0: blockers.append("SPOT_PREFLIGHT_FROM_FUTURE")
    except SpotTier2GateError: blockers.append("SPOT_PREFLIGHT_TIME_INVALID")
    if int(((p.get("checks") or {}).get("orders") or {}).get("open_order_count",999))!=0: blockers.append("OPEN_BTCUSDT_SPOT_ORDER_PRESENT")
    usdt=float((((p.get("checks") or {}).get("account") or {}).get("usdt_free",0)) or 0)
    if usdt+1e-12<quote_qty: blockers.append("SPOT_USDT_FREE_BELOW_ORDER_QTY")

    if r.get("status")!="PASS": blockers.append("ACCOUNT_RISK_STATE_NOT_PASS")
    try:
        age=(now-_utc(r.get("as_of_utc"),"risk_state.as_of_utc")).total_seconds()
        if age>float(a.get("max_risk_state_age_seconds",60)): blockers.append("ACCOUNT_RISK_STATE_STALE")
        if age<0: blockers.append("ACCOUNT_RISK_STATE_FROM_FUTURE")
    except SpotTier2GateError: blockers.append("ACCOUNT_RISK_STATE_TIME_INVALID")
    if float(r.get("daily_realized_loss_usdt",999))>=daily: blockers.append("DAILY_HALT_ACTIVE")
    if float(r.get("rolling_7d_realized_loss_usdt",999))>=weekly: blockers.append("WEEKLY_HALT_ACTIVE")
    if int(r.get("open_micro_live_positions",999))!=0: blockers.append("MICRO_LIVE_POSITION_ALREADY_OPEN")

    exit_target=None; seconds=None
    try:
        entry=_utc(a.get("entry_target_utc"),"entry_target_utc"); exit_target=_utc(a.get("exit_target_utc"),"exit_target_utc")
        if abs((exit_target-entry).total_seconds()-86400)>1e-9: blockers.append("EXIT_TARGET_NOT_EXACTLY_PLUS_24H")
        seconds=(now-entry).total_seconds()
        if seconds<-60: blockers.append("ENTRY_WINDOW_NOT_ARMED")
        elif seconds>float(a.get("max_late_seconds")): blockers.append("STALE_SIGNAL_NO_CHASE")
    except Exception: blockers.append("ENTRY_OR_EXIT_WINDOW_INVALID")
    if not a.get("duplicate_protection_key"): blockers.append("DUPLICATE_PROTECTION_KEY_MISSING")
    if not a.get("client_order_id"): blockers.append("CLIENT_ORDER_ID_MISSING")

    return {
        "gate_id":"MEXC_OPTIONS_V21_LONG_SPOT_TIER2_MICROLIVE_GATE_V0.3",
        "checked_at_utc":now.isoformat().replace("+00:00","Z"),
        "pass":not blockers,"blockers":blockers,"strategy_id":REQUIRED_STRATEGY,
        "symbol":REQUIRED_SYMBOL,"signal_identity":key,"quote_order_qty_usdt":quote_qty,
        "maximum_authorized_notional_usdt":max_quote,"execution_translation":REQUIRED_TRANSLATION,
        "scientific_promotion_credit_from_translation":False,
        "entry_seconds_from_target":seconds,
        "exit_target_utc":exit_target.isoformat().replace("+00:00","Z") if exit_target else None,
        "exchange_mutation_performed":False,"order_created":False
    }

__all__=["EXECUTION_TOKEN","SpotTier2GateError","validate_options_long_spot_execution"]

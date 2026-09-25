from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


STRATEGY="OPTIONS-SPOTPERP-001-V2.1"
SYMBOL="BTCUSDT"
POLICY="TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24"


class OptionsSpotLiveGateError(RuntimeError):
    pass


def _load(path: str) -> dict[str, Any]:
    row=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(row,dict):
        raise OptionsSpotLiveGateError(f"JSON object required: {path}")
    return row


def _dt(value: Any) -> datetime:
    row=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if row.tzinfo is None:
        raise OptionsSpotLiveGateError("timezone-aware timestamp required")
    return row.astimezone(timezone.utc)


def validate_options_spot_long(
    *,
    authority_path:str,
    preflight_path:str,
    order_test_path:str,
    signal_path:str,
    risk_state_path:str,
    kill_switch_path:str="KILL_SWITCH",
    now_utc:datetime|None=None,
)->dict[str,Any]:
    now=(now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    a=_load(authority_path)
    p=_load(preflight_path)
    t=_load(order_test_path)
    s=_load(signal_path)
    r=_load(risk_state_path)
    blockers=[]

    if Path(kill_switch_path).exists():
        blockers.append("KILL_SWITCH_PRESENT")
    if a.get("status")!="ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY":
        blockers.append("ACTIVE_CANDIDATE_SPECIFIC_AUTHORITY_ABSENT")
    if a.get("micro_live_policy_id")!=POLICY:
        blockers.append("MICROLIVE_POLICY_MISMATCH")
    if a.get("strategy_id")!=STRATEGY:
        blockers.append("AUTHORITY_STRATEGY_MISMATCH")
    if a.get("exchange")!="MEXC" or a.get("market")!="SPOT":
        blockers.append("AUTHORITY_VENUE_MISMATCH")
    if a.get("symbol")!=SYMBOL or a.get("direction")!="LONG":
        blockers.append("AUTHORITY_SYMBOL_OR_DIRECTION_MISMATCH")
    if a.get("leverage")!=1 or a.get("leverage_above_one") is not False:
        blockers.append("AUTHORITY_LEVERAGE_MISMATCH")
    if a.get("order_type")!="MARKET":
        blockers.append("AUTHORITY_ORDER_TYPE_MISMATCH")
    if a.get("max_simultaneous_positions")!=1:
        blockers.append("ONE_POSITION_CONSTRAINT_MISSING")

    key=s.get("immutable_signal_key")
    if not key or key!=a.get("signal_identity"):
        blockers.append("SIGNAL_IDENTITY_MISMATCH")
    if s.get("strategy_id")!=STRATEGY:
        blockers.append("SIGNAL_STRATEGY_MISMATCH")
    if s.get("signal_direction")!="LONG" or int(s.get("position",0) or 0)!=1:
        blockers.append("SIGNAL_NOT_LONG")
    if s.get("canonical") is not True:
        blockers.append("SIGNAL_NOT_CANONICAL")
    if s.get("source_healthy") is not True or s.get("radar_motor_healthy") is not True:
        blockers.append("SIGNAL_SOURCE_OR_RADAR_NOT_HEALTHY")

    try:
        weight=float(s.get("weight"))
        authority_weight=float(a.get("weight"))
        if not 0 < weight <= 1 or abs(weight-authority_weight)>1e-12:
            blockers.append("SCIENTIFIC_WEIGHT_MISMATCH")
    except Exception:
        weight=None
        blockers.append("SCIENTIFIC_WEIGHT_INVALID")

    base=float(a.get("base_micro_live_notional_usdt",-1))
    cap=float(a.get("maximum_notional_usdt_equivalent",-1))
    total_cap=float(a.get("maximum_total_account_exposure_usdt_equivalent",-1))
    quote=float(a.get("quote_order_qty_usdt",-1))
    expected=base*weight if weight is not None else -1
    if base!=10.0 or cap!=10.0 or total_cap!=10.0:
        blockers.append("TIER2_10_USDT_ENVELOPE_MISMATCH")
    if quote<=0 or quote>cap or abs(quote-expected)>1e-8:
        blockers.append("QUOTE_ORDER_QTY_NOT_EXACT_SCIENTIFIC_WEIGHT_X_10_USDT")

    if float(a.get("daily_realized_loss_kill_usdt",-1))!=2.0:
        blockers.append("DAILY_LOSS_KILL_MISMATCH")
    if float(a.get("rolling_7d_realized_loss_kill_usdt",-1))!=5.0:
        blockers.append("WEEKLY_LOSS_KILL_MISMATCH")
    if float(r.get("daily_realized_loss_usdt",999))>=2.0:
        blockers.append("DAILY_HALT_ACTIVE")
    if float(r.get("weekly_realized_loss_usdt",999))>=5.0:
        blockers.append("WEEKLY_HALT_ACTIVE")
    if float(r.get("concurrent_planned_notional_usdt",0))+max(quote,0)>10.0+1e-12:
        blockers.append("MAX_TOTAL_ACCOUNT_EXPOSURE_EXCEEDED")
    if int(r.get("open_micro_live_positions",999))!=0:
        blockers.append("MICRO_LIVE_POSITION_ALREADY_OPEN")

    if p.get("pass") is not True or p.get("status")!="PASS":
        blockers.append("SPOT_AUTHENTICATED_PREFLIGHT_NOT_PASS")
    checks=p.get("checks") or {}
    if ((checks.get("orders") or {}).get("open_order_count"))!=0:
        blockers.append("OPEN_SPOT_ORDER_PRESENT")
    if (checks.get("symbol") or {}).get("pass") is not True:
        blockers.append("BTCUSDT_NOT_API_TRADABLE")
    if float((checks.get("account") or {}).get("usdt_free",-1)) < max(quote,0):
        blockers.append("INSUFFICIENT_FREE_USDT")

    if r.get("status")!="PASS":
        blockers.append("ACCOUNT_RISK_STATE_NOT_PASS")

    try:
        p_at=_dt(p.get("checked_at_utc"))
        if (now-p_at).total_seconds()>float(a.get("max_preflight_age_seconds",60)) or p_at>now:
            blockers.append("SPOT_PREFLIGHT_STALE_OR_FUTURE")
    except Exception:
        blockers.append("SPOT_PREFLIGHT_TIME_INVALID")
    try:
        r_at=_dt(r.get("as_of_utc"))
        if (now-r_at).total_seconds()>float(a.get("max_risk_state_age_seconds",60)) or r_at>now:
            blockers.append("RISK_STATE_STALE_OR_FUTURE")
    except Exception:
        blockers.append("RISK_STATE_TIME_INVALID")

    if t.get("status")!="PASS" or t.get("symbol")!=SYMBOL or t.get("side")!="BUY":
        blockers.append("SPOT_ORDER_TEST_NOT_PASS")
    if t.get("matching_engine_order_created") is not False:
        blockers.append("ORDER_TEST_RECEIPT_INVALID")
    if abs(float(t.get("quote_order_qty_usdt",-1))-max(quote,0))>1e-8:
        blockers.append("ORDER_TEST_QTY_MISMATCH")
    if t.get("client_order_id")!=a.get("new_client_order_id"):
        blockers.append("ORDER_TEST_CLIENT_ID_MISMATCH")
    try:
        t_at=_dt(t.get("checked_at_utc"))
        if (now-t_at).total_seconds()>float(a.get("max_order_test_age_seconds",60)) or t_at>now:
            blockers.append("ORDER_TEST_STALE_OR_FUTURE")
    except Exception:
        blockers.append("ORDER_TEST_TIME_INVALID")

    try:
        signal_day=date.fromisoformat(str(s.get("signal_date")))
        expected_entry=datetime.combine(signal_day+timedelta(days=1),datetime.min.time(),tzinfo=timezone.utc)
        expected_exit=expected_entry+timedelta(days=1)
        entry=_dt(a.get("entry_target_utc"))
        exit_target=_dt(a.get("exit_target_utc"))
        if entry!=expected_entry or exit_target!=expected_exit:
            blockers.append("OPTIONS_FROZEN_T_PLUS_1_T_PLUS_2_TIMING_MISMATCH")
        seconds=(now-entry).total_seconds()
        if seconds < -60:
            blockers.append("ENTRY_WINDOW_NOT_ARMED")
        elif seconds > float(a.get("max_late_seconds",2)):
            blockers.append("STALE_SIGNAL_NO_CHASE")
    except Exception:
        entry=None
        exit_target=None
        seconds=None
        blockers.append("ENTRY_EXIT_TIMING_INVALID")

    if not a.get("new_client_order_id") or not a.get("duplicate_protection_key"):
        blockers.append("IDEMPOTENCY_IDENTITY_MISSING")

    return {
        "gate_id":"OPTIONS_V21_MEXC_SPOT_LONG_MICROLIVE_GATE_V0.3",
        "checked_at_utc":now.isoformat().replace("+00:00","Z"),
        "pass":not blockers,
        "blockers":blockers,
        "strategy_id":STRATEGY,
        "symbol":SYMBOL,
        "direction":"LONG",
        "signal_identity":key,
        "scientific_weight":weight,
        "quote_order_qty_usdt":quote,
        "maximum_notional_usdt":cap,
        "entry_target_utc":entry.isoformat().replace("+00:00","Z") if entry else None,
        "exit_target_utc":exit_target.isoformat().replace("+00:00","Z") if exit_target else None,
        "entry_seconds_from_target":seconds,
        "exchange_mutation_performed":False,
        "order_created":False,
    }

from __future__ import annotations

import argparse,hashlib,json
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from typing import Any
from urllib.request import Request,urlopen

from radar.options_v21_live import (
    HISTORICAL_STATE_START,
    BinanceBTCUSDTDailyFeed,
    DeribitBTCOptionTradeFeed,
    _utc_day_bounds,
    build_daily_skew,
    exact_daily_open_if_available,
    latest_complete_signal_day,
    rv20_and_weight,
)

RADAR_URL="http://127.0.0.1:8787/api/state"
EXPECTED_BUILD="v0.14.4-win-cirv-eight-motor"
EXPECTED_REGISTRY="3.7"
EXPECTED_FOCUS=8

class OptionsExecutionBridgeError(RuntimeError): pass

def _utc_midnight(day:date)->datetime:
    return datetime(day.year,day.month,day.day,tzinfo=timezone.utc)

def _radar_state(url:str=RADAR_URL,timeout:int=3)->dict[str,Any]:
    try:
        req=Request(url,method="GET",headers={"User-Agent":"crypto-lab-options-exec-bridge/0.3"})
        with urlopen(req,timeout=timeout) as response:
            payload=json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise OptionsExecutionBridgeError(f"LOCAL_RADAR_UNAVAILABLE:{type(exc).__name__}:{exc}") from exc
    if not isinstance(payload,dict): raise OptionsExecutionBridgeError("LOCAL_RADAR_STATE_INVALID")
    return payload

def radar_healthy(state:dict[str,Any])->bool:
    registry=state.get("registry") or {}
    return (
        str(state.get("build_id"))==EXPECTED_BUILD
        and str(state.get("registry_version"))==EXPECTED_REGISTRY
        and int(registry.get("focus_loaded",-1))==EXPECTED_FOCUS
        and int(registry.get("focus_expected",-1))==EXPECTED_FOCUS
    )

def build_execution_signal(*,now:datetime,options_feed=None,btc_feed=None,radar_state:dict[str,Any])->dict[str,Any]:
    now=now.astimezone(timezone.utc)
    now_ms=int(now.timestamp()*1000)
    signal_day=latest_complete_signal_day(now_ms)
    if signal_day is None: raise OptionsExecutionBridgeError("NO_COMPLETE_POST_FREEZE_SIGNAL_DAY")
    entry_day=signal_day+timedelta(days=1); exit_day=signal_day+timedelta(days=2)
    entry_target=_utc_midnight(entry_day); exit_target=_utc_midnight(exit_day)
    latency=(now-entry_target).total_seconds()
    if latency<0: raise OptionsExecutionBridgeError("ENTRY_WINDOW_NOT_OPEN")
    if latency>30: raise OptionsExecutionBridgeError("ENTRY_WINDOW_MISSED_NO_CHASE")
    if not radar_healthy(radar_state): raise OptionsExecutionBridgeError("LOCAL_RADAR_V0144_8_OF_8_NOT_HEALTHY")

    options_feed=options_feed or DeribitBTCOptionTradeFeed()
    btc_feed=btc_feed or BinanceBTCUSDTDailyFeed()
    start_ms,end_ms=_utc_day_bounds(signal_day)
    trades=options_feed.trades(start_ms=start_ms,end_ms=end_ms)
    sig=build_daily_skew(signal_day,trades)
    if not sig.get("valid"): raise OptionsExecutionBridgeError("OPTIONS_SIGNAL_INVALID")
    position=int(sig.get("position") or 0)
    if position not in (-1,1): raise OptionsExecutionBridgeError("OPTIONS_SIGNAL_FLAT")

    bars=btc_feed.daily(start_day=HISTORICAL_STATE_START,end_day_exclusive=signal_day+timedelta(days=1))
    risk=rv20_and_weight(bars,signal_day=signal_day)
    weight=float(risk["weight"])
    if not 0<weight<=1: raise OptionsExecutionBridgeError("OPTIONS_WEIGHT_INVALID")
    scientific_open=exact_daily_open_if_available(btc_feed,day=entry_day,now_ms=now_ms)
    if scientific_open is None: raise OptionsExecutionBridgeError("SCIENTIFIC_ENTRY_OPEN_UNAVAILABLE")

    direction="LONG" if position>0 else "SHORT"
    key=f"OPTIONS-SPOTPERP-001:V2.1:{signal_day.isoformat()}"
    canonical_material={
        "event_key":key,"signal_date":signal_day.isoformat(),"position":position,
        "skew":sig.get("skew"),"weight":weight,"rv20":risk.get("rv20"),
        "expanding_median_rv20":risk.get("expanding_median_rv20"),
        "entry_target_utc":entry_target.isoformat().replace("+00:00","Z"),
        "exit_target_utc":exit_target.isoformat().replace("+00:00","Z"),
        "scientific_entry_open_btcusdt":scientific_open,
    }
    fingerprint=hashlib.sha256(json.dumps(canonical_material,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {
        "bridge_id":"OPTIONS_V21_EXECUTION_SIGNAL_BRIDGE_V0.3",
        "immutable_signal_key":key,
        "strategy_id":"OPTIONS-SPOTPERP-001-V2.1",
        "signal_date":signal_day.isoformat(),
        "signal_direction":direction,
        "position":position,
        "skew":sig.get("skew"),
        "weight":weight,
        "rv20":risk.get("rv20"),
        "expanding_median_rv20":risk.get("expanding_median_rv20"),
        "scientific_entry_open_btcusdt":scientific_open,
        "entry_target_utc":canonical_material["entry_target_utc"],
        "exit_target_utc":canonical_material["exit_target_utc"],
        "materialized_at_utc":now.isoformat().replace("+00:00","Z"),
        "materialization_latency_seconds":latency,
        "max_execution_translation_latency_seconds":30,
        "canonical":True,
        "source_healthy":True,
        "radar_motor_healthy":True,
        "information_safe_time_passed":True,
        "frozen_scientific_identity_unchanged":True,
        "scientific_promotion_credit_from_execution_translation":False,
        "canonical_material_sha256":fingerprint
    }

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--out",default="options_v21_execution_signal.json"); ap.add_argument("--radar-url",default=RADAR_URL)
    args=ap.parse_args()
    try:
        state=_radar_state(args.radar_url)
        signal=build_execution_signal(now=datetime.now(timezone.utc),radar_state=state)
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CLOSED","blocker":f"{type(exc).__name__}:{exc}"},indent=2)); return 2
    Path(args.out).write_text(json.dumps(signal,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"SIGNAL_READY","direction":signal["signal_direction"],"signal_key":signal["immutable_signal_key"],"latency_seconds":signal["materialization_latency_seconds"],"out":str(Path(args.out).resolve())},indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())

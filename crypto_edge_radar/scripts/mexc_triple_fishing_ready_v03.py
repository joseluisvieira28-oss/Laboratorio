from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
from typing import Any, Callable

from radar.global_slot_reservation_v03 import GlobalSlotReservationV03
from radar.market import MEXCFuturesPublicFeed
from radar.mexc_auth_readonly import MEXCCredentials, MEXCFuturesAuthenticatedReadOnlyClient
from radar.operator_futures_engine_v02 import OFFICIAL_API_TAKER_FLOOR
from radar.operator_risk_v02 import build_operator_risk_state

CANDIDATES=(
    "BNB-LAUNCHPOOL-DEMAND-001",
    "OPTIONS-SPOTPERP-001-V2.1",
    "HTF-DH03-12H-STANDALONE-FORWARD-V1",
)
REQUIRED_SYMBOLS=(
    "BNB_USDT","BTC_USDT","ETH_USDT","SOL_USDT","XRP_USDT","DOGE_USDT",
)
MAX_SUPERVISOR_STATE_AGE_SECONDS=15.0
MAX_CLOCK_OFFSET_MS=500.0


def _load(path:Path)->dict[str,Any]:
    payload=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload,dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload


def _utc(value:Any)->datetime:
    dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-aware timestamp required")
    return dt.astimezone(timezone.utc)


def build_readiness(
    *,
    credentials:MEXCCredentials,
    receipt_root:Path,
    correction_overlay:Path,
    supervisor_state_path:Path,
    global_slot_path:Path,
    kill_switch_path:Path,
    legacy_bnb_armed_path:Path|None=None,
    legacy_options_armed_path:Path|None=None,
    now_fn:Callable[[],datetime]|None=None,
)->dict[str,Any]:
    clock_utc=now_fn or (lambda: datetime.now(timezone.utc))
    started_at=clock_utc()
    blockers:list[str]=[]

    try:
        overlay=_load(correction_overlay)
        if overlay.get("overlay_id")!="OPTIONS_V21_LOCAL_HASH_BOUND_PNL_CORRECTION_V0.1":
            raise RuntimeError("unexpected correction overlay id")
        if int(overlay.get("entry_count",0))!=4:
            raise RuntimeError("expected four historical OPTIONS corrections")
        os.environ["CRYPTO_LAB_PNL_CORRECTION_OVERLAY"]=str(correction_overlay)
        accounting={"pass":True,"entries":4}
    except Exception as exc:
        accounting={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("OPTIONS_CORRECTION_OVERLAY_NOT_VERIFIED")

    private=MEXCFuturesAuthenticatedReadOnlyClient(credentials)
    public=MEXCFuturesPublicFeed(timeout=10)

    try:
        risk=build_operator_risk_state(
            private_client=private,
            receipt_root=receipt_root,
            now=started_at,
        )
        blockers.extend(risk.get("blockers") or [])
    except Exception as exc:
        risk={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("GLOBAL_RISK_STATE_BUILD_FAILED")

    try:
        mode=private.position_mode()
        if mode!=1:
            blockers.append("FUTURES_POSITION_MODE_NOT_HEDGE")
    except Exception as exc:
        mode=None
        blockers.append(f"POSITION_MODE_READ_FAILED:{type(exc).__name__}")

    try:
        before=time.time_ns()/1_000_000.0
        server=float(public.server_time_ms())
        after=time.time_ns()/1_000_000.0
        midpoint=(before+after)/2.0
        offset=server-midpoint
        clock={
            "pass":abs(offset)<=MAX_CLOCK_OFFSET_MS,
            "server_minus_local_midpoint_ms":offset,
            "request_rtt_ms":after-before,
            "max_abs_offset_ms":MAX_CLOCK_OFFSET_MS,
        }
        if not clock["pass"]:
            blockers.append("WINDOWS_CLOCK_OFFSET_OUTSIDE_500MS")
    except Exception as exc:
        clock={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("MEXC_CLOCK_CHECK_FAILED")

    try:
        slot=GlobalSlotReservationV03(global_slot_path).current()
        if slot is not None:
            blockers.append("GLOBAL_POSITION_SLOT_RESERVED")
    except Exception as exc:
        slot=None
        blockers.append(f"GLOBAL_SLOT_READ_FAILED:{type(exc).__name__}")

    try:
        supervisor=_load(supervisor_state_path)
        if supervisor.get("version")!="TRIPLE_FISHING_OPERATOR_V0.3":
            raise RuntimeError("unexpected supervisor version")
        checked=_utc(supervisor["checked_at_utc"])
        # Freshness must be measured against a timestamp captured after the
        # concurrently-updated supervisor state is read. Using the readiness
        # start time can create a false negative age while network checks run.
        supervisor_now=clock_utc()
        age=(supervisor_now-checked).total_seconds()
        if age<0 or age>MAX_SUPERVISOR_STATE_AGE_SECONDS:
            blockers.append("TRIPLE_SUPERVISOR_STATE_STALE")
        source_state=supervisor.get("source_state") or {}
        for candidate in CANDIDATES:
            if candidate not in source_state:
                blockers.append(f"SOURCE_STATE_MISSING:{candidate}")
        bnb=(source_state.get(CANDIDATES[0]) or {})
        if str(bnb.get("status") or "")!="OK":
            blockers.append("BNB_SOURCE_NOT_OK")
        options=(source_state.get(CANDIDATES[1]) or {})
        if str(options.get("status") or "").startswith("FAIL_CLOSED"):
            blockers.append("OPTIONS_SOURCE_FAIL_CLOSED")
        dh03=(source_state.get(CANDIDATES[2]) or {})
        if str(dh03.get("status") or "")!="COLLECTING_LIVE":
            blockers.append("DH03_SOURCE_NOT_LIVE")
        dh03_age=dh03.get("last_websocket_message_age_ms")
        if dh03_age is None or float(dh03_age)>5_000:
            blockers.append("DH03_SOURCE_HEARTBEAT_STALE")
        supervisor_check={"pass":True,"age_seconds":age,"source_state":source_state}
    except Exception as exc:
        supervisor_check={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("TRIPLE_SUPERVISOR_STATE_INVALID")

    contract_checks={}
    for symbol in REQUIRED_SYMBOLS:
        try:
            row=public.contract_row(symbol)
            ok=(
                row.get("apiAllowed") is not False
                and row.get("state") in (None,0)
                and row.get("futureType") in (None,1)
                and float(row.get("contractSize",0) or 0)>0
                and float(row.get("minVol",0) or 0)>0
                and float(row.get("volUnit",0) or 0)>0
                and float(row.get("priceUnit",0) or 0)>0
            )
            contract_checks[symbol]={"pass":ok}
            if not ok:
                blockers.append(f"CONTRACT_NOT_READY:{symbol}")
        except Exception as exc:
            contract_checks[symbol]={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
            blockers.append(f"CONTRACT_READ_FAILED:{symbol}")

    fee_checks={}
    for symbol in REQUIRED_SYMBOLS:
        try:
            fee=private.fee_details(symbol)
            raw=fee.get("realTakerFee")
            if raw is None:
                raw=fee.get("takerFee")
            account=float(raw)
            effective=max(account,OFFICIAL_API_TAKER_FLOOR)
            if not math.isfinite(account) or account<0:
                raise RuntimeError("invalid account taker fee")
            fee_checks[symbol]={
                "pass":True,
                "account_taker_fee_fraction":account,
                "effective_taker_fee_fraction":effective,
            }
        except Exception as exc:
            fee_checks[symbol]={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
            blockers.append(f"FEE_READ_FAILED:{symbol}")

    try:
        tpsl=private.open_tpsl_orders()
        tpsl_check={"pass":len(tpsl)==0,"open_count":len(tpsl)}
        if tpsl:
            blockers.append("GLOBAL_OPEN_TPSL_ORDER_PRESENT")
    except Exception as exc:
        tpsl_check={"pass":False,"error":f"{type(exc).__name__}:{exc}"}
        blockers.append("TPSL_READ_FAILED")

    if kill_switch_path.exists():
        blockers.append("KILL_SWITCH_PRESENT")
    if legacy_bnb_armed_path is not None and legacy_bnb_armed_path.exists():
        blockers.append("LEGACY_BNB_OPERATOR_STILL_ARMED")
    if legacy_options_armed_path is not None and legacy_options_armed_path.exists():
        blockers.append("LEGACY_OPTIONS_OPERATOR_STILL_ARMED")

    blockers=list(dict.fromkeys(blockers))
    completed_at=clock_utc()
    return {
        "readiness_id":"MEXC-TRIPLE-FISHING-READY-V0.3",
        "checked_at_utc":completed_at.isoformat().replace("+00:00","Z"),
        "status":"PASS_READY_TO_ARM" if not blockers else "FAIL_CLOSED",
        "pass":not blockers,
        "blockers":blockers,
        "candidates":list(CANDIDATES),
        "accounting":accounting,
        "risk_state":risk,
        "position_mode":mode,
        "clock":clock,
        "global_slot":slot,
        "supervisor":supervisor_check,
        "contracts":contract_checks,
        "fees":fee_checks,
        "tpsl":tpsl_check,
        "exchange_mutation_performed":False,
        "order_created":False,
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--receipt-root",required=True)
    ap.add_argument("--correction-overlay",required=True)
    ap.add_argument("--supervisor-state",required=True)
    ap.add_argument("--global-slot-path",required=True)
    ap.add_argument("--armed-path",required=True)
    ap.add_argument("--kill-switch",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--legacy-bnb-armed-path")
    ap.add_argument("--legacy-options-armed-path")
    ap.add_argument("--arm",action="store_true")
    args=ap.parse_args()
    try:
        result=build_readiness(
            credentials=MEXCCredentials.from_env(),
            receipt_root=Path(args.receipt_root),
            correction_overlay=Path(args.correction_overlay),
            supervisor_state_path=Path(args.supervisor_state),
            global_slot_path=Path(args.global_slot_path),
            kill_switch_path=Path(args.kill_switch),
            legacy_bnb_armed_path=Path(args.legacy_bnb_armed_path) if args.legacy_bnb_armed_path else None,
            legacy_options_armed_path=Path(args.legacy_options_armed_path) if args.legacy_options_armed_path else None,
        )
    except Exception as exc:
        result={
            "readiness_id":"MEXC-TRIPLE-FISHING-READY-V0.3",
            "status":"FAIL_CLOSED",
            "pass":False,
            "blockers":[f"READINESS_EXCEPTION:{type(exc).__name__}:{exc}"],
            "exchange_mutation_performed":False,
            "order_created":False,
        }
    out=Path(args.out)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    if not result.get("pass"):
        return 2
    if args.arm:
        armed=Path(args.armed_path)
        armed.parent.mkdir(parents=True,exist_ok=True)
        tmp=armed.with_suffix(armed.suffix+".tmp")
        tmp.write_text(json.dumps({
            "authority":"TRIPLE_FISHING_OPERATOR_V0.3",
            "armed_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "candidates":list(CANDIDATES),
            "max_simultaneous_positions":1,
        },indent=2,sort_keys=True)+"\n",encoding="utf-8")
        tmp.replace(armed)
        print(json.dumps({"status":"ARMED","armed_path":str(armed.resolve())},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

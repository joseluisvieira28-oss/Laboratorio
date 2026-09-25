from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from radar.market import MEXCFuturesPublicFeed
from radar.mexc_auth_readonly import MEXCCredentials, MEXCFuturesAuthenticatedReadOnlyClient
from radar.mexc_auth_trade import MEXCFuturesMutationTransport
from radar.mexc_tier2_live_gate import EXECUTION_TOKEN

def _load(path:str|Path)->dict[str,Any]:
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload,dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload

def _write(path:Path,payload:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    tmp.replace(path)

def _parse_utc(v:Any)->datetime:
    dt=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    if dt.tzinfo is None:
        raise ValueError("timezone-aware datetime required")
    return dt.astimezone(timezone.utc)

def _fee(order:dict[str,Any])->float:
    try:
        if order.get("totalFee") is not None:
            return abs(float(order["totalFee"]))
    except Exception:
        pass
    total=0.0
    for key in ("takerFee","makerFee"):
        try: total+=abs(float(order.get(key,0) or 0))
        except Exception: pass
    return total

def _wait_order(client,*,external_oid:str,timeout:float=10.0)->dict[str,Any]:
    deadline=time.monotonic()+timeout
    last=None
    while time.monotonic()<deadline:
        try: last=client.order_by_external(symbol="BTC_USDT",external_oid=external_oid)
        except Exception:
            time.sleep(0.5); continue
        if int(last.get("state",0) or 0) in (3,4,5):
            return last
        time.sleep(0.5)
    if last is None: raise RuntimeError("EXIT_ORDER_LOOKUP_TIMEOUT_NO_STATE")
    return last

def _short_position(client)->dict[str,Any]|None:
    rows=client.open_positions("BTC_USDT")
    short=[r for r in rows if int(r.get("positionType",0) or 0)==2 and float(r.get("holdVol",0) or 0)>0]
    if len(short)>1: raise RuntimeError("MULTIPLE_SHORT_POSITIONS_PRESENT")
    return short[0] if short else None

def _close_once(*,transport,readonly,position,signal_identity,attempt,session)->dict[str,Any]:
    vol=int(float(position["holdVol"]))
    ext=f"exit-{attempt}-"+hashlib.sha256(f"{signal_identity}:exit:{attempt}".encode()).hexdigest()[:20]
    _write(session/f"EXIT_ORDER_REQUEST_{attempt}.json",{
        "receipt_type":"EXIT_ORDER_REQUEST","attempt":attempt,"symbol":"BTC_USDT",
        "position_id":int(position["positionId"]),"volume_contracts":vol,
        "side":2,"side_semantics":"CLOSE_SHORT","type":5,"openType":1,"leverage":1,
        "positionMode":1,"external_oid":ext
    })
    ack=transport.submit_market_order(symbol="BTC_USDT",volume_contracts=vol,side=2,external_oid=ext,position_mode=1,position_id=int(position["positionId"]))
    _write(session/f"EXIT_EXCHANGE_ACK_{attempt}.json",{"receipt_type":"EXIT_EXCHANGE_ACK","attempt":attempt,"exchange_ack":ack,"external_oid":ext})
    order=_wait_order(readonly,external_oid=ext,timeout=10)
    if int(order.get("state",0) or 0) not in (3,4,5):
        cancel=transport.cancel_by_external(symbol="BTC_USDT",external_oid=ext)
        _write(session/f"EXIT_CANCEL_ACK_{attempt}.json",{"receipt_type":"EXIT_CANCEL_ACK","attempt":attempt,"exchange_ack":cancel,"last_order":order})
        order=_wait_order(readonly,external_oid=ext,timeout=3)
    return order

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--authority",required=True)
    ap.add_argument("--active-trade",required=True)
    ap.add_argument("--session-dir",required=True)
    ap.add_argument("--kill-switch",default="KILL_SWITCH")
    ap.add_argument("--execute",action="store_true")
    ap.add_argument("--watch",action="store_true")
    args=ap.parse_args()

    authority=_load(args.authority); active=_load(args.active_trade); session=Path(args.session_dir)
    reconciliation=session/"POST_TRADE_RECONCILIATION.json"
    if reconciliation.exists():
        print(json.dumps({"status":"ALREADY_RECONCILED","path":str(reconciliation.resolve())},indent=2)); return 0
    if active.get("state") not in ("FILLED","EXIT_PENDING"):
        print(json.dumps({"status":"FAIL_CLOSED","blocker":"ACTIVE_TRADE_STATE_INVALID"},indent=2)); return 2
    if authority.get("status")!="ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY":
        print(json.dumps({"status":"FAIL_CLOSED","blocker":"AUTHORITY_NOT_ACTIVE_FOR_OPEN_POSITION"},indent=2)); return 2

    exit_target=_parse_utc(active["exit_target_utc"])
    tolerance=float(authority.get("exit_on_time_tolerance_seconds",2))
    kill=Path(args.kill_switch)
    while True:
        now=datetime.now(timezone.utc)
        seconds=(exit_target-now).total_seconds()
        if kill.exists() or seconds<=0: break
        if not args.watch:
            print(json.dumps({"status":"WAITING_EXIT","exit_target_utc":exit_target.isoformat().replace("+00:00","Z"),"seconds_to_exit":seconds},indent=2)); return 0
        if seconds>60: time.sleep(min(5.0,seconds-60))
        elif seconds>1: time.sleep(min(0.25,seconds-0.5))
        else: time.sleep(0.02)

    now=datetime.now(timezone.utc)
    late=max(0.0,(now-exit_target).total_seconds())
    kill_active=kill.exists()
    reason="KILL_SWITCH_EMERGENCY_EXIT" if kill_active else "SCHEDULED_PLUS_24H_EXIT"
    failure=kill_active or late>tolerance

    if not args.execute:
        print(json.dumps({"status":"EXIT_DUE_NOT_SUBMITTED","reason":reason,"late_seconds":late,"execution_failure_if_submitted":failure},indent=2)); return 0
    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN")!=EXECUTION_TOKEN:
        print(json.dumps({"status":"FAIL_CLOSED","blocker":"LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"},indent=2)); return 3

    creds=MEXCCredentials.from_env()
    readonly=MEXCFuturesAuthenticatedReadOnlyClient(creds)
    transport=MEXCFuturesMutationTransport(creds)
    public=MEXCFuturesPublicFeed(timeout=10)
    position=_short_position(readonly)
    if position is None or int(position.get("positionId",0) or 0)!=int(active["position_id"]):
        print(json.dumps({"status":"FAIL_CLOSED","blocker":"OPEN_POSITION_IDENTITY_MISMATCH"},indent=2)); return 4

    snap=public.all_market_snapshots()["BTCUSDT"]
    exit_reference=(float(snap.bid_price)+float(snap.ask_price))/2.0
    hold_fee=float(position.get("holdFee",0) or 0)
    orders=[]
    for attempt in (1,2):
        position=_short_position(readonly)
        if position is None: break
        order=_close_once(transport=transport,readonly=readonly,position=position,signal_identity=str(active["signal_identity"]),attempt=attempt,session=session)
        orders.append(order); time.sleep(0.25)
        if _short_position(readonly) is None: break
    if _short_position(readonly) is not None:
        _write(session/"EXIT_FAILURE.json",{"receipt_type":"EXIT_FAILURE","reason":"POSITION_REMAINS_AFTER_TWO_CLOSE_ATTEMPTS","execution_failure":True})
        return 5

    filled=[o for o in orders if float(o.get("dealVol",0) or 0)>0]
    if not filled: return 6
    exit_fee=sum(_fee(o) for o in filled)
    gross=sum(float(o.get("profit",0) or 0) for o in filled)
    num=sum(float(o.get("dealAvgPrice",0) or 0)*float(o.get("dealVol",0) or 0) for o in filled)
    den=sum(float(o.get("dealVol",0) or 0) for o in filled)
    exit_price=num/den if den>0 else None
    entry_fee=0.0
    fp=session/"FEE_RECEIPT.json"
    if fp.exists(): entry_fee=float(_load(fp).get("actual_entry_fee_usdt_from_order",0) or 0)
    net=gross+hold_fee-entry_fee-exit_fee
    closed=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

    _write(session/"EXIT_RECEIPT.json",{
        "receipt_type":"EXIT_RECEIPT","reason":reason,"target_exit_utc":exit_target.isoformat().replace("+00:00","Z"),
        "closed_at_utc":closed,"late_seconds":late,"on_time_tolerance_seconds":tolerance,
        "execution_failure":failure,"exit_reference_mid":exit_reference,"exit_fill_price":exit_price,
        "orders":filled,"position_closed_verified":True
    })
    _write(session/"POST_TRADE_RECONCILIATION.json",{
        "receipt_type":"POST_TRADE_RECONCILIATION","strategy_id":active["strategy_id"],
        "signal_identity":active["signal_identity"],"closed_at_utc":closed,
        "gross_close_profit_usdt":gross,"funding_hold_fee_usdt":hold_fee,
        "entry_fee_usdt":entry_fee,"exit_fee_usdt":exit_fee,"realized_net_pnl_usdt":net,
        "entry_price":active["entry_price"],"exit_price":exit_price,
        "execution_translation":active.get("execution_translation"),
        "scientific_promotion_credit_from_translation":False,
        "execution_failure":failure,"valid_micro_live_execution_evidence":not failure,
        "open_position_after_reconciliation":False
    })
    active["state"]="CLOSED"; active["closed_at_utc"]=closed; active["execution_failure"]=failure
    _write(Path(args.active_trade),active)
    print(json.dumps({"status":"CLOSED_RECONCILED","execution_failure":failure,"realized_net_pnl_usdt":net,"session_dir":str(session.resolve())},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())

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
from radar.mexc_tier2_live_gate import EXECUTION_TOKEN, validate_tier2_options_short_execution

def _write(path:Path,payload:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    tmp.replace(path)

def _load(path:str|Path)->dict[str,Any]:
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload,dict):
        raise RuntimeError(f"JSON object required: {path}")
    return payload

def _session_name(signal_key:str)->str:
    return "options-v21-"+hashlib.sha256(signal_key.encode()).hexdigest()[:16]

def _acquire_lock(root:Path,key:str,payload:dict[str,Any])->Path:
    root.mkdir(parents=True,exist_ok=True)
    path=root/(hashlib.sha256(key.encode()).hexdigest()+".lock")
    try:
        fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError as exc:
        raise RuntimeError("DUPLICATE_PROTECTION_KEY_ALREADY_CONSUMED") from exc
    try:
        os.write(fd,(json.dumps(payload,sort_keys=True)+"\n").encode())
    finally:
        os.close(fd)
    return path

def _wait_order(client:MEXCFuturesAuthenticatedReadOnlyClient,*,external_oid:str,timeout:float=10.0)->dict[str,Any]:
    deadline=time.monotonic()+timeout
    last=None
    while time.monotonic()<deadline:
        try:
            last=client.order_by_external(symbol="BTC_USDT",external_oid=external_oid)
        except Exception:
            time.sleep(0.5)
            continue
        if int(last.get("state",0) or 0) in (3,4,5):
            return last
        time.sleep(0.5)
    if last is None:
        raise RuntimeError("ORDER_LOOKUP_TIMEOUT_NO_STATE")
    return last

def _short_position(client:MEXCFuturesAuthenticatedReadOnlyClient,timeout:float=5.0)->dict[str,Any]|None:
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        rows=client.open_positions("BTC_USDT")
        short=[r for r in rows if int(r.get("positionType",0) or 0)==2 and float(r.get("holdVol",0) or 0)>0]
        if len(short)>1:
            raise RuntimeError("MULTIPLE_SHORT_POSITIONS_PRESENT")
        if short:
            return short[0]
        time.sleep(0.25)
    return None

def _fee(order:dict[str,Any])->float:
    if order.get("totalFee") is not None:
        try:
            return abs(float(order["totalFee"]))
        except (TypeError,ValueError):
            pass
    total=0.0
    for key in ("takerFee","makerFee"):
        try:
            total+=abs(float(order.get(key,0) or 0))
        except (TypeError,ValueError):
            pass
    return total

def _emergency_flatten(*,transport,readonly,position,session_dir:Path,reason:str)->None:
    position_id=int(position["positionId"])
    vol=int(float(position["holdVol"]))
    ext="emg-"+hashlib.sha256(f"{position_id}:{reason}".encode()).hexdigest()[:20]
    _write(session_dir/"EMERGENCY_EXIT_REQUEST.json",{
        "receipt_type":"EMERGENCY_EXIT_REQUEST","reason":reason,"symbol":"BTC_USDT",
        "position_id":position_id,"volume_contracts":vol,"side":2,"side_semantics":"CLOSE_SHORT",
        "external_oid":ext
    })
    ack=transport.submit_market_order(symbol="BTC_USDT",volume_contracts=vol,side=2,external_oid=ext,position_mode=1,position_id=position_id)
    _write(session_dir/"EMERGENCY_EXIT_ACK.json",{"receipt_type":"EMERGENCY_EXIT_ACK","reason":reason,"exchange_ack":ack})
    final=_wait_order(readonly,external_oid=ext,timeout=10)
    _write(session_dir/"EMERGENCY_EXIT_RECEIPT.json",{"receipt_type":"EMERGENCY_EXIT_RECEIPT","reason":reason,"order":final,"execution_failure":True})

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--authority",required=True)
    ap.add_argument("--preflight",required=True)
    ap.add_argument("--signal",required=True)
    ap.add_argument("--risk-state",required=True)
    ap.add_argument("--receipt-root",default="live_receipts")
    ap.add_argument("--duplicate-lock-root",default="live_state/duplicate_locks")
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    authority=_load(args.authority)
    signal=_load(args.signal)
    signal_key=str(signal.get("immutable_signal_key") or "missing-signal")
    session=Path(args.receipt_root)/_session_name(signal_key)
    session.mkdir(parents=True,exist_ok=True)
    kill=str(authority.get("kill_switch_path") or "KILL_SWITCH")

    gate=validate_tier2_options_short_execution(
        authority_path=args.authority,preflight_path=args.preflight,
        signal_path=args.signal,risk_state_path=args.risk_state,kill_switch_path=kill
    )
    _write(session/"PRE_ORDER_GATE.json",gate)
    if not gate["pass"]:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":gate["blockers"],"session_dir":str(session.resolve())},indent=2))
        return 2
    if not args.execute:
        print(json.dumps({"status":"TRADE_READY_NOT_SUBMITTED","gate":gate,"session_dir":str(session.resolve())},indent=2))
        return 0
    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN")!=EXECUTION_TOKEN:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"]},indent=2))
        return 3

    credentials=MEXCCredentials.from_env()
    readonly=MEXCFuturesAuthenticatedReadOnlyClient(credentials)
    transport=MEXCFuturesMutationTransport(credentials)
    public=MEXCFuturesPublicFeed(timeout=10)

    if readonly.open_positions() or readonly.open_orders() or readonly.position_mode()!=1:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_POSITION_ORDER_OR_MODE_CONFLICT"]},indent=2))
        return 4

    snap=public.all_market_snapshots()["BTCUSDT"]
    contract=public.contract_row("BTC_USDT")
    assets=readonly.assets()
    usdt=next((r for r in assets if str(r.get("currency","")).upper()=="USDT"),None)
    if usdt is None or float(usdt.get("equity",0) or 0)<=0:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_EQUITY_INVALID"]},indent=2))
        return 4

    volume=int(authority["volume_contracts"])
    current_price=max(float(snap.last_price),float(snap.ask_price))
    current_notional=volume*float(contract["contractSize"])*current_price
    max_notional=float(authority["max_notional_usdt"])
    if current_notional>max_notional+1e-12:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_NOTIONAL_EXCEEDS_10_USDT_CAP"],"current_notional_usdt":current_notional,"max_notional_usdt":max_notional},indent=2))
        return 4
    if Path(kill).exists():
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["KILL_SWITCH_PRESENT_BEFORE_MUTATION"]},indent=2))
        return 4

    _write(session/"PRE_ORDER_RECEIPT.json",{
        "receipt_type":"PRE_ORDER_RECEIPT",
        "created_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "strategy_id":gate["strategy_id"],"signal_identity":gate["signal_identity"],
        "symbol":"BTC_USDT","direction":"SHORT","execution_translation":gate["execution_translation"],
        "scientific_promotion_credit_from_translation":False,
        "requested_notional_usdt_last_moment":current_notional,
        "maximum_authorized_notional_usdt":max_notional,
        "live_equity_usdt":float(usdt.get("equity")),
        "margin_mode":"ISOLATED","leverage":1,"position_mode":"HEDGE","order_type":"MARKET"
    })

    ack=transport.configure_isolated_leverage(symbol="BTC_USDT",position_type=2,leverage=1)
    _write(session/"LEVERAGE_CONFIGURATION_ACK.json",{"receipt_type":"LEVERAGE_CONFIGURATION_ACK","exchange_ack":ack})
    lev=[r for r in readonly.leverage("BTC_USDT") if int(r.get("positionType",0) or 0)==2]
    leverage_ok=len(lev)==1 and int(lev[0].get("leverage",0) or 0)==1 and int(lev[0].get("openType",0) or 0)==1
    _write(session/"LEVERAGE_POST_VERIFY.json",{"receipt_type":"LEVERAGE_POST_VERIFY","pass":leverage_ok,"rows":lev})
    if not leverage_ok:
        return 5
    if Path(kill).exists() or readonly.open_positions() or readonly.open_orders():
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_CONFLICT_BEFORE_ORDER"]},indent=2))
        return 5

    try:
        lock=_acquire_lock(Path(args.duplicate_lock_root),str(authority["duplicate_protection_key"]),{
            "signal_identity":signal_key,"strategy_id":gate["strategy_id"],
            "consumed_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
        })
    except RuntimeError as exc:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":[str(exc)]},indent=2))
        return 6

    ext=str(authority["external_oid"])
    _write(session/"ORDER_REQUEST.json",{
        "receipt_type":"ORDER_REQUEST","symbol":"BTC_USDT","side":3,"side_semantics":"OPEN_SHORT",
        "type":5,"type_semantics":"MARKET","openType":1,"leverage":1,"positionMode":1,
        "volume_contracts":volume,"external_oid":ext,"signal_identity":signal_key,
        "duplicate_lock":str(lock.resolve())
    })
    ack=transport.submit_market_order(symbol="BTC_USDT",volume_contracts=volume,side=3,external_oid=ext,position_mode=1)
    _write(session/"EXCHANGE_ACK.json",{"receipt_type":"EXCHANGE_ACK","exchange_ack":ack,"external_oid":ext})
    order=_wait_order(readonly,external_oid=ext,timeout=10)
    state=int(order.get("state",0) or 0)
    deal=float(order.get("dealVol",0) or 0)
    if state not in (3,4,5):
        cancel=transport.cancel_by_external(symbol="BTC_USDT",external_oid=ext)
        _write(session/"ORDER_TIMEOUT_CANCEL_ACK.json",{"receipt_type":"ORDER_TIMEOUT_CANCEL_ACK","exchange_ack":cancel,"last_order_state":order})
        order=_wait_order(readonly,external_oid=ext,timeout=3)
        deal=float(order.get("dealVol",0) or 0)
    if deal<=0:
        _write(session/"EXECUTION_FAILURE.json",{"receipt_type":"EXECUTION_FAILURE","reason":"ENTRY_ORDER_NOT_FILLED","trade_opened":False,"order":order})
        return 7

    position=_short_position(readonly,timeout=5)
    if position is None:
        _write(session/"EXECUTION_FAILURE.json",{"receipt_type":"EXECUTION_FAILURE","reason":"FILLED_ORDER_WITHOUT_RESOLVABLE_SHORT_POSITION","trade_opened":True})
        return 8
    if int(position.get("openType",0) or 0)!=1 or int(position.get("leverage",0) or 0)!=1:
        _emergency_flatten(transport=transport,readonly=readonly,position=position,session_dir=session,reason="POST_FILL_POSITION_NOT_ISOLATED_1X")
        return 9
    if bool(position.get("autoAddIm")):
        transport.set_auto_add_margin(position_id=int(position["positionId"]),enabled=False)
        time.sleep(0.25)
        refreshed=_short_position(readonly,timeout=3)
        if refreshed is not None:
            position=refreshed
    if position.get("autoAddIm") is not False:
        _emergency_flatten(transport=transport,readonly=readonly,position=position,session_dir=session,reason="AUTO_MARGIN_ADD_OFF_NOT_VERIFIED")
        return 10

    fill_price=float(order.get("dealAvgPrice") or position.get("openAvgPrice"))
    _write(session/"FILL_RECEIPT.json",{
        "receipt_type":"FILL_RECEIPT","order_id":order.get("orderId"),"external_oid":ext,
        "position_id":position.get("positionId"),"deal_volume_contracts":deal,
        "deal_average_price":fill_price,"open_type":position.get("openType"),
        "leverage":position.get("leverage"),"auto_add_im":position.get("autoAddIm")
    })
    _write(session/"FEE_RECEIPT.json",{"receipt_type":"FEE_RECEIPT","actual_entry_fee_usdt_from_order":_fee(order),"fee_currency":order.get("feeCurrency")})

    active={
        "receipt_type":"ACTIVE_TRADE_STATE","state":"EXIT_PENDING",
        "strategy_id":gate["strategy_id"],"signal_identity":signal_key,
        "position_id":int(position["positionId"]),"volume_contracts":int(float(position["holdVol"])),
        "entry_price":fill_price,"entry_order_external_oid":ext,"entry_order_id":order.get("orderId"),
        "entry_target_utc":authority["entry_target_utc"],"exit_target_utc":authority["exit_target_utc"],
        "planned_notional_usdt":current_notional,"max_notional_usdt":max_notional,
        "execution_translation":gate["execution_translation"],
        "scientific_promotion_credit_from_translation":False,
        "authority_path":str(Path(args.authority).resolve()),"execution_failure":False
    }
    _write(session/"ACTIVE_TRADE_STATE.json",active)
    print(json.dumps({"status":"FILLED_EXIT_PENDING","session_dir":str(session.resolve()),"position_id":active["position_id"],"exit_target_utc":active["exit_target_utc"]},indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse,hashlib,json,os,time
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

from radar.mexc_auth_readonly import MEXCCredentials,MEXCFuturesAuthenticatedReadOnlyClient
from radar.mexc_spot import MEXCSpotPublicFeed, floor_market_quantity, market_quantity_rules
from radar.mexc_spot_auth import MEXCSpotAuthenticatedClient
from radar.mexc_tier2_spot_gate import EXECUTION_TOKEN, validate_options_long_spot_execution

def _write(p:Path,row:dict[str,Any])->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(row,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8"); t.replace(p)

def _load(p:str|Path)->dict[str,Any]:
    out=json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(out,dict): raise RuntimeError("JSON object required")
    return out

def _lock(root:Path,key:str,row:dict[str,Any])->Path:
    root.mkdir(parents=True,exist_ok=True); p=root/(hashlib.sha256(key.encode()).hexdigest()+".lock")
    try: fd=os.open(p,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    except FileExistsError as exc: raise RuntimeError("DUPLICATE_PROTECTION_KEY_ALREADY_CONSUMED") from exc
    try: os.write(fd,(json.dumps(row,sort_keys=True)+"\n").encode())
    finally: os.close(fd)
    return p

def _wait_order(client:MEXCSpotAuthenticatedClient,client_id:str,timeout:float=10.0)->dict[str,Any]:
    deadline=time.monotonic()+timeout; last=None
    while time.monotonic()<deadline:
        try: last=client.order(client_order_id=client_id)
        except Exception:
            time.sleep(0.4); continue
        status=str(last.get("status","")).upper()
        if status in {"FILLED","CANCELED","PARTIALLY_FILLED","REJECTED","EXPIRED"}:
            return last
        time.sleep(0.4)
    if last is None: raise RuntimeError("SPOT_ORDER_LOOKUP_TIMEOUT_NO_STATE")
    return last

def _commission_btc(client:MEXCSpotAuthenticatedClient,order_id:str)->float:
    total=0.0
    for row in client.my_trades(order_id=order_id):
        if str(row.get("commissionAsset","")).upper()=="BTC":
            total+=abs(float(row.get("commission",0) or 0))
    return total

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--authority",required=True); ap.add_argument("--preflight",required=True); ap.add_argument("--signal",required=True); ap.add_argument("--risk-state",required=True)
    ap.add_argument("--receipt-root",default="live_receipts"); ap.add_argument("--duplicate-lock-root",default="live_state/duplicate_locks"); ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()
    a=_load(args.authority); s=_load(args.signal); key=str(s.get("immutable_signal_key") or "missing-signal")
    session=Path(args.receipt_root)/("options-v21-spot-"+hashlib.sha256(key.encode()).hexdigest()[:16]); session.mkdir(parents=True,exist_ok=True)
    kill=str(a.get("kill_switch_path") or "KILL_SWITCH")
    gate=validate_options_long_spot_execution(authority_path=args.authority,preflight_path=args.preflight,signal_path=args.signal,risk_state_path=args.risk_state,kill_switch_path=kill)
    _write(session/"PRE_ORDER_GATE.json",gate)
    if not gate["pass"]:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":gate["blockers"],"session_dir":str(session.resolve())},indent=2)); return 2
    if not args.execute:
        print(json.dumps({"status":"TRADE_READY_NOT_SUBMITTED","gate":gate,"session_dir":str(session.resolve())},indent=2)); return 0
    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN")!=EXECUTION_TOKEN:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"]},indent=2)); return 3

    creds=MEXCCredentials.from_env(); auth=MEXCSpotAuthenticatedClient(creds); public=MEXCSpotPublicFeed(); futures=MEXCFuturesAuthenticatedReadOnlyClient(creds)
    try:
        futures_positions=futures.open_positions(); futures_orders=futures.open_orders()
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["FUTURES_CROSS_VENUE_RECONCILIATION_FAILED"],"error":f"{type(exc).__name__}:{exc}"},indent=2)); return 4
    if futures_positions or futures_orders:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["FUTURES_POSITION_OR_ORDER_PRESENT_CROSS_VENUE"]},indent=2)); return 4
    account=auth.account(); opens=auth.open_orders("BTCUSDT")
    if opens:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_OPEN_SPOT_ORDER_PRESENT"]},indent=2)); return 4
    balances=account.get("balances") or []
    usdt=next((x for x in balances if str(x.get("asset","")).upper()=="USDT"),None)
    free=float((usdt or {}).get("free",0) or 0)
    quote=float(a["quote_order_qty_usdt"])
    if free+1e-12<quote:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_SPOT_USDT_INSUFFICIENT"]},indent=2)); return 4
    if Path(kill).exists():
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["KILL_SWITCH_PRESENT_BEFORE_MUTATION"]},indent=2)); return 4
    ticker=public.book_ticker("BTCUSDT"); info=public.exchange_info("BTCUSDT")
    _write(session/"PRE_ORDER_RECEIPT.json",{
        "receipt_type":"PRE_ORDER_RECEIPT","created_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "strategy_id":gate["strategy_id"],"signal_identity":gate["signal_identity"],"symbol":"BTCUSDT","direction":"LONG",
        "execution_translation":gate["execution_translation"],"quote_order_qty_usdt":quote,"max_notional_usdt":10.0,
        "spot_usdt_free":free,"best_bid":ticker.get("bidPrice"),"best_ask":ticker.get("askPrice"),
        "taker_commission_rate":info.get("takerCommission"),"scientific_promotion_credit_from_translation":False
    })
    try:
        lock=_lock(Path(args.duplicate_lock_root),str(a["duplicate_protection_key"]),{"signal_identity":key,"strategy_id":gate["strategy_id"],"consumed_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z")})
    except RuntimeError as exc:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":[str(exc)]},indent=2)); return 5
    client_id=str(a["client_order_id"])
    _write(session/"ORDER_REQUEST.json",{"receipt_type":"ORDER_REQUEST","symbol":"BTCUSDT","side":"BUY","type":"MARKET","quoteOrderQty":quote,"client_order_id":client_id,"duplicate_lock":str(lock.resolve())})
    ack=auth.submit_market_buy(quote_order_qty_usdt=quote,client_order_id=client_id)
    _write(session/"EXCHANGE_ACK.json",{"receipt_type":"EXCHANGE_ACK","exchange_response":ack,"client_order_id":client_id})
    order=_wait_order(auth,client_id,timeout=10)
    status=str(order.get("status","")).upper()
    executed=float(order.get("executedQty",0) or 0); spent=float(order.get("cummulativeQuoteQty",0) or 0)
    if status not in {"FILLED","PARTIALLY_FILLED"} and executed<=0:
        try: cancel=auth.cancel_order(client_order_id=client_id); _write(session/"ORDER_CANCEL_ACK.json",{"receipt_type":"ORDER_CANCEL_ACK","exchange_response":cancel})
        except Exception: pass
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["SPOT_ENTRY_NOT_FILLED"]},indent=2)); return 6
    btc_commission=_commission_btc(auth,str(order.get("orderId")))
    raw_sellable=max(0.0,executed-btc_commission)
    try:
        sellable=floor_market_quantity(raw_sellable,info)
        qty_rules=market_quantity_rules(info)
    except Exception as exc:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["SPOT_EXIT_QUANTITY_CANNOT_BE_SAFELY_QUANTIZED"],"error":f"{type(exc).__name__}:{exc}"},indent=2)); return 7
    if sellable<=0:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["NO_SELLABLE_BTC_AFTER_ENTRY_COMMISSION"]},indent=2)); return 7
    entry_price=spent/executed if executed>0 else None
    _write(session/"FILL_RECEIPT.json",{"receipt_type":"FILL_RECEIPT","order":order,"executed_btc":executed,"spent_usdt":spent,"entry_price":entry_price,"btc_commission":btc_commission,"raw_sellable_btc":raw_sellable,"sellable_btc":sellable,"exit_quantity_rules":qty_rules})
    active={
        "receipt_type":"ACTIVE_TRADE_STATE","state":"EXIT_PENDING","strategy_id":gate["strategy_id"],"signal_identity":key,
        "entry_order_id":order.get("orderId"),"entry_client_order_id":client_id,"entry_price":entry_price,
        "entry_spent_usdt":spent,"executed_btc":executed,"sellable_btc":sellable,
        "entry_target_utc":a["entry_target_utc"],"exit_target_utc":a["exit_target_utc"],
        "execution_translation":gate["execution_translation"],"scientific_promotion_credit_from_translation":False,
        "authority_path":str(Path(args.authority).resolve()),"execution_failure":False
    }
    _write(session/"ACTIVE_TRADE_STATE.json",active)
    print(json.dumps({"status":"FILLED_EXIT_PENDING","session_dir":str(session.resolve()),"sellable_btc":sellable,"exit_target_utc":active["exit_target_utc"]},indent=2))
    return 0

if __name__=="__main__": raise SystemExit(main())

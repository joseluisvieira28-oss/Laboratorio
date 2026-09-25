from __future__ import annotations

import argparse,hashlib,json,os,time
from datetime import datetime,timezone
from pathlib import Path
from typing import Any

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_spot_auth import MEXCSpotAuthenticatedClient
from radar.mexc_tier2_spot_gate import EXECUTION_TOKEN

def _load(p:str|Path)->dict[str,Any]:
    out=json.loads(Path(p).read_text(encoding="utf-8"))
    if not isinstance(out,dict): raise RuntimeError("JSON object required")
    return out

def _write(p:Path,row:dict[str,Any])->None:
    p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(p.suffix+".tmp"); t.write_text(json.dumps(row,indent=2,sort_keys=True)+"\n",encoding="utf-8"); t.replace(p)

def _utc(v:Any)->datetime:
    dt=datetime.fromisoformat(str(v).replace("Z","+00:00"))
    if dt.tzinfo is None: raise ValueError("timezone aware required")
    return dt.astimezone(timezone.utc)

def _wait(client,cid,timeout=10.0):
    deadline=time.monotonic()+timeout; last=None
    while time.monotonic()<deadline:
        try: last=client.order(client_order_id=cid)
        except Exception:
            time.sleep(0.4); continue
        if str(last.get("status","")).upper() in {"FILLED","CANCELED","PARTIALLY_FILLED","REJECTED","EXPIRED"}: return last
        time.sleep(0.4)
    if last is None: raise RuntimeError("SPOT_EXIT_LOOKUP_TIMEOUT")
    return last

def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--authority",required=True); ap.add_argument("--active-trade",required=True); ap.add_argument("--session-dir",required=True); ap.add_argument("--kill-switch",default="KILL_SWITCH"); ap.add_argument("--execute",action="store_true"); ap.add_argument("--watch",action="store_true")
    args=ap.parse_args(); a=_load(args.authority); active=_load(args.active_trade); session=Path(args.session_dir)
    if (session/"POST_TRADE_RECONCILIATION.json").exists():
        print(json.dumps({"status":"ALREADY_RECONCILED"},indent=2)); return 0
    if active.get("state") not in {"FILLED","EXIT_PENDING"} or a.get("status")!="ACTIVE_MICRO_LIVE_EXECUTION_AUTHORITY":
        print(json.dumps({"status":"FAIL_CLOSED","blocker":"ACTIVE_STATE_OR_AUTHORITY_INVALID"},indent=2)); return 2
    target=_utc(active["exit_target_utc"]); tolerance=float(a.get("exit_on_time_tolerance_seconds",2)); kill=Path(args.kill_switch)
    while True:
        now=datetime.now(timezone.utc); sec=(target-now).total_seconds()
        if kill.exists() or sec<=0: break
        if not args.watch:
            print(json.dumps({"status":"WAITING_EXIT","seconds_to_exit":sec,"exit_target_utc":target.isoformat().replace("+00:00","Z")},indent=2)); return 0
        if sec>60: time.sleep(min(5.0,sec-60))
        elif sec>1: time.sleep(min(0.25,sec-0.5))
        else: time.sleep(0.02)
    now=datetime.now(timezone.utc); late=max(0.0,(now-target).total_seconds()); failure=kill.exists() or late>tolerance
    if not args.execute:
        print(json.dumps({"status":"EXIT_DUE_NOT_SUBMITTED","late_seconds":late,"execution_failure_if_submitted":failure},indent=2)); return 0
    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN")!=EXECUTION_TOKEN:
        print(json.dumps({"status":"FAIL_CLOSED","blocker":"LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"},indent=2)); return 3

    auth=MEXCSpotAuthenticatedClient(MEXCCredentials.from_env())
    qty=float(active["sellable_btc"])
    account=auth.account(); btc=next((x for x in (account.get("balances") or []) if str(x.get("asset","")).upper()=="BTC"),None); free=float((btc or {}).get("free",0) or 0)
    if free+1e-12<qty:
        print(json.dumps({"status":"FAIL_CLOSED","blocker":"SPOT_BTC_BALANCE_BELOW_MICROLIVE_SELL_QTY"},indent=2)); return 4
    cid="exit-"+hashlib.sha256(str(active["signal_identity"]).encode()).hexdigest()[:20]
    ack=auth.submit_market_sell(quantity_btc=qty,client_order_id=cid); _write(session/"EXIT_EXCHANGE_ACK.json",{"receipt_type":"EXIT_EXCHANGE_ACK","exchange_response":ack})
    order=_wait(auth,cid,timeout=10)
    executed=float(order.get("executedQty",0) or 0); received=float(order.get("cummulativeQuoteQty",0) or 0)
    if executed<=0:
        print(json.dumps({"status":"FAIL_CLOSED","blocker":"SPOT_EXIT_NOT_FILLED"},indent=2)); return 5
    buy=float(active["entry_spent_usdt"])
    pf=session/"PRE_ORDER_RECEIPT.json"; fee_rate=0.002
    if pf.exists():
        try: fee_rate=max(float(_load(pf).get("taker_commission_rate") or 0),0.0)
        except Exception: pass
    conservative_fee=buy*fee_rate+received*fee_rate
    net=received-buy-conservative_fee; closed=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    _write(session/"EXIT_RECEIPT.json",{"receipt_type":"EXIT_RECEIPT","order":order,"closed_at_utc":closed,"late_seconds":late,"execution_failure":failure})
    _write(session/"POST_TRADE_RECONCILIATION.json",{
        "receipt_type":"POST_TRADE_RECONCILIATION","strategy_id":active["strategy_id"],"signal_identity":active["signal_identity"],
        "closed_at_utc":closed,"buy_quote_usdt":buy,"sell_quote_usdt":received,"conservative_fee_estimate_usdt":conservative_fee,
        "realized_net_pnl_usdt":net,"execution_translation":active.get("execution_translation"),
        "scientific_promotion_credit_from_translation":False,"execution_failure":failure,"valid_micro_live_execution_evidence":not failure
    })
    active["state"]="CLOSED"; active["closed_at_utc"]=closed; active["execution_failure"]=failure; _write(Path(args.active_trade),active)
    print(json.dumps({"status":"CLOSED_RECONCILED","realized_net_pnl_usdt":net,"execution_failure":failure},indent=2)); return 0

if __name__=="__main__": raise SystemExit(main())

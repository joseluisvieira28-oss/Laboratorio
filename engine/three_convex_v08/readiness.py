"""V08 Windows executable: authoritative MEXC Futures readiness NO-ORDER audit.

The old V07 Telegram task remains untouched. This binary cannot send
a real MEXC mutation; it audits real signed private reads and durable intent
safety, and keeps a strict written GO/NO-GO receipt.
"""
from __future__ import annotations
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import sys
import time
from tempfile import TemporaryDirectory

from engine.three_convex_v06.status_app import inspect
from engine.three_convex_v06.mexc_futures_live_transport import FuturesV06Transport,PrivateKey
from engine.three_convex_v08.order_ledger import DurableLedger,SignalIntent
from engine.three_convex_v08.synthetic_execution import FakeMEXC,simulate_protected_open

STATIC_BLOCKERS=(
    "ENTRY_AND_NATIVE_STOP_NOT_PROVEN_ATOMIC_ON_REAL_MEXC",
    "BROKER_FILL_NATIVE_STOP_POST_ACK_REAL_READBACK_NOT_YET_OBSERVED",
    "FULL_NONLATCHED_TRAILING_AND_EXIT_RECOVERY_NOT_IMPLEMENTED",
    "REAL_POST_RISK_CONTROLLER_DIGEST_NOT_CRYPTOGRAPHICALLY_AUTHENTICATED",
    "LIVE_CONVEX_SOURCE_PARITY_AND_PROSPECTIVE_NET_EDGE_NOT_PROVEN",
    "FIRST_REAL_ORDER_OPERATOR_AUTHORIZATION_NOT_ISSUED",
)

def now_utc():return datetime.now(timezone.utc).isoformat()

def audit(*,account_client,ledger):
    try:
        account=inspect(account_client)
    except Exception:
        account={"status":"ACCOUNT_GET_UNAVAILABLE"}
    has_read=account.get("status")=="AUTHENTICATED_ACCOUNT_AND_PUBLIC_MARKET_READS_NO_LIVE_GO"
    blockers=list(STATIC_BLOCKERS)
    if not has_read:
        blockers.insert(0,"MEXC_AUTHENTICATED_READ_OR_PUBLIC_MARKET_FAILED")
    elif not account.get("broker_account_flat_observed_once"):
        blockers.insert(0,"ACCOUNT_NOT_PROVEN_FLAT_AND_ORDER_FREE")
    if has_read and account.get("position_mode")!="HEDGE":
        blockers.append("HEDGE_POSITION_MODE_NOT_PROVEN")
    symbols=account.get("current_public_contract_and_one_lot_models",{}) if has_read else {}
    if not all(sym in symbols and symbols[sym].get("one_contract_model_risk_budget_pass") is True
               for sym in ("SOL_USDT","BNB_USDT")):
        blockers.append("CURRENT_SOL_BNB_ONE_CONTRACT_RISK_GATE_NOT_PROVEN")
    try:
        book=ledger.summary()
    except Exception:
        book={"restart_requires_broker_reconciliation":True,"active":[]}
        blockers.insert(0,"ORDER_LEDGER_CORRUPT_OR_UNAVAILABLE")
    if book.get("restart_requires_broker_reconciliation"):
        blockers.insert(0,"PENDING_ORDER_INTENT_MUST_RECONCILE_BEFORE_RESTART")
    return {
        "component":"CRYPTO_LAB_V08_MEXC_REAL_EXECUTION_READINESS",
        "checked_at_utc":now_utc(),
        "status":"NO_LIVE_GO",
        "broker_authenticated_read_ok":has_read,
        "broker_account_flat_now":bool(account.get("broker_account_flat_observed_once")) if has_read else False,
        "venue_symbols_model_pass":{
            s:bool(symbols.get(s,{}).get("one_contract_model_risk_budget_pass",False))
            for s in ("SOL_USDT","BNB_USDT")
        },
        "position_mode_hedge":account.get("position_mode")=="HEDGE" if has_read else False,
        "account_equity_usdt":account.get("usdt_equity") if has_read else None,
        "account_free_margin_usdt":account.get("usdt_available") if has_read else None,
        "observed_positions":account.get("open_positions_count") if has_read else None,
        "observed_open_orders":account.get("open_orders_count_all_pages") if has_read else None,
        "observed_native_stops":account.get("open_stops_count") if has_read else None,
        "ledger":book,
        "blockers":blockers,
        "order_posts_sent":0,
        "telegram_existing_v07_unchanged":True,
        "trading_authority":"NONE",
    }


def write_atomic(path,payload):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(".tmp")
    with tmp.open("w",encoding="utf-8") as f:
        json.dump(payload,f,sort_keys=True,indent=2,ensure_ascii=False)
        f.flush();os.fsync(f.fileno())
    os.replace(tmp,path)


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--data-dir",required=True)
    p.add_argument("--once",action="store_true")
    p.add_argument("--synthetic-proof",action="store_true")
    args=p.parse_args(argv)
    root=Path(args.data_dir)
    if args.synthetic_proof:
        with TemporaryDirectory() as td:
            l=DurableLedger(td)
            sig=SignalIntent("SOL_CONVEX_NATIVE_5M","SOL_CONVEX_NATIVE_5M:1000000",1000000,1005000)
            answer=simulate_protected_open(broker=FakeMEXC(),ledger=l,signal=sig)
            l.close()
        print(json.dumps(answer,sort_keys=True))
        return 0 if answer["status"]=="SYNTHETIC_NATIVE_STOP_RECONCILIATION_PASS" else 2
    if not args.once:
        print(json.dumps({"status":"V08_REFUSES_AUTO_TRADING_LOOP_UNTIL_REAL_GO",
                          "order_posts_sent":0}))
        return 2
    try:
        creds=PrivateKey(os.environ.get("MEXC_API_KEY",""),
                         os.environ.get("MEXC_API_SECRET",""))
        client=FuturesV06Transport(creds)
        ledger=DurableLedger(root)
        receipt=audit(account_client=client,ledger=ledger)
        ledger.close()
        write_atomic(root/"V08_READINESS_STATUS.json",receipt)
        print(json.dumps(receipt,sort_keys=True,indent=2,ensure_ascii=False))
        return 0 if receipt["broker_authenticated_read_ok"] else 2
    except Exception as exc:
        print(json.dumps({"status":"V08_FAIL_CLOSED","error_type":type(exc).__name__,
                          "order_posts_sent":0,"trading_authority":"NONE"}))
        return 2


if __name__=="__main__":sys.exit(main())

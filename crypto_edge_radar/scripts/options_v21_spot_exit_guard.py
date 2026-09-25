from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any

from radar.mexc_spot_auth_v3 import (
    ALLOWED_SYMBOL,
    MEXCSpotAuthenticatedReadOnlyClient,
    MEXCSpotCredentials,
    MEXCSpotMutationTransport,
)


EXECUTION_TOKEN="CRYPTO_LAB_TIER2_MICROLIVE_V0_3"


def _load(path:Path)->dict[str,Any]:
    row=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(row,dict):
        raise RuntimeError("JSON object required")
    return row


def _write(path:Path,row:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(row,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    tmp.replace(path)


def _dt(value:str)->datetime:
    return datetime.fromisoformat(value.replace("Z","+00:00")).astimezone(timezone.utc)


def _query(client:MEXCSpotAuthenticatedReadOnlyClient,cid:str,timeout:float=10)->dict[str,Any]|None:
    end=time.monotonic()+timeout
    last=None
    while time.monotonic()<end:
        try:
            last=client.order_by_client_id(client_order_id=cid)
            if str(last.get("status","")).upper() in {"FILLED","CANCELED","REJECTED","EXPIRED","PARTIALLY_FILLED"}:
                return last
        except Exception:
            pass
        time.sleep(.4)
    return last


def _fees(trades:list[dict[str,Any]])->tuple[Decimal,list[str]]:
    total=Decimal("0")
    unknown=[]
    for row in trades:
        asset=str(row.get("commissionAsset") or "").upper()
        fee=Decimal(str(row.get("commission") or "0"))
        price=Decimal(str(row.get("price") or "0"))
        if asset=="USDT":
            total+=fee
        elif asset=="BTC":
            total+=fee*price
        elif fee!=0:
            unknown.append(asset or "UNKNOWN")
    return total,unknown


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--active-state",required=True)
    ap.add_argument("--duplicate-lock-root",default="live_state/duplicate_locks")
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    active_path=Path(args.active_state)
    active=_load(active_path)
    root=active_path.parent
    if active.get("state")!="EXIT_PENDING" or active.get("strategy_id")!="OPTIONS-SPOTPERP-001-V2.1":
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["ACTIVE_STATE_NOT_OPTIONS_EXIT_PENDING"]},indent=2))
        return 2

    now=datetime.now(timezone.utc)
    target=_dt(str(active["exit_target_utc"]))
    if now<target:
        print(json.dumps({"status":"WAITING_EXIT_TARGET","exit_target_utc":active["exit_target_utc"]},indent=2))
        return 0

    late_seconds=(now-target).total_seconds()
    if not args.execute:
        print(json.dumps({"status":"EXIT_READY_NOT_SUBMITTED","late_seconds":late_seconds},indent=2))
        return 0
    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN")!=EXECUTION_TOKEN:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"]},indent=2))
        return 3

    creds=MEXCSpotCredentials.from_env()
    ro=MEXCSpotAuthenticatedReadOnlyClient(creds)
    tx=MEXCSpotMutationTransport(creds)
    info=ro.exchange_info(ALLOWED_SYMBOL)
    step=Decimal(str(info.get("baseSizePrecision") or "0"))
    if step<=0:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["BTCUSDT_BASE_SIZE_PRECISION_INVALID"]},indent=2))
        return 4

    intended=Decimal(str(active["net_btc_to_exit"]))
    sell_qty=(intended/step).to_integral_value(rounding=ROUND_DOWN)*step
    dust=intended-sell_qty
    if sell_qty<=0:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["EXIT_QTY_ROUNDS_TO_ZERO"]},indent=2))
        return 4

    account=ro.account()
    balances={str(x.get("asset","")).upper():Decimal(str(x.get("free") or "0")) for x in account.get("balances",[]) if isinstance(x,dict)}
    if balances.get("BTC",Decimal("0")) < sell_qty:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["INSUFFICIENT_FREE_BTC_FOR_ISOLATED_MICROLIVE_EXIT"]},indent=2))
        return 4

    if ro.open_orders(ALLOWED_SYMBOL):
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["CONFLICTING_BTCUSDT_SPOT_ORDER_PRESENT"]},indent=2))
        return 4

    signal_identity=str(active["signal_identity"])
    cid="o3x"+hashlib.sha256(signal_identity.encode()).hexdigest()[:20]
    lock_path=Path(args.duplicate_lock_root)/(hashlib.sha256(("exit:"+signal_identity).encode()).hexdigest()+".lock")
    lock_path.parent.mkdir(parents=True,exist_ok=True)
    try:
        fd=os.open(lock_path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
        os.write(fd,(json.dumps({"signal_identity":signal_identity,"created_at_utc":now.isoformat()})+"\n").encode())
        os.close(fd)
    except FileExistsError:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["DUPLICATE_EXIT_INTENT_ALREADY_CONSUMED"]},indent=2))
        return 5

    qty=format(sell_qty,"f")
    test=tx.test_market_sell(quantity=qty,client_order_id=cid)
    _write(root/"EXIT_ORDER_TEST_RECEIPT.json",{
        "receipt_type":"EXIT_ORDER_TEST_RECEIPT",
        "status":"PASS",
        "matching_engine_order_created":False,
        "quantity_btc":qty,
        "client_order_id":cid,
        "response":test,
    })
    _write(root/"EXIT_ORDER_INTENT.json",{
        "receipt_type":"EXIT_ORDER_INTENT",
        "persisted_before_transport":True,
        "quantity_btc":qty,
        "unavoidable_round_down_dust_btc":str(dust),
        "client_order_id":cid,
        "target_utc":active["exit_target_utc"],
        "late_seconds_at_intent":late_seconds,
        "kill_switch_present":Path("KILL_SWITCH").exists(),
    })

    ack=None
    recovered=False
    try:
        ack=tx.market_sell(quantity=qty,client_order_id=cid)
    except Exception as exc:
        _write(root/"EXIT_TRANSPORT_EXCEPTION.json",{
            "receipt_type":"EXIT_TRANSPORT_EXCEPTION",
            "error":f"{type(exc).__name__}:{exc}",
            "blind_retry_performed":False,
        })
        ack=_query(ro,cid,10)
        if ack is None:
            _write(root/"EXIT_ACK_UNKNOWN.json",{
                "receipt_type":"EXIT_ACK_UNKNOWN",
                "action":"RECONCILE_BY_CLIENT_ID__NO_BLIND_RETRY",
                "client_order_id":cid,
            })
            print(json.dumps({"status":"FAIL_CLOSED_EXIT_ACK_UNKNOWN","client_order_id":cid},indent=2))
            return 6
        recovered=True

    order=_query(ro,cid,10) or ack
    executed=Decimal(str(order.get("executedQty") or "0"))
    proceeds=Decimal(str(order.get("cummulativeQuoteQty") or "0"))
    if executed<=0:
        _write(root/"EXIT_EXECUTION_FAILURE.json",{
            "receipt_type":"EXIT_EXECUTION_FAILURE",
            "reason":"EXIT_NOT_FILLED",
            "order":order,
        })
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["EXIT_NOT_FILLED"]},indent=2))
        return 7

    order_id=str(order.get("orderId") or ack.get("orderId") or "")
    trades=ro.trades_for_order(order_id=order_id) if order_id else []
    exit_fee_usdt,unknown=_fees(trades)
    entry_spent=Decimal(str(active["entry_quote_spent_usdt"]))
    entry_fee=Decimal(str(active.get("entry_fee_usdt_equivalent") or "0"))
    realized=proceeds-entry_spent-entry_fee-exit_fee_usdt
    complete=(executed+step/Decimal("1000000")>=sell_qty) and not unknown

    _write(root/"EXIT_RECEIPT.json",{
        "receipt_type":"EXIT_RECEIPT",
        "order_id":order_id,
        "client_order_id":cid,
        "ack_recovered_after_transport_exception":recovered,
        "requested_qty_btc":str(sell_qty),
        "executed_qty_btc":str(executed),
        "quote_proceeds_usdt":str(proceeds),
        "exit_fee_usdt_equivalent":str(exit_fee_usdt),
        "unknown_fee_assets":unknown,
        "late_seconds":late_seconds,
        "execution_failure":late_seconds>2 or not complete,
        "trades":trades,
    })
    if not complete:
        print(json.dumps({"status":"FAIL_CLOSED_PARTIAL_OR_FEE_RECONCILIATION","executed_qty_btc":str(executed)},indent=2))
        return 8

    closed=datetime.now(timezone.utc)
    _write(root/"POST_TRADE_RECONCILIATION.json",{
        "receipt_type":"POST_TRADE_RECONCILIATION",
        "strategy_id":active["strategy_id"],
        "signal_identity":signal_identity,
        "closed_at_utc":closed.isoformat().replace("+00:00","Z"),
        "entry_quote_spent_usdt":str(entry_spent),
        "exit_quote_proceeds_usdt":str(proceeds),
        "entry_fee_usdt_equivalent":str(entry_fee),
        "exit_fee_usdt_equivalent":str(exit_fee_usdt),
        "realized_net_pnl_usdt":float(realized),
        "late_exit_seconds":late_seconds,
        "execution_failure":late_seconds>2,
        "residual_round_down_dust_btc":str(dust),
        "complete":True,
    })
    print(json.dumps({"status":"CLOSED","realized_net_pnl_usdt":float(realized),"late_exit_seconds":late_seconds},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

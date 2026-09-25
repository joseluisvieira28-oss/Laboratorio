from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
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
from radar.options_v21_spot_live_gate import validate_options_spot_long


EXECUTION_TOKEN="CRYPTO_LAB_TIER2_MICROLIVE_V0_3"


def _write(path:Path,payload:dict[str,Any])->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    tmp.replace(path)


def _load(path:str|Path)->dict[str,Any]:
    row=json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(row,dict):
        raise RuntimeError(f"JSON object required: {path}")
    return row


def _session(signal_key:str)->str:
    return "options-v21-spot-"+hashlib.sha256(signal_key.encode()).hexdigest()[:16]


def _lock(root:Path,key:str,payload:dict[str,Any])->Path:
    root.mkdir(parents=True,exist_ok=True)
    path=root/(hashlib.sha256(key.encode()).hexdigest()+".lock")
    fd=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY)
    try:
        os.write(fd,(json.dumps(payload,sort_keys=True)+"\n").encode())
    finally:
        os.close(fd)
    return path


def _query_until_known(
    client:MEXCSpotAuthenticatedReadOnlyClient,
    client_order_id:str,
    timeout:float=10.0,
)->dict[str,Any]|None:
    deadline=time.monotonic()+timeout
    last=None
    while time.monotonic()<deadline:
        try:
            last=client.order_by_client_id(client_order_id=client_order_id)
            status=str(last.get("status","")).upper()
            if status in {"FILLED","CANCELED","REJECTED","EXPIRED","PARTIALLY_FILLED"}:
                return last
        except Exception:
            pass
        time.sleep(0.4)
    return last


def _fee_usdt_and_btc(trades:list[dict[str,Any]])->tuple[Decimal,Decimal,list[str]]:
    fee_usdt=Decimal("0")
    fee_btc=Decimal("0")
    unknown=[]
    for row in trades:
        asset=str(row.get("commissionAsset") or "").upper()
        try:
            fee=Decimal(str(row.get("commission") or "0"))
            price=Decimal(str(row.get("price") or "0"))
        except InvalidOperation:
            unknown.append(asset or "INVALID")
            continue
        if asset=="USDT":
            fee_usdt+=fee
        elif asset=="BTC":
            fee_btc+=fee
            fee_usdt+=fee*price
        elif fee!=0:
            unknown.append(asset or "UNKNOWN")
    return fee_usdt,fee_btc,unknown


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--authority",required=True)
    ap.add_argument("--preflight",required=True)
    ap.add_argument("--order-test",required=True)
    ap.add_argument("--signal",required=True)
    ap.add_argument("--risk-state",required=True)
    ap.add_argument("--receipt-root",default="live_receipts")
    ap.add_argument("--duplicate-lock-root",default="live_state/duplicate_locks")
    ap.add_argument("--execute",action="store_true")
    args=ap.parse_args()

    authority=_load(args.authority)
    signal=_load(args.signal)
    signal_key=str(signal.get("immutable_signal_key") or "missing")
    root=Path(args.receipt_root)/_session(signal_key)
    root.mkdir(parents=True,exist_ok=True)
    kill_switch=str(authority.get("kill_switch_path") or "KILL_SWITCH")

    gate=validate_options_spot_long(
        authority_path=args.authority,
        preflight_path=args.preflight,
        order_test_path=args.order_test,
        signal_path=args.signal,
        risk_state_path=args.risk_state,
        kill_switch_path=kill_switch,
    )
    _write(root/"PRE_ORDER_GATE.json",gate)
    if not gate["pass"]:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":gate["blockers"],"session_dir":str(root.resolve())},indent=2))
        return 2

    if not args.execute:
        print(json.dumps({"status":"TRADE_READY_NOT_SUBMITTED","gate":gate,"session_dir":str(root.resolve())},indent=2))
        return 0

    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN")!=EXECUTION_TOKEN:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"]},indent=2))
        return 3

    creds=MEXCSpotCredentials.from_env()
    ro=MEXCSpotAuthenticatedReadOnlyClient(creds)
    tx=MEXCSpotMutationTransport(creds)

    if Path(kill_switch).exists():
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["KILL_SWITCH_PRESENT_BEFORE_MUTATION"]},indent=2))
        return 4
    if ro.open_orders(ALLOWED_SYMBOL):
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_OPEN_SPOT_ORDER_PRESENT"]},indent=2))
        return 4

    account=ro.account()
    balances={str(x.get("asset","")).upper():Decimal(str(x.get("free") or "0")) for x in account.get("balances",[]) if isinstance(x,dict)}
    free_usdt=balances.get("USDT",Decimal("0"))
    quote=Decimal(str(gate["quote_order_qty_usdt"]))
    if quote>Decimal("10") or quote<=0 or free_usdt<quote:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["LAST_MOMENT_SPOT_BALANCE_OR_10_USDT_CAP_FAIL"]},indent=2))
        return 4

    duplicate_key=str(authority["duplicate_protection_key"])
    try:
        lock=_lock(
            Path(args.duplicate_lock_root),
            duplicate_key,
            {
                "strategy_id":gate["strategy_id"],
                "signal_identity":signal_key,
                "consumed_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            },
        )
    except FileExistsError:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["DUPLICATE_PROTECTION_KEY_ALREADY_CONSUMED"]},indent=2))
        return 5

    client_id=str(authority["new_client_order_id"])
    intent={
        "receipt_type":"ORDER_INTENT",
        "strategy_id":gate["strategy_id"],
        "signal_identity":signal_key,
        "symbol":ALLOWED_SYMBOL,
        "side":"BUY",
        "type":"MARKET",
        "quote_order_qty_usdt":float(quote),
        "scientific_weight":gate["scientific_weight"],
        "client_order_id":client_id,
        "duplicate_lock":str(lock.resolve()),
        "persisted_before_transport":True,
        "created_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
    }
    _write(root/"ORDER_INTENT.json",intent)

    qty_text=format(quote,"f")
    ack=None
    ack_recovered=False
    try:
        ack=tx.market_buy(quote_order_qty=qty_text,client_order_id=client_id)
    except Exception as exc:
        _write(root/"ORDER_TRANSPORT_EXCEPTION.json",{
            "receipt_type":"ORDER_TRANSPORT_EXCEPTION",
            "error":f"{type(exc).__name__}:{exc}",
            "blind_retry_performed":False,
        })
        recovered=_query_until_known(ro,client_id,timeout=10)
        if recovered is None:
            _write(root/"ACK_UNKNOWN.json",{
                "receipt_type":"ACK_UNKNOWN",
                "client_order_id":client_id,
                "action":"FREEZE_CANDIDATE_AND_RECONCILE_BY_CLIENT_ID__NO_BLIND_RETRY",
            })
            print(json.dumps({"status":"FAIL_CLOSED_ACK_UNKNOWN","client_order_id":client_id,"session_dir":str(root.resolve())},indent=2))
            return 6
        ack=recovered
        ack_recovered=True

    _write(root/"EXCHANGE_ACK.json",{
        "receipt_type":"EXCHANGE_ACK",
        "client_order_id":client_id,
        "ack_recovered_after_transport_exception":ack_recovered,
        "exchange_response":ack,
    })

    order=_query_until_known(ro,client_id,timeout=10) or ack
    executed=Decimal(str(order.get("executedQty") or "0"))
    spent=Decimal(str(order.get("cummulativeQuoteQty") or "0"))
    status=str(order.get("status") or "").upper()
    if executed<=0:
        _write(root/"EXECUTION_FAILURE.json",{
            "receipt_type":"EXECUTION_FAILURE",
            "reason":"ENTRY_NOT_FILLED",
            "order":order,
            "trade_opened":False,
        })
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["ENTRY_NOT_FILLED"],"order_status":status},indent=2))
        return 7

    order_id=str(order.get("orderId") or ack.get("orderId") or "")
    trades=ro.trades_for_order(order_id=order_id) if order_id else []
    entry_fee_usdt,btc_fee,unknown_fee_assets=_fee_usdt_and_btc(trades)
    net_btc=executed-btc_fee
    if net_btc<=0:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":["NET_ACQUIRED_BTC_INVALID"]},indent=2))
        return 8

    fill={
        "receipt_type":"FILL_RECEIPT",
        "order_id":order_id,
        "client_order_id":client_id,
        "status":status,
        "executed_qty_btc":str(executed),
        "quote_spent_usdt":str(spent),
        "entry_fee_usdt_equivalent":str(entry_fee_usdt),
        "entry_btc_commission":str(btc_fee),
        "net_btc_acquired":str(net_btc),
        "unknown_fee_assets":unknown_fee_assets,
        "partial_fill":status!="FILLED",
        "remainder_chased":False,
        "trades":trades,
    }
    _write(root/"FILL_RECEIPT.json",fill)

    active={
        "receipt_type":"ACTIVE_TRADE_STATE",
        "state":"EXIT_PENDING",
        "strategy_id":gate["strategy_id"],
        "signal_identity":signal_key,
        "symbol":ALLOWED_SYMBOL,
        "direction":"LONG",
        "scientific_weight":gate["scientific_weight"],
        "planned_notional_usdt":float(quote),
        "entry_quote_spent_usdt":str(spent),
        "entry_fee_usdt_equivalent":str(entry_fee_usdt),
        "entry_order_id":order_id,
        "entry_client_order_id":client_id,
        "net_btc_to_exit":str(net_btc),
        "entry_target_utc":gate["entry_target_utc"],
        "exit_target_utc":gate["exit_target_utc"],
        "micro_live_policy_id":"TIER2-MICROLIVE-POLICY-V1.0-FROZEN-2026-09-24",
        "execution_failure":bool(unknown_fee_assets),
    }
    _write(root/"ACTIVE_TRADE_STATE.json",active)
    print(json.dumps({
        "status":"FILLED_EXIT_PENDING",
        "session_dir":str(root.resolve()),
        "entry_order_id":order_id,
        "net_btc_to_exit":str(net_btc),
        "exit_target_utc":gate["exit_target_utc"],
        "fee_reconciliation_complete":not unknown_fee_assets,
    },indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from radar.mexc_auth_readonly import MEXCCredentials
from radar.mexc_auth_trade import MEXCFuturesMutationTransport
from radar.mexc_live_gate import EXECUTION_TOKEN, validate_futures_short_execution


def _write(path: Path, payload: dict):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    tmp.replace(path)


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--authority",required=True)
    p.add_argument("--preflight",required=True)
    p.add_argument("--signal",required=True)
    p.add_argument("--receipt-dir",default="live_receipts")
    p.add_argument("--execute",action="store_true")
    args=p.parse_args()

    outdir=Path(args.receipt_dir)
    gate=validate_futures_short_execution(
        authority_path=args.authority,
        preflight_path=args.preflight,
        signal_path=args.signal,
    )
    _write(outdir/"PRE_ORDER_GATE.json",gate)
    if not gate["pass"]:
        print(json.dumps({"status":"FAIL_CLOSED","blockers":gate["blockers"]},indent=2))
        return 2

    if not args.execute:
        print(json.dumps({"status":"TRADE_READY_NOT_SUBMITTED","gate":gate},indent=2))
        return 0

    if os.getenv("CRYPTO_LAB_LIVE_EXECUTION_TOKEN") != EXECUTION_TOKEN:
        fail={**gate,"pass":False,"blockers":["LIVE_EXECUTION_TOKEN_MISSING_OR_WRONG"]}
        _write(outdir/"PRE_ORDER_GATE.json",fail)
        print(json.dumps({"status":"FAIL_CLOSED","blockers":fail["blockers"]},indent=2))
        return 3

    authority=json.loads(Path(args.authority).read_text(encoding="utf-8"))
    credentials=MEXCCredentials.from_env()
    transport=MEXCFuturesMutationTransport(credentials)

    pre_order={
        "receipt_type":"PRE_ORDER_RECEIPT",
        "strategy_id":gate["strategy_id"],
        "signal_identity":gate["signal_identity"],
        "symbol":gate["symbol"],
        "direction":"SHORT",
        "maximum_authorized_notional_usdt":gate["maximum_authorized_notional_usdt"],
        "minimum_notional_usdt":gate["minimum_notional_usdt"],
        "exchange":"MEXC",
        "margin_mode":"ISOLATED",
        "leverage":1,
        "order_type":"MARKET",
    }
    _write(outdir/"PRE_ORDER_RECEIPT.json",pre_order)

    # Configure the SHORT direction to isolated 1x immediately before submission.
    leverage_ack=transport.configure_isolated_leverage(
        symbol="BTC_USDT",position_type=2,leverage=1
    )
    _write(outdir/"LEVERAGE_CONFIGURATION_ACK.json",{
        "receipt_type":"LEVERAGE_CONFIGURATION_ACK",
        "symbol":"BTC_USDT","position_type":2,"open_type":"ISOLATED","leverage":1,
        "exchange_ack":leverage_ack,
    })

    order_request={
        "receipt_type":"ORDER_REQUEST",
        "symbol":"BTC_USDT",
        "side":3,
        "side_semantics":"OPEN_SHORT",
        "type":5,
        "type_semantics":"MARKET",
        "openType":1,
        "open_type_semantics":"ISOLATED",
        "leverage":1,
        "volume_contracts":int(authority["volume_contracts"]),
        "external_oid":authority["external_oid"],
        "signal_identity":authority["signal_identity"],
    }
    _write(outdir/"ORDER_REQUEST.json",order_request)

    order_id=transport.submit_market_order(
        symbol="BTC_USDT",
        volume_contracts=int(authority["volume_contracts"]),
        side=3,
        external_oid=str(authority["external_oid"]),
        position_mode=int(authority.get("position_mode",1)),
    )
    _write(outdir/"EXCHANGE_ACK.json",{
        "receipt_type":"EXCHANGE_ACK",
        "order_id":order_id,
        "external_oid":authority["external_oid"],
        "exchange":"MEXC",
    })
    print(json.dumps({"status":"SUBMITTED","order_id":order_id},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

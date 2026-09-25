from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from radar.mexc_spot_auth_v3 import (
    ALLOWED_SYMBOL,
    MEXCSpotCredentials,
    MEXCSpotMutationTransport,
)


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--quote-order-qty-usdt",required=True,type=float)
    p.add_argument("--client-order-id",required=True)
    p.add_argument("--out",default="mexc_spot_order_test_receipt.json")
    args=p.parse_args()
    if not 0 < args.quote_order_qty_usdt <= 10.0:
        raise SystemExit("quote order qty must be >0 and <=10 USDT")
    qty=format(args.quote_order_qty_usdt, ".8f").rstrip("0").rstrip(".")
    client=MEXCSpotMutationTransport(MEXCSpotCredentials.from_env())
    response=client.test_market_buy(
        quote_order_qty=qty,
        client_order_id=args.client_order_id,
        symbol=ALLOWED_SYMBOL,
    )
    receipt={
        "receipt_id":"MEXC_SPOT_ORDER_TEST_V0.3",
        "checked_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "status":"PASS",
        "symbol":ALLOWED_SYMBOL,
        "side":"BUY",
        "type":"MARKET",
        "quote_order_qty_usdt":args.quote_order_qty_usdt,
        "client_order_id":args.client_order_id,
        "matching_engine_order_created":False,
        "endpoint":"/api/v3/order/test",
        "response":response,
    }
    Path(args.out).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":"PASS","out":str(Path(args.out).resolve()),"matching_engine_order_created":False},indent=2))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

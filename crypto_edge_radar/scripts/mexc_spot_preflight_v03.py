from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from radar.mexc_auth_readonly import MEXCCredentials,MEXCFuturesAuthenticatedReadOnlyClient
from radar.mexc_spot import MEXCSpotPublicFeed, floor_market_quantity, market_quantity_rules
from radar.mexc_spot_auth import MEXCSpotAuthenticatedClient

def _balance(account,asset):
    rows=account.get("balances") or []
    row=next((r for r in rows if str(r.get("asset","")).upper()==asset),None)
    if row is None:
        return 0.0,0.0
    return float(row.get("free",0) or 0),float(row.get("locked",0) or 0)

def run()->dict:
    creds=MEXCCredentials.from_env()
    public=MEXCSpotPublicFeed(timeout=10)
    auth=MEXCSpotAuthenticatedClient(creds,timeout=10)
    futures=MEXCFuturesAuthenticatedReadOnlyClient(creds,timeout=10)
    blockers=[]; candidate=[]
    info=public.exchange_info("BTCUSDT")
    supported="BTCUSDT" in public.default_symbols()
    order_types={str(x).upper() for x in (info.get("orderTypes") or [])}
    spot_ok=supported and bool(info.get("isSpotTradingAllowed")) and "MARKET" in order_types and bool(info.get("quoteOrderQtyMarketAllowed"))
    if not spot_ok: blockers.append("BTCUSDT_SPOT_MARKET_API_NOT_SUPPORTED")
    account=auth.account()
    if account.get("canTrade") is not True: blockers.append("SPOT_ACCOUNT_CANNOT_TRADE")
    open_orders=auth.open_orders("BTCUSDT")
    if open_orders: blockers.append("OPEN_BTCUSDT_SPOT_ORDER_PRESENT")
    try:
        futures_positions=futures.open_positions(); futures_orders=futures.open_orders()
        if futures_positions: blockers.append("OPEN_FUTURES_POSITION_PRESENT_CROSS_VENUE")
        if futures_orders: blockers.append("OPEN_FUTURES_ORDER_PRESENT_CROSS_VENUE")
    except Exception:
        blockers.append("FUTURES_CROSS_VENUE_RECONCILIATION_FAILED")
    usdt_free,_=_balance(account,"USDT")
    btc_free,btc_locked=_balance(account,"BTC")
    if usdt_free<10.0: candidate.append("SPOT_USDT_FREE_BELOW_10_USDT")
    try:
        book=public.book_ticker("BTCUSDT")
        ask=float(book["askPrice"])
        taker=float(info.get("takerCommission",0) or 0)
        estimated_btc=(10.0/ask)*max(0.0,1.0-taker)
        estimated_sell_qty=floor_market_quantity(estimated_btc,info)
        qty_rules=market_quantity_rules(info)
    except Exception:
        estimated_sell_qty=None; qty_rules=None
        candidate.append("SPOT_EXIT_QUANTITY_FEASIBILITY_FAILED")
    test_id="opt-v21-v03-test"
    try:
        auth.test_market_buy(quote_order_qty_usdt=10.0,client_order_id=test_id)
        test_pass=True; test_error=None
    except Exception as exc:
        test_pass=False; test_error=f"{type(exc).__name__}: {exc}"; candidate.append("SPOT_MARKET_ORDER_TEST_FAILED")
    passed=not blockers
    return {
        "preflight_id":"MEXC_SPOT_OPTIONS_V21_PREFLIGHT_V0.3",
        "status":"PASS" if passed else "FAIL_CLOSED","pass":passed,
        "checked_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
        "blockers":blockers,
        "candidate_feasibility":{"OPTIONS-SPOTPERP-001-V2.1-LONG":{
            "pass":not candidate,"status":"PASS" if not candidate else "BLOCKED","blockers":candidate
        }},
        "checks":{
            "symbol":{"symbol":"BTCUSDT","default_symbol_supported":supported,"exchange_info":info},
            "account":{"can_trade":account.get("canTrade"),"usdt_free":usdt_free,"btc_free":btc_free,"btc_locked":btc_locked},
            "orders":{"open_order_count":len(open_orders)},
            "exit_quantity":{"estimated_sell_quantity_btc":estimated_sell_qty,"rules":qty_rules},
            "order_test":{"pass":test_pass,"error":test_error,"matching_engine_submission":False}
        },
        "security":{"authenticated_api_used":True,"real_order_created":False,"exchange_mutation_to_matching_engine":False,"transfer_endpoint_implemented":False,"withdrawal_endpoint_implemented":False}
    }

def main()->int:
    try: result=run()
    except Exception as exc:
        result={"preflight_id":"MEXC_SPOT_OPTIONS_V21_PREFLIGHT_V0.3","status":"FAIL_CLOSED","pass":False,"blockers":["SPOT_PREFLIGHT_RUNTIME_EXCEPTION"],"error":f"{type(exc).__name__}: {exc}","security":{"real_order_created":False}}
    out=Path("mexc_spot_preflight_receipt.json")
    out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":result.get("status"),"pass":result.get("pass"),"blockers":result.get("blockers",[]),"out":str(out.resolve())},indent=2))
    return 0 if result.get("pass") is True else 2

if __name__=="__main__":
    raise SystemExit(main())

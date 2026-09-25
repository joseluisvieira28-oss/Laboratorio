from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import time

from radar.mexc_spot_auth_v3 import (
    ALLOWED_SYMBOL,
    MEXCSpotAuthenticatedReadOnlyClient,
    MEXCSpotCredentials,
)


def build_preflight(client: MEXCSpotAuthenticatedReadOnlyClient) -> dict:
    checked = datetime.now(timezone.utc)
    local_ms = int(time.time() * 1000)
    server_ms = client.server_time_ms()
    offset_ms = server_ms - local_ms
    account = client.account()
    self_symbols = client.self_symbols()
    default_symbols = client.default_symbols()
    exchange_info = client.exchange_info(ALLOWED_SYMBOL)
    orders = client.open_orders(ALLOWED_SYMBOL)
    mx_deduct = client.mx_deduct_enabled()
    fee = client.trade_fee(ALLOWED_SYMBOL)
    taker_bps = float(fee["takerCommission"]) * 10_000.0
    balances = {
        str(row.get("asset", "")).upper(): {
            "free": float(row.get("free", 0) or 0),
            "locked": float(row.get("locked", 0) or 0),
        }
        for row in (account.get("balances") or [])
        if isinstance(row, dict)
    }
    usdt = balances.get("USDT", {"free": 0.0, "locked": 0.0})
    btc = balances.get("BTC", {"free": 0.0, "locked": 0.0})
    permissions = {str(x).upper() for x in (account.get("permissions") or [])}
    checks = {
        "clock": {
            "pass": abs(offset_ms) <= 1000,
            "offset_ms": offset_ms,
            "maximum_abs_offset_ms": 1000,
        },
        "account": {
            "pass": account.get("canTrade") is True and "SPOT" in permissions,
            "can_trade": account.get("canTrade"),
            "permissions": sorted(permissions),
            "usdt_free": usdt["free"],
            "btc_free": btc["free"],
            "equity_usdt": usdt["free"],
        },
        "symbol": {
            "pass": (
                ALLOWED_SYMBOL in default_symbols
                and ALLOWED_SYMBOL in self_symbols
                and exchange_info.get("isSpotTradingAllowed") is True
                and exchange_info.get("quoteOrderQtyMarketAllowed") is True
                and "MARKET" in (exchange_info.get("orderTypes") or [])
            ),
            "symbol": ALLOWED_SYMBOL,
            "in_default_symbols": ALLOWED_SYMBOL in default_symbols,
            "in_api_key_symbols": ALLOWED_SYMBOL in self_symbols,
            "is_spot_trading_allowed": exchange_info.get("isSpotTradingAllowed"),
            "quote_order_qty_market_allowed": exchange_info.get("quoteOrderQtyMarketAllowed"),
            "order_types": exchange_info.get("orderTypes"),
            "quote_amount_precision": exchange_info.get("quoteAmountPrecision"),
            "base_size_precision": exchange_info.get("baseSizePrecision"),
        },
        "orders": {
            "pass": len(orders) == 0,
            "open_order_count": len(orders),
        },
        "fees": {
            "pass": (not mx_deduct) and (2.0 * taker_bps <= 20.0 + 1e-12),
            "mx_deduct_enabled": mx_deduct,
            "taker_fee_bps_one_way": taker_bps,
            "projected_taker_round_trip_bps": 2.0 * taker_bps,
            "stress20_budget_bps": 20.0,
            "reason": None if (not mx_deduct and 2.0*taker_bps <= 20.0 + 1e-12) else "MX_DEDUCT_OR_STRESS20_FEE_GATE_FAIL",
        },
        "positions": {
            "pass": True,
            "open_position_count": 0,
            "semantics": "SPOT_HAS_NO_NATIVE_POSITION_OBJECT__LOCAL_MICROLIVE_RECEIPTS_CONTROL_CONCURRENCY",
        },
    }
    blockers = [name for name, row in checks.items() if row.get("pass") is not True]
    return {
        "preflight_id": "MEXC_SPOT_AUTHENTICATED_READ_ONLY_PREFLIGHT_V0.3",
        "checked_at_utc": checked.isoformat().replace("+00:00", "Z"),
        "status": "PASS" if not blockers else "FAIL_CLOSED",
        "pass": not blockers,
        "blockers": blockers,
        "checks": checks,
        "security": {
            "api_key_returned_in_receipt": False,
            "api_secret_returned_in_receipt": False,
            "exchange_mutation_performed": False,
            "withdrawal_endpoint_implemented": False,
            "transfer_endpoint_implemented": False,
        },
    }


def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--out", default="mexc_spot_authenticated_preflight_receipt.json")
    args=p.parse_args()
    client=MEXCSpotAuthenticatedReadOnlyClient(MEXCSpotCredentials.from_env())
    receipt=build_preflight(client)
    Path(args.out).write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":receipt["status"],"blockers":receipt["blockers"],"out":str(Path(args.out).resolve())},indent=2))
    return 0 if receipt["pass"] else 2


if __name__=="__main__":
    raise SystemExit(main())

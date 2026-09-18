from __future__ import annotations

from decimal import Decimal
import json
import os

from .binance_trading import BinanceUSDMTradingClient
from .execution import (
    ExecutionBlocked,
    MAX_NOTIONAL_USDT,
    SYMBOL,
    round_quantity,
)


def run_binance_preflight() -> dict:
    client = BinanceUSDMTradingClient(
        timeout=int(os.getenv("MICROLIVE_HTTP_TIMEOUT", "10"))
    )
    health = client.preflight(SYMBOL)
    if health.get("ok") is not True:
        raise ExecutionBlocked(f"Binance account preflight failed: {health}")

    rules = client.market_rules(SYMBOL)
    price = client.mark_or_last_price(SYMBOL)
    qty = round_quantity(
        notional_usdt=MAX_NOTIONAL_USDT,
        price=price,
        step_size=rules["step_size"],
        min_qty=rules["min_qty"],
        min_notional=rules.get("min_notional", Decimal("0")),
    )

    # Test-order validates API trade permission and order syntax but does not
    # enter the matching engine.
    test_result = client.test_market(
        symbol=SYMBOL,
        side="BUY",
        quantity=qty,
        reduce_only=False,
        client_order_id="ced0031-preflight-only",
    )
    return {
        "status": "BINANCE_MICROLIVE_CREDENTIAL_PREFLIGHT_PASS",
        "symbol": SYMBOL,
        "health": health,
        "computed_test_quantity": format(qty, "f"),
        "approx_notional_usdt": format(qty * price, "f"),
        "order_test_result": test_result,
        "real_order_submitted": False,
    }


def main() -> int:
    try:
        result = run_binance_preflight()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "BINANCE_MICROLIVE_CREDENTIAL_PREFLIGHT_FAIL_CLOSED",
                    "error": str(exc),
                    "real_order_submitted": False,
                },
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

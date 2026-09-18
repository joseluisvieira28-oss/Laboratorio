from __future__ import annotations

from decimal import Decimal, ROUND_DOWN
import json

from .binance_trading import BinanceUSDMTradingClient
from .ced1d0031_microlive import MAX_NOTIONAL_USDT, TARGET_NOTIONAL_USDT
from .ced1d0031_public import SYMBOL


def _qty(price: Decimal, step: Decimal, min_qty: Decimal, min_notional: Decimal) -> Decimal:
    units = ((TARGET_NOTIONAL_USDT / price) / step).to_integral_value(rounding=ROUND_DOWN)
    qty = units * step
    notional = qty * price
    if qty < min_qty:
        raise RuntimeError("target notional below min quantity")
    if notional < min_notional:
        raise RuntimeError("target notional below min notional")
    if notional > MAX_NOTIONAL_USDT:
        raise RuntimeError("quantity exceeds hard cap")
    return qty


def run() -> dict:
    client = BinanceUSDMTradingClient(timeout=10)
    health = client.preflight(SYMBOL)
    if health.get("ok") is not True:
        raise RuntimeError(f"authenticated preflight failed: {health}")

    rules = client.market_rules(SYMBOL)
    book = client.book_ticker(SYMBOL)
    qty = _qty(
        book["mid"],
        rules["step_size"],
        rules["min_qty"],
        rules["min_notional"],
    )
    test = client.test_market(
        symbol=SYMBOL,
        side="BUY",
        quantity=qty,
        reduce_only=False,
        client_order_id="ced0031-preflight-only",
    )
    return {
        "status": "CED1D0031_BINANCE_MICROLIVE_PREFLIGHT_PASS",
        "symbol": SYMBOL,
        "health": health,
        "test_quantity": format(qty, "f"),
        "preflight_mid": format(book["mid"], "f"),
        "approx_notional_usdt": format(qty * book["mid"], "f"),
        "order_test_result": test,
        "real_order_submitted": False,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(run(), sort_keys=True))
    except Exception as exc:
        print(
            json.dumps(
                {
                    "status": "CED1D0031_BINANCE_MICROLIVE_PREFLIGHT_FAIL_CLOSED",
                    "error": f"{type(exc).__name__}:{exc}",
                    "real_order_submitted": False,
                },
                sort_keys=True,
            )
        )
        raise SystemExit(2)

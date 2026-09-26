"""Exact frozen-scope public source coverage probe for MRCR H02.

This probe checks transport and schema only for the frozen H02 market scope:
BTC/ETH on Binance Spot and Coinbase Advanced Spot, using public trades + L2.

No economic values are printed or persisted. No raw payloads are persisted.
No authentication, account endpoint, signal, outcome or order logic exists here.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed, InvalidStatus


BINANCE_BASE = "wss://data-stream.binance.vision:443/stream?streams="
COINBASE_URL = "wss://advanced-trade-ws.coinbase.com"

BINANCE_SYMBOLS = ("BTCUSDT", "ETHUSDT")
COINBASE_PRODUCTS = ("BTC-USD", "ETH-USD")


def _has(obj: dict[str, Any], fields: set[str]) -> bool:
    return fields.issubset(obj.keys())


def _http_status(exc: Exception) -> int | None:
    if isinstance(exc, InvalidStatus):
        response = getattr(exc, "response", None)
        return getattr(response, "status_code", None)
    return None


async def probe_binance_symbol(symbol: str, seconds: float) -> dict[str, Any]:
    stream = symbol.lower()
    url = BINANCE_BASE + f"{stream}@aggTrade/{stream}@depth@100ms"
    out = {
        "symbol": symbol,
        "transport": "UNKNOWN",
        "aggtrade_messages": 0,
        "depth_messages": 0,
        "aggtrade_schema_pass": False,
        "depth_schema_pass": False,
        "error_class": None,
        "http_status": None,
        "status": "FAIL_CLOSED",
    }
    deadline = time.monotonic() + seconds
    try:
        async with websockets.connect(
            url,
            proxy=None,
            compression=None,
            open_timeout=8,
            close_timeout=2,
            ping_interval=None,
            max_size=4_000_000,
        ) as ws:
            out["transport"] = "PASS"
            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                except asyncio.TimeoutError:
                    continue
                if not isinstance(raw, str):
                    continue
                envelope = json.loads(raw)
                data = envelope.get("data", envelope)
                if not isinstance(data, dict):
                    continue
                event = data.get("e")
                if event == "aggTrade":
                    out["aggtrade_messages"] += 1
                    if _has(data, {"E", "s", "a", "p", "q", "T", "m"}):
                        out["aggtrade_schema_pass"] = True
                elif event == "depthUpdate":
                    out["depth_messages"] += 1
                    if _has(data, {"E", "s", "U", "u", "b", "a"}):
                        out["depth_schema_pass"] = True
    except Exception as exc:
        out["transport"] = "FAIL"
        out["error_class"] = type(exc).__name__
        out["http_status"] = _http_status(exc)

    if (
        out["transport"] == "PASS"
        and out["aggtrade_messages"] > 0
        and out["depth_messages"] > 0
        and out["aggtrade_schema_pass"]
        and out["depth_schema_pass"]
    ):
        out["status"] = "PASS"
    return out


async def probe_coinbase_product(product: str, seconds: float) -> dict[str, Any]:
    out = {
        "product": product,
        "transport": "UNKNOWN",
        "subscription_messages": 0,
        "market_trade_messages": 0,
        "level2_messages": 0,
        "l2_snapshot_seen": False,
        "l2_update_seen": False,
        "market_trade_schema_pass": False,
        "level2_schema_pass": False,
        "sequence_adjudicated": False,
        "error_class": None,
        "close_code": None,
        "http_status": None,
        "status": "FAIL_CLOSED",
    }
    deadline = time.monotonic() + seconds
    try:
        async with websockets.connect(
            COINBASE_URL,
            proxy=None,
            compression=None,
            open_timeout=8,
            close_timeout=2,
            ping_interval=20,
            max_size=16_000_000,
        ) as ws:
            for channel in ("market_trades", "level2"):
                await ws.send(json.dumps({
                    "type": "subscribe",
                    "product_ids": [product],
                    "channel": channel,
                }, separators=(",", ":")))

            out["transport"] = "PASS"
            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                except asyncio.TimeoutError:
                    continue
                if not isinstance(raw, str):
                    continue
                msg = json.loads(raw)
                if not isinstance(msg, dict):
                    continue
                channel = str(msg.get("channel", "UNKNOWN"))

                if channel == "subscriptions":
                    out["subscription_messages"] += 1
                    continue

                if channel == "market_trades":
                    out["market_trade_messages"] += 1
                    for event in msg.get("events", []):
                        if not isinstance(event, dict):
                            continue
                        for trade in event.get("trades", []):
                            if isinstance(trade, dict) and _has(
                                trade,
                                {"trade_id", "product_id", "price", "size", "side", "time"},
                            ):
                                if trade.get("product_id") == product:
                                    out["market_trade_schema_pass"] = True

                elif channel in {"l2_data", "level2"}:
                    out["level2_messages"] += 1
                    for event in msg.get("events", []):
                        if not isinstance(event, dict):
                            continue
                        if event.get("product_id") != product:
                            continue
                        event_type = event.get("type")
                        if event_type == "snapshot":
                            out["l2_snapshot_seen"] = True
                        elif event_type == "update":
                            out["l2_update_seen"] = True
                        for update in event.get("updates", []):
                            if isinstance(update, dict) and _has(
                                update,
                                {"side", "event_time", "price_level", "new_quantity"},
                            ):
                                out["level2_schema_pass"] = True

    except ConnectionClosed as exc:
        out["transport"] = "FAIL"
        out["error_class"] = type(exc).__name__
        out["close_code"] = getattr(exc, "code", None)
    except Exception as exc:
        out["transport"] = "FAIL"
        out["error_class"] = type(exc).__name__
        out["http_status"] = _http_status(exc)

    if (
        out["transport"] == "PASS"
        and out["subscription_messages"] > 0
        and out["market_trade_messages"] > 0
        and out["level2_messages"] > 0
        and out["market_trade_schema_pass"]
        and out["level2_schema_pass"]
        and out["l2_snapshot_seen"]
        and out["l2_update_seen"]
    ):
        out["status"] = "PASS"
    return out


async def run_probe(seconds: float) -> dict[str, Any]:
    tasks = [
        *(probe_binance_symbol(symbol, seconds) for symbol in BINANCE_SYMBOLS),
        *(probe_coinbase_product(product, seconds) for product in COINBASE_PRODUCTS),
    ]
    results = await asyncio.gather(*tasks)
    binance = [row for row in results if "symbol" in row]
    coinbase = [row for row in results if "product" in row]
    all_pass = all(row["status"] == "PASS" for row in results)

    return {
        "probe": "MRCR_H02_EXACT_SOURCE_COVERAGE_V01",
        "frozen_ruleset_id": "MRCR-H02-ACCEPTANCE-REJECTION-V01",
        "scope": {
            "binance_spot": list(BINANCE_SYMBOLS),
            "coinbase_advanced_spot": list(COINBASE_PRODUCTS),
            "channels": {
                "binance": ["aggTrade", "depth@100ms"],
                "coinbase": ["market_trades", "level2"],
            },
        },
        "binance": binance,
        "coinbase": coinbase,
        "economic_values_printed": False,
        "raw_payloads_persisted": False,
        "authentication_used": False,
        "account_endpoints_used": False,
        "signals_computed": False,
        "outcomes_computed": False,
        "orders_enabled": False,
        "status": "PASS" if all_pass else "FAIL_CLOSED",
    }


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=12.0)
    args = parser.parse_args()
    if args.seconds <= 0 or args.seconds > 60:
        raise ValueError("--seconds must be > 0 and <= 60")
    receipt = await run_probe(args.seconds)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

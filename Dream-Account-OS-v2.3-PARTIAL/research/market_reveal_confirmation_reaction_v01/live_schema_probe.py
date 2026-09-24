"""MRCR non-target public live schema shakedown.

Outputs only schema/transport diagnostics. Economic values are never printed or persisted.
"""

from __future__ import annotations

import asyncio
import json
import sys
import time
from typing import Any

import websockets


BINANCE_URL = (
    "wss://stream.binance.com:9443/stream"
    "?streams=btcusdt@aggTrade/btcusdt@depth@100ms"
)
COINBASE_URL = "wss://advanced-trade-ws.coinbase.com"


def _has(obj: dict[str, Any], fields: set[str]) -> bool:
    return fields.issubset(obj.keys())


async def probe_binance(seconds: float = 6.0) -> dict[str, Any]:
    out = {
        "transport": "UNKNOWN",
        "aggtrade_messages": 0,
        "depth_messages": 0,
        "aggtrade_schema_pass": False,
        "depth_schema_pass": False,
        "depth_sequence_anomaly": False,
        "error": None,
    }
    previous_u = None
    deadline = time.monotonic() + seconds
    try:
        async with websockets.connect(
            BINANCE_URL,
            open_timeout=8,
            close_timeout=2,
            ping_interval=None,
            max_size=2_000_000,
        ) as ws:
            out["transport"] = "PASS"
            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                except asyncio.TimeoutError:
                    continue
                envelope = json.loads(raw)
                data = envelope.get("data", envelope)
                event = data.get("e")
                if event == "aggTrade":
                    out["aggtrade_messages"] += 1
                    out["aggtrade_schema_pass"] = out["aggtrade_schema_pass"] or _has(
                        data, {"E", "s", "a", "p", "q", "T", "m"}
                    )
                elif event == "depthUpdate":
                    out["depth_messages"] += 1
                    out["depth_schema_pass"] = out["depth_schema_pass"] or _has(
                        data, {"E", "s", "U", "u", "b", "a"}
                    )
                    if "U" in data and "u" in data:
                        first = int(data["U"])
                        last = int(data["u"])
                        if previous_u is not None and first > previous_u + 1:
                            out["depth_sequence_anomaly"] = True
                        previous_u = max(previous_u or last, last)
    except Exception as exc:  # sanitized: class only, no payloads
        out["transport"] = "FAIL"
        out["error"] = type(exc).__name__
    return out


async def probe_coinbase(seconds: float = 6.0) -> dict[str, Any]:
    out = {
        "transport": "UNKNOWN",
        "market_trade_messages": 0,
        "level2_messages": 0,
        "market_trade_schema_pass": False,
        "level2_schema_pass": False,
        "sequence_anomaly": False,
        "error": None,
    }
    previous_seq = None
    deadline = time.monotonic() + seconds
    try:
        async with websockets.connect(
            COINBASE_URL,
            open_timeout=8,
            close_timeout=2,
            ping_interval=20,
            max_size=2_000_000,
        ) as ws:
            await ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": ["BTC-USD"],
                "channel": "market_trades",
            }))
            await ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": ["BTC-USD"],
                "channel": "level2",
            }))
            out["transport"] = "PASS"
            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                except asyncio.TimeoutError:
                    continue
                msg = json.loads(raw)
                channel = msg.get("channel")
                seq = msg.get("sequence_num")
                if isinstance(seq, int):
                    if previous_seq is not None and seq > previous_seq + 1:
                        out["sequence_anomaly"] = True
                    previous_seq = max(previous_seq if previous_seq is not None else seq, seq)

                if channel == "market_trades":
                    out["market_trade_messages"] += 1
                    for event in msg.get("events", []):
                        for trade in event.get("trades", []):
                            if _has(
                                trade,
                                {"trade_id", "product_id", "price", "size", "side", "time"},
                            ):
                                out["market_trade_schema_pass"] = True
                elif channel in {"l2_data", "level2"}:
                    out["level2_messages"] += 1
                    for event in msg.get("events", []):
                        if "product_id" not in event:
                            continue
                        for update in event.get("updates", []):
                            if _has(
                                update,
                                {"side", "event_time", "price_level", "new_quantity"},
                            ):
                                out["level2_schema_pass"] = True
    except Exception as exc:
        out["transport"] = "FAIL"
        out["error"] = type(exc).__name__
    return out


async def main() -> int:
    binance, coinbase = await asyncio.gather(
        probe_binance(),
        probe_coinbase(),
    )
    receipt = {
        "probe": "MRCR_NON_TARGET_LIVE_SCHEMA_SHAKEDOWN_V01",
        "economic_values_persisted": False,
        "raw_payloads_persisted": False,
        "binance": binance,
        "coinbase": coinbase,
    }
    print(json.dumps(receipt, sort_keys=True))
    both_schema = (
        binance["transport"] == "PASS"
        and binance["aggtrade_schema_pass"]
        and binance["depth_schema_pass"]
        and coinbase["transport"] == "PASS"
        and coinbase["market_trade_schema_pass"]
        and coinbase["level2_schema_pass"]
    )
    return 0 if both_schema else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

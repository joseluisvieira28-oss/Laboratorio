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
from websockets.exceptions import ConnectionClosed, InvalidStatus


BINANCE_ENDPOINTS = [
    (
        "MARKET_DATA_ONLY",
        "wss://data-stream.binance.vision:443/stream"
        "?streams=btcusdt@aggTrade/btcusdt@depth@100ms",
    ),
    (
        "PRIMARY_SPOT",
        "wss://stream.binance.com:9443/stream"
        "?streams=btcusdt@aggTrade/btcusdt@depth@100ms",
    ),
]
COINBASE_URL = "wss://advanced-trade-ws.coinbase.com"


def _has(obj: dict[str, Any], fields: set[str]) -> bool:
    return fields.issubset(obj.keys())


def _http_status(exc: Exception) -> int | None:
    if isinstance(exc, InvalidStatus):
        response = getattr(exc, "response", None)
        return getattr(response, "status_code", None)
    return None


async def _probe_binance_endpoint(label: str, url: str, seconds: float) -> dict[str, Any]:
    out = {
        "endpoint_label": label,
        "transport": "UNKNOWN",
        "aggtrade_messages": 0,
        "depth_messages": 0,
        "aggtrade_schema_pass": False,
        "depth_schema_pass": False,
        "depth_sequence_anomaly": False,
        "error": None,
        "http_status": None,
    }
    previous_u = None
    deadline = time.monotonic() + seconds
    try:
        async with websockets.connect(
            url,
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
    except Exception as exc:
        out["transport"] = "FAIL"
        out["error"] = type(exc).__name__
        out["http_status"] = _http_status(exc)
    return out


async def probe_binance(seconds: float = 6.0) -> dict[str, Any]:
    attempts: list[dict[str, Any]] = []
    for label, url in BINANCE_ENDPOINTS:
        result = await _probe_binance_endpoint(label, url, seconds)
        attempts.append(dict(result))
        if (
            result["transport"] == "PASS"
            and result["aggtrade_schema_pass"]
            and result["depth_schema_pass"]
        ):
            final = dict(result)
            final["attempts"] = list(attempts)
            return final
    final = dict(attempts[-1])
    final["attempts"] = list(attempts)
    return final


async def probe_coinbase(seconds: float = 6.0) -> dict[str, Any]:
    out = {
        "transport": "UNKNOWN",
        "market_trade_messages": 0,
        "level2_messages": 0,
        "heartbeat_messages": 0,
        "market_trade_schema_pass": False,
        "level2_schema_pass": False,
        "sequence_anomaly": None,
        "sequence_scope": "NOT_ADJUDICATED_MULTI_CHANNEL",
        "channels_seen": [],
        "error": None,
        "close_code": None,
    }
    channels_seen: set[str] = set()
    deadline = time.monotonic() + seconds
    try:
        async with websockets.connect(
            COINBASE_URL,
            open_timeout=8,
            close_timeout=2,
            ping_interval=20,
            max_size=2_000_000,
        ) as ws:
            for channel in ("heartbeats", "market_trades", "level2"):
                msg = {"type": "subscribe", "channel": channel}
                if channel != "heartbeats":
                    msg["product_ids"] = ["BTC-USD"]
                await ws.send(json.dumps(msg))

            out["transport"] = "PASS"
            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                except asyncio.TimeoutError:
                    continue
                msg = json.loads(raw)
                channel = str(msg.get("channel", "UNKNOWN"))
                channels_seen.add(channel)

                if channel == "heartbeats":
                    out["heartbeat_messages"] += 1
                elif channel == "market_trades":
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
    except ConnectionClosed as exc:
        out["transport"] = "FAIL"
        out["error"] = type(exc).__name__
        out["close_code"] = getattr(exc, "code", None)
    except Exception as exc:
        out["transport"] = "FAIL"
        out["error"] = type(exc).__name__
    out["channels_seen"] = sorted(channels_seen)
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

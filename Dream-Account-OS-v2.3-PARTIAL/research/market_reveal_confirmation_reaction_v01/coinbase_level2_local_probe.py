"""Portable Coinbase Advanced Trade level2 source-only probe.

No raw payloads or economic values are printed or persisted.
Public market-data only. No authentication. No account access.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed


WS_URL = "wss://advanced-trade-ws.coinbase.com"
PRODUCT = "BTC-USD"
REQUIRED_UPDATE_FIELDS = {
    "side",
    "event_time",
    "price_level",
    "new_quantity",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=12.0)
    parser.add_argument(
        "--heartbeat",
        action="store_true",
        help="also subscribe to public heartbeats",
    )
    return parser.parse_args()


async def run_probe(seconds: float, heartbeat: bool) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "probe": "MRCR_COINBASE_L2_ALTERNATE_HOST_V01",
        "transport": "UNKNOWN",
        "subscription_ack": False,
        "l2_snapshot_seen": False,
        "l2_update_seen": False,
        "l2_schema_pass": False,
        "l2_message_count": 0,
        "heartbeat_message_count": 0,
        "sequence_anomaly": False,
        "error": None,
        "close_code": None,
        "economic_values_persisted": False,
        "raw_payloads_persisted": False,
        "authentication_used": False,
    }
    previous_l2_sequence: int | None = None
    deadline = time.monotonic() + seconds

    try:
        async with websockets.connect(
            WS_URL,
            open_timeout=8,
            close_timeout=2,
            ping_interval=20,
            max_size=2_000_000,
        ) as ws:
            receipt["transport"] = "PASS"

            await ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": [PRODUCT],
                "channel": "level2",
            }))

            if heartbeat:
                await ws.send(json.dumps({
                    "type": "subscribe",
                    "channel": "heartbeats",
                }))

            while time.monotonic() < deadline:
                try:
                    raw = await asyncio.wait_for(ws.recv(), timeout=1.5)
                except asyncio.TimeoutError:
                    continue

                msg = json.loads(raw)
                channel = str(msg.get("channel", ""))

                if channel == "subscriptions":
                    receipt["subscription_ack"] = True
                    continue

                if channel == "heartbeats":
                    receipt["heartbeat_message_count"] += 1
                    continue

                if channel not in {"l2_data", "level2"}:
                    continue

                receipt["l2_message_count"] += 1
                sequence = msg.get("sequence_num")
                if isinstance(sequence, int):
                    if (
                        previous_l2_sequence is not None
                        and sequence > previous_l2_sequence + 1
                    ):
                        receipt["sequence_anomaly"] = True
                    if (
                        previous_l2_sequence is None
                        or sequence > previous_l2_sequence
                    ):
                        previous_l2_sequence = sequence

                for event in msg.get("events", []):
                    if event.get("product_id") != PRODUCT:
                        continue
                    event_type = event.get("type")
                    if event_type == "snapshot":
                        receipt["l2_snapshot_seen"] = True
                    elif event_type == "update":
                        receipt["l2_update_seen"] = True

                    for update in event.get("updates", []):
                        if REQUIRED_UPDATE_FIELDS.issubset(update.keys()):
                            receipt["l2_schema_pass"] = True

                if (
                    receipt["subscription_ack"]
                    and receipt["l2_snapshot_seen"]
                    and receipt["l2_schema_pass"]
                ):
                    break

    except ConnectionClosed as exc:
        receipt["transport"] = "FAIL"
        receipt["error"] = type(exc).__name__
        receipt["close_code"] = getattr(exc, "code", None)
    except Exception as exc:
        receipt["transport"] = "FAIL"
        receipt["error"] = type(exc).__name__

    return receipt


async def main() -> int:
    args = parse_args()
    if args.seconds <= 0 or args.seconds > 60:
        raise ValueError("--seconds must be > 0 and <= 60")

    receipt = await run_probe(args.seconds, args.heartbeat)
    print(json.dumps(receipt, sort_keys=True))

    passed = (
        receipt["transport"] == "PASS"
        and receipt["subscription_ack"]
        and receipt["l2_snapshot_seen"]
        and receipt["l2_schema_pass"]
    )
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

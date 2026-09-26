"""Local non-target Coinbase L2 shadow collector for MRCR V0.1.

Public market-data only. Exact raw payloads are stored locally with hashes and
arrival timestamps. No outcomes, signals, orders, auth or account access.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys
import time
from typing import Any
import uuid

import websockets
from websockets.exceptions import ConnectionClosed

from decision_boundary import rfc3339_to_ns
from shadow_journal import (
    connect_journal,
    finish_session,
    ingest_message,
    message_count,
    start_session,
)
from shadow_recovery import (
    replay_coinbase_level2_session,
    verify_session_chain,
)


COLLECTOR_VERSION = "MRCR_COINBASE_L2_SHADOW_V01"
WS_URL = "wss://advanced-trade-ws.coinbase.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--product", default="BTC-USD")
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument(
        "--db",
        type=Path,
        required=True,
        help="Local SQLite journal path.",
    )
    return parser.parse_args()


def _extract_metadata(
    msg: dict[str, Any],
    *,
    transport_product: str,
) -> tuple[str, str | None, int | None, str | None, int | None]:
    channel = str(msg.get("channel", "UNKNOWN"))
    sequence_num = msg.get("sequence_num")
    if not isinstance(sequence_num, int):
        sequence_num = None

    envelope_timestamp = msg.get("timestamp")
    if not isinstance(envelope_timestamp, str):
        envelope_timestamp = None

    product_id: str | None = None
    source_times: list[int] = []

    if envelope_timestamp:
        try:
            source_times.append(rfc3339_to_ns(envelope_timestamp))
        except ValueError:
            pass

    for event in msg.get("events", []):
        if not isinstance(event, dict):
            continue
        candidate_product = event.get("product_id")
        if candidate_product == transport_product:
            product_id = transport_product
        for update in event.get("updates", []):
            if not isinstance(update, dict):
                continue
            event_time = update.get("event_time")
            if isinstance(event_time, str):
                try:
                    source_times.append(rfc3339_to_ns(event_time))
                except ValueError:
                    pass

    return (
        channel,
        product_id,
        sequence_num,
        envelope_timestamp,
        max(source_times) if source_times else None,
    )


async def run_collector(
    *,
    product: str,
    seconds: float,
    db_path: Path,
) -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    started_wall_ns = time.time_ns()
    started_monotonic_ns = time.monotonic_ns()

    conn = connect_journal(db_path)
    start_session(
        conn,
        session_id=session_id,
        collector_version=COLLECTOR_VERSION,
        endpoint=WS_URL,
        product_id=product,
        started_wall_ns=started_wall_ns,
        started_monotonic_ns=started_monotonic_ns,
    )

    transport = "UNKNOWN"
    subscription_ack = False
    l2_snapshot_seen = False
    l2_update_messages = 0
    heartbeat_messages = 0
    inserted_messages = 0
    deduped_messages = 0
    sequence_anomaly = False
    previous_ws_sequence: int | None = None
    error_class: str | None = None
    close_code: int | None = None

    deadline = time.monotonic() + seconds

    try:
        async with websockets.connect(
            WS_URL,
            proxy=None,
            open_timeout=8,
            close_timeout=2,
            ping_interval=20,
            max_size=16_000_000,
        ) as ws:
            transport = "PASS"

            await ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": [product],
                "channel": "level2",
            }))

            while time.monotonic() < deadline:
                try:
                    raw_text = await asyncio.wait_for(ws.recv(), timeout=1.5)
                except asyncio.TimeoutError:
                    continue

                if not isinstance(raw_text, str):
                    raise ValueError("binary websocket payload is unsupported")

                collector_wall_ns = time.time_ns()
                collector_monotonic_ns = time.monotonic_ns()
                raw_bytes = raw_text.encode("utf-8")

                try:
                    msg = json.loads(raw_text)
                except json.JSONDecodeError:
                    msg = {"channel": "INVALID_JSON"}

                if not isinstance(msg, dict):
                    msg = {"channel": "INVALID_JSON"}

                (
                    channel,
                    product_id,
                    sequence_num,
                    envelope_timestamp,
                    source_time_max_ns,
                ) = _extract_metadata(
                    msg,
                    transport_product=product,
                )

                ingested = ingest_message(
                    conn,
                    session_id=session_id,
                    channel=channel,
                    product_id=product_id,
                    sequence_num=sequence_num,
                    envelope_timestamp=envelope_timestamp,
                    source_time_max_ns=source_time_max_ns,
                    collector_wall_ns=collector_wall_ns,
                    collector_monotonic_ns=collector_monotonic_ns,
                    raw_payload=raw_bytes,
                )
                if ingested.inserted:
                    inserted_messages += 1
                else:
                    deduped_messages += 1

                if sequence_num is None:
                    sequence_anomaly = True
                    raise RuntimeError("websocket message missing integer sequence_num")
                if (
                    previous_ws_sequence is not None
                    and sequence_num != previous_ws_sequence + 1
                ):
                    sequence_anomaly = True
                    raise RuntimeError("websocket sequence discontinuity detected")
                previous_ws_sequence = sequence_num

                if channel == "subscriptions":
                    subscription_ack = True
                    continue

                if channel not in {"l2_data", "level2"}:
                    continue

                for event in msg.get("events", []):
                    if not isinstance(event, dict):
                        continue
                    if event.get("product_id") != product:
                        continue
                    if event.get("type") == "snapshot":
                        l2_snapshot_seen = True
                    elif event.get("type") == "update":
                        l2_update_messages += 1

    except ConnectionClosed as exc:
        transport = "FAIL"
        error_class = type(exc).__name__
        close_code = getattr(exc, "code", None)
    except Exception as exc:
        transport = "FAIL"
        error_class = type(exc).__name__
    finally:
        chain = verify_session_chain(conn, session_id=session_id)
        recovery = replay_coinbase_level2_session(
            conn,
            session_id=session_id,
            product_id=product,
        )
        status = (
            "PASS"
            if (
                transport == "PASS"
                and subscription_ack
                and l2_snapshot_seen
                and not sequence_anomaly
                and chain.ok
                and recovery.ok
            )
            else "FAIL_CLOSED"
        )
        finish_session(
            conn,
            session_id=session_id,
            ended_wall_ns=time.time_ns(),
            status=status,
            terminal_error_class=error_class,
        )
        persisted = message_count(conn, session_id)
        conn.close()

    return {
        "collector": COLLECTOR_VERSION,
        "session_id": session_id,
        "transport_fixture_product": product,
        "websocket_proxy_mode": "DIRECT_NO_PROXY",
        "transport_fixture_is_scientific_target": False,
        "transport": transport,
        "subscription_ack": subscription_ack,
        "l2_snapshot_seen": l2_snapshot_seen,
        "l2_update_messages": l2_update_messages,
        "heartbeat_messages": heartbeat_messages,
        "heartbeat_subscription_used": False,
        "inserted_messages": inserted_messages,
        "deduped_messages": deduped_messages,
        "persisted_messages": persisted,
        "sequence_anomaly": sequence_anomaly,
        "chain_integrity_pass": chain.ok,
        "recovery_pass": recovery.ok,
        "recovery_failure_reason": recovery.failure_reason,
        "recovered_final_sequence": recovery.final_sequence,
        "raw_payloads_persisted_local_only": True,
        "authentication_used": False,
        "account_endpoints_used": False,
        "signals_computed": False,
        "outcomes_computed": False,
        "orders_enabled": False,
        "error_class": error_class,
        "close_code": close_code,
        "status": status,
    }


async def main() -> int:
    args = parse_args()
    if args.seconds <= 0 or args.seconds > 3600:
        raise ValueError("--seconds must be > 0 and <= 3600")
    if not args.product or "/" in args.product or "\\" in args.product:
        raise ValueError("invalid transport fixture product")

    receipt = await run_collector(
        product=args.product,
        seconds=args.seconds,
        db_path=args.db,
    )
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

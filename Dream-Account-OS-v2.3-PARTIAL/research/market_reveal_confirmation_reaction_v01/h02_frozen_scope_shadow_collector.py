"""Local source-only shadow collector for the exact frozen MRCR H02 scope.

Frozen scope only:
- Binance Spot BTCUSDT + ETHUSDT: aggTrade + diff depth@100ms
- Coinbase Advanced Spot BTC-USD + ETH-USD: level2 and market_trades

Raw public payloads are persisted locally in a tamper-evident journal with
source and collector-arrival clocks. No target schedule, classifier, future
outcome, account endpoint, authentication, order or exchange mutation exists.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys
import time
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import uuid

import websockets
from websockets.exceptions import ConnectionClosed

from decision_boundary import epoch_ms_to_ns, rfc3339_to_ns
from h02_scope_journal import (
    connect_scope_journal,
    finish_scope_session,
    ingest_scope_record,
    session_record_count,
    start_scope_session,
)
from h02_scope_recovery import (
    replay_binance_scope_session,
    replay_coinbase_level2_scope_session,
    verify_coinbase_market_trades_scope_session,
    verify_scope_batch,
    verify_scope_session_chain,
)


COLLECTOR_VERSION = "MRCR_H02_FROZEN_SCOPE_SHADOW_V01_1"
BINANCE_WS_BASE = "wss://data-stream.binance.vision:443/stream?streams="
BINANCE_REST_DEPTH = "https://data-api.binance.vision/api/v3/depth"
COINBASE_WS = "wss://advanced-trade-ws.coinbase.com"

BINANCE_SYMBOLS = ("BTCUSDT", "ETHUSDT")
COINBASE_PRODUCTS = ("BTC-USD", "ETH-USD")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=float, default=60.0)
    parser.add_argument("--db", type=Path, required=True)
    return parser.parse_args()


def _fetch_binance_snapshot(symbol: str) -> tuple[bytes, int, int, int]:
    query = urlencode({"symbol": symbol, "limit": 5000})
    request = Request(
        BINANCE_REST_DEPTH + "?" + query,
        headers={
            "Accept": "application/json",
            "User-Agent": "MRCR-H02-Frozen-Scope-Shadow/0.1",
        },
        method="GET",
    )
    with urlopen(request, timeout=8) as response:
        raw = response.read()
        status = getattr(response, "status", 200)
        if int(status) != 200:
            raise RuntimeError(f"Binance public depth snapshot HTTP {status}")
    wall_ns = time.time_ns()
    monotonic_ns = time.monotonic_ns()
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("Binance snapshot must be an object")
    last_update_id = int(value["lastUpdateId"])
    if not isinstance(value.get("bids"), list) or not isinstance(value.get("asks"), list):
        raise ValueError("Binance snapshot missing bids/asks")
    return raw, last_update_id, wall_ns, monotonic_ns


def _binance_source_bounds(data: dict[str, Any]) -> tuple[int | None, int | None]:
    values: list[int] = []
    for key in ("T", "E"):
        value = data.get(key)
        if isinstance(value, int):
            values.append(epoch_ms_to_ns(value))
    if not values:
        return None, None
    return min(values), max(values)


def _coinbase_source_bounds(
    msg: dict[str, Any],
    *,
    product: str,
    subscribed_channel: str,
) -> tuple[int | None, int | None]:
    values: list[int] = []
    envelope = msg.get("timestamp")
    if isinstance(envelope, str) and envelope:
        try:
            values.append(rfc3339_to_ns(envelope))
        except ValueError:
            pass

    if subscribed_channel == "level2":
        for event in msg.get("events", []):
            if not isinstance(event, dict) or event.get("product_id") != product:
                continue
            if event.get("type") == "snapshot":
                # Per-level snapshot event_time may be epoch zero; envelope time is authoritative.
                continue
            for update in event.get("updates", []):
                if not isinstance(update, dict):
                    continue
                event_time = update.get("event_time")
                if isinstance(event_time, str) and event_time:
                    values.append(rfc3339_to_ns(event_time))
    elif subscribed_channel == "market_trades":
        for event in msg.get("events", []):
            if not isinstance(event, dict):
                continue
            for trade in event.get("trades", []):
                if not isinstance(trade, dict) or trade.get("product_id") != product:
                    continue
                trade_time = trade.get("time")
                if isinstance(trade_time, str) and trade_time:
                    values.append(rfc3339_to_ns(trade_time))

    if not values:
        return None, None
    return min(values), max(values)


async def _collect_binance_symbol(
    *,
    batch_id: str,
    symbol: str,
    seconds: float,
    db_path: Path,
) -> dict[str, Any]:
    session_id = str(uuid.uuid4())
    stream = symbol.lower()
    endpoint = (
        BINANCE_WS_BASE
        + f"{stream}@aggTrade/{stream}@depth@100ms"
    )
    conn = connect_scope_journal(db_path)
    start_scope_session(
        conn,
        session_id=session_id,
        batch_id=batch_id,
        collector_version=COLLECTOR_VERSION,
        venue="BINANCE_SPOT",
        native_symbol=symbol,
        stream_group="BINANCE_TRADES_DEPTH",
        endpoint=endpoint,
        started_wall_ns=time.time_ns(),
        started_monotonic_ns=time.monotonic_ns(),
    )

    transport = "UNKNOWN"
    snapshot_seen = False
    aggtrade_messages = 0
    depth_messages = 0
    inserted = 0
    deduped = 0
    error_class: str | None = None
    close_code: int | None = None
    snapshot_task: asyncio.Task | None = None
    buffered_before_snapshot: list[dict[str, Any]] = []

    def persist_record(record: dict[str, Any]) -> None:
        nonlocal inserted, deduped
        result = ingest_scope_record(
            conn,
            session_id=session_id,
            venue="BINANCE_SPOT",
            native_symbol=symbol,
            transport=str(record["transport"]),
            message_kind=str(record["message_kind"]),
            channel=str(record["channel"]),
            sequence_first=record["sequence_first"],
            sequence_last=record["sequence_last"],
            source_time_min_ns=record["source_time_min_ns"],
            source_time_max_ns=record["source_time_max_ns"],
            collector_wall_ns=int(record["collector_wall_ns"]),
            collector_monotonic_ns=int(record["collector_monotonic_ns"]),
            raw_payload=bytes(record["raw_payload"]),
        )
        inserted += int(result.inserted)
        deduped += int(not result.inserted)

    async def flush_snapshot_and_buffer(*, wait: bool = False) -> None:
        nonlocal snapshot_seen, snapshot_task, buffered_before_snapshot
        if snapshot_seen or snapshot_task is None:
            return
        if not snapshot_task.done() and not wait:
            return
        if wait and not snapshot_task.done():
            raw, last_id, wall_ns, mono_ns = await asyncio.wait_for(
                snapshot_task, timeout=10
            )
        else:
            raw, last_id, wall_ns, mono_ns = snapshot_task.result()

        snapshot_record = {
            "transport": "REST",
            "message_kind": "BINANCE_DEPTH_SNAPSHOT",
            "channel": "REST_DEPTH_SNAPSHOT",
            "sequence_first": last_id,
            "sequence_last": last_id,
            "source_time_min_ns": None,
            "source_time_max_ns": None,
            "collector_wall_ns": wall_ns,
            "collector_monotonic_ns": mono_ns,
            "raw_payload": raw,
        }
        pending = [*buffered_before_snapshot, snapshot_record]
        pending.sort(
            key=lambda row: (
                int(row["collector_monotonic_ns"]),
                int(row["collector_wall_ns"]),
                str(row["message_kind"]),
            )
        )
        for record in pending:
            persist_record(record)
        buffered_before_snapshot = []
        snapshot_seen = True

    try:
        async with websockets.connect(
            endpoint,
            proxy=None,
            compression=None,
            open_timeout=8,
            close_timeout=2,
            ping_interval=20,
            max_size=4_000_000,
        ) as ws:
            transport = "PASS"
            snapshot_task = asyncio.create_task(
                asyncio.to_thread(_fetch_binance_snapshot, symbol)
            )
            deadline = time.monotonic() + seconds

            while time.monotonic() < deadline:
                await flush_snapshot_and_buffer()
                try:
                    raw_text = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                if not isinstance(raw_text, str):
                    raise ValueError("binary Binance websocket payload is unsupported")

                wall_ns = time.time_ns()
                mono_ns = time.monotonic_ns()
                raw = raw_text.encode("utf-8")
                envelope = json.loads(raw_text)
                if not isinstance(envelope, dict):
                    raise ValueError("Binance combined payload is not an object")
                channel = str(envelope.get("stream", "UNKNOWN"))
                data = envelope.get("data", envelope)
                if not isinstance(data, dict):
                    raise ValueError("Binance data payload is not an object")
                event = data.get("e")

                if event == "aggTrade":
                    if data.get("s") != symbol:
                        raise ValueError("Binance aggTrade symbol mismatch")
                    sequence_first = sequence_last = int(data["a"])
                    kind = "BINANCE_AGGTRADE"
                    aggtrade_messages += 1
                elif event == "depthUpdate":
                    if data.get("s") != symbol:
                        raise ValueError("Binance depth symbol mismatch")
                    sequence_first = int(data["U"])
                    sequence_last = int(data["u"])
                    if sequence_first > sequence_last:
                        raise ValueError("Binance depth update interval invalid")
                    kind = "BINANCE_DEPTH_DIFF"
                    depth_messages += 1
                else:
                    raise RuntimeError(f"unexpected Binance event type: {event}")

                source_min, source_max = _binance_source_bounds(data)
                record = {
                    "transport": "WEBSOCKET",
                    "message_kind": kind,
                    "channel": channel,
                    "sequence_first": sequence_first,
                    "sequence_last": sequence_last,
                    "source_time_min_ns": source_min,
                    "source_time_max_ns": source_max,
                    "collector_wall_ns": wall_ns,
                    "collector_monotonic_ns": mono_ns,
                    "raw_payload": raw,
                }
                if snapshot_seen:
                    persist_record(record)
                else:
                    buffered_before_snapshot.append(record)

            await flush_snapshot_and_buffer(wait=True)

    except ConnectionClosed as exc:
        transport = "FAIL"
        error_class = type(exc).__name__
        close_code = getattr(exc, "code", None)
    except Exception as exc:
        transport = "FAIL"
        error_class = type(exc).__name__

    chain = verify_scope_session_chain(conn, session_id=session_id)
    recovery = replay_binance_scope_session(conn, session_id=session_id)
    status = (
        "PASS"
        if (
            transport == "PASS"
            and snapshot_seen
            and aggtrade_messages > 0
            and depth_messages > 0
            and chain.ok
            and recovery.ok
        )
        else "FAIL_CLOSED"
    )
    finish_scope_session(
        conn,
        session_id=session_id,
        ended_wall_ns=time.time_ns(),
        status=status,
        terminal_error_class=error_class,
    )
    persisted = session_record_count(conn, session_id)
    conn.close()

    return {
        "session_id": session_id,
        "venue": "BINANCE_SPOT",
        "native_symbol": symbol,
        "stream_group": "BINANCE_TRADES_DEPTH",
        "transport": transport,
        "snapshot_seen": snapshot_seen,
        "aggtrade_messages": aggtrade_messages,
        "depth_messages": depth_messages,
        "inserted_records": inserted,
        "deduped_records": deduped,
        "persisted_records": persisted,
        "chain_integrity_pass": chain.ok,
        "recovery_pass": recovery.ok,
        "recovery_failure_reason": recovery.failure_reason,
        "recovered_final_depth_sequence": recovery.final_sequence,
        "error_class": error_class,
        "close_code": close_code,
        "status": status,
    }


async def _collect_coinbase_channel(
    *,
    batch_id: str,
    product: str,
    subscribed_channel: str,
    seconds: float,
    db_path: Path,
) -> dict[str, Any]:
    if subscribed_channel not in {"level2", "market_trades"}:
        raise ValueError("unsupported Coinbase channel")

    session_id = str(uuid.uuid4())
    group = (
        "COINBASE_LEVEL2"
        if subscribed_channel == "level2"
        else "COINBASE_MARKET_TRADES"
    )
    conn = connect_scope_journal(db_path)
    start_scope_session(
        conn,
        session_id=session_id,
        batch_id=batch_id,
        collector_version=COLLECTOR_VERSION,
        venue="COINBASE_ADVANCED_SPOT",
        native_symbol=product,
        stream_group=group,
        endpoint=COINBASE_WS,
        started_wall_ns=time.time_ns(),
        started_monotonic_ns=time.monotonic_ns(),
    )

    transport = "UNKNOWN"
    subscription_ack = False
    data_messages = 0
    snapshot_seen = False
    update_seen = False
    previous_sequence: int | None = None
    sequence_anomaly = False
    inserted = 0
    deduped = 0
    error_class: str | None = None
    close_code: int | None = None

    try:
        async with websockets.connect(
            COINBASE_WS,
            proxy=None,
            compression=None,
            open_timeout=8,
            close_timeout=2,
            ping_interval=20,
            max_size=16_000_000,
        ) as ws:
            await ws.send(json.dumps({
                "type": "subscribe",
                "product_ids": [product],
                "channel": subscribed_channel,
            }, separators=(",", ":")))
            transport = "PASS"
            deadline = time.monotonic() + seconds

            while time.monotonic() < deadline:
                try:
                    raw_text = await asyncio.wait_for(ws.recv(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue
                if not isinstance(raw_text, str):
                    raise ValueError("binary Coinbase websocket payload is unsupported")

                wall_ns = time.time_ns()
                mono_ns = time.monotonic_ns()
                raw = raw_text.encode("utf-8")
                msg = json.loads(raw_text)
                if not isinstance(msg, dict):
                    raise ValueError("Coinbase websocket payload is not an object")

                channel = str(msg.get("channel", "UNKNOWN"))
                sequence = msg.get("sequence_num")
                if not isinstance(sequence, int):
                    sequence_anomaly = True
                    raise RuntimeError("Coinbase message missing integer sequence_num")
                if previous_sequence is not None and sequence != previous_sequence + 1:
                    sequence_anomaly = True
                    raise RuntimeError("Coinbase websocket sequence discontinuity")
                previous_sequence = sequence

                if channel == "subscriptions":
                    kind = "COINBASE_CONTROL"
                    subscription_ack = True
                elif subscribed_channel == "level2" and channel in {"l2_data", "level2"}:
                    kind = "COINBASE_LEVEL2"
                    matched_event = False
                    for event in msg.get("events", []):
                        if not isinstance(event, dict) or event.get("product_id") != product:
                            continue
                        matched_event = True
                        if event.get("type") == "snapshot":
                            snapshot_seen = True
                        elif event.get("type") == "update":
                            update_seen = True
                    if matched_event:
                        data_messages += 1
                elif subscribed_channel == "market_trades" and channel == "market_trades":
                    kind = "COINBASE_MARKET_TRADES"
                    matched_trade = False
                    for event in msg.get("events", []):
                        if not isinstance(event, dict):
                            continue
                        for trade in event.get("trades", []):
                            if isinstance(trade, dict) and trade.get("product_id") == product:
                                matched_trade = True
                    if matched_trade:
                        data_messages += 1
                else:
                    raise RuntimeError(
                        f"unexpected Coinbase channel for {subscribed_channel}: {channel}"
                    )

                source_min, source_max = _coinbase_source_bounds(
                    msg,
                    product=product,
                    subscribed_channel=subscribed_channel,
                )
                result = ingest_scope_record(
                    conn,
                    session_id=session_id,
                    venue="COINBASE_ADVANCED_SPOT",
                    native_symbol=product,
                    transport="WEBSOCKET",
                    message_kind=kind,
                    channel=channel,
                    sequence_first=sequence,
                    sequence_last=sequence,
                    source_time_min_ns=source_min,
                    source_time_max_ns=source_max,
                    collector_wall_ns=wall_ns,
                    collector_monotonic_ns=mono_ns,
                    raw_payload=raw,
                )
                inserted += int(result.inserted)
                deduped += int(not result.inserted)

    except ConnectionClosed as exc:
        transport = "FAIL"
        error_class = type(exc).__name__
        close_code = getattr(exc, "code", None)
    except Exception as exc:
        transport = "FAIL"
        error_class = type(exc).__name__

    chain = verify_scope_session_chain(conn, session_id=session_id)
    if subscribed_channel == "level2":
        recovery = replay_coinbase_level2_scope_session(conn, session_id=session_id)
        data_ready = snapshot_seen and update_seen and data_messages > 0
    else:
        recovery = verify_coinbase_market_trades_scope_session(
            conn, session_id=session_id
        )
        data_ready = data_messages > 0

    status = (
        "PASS"
        if (
            transport == "PASS"
            and subscription_ack
            and not sequence_anomaly
            and data_ready
            and chain.ok
            and recovery.ok
        )
        else "FAIL_CLOSED"
    )
    finish_scope_session(
        conn,
        session_id=session_id,
        ended_wall_ns=time.time_ns(),
        status=status,
        terminal_error_class=error_class,
    )
    persisted = session_record_count(conn, session_id)
    conn.close()

    return {
        "session_id": session_id,
        "venue": "COINBASE_ADVANCED_SPOT",
        "native_symbol": product,
        "stream_group": group,
        "subscribed_channel": subscribed_channel,
        "transport": transport,
        "subscription_ack": subscription_ack,
        "data_messages": data_messages,
        "snapshot_seen": snapshot_seen if subscribed_channel == "level2" else None,
        "update_seen": update_seen if subscribed_channel == "level2" else None,
        "sequence_anomaly": sequence_anomaly,
        "inserted_records": inserted,
        "deduped_records": deduped,
        "persisted_records": persisted,
        "chain_integrity_pass": chain.ok,
        "recovery_pass": recovery.ok,
        "recovery_failure_reason": recovery.failure_reason,
        "recovered_final_sequence": recovery.final_sequence,
        "error_class": error_class,
        "close_code": close_code,
        "status": status,
    }


async def run_scope_shadow(
    *,
    seconds: float,
    db_path: Path,
) -> dict[str, Any]:
    batch_id = str(uuid.uuid4())

    tasks = [
        *(
            _collect_binance_symbol(
                batch_id=batch_id,
                symbol=symbol,
                seconds=seconds,
                db_path=db_path,
            )
            for symbol in BINANCE_SYMBOLS
        ),
        *(
            _collect_coinbase_channel(
                batch_id=batch_id,
                product=product,
                subscribed_channel=channel,
                seconds=seconds,
                db_path=db_path,
            )
            for product in COINBASE_PRODUCTS
            for channel in ("level2", "market_trades")
        ),
    ]
    session_receipts = await asyncio.gather(*tasks)

    verify_conn = connect_scope_journal(db_path)
    batch = verify_scope_batch(verify_conn, batch_id=batch_id)
    verify_conn.close()

    all_sessions_pass = all(row["status"] == "PASS" for row in session_receipts)
    status = "PASS" if all_sessions_pass and batch.ok else "FAIL_CLOSED"

    return {
        "collector": COLLECTOR_VERSION,
        "batch_id": batch_id,
        "scope": {
            "binance_spot": list(BINANCE_SYMBOLS),
            "coinbase_advanced_spot": list(COINBASE_PRODUCTS),
            "binance_channels": ["aggTrade", "depth@100ms", "REST_DEPTH_SNAPSHOT"],
            "coinbase_channels": ["level2", "market_trades"],
        },
        "sessions": session_receipts,
        "batch_recovery_pass": batch.ok,
        "batch_session_count": batch.session_count,
        "batch_passed_session_count": batch.passed_session_count,
        "batch_blockers": list(batch.blockers),
        "raw_payloads_persisted_local_only": True,
        "source_and_collector_arrival_preserved": True,
        "authentication_used": False,
        "account_endpoints_used": False,
        "signals_computed": False,
        "outcomes_computed": False,
        "orders_enabled": False,
        "target_schedule_used": False,
        "target_observation_authorized": False,
        "scientific_use": "SOURCE_INFRASTRUCTURE_HARDENING_ONLY",
        "promotion_credit": "NONE",
        "status": status,
    }


async def main() -> int:
    args = parse_args()
    if args.seconds <= 0 or args.seconds > 3600:
        raise ValueError("--seconds must be > 0 and <= 3600")
    receipt = await run_scope_shadow(seconds=args.seconds, db_path=args.db)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["status"] == "PASS" else 2


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

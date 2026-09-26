"""Offline integrity and recovery for the frozen MRCR H02 source scope.

No network access. This module validates persisted public-market-data evidence
without computing the H02 classifier, future outcomes, economics or orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
import sqlite3
from typing import Any

from decision_boundary import epoch_ms_to_ns, rfc3339_to_ns
from h02_scope_journal import (
    ZERO_HASH,
    chain_sha256,
    raw_sha256,
    sqlite_integrity_ok,
)
from order_book import BookSequenceGap, LocalOrderBook
from source_adapters import (
    parse_binance_aggtrade,
    parse_binance_depth_update,
    parse_coinbase_level2_event,
    parse_coinbase_market_trade,
)


EXPECTED_BATCH_SCOPE = {
    ("BINANCE_SPOT", "BTCUSDT", "BINANCE_TRADES_DEPTH"),
    ("BINANCE_SPOT", "ETHUSDT", "BINANCE_TRADES_DEPTH"),
    ("COINBASE_ADVANCED_SPOT", "BTC-USD", "COINBASE_LEVEL2"),
    ("COINBASE_ADVANCED_SPOT", "ETH-USD", "COINBASE_LEVEL2"),
    ("COINBASE_ADVANCED_SPOT", "BTC-USD", "COINBASE_MARKET_TRADES"),
    ("COINBASE_ADVANCED_SPOT", "ETH-USD", "COINBASE_MARKET_TRADES"),
}


@dataclass(frozen=True)
class ScopeChainVerification:
    ok: bool
    message_count: int
    chain_head_sha256: str | None
    failure_reason: str | None


@dataclass(frozen=True)
class FeedRecovery:
    ok: bool
    record_count: int
    data_message_count: int
    final_sequence: int | None
    failure_reason: str | None


@dataclass(frozen=True)
class BatchRecovery:
    ok: bool
    batch_id: str
    session_count: int
    passed_session_count: int
    blockers: tuple[str, ...]


def _load_object(raw_payload: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw_payload.decode("utf-8"))
    except Exception as exc:
        raise ValueError("persisted payload is not valid UTF-8 JSON") from exc
    if not isinstance(value, dict):
        raise ValueError("persisted payload must decode to an object")
    return value


def verify_scope_session_chain(
    conn: sqlite3.Connection,
    *,
    session_id: str,
) -> ScopeChainVerification:
    if not sqlite_integrity_ok(conn):
        return ScopeChainVerification(
            ok=False,
            message_count=0,
            chain_head_sha256=None,
            failure_reason="SQLITE_INTEGRITY_CHECK_FAILED",
        )

    rows = conn.execute(
        """
        SELECT *
        FROM scope_records
        WHERE session_id=?
        ORDER BY ordinal
        """,
        (session_id,),
    ).fetchall()

    previous_chain = ZERO_HASH
    expected_ordinal = 1
    previous_monotonic_ns: int | None = None
    for row in rows:
        ordinal = int(row["ordinal"])
        if ordinal != expected_ordinal:
            return ScopeChainVerification(
                False, len(rows), None, "ORDINAL_GAP"
            )
        raw_payload = bytes(row["raw_payload"])
        computed_raw = raw_sha256(raw_payload)
        if computed_raw != row["raw_sha256"]:
            return ScopeChainVerification(
                False, len(rows), None, "RAW_SHA256_MISMATCH"
            )
        if row["previous_chain_sha256"] != previous_chain:
            return ScopeChainVerification(
                False, len(rows), None, "PREVIOUS_CHAIN_MISMATCH"
            )
        current_monotonic_ns = int(row["collector_monotonic_ns"])
        if (
            previous_monotonic_ns is not None
            and current_monotonic_ns < previous_monotonic_ns
        ):
            return ScopeChainVerification(
                False, len(rows), None, "COLLECTOR_MONOTONIC_REVERSAL"
            )
        computed_chain = chain_sha256(
            previous_chain_sha256=previous_chain,
            session_id=str(row["session_id"]),
            ordinal=ordinal,
            venue=str(row["venue"]),
            native_symbol=str(row["native_symbol"]),
            transport=str(row["transport"]),
            message_kind=str(row["message_kind"]),
            channel=str(row["channel"]),
            sequence_first=row["sequence_first"],
            sequence_last=row["sequence_last"],
            source_time_min_ns=row["source_time_min_ns"],
            source_time_max_ns=row["source_time_max_ns"],
            collector_wall_ns=int(row["collector_wall_ns"]),
            collector_monotonic_ns=int(row["collector_monotonic_ns"]),
            raw_sha256_hex=computed_raw,
        )
        if computed_chain != row["chain_sha256"]:
            return ScopeChainVerification(
                False, len(rows), None, "CHAIN_SHA256_MISMATCH"
            )
        previous_chain = computed_chain
        previous_monotonic_ns = current_monotonic_ns
        expected_ordinal += 1

    return ScopeChainVerification(
        ok=True,
        message_count=len(rows),
        chain_head_sha256=previous_chain if rows else None,
        failure_reason=None,
    )


def _session_identity(
    conn: sqlite3.Connection,
    session_id: str,
) -> tuple[str, str, str]:
    row = conn.execute(
        """
        SELECT venue, native_symbol, stream_group
        FROM scope_sessions
        WHERE session_id=?
        """,
        (session_id,),
    ).fetchone()
    if row is None:
        raise ValueError("scope session not found")
    return (
        str(row["venue"]),
        str(row["native_symbol"]),
        str(row["stream_group"]),
    )


def _assert_consecutive_websocket_sequence(rows: list[sqlite3.Row]) -> int | None:
    previous: int | None = None
    final: int | None = None
    for row in rows:
        if row["transport"] != "WEBSOCKET":
            continue
        sequence = row["sequence_last"]
        if not isinstance(sequence, int):
            raise ValueError("websocket record missing integer sequence")
        if previous is not None and sequence != previous + 1:
            raise BookSequenceGap(
                f"websocket sequence discontinuity: previous={previous}, current={sequence}"
            )
        previous = sequence
        final = sequence
    return final


def replay_coinbase_level2_scope_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
) -> FeedRecovery:
    chain = verify_scope_session_chain(conn, session_id=session_id)
    if not chain.ok:
        return FeedRecovery(False, chain.message_count, 0, None, chain.failure_reason)

    venue, product_id, group = _session_identity(conn, session_id)
    if venue != "COINBASE_ADVANCED_SPOT" or group != "COINBASE_LEVEL2":
        return FeedRecovery(False, chain.message_count, 0, None, "SESSION_IDENTITY_MISMATCH")

    rows = conn.execute(
        """
        SELECT *
        FROM scope_records
        WHERE session_id=?
        ORDER BY ordinal
        """,
        (session_id,),
    ).fetchall()
    book = LocalOrderBook(venue=venue, native_symbol=product_id)
    data_messages = 0

    try:
        final_stream_sequence = _assert_consecutive_websocket_sequence(list(rows))
        for row in rows:
            if row["message_kind"] != "COINBASE_LEVEL2":
                continue
            msg = _load_object(bytes(row["raw_payload"]))
            sequence_num = msg.get("sequence_num")
            timestamp = msg.get("timestamp")
            if not isinstance(sequence_num, int):
                raise ValueError("Coinbase level2 message missing sequence_num")
            if not isinstance(timestamp, str) or not timestamp:
                raise ValueError("Coinbase level2 message missing timestamp")

            snapshot_rows = []
            incremental_rows = []
            for event in msg.get("events", []):
                if not isinstance(event, dict) or event.get("product_id") != product_id:
                    continue
                event_type, updates = parse_coinbase_level2_event(
                    event=event,
                    sequence_num=sequence_num,
                    envelope_timestamp=timestamp,
                )
                if event_type == "snapshot":
                    snapshot_rows.extend(updates)
                else:
                    incremental_rows.extend(updates)

            if snapshot_rows and incremental_rows:
                raise ValueError("mixed Coinbase snapshot/update message")
            if snapshot_rows:
                book.initialize_from_snapshot_updates(tuple(snapshot_rows))
                data_messages += 1
            elif incremental_rows:
                if not book.initialized:
                    raise ValueError("Coinbase update arrived before snapshot")
                book.apply_updates(
                    tuple(incremental_rows),
                    coinbase_stream_continuity_verified=True,
                )
                data_messages += 1

        if not book.initialized:
            raise ValueError("Coinbase level2 session has no snapshot")
        return FeedRecovery(
            True,
            len(rows),
            data_messages,
            final_stream_sequence,
            None,
        )
    except Exception as exc:
        return FeedRecovery(
            False,
            len(rows),
            data_messages,
            book.sequence_last if book.initialized else None,
            type(exc).__name__,
        )


def verify_coinbase_market_trades_scope_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
) -> FeedRecovery:
    chain = verify_scope_session_chain(conn, session_id=session_id)
    if not chain.ok:
        return FeedRecovery(False, chain.message_count, 0, None, chain.failure_reason)

    venue, product_id, group = _session_identity(conn, session_id)
    if venue != "COINBASE_ADVANCED_SPOT" or group != "COINBASE_MARKET_TRADES":
        return FeedRecovery(False, chain.message_count, 0, None, "SESSION_IDENTITY_MISMATCH")

    rows = conn.execute(
        """
        SELECT *
        FROM scope_records
        WHERE session_id=?
        ORDER BY ordinal
        """,
        (session_id,),
    ).fetchall()
    data_messages = 0
    unique_trade_ids: set[str] = set()

    try:
        final_sequence = _assert_consecutive_websocket_sequence(list(rows))
        for row in rows:
            if row["message_kind"] != "COINBASE_MARKET_TRADES":
                continue
            msg = _load_object(bytes(row["raw_payload"]))
            envelope_timestamp = msg.get("timestamp")
            if envelope_timestamp is not None and not isinstance(envelope_timestamp, str):
                raise ValueError("invalid Coinbase envelope timestamp")
            valid_in_message = 0
            for event in msg.get("events", []):
                if not isinstance(event, dict):
                    continue
                for trade in event.get("trades", []):
                    if not isinstance(trade, dict) or trade.get("product_id") != product_id:
                        continue
                    parsed = parse_coinbase_market_trade(
                        trade,
                        envelope_timestamp=envelope_timestamp,
                    )
                    rfc3339_to_ns(parsed.trade_time)
                    unique_trade_ids.add(parsed.trade_id)
                    valid_in_message += 1
            if valid_in_message:
                data_messages += 1

        if not unique_trade_ids:
            raise ValueError("no valid Coinbase market trades")
        return FeedRecovery(True, len(rows), data_messages, final_sequence, None)
    except Exception as exc:
        return FeedRecovery(False, len(rows), data_messages, None, type(exc).__name__)


def replay_binance_scope_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
) -> FeedRecovery:
    chain = verify_scope_session_chain(conn, session_id=session_id)
    if not chain.ok:
        return FeedRecovery(False, chain.message_count, 0, None, chain.failure_reason)

    venue, symbol, group = _session_identity(conn, session_id)
    if venue != "BINANCE_SPOT" or group != "BINANCE_TRADES_DEPTH":
        return FeedRecovery(False, chain.message_count, 0, None, "SESSION_IDENTITY_MISMATCH")

    rows = conn.execute(
        """
        SELECT *
        FROM scope_records
        WHERE session_id=?
        ORDER BY ordinal
        """,
        (session_id,),
    ).fetchall()

    snapshots = [row for row in rows if row["message_kind"] == "BINANCE_DEPTH_SNAPSHOT"]
    if len(snapshots) != 1:
        return FeedRecovery(False, len(rows), 0, None, "BINANCE_SNAPSHOT_COUNT_INVALID")

    data_messages = 0
    book = LocalOrderBook(venue=venue, native_symbol=symbol)
    try:
        snapshot = _load_object(bytes(snapshots[0]["raw_payload"]))
        last_update_id = int(snapshot["lastUpdateId"])
        bids = [
            (Decimal(str(level[0])), Decimal(str(level[1])))
            for level in snapshot.get("bids", [])
        ]
        asks = [
            (Decimal(str(level[0])), Decimal(str(level[1])))
            for level in snapshot.get("asks", [])
        ]
        book.load_snapshot_levels(
            bids=bids,
            asks=asks,
            sequence_last=last_update_id,
        )

        depth_rows = [
            row for row in rows
            if row["message_kind"] == "BINANCE_DEPTH_DIFF"
        ]
        depth_rows.sort(
            key=lambda row: (
                int(row["sequence_last"]) if row["sequence_last"] is not None else -1,
                int(row["ordinal"]),
            )
        )
        applied_depth = 0
        for row in depth_rows:
            envelope = _load_object(bytes(row["raw_payload"]))
            data = envelope.get("data", envelope)
            if not isinstance(data, dict) or data.get("s") != symbol:
                raise ValueError("Binance depth symbol mismatch")
            updates = parse_binance_depth_update(data)
            result = book.apply_updates(tuple(updates))
            if result.status == "APPLIED":
                applied_depth += 1
                data_messages += 1

        trade_ids: set[str] = set()
        for row in rows:
            if row["message_kind"] != "BINANCE_AGGTRADE":
                continue
            envelope = _load_object(bytes(row["raw_payload"]))
            data = envelope.get("data", envelope)
            if not isinstance(data, dict) or data.get("s") != symbol:
                raise ValueError("Binance aggTrade symbol mismatch")
            parsed = parse_binance_aggtrade(data)
            epoch_ms_to_ns(parsed.trade_time)
            trade_ids.add(parsed.trade_id)
            data_messages += 1

        if applied_depth == 0:
            raise ValueError("no Binance depth diff bridged/applied after snapshot")
        if not trade_ids:
            raise ValueError("no valid Binance aggTrades")
        return FeedRecovery(
            True,
            len(rows),
            data_messages,
            book.sequence_last,
            None,
        )
    except Exception as exc:
        return FeedRecovery(
            False,
            len(rows),
            data_messages,
            book.sequence_last if book.initialized else None,
            type(exc).__name__,
        )


def verify_scope_batch(
    conn: sqlite3.Connection,
    *,
    batch_id: str,
) -> BatchRecovery:
    sessions = conn.execute(
        """
        SELECT session_id, venue, native_symbol, stream_group, status
        FROM scope_sessions
        WHERE batch_id=?
        ORDER BY venue, native_symbol, stream_group
        """,
        (batch_id,),
    ).fetchall()

    identities = {
        (str(row["venue"]), str(row["native_symbol"]), str(row["stream_group"]))
        for row in sessions
    }
    blockers: list[str] = []
    if identities != EXPECTED_BATCH_SCOPE:
        blockers.append("FROZEN_SCOPE_SESSION_SET_MISMATCH")

    passed = 0
    for row in sessions:
        session_id = str(row["session_id"])
        venue = str(row["venue"])
        group = str(row["stream_group"])
        if row["status"] != "PASS":
            blockers.append(
                f"SESSION_STATUS_NOT_PASS:{venue}:{row['native_symbol']}:{group}:{row['status']}"
            )
            continue
        if venue == "BINANCE_SPOT":
            result = replay_binance_scope_session(conn, session_id=session_id)
        elif group == "COINBASE_LEVEL2":
            result = replay_coinbase_level2_scope_session(conn, session_id=session_id)
        elif group == "COINBASE_MARKET_TRADES":
            result = verify_coinbase_market_trades_scope_session(
                conn, session_id=session_id
            )
        else:
            blockers.append(f"UNSUPPORTED_SESSION:{session_id}")
            continue

        if result.ok:
            passed += 1
        else:
            blockers.append(
                f"SESSION_FAIL:{venue}:{row['native_symbol']}:{group}:{result.failure_reason}"
            )

    return BatchRecovery(
        ok=(not blockers and len(sessions) == len(EXPECTED_BATCH_SCOPE)),
        batch_id=batch_id,
        session_count=len(sessions),
        passed_session_count=passed,
        blockers=tuple(sorted(blockers)),
    )

"""Integrity verification and deterministic replay for MRCR shadow journals."""

from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from typing import Any

from order_book import LocalOrderBook
from shadow_journal import (
    ZERO_HASH,
    chain_sha256,
    raw_sha256,
    sqlite_integrity_ok,
)
from source_adapters import parse_coinbase_level2_event


@dataclass(frozen=True)
class ChainVerification:
    ok: bool
    message_count: int
    chain_head_sha256: str | None
    failure_reason: str | None


@dataclass(frozen=True)
class ReplayRecovery:
    ok: bool
    snapshot_count: int
    update_message_count: int
    final_sequence: int | None
    failure_reason: str | None


def verify_session_chain(
    conn: sqlite3.Connection,
    *,
    session_id: str,
) -> ChainVerification:
    if not sqlite_integrity_ok(conn):
        return ChainVerification(
            ok=False,
            message_count=0,
            chain_head_sha256=None,
            failure_reason="SQLITE_INTEGRITY_CHECK_FAILED",
        )

    rows = conn.execute(
        """
        SELECT *
        FROM shadow_messages
        WHERE session_id=?
        ORDER BY ordinal
        """,
        (session_id,),
    ).fetchall()

    previous_chain = ZERO_HASH
    expected_ordinal = 1

    for row in rows:
        ordinal = int(row["ordinal"])
        if ordinal != expected_ordinal:
            return ChainVerification(
                ok=False,
                message_count=len(rows),
                chain_head_sha256=None,
                failure_reason="ORDINAL_GAP",
            )

        raw_payload = bytes(row["raw_payload"])
        computed_raw = raw_sha256(raw_payload)
        if computed_raw != row["raw_sha256"]:
            return ChainVerification(
                ok=False,
                message_count=len(rows),
                chain_head_sha256=None,
                failure_reason="RAW_SHA256_MISMATCH",
            )

        if row["previous_chain_sha256"] != previous_chain:
            return ChainVerification(
                ok=False,
                message_count=len(rows),
                chain_head_sha256=None,
                failure_reason="PREVIOUS_CHAIN_MISMATCH",
            )

        computed_chain = chain_sha256(
            previous_chain_sha256=previous_chain,
            session_id=str(row["session_id"]),
            ordinal=ordinal,
            channel=str(row["channel"]),
            product_id=row["product_id"],
            sequence_num=row["sequence_num"],
            envelope_timestamp=row["envelope_timestamp"],
            source_time_max_ns=row["source_time_max_ns"],
            collector_wall_ns=int(row["collector_wall_ns"]),
            collector_monotonic_ns=int(row["collector_monotonic_ns"]),
            raw_sha256_hex=computed_raw,
        )
        if computed_chain != row["chain_sha256"]:
            return ChainVerification(
                ok=False,
                message_count=len(rows),
                chain_head_sha256=None,
                failure_reason="CHAIN_SHA256_MISMATCH",
            )

        previous_chain = computed_chain
        expected_ordinal += 1

    return ChainVerification(
        ok=True,
        message_count=len(rows),
        chain_head_sha256=(previous_chain if rows else None),
        failure_reason=None,
    )


def _load_message(raw_payload: bytes) -> dict[str, Any]:
    try:
        value = json.loads(raw_payload.decode("utf-8"))
    except Exception as exc:
        raise ValueError("invalid persisted JSON payload") from exc
    if not isinstance(value, dict):
        raise ValueError("persisted payload must decode to object")
    return value


def replay_coinbase_level2_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    product_id: str,
) -> ReplayRecovery:
    chain = verify_session_chain(conn, session_id=session_id)
    if not chain.ok:
        return ReplayRecovery(
            ok=False,
            snapshot_count=0,
            update_message_count=0,
            final_sequence=None,
            failure_reason=chain.failure_reason,
        )

    rows = conn.execute(
        """
        SELECT ordinal, channel, raw_payload
        FROM shadow_messages
        WHERE session_id=?
        ORDER BY ordinal
        """,
        (session_id,),
    ).fetchall()

    book = LocalOrderBook(
        venue="COINBASE_ADVANCED_SPOT",
        native_symbol=product_id,
    )
    snapshot_count = 0
    update_message_count = 0

    try:
        for row in rows:
            if row["channel"] not in {"l2_data", "level2"}:
                continue

            msg = _load_message(bytes(row["raw_payload"]))
            sequence_num = msg.get("sequence_num")
            envelope_timestamp = msg.get("timestamp")
            if not isinstance(sequence_num, int):
                raise ValueError("level2 payload missing integer sequence_num")
            if not isinstance(envelope_timestamp, str) or not envelope_timestamp:
                raise ValueError("level2 payload missing envelope timestamp")

            for event in msg.get("events", []):
                if not isinstance(event, dict):
                    raise ValueError("level2 event is not object")
                if event.get("product_id") != product_id:
                    continue

                event_type, updates = parse_coinbase_level2_event(
                    event=event,
                    sequence_num=sequence_num,
                    envelope_timestamp=envelope_timestamp,
                )
                if not updates:
                    continue

                if event_type == "snapshot":
                    book.initialize_from_snapshot_updates(updates)
                    snapshot_count += 1
                elif event_type == "update":
                    if not book.initialized:
                        raise ValueError("incremental level2 update before snapshot")
                    book.apply_updates(updates)
                    update_message_count += 1

        if not book.initialized:
            return ReplayRecovery(
                ok=False,
                snapshot_count=snapshot_count,
                update_message_count=update_message_count,
                final_sequence=None,
                failure_reason="NO_LEVEL2_SNAPSHOT",
            )

        return ReplayRecovery(
            ok=True,
            snapshot_count=snapshot_count,
            update_message_count=update_message_count,
            final_sequence=book.sequence_last,
            failure_reason=None,
        )
    except Exception as exc:
        return ReplayRecovery(
            ok=False,
            snapshot_count=snapshot_count,
            update_message_count=update_message_count,
            final_sequence=(book.sequence_last if book.initialized else None),
            failure_reason=type(exc).__name__,
        )

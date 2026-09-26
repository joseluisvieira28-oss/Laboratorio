"""Tamper-evident local journal for the frozen MRCR H02 source scope.

Offline persistence only. This module has no network, signal, outcome, account,
order or exchange-mutation capability.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


SCHEMA_VERSION = "MRCR_H02_SCOPE_JOURNAL_V01"
ZERO_HASH = "0" * 64


@dataclass(frozen=True)
class ScopeIngestResult:
    inserted: bool
    ordinal: int
    raw_sha256: str
    chain_sha256: str


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def raw_sha256(raw_payload: bytes) -> str:
    if not isinstance(raw_payload, (bytes, bytearray)):
        raise TypeError("raw_payload must be bytes")
    return hashlib.sha256(bytes(raw_payload)).hexdigest()


def chain_sha256(
    *,
    previous_chain_sha256: str,
    session_id: str,
    ordinal: int,
    venue: str,
    native_symbol: str,
    transport: str,
    message_kind: str,
    channel: str,
    sequence_first: int | None,
    sequence_last: int | None,
    source_time_min_ns: int | None,
    source_time_max_ns: int | None,
    collector_wall_ns: int,
    collector_monotonic_ns: int,
    raw_sha256_hex: str,
) -> str:
    payload = {
        "previous_chain_sha256": previous_chain_sha256,
        "session_id": session_id,
        "ordinal": int(ordinal),
        "venue": venue,
        "native_symbol": native_symbol,
        "transport": transport,
        "message_kind": message_kind,
        "channel": channel,
        "sequence_first": sequence_first,
        "sequence_last": sequence_last,
        "source_time_min_ns": source_time_min_ns,
        "source_time_max_ns": source_time_max_ns,
        "collector_wall_ns": int(collector_wall_ns),
        "collector_monotonic_ns": int(collector_monotonic_ns),
        "raw_sha256": raw_sha256_hex,
    }
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def connect_scope_journal(path: Path | str) -> sqlite3.Connection:
    db_path = Path(path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=30000")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS scope_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS scope_sessions (
            session_id TEXT PRIMARY KEY,
            batch_id TEXT NOT NULL,
            collector_version TEXT NOT NULL,
            venue TEXT NOT NULL,
            native_symbol TEXT NOT NULL,
            stream_group TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            started_wall_ns INTEGER NOT NULL,
            started_monotonic_ns INTEGER NOT NULL,
            ended_wall_ns INTEGER,
            status TEXT NOT NULL,
            terminal_error_class TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_scope_sessions_batch
        ON scope_sessions(batch_id);

        CREATE TABLE IF NOT EXISTS scope_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            venue TEXT NOT NULL,
            native_symbol TEXT NOT NULL,
            transport TEXT NOT NULL,
            message_kind TEXT NOT NULL,
            channel TEXT NOT NULL,
            sequence_first INTEGER,
            sequence_last INTEGER,
            source_time_min_ns INTEGER,
            source_time_max_ns INTEGER,
            collector_wall_ns INTEGER NOT NULL,
            collector_monotonic_ns INTEGER NOT NULL,
            raw_sha256 TEXT NOT NULL,
            previous_chain_sha256 TEXT NOT NULL,
            chain_sha256 TEXT NOT NULL,
            raw_payload BLOB NOT NULL,
            FOREIGN KEY(session_id) REFERENCES scope_sessions(session_id),
            UNIQUE(session_id, ordinal),
            UNIQUE(
                session_id,
                message_kind,
                sequence_first,
                sequence_last,
                raw_sha256
            )
        );

        CREATE INDEX IF NOT EXISTS idx_scope_records_session_ordinal
        ON scope_records(session_id, ordinal);
        """
    )
    row = conn.execute(
        "SELECT value FROM scope_meta WHERE key='schema_version'"
    ).fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO scope_meta(key, value) VALUES('schema_version', ?)",
            (SCHEMA_VERSION,),
        )
    elif row["value"] != SCHEMA_VERSION:
        raise RuntimeError(
            f"scope journal schema mismatch: {row['value']} != {SCHEMA_VERSION}"
        )
    conn.commit()


def start_scope_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    batch_id: str,
    collector_version: str,
    venue: str,
    native_symbol: str,
    stream_group: str,
    endpoint: str,
    started_wall_ns: int,
    started_monotonic_ns: int,
) -> None:
    with conn:
        conn.execute(
            """
            INSERT INTO scope_sessions(
                session_id, batch_id, collector_version, venue, native_symbol,
                stream_group, endpoint, started_wall_ns, started_monotonic_ns,
                status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'OPEN')
            """,
            (
                session_id,
                batch_id,
                collector_version,
                venue,
                native_symbol,
                stream_group,
                endpoint,
                int(started_wall_ns),
                int(started_monotonic_ns),
            ),
        )


def finish_scope_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    ended_wall_ns: int,
    status: str,
    terminal_error_class: str | None = None,
) -> None:
    with conn:
        conn.execute(
            """
            UPDATE scope_sessions
            SET ended_wall_ns=?, status=?, terminal_error_class=?
            WHERE session_id=?
            """,
            (
                int(ended_wall_ns),
                status,
                terminal_error_class,
                session_id,
            ),
        )


def _last_row(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT ordinal, chain_sha256
        FROM scope_records
        WHERE session_id=?
        ORDER BY ordinal DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()


def ingest_scope_record(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    venue: str,
    native_symbol: str,
    transport: str,
    message_kind: str,
    channel: str,
    sequence_first: int | None,
    sequence_last: int | None,
    source_time_min_ns: int | None,
    source_time_max_ns: int | None,
    collector_wall_ns: int,
    collector_monotonic_ns: int,
    raw_payload: bytes,
) -> ScopeIngestResult:
    session = conn.execute(
        """
        SELECT venue, native_symbol
        FROM scope_sessions
        WHERE session_id=?
        """,
        (session_id,),
    ).fetchone()
    if session is None:
        raise ValueError("scope session does not exist")
    if session["venue"] != venue or session["native_symbol"] != native_symbol:
        raise ValueError("record venue/symbol does not match scope session")
    if sequence_first is not None and sequence_last is not None:
        if int(sequence_first) > int(sequence_last):
            raise ValueError("sequence_first must be <= sequence_last")
    if source_time_min_ns is not None and source_time_max_ns is not None:
        if int(source_time_min_ns) > int(source_time_max_ns):
            raise ValueError("source_time_min_ns must be <= source_time_max_ns")

    raw_hash = raw_sha256(raw_payload)
    duplicate = conn.execute(
        """
        SELECT ordinal, chain_sha256
        FROM scope_records
        WHERE session_id=?
          AND message_kind=?
          AND sequence_first IS ?
          AND sequence_last IS ?
          AND raw_sha256=?
        LIMIT 1
        """,
        (
            session_id,
            message_kind,
            sequence_first,
            sequence_last,
            raw_hash,
        ),
    ).fetchone()
    if duplicate is not None:
        return ScopeIngestResult(
            inserted=False,
            ordinal=int(duplicate["ordinal"]),
            raw_sha256=raw_hash,
            chain_sha256=str(duplicate["chain_sha256"]),
        )

    last = _last_row(conn, session_id)
    ordinal = 1 if last is None else int(last["ordinal"]) + 1
    previous_chain = ZERO_HASH if last is None else str(last["chain_sha256"])
    current_chain = chain_sha256(
        previous_chain_sha256=previous_chain,
        session_id=session_id,
        ordinal=ordinal,
        venue=venue,
        native_symbol=native_symbol,
        transport=transport,
        message_kind=message_kind,
        channel=channel,
        sequence_first=sequence_first,
        sequence_last=sequence_last,
        source_time_min_ns=source_time_min_ns,
        source_time_max_ns=source_time_max_ns,
        collector_wall_ns=collector_wall_ns,
        collector_monotonic_ns=collector_monotonic_ns,
        raw_sha256_hex=raw_hash,
    )

    try:
        with conn:
            conn.execute(
                """
                INSERT INTO scope_records(
                    session_id, ordinal, venue, native_symbol, transport,
                    message_kind, channel, sequence_first, sequence_last,
                    source_time_min_ns, source_time_max_ns,
                    collector_wall_ns, collector_monotonic_ns,
                    raw_sha256, previous_chain_sha256, chain_sha256, raw_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    ordinal,
                    venue,
                    native_symbol,
                    transport,
                    message_kind,
                    channel,
                    sequence_first,
                    sequence_last,
                    source_time_min_ns,
                    source_time_max_ns,
                    int(collector_wall_ns),
                    int(collector_monotonic_ns),
                    raw_hash,
                    previous_chain,
                    current_chain,
                    sqlite3.Binary(bytes(raw_payload)),
                ),
            )
    except sqlite3.IntegrityError:
        duplicate = conn.execute(
            """
            SELECT ordinal, chain_sha256
            FROM scope_records
            WHERE session_id=?
              AND message_kind=?
              AND sequence_first IS ?
              AND sequence_last IS ?
              AND raw_sha256=?
            LIMIT 1
            """,
            (
                session_id,
                message_kind,
                sequence_first,
                sequence_last,
                raw_hash,
            ),
        ).fetchone()
        if duplicate is None:
            raise
        return ScopeIngestResult(
            inserted=False,
            ordinal=int(duplicate["ordinal"]),
            raw_sha256=raw_hash,
            chain_sha256=str(duplicate["chain_sha256"]),
        )

    return ScopeIngestResult(
        inserted=True,
        ordinal=ordinal,
        raw_sha256=raw_hash,
        chain_sha256=current_chain,
    )


def session_record_count(conn: sqlite3.Connection, session_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM scope_records WHERE session_id=?",
        (session_id,),
    ).fetchone()
    return int(row["n"])


def sqlite_integrity_ok(conn: sqlite3.Connection) -> bool:
    rows = conn.execute("PRAGMA integrity_check").fetchall()
    return bool(rows) and all(str(row[0]).lower() == "ok" for row in rows)


def latest_batch_id(conn: sqlite3.Connection) -> str | None:
    row = conn.execute(
        """
        SELECT batch_id
        FROM scope_sessions
        ORDER BY started_wall_ns DESC
        LIMIT 1
        """
    ).fetchone()
    return None if row is None else str(row["batch_id"])

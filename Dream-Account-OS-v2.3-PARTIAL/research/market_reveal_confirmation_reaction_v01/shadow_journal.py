"""Local append-only-ish shadow journal for non-target MRCR source validation.

Public market data only. No network client, signals, outcomes or trading logic.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
from typing import Any


SCHEMA_VERSION = "MRCR_SHADOW_JOURNAL_V01"
ZERO_HASH = "0" * 64


@dataclass(frozen=True)
class IngestResult:
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
    channel: str,
    product_id: str | None,
    sequence_num: int | None,
    envelope_timestamp: str | None,
    source_time_max_ns: int | None,
    collector_wall_ns: int,
    collector_monotonic_ns: int,
    raw_sha256_hex: str,
) -> str:
    payload = {
        "previous_chain_sha256": previous_chain_sha256,
        "session_id": session_id,
        "ordinal": int(ordinal),
        "channel": channel,
        "product_id": product_id,
        "sequence_num": sequence_num,
        "envelope_timestamp": envelope_timestamp,
        "source_time_max_ns": source_time_max_ns,
        "collector_wall_ns": int(collector_wall_ns),
        "collector_monotonic_ns": int(collector_monotonic_ns),
        "raw_sha256": raw_sha256_hex,
    }
    return hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def connect_journal(path: Path | str) -> sqlite3.Connection:
    db_path = Path(path).expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=FULL")
    conn.execute("PRAGMA foreign_keys=ON")
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS journal_meta (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS shadow_sessions (
            session_id TEXT PRIMARY KEY,
            collector_version TEXT NOT NULL,
            endpoint TEXT NOT NULL,
            product_id TEXT NOT NULL,
            started_wall_ns INTEGER NOT NULL,
            started_monotonic_ns INTEGER NOT NULL,
            ended_wall_ns INTEGER,
            status TEXT NOT NULL,
            terminal_error_class TEXT
        );

        CREATE TABLE IF NOT EXISTS shadow_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            ordinal INTEGER NOT NULL,
            channel TEXT NOT NULL,
            product_id TEXT,
            sequence_num INTEGER,
            envelope_timestamp TEXT,
            source_time_max_ns INTEGER,
            collector_wall_ns INTEGER NOT NULL,
            collector_monotonic_ns INTEGER NOT NULL,
            raw_sha256 TEXT NOT NULL,
            previous_chain_sha256 TEXT NOT NULL,
            chain_sha256 TEXT NOT NULL,
            raw_payload BLOB NOT NULL,
            FOREIGN KEY(session_id) REFERENCES shadow_sessions(session_id),
            UNIQUE(session_id, ordinal),
            UNIQUE(
                session_id,
                channel,
                product_id,
                sequence_num,
                raw_sha256
            )
        );

        CREATE INDEX IF NOT EXISTS idx_shadow_messages_session_ordinal
        ON shadow_messages(session_id, ordinal);
        """
    )
    existing = conn.execute(
        "SELECT value FROM journal_meta WHERE key='schema_version'"
    ).fetchone()
    if existing is None:
        conn.execute(
            "INSERT INTO journal_meta(key, value) VALUES('schema_version', ?)",
            (SCHEMA_VERSION,),
        )
    elif existing["value"] != SCHEMA_VERSION:
        raise RuntimeError(
            f"journal schema mismatch: {existing['value']} != {SCHEMA_VERSION}"
        )
    conn.commit()


def start_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    collector_version: str,
    endpoint: str,
    product_id: str,
    started_wall_ns: int,
    started_monotonic_ns: int,
) -> None:
    conn.execute(
        """
        INSERT INTO shadow_sessions(
            session_id, collector_version, endpoint, product_id,
            started_wall_ns, started_monotonic_ns, status
        ) VALUES (?, ?, ?, ?, ?, ?, 'OPEN')
        """,
        (
            session_id,
            collector_version,
            endpoint,
            product_id,
            int(started_wall_ns),
            int(started_monotonic_ns),
        ),
    )
    conn.commit()


def finish_session(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    ended_wall_ns: int,
    status: str,
    terminal_error_class: str | None = None,
) -> None:
    conn.execute(
        """
        UPDATE shadow_sessions
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
    conn.commit()


def _last_row(conn: sqlite3.Connection, session_id: str) -> sqlite3.Row | None:
    return conn.execute(
        """
        SELECT ordinal, chain_sha256
        FROM shadow_messages
        WHERE session_id=?
        ORDER BY ordinal DESC
        LIMIT 1
        """,
        (session_id,),
    ).fetchone()


def ingest_message(
    conn: sqlite3.Connection,
    *,
    session_id: str,
    channel: str,
    product_id: str | None,
    sequence_num: int | None,
    envelope_timestamp: str | None,
    source_time_max_ns: int | None,
    collector_wall_ns: int,
    collector_monotonic_ns: int,
    raw_payload: bytes,
) -> IngestResult:
    raw_hash = raw_sha256(raw_payload)

    duplicate = conn.execute(
        """
        SELECT ordinal, chain_sha256
        FROM shadow_messages
        WHERE session_id=?
          AND channel=?
          AND product_id IS ?
          AND sequence_num IS ?
          AND raw_sha256=?
        LIMIT 1
        """,
        (
            session_id,
            channel,
            product_id,
            sequence_num,
            raw_hash,
        ),
    ).fetchone()
    if duplicate is not None:
        return IngestResult(
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
        channel=channel,
        product_id=product_id,
        sequence_num=sequence_num,
        envelope_timestamp=envelope_timestamp,
        source_time_max_ns=source_time_max_ns,
        collector_wall_ns=collector_wall_ns,
        collector_monotonic_ns=collector_monotonic_ns,
        raw_sha256_hex=raw_hash,
    )

    try:
        with conn:
            conn.execute(
                """
                INSERT INTO shadow_messages(
                    session_id, ordinal, channel, product_id, sequence_num,
                    envelope_timestamp, source_time_max_ns,
                    collector_wall_ns, collector_monotonic_ns,
                    raw_sha256, previous_chain_sha256, chain_sha256, raw_payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    ordinal,
                    channel,
                    product_id,
                    sequence_num,
                    envelope_timestamp,
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
            FROM shadow_messages
            WHERE session_id=?
              AND channel=?
              AND product_id IS ?
              AND sequence_num IS ?
              AND raw_sha256=?
            LIMIT 1
            """,
            (
                session_id,
                channel,
                product_id,
                sequence_num,
                raw_hash,
            ),
        ).fetchone()
        if duplicate is None:
            raise
        return IngestResult(
            inserted=False,
            ordinal=int(duplicate["ordinal"]),
            raw_sha256=raw_hash,
            chain_sha256=str(duplicate["chain_sha256"]),
        )

    return IngestResult(
        inserted=True,
        ordinal=ordinal,
        raw_sha256=raw_hash,
        chain_sha256=current_chain,
    )


def message_count(conn: sqlite3.Connection, session_id: str) -> int:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM shadow_messages WHERE session_id=?",
        (session_id,),
    ).fetchone()
    return int(row["n"])


def sqlite_integrity_ok(conn: sqlite3.Connection) -> bool:
    rows = conn.execute("PRAGMA integrity_check").fetchall()
    return bool(rows) and all(str(row[0]).lower() == "ok" for row in rows)

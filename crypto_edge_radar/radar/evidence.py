from __future__ import annotations

from contextlib import closing
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

try:
    import psycopg
except ImportError:  # pragma: no cover - exercised by fail-closed construction path
    psycopg = None

from .models import utc_now_iso

GENESIS_HASH = "0" * 64
POSTGRES_CHAIN_LOCK_ID = 48501847412818


def _canonical_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _receipt(
    *,
    event_id: int,
    event_ts: str,
    event_type: str,
    payload_sha: str,
    prev_hash: str,
    chain_sha: str,
    backend: str,
) -> dict[str, Any]:
    return {
        "id": event_id,
        "event_ts": event_ts,
        "event_type": event_type,
        "payload_sha256": payload_sha,
        "prev_chain_sha256": prev_hash,
        "chain_sha256": chain_sha,
        "backend": backend,
    }


def _duplicate_receipt(*, event_id: int, event_type: str, event_key: str, backend: str) -> dict[str, Any]:
    return {
        "id": event_id,
        "event_type": event_type,
        "event_key": event_key,
        "backend": backend,
        "inserted": False,
        "duplicate": True,
    }


class EvidenceStore:
    """SQLite append-only event store with a SHA-256 hash chain and idempotency keys."""

    backend = "sqlite"

    def __init__(self, db_path: str) -> None:
        self.db_path: str | None = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        if self.db_path is None:
            raise RuntimeError("sqlite db_path is not configured")
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS events (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        event_ts TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        payload_json TEXT NOT NULL,
                        payload_sha256 TEXT NOT NULL,
                        prev_chain_sha256 TEXT NOT NULL,
                        chain_sha256 TEXT NOT NULL UNIQUE
                    )
                    """
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_events_type_ts ON events(event_type, event_ts)"
                )
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS event_keys (
                        event_type TEXT NOT NULL,
                        event_key TEXT NOT NULL,
                        event_id INTEGER NOT NULL,
                        PRIMARY KEY (event_type, event_key),
                        FOREIGN KEY (event_id) REFERENCES events(id)
                    )
                    """
                )

    def _last_chain_hash(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT chain_sha256 FROM events ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["chain_sha256"] if row else GENESIS_HASH

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not event_type.strip():
            raise ValueError("event_type is required")
        payload_json = _canonical_json(payload)
        payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        event_ts = utc_now_iso()

        with closing(self._connect()) as conn:
            with conn:
                prev_hash = self._last_chain_hash(conn)
                chain_material = "|".join((prev_hash, event_ts, event_type, payload_sha))
                chain_sha = hashlib.sha256(chain_material.encode("utf-8")).hexdigest()
                cursor = conn.execute(
                    """
                    INSERT INTO events (
                        event_ts, event_type, payload_json, payload_sha256,
                        prev_chain_sha256, chain_sha256
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (event_ts, event_type, payload_json, payload_sha, prev_hash, chain_sha),
                )
                event_id = int(cursor.lastrowid)

        return _receipt(
            event_id=event_id,
            event_ts=event_ts,
            event_type=event_type,
            payload_sha=payload_sha,
            prev_hash=prev_hash,
            chain_sha=chain_sha,
            backend=self.backend,
        )

    def append_once(self, event_type: str, event_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Atomically append one keyed event, returning duplicate metadata on retries."""
        if not event_type.strip():
            raise ValueError("event_type is required")
        if not event_key.strip():
            raise ValueError("event_key is required")
        payload_json = _canonical_json(payload)
        payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        event_ts = utc_now_iso()

        with closing(self._connect()) as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                existing = conn.execute(
                    "SELECT event_id FROM event_keys WHERE event_type = ? AND event_key = ?",
                    (event_type, event_key),
                ).fetchone()
                if existing is not None:
                    conn.rollback()
                    return _duplicate_receipt(
                        event_id=int(existing["event_id"]),
                        event_type=event_type,
                        event_key=event_key,
                        backend=self.backend,
                    )

                prev_hash = self._last_chain_hash(conn)
                chain_material = "|".join((prev_hash, event_ts, event_type, payload_sha))
                chain_sha = hashlib.sha256(chain_material.encode("utf-8")).hexdigest()
                cursor = conn.execute(
                    """
                    INSERT INTO events (
                        event_ts, event_type, payload_json, payload_sha256,
                        prev_chain_sha256, chain_sha256
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (event_ts, event_type, payload_json, payload_sha, prev_hash, chain_sha),
                )
                event_id = int(cursor.lastrowid)
                conn.execute(
                    "INSERT INTO event_keys (event_type, event_key, event_id) VALUES (?, ?, ?)",
                    (event_type, event_key, event_id),
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        receipt = _receipt(
            event_id=event_id,
            event_ts=event_ts,
            event_type=event_type,
            payload_sha=payload_sha,
            prev_hash=prev_hash,
            chain_sha=chain_sha,
            backend=self.backend,
        )
        receipt.update({"event_key": event_key, "inserted": True, "duplicate": False})
        return receipt

    def read_payloads(self, event_type: str) -> list[dict[str, Any]]:
        """Read one event type in append order without mutating the evidence chain."""
        if not event_type.strip():
            raise ValueError("event_type is required")
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT payload_json FROM events WHERE event_type = ? ORDER BY id ASC",
                (event_type,),
            ).fetchall()
        return [json.loads(row["payload_json"]) for row in rows]

    def verify_chain(self) -> tuple[bool, str]:
        with closing(self._connect()) as conn:
            rows = conn.execute("SELECT * FROM events ORDER BY id ASC").fetchall()

        expected_prev = GENESIS_HASH
        for row in rows:
            payload_sha = hashlib.sha256(row["payload_json"].encode("utf-8")).hexdigest()
            if payload_sha != row["payload_sha256"]:
                return False, f"payload hash mismatch at event {row['id']}"
            if row["prev_chain_sha256"] != expected_prev:
                return False, f"previous chain mismatch at event {row['id']}"
            material = "|".join(
                (expected_prev, row["event_ts"], row["event_type"], payload_sha)
            )
            expected_chain = hashlib.sha256(material.encode("utf-8")).hexdigest()
            if row["chain_sha256"] != expected_chain:
                return False, f"chain hash mismatch at event {row['id']}"
            expected_prev = expected_chain
        return True, f"verified {len(rows)} events via sqlite"


class PostgresEvidenceStore:
    """Remote append-only evidence chain using transactional PostgreSQL writes."""

    backend = "postgres"
    db_path: None = None

    def __init__(self, database_url: str) -> None:
        if not database_url or not database_url.strip():
            raise ValueError("database_url is required")
        if psycopg is None:
            raise RuntimeError("Postgres evidence store requires psycopg")
        self._database_url = database_url.strip()
        self._init_db()

    def _connect(self):
        if psycopg is None:
            raise RuntimeError("Postgres evidence store requires psycopg")
        return psycopg.connect(self._database_url, connect_timeout=5)

    def _init_db(self) -> None:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS radar_events (
                            id BIGSERIAL PRIMARY KEY,
                            event_ts TEXT NOT NULL,
                            event_type TEXT NOT NULL,
                            payload_json TEXT NOT NULL,
                            payload_sha256 TEXT NOT NULL,
                            prev_chain_sha256 TEXT NOT NULL,
                            chain_sha256 TEXT NOT NULL UNIQUE
                        )
                        """
                    )
                    cur.execute(
                        "CREATE INDEX IF NOT EXISTS idx_radar_events_type_ts "
                        "ON radar_events(event_type, event_ts)"
                    )
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS radar_event_keys (
                            event_type TEXT NOT NULL,
                            event_key TEXT NOT NULL,
                            event_id BIGINT NOT NULL REFERENCES radar_events(id),
                            PRIMARY KEY (event_type, event_key)
                        )
                        """
                    )
        except Exception as exc:
            raise RuntimeError(
                f"postgres evidence initialization failed: {type(exc).__name__}: {exc}"
            ) from exc

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not event_type.strip():
            raise ValueError("event_type is required")
        payload_json = _canonical_json(payload)
        payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        event_ts = utc_now_iso()

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_advisory_xact_lock(%s)", (POSTGRES_CHAIN_LOCK_ID,))
                    cur.execute(
                        "SELECT chain_sha256 FROM radar_events ORDER BY id DESC LIMIT 1"
                    )
                    row = cur.fetchone()
                    prev_hash = row[0] if row else GENESIS_HASH
                    chain_material = "|".join(
                        (prev_hash, event_ts, event_type, payload_sha)
                    )
                    chain_sha = hashlib.sha256(chain_material.encode("utf-8")).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO radar_events (
                            event_ts, event_type, payload_json, payload_sha256,
                            prev_chain_sha256, chain_sha256
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (
                            event_ts,
                            event_type,
                            payload_json,
                            payload_sha,
                            prev_hash,
                            chain_sha,
                        ),
                    )
                    event_id = int(cur.fetchone()[0])
        except Exception as exc:
            raise RuntimeError(
                f"postgres evidence append failed: {type(exc).__name__}: {exc}"
            ) from exc

        return _receipt(
            event_id=event_id,
            event_ts=event_ts,
            event_type=event_type,
            payload_sha=payload_sha,
            prev_hash=prev_hash,
            chain_sha=chain_sha,
            backend=self.backend,
        )

    def append_once(self, event_type: str, event_key: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not event_type.strip():
            raise ValueError("event_type is required")
        if not event_key.strip():
            raise ValueError("event_key is required")
        payload_json = _canonical_json(payload)
        payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        event_ts = utc_now_iso()

        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT pg_advisory_xact_lock(%s)", (POSTGRES_CHAIN_LOCK_ID,))
                    cur.execute(
                        "SELECT event_id FROM radar_event_keys WHERE event_type = %s AND event_key = %s",
                        (event_type, event_key),
                    )
                    existing = cur.fetchone()
                    if existing is not None:
                        return _duplicate_receipt(
                            event_id=int(existing[0]),
                            event_type=event_type,
                            event_key=event_key,
                            backend=self.backend,
                        )

                    cur.execute(
                        "SELECT chain_sha256 FROM radar_events ORDER BY id DESC LIMIT 1"
                    )
                    row = cur.fetchone()
                    prev_hash = row[0] if row else GENESIS_HASH
                    chain_material = "|".join(
                        (prev_hash, event_ts, event_type, payload_sha)
                    )
                    chain_sha = hashlib.sha256(chain_material.encode("utf-8")).hexdigest()
                    cur.execute(
                        """
                        INSERT INTO radar_events (
                            event_ts, event_type, payload_json, payload_sha256,
                            prev_chain_sha256, chain_sha256
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                        """,
                        (event_ts, event_type, payload_json, payload_sha, prev_hash, chain_sha),
                    )
                    event_id = int(cur.fetchone()[0])
                    cur.execute(
                        "INSERT INTO radar_event_keys (event_type, event_key, event_id) VALUES (%s, %s, %s)",
                        (event_type, event_key, event_id),
                    )
        except Exception as exc:
            raise RuntimeError(
                f"postgres keyed append failed: {type(exc).__name__}: {exc}"
            ) from exc

        receipt = _receipt(
            event_id=event_id,
            event_ts=event_ts,
            event_type=event_type,
            payload_sha=payload_sha,
            prev_hash=prev_hash,
            chain_sha=chain_sha,
            backend=self.backend,
        )
        receipt.update({"event_key": event_key, "inserted": True, "duplicate": False})
        return receipt

    def read_payloads(self, event_type: str) -> list[dict[str, Any]]:
        """Read one event type in append order without mutating the evidence chain."""
        if not event_type.strip():
            raise ValueError("event_type is required")
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT payload_json FROM radar_events WHERE event_type = %s ORDER BY id ASC",
                        (event_type,),
                    )
                    rows = cur.fetchall()
        except Exception as exc:
            raise RuntimeError(
                f"postgres evidence read failed: {type(exc).__name__}: {exc}"
            ) from exc
        return [json.loads(row[0]) for row in rows]

    def verify_chain(self) -> tuple[bool, str]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, event_ts, event_type, payload_json, payload_sha256,
                               prev_chain_sha256, chain_sha256
                        FROM radar_events ORDER BY id ASC
                        """
                    )
                    rows = cur.fetchall()
        except Exception as exc:
            return False, f"postgres verification unavailable: {type(exc).__name__}: {exc}"

        expected_prev = GENESIS_HASH
        for row in rows:
            event_id, event_ts, event_type, payload_json, stored_payload_sha, stored_prev, stored_chain = row
            payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
            if payload_sha != stored_payload_sha:
                return False, f"payload hash mismatch at event {event_id}"
            if stored_prev != expected_prev:
                return False, f"previous chain mismatch at event {event_id}"
            material = "|".join((expected_prev, event_ts, event_type, payload_sha))
            expected_chain = hashlib.sha256(material.encode("utf-8")).hexdigest()
            if stored_chain != expected_chain:
                return False, f"chain hash mismatch at event {event_id}"
            expected_prev = expected_chain
        return True, f"verified {len(rows)} events via postgres"


def build_evidence_store(db_path: str, database_url: str | None = None):
    """Use remote Postgres when explicitly configured; otherwise retain SQLite."""
    if database_url:
        return PostgresEvidenceStore(database_url)
    return EvidenceStore(db_path)

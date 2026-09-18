from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import utc_now_iso

GENESIS_HASH = "0" * 64


class EvidenceStore:
    """Append-only event store with a simple SHA-256 hash chain."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
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

    @staticmethod
    def _canonical_json(payload: dict[str, Any]) -> str:
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    def _last_chain_hash(self, conn: sqlite3.Connection) -> str:
        row = conn.execute(
            "SELECT chain_sha256 FROM events ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return row["chain_sha256"] if row else GENESIS_HASH

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        if not event_type.strip():
            raise ValueError("event_type is required")
        payload_json = self._canonical_json(payload)
        payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        event_ts = utc_now_iso()

        with self._connect() as conn:
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
            event_id = cursor.lastrowid

        return {
            "id": event_id,
            "event_ts": event_ts,
            "event_type": event_type,
            "payload_sha256": payload_sha,
            "prev_chain_sha256": prev_hash,
            "chain_sha256": chain_sha,
        }

    def signal_key_seen(self, signal_key: str) -> bool:
        if not signal_key:
            raise ValueError("signal_key is required")
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM events WHERE event_type = ? ORDER BY id ASC",
                ("VALID_SHADOW_SIGNAL",),
            ).fetchall()
        for row in rows:
            try:
                payload = json.loads(row["payload_json"])
            except json.JSONDecodeError:
                continue
            if payload.get("signal_key") == signal_key:
                return True
        return False

    def verify_chain(self) -> tuple[bool, str]:
        with self._connect() as conn:
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
        return True, f"verified {len(rows)} events"

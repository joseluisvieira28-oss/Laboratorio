from __future__ import annotations

import hashlib
import json
from typing import Any

from .evidence import GENESIS_HASH

try:
    import psycopg
except Exception:  # pragma: no cover
    psycopg = None


EVENT_SCHEMA_SQL = """
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

KEY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS radar_event_keys (
    event_type TEXT NOT NULL,
    event_key TEXT NOT NULL,
    event_id BIGINT NOT NULL REFERENCES radar_events(id),
    PRIMARY KEY (event_type, event_key)
)
"""


def canonical_snapshot_sha(snapshot: dict[str, Any]) -> str:
    core = {
        "events": snapshot["events"],
        "event_keys": snapshot["event_keys"],
    }
    raw = json.dumps(
        core, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def verify_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    events = snapshot.get("events")
    keys = snapshot.get("event_keys")
    if not isinstance(events, list) or not isinstance(keys, list):
        raise ValueError("snapshot events/event_keys must be lists")

    expected_prev = GENESIS_HASH
    event_ids: set[int] = set()
    last_id = 0
    counts: dict[str, int] = {}

    for row in events:
        event_id = int(row["id"])
        if event_id <= last_id:
            raise ValueError(f"event ids not strictly increasing at {event_id}")
        last_id = event_id
        event_ids.add(event_id)

        payload_json = str(row["payload_json"])
        payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        if payload_sha != row["payload_sha256"]:
            raise ValueError(f"payload hash mismatch at event {event_id}")
        if row["prev_chain_sha256"] != expected_prev:
            raise ValueError(f"previous chain mismatch at event {event_id}")
        material = "|".join(
            (expected_prev, row["event_ts"], row["event_type"], payload_sha)
        )
        chain_sha = hashlib.sha256(material.encode("utf-8")).hexdigest()
        if chain_sha != row["chain_sha256"]:
            raise ValueError(f"chain hash mismatch at event {event_id}")
        expected_prev = chain_sha
        counts[row["event_type"]] = counts.get(row["event_type"], 0) + 1

    seen_keys: set[tuple[str, str]] = set()
    for row in keys:
        key = (str(row["event_type"]), str(row["event_key"]))
        if key in seen_keys:
            raise ValueError(f"duplicate event key: {key[0]}:{key[1]}")
        seen_keys.add(key)
        event_id = int(row["event_id"])
        if event_id not in event_ids:
            raise ValueError(f"event key references missing event {event_id}")

    if "event_count" in snapshot and int(snapshot["event_count"]) != len(events):
        raise ValueError("event_count mismatch")
    if "key_count" in snapshot and int(snapshot["key_count"]) != len(keys):
        raise ValueError("key_count mismatch")
    if snapshot.get("chain_head_sha256") not in (None, expected_prev):
        raise ValueError("chain head mismatch")
    if snapshot.get("snapshot_sha256") not in (None, canonical_snapshot_sha(snapshot)):
        raise ValueError("snapshot sha mismatch")

    return {
        "event_count": len(events),
        "key_count": len(keys),
        "chain_head_sha256": expected_prev,
        "snapshot_sha256": canonical_snapshot_sha(snapshot),
        "event_type_counts": dict(sorted(counts.items())),
    }


def restore_snapshot(
    snapshot: dict[str, Any],
    *,
    target_url: str,
    apply: bool,
) -> dict[str, Any]:
    verified = verify_snapshot(snapshot)
    if not target_url or not target_url.strip():
        return {
            "classification": "AUTH_REQUIRED_NOT_EXECUTED",
            **verified,
            "target_mutation": False,
            "secret_value_exposed": False,
        }
    if not apply:
        return {
            "classification": "DRY_RUN_VERIFIED_NO_TARGET_MUTATION",
            **verified,
            "target_mutation": False,
            "secret_value_exposed": False,
        }
    if psycopg is None:
        raise RuntimeError("psycopg is required for Postgres restore")

    events = snapshot["events"]
    keys = snapshot["event_keys"]

    with psycopg.connect(target_url.strip(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(EVENT_SCHEMA_SQL)
            cur.execute(
                "CREATE INDEX IF NOT EXISTS idx_radar_events_type_ts "
                "ON radar_events(event_type, event_ts)"
            )
            cur.execute(KEY_SCHEMA_SQL)

            cur.execute("SELECT COUNT(*) FROM radar_events")
            target_events = int(cur.fetchone()[0])
            cur.execute("SELECT COUNT(*) FROM radar_event_keys")
            target_keys = int(cur.fetchone()[0])
            if target_events or target_keys:
                raise RuntimeError(
                    f"target is not empty: events={target_events}, keys={target_keys}"
                )

            for row in events:
                cur.execute(
                    """
                    INSERT INTO radar_events (
                        id,event_ts,event_type,payload_json,payload_sha256,
                        prev_chain_sha256,chain_sha256
                    ) VALUES (%s,%s,%s,%s,%s,%s,%s)
                    """,
                    (
                        int(row["id"]),
                        row["event_ts"],
                        row["event_type"],
                        row["payload_json"],
                        row["payload_sha256"],
                        row["prev_chain_sha256"],
                        row["chain_sha256"],
                    ),
                )

            for row in keys:
                cur.execute(
                    "INSERT INTO radar_event_keys(event_type,event_key,event_id) "
                    "VALUES (%s,%s,%s)",
                    (
                        row["event_type"],
                        row["event_key"],
                        int(row["event_id"]),
                    ),
                )

            max_id = max((int(x["id"]) for x in events), default=0)
            if max_id:
                cur.execute(
                    "SELECT setval(pg_get_serial_sequence('radar_events','id'), %s, true)",
                    (max_id,),
                )

            cur.execute(
                "SELECT id,event_ts,event_type,payload_json,payload_sha256,"
                "prev_chain_sha256,chain_sha256 FROM radar_events ORDER BY id ASC"
            )
            target_event_rows = [
                {
                    "id": int(r[0]),
                    "event_ts": r[1],
                    "event_type": r[2],
                    "payload_json": r[3],
                    "payload_sha256": r[4],
                    "prev_chain_sha256": r[5],
                    "chain_sha256": r[6],
                }
                for r in cur.fetchall()
            ]
            cur.execute(
                "SELECT event_type,event_key,event_id FROM radar_event_keys "
                "ORDER BY event_type,event_key"
            )
            target_key_rows = [
                {"event_type": r[0], "event_key": r[1], "event_id": int(r[2])}
                for r in cur.fetchall()
            ]
            target_snapshot = {
                "events": target_event_rows,
                "event_keys": target_key_rows,
                "event_count": len(target_event_rows),
                "key_count": len(target_key_rows),
                "chain_head_sha256": verified["chain_head_sha256"],
                "snapshot_sha256": verified["snapshot_sha256"],
            }
            target_verified = verify_snapshot(target_snapshot)
            if target_verified != verified:
                raise RuntimeError("target verification differs from source snapshot")

    return {
        "classification": "TARGET_RESTORE_VERIFIED",
        **verified,
        "target_mutation": True,
        "secret_value_exposed": False,
    }

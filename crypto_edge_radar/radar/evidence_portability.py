from __future__ import annotations

import hashlib
import json
from typing import Any

from .evidence import GENESIS_HASH, POSTGRES_CHAIN_LOCK_ID

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


def _read_target_snapshot(cur) -> dict[str, Any]:
    cur.execute(
        "SELECT id,event_ts,event_type,payload_json,payload_sha256,"
        "prev_chain_sha256,chain_sha256 FROM radar_events ORDER BY id ASC"
    )
    events = [
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
    keys = [
        {
            "event_type": r[0],
            "event_key": r[1],
            "event_id": int(r[2]),
        }
        for r in cur.fetchall()
    ]
    head = events[-1]["chain_sha256"] if events else GENESIS_HASH
    snapshot = {
        "events": events,
        "event_keys": keys,
        "event_count": len(events),
        "key_count": len(keys),
        "chain_head_sha256": head,
    }
    snapshot["snapshot_sha256"] = canonical_snapshot_sha(snapshot)
    return snapshot


def _target_sequence_state(cur) -> tuple[int, bool]:
    cur.execute("SELECT last_value,is_called FROM radar_events_id_seq")
    row = cur.fetchone()
    if row is None:
        raise RuntimeError("target sequence unavailable")
    return int(row[0]), bool(row[1])


def _sorted_keys(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        (
            {
                "event_type": str(x["event_type"]),
                "event_key": str(x["event_key"]),
                "event_id": int(x["event_id"]),
            }
            for x in rows
        ),
        key=lambda x: (x["event_type"], x["event_key"]),
    )


def _prefix_comparison(
    source: dict[str, Any],
    target: dict[str, Any],
    *,
    sequence_last_value: int,
    sequence_is_called: bool,
) -> dict[str, Any]:
    source_events = source["events"]
    target_events = target["events"]
    source_keys = _sorted_keys(source["event_keys"])
    target_keys = _sorted_keys(target["event_keys"])

    reasons: list[str] = []

    source_ids = [int(x["id"]) for x in source_events]
    if source_ids != list(range(1, len(source_ids) + 1)):
        reasons.append("SOURCE_EVENT_IDS_NOT_CONTIGUOUS_FROM_ONE")

    target_ids = [int(x["id"]) for x in target_events]
    if target_ids != list(range(1, len(target_ids) + 1)):
        reasons.append("TARGET_EVENT_IDS_NOT_CONTIGUOUS_FROM_ONE")

    if len(target_events) > len(source_events):
        reasons.append("TARGET_LONGER_THAN_SOURCE")
    elif target_events != source_events[: len(target_events)]:
        reasons.append("TARGET_EVENTS_NOT_EXACT_SOURCE_PREFIX")

    target_max = target_ids[-1] if target_ids else 0
    expected_target_keys = _sorted_keys(
        [x for x in source_keys if int(x["event_id"]) <= target_max]
    )
    if target_keys != expected_target_keys:
        reasons.append("TARGET_KEYS_NOT_EXACT_SOURCE_PREFIX")

    if target_max == 0:
        sequence_aligned = sequence_last_value in (0, 1) and not sequence_is_called
    else:
        sequence_aligned = (
            sequence_last_value == target_max and sequence_is_called
        )
    if not sequence_aligned:
        reasons.append("TARGET_SEQUENCE_NOT_ALIGNED_TO_PREFIX_MAX_ID")

    exact_prefix = not reasons
    return {
        "exact_prefix": exact_prefix,
        "reasons": reasons,
        "target_event_count": len(target_events),
        "target_key_count": len(target_keys),
        "target_max_id": target_max,
        "target_chain_head_sha256": target.get("chain_head_sha256"),
        "target_snapshot_sha256": target.get("snapshot_sha256"),
        "sequence_last_value": sequence_last_value,
        "sequence_is_called": sequence_is_called,
        "sequence_aligned": sequence_aligned,
        "missing_event_count": (
            len(source_events) - len(target_events)
            if len(target_events) <= len(source_events)
            else None
        ),
        "missing_key_count": (
            len(source_keys) - len(target_keys)
            if len(target_keys) <= len(source_keys)
            else None
        ),
    }


def inspect_target_prefix(
    snapshot: dict[str, Any],
    *,
    target_url: str,
) -> dict[str, Any]:
    source_verified = verify_snapshot(snapshot)
    if not target_url or not target_url.strip():
        return {
            "classification": "AUTH_REQUIRED_NOT_EXECUTED",
            **source_verified,
            "target_mutation": False,
            "secret_value_exposed": False,
        }
    if psycopg is None:
        raise RuntimeError("psycopg is required for Postgres prefix inspection")

    with psycopg.connect(target_url.strip(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("SET TRANSACTION READ ONLY")
            target = _read_target_snapshot(cur)
            target_verified = verify_snapshot(target)
            sequence_last, sequence_called = _target_sequence_state(cur)

    comparison = _prefix_comparison(
        snapshot,
        target,
        sequence_last_value=sequence_last,
        sequence_is_called=sequence_called,
    )
    return {
        "classification": (
            "TARGET_EXACT_PREFIX_READY_FOR_DELTA"
            if comparison["exact_prefix"]
            else "TARGET_PREFIX_FAIL_CLOSED"
        ),
        "source_event_count": source_verified["event_count"],
        "source_key_count": source_verified["key_count"],
        "source_chain_head_sha256": source_verified["chain_head_sha256"],
        "source_snapshot_sha256": source_verified["snapshot_sha256"],
        "target_verified": True,
        "target_verified_event_count": target_verified["event_count"],
        "target_verified_key_count": target_verified["key_count"],
        **comparison,
        "target_mutation": False,
        "secret_value_exposed": False,
        "cutover_authorized": False,
    }


def reconcile_target_prefix(
    snapshot: dict[str, Any],
    *,
    target_url: str,
    apply: bool,
) -> dict[str, Any]:
    inspected = inspect_target_prefix(snapshot, target_url=target_url)
    if inspected["classification"] == "AUTH_REQUIRED_NOT_EXECUTED":
        return inspected
    if not inspected.get("exact_prefix"):
        return {
            **inspected,
            "classification": "TARGET_PREFIX_FAIL_CLOSED_NO_MUTATION",
            "target_mutation": False,
            "cutover_authorized": False,
        }
    if not apply:
        return {
            **inspected,
            "classification": "DRY_RUN_TARGET_EXACT_PREFIX",
            "target_mutation": False,
            "cutover_authorized": False,
        }

    source_verified = verify_snapshot(snapshot)
    source_events = snapshot["events"]
    source_keys = _sorted_keys(snapshot["event_keys"])

    if psycopg is None:
        raise RuntimeError("psycopg is required for Postgres prefix reconciliation")

    with psycopg.connect(target_url.strip(), connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT pg_advisory_xact_lock(%s)",
                (POSTGRES_CHAIN_LOCK_ID,),
            )
            target_before = _read_target_snapshot(cur)
            verify_snapshot(target_before)
            sequence_last, sequence_called = _target_sequence_state(cur)
            check = _prefix_comparison(
                snapshot,
                target_before,
                sequence_last_value=sequence_last,
                sequence_is_called=sequence_called,
            )
            if not check["exact_prefix"]:
                raise RuntimeError(
                    "target changed after prefix inspection: "
                    + ",".join(check["reasons"])
                )

            target_count = len(target_before["events"])
            target_max = check["target_max_id"]
            missing_events = source_events[target_count:]
            missing_keys = [
                x for x in source_keys if int(x["event_id"]) > target_max
            ]

            for row in missing_events:
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

            for row in missing_keys:
                cur.execute(
                    "INSERT INTO radar_event_keys(event_type,event_key,event_id) "
                    "VALUES (%s,%s,%s)",
                    (
                        row["event_type"],
                        row["event_key"],
                        int(row["event_id"]),
                    ),
                )

            target_after = _read_target_snapshot(cur)
            target_after_verified = verify_snapshot(target_after)
            if target_after["events"] != source_events:
                raise RuntimeError("target events differ after append-only reconciliation")
            if _sorted_keys(target_after["event_keys"]) != source_keys:
                raise RuntimeError("target event keys differ after append-only reconciliation")
            if (
                target_after_verified["snapshot_sha256"]
                != source_verified["snapshot_sha256"]
            ):
                raise RuntimeError("target snapshot hash differs after reconciliation")

    delta_events = len(source_events) - inspected["target_event_count"]
    return {
        "classification": (
            "TARGET_DELTA_ROWS_VERIFIED__SEQUENCE_FINALIZATION_REQUIRED"
            if delta_events > 0
            else "TARGET_ALREADY_EXACT__SEQUENCE_ALIGNED"
        ),
        "source_event_count": source_verified["event_count"],
        "source_key_count": source_verified["key_count"],
        "source_chain_head_sha256": source_verified["chain_head_sha256"],
        "source_snapshot_sha256": source_verified["snapshot_sha256"],
        "inserted_event_count": delta_events,
        "inserted_key_count": len(source_keys) - inspected["target_key_count"],
        "target_rows_exact_after_reconcile": True,
        "sequence_finalization_required": delta_events > 0,
        "required_sequence_last_value": (
            int(source_events[-1]["id"]) if source_events else 0
        ),
        "target_mutation": delta_events > 0,
        "secret_value_exposed": False,
        "cutover_authorized": False,
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

from __future__ import annotations

import hashlib
from typing import Any

from .evidence import GENESIS_HASH


IDENTITY_SCHEMA = "RADAR_EVIDENCE_IDENTITY_V0.1"


def key_binding_material(rows: list[tuple[str, str, int]]) -> bytes:
    ordered = sorted(
        ((str(t), str(k), int(i)) for t, k, i in rows),
        key=lambda x: (x[0], x[1]),
    )
    text = "".join(
        f"{len(event_type)}:{event_type}|{len(event_key)}:{event_key}|{event_id}\n"
        for event_type, event_key, event_id in ordered
    )
    return text.encode("utf-8")


def key_binding_sha256(rows: list[tuple[str, str, int]]) -> str:
    return hashlib.sha256(key_binding_material(rows)).hexdigest()


def build_evidence_identity(store) -> dict[str, Any]:
    chain_ok, chain_detail = store.verify_chain()
    if not chain_ok:
        raise RuntimeError(f"EVIDENCE_CHAIN_INVALID:{chain_detail}")

    if store.backend == "postgres":
        with store._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(
                    "SELECT COUNT(*), COALESCE(MAX(id),0) FROM radar_events"
                )
                event_count, max_id = cur.fetchone()
                cur.execute(
                    "SELECT chain_sha256 FROM radar_events ORDER BY id DESC LIMIT 1"
                )
                row = cur.fetchone()
                chain_head = row[0] if row else GENESIS_HASH
                cur.execute("SELECT COUNT(*) FROM radar_event_keys")
                key_count = int(cur.fetchone()[0])
                cur.execute(
                    "SELECT event_type,event_key,event_id "
                    "FROM radar_event_keys ORDER BY event_type,event_key"
                )
                key_rows = [
                    (str(r[0]), str(r[1]), int(r[2]))
                    for r in cur.fetchall()
                ]
                cur.execute("SELECT last_value,is_called FROM radar_events_id_seq")
                seq = cur.fetchone()
                sequence_last_value = int(seq[0]) if seq is not None else None
                sequence_is_called = bool(seq[1]) if seq is not None else None
    elif store.backend == "sqlite":
        with store._connect() as conn:
            row = conn.execute(
                "SELECT COUNT(*) AS n, COALESCE(MAX(id),0) AS max_id FROM events"
            ).fetchone()
            event_count, max_id = int(row["n"]), int(row["max_id"])
            row = conn.execute(
                "SELECT chain_sha256 FROM events ORDER BY id DESC LIMIT 1"
            ).fetchone()
            chain_head = row["chain_sha256"] if row else GENESIS_HASH
            key_count = int(
                conn.execute("SELECT COUNT(*) AS n FROM event_keys").fetchone()["n"]
            )
            key_rows = [
                (str(r["event_type"]), str(r["event_key"]), int(r["event_id"]))
                for r in conn.execute(
                    "SELECT event_type,event_key,event_id "
                    "FROM event_keys ORDER BY event_type,event_key"
                ).fetchall()
            ]
            sequence_last_value = max_id
            sequence_is_called = event_count > 0
    else:
        raise RuntimeError(f"unsupported evidence backend:{store.backend}")

    if key_count != len(key_rows):
        raise RuntimeError("EVENT_KEY_COUNT_MISMATCH")

    return {
        "schema_version": IDENTITY_SCHEMA,
        "status": "VERIFIED",
        "backend": store.backend,
        "event_count": int(event_count),
        "max_event_id": int(max_id),
        "key_count": int(key_count),
        "chain_head_sha256": str(chain_head),
        "key_binding_sha256": key_binding_sha256(key_rows),
        "sequence_last_value": sequence_last_value,
        "sequence_is_called": sequence_is_called,
        "chain_verified": True,
        "chain_detail": chain_detail,
        "payloads_exposed": False,
        "science_changed": False,
        "database_mutation": False,
    }

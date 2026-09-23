from __future__ import annotations

import base64
import gzip
import hashlib
import json
from typing import Any

GENESIS = "0" * 64


def _snapshot_sha(events: list[dict[str, Any]], keys: list[dict[str, Any]]) -> str:
    raw = json.dumps(
        {"events": events, "event_keys": keys},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _verify(events: list[dict[str, Any]]) -> tuple[bool, str, str]:
    expected_prev = GENESIS
    for row in events:
        payload_json = row["payload_json"]
        payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
        if payload_sha != row["payload_sha256"]:
            return False, f"payload hash mismatch at event {row['id']}", expected_prev
        if row["prev_chain_sha256"] != expected_prev:
            return False, f"previous chain mismatch at event {row['id']}", expected_prev
        material = "|".join(
            (expected_prev, row["event_ts"], row["event_type"], payload_sha)
        )
        expected_chain = hashlib.sha256(material.encode("utf-8")).hexdigest()
        if row["chain_sha256"] != expected_chain:
            return False, f"chain hash mismatch at event {row['id']}", expected_prev
        expected_prev = expected_chain
    return True, f"verified {len(events)} events", expected_prev


def build_private_evidence_snapshot(store) -> dict[str, Any]:
    events: list[dict[str, Any]] = []
    keys: list[dict[str, Any]] = []

    if store.backend == "postgres":
        with store._connect() as conn:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(
                    "SELECT id,event_ts,event_type,payload_json,payload_sha256,"
                    "prev_chain_sha256,chain_sha256 FROM radar_events ORDER BY id ASC"
                )
                for row in cur.fetchall():
                    events.append(
                        {
                            "id": int(row[0]),
                            "event_ts": row[1],
                            "event_type": row[2],
                            "payload_json": row[3],
                            "payload_sha256": row[4],
                            "prev_chain_sha256": row[5],
                            "chain_sha256": row[6],
                        }
                    )
                cur.execute(
                    "SELECT event_type,event_key,event_id FROM radar_event_keys "
                    "ORDER BY event_type,event_key"
                )
                for row in cur.fetchall():
                    keys.append(
                        {
                            "event_type": row[0],
                            "event_key": row[1],
                            "event_id": int(row[2]),
                        }
                    )
    elif store.backend == "sqlite":
        with store._connect() as conn:
            for row in conn.execute(
                "SELECT id,event_ts,event_type,payload_json,payload_sha256,"
                "prev_chain_sha256,chain_sha256 FROM events ORDER BY id ASC"
            ).fetchall():
                events.append(
                    {
                        "id": int(row["id"]),
                        "event_ts": row["event_ts"],
                        "event_type": row["event_type"],
                        "payload_json": row["payload_json"],
                        "payload_sha256": row["payload_sha256"],
                        "prev_chain_sha256": row["prev_chain_sha256"],
                        "chain_sha256": row["chain_sha256"],
                    }
                )
            for row in conn.execute(
                "SELECT event_type,event_key,event_id FROM event_keys "
                "ORDER BY event_type,event_key"
            ).fetchall():
                keys.append(
                    {
                        "event_type": row["event_type"],
                        "event_key": row["event_key"],
                        "event_id": int(row["event_id"]),
                    }
                )
    else:
        raise RuntimeError(f"unsupported evidence backend: {store.backend}")

    ok, detail, head = _verify(events)
    if not ok:
        raise RuntimeError(detail)

    counts: dict[str, int] = {}
    for row in events:
        counts[row["event_type"]] = counts.get(row["event_type"], 0) + 1

    return {
        "classification": "PRIVATE_READ_ONLY_EVIDENCE_SNAPSHOT_COMPLETE",
        "backend": store.backend,
        "event_count": len(events),
        "key_count": len(keys),
        "first_event_ts": events[0]["event_ts"] if events else None,
        "last_event_ts": events[-1]["event_ts"] if events else None,
        "event_type_counts": dict(sorted(counts.items())),
        "chain_verified": True,
        "chain_detail": detail,
        "chain_head_sha256": head,
        "snapshot_sha256": _snapshot_sha(events, keys),
        "database_mutation": False,
        "secret_values_included": False,
        "events": events,
        "event_keys": keys,
    }


def emit_snapshot_log_chunks(store, *, chunk_chars: int = 8000) -> dict[str, Any]:
    if chunk_chars < 1000:
        raise ValueError("chunk_chars too small")
    snapshot = build_private_evidence_snapshot(store)
    raw = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    packed = gzip.compress(raw, compresslevel=9)
    encoded = base64.b64encode(packed).decode("ascii")
    total = (len(encoded) + chunk_chars - 1) // chunk_chars
    header = {
        "snapshot_sha256": hashlib.sha256(raw).hexdigest(),
        "gzip_sha256": hashlib.sha256(packed).hexdigest(),
        "event_count": snapshot["event_count"],
        "key_count": snapshot["key_count"],
        "chunk_chars": chunk_chars,
        "chunk_count": total,
        "database_mutation": False,
        "secret_values_included": False,
    }
    print("RADAR_BACKUP_HEADER " + json.dumps(header, sort_keys=True), flush=True)
    for idx in range(total):
        chunk = encoded[idx * chunk_chars : (idx + 1) * chunk_chars]
        print(
            f"RADAR_BACKUP_CHUNK {idx + 1}/{total} {chunk}",
            flush=True,
        )
    print("RADAR_BACKUP_END", flush=True)
    return header


def emit_snapshot_json_chunks(store, *, chunk_chars: int = 8000) -> dict[str, Any]:
    """Emit one verified snapshot as ASCII JSON chunks for private log transport."""
    if chunk_chars < 1000:
        raise ValueError("chunk_chars too small")
    snapshot = build_private_evidence_snapshot(store)
    raw_text = json.dumps(
        snapshot,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )
    raw = raw_text.encode("ascii")
    total = (len(raw_text) + chunk_chars - 1) // chunk_chars
    header = {
        "raw_json_sha256": hashlib.sha256(raw).hexdigest(),
        "event_count": snapshot["event_count"],
        "key_count": snapshot["key_count"],
        "chain_head_sha256": snapshot["chain_head_sha256"],
        "canonical_snapshot_sha256": snapshot["snapshot_sha256"],
        "chunk_chars": chunk_chars,
        "chunk_count": total,
        "database_mutation": False,
        "secret_values_included": False,
    }
    print("RADAR_JSON_HEADER " + json.dumps(header, sort_keys=True), flush=True)
    for idx in range(total):
        chunk = raw_text[idx * chunk_chars : (idx + 1) * chunk_chars]
        print(f"RADAR_JSON_CHUNK {idx + 1}/{total} {chunk}", flush=True)
    print("RADAR_JSON_END", flush=True)
    return header

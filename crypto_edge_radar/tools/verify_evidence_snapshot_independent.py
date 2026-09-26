#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

GENESIS = "0" * 64


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_snapshot_sha(events: list[dict], keys: list[dict]) -> str:
    raw = json.dumps(
        {"events": events, "event_keys": keys},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def main() -> int:
    root = Path("evidence_snapshot")
    receipt_path = root / "SNAPSHOT_RECEIPT.json"
    events_path = root / "radar_events.jsonl"
    keys_path = root / "radar_event_keys.csv"
    manifest_path = root / "MEMBER_SHA256.json"

    for p in (receipt_path, events_path, keys_path, manifest_path):
        if not p.exists():
            raise SystemExit(f"MISSING_REQUIRED_MEMBER:{p.name}")

    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("classification") != "READ_ONLY_EVIDENCE_SNAPSHOT_COMPLETE":
        raise SystemExit(f"SNAPSHOT_NOT_COMPLETE:{receipt.get('classification')}")
    if receipt.get("database_mutation") is not False:
        raise SystemExit("DATABASE_MUTATION_FIREWALL_FAIL")
    if receipt.get("secret_value_exposed") is not False:
        raise SystemExit("SECRET_EXPOSURE_FIREWALL_FAIL")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for name, expected in manifest.items():
        p = root / name
        if not p.exists():
            raise SystemExit(f"MANIFEST_MEMBER_MISSING:{name}")
        got = sha256_file(p)
        if got != expected:
            raise SystemExit(f"MANIFEST_SHA_MISMATCH:{name}")

    events: list[dict] = []
    expected_prev = GENESIS
    previous_id = 0
    counts: dict[str, int] = {}
    with events_path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            event_id = int(row["id"])
            if event_id <= previous_id:
                raise SystemExit(f"EVENT_ID_ORDER_FAIL:{line_no}:{event_id}:{previous_id}")
            previous_id = event_id

            payload_json = row["payload_json"]
            payload_sha = hashlib.sha256(payload_json.encode("utf-8")).hexdigest()
            if payload_sha != row["payload_sha256"]:
                raise SystemExit(f"PAYLOAD_SHA_FAIL:{event_id}")
            if row["prev_chain_sha256"] != expected_prev:
                raise SystemExit(f"PREV_CHAIN_FAIL:{event_id}")
            material = "|".join(
                (expected_prev, row["event_ts"], row["event_type"], payload_sha)
            )
            expected_chain = hashlib.sha256(material.encode("utf-8")).hexdigest()
            if row["chain_sha256"] != expected_chain:
                raise SystemExit(f"CHAIN_SHA_FAIL:{event_id}")
            expected_prev = expected_chain
            counts[row["event_type"]] = counts.get(row["event_type"], 0) + 1
            events.append(row)

    keys: list[dict] = []
    event_ids = {int(x["id"]) for x in events}
    seen_pairs: set[tuple[str, str]] = set()
    with keys_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != ["event_type", "event_key", "event_id"]:
            raise SystemExit(f"KEY_HEADER_FAIL:{reader.fieldnames}")
        for line_no, row in enumerate(reader, start=2):
            event_id = int(row["event_id"])
            if event_id not in event_ids:
                raise SystemExit(f"KEY_REFERENCES_MISSING_EVENT:{line_no}:{event_id}")
            pair = (row["event_type"], row["event_key"])
            if pair in seen_pairs:
                raise SystemExit(f"DUPLICATE_EVENT_KEY:{line_no}:{pair[0]}:{pair[1]}")
            seen_pairs.add(pair)
            keys.append({
                "event_type": row["event_type"],
                "event_key": row["event_key"],
                "event_id": event_id,
            })

    if len(events) != int(receipt["event_count"]):
        raise SystemExit(f"EVENT_COUNT_MISMATCH:{len(events)}:{receipt['event_count']}")
    if len(keys) != int(receipt["key_count"]):
        raise SystemExit(f"KEY_COUNT_MISMATCH:{len(keys)}:{receipt['key_count']}")
    if expected_prev != receipt["chain_head_sha256"]:
        raise SystemExit("CHAIN_HEAD_MISMATCH")
    if dict(sorted(counts.items())) != receipt.get("event_type_counts"):
        raise SystemExit("EVENT_TYPE_COUNTS_MISMATCH")

    snapshot_sha = canonical_snapshot_sha(events, keys)
    result = {
        "classification": "INDEPENDENT_READ_ONLY_BACKUP_REVERIFY_PASS",
        "event_count": len(events),
        "key_count": len(keys),
        "chain_head_sha256": expected_prev,
        "canonical_snapshot_sha256": snapshot_sha,
        "events_member_sha256": sha256_file(events_path),
        "keys_member_sha256": sha256_file(keys_path),
        "receipt_member_sha256": sha256_file(receipt_path),
        "database_mutation": False,
        "secret_value_exposed": False,
        "verification_implementation": "independent_jsonl_csv_recompute_v0.2",
    }
    out = root / "INDEPENDENT_REVERIFY.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

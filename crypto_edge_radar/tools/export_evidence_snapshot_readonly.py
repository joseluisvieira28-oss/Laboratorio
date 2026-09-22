#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import zipfile
from pathlib import Path

import psycopg

GENESIS="0"*64


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1<<20),b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_payload_hash(payload_json: str) -> str:
    return hashlib.sha256(payload_json.encode("utf-8")).hexdigest()


def main() -> int:
    out=Path("evidence_snapshot")
    out.mkdir(exist_ok=True)
    url=os.environ.get("RADAR_DATABASE_URL","").strip()

    if not url:
        receipt={
            "classification":"AUTH_REQUIRED_NOT_EXECUTED",
            "secret_name":"RADAR_DATABASE_URL",
            "secret_value_exposed":False,
            "database_mutation":False,
        }
        (out/"SNAPSHOT_RECEIPT.json").write_text(
            json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8"
        )
    else:
        with psycopg.connect(
            url,
            connect_timeout=10,
            options="-c default_transaction_read_only=on",
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id,event_ts,event_type,payload_json,payload_sha256,"
                    "prev_chain_sha256,chain_sha256 FROM radar_events ORDER BY id ASC"
                )
                events=cur.fetchall()
                cur.execute(
                    "SELECT event_type,event_key,event_id FROM radar_event_keys "
                    "ORDER BY event_type,event_key"
                )
                keys=cur.fetchall()

        expected_prev=GENESIS
        event_counts={}
        first_ts=None
        last_ts=None
        with (out/"radar_events.jsonl").open("w",encoding="utf-8") as f:
            for row in events:
                event_id,event_ts,event_type,payload_json,payload_sha,prev_hash,chain_hash=row
                got_payload=canonical_payload_hash(payload_json)
                if got_payload != payload_sha:
                    raise SystemExit(f"PAYLOAD_HASH_MISMATCH:{event_id}")
                if prev_hash != expected_prev:
                    raise SystemExit(f"PREV_CHAIN_MISMATCH:{event_id}")
                material="|".join((expected_prev,event_ts,event_type,payload_sha))
                expected_chain=hashlib.sha256(material.encode("utf-8")).hexdigest()
                if chain_hash != expected_chain:
                    raise SystemExit(f"CHAIN_HASH_MISMATCH:{event_id}")
                expected_prev=chain_hash
                event_counts[event_type]=event_counts.get(event_type,0)+1
                first_ts=first_ts or event_ts
                last_ts=event_ts
                f.write(json.dumps({
                    "id":event_id,
                    "event_ts":event_ts,
                    "event_type":event_type,
                    "payload_json":payload_json,
                    "payload_sha256":payload_sha,
                    "prev_chain_sha256":prev_hash,
                    "chain_sha256":chain_hash,
                },sort_keys=True,separators=(",",":"))+"\n")

        with (out/"radar_event_keys.csv").open("w",encoding="utf-8",newline="") as f:
            w=csv.writer(f,lineterminator="\n")
            w.writerow(["event_type","event_key","event_id"])
            w.writerows(keys)

        summary={
            "classification":"READ_ONLY_EVIDENCE_SNAPSHOT_COMPLETE",
            "event_count":len(events),
            "key_count":len(keys),
            "first_event_ts":first_ts,
            "last_event_ts":last_ts,
            "chain_verified":True,
            "chain_head_sha256":expected_prev,
            "event_type_counts":dict(sorted(event_counts.items())),
            "database_mutation":False,
            "secret_value_exposed":False,
        }
        (out/"SNAPSHOT_RECEIPT.json").write_text(
            json.dumps(summary,indent=2,sort_keys=True)+"\n",encoding="utf-8"
        )

    members=sorted(p for p in out.iterdir() if p.is_file())
    manifest={p.name:sha256_file(p) for p in members}
    (out/"MEMBER_SHA256.json").write_text(
        json.dumps(manifest,indent=2,sort_keys=True)+"\n",encoding="utf-8"
    )
    zip_path=Path("RADAR_EVIDENCE_SNAPSHOT_READONLY.zip")
    with zipfile.ZipFile(zip_path,"w",zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):
            if p.is_file():
                z.write(p,arcname=p.name)
    print(json.dumps({
        "zip":str(zip_path),
        "zip_sha256":sha256_file(zip_path),
        "receipt":json.loads((out/"SNAPSHOT_RECEIPT.json").read_text()),
    },sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

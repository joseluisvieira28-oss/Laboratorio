#!/usr/bin/env python3
"""MSEL-002 S1: download only hash-pinned public source/docs, never DB rows."""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import urllib.request

ARTICLE_ID = 33420628
API = f"https://api.figshare.com/v2/articles/{ARTICLE_ID}"
ALLOWED = {
    68211631: ("README.txt", 6616, "1180ae616fc9bfdb5616820efcbdee51"),
    68208451: ("analyze_copy_tokens.py", 27971, "4580d164cd298ab69d8597c2996908f4"),
    68208463: ("create_labels.py", 19679, "ac0e52e6c8904a68ae0f785c15707a16"),
    68208472: ("requirements.txt", 318, "3446684d859f29193044da27129d0b04"),
}
HERE = pathlib.Path(__file__).resolve().parent
RAW = HERE / "data" / "s1_source_code"
REPORT = HERE / "data" / "source_code_audit_s1_v01.json"


def md5(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()


def sha256(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def get_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "MSEL-002-S1/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def get_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "MSEL-002-S1/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def static_signals(text: str) -> dict:
    # Static source-code inventory only; do not execute author code or connect DB.
    tables = sorted(set(re.findall(r"(?:FROM|JOIN|INTO|UPDATE|TABLE)\s+([A-Za-z_][A-Za-z0-9_.]*)", text, flags=re.I)))
    quoted = sorted(set(re.findall(r"['\"]([A-Za-z_][A-Za-z0-9_]{2,})['\"]", text)))
    relevant = [x for x in quoted if any(k in x.lower() for k in (
        "copy", "token", "coin", "name", "symbol", "description", "image", "creator", "cluster", "time", "created", "gradu", "label"
    ))]
    return {
        "sql_like_table_tokens": tables[:200],
        "relevant_quoted_identifiers": relevant[:400],
        "mentions_same_creator": "same creator" in text.lower() or "same_creator" in text.lower(),
        "mentions_creator_cluster": "creator_cluster" in text.lower() or "cluster" in text.lower(),
        "mentions_image_hash": "image_hash" in text.lower() or "image hash" in text.lower(),
        "mentions_description": "description" in text.lower(),
        "mentions_graduation": "graduat" in text.lower(),
    }


def main() -> int:
    article = get_json(API)
    by_id = {int(f["id"]): f for f in article.get("files") or []}
    RAW.mkdir(parents=True, exist_ok=True)
    downloaded = []
    signals = {}
    for file_id, (name, size, expected_md5) in ALLOWED.items():
        if file_id not in by_id:
            raise RuntimeError(f"ALLOWED_FILE_ID_MISSING {file_id}")
        f = by_id[file_id]
        if f.get("name") != name or int(f.get("size", -1)) != size:
            raise RuntimeError(f"FILE_METADATA_MISMATCH {file_id} {f.get('name')} {f.get('size')}")
        provider_md5 = f.get("computed_md5") or f.get("supplied_md5")
        if provider_md5 != expected_md5:
            raise RuntimeError(f"PROVIDER_MD5_MISMATCH {name} {provider_md5}")
        url = f.get("download_url")
        if not url:
            raise RuntimeError(f"NO_DOWNLOAD_URL {name}")
        blob = get_bytes(url)
        if len(blob) != size:
            raise RuntimeError(f"SIZE_MISMATCH {name} {len(blob)}/{size}")
        if md5(blob) != expected_md5:
            raise RuntimeError(f"DOWNLOADED_MD5_MISMATCH {name}")
        p = RAW / name
        p.write_bytes(blob)
        text = blob.decode("utf-8", errors="replace")
        downloaded.append({
            "file_id": file_id,
            "name": name,
            "size": size,
            "md5": expected_md5,
            "sha256": sha256(blob),
        })
        signals[name] = static_signals(text)

    report = {
        "artifact": "MSEL_002_SOURCE_CODE_AUDIT_S1_V01",
        "record_rows_opened": False,
        "db_dump_parts_downloaded": 0,
        "prevalence_computed": False,
        "candidate_outcomes_opened": False,
        "downloaded_files": downloaded,
        "static_signals": signals,
    }
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    if REPORT.exists():
        raise RuntimeError(f"S1_OUTPUT_ALREADY_EXISTS {REPORT}")
    REPORT.write_bytes(payload)
    print("PASS: MSEL-002 S1 source-code audit complete")
    for d in downloaded:
        print(f"FILE {d['name']} sha256={d['sha256']}")
    print(f"report_sha256={sha256(payload)}")
    print("NO DB DUMP PART DOWNLOADED / NO RECORD ROW OPENED / NO OUTCOME OPENED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

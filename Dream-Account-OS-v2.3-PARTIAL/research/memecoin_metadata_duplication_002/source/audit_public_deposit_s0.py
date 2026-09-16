#!/usr/bin/env python3
"""MSEL-002 Source Stage S0: metadata-only public deposit inventory.

READ-ONLY / RESEARCH-ONLY / OUTCOMES LOCKED.

This script queries Figshare's PUBLIC ARTICLE METADATA endpoint for the authors'
KiltHub/Figshare deposit. It does not download dataset files and does not inspect
record-level rows, prevalence, labels, prices, trades, graduation, or outcomes.
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import urllib.request

ARTICLE_ID = 33420628
DOI = "10.1184/R1/33420628"
API_URL = f"https://api.figshare.com/v2/articles/{ARTICLE_ID}"
OUT = pathlib.Path(__file__).resolve().parent / "data" / "source_inventory_s0_v01.json"


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    req = urllib.request.Request(
        API_URL,
        headers={"User-Agent": "MSEL-002-S0/0.1 metadata-only research"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read()
    obj = json.loads(raw)

    if int(obj.get("id", -1)) != ARTICLE_ID:
        raise RuntimeError(f"ARTICLE_ID_MISMATCH {obj.get('id')}")

    files = []
    for f in obj.get("files") or []:
        # Inventory metadata only. Never fetch download_url here.
        files.append({
            "id": f.get("id"),
            "name": f.get("name"),
            "size": f.get("size"),
            "is_link_only": f.get("is_link_only"),
            "supplied_md5": f.get("supplied_md5"),
            "computed_md5": f.get("computed_md5"),
            "download_url_present": bool(f.get("download_url")),
        })

    inventory = {
        "artifact": "MSEL_002_PUBLIC_DEPOSIT_S0_INVENTORY_V01",
        "stage": "S0_METADATA_ONLY",
        "outcomes_locked": True,
        "record_rows_opened": False,
        "article_id": ARTICLE_ID,
        "expected_doi": DOI,
        "article_api_url": API_URL,
        "article_api_response_sha256": sha256_bytes(raw),
        "title": obj.get("title"),
        "doi": obj.get("doi"),
        "url_private_api": obj.get("url_private_api"),
        "url_public_api": obj.get("url_public_api"),
        "url_private_html": obj.get("url_private_html"),
        "url_public_html": obj.get("url_public_html"),
        "published_date": obj.get("published_date"),
        "modified_date": obj.get("modified_date"),
        "version": obj.get("version"),
        "resource_doi": obj.get("resource_doi"),
        "license": obj.get("license"),
        "defined_type_name": obj.get("defined_type_name"),
        "file_count": len(files),
        "files": files,
        "guardrails": {
            "dataset_files_downloaded": False,
            "record_level_rows_read": False,
            "prevalence_computed": False,
            "candidate_outcomes_opened": False,
        },
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    if OUT.exists():
        raise RuntimeError(f"S0_OUTPUT_ALREADY_EXISTS {OUT}")
    payload = (json.dumps(inventory, indent=2, sort_keys=True) + "\n").encode()
    OUT.write_bytes(payload)
    print("PASS: MSEL-002 public deposit S0 inventory complete")
    print(f"article={ARTICLE_ID} title={inventory['title']!r}")
    print(f"doi={inventory['doi']!r} version={inventory['version']!r}")
    print(f"file_count={len(files)} total_bytes={sum(int(f['size'] or 0) for f in files)}")
    for f in files:
        print(f"FILE name={f['name']!r} size={f['size']} md5={f['computed_md5'] or f['supplied_md5']}")
    print(f"inventory_sha256={sha256_bytes(payload)}")
    print("NO DATASET FILE DOWNLOADED / NO ROW OPENED / NO OUTCOME OPENED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

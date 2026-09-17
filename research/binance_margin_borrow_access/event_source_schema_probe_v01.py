#!/usr/bin/env python3
"""Outcome-blind schema probe for BINANCE-MARGIN-BORROW-ACCESS-001.

Inspects only the 69 structural official Binance Support articles frozen by the
V0.4 SOURCE_CENSUS_PASS. Emits string-field paths and short source snippets
around structural phrases. It does not parse market outcomes or decide edge.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

import source_census_v04 as base

SHARD_COUNT = 4
PHRASES = (
    "borrowable asset",
    "cross margin",
    "new cross margin pair",
    "isolated margin",
    "spot trading",
    "futures",
    "convert",
    "earn",
)


def walk_strings(obj: Any, path: str = "$"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            if isinstance(v, str):
                yield p, v
            elif isinstance(v, (dict, list)):
                yield from walk_strings(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            p = f"{path}[{i}]"
            if isinstance(v, str):
                yield p, v
            elif isinstance(v, (dict, list)):
                yield from walk_strings(v, p)


def clean(s: str) -> str:
    return base.normalize_text(s)


def snippet(text: str, needle: str, radius: int = 260) -> str | None:
    low = text.lower()
    pos = low.find(needle.lower())
    if pos < 0:
        return None
    a = max(0, pos - radius)
    b = min(len(text), pos + len(needle) + radius)
    return text[a:b]


def probe_article(code: str) -> dict[str, Any]:
    obj, status, raw_sha, retries = base.detail_request(code)
    data = obj.get("data", obj)
    all_text = clean(" ".join(base.collect_strings(data)))
    paths: list[dict[str, Any]] = []
    seen = set()
    for p, raw in walk_strings(data):
        text = clean(raw)
        low = text.lower()
        hits = sorted({ph for ph in PHRASES if ph in low})
        if not hits:
            continue
        key = (p, tuple(hits), hashlib.sha256(text.encode()).hexdigest())
        if key in seen:
            continue
        seen.add(key)
        snippets = []
        for ph in hits:
            s = snippet(text, ph)
            if s:
                snippets.append({"phrase": ph, "snippet": s[:900]})
        paths.append({
            "path": p,
            "string_length": len(text),
            "string_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "hits": hits,
            "snippets": snippets[:8],
        })
    article_snippets = []
    for ph in PHRASES:
        s = snippet(all_text, ph)
        if s:
            article_snippets.append({"phrase": ph, "snippet": s[:900]})
    return {
        "code": code,
        "http_status": status,
        "response_sha256": raw_sha,
        "request_retries": retries,
        "official_title": base.extract_title(obj),
        "data_type": type(data).__name__,
        "data_top_keys": sorted(data.keys()) if isinstance(data, dict) else [],
        "canonical_text_length": len(all_text),
        "structural_field_paths": paths[:40],
        "canonical_snippets": article_snippets,
        "title_has_delist_remove": bool(re.search(r"\b(delist|remove|removal)\b", base.extract_title(obj), re.I)),
        "title_has_will_add_bundle": bool(re.search(r"\bWill Add\b", base.extract_title(obj), re.I)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=Path, required=True)
    ap.add_argument("--shard", type=int, required=True)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    if not 0 <= a.shard < SHARD_COUNT:
        raise SystemExit("invalid shard")
    source = json.loads(a.input.read_text())
    codes = source.get("codes", [])
    if source.get("structural_articles") != 69 or len(codes) != 69 or len(set(codes)) != 69:
        raise SystemExit("frozen schema input invariant failed")
    assigned = [c for i, c in enumerate(codes) if i % SHARD_COUNT == a.shard]
    records = []
    failure = None
    classification = "SCHEMA_SHARD_PASS"
    try:
        for code in assigned:
            records.append(probe_article(code))
            time.sleep(2.5)
    except Exception as exc:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"
    out = {
        "lab_id": base.LAB_ID,
        "phase": "EVENT_SOURCE_SCHEMA_CENSUS_V0_1",
        "classification": classification,
        "shard": a.shard,
        "shard_count": SHARD_COUNT,
        "assigned_codes": len(assigned),
        "resolved_codes": len(records),
        "records": records,
        "failure": failure,
        "safety": base.SAFETY,
    }
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / f"schema_shard_{a.shard}.json").write_text(json.dumps(out, indent=2, sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"shard":a.shard,"assigned":len(assigned),"resolved":len(records),"failure":failure}))
    return 0 if classification == "SCHEMA_SHARD_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""BINANCE-MARGIN-BORROW-ACCESS-001 source census V0.1.

Source-only / outcome-blind.
Canonical transport after prospectively recorded remediation:
- catalog 48 is paginated deterministically for the complete 2023-2024 window;
- official CMS detail payload resolves structural article text;
- no price, market, account, borrow-rate, borrow-inventory or user data is requested.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests

LAB_ID = "BINANCE-MARGIN-BORROW-ACCESS-001"
CATALOG_ID = 48
CATALOG_ENDPOINTS = [
    "https://www.binance.com/bapi/composite/v1/public/cms/article/catalog/list/query",
    "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query",
]
DETAIL_ENDPOINTS = [
    "https://www.binance.com/bapi/composite/v1/public/cms/article/detail/query",
]
REFERER = "https://www.binance.com/en/messages/v2/group/announcement"
START_MS = int(datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp() * 1000)
END_MS = int(datetime(2024, 12, 31, 23, 59, 59, tzinfo=timezone.utc).timestamp() * 1000)
PAGE_SIZE = 20
MAX_PAGES = 500

# Fixed before this remediation; source controls only, never outcome-selected.
POSITIVE_CONTROLS = {
    "a74f935eaa2247889d58e33ec23313bb": 2023,
    "6674719e209641bda688729852d35fb5": 2024,
}

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": UA,
    "Accept-Language": "en-US,en;q=0.9",
    "lang": "en",
    "clienttype": "web",
})


def request_json(url: str, params: dict[str, str], attempts: int = 5) -> tuple[dict[str, Any], int, str]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            r = SESSION.get(url, params=params, headers={"Referer": REFERER}, timeout=45)
            status = r.status_code
            r.raise_for_status()
            raw = r.content
            obj = r.json()
            if not isinstance(obj, dict):
                raise RuntimeError("non-object JSON response")
            return obj, status, hashlib.sha256(raw).hexdigest()
        except Exception as exc:
            last = exc
            if attempt + 1 < attempts:
                time.sleep(1.25 * (attempt + 1))
    raise RuntimeError(str(last))


def iter_dicts(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from iter_dicts(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from iter_dicts(v)


def article_nodes(obj: dict[str, Any]) -> list[dict[str, Any]]:
    """Find article-like nodes independent of Binance response-envelope generation."""
    found: dict[str, dict[str, Any]] = {}
    for d in iter_dicts(obj):
        code = d.get("code") or d.get("articleCode") or d.get("articlecode")
        title = d.get("title")
        rd = d.get("releaseDate") or d.get("releaseTime") or d.get("publishTime")
        if code and title and rd is not None:
            try:
                rd_i = int(rd)
            except (TypeError, ValueError):
                continue
            if rd_i < 10_000_000_000:
                rd_i *= 1000
            c = str(code).strip()
            if not re.fullmatch(r"[0-9a-fA-F]{32}", c):
                continue
            found[c.lower()] = {
                "code": c.lower(),
                "title": str(title).strip(),
                "releaseDate": rd_i,
            }
    return list(found.values())


def get_catalog_page(page: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    failures = []
    for endpoint in CATALOG_ENDPOINTS:
        params = {
            "type": "1",
            "catalogId": str(CATALOG_ID),
            "pageNo": str(page),
            "pageSize": str(PAGE_SIZE),
        }
        try:
            obj, status, sha = request_json(endpoint, params)
            arts = article_nodes(obj)
            if not arts:
                failures.append(f"{endpoint}: no article nodes")
                continue
            return arts, {
                "endpoint": endpoint,
                "http_status": status,
                "response_sha256": sha,
                "article_nodes": len(arts),
            }
        except Exception as exc:
            failures.append(f"{endpoint}: {type(exc).__name__}: {str(exc)[:180]}")
    raise RuntimeError("catalog transports failed: " + " | ".join(failures))


def normalize_text(raw: str) -> str:
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def collect_strings(obj: Any) -> list[str]:
    out: list[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            # Exclude URLs/IDs where possible; content/title/summary strings remain.
            if isinstance(v, str) and k.lower() not in {"url", "link", "shareurl", "image", "icon"}:
                out.append(v)
            elif isinstance(v, (dict, list)):
                out.extend(collect_strings(v))
    elif isinstance(obj, list):
        for v in obj:
            out.extend(collect_strings(v))
    return out


def resolve_detail(code: str) -> dict[str, Any]:
    failures = []
    for endpoint in DETAIL_ENDPOINTS:
        for key in ("articleCode", "articlecode"):
            try:
                obj, status, sha = request_json(endpoint, {key: code})
                strings = collect_strings(obj.get("data", obj))
                text = normalize_text(" ".join(strings))
                # Provenance: the requested code must occur in a code-like field somewhere in payload,
                # unless Binance's detail generation omits it but returns non-empty canonical content.
                codes_in_payload = set()
                for d in iter_dicts(obj):
                    for ck in ("code", "articleCode", "articlecode"):
                        if d.get(ck):
                            codes_in_payload.add(str(d.get(ck)).lower())
                code_match = (code.lower() in codes_in_payload) if codes_in_payload else False
                if not text:
                    failures.append(f"{endpoint}?{key}: empty canonical text")
                    continue
                low = text.lower()
                return {
                    "code": code,
                    "detail_endpoint": endpoint,
                    "detail_param": key,
                    "http_status": status,
                    "response_sha256": sha,
                    "canonical_text_length": len(text),
                    "payload_code_match": code_match,
                    "contains_borrowable_asset_phrase": "borrowable asset" in low,
                    "contains_cross_margin_phrase": "cross margin" in low,
                    "structural_phrase_pass": ("borrowable asset" in low and "cross margin" in low),
                }
            except Exception as exc:
                failures.append(f"{endpoint}?{key}: {type(exc).__name__}: {str(exc)[:180]}")
    raise RuntimeError("detail transports failed for " + code + ": " + " | ".join(failures))


def main() -> int:
    article_by_code: dict[str, dict[str, Any]] = {}
    pages: list[dict[str, Any]] = []
    failure = None
    reached_before_start = False
    repeated_without_new = 0

    try:
        for page in range(1, MAX_PAGES + 1):
            arts, transport = get_catalog_page(page)
            dates = [a["releaseDate"] for a in arts]
            before = len(article_by_code)
            for a in arts:
                # Retain only through frozen end; older records are allowed only to prove lower boundary.
                if a["releaseDate"] <= END_MS:
                    article_by_code.setdefault(a["code"], a)
            added = len(article_by_code) - before
            pages.append({
                "page": page,
                "records_returned": len(arts),
                "new_records_at_or_before_frozen_end": added,
                "min_release_ms": min(dates),
                "max_release_ms": max(dates),
                **transport,
            })
            if min(dates) < START_MS:
                reached_before_start = True
                break
            repeated_without_new = repeated_without_new + 1 if added == 0 else 0
            if repeated_without_new >= 3:
                raise RuntimeError("catalog pagination repeated without new records before lower boundary")

        frozen = sorted(
            [a for a in article_by_code.values() if START_MS <= a["releaseDate"] <= END_MS],
            key=lambda x: (x["releaseDate"], x["code"]),
        )
        margin_like = [
            a for a in frozen
            if any(k in a["title"].lower() for k in ("margin", "borrowable", "cross margin"))
        ]
        codes_to_resolve = {a["code"] for a in margin_like} | set(POSITIVE_CONTROLS)
        resolved = []
        for code in sorted(codes_to_resolve):
            meta = article_by_code.get(code.lower())
            if meta is None:
                resolved.append({
                    "code": code.lower(), "index_present": False,
                    "payload_code_match": False, "structural_phrase_pass": False,
                })
                continue
            d = resolve_detail(code.lower())
            d.update({
                "index_present": True,
                "releaseDate": meta["releaseDate"],
                "title": meta["title"],
            })
            resolved.append(d)

        controls = {
            c: next((x for x in resolved if x["code"] == c), {
                "index_present": False, "payload_code_match": False, "structural_phrase_pass": False
            })
            for c in POSITIVE_CONTROLS
        }
        controls_ok = all(
            x.get("index_present") and x.get("payload_code_match") and x.get("structural_phrase_pass")
            for x in controls.values()
        )
        qualifying = [x for x in resolved if x.get("structural_phrase_pass")]
        years_with_phrase = sorted({
            datetime.fromtimestamp(x["releaseDate"] / 1000, tz=timezone.utc).year
            for x in qualifying
            if START_MS <= x.get("releaseDate", 0) <= END_MS
        })

        if not reached_before_start:
            classification = "SOURCE_ENUMERATION_INCOMPLETE"
        elif not controls_ok:
            classification = "PROVENANCE_FAILURE"
        elif not ({2023, 2024} <= set(years_with_phrase)):
            classification = "INSUFFICIENT_EVENT_SAMPLE"
        else:
            classification = "SOURCE_CENSUS_PASS"
    except Exception as exc:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        failure = f"{type(exc).__name__}: {str(exc)[:1000]}"
        frozen = []
        margin_like = []
        resolved = []
        qualifying = []
        years_with_phrase = []
        controls = {}

    receipt = {
        "lab_id": LAB_ID,
        "phase": "SOURCE_CENSUS_ONLY_OUTCOME_BLIND",
        "classification": classification,
        "catalog_id": CATALOG_ID,
        "frozen_start_utc": "2023-01-01T00:00:00Z",
        "frozen_end_utc": "2024-12-31T23:59:59Z",
        "enumeration_boundary_reached_before_start": reached_before_start,
        "pages": pages,
        "unique_frozen_article_metadata": len(frozen),
        "margin_title_candidates": len(margin_like),
        "resolved_margin_or_control_articles": len(resolved),
        "qualifying_cross_margin_borrowable_articles": len(qualifying),
        "years_with_structural_phrase": years_with_phrase,
        "positive_controls": controls,
        "resolved_articles": resolved,
        "failure": failure,
        "safety": {
            "price_data_opened": False,
            "returns_opened": False,
            "basis_opened": False,
            "borrow_rate_opened": False,
            "borrow_inventory_opened": False,
            "authenticated_exchange_api_used": False,
            "pnl_opened": False,
            "scientific_candidates_outside_2023_2024_retained": False,
            "live_trading": False,
            "exchange_mutation": False,
        },
    }
    out = Path("source_census_output")
    out.mkdir(parents=True, exist_ok=True)
    path = out / "BINANCE_MARGIN_BORROW_ACCESS_001_SOURCE_CENSUS_RECEIPT_V0_1.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "lab_id": LAB_ID,
        "classification": classification,
        "catalog_id": CATALOG_ID,
        "enumeration_boundary_reached": reached_before_start,
        "unique_frozen_article_metadata": len(frozen),
        "margin_title_candidates": len(margin_like),
        "qualifying_articles": len(qualifying),
        "years_with_structural_phrase": years_with_phrase,
        "prices_opened": False,
        "returns_opened": False,
        "pnl_opened": False,
    }, sort_keys=True))
    return 0 if classification == "SOURCE_CENSUS_PASS" else 2


if __name__ == "__main__":
    sys.exit(main())

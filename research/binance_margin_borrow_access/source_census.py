#!/usr/bin/env python3
"""BINANCE-MARGIN-BORROW-ACCESS-001 source census.

Source-only / outcome-blind:
- enumerates Binance announcement metadata from Binance public CMS transport;
- resolves only official Binance Support article identity/text for structural phrases;
- never requests price, market, account, margin-rate, borrow inventory or user data;
- never accesses 2025/2026 article candidates for the scientific event window.
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
from typing import Any

import requests

LAB_ID = "BINANCE-MARGIN-BORROW-ACCESS-001"
INDEX = "https://www.binance.com/bapi/apex/v1/public/apex/cms/article/list/query"
ARTICLE = "https://www.binance.com/en/support/announcement/detail/{code}"
REFERER = "https://www.binance.com/en/messages/v2/group/announcement"
START_MS = int(datetime(2023,1,1,tzinfo=timezone.utc).timestamp()*1000)
END_MS = int(datetime(2024,12,31,23,59,59,tzinfo=timezone.utc).timestamp()*1000)
# Transport-only remediation: use the website-compatible page size demonstrated by the current announcement client.
PAGE_SIZE = 20
MAX_PAGES = 600

# Positive source controls prospectively fixed before execution; not a discovery sample.
POSITIVE_CONTROLS = {
    "a74f935eaa2247889d58e33ec23313bb": 2023,
    "6674719e209641bda688729852d35fb5": 2024,
}

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9", "lang": "en"})


def get_index(page: int) -> dict[str, Any]:
    params = {"type": "1", "pageNo": str(page), "pageSize": str(PAGE_SIZE)}
    last = None
    for attempt in range(5):
        try:
            r = SESSION.get(INDEX, params=params, headers={"Referer": REFERER}, timeout=45)
            r.raise_for_status()
            obj = r.json()
            if str(obj.get("code")) not in ("000000", "0", "200", "None") and not obj.get("data"):
                raise RuntimeError(f"CMS code={obj.get('code')} msg={obj.get('message')}")
            return obj
        except Exception as exc:
            last = exc
            if attempt < 4:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(str(last))


def flatten_articles(obj: dict[str, Any]) -> list[dict[str, Any]]:
    data = obj.get("data") or {}
    catalogs = data.get("catalogs") or []
    out = []
    for cat in catalogs:
        cid = cat.get("catalogId")
        cname = cat.get("catalogName")
        for a in cat.get("articles") or []:
            code = str(a.get("code") or "").strip()
            title = str(a.get("title") or "").strip()
            rd = a.get("releaseDate")
            if not code or not title or rd is None:
                continue
            out.append({"code": code, "title": title, "releaseDate": int(rd), "catalogId": cid, "catalogName": cname})
    return out


def normalize_text(raw: str) -> str:
    raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.I|re.S)
    raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.I|re.S)
    raw = re.sub(r"<[^>]+>", " ", raw)
    raw = html.unescape(raw)
    return re.sub(r"\s+", " ", raw).strip()


def fetch_article(code: str) -> dict[str, Any]:
    url = ARTICLE.format(code=code)
    r = SESSION.get(url, timeout=45, headers={"Referer": REFERER})
    r.raise_for_status()
    text = normalize_text(r.text)
    low = text.lower()
    has_borrowable = "borrowable asset" in low
    has_cross = "cross margin" in low
    return {
        "code": code,
        "url": url,
        "http_status": r.status_code,
        "text_bytes": len(r.content),
        "text_sha256": hashlib.sha256(r.content).hexdigest(),
        "contains_borrowable_asset_phrase": has_borrowable,
        "contains_cross_margin_phrase": has_cross,
        "structural_phrase_pass": has_borrowable and has_cross,
    }


def main() -> int:
    article_by_code: dict[str, dict[str, Any]] = {}
    pages = []
    failure = None
    reached_before_start = False
    no_new_pages = 0

    try:
        for page in range(1, MAX_PAGES + 1):
            obj = get_index(page)
            arts = flatten_articles(obj)
            before = len(article_by_code)
            dates = []
            for a in arts:
                dates.append(a["releaseDate"])
                if a["releaseDate"] <= END_MS:
                    article_by_code.setdefault(a["code"], a)
            added = len(article_by_code) - before
            pages.append({
                "page": page,
                "records_returned": len(arts),
                "new_records_at_or_before_frozen_end": added,
                "min_release_ms": min(dates) if dates else None,
                "max_release_ms": max(dates) if dates else None,
            })
            if dates and min(dates) < START_MS:
                reached_before_start = True
                break
            if added == 0:
                no_new_pages += 1
            else:
                no_new_pages = 0
            if no_new_pages >= 3:
                break

        frozen = [a for a in article_by_code.values() if START_MS <= a["releaseDate"] <= END_MS]
        frozen.sort(key=lambda x: (x["releaseDate"], x["code"]))
        margin_like = [a for a in frozen if "margin" in a["title"].lower()]
        codes_to_resolve = {a["code"] for a in margin_like} | set(POSITIVE_CONTROLS)
        resolved = []
        for code in sorted(codes_to_resolve):
            if code not in article_by_code:
                resolved.append({"code": code, "index_present": False, "structural_phrase_pass": False})
                continue
            x = fetch_article(code)
            x["index_present"] = True
            meta = article_by_code[code]
            x["releaseDate"] = meta["releaseDate"]
            x["title"] = meta["title"]
            resolved.append(x)

        controls = {
            c: next((x for x in resolved if x["code"] == c), {"index_present": False, "structural_phrase_pass": False})
            for c in POSITIVE_CONTROLS
        }
        controls_ok = all(x.get("index_present") and x.get("structural_phrase_pass") for x in controls.values())
        years_with_phrase = sorted({
            datetime.fromtimestamp(x["releaseDate"] / 1000, tz=timezone.utc).year
            for x in resolved
            if x.get("structural_phrase_pass") and START_MS <= x.get("releaseDate", 0) <= END_MS
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
        failure = f"{type(exc).__name__}: {str(exc)[:700]}"
        frozen = []
        margin_like = []
        resolved = []
        years_with_phrase = []
        controls = {}

    receipt = {
        "lab_id": LAB_ID,
        "phase": "SOURCE_CENSUS_ONLY_OUTCOME_BLIND",
        "classification": classification,
        "frozen_start_utc": "2023-01-01T00:00:00Z",
        "frozen_end_utc": "2024-12-31T23:59:59Z",
        "enumeration_boundary_reached_before_start": reached_before_start,
        "transport_page_size": PAGE_SIZE,
        "pages": pages,
        "unique_frozen_article_metadata": len(frozen),
        "margin_title_candidates": len(margin_like),
        "resolved_margin_or_control_articles": len(resolved),
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
        "lab_id": LAB_ID, "classification": classification,
        "enumeration_boundary_reached": reached_before_start,
        "unique_frozen_article_metadata": len(frozen),
        "margin_title_candidates": len(margin_like),
        "resolved_articles": len(resolved),
        "years_with_structural_phrase": years_with_phrase,
        "prices_opened": False, "returns_opened": False, "pnl_opened": False,
    }, sort_keys=True))
    return 0 if classification == "SOURCE_CENSUS_PASS" else 2

if __name__ == "__main__":
    sys.exit(main())

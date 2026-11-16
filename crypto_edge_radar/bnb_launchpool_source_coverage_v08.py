#!/usr/bin/env python3
"""BNB V8 audit: source coverage only. Never read market outcomes or trading APIs."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from radar.bnb_launchpool_watcher import (
    BinanceOfficialLaunchpoolSource,
    CATALOG_ID, CATALOG_PATH, PAGE_SIZE,
    _article_code_from_dict, _find_original_publication_ms,
)

COMMIT_BOUNDARY_UTC = "2026-09-24T17:58:57Z"
BOUNDARY_MS = int(datetime.fromisoformat(COMMIT_BOUNDARY_UTC.replace("Z", "+00:00")).timestamp() * 1000)
MAX_PAGES = 80
OUT = Path("artifacts/bnb_launchpool/source_coverage_v08")


def catalog_articles(payload: Any) -> list[dict[str, Any]]:
    """Deduplicate article objects by official 32-character code."""
    found: dict[str, dict[str, Any]] = {}
    def walk(node: Any) -> None:
        if isinstance(node, list):
            for child in node:
                walk(child)
        elif isinstance(node, dict):
            code = _article_code_from_dict(node)
            title = node.get("title")
            if code and isinstance(title, str):
                found[code] = {
                    "code": code, "title": title.strip(),
                    "listed_published_ms": _find_original_publication_ms(node),
                }
            for child in node.values():
                walk(child)
    walk(payload)
    return sorted(found.values(), key=lambda x: x["code"])


def audit(source: BinanceOfficialLaunchpoolSource, *, now_ms: int, max_pages: int = MAX_PAGES) -> dict[str, Any]:
    if max_pages < 2:
        raise ValueError("audit must check more than the first page")
    page_receipts: list[dict[str, Any]] = []
    candidates: dict[str, dict[str, Any]] = {}
    previous_signature: tuple[str, ...] | None = None
    all_codes: set[str] = set()
    end_reason = "MAX_PAGES_REACHED__NOT_EXHAUSTIVE"
    for page_no in range(1, max_pages + 1):
        data, raw = source._get(CATALOG_PATH, {
            "catalogId": CATALOG_ID, "pageNo": page_no, "pageSize": PAGE_SIZE,
        })
        if isinstance(data, dict) and data.get("success") is False:
            end_reason = "PROVIDER_REPORTED_FAILURE"
            break
        articles = catalog_articles(data)
        signature = tuple(a["code"] for a in articles)
        listed_times = [int(a["listed_published_ms"]) for a in articles if a["listed_published_ms"]]
        receipt = {
            "page_no": page_no,
            "catalog_sha256": hashlib.sha256(raw).hexdigest(),
            "unique_article_count": len(articles),
            "launchpool_title_count": sum("launchpool" in a["title"].lower() for a in articles),
            "min_listed_pub_ms": min(listed_times) if listed_times else None,
            "max_listed_pub_ms": max(listed_times) if listed_times else None,
        }
        page_receipts.append(receipt)
        if not articles:
            end_reason = "END_OF_PAGINATION_VERIFIED" if page_no > 1 and all_codes else "SCHEMA_EMPTY_OR_FIRST_PAGE_EMPTY__BLOCKED"
            break
        if signature == previous_signature:
            end_reason = "PAGINATION_REPEATS_PREVIOUS_PAGE__BLOCKED"
            break
        previous_signature = signature
        all_codes.update(signature)
        for row in articles:
            if "launchpool" in row["title"].lower():
                candidates.setdefault(row["code"], {
                    **row, "first_catalog_page": page_no,
                })

    selected = []
    failures = []
    for code, row in sorted(candidates.items()):
        try:
            event = source.validate_detail(
                article_code=code, fallback_title=row["title"],
                now_ms=now_ms, require_post_boundary=True,
            )
        except Exception as exc:
            failures.append({"article_code": code, "error": f"{type(exc).__name__}:{exc}"})
            continue
        if event is not None and event.published_ms > BOUNDARY_MS:
            selected.append({
                "article_code": event.article_code,
                "title": event.title, "published_utc": event.published_utc,
                "published_ms": event.published_ms,
                "detail_sha256": event.detail_sha256,
                "first_catalog_page": row["first_catalog_page"],
                "NEVER_BACKFILL_PROSPECTIVE": True,
            })

    fully_paginated = end_reason == "END_OF_PAGINATION_VERIFIED"
    source_coverage_complete = fully_paginated and not failures
    classification = (
        "SOURCE_CATALOG_PAGINATION_PASS__NO_TRADING_CLAIM"
        if source_coverage_complete else "SOURCE_COVERAGE_BLOCKED__NO_ZERO_EVENT_CLAIM"
    )
    return {
        "audit_id": "BNB-LAUNCHPOOL-SOURCE-COVERAGE-V08-2026-11-16",
        "checked_at_utc": datetime.fromtimestamp(now_ms/1000, tz=timezone.utc).isoformat(),
        "prospective_boundary_utc": COMMIT_BOUNDARY_UTC,
        "provider": "BINANCE_SUPPORT_CMS_PUBLIC",
        "catalog_id": CATALOG_ID,
        "page_size": PAGE_SIZE,
        "pages_examined": len(page_receipts),
        "articles_found_unique": len(all_codes),
        "launchpool_title_candidates": len(candidates),
        "qualified_post_boundary_count": len(selected),
        "qualified_post_boundary_articles": selected,
        "detail_failures": failures,
        "pages": page_receipts,
        "pagination_end_reason": end_reason,
        "source_coverage_complete": source_coverage_complete,
        "classification": classification,
        "limitation": (
            "A catalogue queried retrospectively cannot prove first-observed-at signal time. "
            "This audit cannot claim historical forward trades or 25-event diamond qualification. "
            "Title-screening does not certify that every Launchpool body outside Launchpool titles was detected."
        ),
        "market_prices_accessed": False,
        "outcomes_accessed": False,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_trading_authorized": False,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    now_ms = int(datetime.now(timezone.utc).timestamp() * 1000)
    try:
        result = audit(BinanceOfficialLaunchpoolSource(timeout=12), now_ms=now_ms)
    except Exception as exc:
        result = {
            "audit_id": "BNB-LAUNCHPOOL-SOURCE-COVERAGE-V08-2026-11-16",
            "classification": "SOURCE_COVERAGE_BLOCKED__NO_ZERO_EVENT_CLAIM",
            "error": f"{type(exc).__name__}:{exc}",
            "checked_at_utc": datetime.now(timezone.utc).isoformat(),
            "market_prices_accessed": False, "outcomes_accessed": False,
            "orders_created": False, "exchange_mutation_performed": False,
        }
    (OUT / "SOURCE_COVERAGE_V08.json").write_text(
        json.dumps(result, sort_keys=True, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: result.get(k) for k in (
        "classification", "error", "pages_examined", "articles_found_unique",
        "qualified_post_boundary_count", "pagination_end_reason",
        "source_coverage_complete",
    )}, indent=2))
    return 0 if result["classification"] == "SOURCE_CATALOG_PAGINATION_PASS__NO_TRADING_CLAIM" else 2


if __name__ == "__main__":
    raise SystemExit(main())

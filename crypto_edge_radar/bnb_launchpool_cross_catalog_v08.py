#!/usr/bin/env python3
"""Source-only cross-category sentinel audit. Does not change frozen parent watcher."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path

from bnb_launchpool_source_coverage_v08 import audit, MAX_PAGES, OUT
from radar.bnb_launchpool_watcher import BinanceOfficialLaunchpoolSource, CATALOG_PATH

# Official Binance announcements categories: latest news, activities, crypto airdrop.
# 48 is separately covered by the frozen V8 primary source audit.
SECONDARY_CATALOG_IDS = (49, 93, 128)


class RoutedCatalogSource(BinanceOfficialLaunchpoolSource):
    def __init__(self, catalog_id: int) -> None:
        super().__init__(timeout=12)
        self.catalog_id = catalog_id

    def _get(self, path, query):
        q = dict(query)
        if path == CATALOG_PATH:
            q["catalogId"] = self.catalog_id
        return super()._get(path, q)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    now_ms = int(datetime.now(timezone.utc).timestamp()*1000)
    results = []
    for catalog_id in SECONDARY_CATALOG_IDS:
        try:
            report = audit(RoutedCatalogSource(catalog_id), now_ms=now_ms, max_pages=MAX_PAGES)
            report["catalog_id"] = catalog_id
            report["audit_scope"] = "SECONDARY_CATEGORY_SENTINEL__NON_CANONICAL__READ_ONLY"
        except Exception as exc:
            report = {
                "catalog_id": catalog_id,
                "classification": "SOURCE_COVERAGE_BLOCKED__NO_ZERO_EVENT_CLAIM",
                "error": f"{type(exc).__name__}:{exc}",
                "source_coverage_complete": False,
                "market_prices_accessed": False,
                "outcomes_accessed": False,
            }
        results.append(report)
    combined = {
        "audit_id": "BNB-LAUNCHPOOL-SOURCE-COVERAGE-V08-CROSS-CATEGORY-SENTINEL",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "categories": results,
        "all_categories_exhausted": all(x.get("source_coverage_complete") for x in results),
        "total_historic_postboundary_articles_found": sum(x.get("qualified_post_boundary_count",0) for x in results),
        "scientific_significance": "Source provenance only. No retrospectively found article qualifies as prospective execution evidence.",
        "parent_rules_changed": False,
        "market_prices_accessed": False, "outcomes_accessed": False, "orders_created": False,
        "authenticated_exchange_api_used": False, "exchange_mutation_performed": False,
    }
    (OUT/"CROSS_CATEGORY_SENTINEL.json").write_text(json.dumps(combined,sort_keys=True,indent=2),encoding="utf-8")
    print(json.dumps({
        "all_categories_exhausted":combined["all_categories_exhausted"],
        "total_historic_postboundary_articles_found":combined["total_historic_postboundary_articles_found"],
        "categories":[{
            k:r.get(k) for k in ("catalog_id","classification","pages_examined",
                               "articles_found_unique","launchpool_title_candidates",
                               "qualified_post_boundary_count","pagination_end_reason","error")
        } for r in results]
    },indent=2))
    return 0 if combined["all_categories_exhausted"] else 2


if __name__ == "__main__":
    raise SystemExit(main())

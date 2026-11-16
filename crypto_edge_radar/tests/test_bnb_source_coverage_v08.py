"""Deterministic source-only tests. No network, prices or private data."""
import json
import unittest
from types import SimpleNamespace

from bnb_launchpool_source_coverage_v08 import audit, catalog_articles, BOUNDARY_MS


def row(ch, title):
    return {"articleCode": ch * 32, "title": title, "releaseDate": BOUNDARY_MS + 3600000}


class FakeSource:
    def __init__(self, pages):
        self.pages = pages
        self.detail_calls = []
    def _get(self, path, query):
        page = self.pages.get(query["pageNo"], {"data": {"catalogs": []}})
        return page, json.dumps(page).encode()
    def validate_detail(self, *, article_code, fallback_title, now_ms, require_post_boundary):
        self.detail_calls.append(article_code)
        return SimpleNamespace(
            article_code=article_code, title=fallback_title,
            published_ms=BOUNDARY_MS+3600000,
            published_utc="2026-09-24T18:58:57Z",
            detail_sha256="c"*64
        )


class CoverageTests(unittest.TestCase):
    def test_nested_catalog_article_extraction(self):
        payload = {"data": {"catalogs": [{"articles": [
            row("a", "Ordinary listing"), row("b", "Introducing B on Launchpool"),
            row("a", "Ordinary listing"),
        ]}]}}
        self.assertEqual(len(catalog_articles(payload)), 2)

    def test_page_two_candidate_cannot_be_silently_ignored(self):
        pages = {
            1: {"data": {"catalogs": [{"articles": [row("a", "Ordinary listing")]}]}},
            2: {"data": {"catalogs": [{"articles": [row("b", "Introducing B on Launchpool")]}]}},
            3: {"data": {"catalogs": []}},
        }
        source = FakeSource(pages)
        report = audit(source, now_ms=BOUNDARY_MS+86400000, max_pages=4)
        self.assertTrue(report["source_coverage_complete"])
        self.assertEqual(report["qualified_post_boundary_count"], 1)
        self.assertEqual(report["qualified_post_boundary_articles"][0]["first_catalog_page"], 2)

    def test_repeated_page_is_not_exhaustion(self):
        item = {"data": {"catalogs": [{"articles": [row("a", "Ordinary listing")]}]}}
        source = FakeSource({1:item,2:item})
        report = audit(source, now_ms=BOUNDARY_MS+86400000, max_pages=3)
        self.assertFalse(report["source_coverage_complete"])
        self.assertEqual(report["pagination_end_reason"], "PAGINATION_REPEATS_PREVIOUS_PAGE__BLOCKED")

    def test_max_pages_is_not_zero_event_proof(self):
        pages = {i: {"data": {"catalogs": [{"articles": [row(format(i,"032x")[-1], "Ordinary listing")]}]}}
                 for i in range(1, 3)}
        source = FakeSource(pages)
        report = audit(source, now_ms=BOUNDARY_MS+86400000, max_pages=2)
        self.assertFalse(report["source_coverage_complete"])
        self.assertEqual(report["pagination_end_reason"], "MAX_PAGES_REACHED__NOT_EXHAUSTIVE")

if __name__ == "__main__":
    unittest.main()

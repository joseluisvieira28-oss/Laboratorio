"""BNB V9: deterministic fail-closed source-only tests; zero network calls."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError

from bnb_launchpool_source_v09 import (
    audit_one, load_state, new_state, parse_utc, retry_after_seconds,
    save_state, utc, known_catalog_schema
)

NOW = datetime(2026, 11, 16, 10, 50, tzinfo=timezone.utc)

def row(c: str, title: str):
    return {
        "articleCode": c * 32,
        "title": title,
        "releaseDate": int(NOW.timestamp() * 1000) - 60_000
    }

def payload(*entries):
    return {"success": True, "data": {"catalogs": [{"articles": list(entries)}]}}

def empty_payload():
    return {"success": True, "data": {"catalogs": []}}

class Fake:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []
    def __call__(self, catalog_id, page):
        self.calls.append((catalog_id, page))
        response = self.responses[page]
        if isinstance(response, BaseException):
            raise response
        return response, json.dumps(response).encode("utf-8")

class SourceV9Tests(unittest.TestCase):
    def test_page_one_is_incremental_not_global_zero(self):
        f = Fake({1: payload(row("a", "ordinary listing"))})
        s, r = audit_one(new_state(), catalog_id=49, now=NOW, transport=f)
        self.assertEqual(r["status"], "INCREMENTAL_PAGE_OBSERVED__NOT_FORWARD_PROOF")
        self.assertEqual(r["attempted_requests"], 1)
        self.assertEqual(s["catalogs"]["49"]["next_page"], 2)
        self.assertEqual(len(f.calls), 1)
        self.assertFalse(r.get("all_categories_complete", False))

    def test_first_seen_is_stable_and_never_backfilled(self):
        f = Fake({
            1: payload(row("b", "New Launchpool project")),
            2: payload(row("b", "New Launchpool project"), row("a", "other"))
        })
        s, r = audit_one(new_state(), catalog_id=49, now=NOW, transport=f)
        first = s["catalogs"]["49"]["first_seen"]["b"*32]
        self.assertEqual(first["first_seen_at_utc"], utc(NOW))
        self.assertFalse(first["historical_backfill_allowed"])
        self.assertFalse(first["detail_eligibility_verified"])
        s, r2 = audit_one(s, catalog_id=49, now=NOW+timedelta(minutes=16), transport=f)
        self.assertEqual(first, s["catalogs"]["49"]["first_seen"]["b"*32])
        self.assertEqual(r2["status"], "INCREMENTAL_PAGE_OBSERVED__NOT_FORWARD_PROOF")

    def test_empty_first_page_cannot_mean_no_eligible_events(self):
        f = Fake({1: empty_payload()})
        s,r = audit_one(new_state(), catalog_id=49, now=NOW, transport=f)
        self.assertEqual(r["status"], "EMPTY_FIRST_PAGE_SOURCE_BLOCKED")
        self.assertEqual(s["catalogs"]["49"]["next_page"], 1)

    def test_repeated_page_detected(self):
        item = payload(row("c","regular"))
        f = Fake({1:item, 2:item})
        s,r = audit_one(new_state(), catalog_id=49, now=NOW, transport=f)
        s,r = audit_one(s, catalog_id=49, now=NOW+timedelta(minutes=16), transport=f)
        self.assertEqual(r["status"], "PAGINATION_REPEAT_SOURCE_BLOCKED")
        self.assertEqual(s["catalogs"]["49"]["next_page"],2)

    def test_valid_empty_page_requires_review_not_forward_promotion(self):
        f = Fake({1:payload(row("a","regular")), 2:empty_payload()})
        s,_ = audit_one(new_state(), catalog_id=49, now=NOW, transport=f)
        s,r = audit_one(s, catalog_id=49, now=NOW+timedelta(minutes=16), transport=f)
        self.assertEqual(r["status"],"CATALOG_PAGINATION_REACHED_END__NOT_FORWARD_PROOF")
        self.assertEqual(s["catalogs"]["49"]["phase"],"CATALOG_REACHED_END__REVIEW_REQUIRED")

    def test_http_429_without_retry_and_global_cooldown(self):
        err = HTTPError("https://www.binance.com",429,"Too Many Requests",{"Retry-After":"120"},None)
        f = Fake({1:err})
        s,r = audit_one(new_state(), catalog_id=49, now=NOW, transport=f)
        self.assertEqual(r["status"],"HTTP_429_SOURCE_BLOCKED")
        self.assertEqual(f.calls, [(49,1)])
        self.assertGreaterEqual(parse_utc(r["next_eligible_utc"]), NOW+timedelta(hours=1))
        s,r2 = audit_one(s, catalog_id=93, now=NOW+timedelta(minutes=10), transport=f)
        self.assertEqual(r2["attempted_requests"],0)
        self.assertEqual(r2["status"],"GLOBAL_COOLDOWN_HONORED__SOURCE_PENDING")
        self.assertEqual(len(f.calls),1)

    def test_retry_after_http_date(self):
        future = NOW+timedelta(minutes=95)
        h = format_datetime(future)
        self.assertEqual(retry_after_seconds(h, NOW),95*60)
        self.assertEqual(retry_after_seconds("bogus",NOW),3600)

    def test_checkpoint_digest_and_tamper_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            path=Path(td)
            state=new_state()
            digest=save_state(state,path)
            restored,status=load_state(path)
            self.assertEqual(restored,state)
            self.assertEqual(status,"VERIFIED_RESTORED_CHECKPOINT")
            self.assertEqual(len(digest),64)
            (path/"checkpoint.json").write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"CHECKPOINT_SHA256_MISMATCH"):
                load_state(path)

    def test_partial_checkpoint_fails(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td)/"checkpoint.json").write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"CHECKPOINT_PAIR_INCOMPLETE"):
                load_state(Path(td))

    def test_schema_mismatch_fail_closed(self):
        f=Fake({1:{"success":True, "data":{"unexpected":{"rows":[]}}}})
        s,r=audit_one(new_state(),catalog_id=49,now=NOW,transport=f)
        self.assertEqual(r["status"],"SCHEMA_ERROR_SOURCE_BLOCKED")
        self.assertEqual(s["catalogs"]["49"]["next_page"],1)

    def test_invalid_launchpool_article_identity_blocked(self):
        f=Fake({1:payload({"title":"Launchpool BNB staking","articleCode":"INVALID"})})
        s,r=audit_one(new_state(),catalog_id=49,now=NOW,transport=f)
        self.assertEqual(r["status"],"BAD_LAUNCHPOOL_ARTICLE_ID_SOURCE_BLOCKED")
        self.assertEqual(s["catalogs"]["49"]["next_page"],1)

    def test_per_category_min_spacing_prevents_request(self):
        f=Fake({1:payload(row("a","normal"))})
        s,_=audit_one(new_state(),catalog_id=49,now=NOW,transport=f)
        s,r=audit_one(s,catalog_id=49,now=NOW+timedelta(minutes=2),transport=f)
        self.assertEqual(r["status"],"CATALOG_MIN_INTERVAL_HONORED__SOURCE_PENDING")
        self.assertEqual(len(f.calls),1)

if __name__ == "__main__":
    unittest.main()

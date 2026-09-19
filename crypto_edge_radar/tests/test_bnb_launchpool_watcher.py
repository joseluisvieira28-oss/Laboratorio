from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from radar.bnb_launchpool_watcher import (
    BNBLaunchpoolForwardShadowWatcher,
    BinanceOfficialLaunchpoolSource,
    LaunchpoolAnnouncement,
    _candidate_rows,
    _cluster_announcements,
    _cluster_key,
    MISSED_PROSPECTIVE_EVENT,
)
from radar.evidence import EvidenceStore
from radar.strategies.bnb_launchpool_demand import (
    FIFTEEN_MIN_MS,
    FORWARD_BOUNDARY_MS,
    SpotKline,
    first_eligible_entry_open_ms,
    exact_exit_open_ms,
)


CODE1 = "a" * 32
CODE2 = "b" * 32
CODE3 = "c" * 32


class FakeDetailSource(BinanceOfficialLaunchpoolSource):
    def __init__(self, payloads):
        super().__init__(timeout=1)
        self.payloads = payloads

    def detail(self, article_code: str):
        obj = self.payloads[article_code]
        return obj, json.dumps(obj, sort_keys=True).encode("utf-8")


class StaticEligibleSource:
    provider = "BINANCE_SUPPORT_CMS_PUBLIC"

    def __init__(self, events):
        self.events = events

    def discover_eligible(self, *, now_ms: int):
        return list(self.events)


class FakeMarket:
    provider = "BINANCE_SPOT_DATA_API_PUBLIC"

    def exact_bar(self, open_ms: int, *, now_ms: int):
        if now_ms <= open_ms + FIFTEEN_MIN_MS:
            return None
        price = 0.01 if open_ms % (2 * FIFTEEN_MIN_MS) == 0 else 0.011
        return SpotKline(
            open_time=open_ms,
            open=price,
            high=price * 1.01,
            low=price * 0.99,
            close=price,
            volume=100.0,
            close_time=open_ms + FIFTEEN_MIN_MS - 1,
        )


class BNBLaunchpoolWatcherTests(TestCase):
    def test_catalog_candidate_extraction_is_launchpool_only(self) -> None:
        payload = {
            "data": {
                "articles": [
                    {"articleCode": CODE1, "title": "Introducing AAA on Binance Launchpool!"},
                    {"articleCode": CODE2, "title": "Binance Will List BBB"},
                ]
            }
        }
        self.assertEqual(_candidate_rows(payload), [(CODE1, "Introducing AAA on Binance Launchpool!")])

    def test_detail_requires_bnb_launchpool_utility_and_original_timestamp(self) -> None:
        published = FORWARD_BOUNDARY_MS + 123_000
        valid = {
            "data": {
                "articleCode": CODE1,
                "title": "Introducing AAA on Binance Launchpool!",
                "releaseDate": published,
                "body": "Users can farm AAA on Binance Launchpool by staking BNB in the BNB pool.",
            }
        }
        no_bnb = {
            "data": {
                "articleCode": CODE2,
                "title": "Introducing BBB on Binance Launchpool!",
                "releaseDate": published,
                "body": "Users can farm BBB by staking FDUSD only.",
            }
        }
        source = FakeDetailSource({CODE1: valid, CODE2: no_bnb})
        event = source.validate_detail(
            article_code=CODE1,
            fallback_title="x",
            now_ms=published + 1000,
        )
        self.assertIsNotNone(event)
        assert event is not None
        self.assertEqual(event.published_ms, published)
        self.assertIsNone(
            source.validate_detail(
                article_code=CODE2,
                fallback_title="y",
                now_ms=published + 1000,
            )
        )

    def test_adjacent_events_cluster_with_earliest_anchor(self) -> None:
        t0 = FORWARD_BOUNDARY_MS + 10_000
        events = [
            LaunchpoolAnnouncement(CODE1, "A Launchpool", t0, "a", "1" * 64),
            LaunchpoolAnnouncement(CODE2, "B Launchpool", t0 + 30 * 60_000, "b", "2" * 64),
            LaunchpoolAnnouncement(CODE3, "C Launchpool", t0 + 2 * 60 * 60_000, "c", "3" * 64),
        ]
        clusters = _cluster_announcements(events)
        self.assertEqual(len(clusters), 2)
        self.assertEqual([x.article_code for x in clusters[0]], [CODE1, CODE2])
        self.assertEqual(clusters[0][0].article_code, CODE1)

    def test_overlap_is_suppressed_and_replay_is_idempotent(self) -> None:
        t0 = FORWARD_BOUNDARY_MS + 10_000
        events = [
            LaunchpoolAnnouncement(CODE1, "A Launchpool", t0, "a", "1" * 64),
            LaunchpoolAnnouncement(CODE2, "B Launchpool", t0 + 30 * 60_000, "b", "2" * 64),
            LaunchpoolAnnouncement(CODE3, "C Launchpool", t0 + 2 * 60 * 60_000, "c", "3" * 64),
        ]
        entry = first_eligible_entry_open_ms(t0)
        now_ms = exact_exit_open_ms(entry) + 2 * FIFTEEN_MIN_MS

        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(str(Path(td) / "evidence.sqlite3"))
            watcher = BNBLaunchpoolForwardShadowWatcher(
                store=store,
                source=StaticEligibleSource(events),
                market=FakeMarket(),
            )
            # Seed the two cluster identities as if they had been observed prospectively
            # before their frozen entry opens. A later restart may then bind/resolve them.
            for cluster in _cluster_announcements(events):
                key = _cluster_key(cluster)
                store.append_once(
                    "BNB_FORWARD_ELIGIBLE_EVENT",
                    key,
                    {"event_key": key, "prospective_observation_seed": True},
                )
            first = watcher.run_once(now_ms=now_ms)
            second = watcher.run_once(now_ms=now_ms)

            self.assertEqual(first["clusters_visible"], 2)
            self.assertEqual(first["inserted_events"], 0)
            self.assertEqual(first["inserted_selections"], 1)
            self.assertEqual(first["inserted_resolutions"], 1)
            self.assertEqual(first["inserted_suppressions"], 1)
            self.assertEqual(second["inserted_events"], 0)
            self.assertEqual(second["inserted_selections"], 0)
            self.assertEqual(second["inserted_resolutions"], 0)
            self.assertEqual(second["inserted_suppressions"], 0)
            self.assertEqual(second["duplicate_events"], 2)
            self.assertEqual(second["duplicate_selections"], 1)
            self.assertEqual(second["duplicate_resolutions"], 1)
            self.assertEqual(second["duplicate_suppressions"], 1)
            self.assertEqual(first["missed_prospective_observation_count"], 0)
            ok, detail = store.verify_chain()
            self.assertTrue(ok, detail)

    def test_late_first_discovery_is_recorded_missed_and_never_backfilled(self) -> None:
        t0 = FORWARD_BOUNDARY_MS + 10_000
        event = LaunchpoolAnnouncement(CODE1, "A Launchpool", t0, "a", "1" * 64)
        entry = first_eligible_entry_open_ms(t0)
        now_ms = entry + FIFTEEN_MIN_MS

        with tempfile.TemporaryDirectory() as td:
            store = EvidenceStore(str(Path(td) / "evidence.sqlite3"))
            watcher = BNBLaunchpoolForwardShadowWatcher(
                store=store,
                source=StaticEligibleSource([event]),
                market=FakeMarket(),
            )
            first = watcher.run_once(now_ms=now_ms)
            second = watcher.run_once(now_ms=now_ms)

            self.assertEqual(first["inserted_events"], 0)
            self.assertEqual(first["inserted_selections"], 0)
            self.assertEqual(first["inserted_resolutions"], 0)
            self.assertEqual(first["inserted_missed_observations"], 1)
            self.assertEqual(first["missed_prospective_observation_count"], 1)
            self.assertEqual(second["duplicate_missed_observations"], 1)
            rows = store.read_payloads(MISSED_PROSPECTIVE_EVENT)
            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0]["late_reconstruction_forbidden"])
            self.assertFalse(rows[0]["used_as_forward_trade_evidence"])


if __name__ == "__main__":
    import unittest

    unittest.main()

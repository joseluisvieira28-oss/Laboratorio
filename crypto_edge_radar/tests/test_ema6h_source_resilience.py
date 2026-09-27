from __future__ import annotations

import unittest

from radar.ema6h_source_resilience import (
    ResilientBinanceSpotKlineFeed,
    is_retryable_binance_transport_error,
)
from radar.strategies.ema6h_50x200_regime_forward import (
    Candle,
    EMA6HRegimeSourceError,
)


ROW = Candle(
    open_time=1_795_219_200_000,
    open=100.0,
    high=101.0,
    low=99.0,
    close=100.5,
    volume=10.0,
    close_time=1_795_220_099_999,
)


class FakeFeed:
    behaviors = {}
    calls = []

    def __init__(self, timeout=10, *, max_attempts=1, retry_backoff_seconds=0):
        self.base_url = ""
        self.timeout = timeout

    def klines(self, symbol, interval, *, start_ms, end_ms, now_ms):
        FakeFeed.calls.append(self.base_url)
        behavior = FakeFeed.behaviors[self.base_url]
        if isinstance(behavior, Exception):
            raise behavior
        return list(behavior)


class EMA6HSourceResilienceTests(unittest.TestCase):
    def setUp(self):
        FakeFeed.calls = []
        FakeFeed.behaviors = {}

    def feed(self, endpoints):
        return ResilientBinanceSpotKlineFeed(
            endpoints=endpoints,
            base_feed_cls=FakeFeed,
            cooldown_seconds=3600,
            monotonic=lambda: 1000.0,
        )

    def test_primary_transport_passes_without_fallback(self):
        endpoints = (("PRIMARY_DATA", "https://a"), ("FALLBACK", "https://b"))
        FakeFeed.behaviors = {"https://a": [ROW], "https://b": [ROW]}
        feed = self.feed(endpoints)

        rows = feed.klines(
            "BTCUSDT",
            "15m",
            start_ms=ROW.open_time,
            end_ms=ROW.open_time + 900_000,
            now_ms=ROW.close_time + 1,
        )

        self.assertEqual(rows, [ROW])
        self.assertEqual(FakeFeed.calls, ["https://a"])
        receipt = feed.transport_receipt()
        self.assertEqual(receipt["classification"], "PRIMARY_TRANSPORT_PASS")
        self.assertFalse(receipt["fallback_used"])
        self.assertFalse(receipt["science_changed"])

    def test_418_rotates_to_official_fallback(self):
        endpoints = (("PRIMARY_DATA", "https://a"), ("GCP", "https://b"))
        FakeFeed.behaviors = {
            "https://a": EMA6HRegimeSourceError(
                "Binance source unavailable: HTTPError: HTTP Error 418: I'm a teapot"
            ),
            "https://b": [ROW],
        }
        feed = self.feed(endpoints)

        rows = feed.klines(
            "BTCUSDT",
            "15m",
            start_ms=ROW.open_time,
            end_ms=ROW.open_time + 900_000,
            now_ms=ROW.close_time + 1,
        )

        self.assertEqual(rows, [ROW])
        self.assertEqual(FakeFeed.calls, ["https://a", "https://b"])
        receipt = feed.transport_receipt()
        self.assertEqual(
            receipt["classification"],
            "OFFICIAL_FALLBACK_TRANSPORT_PASS",
        )
        self.assertEqual(receipt["selected_endpoint"], "GCP")
        self.assertTrue(receipt["fallback_used"])
        self.assertEqual(receipt["retryable_failures"][0]["endpoint"], "PRIMARY_DATA")

    def test_successful_fallback_becomes_preferred_and_blocked_primary_is_skipped(self):
        endpoints = (("PRIMARY_DATA", "https://a"), ("GCP", "https://b"))
        FakeFeed.behaviors = {
            "https://a": EMA6HRegimeSourceError("HTTP Error 429"),
            "https://b": [ROW],
        }
        feed = self.feed(endpoints)

        kwargs = dict(
            symbol="BTCUSDT",
            interval="15m",
            start_ms=ROW.open_time,
            end_ms=ROW.open_time + 900_000,
            now_ms=ROW.close_time + 1,
        )
        feed.klines(**kwargs)
        FakeFeed.calls = []
        feed.klines(**kwargs)

        self.assertEqual(FakeFeed.calls, ["https://b"])

    def test_semantic_validation_error_does_not_fallback(self):
        endpoints = (("PRIMARY_DATA", "https://a"), ("GCP", "https://b"))
        FakeFeed.behaviors = {
            "https://a": EMA6HRegimeSourceError("Binance timestamp/alignment violation"),
            "https://b": [ROW],
        }
        feed = self.feed(endpoints)

        with self.assertRaisesRegex(
            EMA6HRegimeSourceError,
            "timestamp/alignment",
        ):
            feed.klines(
                "BTCUSDT",
                "15m",
                start_ms=ROW.open_time,
                end_ms=ROW.open_time + 900_000,
                now_ms=ROW.close_time + 1,
            )

        self.assertEqual(FakeFeed.calls, ["https://a"])
        self.assertEqual(
            feed.transport_receipt()["classification"],
            "FAIL_CLOSED_SEMANTIC_SOURCE_ERROR",
        )

    def test_all_official_endpoints_unavailable_fails_closed(self):
        endpoints = (("PRIMARY_DATA", "https://a"), ("GCP", "https://b"))
        FakeFeed.behaviors = {
            "https://a": EMA6HRegimeSourceError("HTTP Error 418"),
            "https://b": EMA6HRegimeSourceError("HTTP Error 429"),
        }
        feed = self.feed(endpoints)

        with self.assertRaisesRegex(
            EMA6HRegimeSourceError,
            "all official Binance Spot endpoints unavailable",
        ):
            feed.klines(
                "BTCUSDT",
                "15m",
                start_ms=ROW.open_time,
                end_ms=ROW.open_time + 900_000,
                now_ms=ROW.close_time + 1,
            )

        self.assertEqual(
            feed.transport_receipt()["classification"],
            "ALL_OFFICIAL_ENDPOINTS_UNAVAILABLE_FAIL_CLOSED",
        )

    def test_only_transport_errors_are_retryable(self):
        self.assertTrue(is_retryable_binance_transport_error("HTTP Error 418"))
        self.assertTrue(is_retryable_binance_transport_error("HTTP Error 429"))
        self.assertTrue(is_retryable_binance_transport_error("HTTP Error 503"))
        self.assertFalse(
            is_retryable_binance_transport_error(
                "Binance timestamp/alignment violation"
            )
        )


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest

from radar.ema6h_source_resilience import (
    BinanceSpotWebSocketKlineFeed,
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


class FakeRestFeed:
    behaviors = {}
    calls = []

    def __init__(self, timeout=10, *, max_attempts=1, retry_backoff_seconds=0):
        self.base_url = ""
        self.timeout = timeout

    def klines(self, symbol, interval, *, start_ms, end_ms, now_ms):
        FakeRestFeed.calls.append(self.base_url)
        behavior = FakeRestFeed.behaviors[self.base_url]
        if isinstance(behavior, Exception):
            raise behavior
        return list(behavior)


class FakeWsFeed:
    behaviors = {}
    calls = []

    def __init__(self, timeout=10):
        self.endpoint_url = ""
        self.timeout = timeout

    def klines(self, symbol, interval, *, start_ms, end_ms, now_ms):
        FakeWsFeed.calls.append(self.endpoint_url)
        behavior = FakeWsFeed.behaviors[self.endpoint_url]
        if isinstance(behavior, Exception):
            raise behavior
        return list(behavior)


class FakeConnection:
    def __init__(self, responses):
        self.responses = list(responses)
        self.sent = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def send(self, raw):
        self.sent.append(json.loads(raw))

    def recv(self, timeout=None):
        return json.dumps(self.responses.pop(0))


class EMA6HSourceResilienceTests(unittest.TestCase):
    def setUp(self):
        FakeRestFeed.calls = []
        FakeRestFeed.behaviors = {}
        FakeWsFeed.calls = []
        FakeWsFeed.behaviors = {}

    def feed(self, transports):
        return ResilientBinanceSpotKlineFeed(
            transports=transports,
            rest_feed_cls=FakeRestFeed,
            ws_feed_cls=FakeWsFeed,
            cooldown_seconds=3600,
            monotonic=lambda: 1000.0,
        )

    def test_primary_rest_transport_passes_without_fallback(self):
        transports = (
            ("MARKET_DATA_ONLY", "REST", "https://a"),
            ("WS_API", "WEBSOCKET_API", "wss://b"),
        )
        FakeRestFeed.behaviors = {"https://a": [ROW]}
        FakeWsFeed.behaviors = {"wss://b": [ROW]}
        feed = self.feed(transports)

        rows = feed.klines(
            "BTCUSDT",
            "15m",
            start_ms=ROW.open_time,
            end_ms=ROW.open_time + 900_000,
            now_ms=ROW.close_time + 1,
        )

        self.assertEqual(rows, [ROW])
        self.assertEqual(FakeRestFeed.calls, ["https://a"])
        self.assertEqual(FakeWsFeed.calls, [])
        receipt = feed.transport_receipt()
        self.assertEqual(receipt["classification"], "PRIMARY_TRANSPORT_PASS")
        self.assertFalse(receipt["fallback_used"])
        self.assertFalse(receipt["science_changed"])

    def test_418_rest_rotates_to_official_websocket_api(self):
        transports = (
            ("MARKET_DATA_ONLY", "REST", "https://a"),
            ("WS_API", "WEBSOCKET_API", "wss://b"),
        )
        FakeRestFeed.behaviors = {
            "https://a": EMA6HRegimeSourceError(
                "Binance source unavailable: HTTPError: HTTP Error 418: I'm a teapot"
            ),
        }
        FakeWsFeed.behaviors = {"wss://b": [ROW]}
        feed = self.feed(transports)

        rows = feed.klines(
            "BTCUSDT",
            "15m",
            start_ms=ROW.open_time,
            end_ms=ROW.open_time + 900_000,
            now_ms=ROW.close_time + 1,
        )

        self.assertEqual(rows, [ROW])
        self.assertEqual(FakeRestFeed.calls, ["https://a"])
        self.assertEqual(FakeWsFeed.calls, ["wss://b"])
        receipt = feed.transport_receipt()
        self.assertEqual(
            receipt["classification"],
            "OFFICIAL_FALLBACK_TRANSPORT_PASS",
        )
        self.assertEqual(receipt["selected_transport"], "WS_API")
        self.assertEqual(receipt["selected_kind"], "WEBSOCKET_API")
        self.assertTrue(receipt["fallback_used"])
        self.assertEqual(
            receipt["retryable_failures"][0]["transport"],
            "MARKET_DATA_ONLY",
        )

    def test_successful_ws_fallback_becomes_preferred(self):
        transports = (
            ("MARKET_DATA_ONLY", "REST", "https://a"),
            ("WS_API", "WEBSOCKET_API", "wss://b"),
        )
        FakeRestFeed.behaviors = {
            "https://a": EMA6HRegimeSourceError("HTTP Error 429"),
        }
        FakeWsFeed.behaviors = {"wss://b": [ROW]}
        feed = self.feed(transports)

        kwargs = dict(
            symbol="BTCUSDT",
            interval="15m",
            start_ms=ROW.open_time,
            end_ms=ROW.open_time + 900_000,
            now_ms=ROW.close_time + 1,
        )
        feed.klines(**kwargs)
        FakeRestFeed.calls = []
        FakeWsFeed.calls = []
        feed.klines(**kwargs)

        self.assertEqual(FakeRestFeed.calls, [])
        self.assertEqual(FakeWsFeed.calls, ["wss://b"])

    def test_semantic_validation_error_does_not_fallback(self):
        transports = (
            ("MARKET_DATA_ONLY", "REST", "https://a"),
            ("WS_API", "WEBSOCKET_API", "wss://b"),
        )
        FakeRestFeed.behaviors = {
            "https://a": EMA6HRegimeSourceError(
                "Binance timestamp/alignment violation"
            ),
        }
        FakeWsFeed.behaviors = {"wss://b": [ROW]}
        feed = self.feed(transports)

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

        self.assertEqual(FakeRestFeed.calls, ["https://a"])
        self.assertEqual(FakeWsFeed.calls, [])
        self.assertEqual(
            feed.transport_receipt()["classification"],
            "FAIL_CLOSED_SEMANTIC_SOURCE_ERROR",
        )

    def test_all_official_transports_unavailable_fails_closed(self):
        transports = (
            ("MARKET_DATA_ONLY", "REST", "https://a"),
            ("WS_API", "WEBSOCKET_API", "wss://b"),
        )
        FakeRestFeed.behaviors = {
            "https://a": EMA6HRegimeSourceError("HTTP Error 418"),
        }
        FakeWsFeed.behaviors = {
            "wss://b": EMA6HRegimeSourceError(
                "Binance WebSocket transport unavailable: InvalidStatus: HTTP 451"
            ),
        }
        feed = self.feed(transports)

        with self.assertRaisesRegex(
            EMA6HRegimeSourceError,
            "all official Binance transports unavailable",
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
            "ALL_OFFICIAL_TRANSPORTS_UNAVAILABLE_FAIL_CLOSED",
        )

    def test_only_transport_errors_are_retryable(self):
        self.assertTrue(is_retryable_binance_transport_error("HTTP Error 418"))
        self.assertTrue(is_retryable_binance_transport_error("HTTP Error 429"))
        self.assertTrue(is_retryable_binance_transport_error("HTTP Error 451"))
        self.assertTrue(
            is_retryable_binance_transport_error(
                "Binance WebSocket transport unavailable: InvalidStatus"
            )
        )
        self.assertFalse(
            is_retryable_binance_transport_error(
                "Binance timestamp/alignment violation"
            )
        )

    def test_websocket_feed_uses_frozen_parser_and_public_klines_method(self):
        raw_row = [
            ROW.open_time,
            "100.0",
            "101.0",
            "99.0",
            "100.5",
            "10.0",
            ROW.close_time,
            "1005.0",
            100,
            "5.0",
            "502.5",
            "0",
        ]
        connection = FakeConnection(
            [
                {
                    "id": "ema6h-1",
                    "status": 200,
                    "result": [raw_row],
                    "rateLimits": [],
                }
            ]
        )
        feed = BinanceSpotWebSocketKlineFeed(
            timeout=3,
            connect_fn=lambda *_args, **_kwargs: connection,
        )

        rows = feed.klines(
            "BTCUSDT",
            "15m",
            start_ms=ROW.open_time,
            end_ms=ROW.open_time + 900_000,
            now_ms=ROW.close_time + 1,
        )

        self.assertEqual(rows, [ROW])
        self.assertEqual(len(connection.sent), 1)
        req = connection.sent[0]
        self.assertEqual(req["method"], "klines")
        self.assertEqual(req["params"]["symbol"], "BTCUSDT")
        self.assertEqual(req["params"]["interval"], "15m")
        self.assertNotIn("apiKey", req["params"])
        self.assertNotIn("signature", req["params"])

    def test_websocket_semantic_bad_row_fails_closed(self):
        bad_row = [
            ROW.open_time + 1,
            "100.0",
            "101.0",
            "99.0",
            "100.5",
            "10.0",
            ROW.close_time,
        ]
        connection = FakeConnection(
            [
                {
                    "id": "ema6h-1",
                    "status": 200,
                    "result": [bad_row],
                    "rateLimits": [],
                }
            ]
        )
        feed = BinanceSpotWebSocketKlineFeed(
            connect_fn=lambda *_args, **_kwargs: connection,
        )

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


if __name__ == "__main__":
    unittest.main()

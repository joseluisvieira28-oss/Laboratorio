from __future__ import annotations

import io
import json
import unittest
from urllib.error import HTTPError

from radar.binance_source_resilience import (
    BinanceOfficialKlineTransport,
    BinancePublicSourceUnavailable,
    canonical_kline_sha256,
)


ROWS = [
    [
        1790467200000,
        "109000.00000000",
        "110000.00000000",
        "108500.00000000",
        "109500.00000000",
        "123.45000000",
        1790468099999,
        "0",
        1,
        "0",
        "0",
        "0",
    ]
]


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode("utf-8")


def host_from_request(req):
    return req.full_url.split("/api/v3/klines", 1)[0]


class BinanceSourceResilienceTests(unittest.TestCase):
    def test_418_primary_falls_back_to_next_official_host(self):
        calls = []

        def opener(req, timeout):
            host = host_from_request(req)
            calls.append(host)
            if host == "https://data-api.binance.vision":
                raise HTTPError(req.full_url, 418, "teapot", {}, io.BytesIO())
            return FakeResponse(ROWS)

        transport = BinanceOfficialKlineTransport(
            base_urls=(
                "https://data-api.binance.vision",
                "https://api.binance.com",
            ),
            opener=opener,
        )
        payload = transport.get_klines(
            {"symbol": "BTCUSDT", "interval": "15m", "limit": 1}
        )
        self.assertEqual(payload, ROWS)
        self.assertEqual(
            transport.last_success_base_url,
            "https://api.binance.com",
        )
        self.assertEqual(
            calls,
            [
                "https://data-api.binance.vision",
                "https://api.binance.com",
            ],
        )

    def test_equivalence_probe_passes_only_on_matching_science_fields(self):
        def opener(req, timeout):
            return FakeResponse(ROWS)

        transport = BinanceOfficialKlineTransport(
            base_urls=(
                "https://data-api.binance.vision",
                "https://api.binance.com",
                "https://api-gcp.binance.com",
            ),
            opener=opener,
        )
        result = transport.equivalence_probe(
            {"symbol": "BTCUSDT", "interval": "15m", "limit": 1}
        )
        self.assertTrue(result["pass"])
        self.assertEqual(
            result["classification"],
            "PASS_OFFICIAL_HOST_KLINE_EQUIVALENCE",
        )
        self.assertEqual(result["successful_hosts"], 3)
        self.assertEqual(result["matching_sha256"], canonical_kline_sha256(ROWS))

    def test_equivalence_probe_fails_closed_on_divergent_ohlcv(self):
        divergent = [list(ROWS[0])]
        divergent[0][4] = "109501.00000000"

        def opener(req, timeout):
            if host_from_request(req) == "https://api.binance.com":
                return FakeResponse(divergent)
            return FakeResponse(ROWS)

        transport = BinanceOfficialKlineTransport(
            base_urls=(
                "https://data-api.binance.vision",
                "https://api.binance.com",
            ),
            opener=opener,
        )
        result = transport.equivalence_probe(
            {"symbol": "BTCUSDT", "interval": "15m", "limit": 1}
        )
        self.assertFalse(result["pass"])
        self.assertEqual(
            result["classification"],
            "FAIL_CLOSED_OFFICIAL_HOST_DIVERGENCE",
        )

    def test_all_hosts_unavailable_is_fail_closed(self):
        def opener(req, timeout):
            raise HTTPError(req.full_url, 429, "rate limit", {}, io.BytesIO())

        transport = BinanceOfficialKlineTransport(
            base_urls=(
                "https://data-api.binance.vision",
                "https://api.binance.com",
            ),
            opener=opener,
        )
        with self.assertRaises(BinancePublicSourceUnavailable):
            transport.get_klines(
                {"symbol": "BTCUSDT", "interval": "15m", "limit": 1}
            )
        self.assertEqual(len(transport.last_observations), 2)

    def test_hash_ignores_fields_not_consumed_by_frozen_ema6h_science(self):
        a = [list(ROWS[0])]
        b = [list(ROWS[0])]
        b[0][7] = "999999"
        b[0][8] = 999
        self.assertEqual(canonical_kline_sha256(a), canonical_kline_sha256(b))


if __name__ == "__main__":
    unittest.main()

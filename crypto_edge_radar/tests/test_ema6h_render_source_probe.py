from __future__ import annotations

import unittest
from unittest.mock import patch

from radar import ema6h_render_source_probe as probe
from radar.strategies.ema6h_50x200_regime_forward import Candle


ROW = Candle(
    open_time=1790380800000,
    open=100.0,
    high=101.0,
    low=99.0,
    close=100.5,
    volume=10.0,
    close_time=1790381699999,
)


class FakeFeed:
    behavior = {}

    def __init__(self, timeout=5, *, max_attempts=1, retry_backoff_seconds=0):
        self.base_url = ""

    def klines(self, *args, **kwargs):
        value = self.behavior[self.base_url]
        if isinstance(value, Exception):
            raise value
        return list(value)


class EMA6HRenderSourceProbeTests(unittest.TestCase):
    def test_two_matching_hosts_pass(self):
        FakeFeed.behavior = {
            "https://a": [ROW],
            "https://b": [ROW],
        }
        with patch.object(probe, "BinanceSpotKlineFeed", FakeFeed):
            result = probe.probe_official_binance_hosts(
                endpoints=(("A", "https://a"), ("B", "https://b"))
            )
        self.assertEqual(result["classification"], "PASS_EXACT_MULTI_HOST_EQUIVALENCE")
        self.assertTrue(result["equivalent_multi_host"])
        self.assertFalse(result["automatic_source_switch"])

    def test_single_host_is_observation_not_pass(self):
        FakeFeed.behavior = {
            "https://a": [ROW],
            "https://b": RuntimeError("451"),
        }
        with patch.object(probe, "BinanceSpotKlineFeed", FakeFeed):
            result = probe.probe_official_binance_hosts(
                endpoints=(("A", "https://a"), ("B", "https://b"))
            )
        self.assertEqual(result["classification"], "SINGLE_ACCESSIBLE_HOST_ONLY")
        self.assertFalse(result["equivalent_multi_host"])

    def test_divergence_fails_closed(self):
        other = Candle(
            open_time=ROW.open_time,
            open=ROW.open,
            high=ROW.high,
            low=ROW.low,
            close=101.5,
            volume=ROW.volume,
            close_time=ROW.close_time,
        )
        FakeFeed.behavior = {
            "https://a": [ROW],
            "https://b": [other],
        }
        with patch.object(probe, "BinanceSpotKlineFeed", FakeFeed):
            result = probe.probe_official_binance_hosts(
                endpoints=(("A", "https://a"), ("B", "https://b"))
            )
        self.assertEqual(result["classification"], "FAIL_CLOSED_MULTI_HOST_DIVERGENCE")
        self.assertFalse(result["equivalent_multi_host"])


if __name__ == "__main__":
    unittest.main()

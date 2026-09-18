import unittest
from unittest.mock import patch

from radar.bnb_launchpool_watcher import BinanceOfficialLaunchpoolSource, BNBLaunchpoolSourceError
from radar.forward_web import CachingBinanceOfficialLaunchpoolSource


class BNBRateLimitCacheTests(unittest.TestCase):
    def test_catalog_ttl_prevents_repeated_live_calls(self):
        src=CachingBinanceOfficialLaunchpoolSource()
        live=({"data":"x"},b"raw")
        with patch.object(BinanceOfficialLaunchpoolSource,"catalog",return_value=live) as base:
            with patch("radar.forward_web.time.monotonic",side_effect=[100.0,200.0]):
                self.assertEqual(src.catalog(),live)
                self.assertEqual(src.catalog(),live)
        self.assertEqual(base.call_count,1)
        self.assertEqual(src.catalog_status,"CACHE_FRESH")

    def test_429_uses_explicit_stale_cache_and_backoff(self):
        src=CachingBinanceOfficialLaunchpoolSource()
        live=({"data":"x"},b"raw")
        with patch.object(
            BinanceOfficialLaunchpoolSource,
            "catalog",
            side_effect=[live, BNBLaunchpoolSourceError("Binance CMS source unavailable:HTTPError:HTTP Error 429: Too Many Requests")],
        ) as base:
            with patch("radar.forward_web.time.monotonic",side_effect=[100.0,701.0,702.0]):
                self.assertEqual(src.catalog(),live)
                self.assertEqual(src.catalog(),live)
                self.assertEqual(src.catalog_status,"CACHE_BACKOFF_STALE")
                self.assertEqual(src.catalog(),live)
                self.assertEqual(src.catalog_status,"CACHE_BACKOFF_STALE")
        self.assertEqual(base.call_count,2)
        self.assertGreater(src._catalog_backoff_until,702.0)

    def test_429_without_prior_cache_fails_closed(self):
        src=CachingBinanceOfficialLaunchpoolSource()
        with patch.object(
            BinanceOfficialLaunchpoolSource,
            "catalog",
            side_effect=BNBLaunchpoolSourceError("HTTP 429"),
        ):
            with self.assertRaises(BNBLaunchpoolSourceError):
                src.catalog()


if __name__=="__main__":
    unittest.main()

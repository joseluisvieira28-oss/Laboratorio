import unittest

from radar.market import BinancePublicFeed, BinanceSpotPublicFeed, MarketDataError


class MarketSafetyTests(unittest.TestCase):
    def test_usdm_order_path_is_blocked_before_network(self):
        feed = BinancePublicFeed()
        with self.assertRaises(MarketDataError):
            feed._get_json("/fapi/v1/order")

    def test_usdm_account_path_is_blocked_before_network(self):
        feed = BinancePublicFeed()
        with self.assertRaises(MarketDataError):
            feed._get_json("/fapi/v2/account")

    def test_spot_order_path_is_blocked_before_network(self):
        feed = BinanceSpotPublicFeed()
        with self.assertRaises(MarketDataError):
            feed._get_json("/api/v3/order")

    def test_spot_account_path_is_blocked_before_network(self):
        feed = BinanceSpotPublicFeed()
        with self.assertRaises(MarketDataError):
            feed._get_json("/api/v3/account")


if __name__ == "__main__":
    unittest.main()

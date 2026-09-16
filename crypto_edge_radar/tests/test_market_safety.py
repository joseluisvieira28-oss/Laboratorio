import unittest

from radar.market import BinancePublicFeed, MarketDataError


class MarketSafetyTests(unittest.TestCase):
    def test_order_path_is_blocked_before_network(self):
        feed = BinancePublicFeed()
        with self.assertRaises(MarketDataError):
            feed._get_json("/fapi/v1/order")

    def test_account_path_is_blocked_before_network(self):
        feed = BinancePublicFeed()
        with self.assertRaises(MarketDataError):
            feed._get_json("/fapi/v2/account")


if __name__ == "__main__":
    unittest.main()

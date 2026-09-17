import unittest

from radar.market import MEXCFuturesPublicFeed
from radar.mexc_spot import MEXCSpotPublicFeed, MEXCSpotPublicError
from radar.models import MarketSnapshot
from radar.spot_mapping import spot_perp_mapping_receipt


class StubSpot(MEXCSpotPublicFeed):
    def default_symbols(self):
        return {"BTCUSDT", "ETHUSDT"}

    def book_ticker(self, symbol):
        self._validate_symbol(symbol)
        return {"symbol": symbol, "bidPrice": "99.9", "askPrice": "100.1"}

    def price(self, symbol):
        self._validate_symbol(symbol)
        return 100.0

    def depth(self, symbol, limit=20):
        self._validate_symbol(symbol)
        return {"bids": [["99.9", "2"]], "asks": [["100.1", "2"]]}


class UnsupportedSpot(StubSpot):
    def default_symbols(self):
        return {"ETHUSDT"}


class StubFutures(MEXCFuturesPublicFeed):
    def all_market_snapshots(self):
        return {
            "BTCUSDT": MarketSnapshot(
                symbol="BTCUSDT",
                observed_at="2026-09-17T19:00:00Z",
                last_price=100.2,
                bid_price=100.15,
                ask_price=100.25,
                quote_volume_24h=1_000_000.0,
            )
        }


class SpotMappingTests(unittest.TestCase):
    def test_public_mapping_never_enables_capital(self):
        receipt = spot_perp_mapping_receipt(spot=StubSpot(), futures=StubFutures())
        self.assertFalse(receipt["capital_enabled"])
        self.assertFalse(receipt["orders_created"])
        self.assertFalse(receipt["authenticated_api_used"])
        self.assertEqual(receipt["long_mapping_candidate"]["funding_cost"], "NONE_FOR_UNLEVERED_SPOT_HOLD")
        self.assertEqual(receipt["gates"]["capital"], "BLOCKED")

    def test_basis_and_spread_are_observations_not_signal_changes(self):
        receipt = spot_perp_mapping_receipt(spot=StubSpot(), futures=StubFutures())
        self.assertAlmostEqual(receipt["long_mapping_candidate"]["spread_bps"], 20.0)
        self.assertAlmostEqual(receipt["cross_market"]["perp_minus_spot_mid_bps"], 20.0)
        self.assertIn("not a return forecast", receipt["cross_market"]["note"])

    def test_missing_btc_spot_support_fails_closed(self):
        with self.assertRaises(MEXCSpotPublicError):
            spot_perp_mapping_receipt(spot=UnsupportedSpot(), futures=StubFutures())


if __name__ == "__main__":
    unittest.main()

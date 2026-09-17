import unittest

from radar.friction import mexc_friction_shadow_receipt
from radar.market import MEXCFuturesPublicFeed
from radar.models import MarketSnapshot


class StubFrictionFeed(MEXCFuturesPublicFeed):
    def __init__(self):
        super().__init__(timeout=1)

    def server_time_ms(self):
        return 1_800_000_000_000

    def all_market_snapshots(self):
        return {
            "BTCUSDT": MarketSnapshot(
                symbol="BTCUSDT",
                observed_at="2026-09-17T16:00:00Z",
                last_price=100.0,
                bid_price=99.9,
                ask_price=100.1,
                quote_volume_24h=1_000_000.0,
            )
        }

    def contract_row(self, symbol):
        self._validate_contract_symbol(symbol)
        return {
            "symbol": "BTC_USDT",
            "apiAllowed": True,
            "futureType": 1,
            "state": 0,
            "contractSize": 0.0001,
            "minVol": 1,
            "volUnit": 1,
            "positionOpenType": 3,
        }

    def order_book_depth(self, symbol, limit=20):
        self._validate_contract_symbol(symbol)
        return {
            "bids": [[99.9, 10, 5]],
            "asks": [[100.1, 10, 5]],
            "timestamp": 1_800_000_000_000,
        }

    def funding_rate(self, symbol):
        self._validate_contract_symbol(symbol)
        return {
            "fundingRate": 0.0001,
            "collectCycle": 8,
            "nextSettleTime": 1_800_000_100_000,
            "idxPrice": 100.0,
            "fairPrice": 100.05,
        }

    def recent_trades(self, symbol, limit=100):
        self._validate_contract_symbol(symbol)
        return [{"p": 100.0, "v": 1, "T": 1, "t": 1_800_000_000_000}]


class FrictionShadowTests(unittest.TestCase):
    def test_public_receipt_never_enables_capital_or_orders(self):
        receipt = mexc_friction_shadow_receipt(feed=StubFrictionFeed())
        self.assertEqual(receipt["receipt_type"], "MEXC_FRICTION_SHADOW_V1")
        self.assertFalse(receipt["capital_enabled"])
        self.assertFalse(receipt["orders_created"])
        self.assertEqual(receipt["contract"]["api_allowed"], True)

    def test_fee_and_spread_budget_is_explicit(self):
        receipt = mexc_friction_shadow_receipt(feed=StubFrictionFeed())
        self.assertAlmostEqual(receipt["fees"]["taker_round_trip_bps"], 16.0)
        self.assertAlmostEqual(receipt["top_of_book"]["spread_bps"], 20.0)
        self.assertAlmostEqual(
            receipt["edge_budget"]["same_book_taker_round_trip_proxy_bps"], 36.0
        )
        self.assertAlmostEqual(
            receipt["edge_budget"]["headroom_after_fee_plus_current_spread_proxy_bps"],
            -14.8,
        )

    def test_funding_projection_is_scenario_only(self):
        receipt = mexc_friction_shadow_receipt(feed=StubFrictionFeed())
        funding = receipt["funding_and_basis"]
        self.assertEqual(funding["collect_cycle_hours"], 8)
        self.assertAlmostEqual(
            funding["constant_current_rate_7d_absolute_magnitude_bps_scenario"],
            21.0,
        )
        self.assertIn("Not a forecast", funding["scenario_warning"])


if __name__ == "__main__":
    unittest.main()

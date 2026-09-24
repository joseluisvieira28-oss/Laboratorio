import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from source_adapters import (
    binance_depth_sequence_ok,
    coinbase_sequence_transition,
    parse_binance_aggtrade,
    parse_binance_depth_update,
    parse_coinbase_level2_update,
    parse_coinbase_market_trade,
)


class SourceAdapterTests(unittest.TestCase):
    def test_binance_buyer_maker_means_sell_aggressor(self):
        row = parse_binance_aggtrade({
            "e": "aggTrade",
            "E": 1672515782136,
            "s": "BTCUSDT",
            "a": 12345,
            "p": "100.0",
            "q": "2.0",
            "T": 1672515782100,
            "m": True,
        })
        self.assertEqual(row.aggressor_side, "SELL")
        self.assertEqual(row.quote_notional, Decimal("200.00"))

    def test_binance_buyer_taker_means_buy_aggressor(self):
        row = parse_binance_aggtrade({
            "e": "aggTrade",
            "E": 1672515782136,
            "s": "BTCUSDT",
            "a": 12346,
            "p": "100",
            "q": "1",
            "T": 1672515782101,
            "m": False,
        })
        self.assertEqual(row.aggressor_side, "BUY")

    def test_coinbase_side_is_maker_side_and_must_be_inverted(self):
        sell_aggressor = parse_coinbase_market_trade({
            "trade_id": "1",
            "product_id": "BTC-USD",
            "price": "100",
            "size": "2",
            "side": "BUY",
            "time": "2026-01-01T00:00:00Z",
        })
        buy_aggressor = parse_coinbase_market_trade({
            "trade_id": "2",
            "product_id": "BTC-USD",
            "price": "100",
            "size": "2",
            "side": "SELL",
            "time": "2026-01-01T00:00:01Z",
        })
        self.assertEqual(sell_aggressor.aggressor_side, "SELL")
        self.assertEqual(buy_aggressor.aggressor_side, "BUY")

    def test_binance_depth_quantities_are_absolute_and_zero_is_valid(self):
        rows = parse_binance_depth_update({
            "e": "depthUpdate",
            "E": 1672515782136,
            "s": "BTCUSDT",
            "U": 157,
            "u": 160,
            "b": [["100", "2"], ["99", "0"]],
            "a": [["101", "3"]],
        })
        self.assertEqual(len(rows), 3)
        self.assertEqual(rows[1].absolute_quantity, Decimal("0"))

    def test_coinbase_level2_absolute_quantity(self):
        row = parse_coinbase_level2_update(
            product_id="BTC-USD",
            sequence_num=42,
            update={
                "side": "bid",
                "event_time": "2026-01-01T00:00:00.123Z",
                "price_level": "100",
                "new_quantity": "0",
            },
        )
        self.assertEqual(row.side, "BID")
        self.assertEqual(row.absolute_quantity, Decimal("0"))
        self.assertEqual(row.sequence_first, 42)

    def test_binance_sequence_gap_detection(self):
        self.assertTrue(binance_depth_sequence_ok(156, 157, 160))
        self.assertTrue(binance_depth_sequence_ok(160, 159, 160))
        self.assertFalse(binance_depth_sequence_ok(160, 162, 163))

    def test_coinbase_sequence_transition(self):
        self.assertEqual(coinbase_sequence_transition(10, 11), "OK")
        self.assertEqual(coinbase_sequence_transition(10, 13), "GAP")
        self.assertEqual(
            coinbase_sequence_transition(10, 10),
            "OUT_OF_ORDER_OR_DUPLICATE",
        )

    def test_invalid_ambiguous_side_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_coinbase_market_trade({
                "trade_id": "3",
                "product_id": "BTC-USD",
                "price": "100",
                "size": "2",
                "side": "UNKNOWN",
                "time": "2026-01-01T00:00:00Z",
            })


if __name__ == "__main__":
    unittest.main()

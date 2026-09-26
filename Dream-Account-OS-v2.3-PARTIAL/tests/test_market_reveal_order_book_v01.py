import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from order_book import (
    BookSequenceGap,
    CrossedBook,
    DepthSpec,
    LocalOrderBook,
)
from source_adapters import CanonicalBookUpdate


def upd(
    *,
    venue="BINANCE_SPOT",
    symbol="BTCUSDT",
    first=11,
    last=11,
    side,
    price,
    qty,
):
    return CanonicalBookUpdate(
        venue=venue,
        native_symbol=symbol,
        source_event_time="0",
        sequence_first=first,
        sequence_last=last,
        side=side,
        price_level=Decimal(str(price)),
        absolute_quantity=Decimal(str(qty)),
    )


class LocalOrderBookTests(unittest.TestCase):
    def setUp(self):
        self.book = LocalOrderBook(
            venue="BINANCE_SPOT",
            native_symbol="BTCUSDT",
        )
        self.book.load_snapshot_levels(
            bids=[
                (Decimal("99"), Decimal("2")),
                (Decimal("98"), Decimal("1")),
            ],
            asks=[
                (Decimal("101"), Decimal("3")),
                (Decimal("102"), Decimal("1")),
            ],
            sequence_last=10,
        )

    def test_bbo_spread_mid_and_top_n_depth(self):
        m = self.book.metrics(DepthSpec("TOP_N", Decimal("1")))
        self.assertEqual(m.best_bid, Decimal("99"))
        self.assertEqual(m.best_ask, Decimal("101"))
        self.assertEqual(m.mid, Decimal("100"))
        self.assertEqual(m.spread_abs, Decimal("2"))
        self.assertEqual(m.bid_depth_quote, Decimal("198"))
        self.assertEqual(m.ask_depth_quote, Decimal("303"))
        self.assertEqual(m.total_depth_quote, Decimal("501"))

    def test_bps_band_is_parameterized_not_hardcoded(self):
        m = self.book.metrics(DepthSpec("BPS_BAND", Decimal("250")))
        self.assertGreater(m.total_depth_quote, Decimal("0"))

    def test_absolute_update_and_level_removal(self):
        result = self.book.apply_updates([
            upd(side="BID", price="99", qty="0"),
            upd(side="BID", price="100", qty="1"),
            upd(side="ASK", price="101", qty="2"),
        ])
        self.assertEqual(result.status, "APPLIED")
        m = self.book.metrics(DepthSpec("TOP_N", Decimal("1")))
        self.assertEqual(m.best_bid, Decimal("100"))
        self.assertEqual(m.best_ask, Decimal("101"))
        self.assertEqual(m.sequence_last, 11)

    def test_gap_fails_closed(self):
        with self.assertRaises(BookSequenceGap):
            self.book.apply_updates([
                upd(first=12, last=12, side="BID", price="100", qty="1"),
            ])
        self.assertEqual(self.book.sequence_last, 10)

    def test_stale_update_is_ignored(self):
        result = self.book.apply_updates([
            upd(first=9, last=10, side="BID", price="100", qty="1"),
        ])
        self.assertEqual(result.status, "STALE_OR_DUPLICATE_IGNORED")
        self.assertEqual(self.book.sequence_last, 10)

    def test_crossed_update_is_atomic(self):
        before = self.book.metrics(DepthSpec("TOP_N", Decimal("1")))
        with self.assertRaises(CrossedBook):
            self.book.apply_updates([
                upd(side="BID", price="102", qty="1"),
            ])
        after = self.book.metrics(DepthSpec("TOP_N", Decimal("1")))
        self.assertEqual(after.best_bid, before.best_bid)
        self.assertEqual(after.best_ask, before.best_ask)
        self.assertEqual(after.sequence_last, before.sequence_last)

    def test_coinbase_snapshot_and_incremental_update(self):
        book = LocalOrderBook(
            venue="COINBASE_ADVANCED_SPOT",
            native_symbol="BTC-USD",
        )
        snapshot = [
            upd(
                venue="COINBASE_ADVANCED_SPOT",
                symbol="BTC-USD",
                first=0,
                last=0,
                side="BID",
                price="99",
                qty="1",
            ),
            upd(
                venue="COINBASE_ADVANCED_SPOT",
                symbol="BTC-USD",
                first=0,
                last=0,
                side="ASK",
                price="101",
                qty="1",
            ),
        ]
        book.initialize_from_snapshot_updates(snapshot)
        book.apply_updates([
            upd(
                venue="COINBASE_ADVANCED_SPOT",
                symbol="BTC-USD",
                first=1,
                last=1,
                side="BID",
                price="100",
                qty="2",
            ),
        ])
        m = book.metrics(DepthSpec("TOP_N", Decimal("1")))
        self.assertEqual(m.best_bid, Decimal("100"))
        self.assertEqual(m.sequence_last, 1)

    def test_invalid_depth_spec_rejected(self):
        with self.assertRaises(ValueError):
            DepthSpec("TOP_N", Decimal("1.5"))
        with self.assertRaises(ValueError):
            DepthSpec("UNKNOWN", Decimal("1"))


if __name__ == "__main__":
    unittest.main()

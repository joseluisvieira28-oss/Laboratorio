import random
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from order_book import BookSequenceGap, CrossedBook, DepthSpec, LocalOrderBook
from source_adapters import CanonicalBookUpdate


def make_update(sequence, side, price, qty):
    return CanonicalBookUpdate(
        venue="BINANCE_SPOT",
        native_symbol="BTCUSDT",
        source_event_time=str(sequence),
        sequence_first=sequence,
        sequence_last=sequence,
        side=side,
        price_level=Decimal(str(price)),
        absolute_quantity=Decimal(str(qty)),
    )


class FaultInjectionTests(unittest.TestCase):
    def _book(self):
        book = LocalOrderBook(venue="BINANCE_SPOT", native_symbol="BTCUSDT")
        book.load_snapshot_levels(
            bids=[
                (Decimal("99"), Decimal("5")),
                (Decimal("98"), Decimal("5")),
                (Decimal("97"), Decimal("5")),
            ],
            asks=[
                (Decimal("101"), Decimal("5")),
                (Decimal("102"), Decimal("5")),
                (Decimal("103"), Decimal("5")),
            ],
            sequence_last=100,
        )
        return book

    def test_seeded_update_stress_preserves_valid_book(self):
        rng = random.Random(20260924)
        book = self._book()
        seq = 100
        for _ in range(500):
            seq += 1
            side = "BID" if rng.random() < 0.5 else "ASK"
            if side == "BID":
                price = rng.choice([96, 97, 98])
            else:
                price = rng.choice([102, 103, 104])
            qty = rng.choice([0, 1, 2, 3, 5])
            book.apply_updates([make_update(seq, side, price, qty)])
            m = book.metrics(DepthSpec("TOP_N", Decimal("2")))
            self.assertLess(m.best_bid, m.best_ask)
            self.assertGreater(m.total_depth_quote, 0)
            self.assertEqual(m.sequence_last, seq)

    def test_gap_injection_leaves_previous_state_intact(self):
        book = self._book()
        before = book.metrics(DepthSpec("TOP_N", Decimal("2")))
        with self.assertRaises(BookSequenceGap):
            book.apply_updates([make_update(102, "BID", 98, 4)])
        after = book.metrics(DepthSpec("TOP_N", Decimal("2")))
        self.assertEqual(before, after)

    def test_cross_injection_leaves_previous_state_intact(self):
        book = self._book()
        before = book.metrics(DepthSpec("TOP_N", Decimal("2")))
        with self.assertRaises(CrossedBook):
            book.apply_updates([make_update(101, "BID", 101, 1)])
        after = book.metrics(DepthSpec("TOP_N", Decimal("2")))
        self.assertEqual(before, after)

    def test_duplicate_replay_does_not_mutate(self):
        book = self._book()
        book.apply_updates([make_update(101, "BID", 98, 7)])
        once = book.metrics(DepthSpec("TOP_N", Decimal("2")))
        result = book.apply_updates([make_update(101, "BID", 98, 1)])
        twice = book.metrics(DepthSpec("TOP_N", Decimal("2")))
        self.assertEqual(result.status, "STALE_OR_DUPLICATE_IGNORED")
        self.assertEqual(once, twice)


if __name__ == "__main__":
    unittest.main()

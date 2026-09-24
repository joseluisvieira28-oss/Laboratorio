import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from book_replay import (
    batch_time_ns,
    initial_observation,
    replay_incremental_batches,
)
from decision_boundary import rfc3339_to_ns
from order_book import BookSequenceGap, DepthSpec, LocalOrderBook
from source_adapters import CanonicalBookUpdate, parse_coinbase_level2_event


class BookReplayTests(unittest.TestCase):
    def setUp(self):
        self.depth = DepthSpec("TOP_N", Decimal("1"))
        snapshot_type, snapshot = parse_coinbase_level2_event(
            event={
                "type": "snapshot",
                "product_id": "BTC-USD",
                "updates": [
                    {
                        "side": "bid",
                        "event_time": "1970-01-01T00:00:00Z",
                        "price_level": "99",
                        "new_quantity": "2",
                    },
                    {
                        "side": "ask",
                        "event_time": "1970-01-01T00:00:00Z",
                        "price_level": "101",
                        "new_quantity": "2",
                    },
                ],
            },
            sequence_num=0,
            envelope_timestamp="2026-09-24T17:00:00Z",
        )
        self.assertEqual(snapshot_type, "snapshot")
        self.book = LocalOrderBook(
            venue="COINBASE_ADVANCED_SPOT",
            native_symbol="BTC-USD",
        )
        self.book.initialize_from_snapshot_updates(snapshot)
        self.anchor = rfc3339_to_ns("2026-09-24T17:00:00Z")
        self.decision = rfc3339_to_ns("2026-09-24T17:00:02Z")

    def _batch(self, sequence, event_time, bid_price):
        event_type, rows = parse_coinbase_level2_event(
            event={
                "type": "update",
                "product_id": "BTC-USD",
                "updates": [
                    {
                        "side": "bid",
                        "event_time": event_time,
                        "price_level": bid_price,
                        "new_quantity": "1",
                    }
                ],
            },
            sequence_num=sequence,
            envelope_timestamp=event_time,
        )
        self.assertEqual(event_type, "update")
        return rows

    def test_initial_snapshot_observation_uses_real_acquisition_time(self):
        obs = initial_observation(
            book=self.book,
            timestamp_ns=self.anchor,
            depth_spec=self.depth,
        )
        self.assertEqual(obs.timestamp_ns, self.anchor)
        self.assertEqual(obs.metrics.sequence_last, 0)

    def test_incremental_replay_produces_timed_metrics(self):
        batch = self._batch(
            1,
            "2026-09-24T17:00:01Z",
            "100",
        )
        out = replay_incremental_batches(
            book=self.book,
            batches=[batch],
            depth_spec=self.depth,
            decision_ns=self.decision,
        )
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].metrics.sequence_last, 1)
        self.assertEqual(out[0].metrics.best_bid, Decimal("100"))

    def test_coinbase_multi_update_batch_uses_latest_engine_time(self):
        batch = (
            CanonicalBookUpdate(
                venue="COINBASE_ADVANCED_SPOT",
                native_symbol="BTC-USD",
                source_event_time="2026-09-24T17:00:01.000000001Z",
                sequence_first=1,
                sequence_last=1,
                side="BID",
                price_level=Decimal("100"),
                absolute_quantity=Decimal("1"),
            ),
            CanonicalBookUpdate(
                venue="COINBASE_ADVANCED_SPOT",
                native_symbol="BTC-USD",
                source_event_time="2026-09-24T17:00:01.000000009Z",
                sequence_first=1,
                sequence_last=1,
                side="ASK",
                price_level=Decimal("102"),
                absolute_quantity=Decimal("1"),
            ),
        )
        self.assertEqual(
            batch_time_ns(batch),
            rfc3339_to_ns("2026-09-24T17:00:01.000000009Z"),
        )

    def test_latest_update_one_ns_after_decision_blocks_entire_batch(self):
        decision = rfc3339_to_ns("2026-09-24T17:00:01.000000008Z")
        batch = (
            CanonicalBookUpdate(
                venue="COINBASE_ADVANCED_SPOT",
                native_symbol="BTC-USD",
                source_event_time="2026-09-24T17:00:01.000000001Z",
                sequence_first=1,
                sequence_last=1,
                side="BID",
                price_level=Decimal("100"),
                absolute_quantity=Decimal("1"),
            ),
            CanonicalBookUpdate(
                venue="COINBASE_ADVANCED_SPOT",
                native_symbol="BTC-USD",
                source_event_time="2026-09-24T17:00:01.000000009Z",
                sequence_first=1,
                sequence_last=1,
                side="ASK",
                price_level=Decimal("102"),
                absolute_quantity=Decimal("1"),
            ),
        )
        with self.assertRaises(ValueError):
            replay_incremental_batches(
                book=self.book,
                batches=[batch],
                depth_spec=self.depth,
                decision_ns=decision,
            )
        self.assertEqual(self.book.sequence_last, 0)

    def test_future_batch_fails_before_mutating_book(self):
        batch = self._batch(
            1,
            "2026-09-24T17:00:03Z",
            "100",
        )
        with self.assertRaises(ValueError):
            replay_incremental_batches(
                book=self.book,
                batches=[batch],
                depth_spec=self.depth,
                decision_ns=self.decision,
            )
        self.assertEqual(self.book.sequence_last, 0)

    def test_sequence_gap_fails_closed(self):
        gap = self._batch(
            2,
            "2026-09-24T17:00:01Z",
            "100",
        )
        with self.assertRaises(BookSequenceGap):
            replay_incremental_batches(
                book=self.book,
                batches=[gap],
                depth_spec=self.depth,
                decision_ns=self.decision,
            )
        self.assertEqual(self.book.sequence_last, 0)


if __name__ == "__main__":
    unittest.main()

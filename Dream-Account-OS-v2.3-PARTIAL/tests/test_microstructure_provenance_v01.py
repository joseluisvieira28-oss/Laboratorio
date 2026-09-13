import sys
from pathlib import Path
import unittest

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH_DIR))

import microstructure_provenance_v01 as mp


class MicrostructureProvenanceV01Tests(unittest.TestCase):
    def test_canonical_hash_is_deterministic(self):
        a = {"b": 2, "a": 1}
        b = {"a": 1, "b": 2}
        self.assertEqual(mp.canonical_payload_hash(a), mp.canonical_payload_hash(b))
        self.assertEqual(len(mp.canonical_payload_hash(a)), 64)

    def test_normalized_record_validates_hash_and_contract(self):
        payload = {"bids": [[100.0, 1.0]], "asks": [[101.0, 2.0]]}
        record = mp.NormalizedRecord(
            venue="BINANCE_SPOT",
            market_type="SPOT",
            symbol="BTCUSDT",
            stream_type="L2_SNAPSHOT",
            exchange_ts_ns=123,
            collector_ts_ns=456,
            sequence_start=None,
            sequence_end=10,
            payload=payload,
            source_message_hash_sha256=mp.canonical_payload_hash(payload),
            segment_id="seg-1",
        )
        record.validate()

        bad = mp.NormalizedRecord(
            venue="BINANCE_SPOT",
            market_type="SPOT",
            symbol="BTCUSDT",
            stream_type="L2_SNAPSHOT",
            exchange_ts_ns=123,
            collector_ts_ns=456,
            sequence_start=None,
            sequence_end=10,
            payload=payload,
            source_message_hash_sha256="0" * 64,
            segment_id="seg-1",
        )
        with self.assertRaises(mp.ProvenanceViolation):
            bad.validate()

    def test_snapshot_and_delta_reconstruction(self):
        book = mp.L2Book()
        book.load_snapshot(
            bids=[(100.0, 1.0), (99.5, 2.0)],
            asks=[(101.0, 1.5), (101.5, 3.0)],
            sequence_end=10,
        )
        self.assertTrue(book.valid)
        self.assertEqual(book.best_bid, 100.0)
        self.assertEqual(book.best_ask, 101.0)

        book.apply_delta(
            [
                mp.BookLevelUpdate("BID", 100.0, 0.0),
                mp.BookLevelUpdate("BID", 100.5, 1.2),
                mp.BookLevelUpdate("ASK", 101.0, 2.5),
            ],
            sequence_start=11,
            sequence_end=11,
        )
        self.assertEqual(book.best_bid, 100.5)
        self.assertEqual(book.best_ask, 101.0)
        self.assertGreater(book.spread_bps(), 0.0)

    def test_gap_fails_closed_until_resync(self):
        book = mp.L2Book()
        book.load_snapshot(
            bids=[(100.0, 1.0)],
            asks=[(101.0, 1.0)],
            sequence_end=10,
        )
        with self.assertRaises(mp.ProvenanceViolation):
            book.apply_delta(
                [mp.BookLevelUpdate("BID", 100.0, 2.0)],
                sequence_start=12,
                sequence_end=12,
            )
        self.assertFalse(book.valid)
        with self.assertRaises(mp.ProvenanceViolation):
            book.spread_bps()

        book.load_snapshot(
            bids=[(100.0, 1.0)],
            asks=[(101.0, 1.0)],
            sequence_end=20,
        )
        self.assertTrue(book.valid)

    def test_crossed_book_fails_closed(self):
        book = mp.L2Book()
        book.load_snapshot(
            bids=[(100.0, 1.0)],
            asks=[(101.0, 1.0)],
            sequence_end=1,
        )
        with self.assertRaises(mp.ProvenanceViolation):
            book.apply_delta(
                [mp.BookLevelUpdate("BID", 102.0, 1.0)],
                sequence_start=2,
                sequence_end=2,
            )
        self.assertFalse(book.valid)

    def test_depth_within_bps(self):
        book = mp.L2Book()
        book.load_snapshot(
            bids=[(100.0, 1.0), (99.9, 2.0), (98.0, 100.0)],
            asks=[(100.2, 1.5), (100.3, 2.5), (102.0, 100.0)],
            sequence_end=None,
        )
        depth = book.depth_within_bps(25.0)
        self.assertAlmostEqual(depth["bid_quantity"], 3.0)
        self.assertAlmostEqual(depth["ask_quantity"], 4.0)

    def test_ordered_segment_digest_depends_on_order(self):
        h1 = mp.canonical_payload_hash({"n": 1})
        h2 = mp.canonical_payload_hash({"n": 2})
        self.assertNotEqual(
            mp.ordered_segment_digest([h1, h2]),
            mp.ordered_segment_digest([h2, h1]),
        )

    def test_bad_numeric_state_rejected(self):
        with self.assertRaises(mp.ProvenanceViolation):
            mp.BookLevelUpdate("BID", 0.0, 1.0).validate()
        with self.assertRaises(mp.ProvenanceViolation):
            mp.BookLevelUpdate("ASK", 100.0, -1.0).validate()

    def test_governance_receipt_is_fail_closed(self):
        receipt = mp.provenance_governance_receipt()
        self.assertEqual(receipt["h02_status"], "NOT_AUTHORIZED")
        self.assertFalse(receipt["target_outcomes_accessed_by_this_module"])
        self.assertFalse(receipt["live_trading_authorized"])
        self.assertFalse(receipt["exchange_mutation_authorized"])
        self.assertFalse(receipt["authenticated_trading_endpoints_required"])
        self.assertFalse(receipt["network_access_in_this_module"])
        self.assertFalse(receipt["mexc_2025_09_through_2025_12_accessed"])


if __name__ == "__main__":
    unittest.main()

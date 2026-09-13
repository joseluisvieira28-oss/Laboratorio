import sys
from pathlib import Path
import unittest

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH_DIR))

import microstructure_collector_parsers_v01 as cp
import microstructure_provenance_v01 as mp


class MicrostructureCollectorParsersV01Tests(unittest.TestCase):
    def test_binance_diff_depth_parser(self):
        msg = {
            "e": "depthUpdate",
            "E": 1672515782136,
            "s": "BTCUSDT",
            "U": 157,
            "u": 160,
            "b": [["100.0", "2.0"]],
            "a": [["101.0", "3.0"]],
        }
        env = cp.parse_binance_diff_depth(msg)
        self.assertEqual(env.venue, "BINANCE_SPOT")
        self.assertEqual(env.stream_type, "L2_DELTA")
        self.assertEqual(env.sequence_start, 157)
        self.assertEqual(env.sequence_end, 160)
        self.assertEqual(env.exchange_ts_ns, 1672515782136 * 1_000_000)

    def test_binance_snapshot_bridge_and_gap_resync(self):
        bridge = cp.BinanceSnapshotBridge()
        bridge.load_snapshot(
            {
                "lastUpdateId": 100,
                "bids": [["100.0", "1.0"], ["99.5", "2.0"]],
                "asks": [["101.0", "1.0"], ["101.5", "2.0"]],
            },
            "BTCUSDT",
        )
        stale = {
            "e": "depthUpdate", "E": 1, "s": "BTCUSDT",
            "U": 90, "u": 100, "b": [], "a": [],
        }
        self.assertFalse(bridge.apply_first_buffered(stale))
        first = {
            "e": "depthUpdate", "E": 2, "s": "BTCUSDT",
            "U": 99, "u": 103,
            "b": [["100.0", "0"], ["100.5", "1.25"]],
            "a": [["101.0", "2.0"]],
        }
        self.assertTrue(bridge.apply_first_buffered(first))
        self.assertTrue(bridge.synchronized)
        self.assertEqual(bridge.book.best_bid, 100.5)
        self.assertEqual(bridge.book.last_sequence_end, 103)

        nxt = {
            "e": "depthUpdate", "E": 3, "s": "BTCUSDT",
            "U": 104, "u": 105,
            "b": [["100.5", "1.5"]], "a": [],
        }
        bridge.apply_next(nxt)
        self.assertEqual(bridge.book.last_sequence_end, 105)

        gap = {
            "e": "depthUpdate", "E": 4, "s": "BTCUSDT",
            "U": 108, "u": 109,
            "b": [], "a": [["101.0", "1.5"]],
        }
        with self.assertRaises(mp.ProvenanceViolation):
            bridge.apply_next(gap)
        self.assertFalse(bridge.synchronized)
        self.assertFalse(bridge.book.valid)

    def test_binance_invalid_first_bridge_fails_closed(self):
        bridge = cp.BinanceSnapshotBridge()
        bridge.load_snapshot(
            {"lastUpdateId": 100, "bids": [["100", "1"]], "asks": [["101", "1"]]},
            "BTCUSDT",
        )
        msg = {
            "e": "depthUpdate", "E": 2, "s": "BTCUSDT",
            "U": 102, "u": 103, "b": [], "a": [],
        }
        with self.assertRaises(mp.ProvenanceViolation):
            bridge.apply_first_buffered(msg)
        self.assertFalse(bridge.book.valid)

    def test_binance_book_ticker_and_trade(self):
        bbo = cp.parse_binance_book_ticker(
            {"u": 400900217, "s": "ETHUSDT", "b": "2500", "B": "2", "a": "2500.1", "A": "3"}
        )
        self.assertEqual(bbo.stream_type, "BBO")
        self.assertIsNone(bbo.exchange_ts_ns)
        trade = cp.parse_binance_trade(
            {
                "e": "trade", "E": 1000, "s": "ETHUSDT", "t": 7,
                "p": "2500.0", "q": "0.1", "T": 999, "m": True, "M": True,
            }
        )
        self.assertEqual(trade.stream_type, "TRADE")
        self.assertEqual(trade.exchange_ts_ns, 999_000_000)

    def test_coinbase_snapshot_and_update_parser(self):
        snap = {
            "type": "snapshot",
            "product_id": "BTC-USD",
            "time": "2026-09-12T10:20:30.123456789Z",
            "sequence": 10,
            "bids": [["100.0", "1.0"]],
            "asks": [["101.0", "2.0"]],
        }
        env = cp.parse_coinbase_level2(snap)
        self.assertEqual(env.stream_type, "L2_SNAPSHOT")
        self.assertEqual(env.sequence_start, 10)
        self.assertEqual(env.exchange_ts_ns % 1_000_000_000, 123456789)
        bids, asks = cp.coinbase_snapshot_levels(snap)
        self.assertEqual(bids[0].side, "BID")
        self.assertEqual(asks[0].side, "ASK")

        update = {
            "type": "l2update",
            "product_id": "BTC-USD",
            "time": "2026-09-12T10:20:30.223456789Z",
            "sequence": 11,
            "changes": [["buy", "100.0", "0"], ["sell", "101.0", "3.0"]],
        }
        env2 = cp.parse_coinbase_level2(update)
        self.assertEqual(env2.stream_type, "L2_DELTA")
        changes = cp.coinbase_delta_updates(update)
        self.assertEqual(changes[0].quantity, 0.0)
        self.assertEqual(changes[1].side, "ASK")

    def test_coinbase_heartbeat(self):
        env = cp.parse_coinbase_heartbeat(
            {
                "type": "heartbeat",
                "sequence": 90,
                "last_trade_id": 20,
                "product_id": "ETH-USD",
                "time": "2026-09-12T10:20:30.464459Z",
            }
        )
        self.assertEqual(env.venue, "COINBASE_SPOT")
        self.assertEqual(env.sequence_end, 90)

    def test_contract_rejects_unfrozen_symbols(self):
        with self.assertRaises(mp.ProvenanceViolation):
            cp.parse_binance_diff_depth(
                {"e": "depthUpdate", "E": 1, "s": "SOLUSDT", "U": 1, "u": 1, "b": [], "a": []}
            )
        with self.assertRaises(mp.ProvenanceViolation):
            cp.parse_coinbase_level2(
                {"type": "snapshot", "product_id": "SOL-USD", "bids": [["1", "1"]], "asks": [["2", "1"]]}
            )

    def test_malformed_json_fails_closed(self):
        with self.assertRaises(mp.ProvenanceViolation):
            cp.parse_json_text("{not-json}")


if __name__ == "__main__":
    unittest.main()

import sys
from pathlib import Path
import unittest

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH_DIR))

import microstructure_coinbase_advanced_v01 as ca
import microstructure_provenance_v01 as mp


def l2_message(sequence_num, event_type, updates):
    return {
        "channel": "l2_data",
        "client_id": "",
        "timestamp": "2026-09-12T10:20:30.123456789Z",
        "sequence_num": sequence_num,
        "events": [{
            "type": event_type,
            "product_id": "BTC-USD",
            "updates": updates,
        }],
    }


class CoinbaseAdvancedV01Tests(unittest.TestCase):
    def test_level2_snapshot_and_update(self):
        snap = l2_message(0, "snapshot", [
            {"side": "bid", "event_time": "2026-09-12T10:20:30Z", "price_level": "100", "new_quantity": "1"},
            {"side": "ask", "event_time": "2026-09-12T10:20:30Z", "price_level": "101", "new_quantity": "2"},
        ])
        env = ca.parse_envelope(snap)
        self.assertEqual(env.venue, "COINBASE_ADVANCED_SPOT")
        self.assertEqual(env.stream_type, "L2_SNAPSHOT")
        self.assertEqual(env.exchange_ts_ns % 1_000_000_000, 123456789)

        book = ca.AdvancedTradeBook("BTC-USD")
        book.apply_message(snap)
        self.assertTrue(book.synchronized)
        self.assertEqual(book.book.best_bid, 100.0)
        self.assertEqual(book.book.best_ask, 101.0)

        upd = l2_message(1, "update", [
            {"side": "bid", "event_time": "2026-09-12T10:20:31Z", "price_level": "100", "new_quantity": "0"},
            {"side": "bid", "event_time": "2026-09-12T10:20:31Z", "price_level": "100.5", "new_quantity": "3"},
        ])
        book.apply_message(upd)
        self.assertEqual(book.book.best_bid, 100.5)

    def test_sequence_gap_fails_closed(self):
        book = ca.AdvancedTradeBook("BTC-USD")
        book.apply_message(l2_message(5, "snapshot", [
            {"side": "bid", "event_time": "2026-09-12T10:20:30Z", "price_level": "100", "new_quantity": "1"},
            {"side": "ask", "event_time": "2026-09-12T10:20:30Z", "price_level": "101", "new_quantity": "1"},
        ]))
        with self.assertRaises(mp.ProvenanceViolation):
            book.apply_message(l2_message(7, "update", [
                {"side": "bid", "event_time": "2026-09-12T10:20:31Z", "price_level": "100", "new_quantity": "2"},
            ]))
        self.assertFalse(book.synchronized)
        self.assertFalse(book.book.valid)

    def test_update_before_snapshot_rejected(self):
        book = ca.AdvancedTradeBook("BTC-USD")
        with self.assertRaises(mp.ProvenanceViolation):
            book.apply_message(l2_message(0, "update", [
                {"side": "bid", "event_time": "2026-09-12T10:20:31Z", "price_level": "100", "new_quantity": "2"},
            ]))

    def test_market_trades_are_public_trade_records_only(self):
        msg = {
            "channel": "market_trades",
            "client_id": "",
            "timestamp": "2026-09-12T10:20:30.123Z",
            "sequence_num": 12,
            "events": [{
                "type": "update",
                "trades": [{
                    "trade_id": "1",
                    "product_id": "ETH-USD",
                    "price": "2500.1",
                    "size": "0.3",
                    "side": "BUY",
                    "time": "2026-09-12T10:20:30.100Z",
                }],
            }],
        }
        env = ca.parse_envelope(msg)
        self.assertEqual(env.stream_type, "TRADE")
        self.assertEqual(env.product_ids, ("ETH-USD",))

    def test_heartbeat_has_dedicated_stream_type(self):
        msg = {
            "channel": "heartbeats",
            "client_id": "",
            "timestamp": "2026-09-12T10:20:30.123Z",
            "sequence_num": 9,
            "events": [{"current_time": "x", "heartbeat_counter": "3049"}],
        }
        env = ca.parse_envelope(msg)
        self.assertEqual(env.stream_type, "HEARTBEAT")
        payload_hash = mp.canonical_payload_hash(msg)
        record = mp.NormalizedRecord(
            venue="COINBASE_ADVANCED_SPOT",
            market_type="SPOT",
            symbol="HEARTBEAT",
            stream_type="HEARTBEAT",
            exchange_ts_ns=env.exchange_ts_ns,
            collector_ts_ns=env.exchange_ts_ns,
            sequence_start=9,
            sequence_end=9,
            payload=msg,
            source_message_hash_sha256=payload_hash,
            segment_id="hb-1",
        )
        record.validate()

    def test_private_or_unknown_channels_rejected(self):
        for channel in ("user", "futures_balance_summary", "orders"):
            with self.assertRaises(mp.ProvenanceViolation):
                ca.parse_envelope({
                    "channel": channel,
                    "client_id": "",
                    "timestamp": "2026-09-12T10:20:30Z",
                    "sequence_num": 0,
                    "events": [{}],
                })

    def test_non_empty_client_id_rejected_for_public_contract(self):
        with self.assertRaises(mp.ProvenanceViolation):
            ca.parse_envelope({
                "channel": "heartbeats",
                "client_id": "account-bound-client",
                "timestamp": "2026-09-12T10:20:30Z",
                "sequence_num": 0,
                "events": [{"heartbeat_counter": "1"}],
            })


if __name__ == "__main__":
    unittest.main()

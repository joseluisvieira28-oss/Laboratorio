import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from shadow_journal import connect_journal, ingest_message, start_session
from shadow_recovery import replay_coinbase_level2_session


def snapshot_message(sequence=10):
    return {
        "channel": "l2_data",
        "timestamp": "2026-09-24T17:00:00.000000000Z",
        "sequence_num": sequence,
        "events": [{
            "type": "snapshot",
            "product_id": "BTC-USD",
            "updates": [
                {
                    "side": "bid",
                    "event_time": "1970-01-01T00:00:00Z",
                    "price_level": "99",
                    "new_quantity": "2"
                },
                {
                    "side": "ask",
                    "event_time": "1970-01-01T00:00:00Z",
                    "price_level": "101",
                    "new_quantity": "2"
                }
            ]
        }]
    }


def update_message(sequence=11):
    return {
        "channel": "l2_data",
        "timestamp": "2026-09-24T17:00:01.000000010Z",
        "sequence_num": sequence,
        "events": [{
            "type": "update",
            "product_id": "BTC-USD",
            "updates": [
                {
                    "side": "bid",
                    "event_time": "2026-09-24T17:00:01.000000001Z",
                    "price_level": "100",
                    "new_quantity": "1"
                },
                {
                    "side": "ask",
                    "event_time": "2026-09-24T17:00:01.000000009Z",
                    "price_level": "102",
                    "new_quantity": "1"
                }
            ]
        }]
    }


class ShadowRecoveryTests(unittest.TestCase):
    def _conn(self, path):
        conn = connect_journal(path)
        start_session(
            conn,
            session_id="S1",
            collector_version="TEST",
            endpoint="wss://example.invalid",
            product_id=product_id,
            started_wall_ns=1,
            started_monotonic_ns=2,
        )
        return conn

    def _ingest(self, conn, msg, wall, product_id="BTC-USD"):
        raw = json.dumps(msg, separators=(",", ":")).encode()
        ingest_message(
            conn,
            session_id="S1",
            channel=msg["channel"],
            product_id="BTC-USD",
            sequence_num=msg["sequence_num"],
            envelope_timestamp=msg["timestamp"],
            source_time_max_ns=wall,
            collector_wall_ns=wall,
            collector_monotonic_ns=wall + 1,
            raw_payload=raw,
        )

    def test_recovery_reconstructs_from_raw_journal_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            conn = self._conn(path)
            self._ingest(conn, snapshot_message(), 100)
            self._ingest(conn, update_message(), 200)
            result = replay_coinbase_level2_session(
                conn,
                session_id="S1",
                product_id="BTC-USD",
            )
            self.assertTrue(result.ok, result.failure_reason)
            self.assertEqual(result.snapshot_count, 1)
            self.assertEqual(result.update_message_count, 1)
            self.assertEqual(result.final_sequence, 11)
            conn.close()

            conn = connect_journal(path)
            restarted = replay_coinbase_level2_session(
                conn,
                session_id="S1",
                product_id="BTC-USD",
            )
            self.assertEqual(result, restarted)
            conn.close()

    def test_intervening_subscription_sequence_is_not_l2_gap(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            conn = self._conn(path)
            self._ingest(conn, snapshot_message(0), 100)
            self._ingest(conn, update_message(1), 200)
            subscription = {
                "channel": "subscriptions",
                "timestamp": "2026-09-24T17:00:01.100000000Z",
                "sequence_num": 2,
                "events": [{"subscriptions": {"level2": ["BTC-USD"]}}],
            }
            self._ingest(conn, subscription, 250, product_id=None)
            self._ingest(conn, update_message(3), 300)
            result = replay_coinbase_level2_session(
                conn,
                session_id="S1",
                product_id="BTC-USD",
            )
            self.assertTrue(result.ok, result.failure_reason)
            self.assertEqual(result.snapshot_count, 1)
            self.assertEqual(result.update_message_count, 2)
            self.assertEqual(result.final_sequence, 3)
            conn.close()

    def test_gap_fails_recovery_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            conn = self._conn(path)
            self._ingest(conn, snapshot_message(10), 100)
            self._ingest(conn, update_message(12), 200)
            result = replay_coinbase_level2_session(
                conn,
                session_id="S1",
                product_id="BTC-USD",
            )
            self.assertFalse(result.ok)
            self.assertIsNotNone(result.failure_reason)
            conn.close()

    def test_update_without_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            conn = self._conn(path)
            self._ingest(conn, update_message(11), 200)
            result = replay_coinbase_level2_session(
                conn,
                session_id="S1",
                product_id="BTC-USD",
            )
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "ValueError")
            conn.close()


if __name__ == "__main__":
    unittest.main()

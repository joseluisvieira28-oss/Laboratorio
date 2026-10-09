import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from shadow_journal import (
    connect_journal,
    ingest_message,
    message_count,
    sqlite_integrity_ok,
    start_session,
)
from shadow_recovery import verify_session_chain


class ShadowJournalTests(unittest.TestCase):
    def _start(self, path):
        conn = connect_journal(path)
        start_session(
            conn,
            session_id="S1",
            collector_version="TEST",
            endpoint="wss://example.invalid",
            product_id="BTC-USD",
            started_wall_ns=100,
            started_monotonic_ns=200,
        )
        return conn

    def test_insert_duplicate_is_idempotent_within_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            conn = self._start(path)
            raw = b'{"channel":"level2","sequence_num":1}'
            first = ingest_message(
                conn,
                session_id="S1",
                channel="level2",
                product_id="BTC-USD",
                sequence_num=1,
                envelope_timestamp="2026-09-24T17:00:00Z",
                source_time_max_ns=1,
                collector_wall_ns=10,
                collector_monotonic_ns=20,
                raw_payload=raw,
            )
            second = ingest_message(
                conn,
                session_id="S1",
                channel="level2",
                product_id="BTC-USD",
                sequence_num=1,
                envelope_timestamp="2026-09-24T17:00:00Z",
                source_time_max_ns=1,
                collector_wall_ns=999,
                collector_monotonic_ns=999,
                raw_payload=raw,
            )
            self.assertTrue(first.inserted)
            self.assertFalse(second.inserted)
            self.assertEqual(first.ordinal, second.ordinal)
            self.assertEqual(message_count(conn, "S1"), 1)
            self.assertTrue(verify_session_chain(conn, session_id="S1").ok)
            conn.close()

    def test_restart_reopens_and_verifies_same_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            conn = self._start(path)
            for seq in (1, 2, 3):
                ingest_message(
                    conn,
                    session_id="S1",
                    channel="level2",
                    product_id="BTC-USD",
                    sequence_num=seq,
                    envelope_timestamp=f"2026-09-24T17:00:0{seq}Z",
                    source_time_max_ns=seq,
                    collector_wall_ns=100 + seq,
                    collector_monotonic_ns=200 + seq,
                    raw_payload=f'{{"sequence_num":{seq}}}'.encode(),
                )
            before = verify_session_chain(conn, session_id="S1")
            conn.close()

            conn = connect_journal(path)
            after = verify_session_chain(conn, session_id="S1")
            self.assertTrue(after.ok)
            self.assertEqual(before.chain_head_sha256, after.chain_head_sha256)
            self.assertEqual(after.message_count, 3)
            self.assertTrue(sqlite_integrity_ok(conn))
            conn.close()

    def test_raw_payload_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            conn = self._start(path)
            ingest_message(
                conn,
                session_id="S1",
                channel="level2",
                product_id="BTC-USD",
                sequence_num=1,
                envelope_timestamp="2026-09-24T17:00:00Z",
                source_time_max_ns=1,
                collector_wall_ns=10,
                collector_monotonic_ns=20,
                raw_payload=b'{"x":1}',
            )
            conn.execute(
                "UPDATE shadow_messages SET raw_payload=? WHERE session_id='S1'",
                (sqlite3.Binary(b'{"x":2}'),),
            )
            conn.commit()
            result = verify_session_chain(conn, session_id="S1")
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "RAW_SHA256_MISMATCH")
            conn.close()

    def test_chain_metadata_tamper_is_detected(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "journal.sqlite3"
            conn = self._start(path)
            ingest_message(
                conn,
                session_id="S1",
                channel="level2",
                product_id="BTC-USD",
                sequence_num=1,
                envelope_timestamp="2026-09-24T17:00:00Z",
                source_time_max_ns=1,
                collector_wall_ns=10,
                collector_monotonic_ns=20,
                raw_payload=b'{"x":1}',
            )
            conn.execute(
                "UPDATE shadow_messages SET collector_wall_ns=11 WHERE session_id='S1'"
            )
            conn.commit()
            result = verify_session_chain(conn, session_id="S1")
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "CHAIN_SHA256_MISMATCH")
            conn.close()


if __name__ == "__main__":
    unittest.main()

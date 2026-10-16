import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from h02_scope_journal import (
    connect_scope_journal,
    ingest_scope_record,
    ordered_by_collector_arrival,
    session_record_count,
    sqlite_integrity_ok,
    start_scope_session,
)
from h02_scope_recovery import verify_scope_session_chain


class H02ScopeJournalTests(unittest.TestCase):
    def _start(self, path):
        conn = connect_scope_journal(path)
        start_scope_session(
            conn,
            session_id="S1",
            batch_id="B1",
            collector_version="TEST",
            venue="BINANCE_SPOT",
            native_symbol="BTCUSDT",
            stream_group="BINANCE_TRADES_DEPTH",
            endpoint="wss://example.invalid",
            started_wall_ns=10,
            started_monotonic_ns=20,
        )
        return conn

    def _ingest(self, conn, raw=b'{"x":1}', wall=100):
        return ingest_scope_record(
            conn,
            session_id="S1",
            venue="BINANCE_SPOT",
            native_symbol="BTCUSDT",
            transport="WEBSOCKET",
            message_kind="BINANCE_DEPTH_DIFF",
            channel="btcusdt@depth@100ms",
            sequence_first=1,
            sequence_last=1,
            source_time_min_ns=1,
            source_time_max_ns=1,
            collector_wall_ns=wall,
            collector_monotonic_ns=wall + 1,
            raw_payload=raw,
        )

    def test_duplicate_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope.sqlite3"
            conn = self._start(path)
            first = self._ingest(conn)
            second = self._ingest(conn, wall=999)
            self.assertTrue(first.inserted)
            self.assertFalse(second.inserted)
            self.assertEqual(first.ordinal, second.ordinal)
            self.assertEqual(session_record_count(conn, "S1"), 1)
            self.assertTrue(verify_scope_session_chain(conn, session_id="S1").ok)
            conn.close()

    def test_restart_preserves_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope.sqlite3"
            conn = self._start(path)
            for seq in (1, 2, 3):
                ingest_scope_record(
                    conn,
                    session_id="S1",
                    venue="BINANCE_SPOT",
                    native_symbol="BTCUSDT",
                    transport="WEBSOCKET",
                    message_kind="BINANCE_DEPTH_DIFF",
                    channel="btcusdt@depth@100ms",
                    sequence_first=seq,
                    sequence_last=seq,
                    source_time_min_ns=seq,
                    source_time_max_ns=seq,
                    collector_wall_ns=100 + seq,
                    collector_monotonic_ns=200 + seq,
                    raw_payload=f'{{"seq":{seq}}}'.encode(),
                )
            before = verify_scope_session_chain(conn, session_id="S1")
            conn.close()

            conn = connect_scope_journal(path)
            after = verify_scope_session_chain(conn, session_id="S1")
            self.assertTrue(after.ok)
            self.assertEqual(before.chain_head_sha256, after.chain_head_sha256)
            self.assertEqual(after.message_count, 3)
            self.assertTrue(sqlite_integrity_ok(conn))
            conn.close()

    def test_raw_tamper_fails_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope.sqlite3"
            conn = self._start(path)
            self._ingest(conn)
            conn.execute(
                "UPDATE scope_records SET raw_payload=? WHERE session_id='S1'",
                (sqlite3.Binary(b'{"x":2}'),),
            )
            conn.commit()
            result = verify_scope_session_chain(conn, session_id="S1")
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "RAW_SHA256_MISMATCH")
            conn.close()

    def test_metadata_tamper_fails_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope.sqlite3"
            conn = self._start(path)
            self._ingest(conn)
            conn.execute(
                "UPDATE scope_records SET collector_wall_ns=999 WHERE session_id='S1'"
            )
            conn.commit()
            result = verify_scope_session_chain(conn, session_id="S1")
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "CHAIN_SHA256_MISMATCH")
            conn.close()

    def test_session_identity_is_enforced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope.sqlite3"
            conn = self._start(path)
            with self.assertRaisesRegex(ValueError, "venue/symbol"):
                ingest_scope_record(
                    conn,
                    session_id="S1",
                    venue="COINBASE_ADVANCED_SPOT",
                    native_symbol="BTC-USD",
                    transport="WEBSOCKET",
                    message_kind="X",
                    channel="X",
                    sequence_first=None,
                    sequence_last=None,
                    source_time_min_ns=None,
                    source_time_max_ns=None,
                    collector_wall_ns=1,
                    collector_monotonic_ns=2,
                    raw_payload=b"{}",
                )
            conn.close()


    def test_monotonic_reversal_fails_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope.sqlite3"
            conn = self._start(path)
            ingest_scope_record(
                conn,
                session_id="S1",
                venue="BINANCE_SPOT",
                native_symbol="BTCUSDT",
                transport="WEBSOCKET",
                message_kind="BINANCE_DEPTH_DIFF",
                channel="btcusdt@depth@100ms",
                sequence_first=1,
                sequence_last=1,
                source_time_min_ns=1,
                source_time_max_ns=1,
                collector_wall_ns=100,
                collector_monotonic_ns=200,
                raw_payload=b'{"seq":1}',
            )
            ingest_scope_record(
                conn,
                session_id="S1",
                venue="BINANCE_SPOT",
                native_symbol="BTCUSDT",
                transport="WEBSOCKET",
                message_kind="BINANCE_DEPTH_DIFF",
                channel="btcusdt@depth@100ms",
                sequence_first=2,
                sequence_last=2,
                source_time_min_ns=2,
                source_time_max_ns=2,
                collector_wall_ns=101,
                collector_monotonic_ns=199,
                raw_payload=b'{"seq":2}',
            )
            result = verify_scope_session_chain(conn, session_id="S1")
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "COLLECTOR_MONOTONIC_REVERSAL")
            conn.close()


    def test_market_data_without_source_time_fails_chain(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "scope.sqlite3"
            conn = self._start(path)
            ingest_scope_record(
                conn,
                session_id="S1",
                venue="BINANCE_SPOT",
                native_symbol="BTCUSDT",
                transport="WEBSOCKET",
                message_kind="BINANCE_DEPTH_DIFF",
                channel="btcusdt@depth@100ms",
                sequence_first=1,
                sequence_last=1,
                source_time_min_ns=None,
                source_time_max_ns=None,
                collector_wall_ns=100,
                collector_monotonic_ns=200,
                raw_payload=b'{"seq":1}',
            )
            result = verify_scope_session_chain(conn, session_id="S1")
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "SOURCE_TIME_MISSING")
            conn.close()


    def test_binance_async_snapshot_records_are_sorted_before_journaling(self):
        records = [
            {
                "message_kind": "BINANCE_DEPTH_DIFF",
                "collector_monotonic_ns": 300,
                "collector_wall_ns": 3000,
            },
            {
                "message_kind": "BINANCE_DEPTH_SNAPSHOT",
                "collector_monotonic_ns": 200,
                "collector_wall_ns": 2000,
            },
            {
                "message_kind": "BINANCE_AGGTRADE",
                "collector_monotonic_ns": 100,
                "collector_wall_ns": 1000,
            },
        ]
        ordered = ordered_by_collector_arrival(records)
        self.assertEqual(
            [row["collector_monotonic_ns"] for row in ordered],
            [100, 200, 300],
        )


if __name__ == "__main__":
    unittest.main()

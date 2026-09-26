import json
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
    start_scope_session,
)
from h02_scope_recovery import (
    replay_binance_scope_session,
    replay_coinbase_level2_scope_session,
    verify_coinbase_market_trades_scope_session,
)


def _start(conn, *, session_id, venue, symbol, group):
    start_scope_session(
        conn,
        session_id=session_id,
        batch_id="B1",
        collector_version="TEST",
        venue=venue,
        native_symbol=symbol,
        stream_group=group,
        endpoint="public://example",
        started_wall_ns=1,
        started_monotonic_ns=2,
    )


def _ingest(
    conn,
    *,
    session_id,
    venue,
    symbol,
    kind,
    channel,
    raw,
    seq_first,
    seq_last,
    ordinal_clock,
    transport="WEBSOCKET",
):
    ingest_scope_record(
        conn,
        session_id=session_id,
        venue=venue,
        native_symbol=symbol,
        transport=transport,
        message_kind=kind,
        channel=channel,
        sequence_first=seq_first,
        sequence_last=seq_last,
        source_time_min_ns=ordinal_clock,
        source_time_max_ns=ordinal_clock,
        collector_wall_ns=ordinal_clock,
        collector_monotonic_ns=ordinal_clock + 1,
        raw_payload=json.dumps(raw, separators=(",", ":")).encode(),
    )


def cb_subscription(seq, channel, product):
    return {
        "channel": "subscriptions",
        "timestamp": "2026-09-26T18:00:00Z",
        "sequence_num": seq,
        "events": [{"subscriptions": {channel: [product]}}],
    }


def cb_l2_snapshot(seq, product):
    return {
        "channel": "l2_data",
        "timestamp": "2026-09-26T18:00:01.000000000Z",
        "sequence_num": seq,
        "events": [{
            "type": "snapshot",
            "product_id": product,
            "updates": [
                {"side": "bid", "event_time": "1970-01-01T00:00:00Z", "price_level": "99", "new_quantity": "2"},
                {"side": "ask", "event_time": "1970-01-01T00:00:00Z", "price_level": "101", "new_quantity": "2"},
            ],
        }],
    }


def cb_l2_update(seq, product):
    return {
        "channel": "l2_data",
        "timestamp": "2026-09-26T18:00:02.000000010Z",
        "sequence_num": seq,
        "events": [{
            "type": "update",
            "product_id": product,
            "updates": [
                {"side": "bid", "event_time": "2026-09-26T18:00:02.000000001Z", "price_level": "100", "new_quantity": "1"},
                {"side": "ask", "event_time": "2026-09-26T18:00:02.000000009Z", "price_level": "102", "new_quantity": "1"},
            ],
        }],
    }


def cb_trade(seq, product, trade_id="1"):
    return {
        "channel": "market_trades",
        "timestamp": "2026-09-26T18:00:01Z",
        "sequence_num": seq,
        "events": [{
            "type": "update",
            "trades": [{
                "trade_id": trade_id,
                "product_id": product,
                "price": "100",
                "size": "1",
                "side": "SELL",
                "time": "2026-09-26T18:00:01Z",
            }],
        }],
    }


class H02ScopeRecoveryTests(unittest.TestCase):
    def test_coinbase_level2_recovery_passes_contiguous_single_channel(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect_scope_journal(Path(tmp) / "scope.sqlite3")
            _start(conn, session_id="C1", venue="COINBASE_ADVANCED_SPOT", symbol="BTC-USD", group="COINBASE_LEVEL2")
            for clock, msg, kind in (
                (10, cb_subscription(0, "level2", "BTC-USD"), "COINBASE_CONTROL"),
                (20, cb_l2_snapshot(1, "BTC-USD"), "COINBASE_LEVEL2"),
                (30, cb_l2_update(2, "BTC-USD"), "COINBASE_LEVEL2"),
            ):
                _ingest(
                    conn,
                    session_id="C1",
                    venue="COINBASE_ADVANCED_SPOT",
                    symbol="BTC-USD",
                    kind=kind,
                    channel=msg["channel"],
                    raw=msg,
                    seq_first=msg["sequence_num"],
                    seq_last=msg["sequence_num"],
                    ordinal_clock=clock,
                )
            result = replay_coinbase_level2_scope_session(conn, session_id="C1")
            self.assertTrue(result.ok, result.failure_reason)
            self.assertEqual(result.final_sequence, 2)
            conn.close()

    def test_coinbase_level2_gap_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect_scope_journal(Path(tmp) / "scope.sqlite3")
            _start(conn, session_id="C1", venue="COINBASE_ADVANCED_SPOT", symbol="BTC-USD", group="COINBASE_LEVEL2")
            for clock, msg, kind in (
                (10, cb_subscription(0, "level2", "BTC-USD"), "COINBASE_CONTROL"),
                (20, cb_l2_snapshot(2, "BTC-USD"), "COINBASE_LEVEL2"),
            ):
                _ingest(
                    conn,
                    session_id="C1",
                    venue="COINBASE_ADVANCED_SPOT",
                    symbol="BTC-USD",
                    kind=kind,
                    channel=msg["channel"],
                    raw=msg,
                    seq_first=msg["sequence_num"],
                    seq_last=msg["sequence_num"],
                    ordinal_clock=clock,
                )
            result = replay_coinbase_level2_scope_session(conn, session_id="C1")
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "BookSequenceGap")
            conn.close()

    def test_coinbase_market_trades_recovery(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect_scope_journal(Path(tmp) / "scope.sqlite3")
            _start(conn, session_id="T1", venue="COINBASE_ADVANCED_SPOT", symbol="ETH-USD", group="COINBASE_MARKET_TRADES")
            for clock, msg, kind in (
                (10, cb_subscription(0, "market_trades", "ETH-USD"), "COINBASE_CONTROL"),
                (20, cb_trade(1, "ETH-USD", "99"), "COINBASE_MARKET_TRADES"),
            ):
                _ingest(
                    conn,
                    session_id="T1",
                    venue="COINBASE_ADVANCED_SPOT",
                    symbol="ETH-USD",
                    kind=kind,
                    channel=msg["channel"],
                    raw=msg,
                    seq_first=msg["sequence_num"],
                    seq_last=msg["sequence_num"],
                    ordinal_clock=clock,
                )
            result = verify_coinbase_market_trades_scope_session(conn, session_id="T1")
            self.assertTrue(result.ok, result.failure_reason)
            self.assertEqual(result.final_sequence, 1)
            conn.close()

    def test_binance_buffered_depth_bridges_snapshot_and_replays(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect_scope_journal(Path(tmp) / "scope.sqlite3")
            _start(conn, session_id="B1", venue="BINANCE_SPOT", symbol="BTCUSDT", group="BINANCE_TRADES_DEPTH")

            depth = {
                "stream": "btcusdt@depth@100ms",
                "data": {
                    "e": "depthUpdate",
                    "E": 1000,
                    "s": "BTCUSDT",
                    "U": 101,
                    "u": 101,
                    "b": [["100", "1"]],
                    "a": [["102", "1"]],
                },
            }
            snapshot = {
                "lastUpdateId": 100,
                "bids": [["99", "2"]],
                "asks": [["101", "2"]],
            }
            trade = {
                "stream": "btcusdt@aggTrade",
                "data": {
                    "e": "aggTrade",
                    "E": 1002,
                    "s": "BTCUSDT",
                    "a": 7,
                    "p": "100",
                    "q": "1",
                    "T": 1001,
                    "m": False,
                },
            }

            # Persist diff before snapshot to emulate official buffer-then-snapshot chronology.
            _ingest(
                conn, session_id="B1", venue="BINANCE_SPOT", symbol="BTCUSDT",
                kind="BINANCE_DEPTH_DIFF", channel="btcusdt@depth@100ms", raw=depth,
                seq_first=101, seq_last=101, ordinal_clock=10,
            )
            _ingest(
                conn, session_id="B1", venue="BINANCE_SPOT", symbol="BTCUSDT",
                kind="BINANCE_DEPTH_SNAPSHOT", channel="REST_DEPTH_SNAPSHOT", raw=snapshot,
                seq_first=100, seq_last=100, ordinal_clock=20, transport="REST",
            )
            _ingest(
                conn, session_id="B1", venue="BINANCE_SPOT", symbol="BTCUSDT",
                kind="BINANCE_AGGTRADE", channel="btcusdt@aggTrade", raw=trade,
                seq_first=7, seq_last=7, ordinal_clock=30,
            )
            result = replay_binance_scope_session(conn, session_id="B1")
            self.assertTrue(result.ok, result.failure_reason)
            self.assertEqual(result.final_sequence, 101)
            conn.close()

    def test_binance_gap_after_snapshot_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn = connect_scope_journal(Path(tmp) / "scope.sqlite3")
            _start(conn, session_id="B1", venue="BINANCE_SPOT", symbol="BTCUSDT", group="BINANCE_TRADES_DEPTH")
            snapshot = {"lastUpdateId": 100, "bids": [["99", "2"]], "asks": [["101", "2"]]}
            depth = {
                "stream": "btcusdt@depth@100ms",
                "data": {"e": "depthUpdate", "E": 1000, "s": "BTCUSDT", "U": 102, "u": 102, "b": [["100", "1"]], "a": []},
            }
            trade = {
                "stream": "btcusdt@aggTrade",
                "data": {"e": "aggTrade", "E": 1002, "s": "BTCUSDT", "a": 7, "p": "100", "q": "1", "T": 1001, "m": False},
            }
            _ingest(conn, session_id="B1", venue="BINANCE_SPOT", symbol="BTCUSDT", kind="BINANCE_DEPTH_SNAPSHOT", channel="REST_DEPTH_SNAPSHOT", raw=snapshot, seq_first=100, seq_last=100, ordinal_clock=10, transport="REST")
            _ingest(conn, session_id="B1", venue="BINANCE_SPOT", symbol="BTCUSDT", kind="BINANCE_DEPTH_DIFF", channel="btcusdt@depth@100ms", raw=depth, seq_first=102, seq_last=102, ordinal_clock=20)
            _ingest(conn, session_id="B1", venue="BINANCE_SPOT", symbol="BTCUSDT", kind="BINANCE_AGGTRADE", channel="btcusdt@aggTrade", raw=trade, seq_first=7, seq_last=7, ordinal_clock=30)
            result = replay_binance_scope_session(conn, session_id="B1")
            self.assertFalse(result.ok)
            self.assertEqual(result.failure_reason, "BookSequenceGap")
            conn.close()


if __name__ == "__main__":
    unittest.main()

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
    finish_scope_session,
    ingest_scope_record,
    start_scope_session,
)
from h02_scope_recovery import verify_scope_batch


def start(conn, sid, venue, symbol, group, batch="BATCH"):
    start_scope_session(
        conn,
        session_id=sid,
        batch_id=batch,
        collector_version="TEST",
        venue=venue,
        native_symbol=symbol,
        stream_group=group,
        endpoint="public://synthetic",
        started_wall_ns=1,
        started_monotonic_ns=2,
    )


def ingest(conn, sid, venue, symbol, kind, channel, payload, seq1, seq2, clock, transport="WEBSOCKET"):
    ingest_scope_record(
        conn,
        session_id=sid,
        venue=venue,
        native_symbol=symbol,
        transport=transport,
        message_kind=kind,
        channel=channel,
        sequence_first=seq1,
        sequence_last=seq2,
        source_time_min_ns=clock if transport == "WEBSOCKET" else None,
        source_time_max_ns=clock if transport == "WEBSOCKET" else None,
        collector_wall_ns=clock,
        collector_monotonic_ns=clock + 1,
        raw_payload=json.dumps(payload, separators=(",", ":")).encode(),
    )


def add_binance(conn, sid, symbol):
    low=symbol.lower()
    snapshot={"lastUpdateId":100,"bids":[["99","2"]],"asks":[["101","2"]]}
    depth={"stream":f"{low}@depth@100ms","data":{"e":"depthUpdate","E":1000,"s":symbol,"U":101,"u":101,"b":[["100","1"]],"a":[["102","1"]]}}
    trade={"stream":f"{low}@aggTrade","data":{"e":"aggTrade","E":1002,"s":symbol,"a":7,"p":"100","q":"1","T":1001,"m":False}}
    ingest(conn,sid,"BINANCE_SPOT",symbol,"BINANCE_DEPTH_DIFF",f"{low}@depth@100ms",depth,101,101,10)
    ingest(conn,sid,"BINANCE_SPOT",symbol,"BINANCE_DEPTH_SNAPSHOT","REST_DEPTH_SNAPSHOT",snapshot,100,100,20,"REST")
    ingest(conn,sid,"BINANCE_SPOT",symbol,"BINANCE_AGGTRADE",f"{low}@aggTrade",trade,7,7,30)
    finish_scope_session(conn,session_id=sid,ended_wall_ns=40,status="PASS")


def add_cb_l2(conn, sid, product):
    control={"channel":"subscriptions","timestamp":"2026-09-26T18:00:00Z","sequence_num":0,"events":[{"subscriptions":{"level2":[product]}}]}
    snap={"channel":"l2_data","timestamp":"2026-09-26T18:00:01Z","sequence_num":1,"events":[{"type":"snapshot","product_id":product,"updates":[{"side":"bid","event_time":"1970-01-01T00:00:00Z","price_level":"99","new_quantity":"2"},{"side":"ask","event_time":"1970-01-01T00:00:00Z","price_level":"101","new_quantity":"2"}]}]}
    upd={"channel":"l2_data","timestamp":"2026-09-26T18:00:02Z","sequence_num":2,"events":[{"type":"update","product_id":product,"updates":[{"side":"bid","event_time":"2026-09-26T18:00:02Z","price_level":"100","new_quantity":"1"}]}]}
    ingest(conn,sid,"COINBASE_ADVANCED_SPOT",product,"COINBASE_CONTROL","subscriptions",control,0,0,10)
    ingest(conn,sid,"COINBASE_ADVANCED_SPOT",product,"COINBASE_LEVEL2","l2_data",snap,1,1,20)
    ingest(conn,sid,"COINBASE_ADVANCED_SPOT",product,"COINBASE_LEVEL2","l2_data",upd,2,2,30)
    finish_scope_session(conn,session_id=sid,ended_wall_ns=40,status="PASS")


def add_cb_trades(conn, sid, product):
    control={"channel":"subscriptions","timestamp":"2026-09-26T18:00:00Z","sequence_num":0,"events":[{"subscriptions":{"market_trades":[product]}}]}
    trade={"channel":"market_trades","timestamp":"2026-09-26T18:00:01Z","sequence_num":1,"events":[{"type":"update","trades":[{"trade_id":"1","product_id":product,"price":"100","size":"1","side":"SELL","time":"2026-09-26T18:00:01Z"}]}]}
    ingest(conn,sid,"COINBASE_ADVANCED_SPOT",product,"COINBASE_CONTROL","subscriptions",control,0,0,10)
    ingest(conn,sid,"COINBASE_ADVANCED_SPOT",product,"COINBASE_MARKET_TRADES","market_trades",trade,1,1,20)
    finish_scope_session(conn,session_id=sid,ended_wall_ns=30,status="PASS")


def build_full_batch(conn):
    for sid,symbol in (("B-BTC","BTCUSDT"),("B-ETH","ETHUSDT")):
        start(conn,sid,"BINANCE_SPOT",symbol,"BINANCE_TRADES_DEPTH")
        add_binance(conn,sid,symbol)
    for prefix,product in (("BTC","BTC-USD"),("ETH","ETH-USD")):
        sid=f"C-{prefix}-L2"
        start(conn,sid,"COINBASE_ADVANCED_SPOT",product,"COINBASE_LEVEL2")
        add_cb_l2(conn,sid,product)
        sid=f"C-{prefix}-TR"
        start(conn,sid,"COINBASE_ADVANCED_SPOT",product,"COINBASE_MARKET_TRADES")
        add_cb_trades(conn,sid,product)


class H02ScopeBatchTests(unittest.TestCase):
    def test_exact_six_session_batch_passes_and_survives_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"scope.sqlite3"
            conn=connect_scope_journal(path)
            build_full_batch(conn)
            first=verify_scope_batch(conn,batch_id="BATCH")
            self.assertTrue(first.ok, first.blockers)
            self.assertEqual(first.session_count,6)
            self.assertEqual(first.passed_session_count,6)
            conn.close()

            conn=connect_scope_journal(path)
            second=verify_scope_batch(conn,batch_id="BATCH")
            self.assertEqual(first,second)
            conn.close()

    def test_missing_frozen_scope_session_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=connect_scope_journal(Path(tmp)/"scope.sqlite3")
            start(conn,"B-BTC","BINANCE_SPOT","BTCUSDT","BINANCE_TRADES_DEPTH")
            add_binance(conn,"B-BTC","BTCUSDT")
            result=verify_scope_batch(conn,batch_id="BATCH")
            self.assertFalse(result.ok)
            self.assertIn("FROZEN_SCOPE_SESSION_SET_MISMATCH",result.blockers)
            conn.close()

    def test_terminal_nonpass_session_blocks_batch(self):
        with tempfile.TemporaryDirectory() as tmp:
            conn=connect_scope_journal(Path(tmp)/"scope.sqlite3")
            build_full_batch(conn)
            conn.execute("UPDATE scope_sessions SET status='FAIL_CLOSED' WHERE session_id='C-ETH-TR'")
            conn.commit()
            result=verify_scope_batch(conn,batch_id="BATCH")
            self.assertFalse(result.ok)
            self.assertTrue(any(x.startswith("SESSION_STATUS_NOT_PASS:") for x in result.blockers))
            conn.close()


if __name__=="__main__":
    unittest.main()

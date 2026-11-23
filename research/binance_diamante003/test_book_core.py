#!/usr/bin/env python3
"""Offline fail-closed independent regression: zero network and no price forecasting."""
import hashlib
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from book_core import Journal, LocalBook, SYMBOLS, event_validation, replay, positive
from capture import rest_url, WSS

T = 1795412915000

def snap(seq=100):
    return {"lastUpdateId":seq,"bids":[["99","2"],["98","4"]],"asks":[["101","3"],["102","5"]]}

def depth(U=101,u=101,s="BTCUSDT",b=None,a=None):
    return {"e":"depthUpdate","E":T,"s":s,"U":U,"u":u,
            "b":b if b is not None else [["99","1.5"]],
            "a":a if a is not None else [["101","4"]]}

def trade(a=101,s="BTCUSDT",buyer_maker=True):
    return {"e":"aggTrade","E":T,"s":s,"a":a,"p":"100","q":"0.1",
            "f":200,"l":200,"T":T-20,"m":buyer_maker}

class ValidationTests(unittest.TestCase):
    def test_positive(self):self.assertEqual(str(positive("1.2")),"1.2")
    def test_nan_rejected(self):
        with self.assertRaises(ValueError):positive("NaN")
    def test_zero_rejected(self):
        with self.assertRaises(ValueError):positive("0")
    def test_symbol_whitelist(self):
        with self.assertRaises(ValueError):LocalBook("DOGEUSDT")
    def test_bad_future_symbol(self):
        with self.assertRaisesRegex(ValueError,"WRONG_EVENT_SYMBOL"):
            event_validation(depth(s="ETHUSDT"),"BTCUSDT")
    def test_millisecond_field_rejected(self):
        x=depth();x["E"]=1795412915000000
        with self.assertRaisesRegex(ValueError,"MILLISECONDS"):
            event_validation(x,"BTCUSDT")
    def test_invalid_update_range(self):
        x=depth(103,102)
        with self.assertRaisesRegex(ValueError,"DEPTH_RANGE"):
            event_validation(x,"BTCUSDT")
    def test_wrong_trade_side_type(self):
        x=trade();x["m"]=1
        with self.assertRaisesRegex(ValueError,"SIDE"):
            event_validation(x,"BTCUSDT")
    def test_public_snapshot_route(self):
        self.assertTrue(rest_url("BTCUSDT").startswith("https://data-api.binance.vision/api/v3/depth?"))
        self.assertIn("data-stream.binance.vision",WSS)
        with self.assertRaisesRegex(ValueError,"UNAUTHORIZED"):rest_url("ETHBTC")

class BookTests(unittest.TestCase):
    def test_buffer_then_bridge(self):
        b=LocalBook("BTCUSDT")
        b.ingest(depth(U=99,u=101))
        self.assertEqual(b.status,"BUFFERING")
        b.snapshot(snap(100))
        self.assertEqual(b.status,"SYNCED")
        self.assertEqual(b.last_update_id,101)
        self.assertEqual(b.depth_applied,1)
        self.assertEqual(b.summary()["best_bid"],"99")
    def test_gap_stops_forever(self):
        b=LocalBook("BTCUSDT")
        b.ingest(depth(101,101));b.snapshot(snap())
        b.ingest(depth(103,103))
        self.assertEqual(b.status,"SOURCE_BLOCKED")
        self.assertEqual(b.failure,"SEQUENCE_GAP_NO_RESTART")
        before=b.last_update_id
        b.ingest(depth(102,102))
        self.assertEqual(b.last_update_id,before)
    def test_missing_buffer_first_depth_fails(self):
        b=LocalBook("BTCUSDT")
        b.ingest(depth(104,104));b.snapshot(snap(100))
        self.assertEqual(b.status,"SOURCE_BLOCKED")
    def test_stale_depth_ignored(self):
        b=LocalBook("BTCUSDT");b.ingest(depth(101,101));b.snapshot(snap())
        b.ingest(depth(101,101))
        self.assertEqual(b.stale_depth,1)
        self.assertEqual(b.depth_applied,1)
    def test_zero_qty_removes_level_not_order_cancel(self):
        b=LocalBook("BTCUSDT")
        b.ingest(depth(101,101,b=[["98","0"]],a=[]));b.snapshot(snap())
        self.assertEqual(b.level_removed,1)
        self.assertTrue(b.summary()["removal_not_identical_to_cancellation"])
    def test_unseen_zero_removal_is_not_error(self):
        b=LocalBook("BTCUSDT")
        b.ingest(depth(101,101,b=[["97","0"]],a=[]));b.snapshot(snap())
        self.assertEqual(b.level_removed,0)
        self.assertEqual(b.status,"SYNCED")
    def test_crossed_book_blocked(self):
        b=LocalBook("BTCUSDT")
        b.ingest(depth(101,101,b=[["104","2"]],a=[]));b.snapshot(snap())
        self.assertEqual(b.status,"SOURCE_BLOCKED")
        self.assertIn("CROSSED",b.failure)
    def test_snapshot_order_rejected(self):
        bad=snap();bad["bids"][1][0]="100"
        b=LocalBook("BTCUSDT");b.snapshot(bad)
        self.assertEqual(b.status,"SOURCE_BLOCKED")
    def test_trades_flag_and_ids(self):
        b=LocalBook("BTCUSDT")
        b.ingest(trade(1,buyer_maker=True))
        b.ingest(trade(2,buyer_maker=False))
        self.assertEqual(b.aggressive_buys,1)
        self.assertEqual(b.aggressive_sells,1)
        b.ingest(trade(2,buyer_maker=False))
        self.assertEqual(b.status,"SOURCE_BLOCKED")
    def test_snapshot_id_ahead_of_all_buffer(self):
        b=LocalBook("BTCUSDT")
        b.ingest(depth(101,101))
        b.snapshot(snap(105))
        self.assertEqual(b.status,"SYNCED")
        self.assertEqual(b.stale_depth,1)
        b.ingest(depth(106,106))
        self.assertEqual(b.last_update_id,106)

class JournalTests(unittest.TestCase):
    def test_exact_raw_chain_and_replay(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"raw.jsonl"; j=Journal(path)
            msg1=json.dumps({"stream":"btcusdt@depth@100ms","data":depth(101,101)})
            snapshot=json.dumps(snap(100))
            msg2=json.dumps({"stream":"btcusdt@aggTrade","data":trade(23)})
            j.append(kind="ws",symbol="BTCUSDT",raw=msg1,utc_ns=101,mono_ns=201)
            j.append(kind="snapshot",symbol="BTCUSDT",raw=snapshot,utc_ns=102,mono_ns=202)
            j.append(kind="ws",symbol="BTCUSDT",raw=msg2,utc_ns=103,mono_ns=203)
            j.close()
            result=replay(path)
            self.assertEqual(result["last_chain_hash"],j.prev)
            self.assertEqual(result["events"],3)
            self.assertEqual(result["books"]["BTCUSDT"]["status"],"SYNCED")
            self.assertEqual(result["books"]["BTCUSDT"]["aggtrades"],1)
    def test_payload_tamper_detected(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"raw.jsonl";j=Journal(path)
            raw=json.dumps({"stream":"btcusdt@depth@100ms","data":depth(101,101)})
            j.append(kind="ws",symbol="BTCUSDT",raw=raw,utc_ns=1,mono_ns=2);j.close()
            changed=path.read_text().replace("99","98",1)
            path.write_text(changed)
            with self.assertRaisesRegex(ValueError,"TAMPERED_JOURNAL_RAW"):replay(path)
    def test_sequence_reorder_detected(self):
        with tempfile.TemporaryDirectory() as root:
            path=Path(root)/"raw.jsonl";j=Journal(path)
            raw=json.dumps({"stream":"btcusdt@aggTrade","data":trade(1)})
            j.append(kind="ws",symbol="BTCUSDT",raw=raw,utc_ns=1,mono_ns=2)
            j.append(kind="ws",symbol="BTCUSDT",raw=raw,utc_ns=3,mono_ns=4);j.close()
            lines=path.read_text().splitlines()
            path.write_text(lines[1]+"\n"+lines[0]+"\n")
            with self.assertRaisesRegex(ValueError,"BROKEN_JOURNAL_CHAIN"):replay(path)

if __name__ == "__main__":
    unittest.main()

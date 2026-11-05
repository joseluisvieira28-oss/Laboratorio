"""Synthetic attacks against independent V2.3 forensic source auditor.

No network, historical price data or exchange accounts.
"""
import unittest
from audit_v23 import Parity, Independent

BASE=1793857705959

def rec(seq,venue="bybit",kind="frame",t=1.,raw=None):
    import json
    return {"seq":seq,"venue":venue,"kind":kind,"segment":1,
            "elapsed":t,"mono_ns":int(t*1e9)+100000000,
            "utc_ms":BASE+int(t*1000),"raw":json.dumps(raw) if not isinstance(raw,str) else raw}

def m1(u=50,seq=100,bid="99",ask="101"):
    return {"topic":"orderbook.1.BTCUSDT","type":"snapshot",
            "ts":BASE+1000,
            "data":{"s":"BTCUSDT","seq":seq,"u":u,
                    "b":[[bid,"1"]],"a":[[ask,"1"]]}}

def m50(u=100,seq=110,typ="snapshot",b=None,a=None):
    return {"topic":"orderbook.50.BTCUSDT","type":typ,
            "ts":BASE+1000,
            "data":{"s":"BTCUSDT","seq":seq,"u":u,
                    "b":b if b is not None else [["99","1"]],
                    "a":a if a is not None else [["101","1"]]}}

class ParityOfflineThreats(unittest.TestCase):
    def setUp(self):
        self.p=Parity()
        self.p.feed(rec(1,kind="connect",t=0,raw="url"))

    def test_stable_cross_seq_matches_both_sides(self):
        self.p.feed(rec(2,t=1.00,raw=m1(50,100)))
        self.p.feed(rec(3,t=1.05,raw=m50(400,110)))
        self.p.feed(rec(4,t=1.10,raw=m1(51,120)))
        q=self.p.measure()
        self.assertEqual(q["stable_brackets"],1)
        self.assertEqual(q["price_parity_match"],1)
        self.assertEqual(q["price_parity_mismatch"],0)
    def test_same_sequence_time_anchors_different_prices_not_compared(self):
        self.p.feed(rec(2,t=1,raw=m1(50,100)))
        self.p.feed(rec(3,t=1.05,raw=m50(400,110)))
        self.p.feed(rec(4,t=1.1,raw=m1(51,120,ask="102")))
        q=self.p.measure()
        self.assertEqual(q["stable_brackets"],0)
        self.assertEqual(q["moving_l1_anchor"],1)
    def test_differing_anchored_bid_ask_counts_mismatch(self):
        self.p.feed(rec(2,t=1,raw=m1(50,100)))
        self.p.feed(rec(3,t=1.05,raw=m50(400,110,
                                    b=[["98","1"]],a=[["101","1"]])))
        self.p.feed(rec(4,t=1.1,raw=m1(51,120)))
        q=self.p.measure()
        self.assertEqual(q["stable_brackets"],1)
        self.assertEqual(q["price_parity_mismatch"],1)
    def test_outside_200ms_is_uncomparable_not_match(self):
        self.p.feed(rec(2,t=1,raw=m1(50,100)))
        self.p.feed(rec(3,t=1.25,raw=m50(400,110)))
        self.p.feed(rec(4,t=1.5,raw=m1(51,120)))
        q=self.p.measure()
        self.assertEqual(q["stable_brackets"],0)
        self.assertEqual(q["not_within_200ms"],1)
    def test_consecutive_l50_u_and_seq_accepted(self):
        self.p.feed(rec(2,t=1,raw=m50(100,110)))
        self.p.feed(rec(3,t=1.02,raw=m50(101,115,"delta",[],[])))
        self.assertEqual(self.p.deltas,1)
        self.assertEqual(self.p.gaps,0)
        self.assertTrue(self.p.ready)
    def test_delta_u_gap_is_not_silently_applied(self):
        self.p.feed(rec(2,t=1,raw=m50(100,110)))
        self.p.feed(rec(3,t=1.02,raw=m50(102,115,"delta",[],[])))
        self.assertEqual(self.p.gaps,1)
        self.assertFalse(self.p.ready)
        self.assertEqual(self.p.deltas,0)
        self.assertEqual(self.p.errors[0]["reason"],"L50_U_NOT_CONSECUTIVE")
    def test_after_gap_deltas_discarded_until_snapshot(self):
        self.p.feed(rec(2,t=1,raw=m50(100,110)))
        self.p.feed(rec(3,t=1.02,raw=m50(102,115,"delta",[],[])))
        self.p.feed(rec(4,t=1.04,raw=m50(103,117,"delta",[],[])))
        self.assertEqual(self.p.after_gap_without_snapshot,1)
        self.assertEqual(self.p.deltas,0)
        self.p.feed(rec(5,t=1.06,raw=m50(200,201,"snapshot")))
        self.assertTrue(self.p.ready)
    def test_l50_crossed_book_fails_closed(self):
        self.p.feed(rec(2,t=1,raw=m50(100,110)))
        self.p.feed(rec(3,t=1.02,raw=m50(101,115,"delta",
                                    [["102","1"]],[])))
        self.assertEqual(self.p.badbooks,1)
        self.assertFalse(self.p.ready)
    def test_snapshot_resets_old_book(self):
        self.p.feed(rec(2,t=1,raw=m50(100,110,
                             b=[["99","1"],["98","2"]],a=[["101","1"]])))
        self.p.feed(rec(3,t=1.05,raw=m50(200,220,"snapshot",
                             b=[["95","1"]],a=[["96","1"]])))
        self.assertEqual(max(self.p.bid),95)
        self.assertEqual(self.p.snapshots,2)
    def test_seq_regression_rejects_delta(self):
        self.p.feed(rec(2,t=1,raw=m50(100,110)))
        self.p.feed(rec(3,t=1.02,raw=m50(101,109,"delta",[],[])))
        self.assertEqual(self.p.sequence_reversals,1)
        self.assertFalse(self.p.ready)
    def test_cross_connect_does_not_join_l1_anchors(self):
        self.p.feed(rec(2,t=1,raw=m1(50,100)))
        self.p.feed(rec(3,t=1.05,raw=m50(400,110)))
        self.p.feed(rec(4,kind="connect",t=1.07,raw="new url"))
        self.p.feed(rec(5,t=1.10,raw=m1(51,120)))
        q=self.p.measure()
        self.assertEqual(q["stable_brackets"],0)
        self.assertEqual(q["no_seq_bracket"],1)
    def test_u1_without_new_snapshot_invalidates_l50(self):
        self.p.feed(rec(2,t=1,raw=m50(100,110)))
        self.p.feed(rec(3,t=1.05,raw=m50(1,115,"delta",[],[])))
        self.assertEqual(self.p.u1_resets,1)
        self.assertFalse(self.p.ready)
        self.p.feed(rec(4,t=1.10,raw=m50(2,120,"delta",[],[])))
        self.assertEqual(self.p.after_gap_without_snapshot,1)
    def test_wrong_source_timestamp_invalidated(self):
        x=m50();x["ts"]=BASE-30000
        self.p.feed(rec(2,t=1,raw=x))
        self.assertFalse(self.p.ready)
        self.assertEqual(self.p.errors[0]["reason"],"SOURCE_TIMESTAMP")
    def test_independent_grid_900_seconds_no_fake_pnl(self):
        r=Independent();r.finish()
        self.assertEqual(len(r.good),0)
        self.assertEqual(r.nexttick,901)

if __name__=="__main__":unittest.main(verbosity=2)

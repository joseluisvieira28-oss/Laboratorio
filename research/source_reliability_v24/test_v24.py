#!/usr/bin/env python3
"""Synthetic-only fault injection for V2.4; NEVER market or profitability evidence."""
import unittest
from decimal import Decimal
import json
from source_guard import SafeL50,Blocked,live_enabled
from audit_v24 import LiquidationStress,window_quality,stress_brackets

T=1_000_000_000
def book(u=100,seq=1000,typ="snapshot",ts=T,b=None,a=None):
    return {"topic":"orderbook.50.BTCUSDT","type":typ,"ts":ts,
        "data":{"s":"BTCUSDT","u":u,"seq":seq,
                "b":[["99","1"],["98","1"]] if b is None else b,
                "a":[["101","1"],["102","1"]] if a is None else a}}
def child(t,side="Buy",size="1",price="100000"):
    return {"T":t,"s":"BTCUSDT","S":side,"v":size,"p":price}
def liq_record(seq,elapsed,children,ts=None):
    rtime=T+round(elapsed*1000)
    m={"topic":"allLiquidation.BTCUSDT","type":"snapshot","ts":ts or rtime,
       "data":children}
    return {"seq":seq,"venue":"bybit","kind":"frame",
            "elapsed":elapsed,"utc_ms":rtime,"raw":json.dumps(m)}

class SafeReconstruction(unittest.TestCase):
    def setUp(self):self.a=SafeL50()
    def warm(self):
        self.assertEqual(self.a.event(book(),T),"QUARANTINED")
        self.assertEqual(self.a.event(book(101,1001,"delta",T+30005,[],[]),T+30005),
                         "SOURCE_READY")
    def test_initial_snapshot_quarantined_for_30_seconds(self):
        self.assertEqual(self.a.event(book(),T),"QUARANTINED")
        with self.assertRaisesRegex(Blocked,"SOURCE_NOT_READY"):self.a.quote(T+100)
        self.assertGreaterEqual(self.a.ready_after_ms,T+30000)
    def test_success_requires_real_snapshot_and_new_delta_after_quarantine(self):
        self.warm()
        self.assertEqual(self.a.quote(T+30006)["u"],101)
    def test_missing_u_plus_two_fails_closed_and_needs_resubscribe(self):
        self.warm()
        self.assertEqual(self.a.event(book(103,1002,"delta",T+30006,[],[]),T+30006),
                         "RECONNECT_AND_RESUBSCRIBE_REQUIRED")
        self.assertTrue(self.a.resubscribe_required)
        self.assertEqual(self.a.incidents[-1]["reason"],"MISSING_L50_UPDATE_ID")
        with self.assertRaisesRegex(Blocked,"SOURCE_NOT_READY"):self.a.quote(T+30007)
    def test_after_gap_delta_never_reanimates_old_book(self):
        self.warm()
        self.a.event(book(103,1002,"delta",T+30006,[],[]),T+30006)
        self.assertEqual(self.a.event(book(104,1003,"delta",T+30007,[],[]),T+30007),
                         "IGNORE_DELTA_UNTIL_NEW_SNAPSHOT")
        self.assertEqual(self.a.state,"AWAIT_SNAPSHOT")
    def test_after_gap_snapshot_rearms_only_after_new_quarantine(self):
        self.warm()
        self.a.event(book(103,1002,"delta",T+30006,[],[]),T+30006)
        self.assertEqual(self.a.event(book(200,2000,"snapshot",T+30010),T+30010),"QUARANTINED")
        self.assertEqual(self.a.event(book(201,2001,"delta",T+60000,[],[]),T+60000),"QUARANTINED")
        self.assertEqual(self.a.event(book(202,2002,"delta",T+60011,[],[]),T+60011),"SOURCE_READY")
        self.assertEqual(self.a.quote(T+60012)["u"],202)
    def test_u1_service_restart_fails_closed(self):
        self.warm()
        self.assertEqual(self.a.event(book(1,1100,"delta",T+30006,[],[]),T+30006),
                         "RECONNECT_AND_RESUBSCRIBE_REQUIRED")
    def test_seq_regression_fails_closed_not_gap_inferred(self):
        self.warm()
        self.a.event(book(102,1000,"delta",T+30006,[],[]),T+30006)
        self.assertEqual(self.a.incidents[-1]["reason"],"SEQ_REGRESSION")
    def test_crossed_book_not_submitted_as_valid_quote(self):
        self.warm()
        self.a.event(book(102,1002,"delta",T+30006,[["102","2"]],[]),T+30006)
        self.assertEqual(self.a.incidents[-1]["reason"],"CROSSED_OR_EMPTY")
        with self.assertRaisesRegex(Blocked,"SOURCE_NOT_READY"):self.a.quote(T+30007)
    def test_invalid_size_nan_freezes(self):
        self.warm()
        self.a.event(book(102,1002,"delta",T+30006,[["99","NaN"]],[]),T+30006)
        self.assertEqual(self.a.incidents[-1]["reason"],"INVALID_QUANTITY_OR_PRICE")
    def test_stale_publisher_clock_freezes(self):
        self.warm()
        self.a.event(book(102,1002,"delta",T-5000,[],[]),T+30006)
        self.assertEqual(self.a.incidents[-1]["reason"],"STALE_OR_FUTURE_PUBLISHER")
    def test_stale_quote_fails_closed_and_requires_snapshot(self):
        self.warm()
        with self.assertRaisesRegex(Blocked,"STALE_BOOK_QUARANTINED"):
            self.a.quote(T+31007)
        self.assertTrue(self.a.resubscribe_required)
    def test_no_live_transport(self):
        self.assertFalse(live_enabled())

class SourcePower(unittest.TestCase):
    def test_per_10minute_exact_threshold_accept(self):
        # 570 first window, 600 each subsequent = >=540 every window
        good=list(range(31,601))
        for w in range(1,12):
            good.extend(range(w*600+1,(w+1)*600+1))
        windows,bad=window_quality(good)
        self.assertEqual(len(windows),12)
        self.assertEqual(bad,[])
        self.assertEqual(windows[0]["joint_good"],570)
    def test_single_very_bad_window_fails_despite_high_total(self):
        good=[]
        for w in range(12):
            limit=530 if w==7 else 600
            good.extend(range(w*600+1,w*600+limit+1))
        windows,bad=window_quality(good)
        self.assertEqual(sum(w["joint_good"] for w in windows),7130)
        self.assertEqual(bad,[7])
    def test_boundary_no_duplicate_second(self):
        windows,_=window_quality([600,601,1200,1201])
        self.assertEqual([w["joint_good"] for w in windows[:3]],[1,2,1])

class LiquidationAttack(unittest.TestCase):
    def test_two_unique_liquidations_same_side_create_one_cluster(self):
        x=LiquidationStress()
        x.feed(liq_record(1,1,[child(T+1000,size=".7")]))
        x.feed(liq_record(2,2,[child(T+2000,size=".7")]))
        self.assertEqual(len(x.events),2)
        self.assertEqual(len(x.clusters),1)
        self.assertEqual(x.clusters[0]["side"],"Buy")
    def test_exact_duplicate_child_not_counted_twice(self):
        x=LiquidationStress()
        rec=liq_record(1,1,[child(T+1000,size="2")])
        x.feed(rec);x.feed({**rec,"seq":2})
        self.assertEqual(len(x.events),1)
        self.assertEqual(x.duplicates,1)
        self.assertEqual(len(x.clusters),0)
    def test_opposite_side_not_merged_into_cluster(self):
        x=LiquidationStress()
        x.feed(liq_record(1,1,[child(T+1000,size="1",side="Buy")]))
        x.feed(liq_record(2,2,[child(T+2000,size="1",side="Sell")]))
        self.assertEqual(len(x.clusters),0)
    def test_second_cluster_needs_60s_separation(self):
        x=LiquidationStress()
        for idx,t in enumerate([1,2,3,4,63,64],1):
            x.feed(liq_record(idx,t,[child(T+int(t*1000),size="1")]))
        self.assertEqual(len(x.clusters),2)
    def test_malformed_side_quarantined_as_invalid_event(self):
        x=LiquidationStress()
        x.feed(liq_record(1,1,[child(T+1000,side="WRONG")]))
        self.assertEqual(len(x.events),0)
        self.assertEqual(x.invalid[0]["error"],"LIQ_DIRECTION")
    def test_event_timestamp_too_old_is_invalid(self):
        x=LiquidationStress()
        x.feed(liq_record(1,1,[child(T-3000)]))
        self.assertEqual(x.invalid[0]["error"],"LIQ_EVENT_CLOCK")
    def test_zero_quantity_rejected(self):
        x=LiquidationStress()
        x.feed(liq_record(1,1,[child(T+1000,size="0")]))
        self.assertEqual(x.invalid[0]["error"],"BAD_SIZE_OR_PRICE")
    def test_nan_notional_rejected(self):
        x=LiquidationStress()
        x.feed(liq_record(1,1,[child(T+1000,price="NaN")]))
        self.assertEqual(x.invalid[0]["error"],"BAD_SIZE_OR_PRICE")

if __name__=="__main__":
    unittest.main(verbosity=2)

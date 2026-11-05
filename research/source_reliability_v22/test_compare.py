"""Adversarial source-only synthetic tests (NEVER economic episodes)."""
import copy
import unittest
from compare import L50,L1,PairObserver,SourceFault,timestamp,live_enabled,WINDOW

BASE=1793850000000
MONO=123456789000000000

def ob50(u=100,seq=1000,typ="snapshot",b=None,a=None):
    if b is None:b=[["99","1"],["98","1"]]
    if a is None:a=[["101","1"],["102","1"]]
    return {"topic":"orderbook.50.BTCUSDT","type":typ,"ts":BASE,
            "data":{"s":"BTCUSDT","u":u,"seq":seq,"b":b,"a":a}}
def ob1(u=4):
    return {"topic":"orderbook.1.BTCUSDT","type":"snapshot","ts":BASE,
            "data":{"s":"BTCUSDT","u":u,"b":[["99","1"]],"a":[["101","1"]]}}
def mexc(v=1):
    return {"channel":"push.depth.full","symbol":"BTC_USDT","ts":BASE,
      "data":{"version":v,"bids":[[str(99-i),"1"] for i in range(5)],
              "asks":[[str(101+i),"1"] for i in range(5)]}}

class Book50Regressions(unittest.TestCase):
    def setUp(self):self.b=L50()
    def test_requires_snapshot_before_deltas(self):
        self.assertEqual(self.b.consume(ob50(5,5,"delta",[],[])),"WAIT_FOR_SNAPSHOT")
        self.assertFalse(self.b.ready)
    def test_snapshot_rebuild_then_delta_deletes_and_adds(self):
        self.assertEqual(self.b.consume(ob50()),"SNAPSHOT")
        self.assertEqual(self.b.consume(ob50(101,1001,"delta",
                       [["99","0"],["97","2"]],[["100.5","1"]])),"DELTA")
        self.assertEqual(max(self.b.bids),98)
        self.assertEqual(min(self.b.asks),100.5)
    def test_out_of_sequence_u_fails_closed(self):
        self.b.consume(ob50())
        with self.assertRaisesRegex(SourceFault,"BOOK_VERSION_OR_SEQUENCE"):
            self.b.consume(ob50(99,1001,"delta",[],[]))
        self.assertFalse(self.b.ready)
    def test_out_of_sequence_seq_fails_closed(self):
        self.b.consume(ob50())
        with self.assertRaisesRegex(SourceFault,"BOOK_VERSION_OR_SEQUENCE"):
            self.b.consume(ob50(101,999,"delta",[],[]))
    def test_service_restart_u1_needs_new_snapshot(self):
        self.b.consume(ob50())
        self.assertEqual(self.b.consume(ob50(1,2000,"delta",[],[])),
                         "RESET_U1_NEEDS_SNAPSHOT")
        self.assertFalse(self.b.ready)
        self.b.consume(ob50(2,2001,"snapshot"))
        self.assertTrue(self.b.ready)
    def test_snapshot_replace_removes_old_levels(self):
        self.b.consume(ob50())
        self.b.consume(ob50(300,5000,"snapshot",[["80","1"]],[["82","1"]]))
        self.assertEqual(max(self.b.bids),80)
    def test_zero_qty_delete_can_empty_side_and_fails(self):
        self.b.consume(ob50(100,1000,"snapshot",[["99","1"]],[["101","1"]]))
        with self.assertRaisesRegex(SourceFault,"CROSSED_OR_EMPTY_BOOK"):
            self.b.consume(ob50(101,1001,"delta",[["99","0"]],[]))
        self.assertFalse(self.b.ready)
    def test_crossed_delta_fails_closed(self):
        self.b.consume(ob50())
        with self.assertRaisesRegex(SourceFault,"CROSSED_OR_EMPTY_BOOK"):
            self.b.consume(ob50(101,1001,"delta",[["102","1"]],[]))
        self.assertFalse(self.b.ready)
    def test_bad_negative_or_nan_qty(self):
        self.b.consume(ob50())
        with self.assertRaisesRegex(SourceFault,"NONPOSITIVE_DECIMAL"):
            self.b.consume(ob50(101,1001,"delta",[["99","NaN"]],[]))
    def test_duplicate_price_on_same_message(self):
        with self.assertRaisesRegex(SourceFault,"DUPLICATE_PRICE"):
            self.b.consume(ob50(b=[["99","1"],["99","2"]]))

class L1Regressions(unittest.TestCase):
    def test_same_u_duplicate_no_refresh_in_control(self):
        a=L1(False)
        self.assertEqual(a.consume(ob1(),31),"CHANGED")
        self.assertEqual(a.consume(ob1(),32),"DUPLICATE_IGNORED")
        self.assertEqual(a.last,31)
    def test_same_u_duplicate_refreshes_diagnostic_only(self):
        b=L1(True)
        b.consume(ob1(),31)
        self.assertEqual(b.consume(ob1(),32),"DUPLICATE_REFRESH")
        self.assertEqual(b.last,32)
    def test_same_u_changed_values_is_invalid(self):
        a=L1(False);a.consume(ob1(),31)
        x=ob1();x["data"]["b"][0][0]="98"
        with self.assertRaisesRegex(SourceFault,"L1_SAME_VERSION_CONFLICT"):
            a.consume(x,32)
    def test_l1_u1_resets_on_service_restart(self):
        a=L1(False);a.consume(ob1(100),31)
        self.assertEqual(a.consume(ob1(1),32),"CHANGED")
    def test_source_timestamp_future_is_not_joined(self):
        with self.assertRaisesRegex(SourceFault,"PUBLISHER_CLOCK"):
            timestamp(BASE+500,BASE)
    def test_source_timestamp_too_old_is_not_joined(self):
        with self.assertRaisesRegex(SourceFault,"PUBLISHER_CLOCK"):
            timestamp(BASE-2000,BASE)

class PairedGridRegressions(unittest.TestCase):
    def setUp(self):
        self.o=PairObserver();self.seq=0
    def feed(self,v,k,t,m,dt=0):
        import json
        self.seq+=1
        if isinstance(m,str):raw=m
        else:raw=json.dumps(m)
        r={"seq":self.seq,"mono_ns":MONO+round(t*1e9),
           "utc_ms":BASE+round(t*1000),"elapsed":t,
           "venue":v,"kind":k,"raw":raw,"segment":1}
        if k=="frame":
            # Ensure mock published time is as-of current receive.
            x=json.loads(raw)
            if "ts" in x:x["ts"]=r["utc_ms"]+dt
            r["raw"]=json.dumps(x)
        self.o.feed(r)
    def prime(self):
        self.feed("bybit","connect",.01,"url")
        self.feed("mexc","connect",.02,"url")
        self.feed("bybit","frame",.03,{"op":"subscribe","success":True})
        self.feed("mexc","frame",.04,{"channel":"rs.sub.depth.full","data":"success"})
        self.feed("bybit","frame",.05,{"op":"pong"})
        self.feed("mexc","frame",.06,{"channel":"pong"})
        self.feed("bybit","frame",30.01,ob1())
        self.feed("bybit","frame",30.02,ob50())
        self.feed("mexc","frame",30.03,mexc())
    def test_initial_warmup_never_count_good(self):
        self.prime()
        self.assertEqual(self.o.good["A"],0)
        self.assertEqual(self.o.good["B"],0)
        self.assertEqual(self.o.good["C"],0)
    def test_same_record_time_uses_causal_event_order(self):
        self.prime()
        self.feed("bybit","frame",30.51,{"op":"pong"})
        self.feed("mexc","frame",30.52,{"channel":"pong"})
        self.feed("bybit","frame",30.98,ob50(101,1001,"delta",[],[]))
        self.feed("mexc","frame",30.99,mexc(2))
        self.feed("bybit","frame",31.01,ob1())
        # At t=31, L1 from t=30.01 and L50 from t=30.98 and mexc 30.99
        self.assertEqual(self.o.good["C"],1)
        self.assertEqual(self.o.good["A"],1)
    def test_no_lookahead_future_book_does_not_fix_past_second(self):
        self.prime()
        self.feed("bybit","frame",32.1,ob50(101,1001,"delta",[],[]))
        # t=31 old book 30.02 still fresh, t=32 old >1s stale.
        self.assertEqual(self.o.good["C"],1)
        self.assertIn(32,self.o.bad["C"])
    def test_mexc_disconnect_invalidates_all(self):
        self.prime()
        self.feed("mexc","disconnect",31,{"exception":"simulated"})
        self.assertFalse(self.o.healthy("A",31.1))
        self.assertFalse(self.o.healthy("C",31.1))
    def test_bybit_duplicate_l1_only_b_refreshes(self):
        self.prime()
        self.feed("bybit","frame",30.7,ob1())
        self.assertLess(self.o.l1a.last,self.o.l1b.last)
        self.assertEqual(self.o.count["l1_DUPLICATE_IGNORED"],1)
    def test_invalid_book_quarantines_variants(self):
        self.prime()
        x=ob50(101,1001,"delta",[["102","1"]],[])
        self.feed("bybit","frame",30.2,x)
        self.assertGreater(self.o.quarantine["C"],30)
        self.assertFalse(self.o.l50.ready)
    def test_report_verdict_gate_does_not_claim_profit(self):
        self.o.good["C"]=600;self.o.good["A"]=500
        self.o.l50.snapshot_count=1
        rpt=self.o.report("WALL_LIMIT",600.5,1200)
        self.assertEqual(rpt["source_verdict"],"SOURCE_COMPARE_CANDIDATE")
        self.assertEqual(rpt["pnl"],"NOT_COMPUTED_SOURCE_ONLY")
        self.assertEqual(rpt["live_verdict"],"NO_LIVE_GO")
    def test_unmeasured_never_candidate(self):
        self.o.good["C"]=600;self.o.good["A"]=500
        self.o.l50.snapshot_count=1
        self.assertEqual(self.o.report("EARLY_TERMINATION",240,0)["source_verdict"],
                         "SOURCE_COMPARE_BLOCKED")

class NoBrokerTransport(unittest.TestCase):
    def test_live_is_hardcoded_false(self):self.assertIs(live_enabled(),False)

if __name__=="__main__":unittest.main(verbosity=2)

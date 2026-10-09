"""Synthetic-only causality / fill / overlap regression tests for LOR-RLE-001."""
import unittest
from datetime import datetime,timezone
import rle_engine_v01 as s

T=int(datetime(2023,3,1,tzinfo=timezone.utc).timestamp()*1000)
def bar(t,o=100,h=101,l=99,c=100):
    return s.Bar(t,o,h,l,c)

def long_sig(t=T):
    return s.Signal(t,1,"RLE_NARROW",101,99,5,6)

def short_sig(t=T):
    return s.Signal(t,-1,"RLE_NARROW",99,101,5,6)

class FakeArchive:
    def __init__(self,bars):
        self.bars=bars
    def minute(self,t):
        if t in self.bars:
            return self.bars[t]
        return bar(t,o=100,h=100.4,l=99.6,c=100)

class RLETests(unittest.TestCase):
    def test_forbid_future_month_2025(self):
        with self.assertRaises(s.SourceBlocked):
            s.expected_month("1h",2025,1)
    def test_forbid_future_month_2026(self):
        with self.assertRaises(s.SourceBlocked):
            s.expected_month("1m",2026,1)
    def test_forbid_warmup_minute(self):
        with self.assertRaises(s.SourceBlocked):
            s.expected_month("1m",2021,12)
    def test_expected_month_hours(self):
        _,n,step=s.expected_month("1h",2024,2)
        self.assertEqual((n,step),(696,s.MS_H))
    def test_q25_exact(self):
        self.assertEqual(s.nearest_q25(list(range(1,121))),30)
    def test_q25_incomplete_reject(self):
        with self.assertRaises(ValueError):
            s.nearest_q25([1.0]*119)
    def test_net_bps_long(self):
        self.assertAlmostEqual(s.pnl_bps(1,100,101),100)
    def test_net_bps_short(self):
        self.assertAlmostEqual(s.pnl_bps(-1,100,99),100)
    def test_same_minute_long_collision_stop_wins(self):
        state,trade=s.step_trade(long_sig(),bar(T,100,101.5,98.8,100))
        self.assertEqual(state,"STOP")
        self.assertEqual(trade.reason,"STOP_SAME_MINUTE")
        self.assertLess(trade.gross_bps,0)
    def test_same_minute_short_collision_stop_wins(self):
        state,trade=s.step_trade(short_sig(),bar(T,100,101.5,98.5,100))
        self.assertEqual(state,"STOP")
        self.assertLess(trade.gross_bps,0)
    def test_pending_invalidated_long(self):
        state,_=s.step_trade(long_sig(),bar(T,100,100.2,98.5,99))
        self.assertEqual(state,"CANCEL")
    def test_pending_invalidated_short(self):
        state,_=s.step_trade(short_sig(),bar(T,100,101.7,99.3,101))
        self.assertEqual(state,"CANCEL")
    def test_gap_long_entry_worse(self):
        state,obj=s.step_trade(long_sig(),bar(T,102,102.5,101.8,102))
        self.assertEqual(state,"ENTER")
        self.assertEqual(obj[0],102)
    def test_gap_short_entry_worse(self):
        state,obj=s.step_trade(short_sig(),bar(T,98,98.5,97.5,98))
        self.assertEqual(state,"ENTER")
        self.assertEqual(obj[0],98)
    def test_only_wait_when_no_trigger(self):
        state,_=s.step_trade(long_sig(),bar(T,100,100.3,99.5,100))
        self.assertEqual(state,"WAIT")
    def test_simulation_no_entry_expiry(self):
        a=FakeArchive({})
        result,end,state=s.simulate_one(long_sig(),a)
        self.assertIsNone(result)
        self.assertEqual(state,"EXPIRED")
        self.assertEqual(end,T+s.MS_H+180*s.MS_M)
    def test_simulation_short_target(self):
        start=T+s.MS_H
        a=FakeArchive({start:bar(start,100,100.2,98.8,99.2),
                       start+s.MS_M:bar(start+s.MS_M,98,98.5,94,95)})
        trade,t,state=s.simulate_one(short_sig(),a)
        self.assertEqual(state,"EXIT")
        self.assertEqual(trade.reason,"TARGET")
        self.assertAlmostEqual(trade.gross_bps,400)
    def test_simulation_long_adverse_stop_gap(self):
        start=T+s.MS_H
        a=FakeArchive({start:bar(start,100,101.5,99.9,101),
                       start+s.MS_M:bar(start+s.MS_M,97.5,98.8,97,98)})
        trade,_,state=s.simulate_one(long_sig(),a)
        self.assertEqual(trade.reason,"STOP")
        self.assertEqual(trade.exit,97.5)
    def test_stats_no_trades(self):
        x=s.stats([])
        self.assertEqual(x["n"],0)
        self.assertIsNone(x["gross_mean_bps"])
    def test_insufficient_sample_rejected(self):
        o=s.verdict([],[])
        self.assertEqual(o["classification"],"SIGNAL_SAMPLE_INSUFFICIENT")
        self.assertFalse(o["economic_gate_unlocked"])
    def test_week_key_is_utc(self):
        self.assertRegex(s.iso_week(T),r"\d{4}-W\d{2}")
    def test_timestamp_lookahead_guard_in_detection(self):
        start=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)
        arr=[bar(start+i*s.MS_H,100,101,99,100) for i in range(240)]
        signals,_=s.detect_signals(arr)
        self.assertEqual(signals,[])
    def test_rle_synthetic_ignition_and_compression(self):
        arr=[]
        for i in range(230):
            p=100+i*.1
            arr.append(bar(T+i*s.MS_H,p,p+.2,p-.2,p+.05))
        p=123
        arr.append(bar(T+230*s.MS_H,p,130.5,122.9,130))
        signals,counts=s.detect_signals(arr)
        self.assertTrue(any(q.group=="RLE_NARROW" and q.side==1 for q in signals),counts)
    def test_weak_ignition_not_detected(self):
        arr=[bar(T+i*s.MS_H,100,101,99,100) for i in range(230)]
        arr.append(bar(T+230*s.MS_H,100,110,98,104))
        signals,_=s.detect_signals(arr)
        self.assertEqual(signals,[])
    def test_failed_future_pending_source_blocks(self):
        class Missing:
            def minute(self,t):
                raise s.SourceBlocked("MISSING_MINUTE")
        with self.assertRaises(s.SourceBlocked):
            s.simulate_one(long_sig(),Missing())
    def test_trade_sign_group_independent(self):
        one=s.Trade(T,T+3600000,1,"RLE_NARROW",100,101,100,"TARGET")
        two=s.Trade(T,T+3600000,1,"NON_NARROW_CONTROL",100,101,100,"TARGET")
        self.assertEqual(s.stats([one])["n"],1)
        self.assertEqual(s.stats([two])["n"],1)

if __name__=="__main__":
    unittest.main()

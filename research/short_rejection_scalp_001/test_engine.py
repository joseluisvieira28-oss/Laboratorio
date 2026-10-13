"""Entirely synthetic pre-outcome tests of SHORT-REJECTION-SCALP-001."""
import math
import unittest
from unittest.mock import patch
from research.short_rejection_scalp_001 import engine as e

T=e.START+5*e.FIVE

class FakeMinutes:
    def __init__(self,modified=None):
        self.modified=modified or {}
    def get(self,t):
        b={"t":t,"open":100.,"high":100.1,"low":99.9,"close":100.}
        b.update(self.modified.get(t,{}))
        return b

class ShortRejectionTests(unittest.TestCase):
    def test_frozen_case_and_cost_scope(self):
        self.assertEqual(len(e.ASSETS),8)
        self.assertEqual(set(e.SLIPPAGES),{"BASE","STRESS","DELAY_6H_BASE"})
        self.assertEqual((e.STOP,e.TARGET,e.HOLD_MIN,e.FEE,e.EXPOSURE),
                         (.004,.008,90,.0008,.2))

    def test_bearish_hour_regime_requires_200_plus_24_complete_hours(self):
        first=e.START-230*e.HOUR
        one={first+i*e.HOUR:{"t":first+i*e.HOUR,
             "close":130-i*.15,"open":130-i*.15,"high":130-i*.15,
             "low":130-i*.15,"volume":1.} for i in range(230)}
        state=e.hour_regime(one)
        self.assertFalse(state[first+220*e.HOUR])
        self.assertTrue(state[first+230*e.HOUR])

    def test_5m_upper_wick_sweep_needs_completed_bearish_hour(self):
        bars={}
        for i in range(13):
            t=T+i*e.FIVE
            b={"t":t,"open":100.,"high":105.,"low":99.,"close":100.,"volume":1.}
            if i==12:b.update(open=102.,high=110.,low=98.,close=99.)
            bars[t]=b
        decision=T+13*e.FIVE
        hour=(decision//e.HOUR)*e.HOUR
        with patch.object(e,"hour_regime",return_value={hour:True}):
            signals,stats=e.rejection_decisions(bars,{},start=T,end=T+14*e.FIVE)
        self.assertEqual(signals,[decision])
        with patch.object(e,"hour_regime",return_value={hour+e.HOUR:True}):
            next_only,stats=e.rejection_decisions(bars,{},start=T,end=T+14*e.FIVE)
        self.assertEqual(next_only,[])

    def test_upper_wick_gate_rejects_green_and_body_candles(self):
        bars={T+i*e.FIVE:{"t":T+i*e.FIVE,"open":100.,"high":105.,"low":99.,"close":100.,"volume":1.}
              for i in range(13)}
        end=T+12*e.FIVE
        bars[end].update(open=99.,high=110.,low=98.,close=102.)
        with patch.object(e,"hour_regime",return_value={(end+e.FIVE)//e.HOUR*e.HOUR:True}):
            sig,_=e.rejection_decisions(bars,{},start=T,end=end+e.FIVE)
        self.assertEqual(sig,[])

    def test_entry_after_signal_plus_one_minute_stop_first(self):
        dec=T
        entry=T+e.ONE
        store=FakeMinutes({entry:{"high":101.,"low":98.,"open":100.,"close":99.}})
        out=e.close_trace(dec,store,{},10000,2)
        tr=out["closed"]
        self.assertEqual(tr["entry_t"],entry)
        self.assertEqual(tr["exit_t"],entry+e.ONE)
        self.assertEqual(tr["exit_reason"],"STOP_FIRST")
        self.assertLess(tr["net_pnl_usdt"],0)

    def test_short_gap_buy_uses_worse_observed_open(self):
        dec=T
        entry=T+e.ONE
        store=FakeMinutes({entry+e.ONE:{"open":105.,"high":106.,"low":104.,"close":105.}})
        tr=e.close_trace(dec,store,{},10000,2)["closed"]
        self.assertEqual(tr["exit_reason"],"STOP_GAP")
        self.assertGreater(tr["exit_price"],105.)
        self.assertLess(tr["exit_notional_return_pct"],-4.9)

    def test_target_and_gap_target_price_improvement(self):
        entry=T+e.ONE
        target=FakeMinutes({entry+e.ONE:{"open":98.,"high":98.1,"low":97.,"close":98.}})
        x=e.close_trace(T,target,{},10000,2)["closed"]
        self.assertEqual(x["exit_reason"],"TARGET_GAP")
        self.assertLess(x["exit_price"],99.)

    def test_exact_90m_timeout_not_early_close(self):
        x=e.close_trace(T,FakeMinutes(),{},10000,2)
        tr=x["closed"]
        self.assertEqual(tr["exit_reason"],"TIME_90M")
        self.assertEqual(tr["exit_t"],T+e.ONE+90*e.ONE)

    def test_short_funding_sign_reverses_with_rate(self):
        ts=T+e.ONE+e.ONE
        base=e.close_trace(T,FakeMinutes(),{},10000,2)
        plus=e.close_trace(T,FakeMinutes(),{ts:.01},10000,2)
        minus=e.close_trace(T,FakeMinutes(),{ts:-.01},10000,2)
        self.assertGreater(plus["after_cash"],base["after_cash"])
        self.assertLess(minus["after_cash"],base["after_cash"])
        self.assertGreater(plus["closed"]["funding_usdt"],0.)

    def test_base_stress_execution_price_and_loss(self):
        d=FakeMinutes()
        b=e.close_trace(T,d,{},10000,2)["closed"]
        s=e.close_trace(T,d,{},10000,5)["closed"]
        self.assertLess(s["net_pnl_usdt"],b["net_pnl_usdt"])
        self.assertLess(s["entry_price"],b["entry_price"])

    def test_delayed_placebo_is_six_hours_later_without_lookahead(self):
        dec=T
        r=e.replay([dec],FakeMinutes(),{},2,start=e.START,end=e.START+2*e.HOUR)
        self.assertEqual(r["closed_trades"],1)
        future=e.replay([dec],FakeMinutes(),{},2,delay_hours=6,
                        start=e.START,end=e.START+10*e.HOUR)
        self.assertEqual(future["closed_trades"],1)
        base=e.replay([dec],FakeMinutes(),{},2,start=e.START,end=e.START+10*e.HOUR)
        self.assertEqual(base["trades"][0]["entry_t"]+6*e.HOUR,
                         future["trades"][0]["entry_t"])

    def test_end_of_2025_censor_not_fabricated_close(self):
        x=e.close_trace(e.END-3*e.ONE,FakeMinutes(),{},10000,2)
        self.assertIsNone(x["closed"])
        self.assertTrue(math.isfinite(x["after_mark"]))
        self.assertEqual(x["next_free"],e.END)

    def test_source_checksum_failure_fails_closed(self):
        with __import__("tempfile").TemporaryDirectory() as d:
            store=e.OfficialMinuteStore("ETHUSDT",{},d,
                         fetch_fn=lambda url,maxbytes: b"invalid" if not url.endswith(".CHECKSUM") else b"0"*64)
            with self.assertRaisesRegex(ValueError,"ONE_MIN_PUBLISHER_SHA256_FAIL"):
                store.get(e.START)

if __name__=="__main__":unittest.main()

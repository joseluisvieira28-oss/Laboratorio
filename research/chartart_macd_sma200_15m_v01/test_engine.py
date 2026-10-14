import unittest
from engine import (START, STEP, SourceBlocked, ms_timestamp, rolling_sma, compute_signals, simulate, evaluate)


def orders(**arg):
    return {k: v for k, v in arg.items()}


class ChartArtSyntheticQATest(unittest.TestCase):
    def candle(self,t=START,o=100,hi=102,lo=99,c=100):
        return (t,float(o),float(hi),float(lo),float(c))

    def test_timestamp_ms_vs_microseconds_and_invalid(self):
        self.assertEqual(ms_timestamp(START),START)
        self.assertEqual(ms_timestamp(START*1000),START)
        with self.assertRaises(SourceBlocked):
            ms_timestamp(START*1000+1)

    def test_sma_is_simple_not_exponential(self):
        self.assertEqual(rolling_sma([1.,2.,3.,4.,5.],3),[None,None,2.,3.,4.])

    def test_closed_signal_emits_only_next_bar(self):
        candles=[self.candle(START+(i-220)*STEP,o=1000+i,c=1001+i) for i in range(223)]
        signal=compute_signals(candles)
        self.assertTrue(all(t in {x[0] for x in candles[1:]} for t in signal))

    def test_protected_long_entry_bar_stop(self):
        c=[self.candle(lo=94.5,c=95.)]
        res,tr=simulate(c,{}, {START:1},"E1_PROTECTED_4PCT_7DAY",.0002)
        self.assertEqual(res["closed"],1)
        self.assertEqual(tr[0]["reason"],"STOP_4PCT")
        self.assertLess(tr[0]["exit_px"],tr[0]["entry"])
        self.assertFalse(res["open_position"])

    def test_short_gap_stop_is_worse_than_stop(self):
        c=[self.candle(c=100,lo=99,hi=101), self.candle(t=START+STEP,o=110,hi=111,lo=109,c=110)]
        res,tr=simulate(c,{}, {START:-1},"E1_PROTECTED_4PCT_7DAY",.0002)
        self.assertEqual(tr[0]["reason"],"STOP_4PCT")
        self.assertGreater(tr[0]["exit_px"],110)
        self.assertGreater(res["stop_gap_worse_fills"],0)

    def test_funding_sign_long_and_short(self):
        c=[self.candle(),self.candle(t=START+STEP)]
        out={}
        for side in (1,-1):
            z,_=simulate(c,{START+STEP:(.001,None)},{START:side},"E0_ORIGINAL_SIGNALS",.0002)
            out[side]=z["funding_total"]
        self.assertLess(out[1],0);self.assertGreater(out[-1],0)

    def test_opposite_signal_is_flat_then_reopen(self):
        c=[self.candle(),self.candle(t=START+STEP,lo=99,hi=101),self.candle(t=START+2*STEP)]
        z,tr=simulate(c,{}, {START:1,START+STEP:-1},"E0_ORIGINAL_SIGNALS",.0002)
        self.assertEqual(len(tr),1)
        self.assertEqual(tr[0]["reason"],"OPPOSITE_SIGNAL")
        self.assertEqual(z["signal_count"],2)
        self.assertTrue(z["open_position"])
        # 1 LONG entry, long closing exit, 1 SHORT entry = 3 legs each charged 8bps.
        self.assertGreater(z["fees_paid"],2.0)

    def test_protected_no_stale_reentry_after_stop(self):
        c=[self.candle(lo=95,c=95),self.candle(t=START+STEP)]
        z,t=simulate(c,{}, {START:1},"E1_PROTECTED_4PCT_7DAY",.0002)
        self.assertEqual(len(t),1)
        self.assertFalse(z["open_position"])

    def test_seven_day_time_limit(self):
        seq=[self.candle(t=START+i*STEP,o=100,hi=101,lo=99,c=100) for i in range(672+1)]
        z,t=simulate(seq,{}, {START:1},"E1_PROTECTED_4PCT_7DAY",.0002)
        self.assertEqual(len(t),1)
        self.assertEqual(t[0]["reason"],"TIME_7D")

    def test_history_freeze_boundary_and_mutual_futures_signal(self):
        self.assertEqual(START,1640995200000)
        # Different model calls with same source and signals must be deterministic.
        c=[self.candle()]
        a,_=simulate(c,{}, {START:1},"E0_ORIGINAL_SIGNALS",.0002)
        b,_=simulate(c,{}, {START:1},"E0_ORIGINAL_SIGNALS",.0002)
        self.assertEqual(a,b)

    def test_predeclared_gate_must_not_promote_insufficient(self):
        core={"closed":5,"terminal_return_pct":3,"pf":2.0,
              "years":{str(y):{"net":100,"trades":1} for y in range(2022,2026)},
              "max_15m_mtm_dd_pct":-1,"net_excluding_top3_static":100,
              "closed_realized_net":300}
        outcomes={s:{"E0_ORIGINAL_SIGNALS":dict(core),"E1_PROTECTED_4PCT_7DAY":dict(core)}
                  for s in ("BASE","STRESS")}
        self.assertEqual(evaluate(outcomes)["verdict"],"NO_HISTORICAL_CANDIDACY")


if __name__=="__main__":
    unittest.main(verbosity=2)

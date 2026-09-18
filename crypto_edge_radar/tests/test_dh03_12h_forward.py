import unittest
from radar.dh03_12h_forward import ATR_LEN,BAR_MS,FIRST_SIGNAL_BAR_OPEN_MS,MinuteBar,Signal,aggregate_12h,atr_series,derive_signals,simulate_signal

class DH0312HForwardTests(unittest.TestCase):
    def _minutes(self,start,bars,base=100.0):
        out=[]
        for i in range(bars*720):
            t=start+i*60_000
            p=base+0.001*i
            out.append(MinuteBar(t,p,p+0.1,p-0.1,p+0.05))
        return out
    def test_aggregate_requires_all_720_minutes(self):
        start=FIRST_SIGNAL_BAR_OPEN_MS-(45*BAR_MS)
        m=self._minutes(start,2)
        bars,inc=aggregate_12h(m)
        self.assertEqual(len(bars),2); self.assertEqual(inc,0)
        broken=m[:800]+m[801:]
        bars2,inc2=aggregate_12h(broken)
        self.assertEqual(len(bars2),1); self.assertEqual(inc2,1)
    def test_first_eligible_signal_bar_is_fully_postfreeze(self):
        start=FIRST_SIGNAL_BAR_OPEN_MS-(45*BAR_MS)
        m=self._minutes(start,47)
        bars,_=aggregate_12h(m)
        sigs,diag=derive_signals("BTCUSDT",bars)
        self.assertTrue(all(s.signal_open_time>=FIRST_SIGNAL_BAR_OPEN_MS for s in sigs))
        self.assertGreater(diag["prefreeze_or_crossing_bars_ignored"],0)
    def test_atr_is_wilder_after_seed(self):
        start=FIRST_SIGNAL_BAR_OPEN_MS-(40*BAR_MS)
        m=self._minutes(start,35)
        bars,_=aggregate_12h(m)
        atr=atr_series(bars,ATR_LEN)
        self.assertIsNotNone(atr[ATR_LEN]); self.assertIsNotNone(atr[ATR_LEN+1])
    def test_same_minute_stop_target_is_stop_first(self):
        entry_t=FIRST_SIGNAL_BAR_OPEN_MS+BAR_MS
        sig=Signal("BTCUSDT",FIRST_SIGNAL_BAR_OPEN_MS,entry_t,100.0,99.0,103.0,0.01,"x")
        minutes=[MinuteBar(entry_t,100.0,104.0,98.0,101.0),MinuteBar(entry_t+60_000,101.0,101.2,100.5,101.0)]
        row=simulate_signal(sig,minutes,[],[])
        self.assertEqual(row.exit_reason,"STOP_WINS_SAME_MINUTE_AMBIGUITY"); self.assertEqual(row.exit_price,99.0); self.assertFalse(row.execution_path_unresolved)
    def test_long_funding_is_negative_sum_between_entry_and_exit(self):
        entry_t=FIRST_SIGNAL_BAR_OPEN_MS+BAR_MS
        sig=Signal("BTCUSDT",FIRST_SIGNAL_BAR_OPEN_MS,entry_t,100.0,99.0,101.0,0.01,"x")
        minutes=[MinuteBar(entry_t,100.0,100.2,99.8,100.1),MinuteBar(entry_t+60_000,100.1,101.1,100.0,101.0)]
        row=simulate_signal(sig,minutes,[entry_t,entry_t+30_000],[0.001,0.002])
        self.assertEqual(row.exit_reason,"TARGET"); self.assertAlmostEqual(row.funding_return,-0.002,12); self.assertEqual(row.funding_event_count,1)
    def test_gap_fails_closed(self):
        entry_t=FIRST_SIGNAL_BAR_OPEN_MS+BAR_MS
        sig=Signal("BTCUSDT",FIRST_SIGNAL_BAR_OPEN_MS,entry_t,100.0,90.0,130.0,0.1,"x")
        minutes=[MinuteBar(entry_t,100.0,101.0,99.0,100.0),MinuteBar(entry_t+120_000,100.0,101.0,99.0,100.0)]
        row=simulate_signal(sig,minutes,[],[])
        self.assertTrue(row.execution_path_unresolved); self.assertEqual(row.exit_reason,"EXECUTION_PATH_UNRESOLVED_GAP")

if __name__=="__main__": unittest.main()

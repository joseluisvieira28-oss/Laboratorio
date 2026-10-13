"""Offline regression tests for archival retrospective replay, no networks."""
import unittest
from retrospective_diagnostic import backtest,H,FIVE,START_MS

def fake_data(start=START_MS, n_hours=14):
    # Flat synthetic market with full 5m continuity. Single entry at first hour.
    one=[dict(t=start+i*H,open=100.,high=100.1,low=99.9,close=100.,volume=1.)
         for i in range(n_hours)]
    five={}
    for i in range(n_hours*12):
        t=start+i*FIVE
        five[t]=dict(t=t,open=100.,high=100.01,low=99.99,close=100.,volume=1.)
    return one,five

class HistoricalReplayUnitTests(unittest.TestCase):
    def test_first_entry_after_signal_close_and_5m(self):
        one,five=fake_data()
        signals=[True]+[False]*(len(one)-1)
        a=backtest(signals,one,five,{},2)
        self.assertEqual(a["closed_trades"],1)
        self.assertEqual(a["reason_counts"]["TIME_EXIT"],1)
        self.assertEqual(a["trades"][0]["entry_t"],START_MS+H+FIVE)
        self.assertEqual(a["trades"][0]["exit_t"],START_MS+H+FIVE+4*H)
        self.assertLess(a["return_pct"],0) # costs aren't zero

    def test_same_bar_stop_first(self):
        one,five=fake_data()
        entry=START_MS+H+FIVE
        five[entry]["high"]=110
        five[entry]["low"]=90
        signals=[True]+[False]*(len(one)-1)
        a=backtest(signals,one,five,{},2)
        self.assertEqual(a["reason_counts"]["STOP_FIRST"],1)
        self.assertLess(a["return_pct"],0)

    def test_negative_gap_not_filled_at_stop_level(self):
        one,five=fake_data()
        entry=START_MS+H+FIVE
        five[entry+FIVE].update(open=90,high=95,low=89,close=91)
        signals=[True]+[False]*(len(one)-1)
        a=backtest(signals,one,five,{},2)
        self.assertEqual(a["reason_counts"]["STOP_GAP"],1)
        self.assertLess(a["return_pct"],-1.0)

    def test_positive_funding_is_a_long_cost(self):
        one,five=fake_data()
        signals=[True]+[False]*(len(one)-1)
        settle=START_MS+2*H
        base=backtest(signals,one,five,{},2)
        funded=backtest(signals,one,five,{settle:0.001},2)
        self.assertLess(funded["return_pct"],base["return_pct"])

    def test_six_hour_placebo_is_shifted_and_not_lookahead(self):
        one,five=fake_data(n_hours=18)
        signals=[True]+[False]*(len(one)-1)
        a=backtest(signals,one,five,{},2,delay_hours=0)
        b=backtest(signals,one,five,{},2,delay_hours=6)
        self.assertEqual(b["trades"][0]["entry_t"]-a["trades"][0]["entry_t"],6*H)

if __name__=="__main__":
    unittest.main()

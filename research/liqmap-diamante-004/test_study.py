import datetime as dt,math,unittest
import numpy as np,pandas as pd
import study

def fake(weeks=5):
    n=weeks*7*24
    times=pd.date_range("2026-07-01T00:00:00Z",periods=n,freq="h")
    return {"time":times,"open":np.full(n,100.),"close":np.full(n,100.),
           "long":np.zeros(n),"short":np.zeros(n),"nlong":np.zeros(n),
           "nshort":np.zeros(n),"raw_position_events":0}

class ScientificGates(unittest.TestCase):
    def test_quantile_uses_exact_336_old_hours(self):
        old=[0.]*320+[100.]*16
        self.assertEqual(study.quantile95(old),0.)
        old=[0.]*319+[100.]*17
        self.assertEqual(study.quantile95(old),100.)
        with self.assertRaises(ValueError):study.quantile95([1.]*335)
    def test_cascade_trigger_and_dominance(self):
        a=fake(5);i=400
        a["long"][i]=150000.;a["short"][i]=5000.;a["nlong"][i]=4
        signal,threshold=study.mode_at(a,i)
        self.assertEqual(signal,-1)
        self.assertEqual(threshold,0.)
        a["short"][i]=150000.
        signal,_=study.mode_at(a,i)
        self.assertEqual(signal,"NEUTRAL")
    def test_future_candles_do_not_affect_signal(self):
        a=fake(5);i=400
        a["short"][i]=250000.;a["nshort"][i]=5
        before=study.mode_at(a,i)
        a["close"][i+1:i+10]*=1.2
        self.assertEqual(study.mode_at(a,i),before)
    def test_no_signals_without_real_liquidations(self):
        a=fake(5)
        r=study.study_one(a,"BTC-PERP")
        self.assertEqual(r["independent_event_count"],0)
    def test_event_direction_costs(self):
        self.assertAlmostEqual(study.event_return(102.,100.,1,10)-
               study.event_return(102.,100.,1,80),140.)
        self.assertAlmostEqual(study.event_return(98.,100.,-1,10)-
               study.event_return(98.,100.,-1,35),50.)
    def test_same_4hour_interval_no_overlap(self):
        a=fake(5)
        for i in range(350,356):
            a["long"][i]=500000;a["nlong"][i]=4
        r=study.study_one(a,"BTC-PERP")
        self.assertGreaterEqual(r["overlapping_candidates_skipped"],4)
        self.assertEqual(r["independent_event_count"],2)
    def test_bootstrap_repeatable(self):
        sample=[{"time":str(pd.Timestamp("2026-07-01T00:00Z")+pd.Timedelta(days=i)),
             "value":(-1)**i*30.} for i in range(30)]
        self.assertEqual(study.bootstrap_week(sample,lambda x:x["value"]),
             study.bootstrap_week(sample,lambda x:x["value"]))
    def test_source_unsupported_never_go(self):
        r={"results":{"BTC-PERP":{"independent_event_count":0,
            "summary":{k:{"n_events":0,"mean_80bps_plus5_slip_per_side_net_bps":None,
              "weekly_bootstrap_mean_net_CI975":{"low":None},
              "weekly_bootstrap_excess_v_mom_CI975":{"low":None},
              "months_positive":0,"max_sequential_close_drawdown_pct":0} for k in ("continuation","reversal")}},
            "ETH-PERP":{"independent_event_count":0,
            "summary":{k:{"n_events":0,"mean_80bps_plus5_slip_per_side_net_bps":None,
              "weekly_bootstrap_mean_net_CI975":{"low":None},
              "weekly_bootstrap_excess_v_mom_CI975":{"low":None},
              "months_positive":0,"max_sequential_close_drawdown_pct":0} for k in ("continuation","reversal")}}}}
        self.assertEqual(study.gate(r)["scientific_verdict"],"INCONCLUSIVE_SMALL_INDEPENDENT_SAMPLE")
if __name__=="__main__":unittest.main()

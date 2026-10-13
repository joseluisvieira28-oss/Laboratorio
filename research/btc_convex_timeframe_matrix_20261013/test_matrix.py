"""NO market downloads: strict synthetic invariants for four-TF Parent replay."""
import unittest
from unittest.mock import patch
from research.btc_convex_timeframe_matrix_20261013 import matrix as m

def minute_5_bars(start,n,open_=100.):
    return {start+i*m.M5:{"t":start+i*m.M5,"open":open_,"high":open_+1,
                          "low":open_-1,"close":open_,"volume":10.}
            for i in range(n)}

def run_synth(tf, five, signal_index=0, *, slip=2, funding=None):
    start=min(five)
    end=max(five)+m.M5
    tfs=[{"t":start+i*tf,"open":100.,"high":101.,"low":99.,"close":100.,"volume":30.}
         for i in range((end-start)//tf)]
    sig=[i==signal_index for i in range(len(tfs))]
    with patch.object(m,"START",start),patch.object(m,"END",end),patch.object(
            m.src,"load_parent",return_value=lambda _: (sig,[None]*len(sig))):
        return m.simulate(tf,tfs,five,funding or {},slip,include_trades=True)

class MatrixSyntheticTest(unittest.TestCase):
    def test_tf_resample_four_families(self):
        for label,tf in m.TFS:
            with self.subTest(tf=label):
                src=minute_5_bars(m.PRE,tf//m.M5*2)
                with patch.object(m,"END",m.PRE+2*tf):
                    rs=m.resample(src,tf)
                self.assertEqual(len(rs),2)
                self.assertEqual(rs[0]["volume"],10*tf//m.M5)
                self.assertEqual(rs[1]["t"]-rs[0]["t"],tf)

    def test_parity_with_official_source(self):
        src=minute_5_bars(m.PRE,12)
        with patch.object(m,"END",m.PRE+m.HOUR):
            a=m.resample(src,m.HOUR)
        self.assertEqual(m.verify_one_hour_parity(a,{a[0]["t"]:dict(a[0])})["status"],"PASS_ALL_FIELDS")
        b=dict(a[0]);b["volume"]+=0.2
        audit=m.verify_one_hour_parity(a,{a[0]["t"]:b})
        self.assertEqual(audit["volume_mismatch_count"],1)
        self.assertEqual(audit["price_status"],"PASS_ALL_OHLC")
        self.assertEqual(audit["status"],"PRICE_PARITY_PASS_VOLUME_DIFFERENCES_RECORDED")
        b=dict(a[0]); b["high"]+=0.2
        with self.assertRaisesRegex(ValueError,"PRICE_PARITY_MISMATCH"):
            m.verify_one_hour_parity(a,{a[0]["t"]:b})

    def test_entry_after_closed_bar_for_four_tfs(self):
        for _,tf in m.TFS:
            with self.subTest(tf=tf):
                n=3*tf//m.M5
                b=minute_5_bars(m.PRE+n*m.M5,n+1)
                event_t=min(b)+tf+2*m.M5
                b[event_t].update(open=100.,high=101.,low=90.,close=100.)
                res=run_synth(tf,b)
                self.assertEqual(res["entries"],1)
                self.assertEqual(res["trades"][0]["open_t"],min(b)+tf+m.M5)
                self.assertEqual(res["trades"][0]["exit_reason"],"STOP_INTRABAR")

    def test_gap_executes_at_observed_open_not_stop(self):
        tf=3*m.M5
        start=m.PRE+tf
        bars=minute_5_bars(start,40)
        entry=start+tf+m.M5
        bars[entry+m.M5].update(open=90,high=91,low=89,close=90)
        res=run_synth(tf,bars)
        self.assertEqual(res["trades"][0]["exit_reason"],"STOP_OPEN_GAP")
        self.assertLess(res["trades"][0]["notional_return_pct"],-9.0)

    def test_nonlatched_original_trailing_reverts_below_five_percent(self):
        tf=3*m.M5
        start=m.PRE+tf
        bars=minute_5_bars(start,50)
        entry=start+tf+m.M5
        # Entry bar: briefly +15% high, but stop only updates at TF close
        bars[entry].update(open=100,high=115,low=99,close=110)
        # Next bar TF close +15%, sets new trailing >100.
        bars[entry+m.M5].update(open=110,high=114,low=109,close=110)
        # Next TF close below +5%; all bars before must stay above 101.2
        bars[entry+2*m.M5].update(open=110,high=111,low=109,close=109)
        bars[entry+3*m.M5].update(open=109,high=110,low=107,close=108)
        bars[entry+4*m.M5].update(open=108,high=108,low=104,close=104)
        # original nonlatched now reverts from 101.2 to 96
        bars[entry+5*m.M5].update(open=104,high=105,low=99,close=100)
        bars[entry+6*m.M5].update(open=100,high=101,low=95,close=96)
        res=run_synth(tf,bars)
        self.assertEqual(res["trades"][0]["close_t"],entry+7*m.M5)
        self.assertEqual(res["trades"][0]["exit_reason"],"STOP_INTRABAR")

    def test_funding_while_carried_into_timestamp(self):
        tf=3*m.M5
        start=m.PRE+tf
        bars=minute_5_bars(start,35)
        base=run_synth(tf,bars)
        settle=start+2*tf
        funded=run_synth(tf,bars,funding={settle:0.001})
        self.assertLess(funded["marked_return_pct"],base["marked_return_pct"])
        self.assertLess(funded["funding_usdt"],0)

    def test_source_misalignment_blocks(self):
        tf=3*m.M5
        src=minute_5_bars(m.PRE,6)
        src.pop(m.PRE+2*m.M5)
        with self.assertRaisesRegex(ValueError,"INCOMPLETE_AGGREGATION|AGGREGATION_GAP"):
            m.resample(src,tf)

    def test_all_tf_cost_stress_degrades_returns(self):
        tf=3*m.M5
        start=m.PRE+tf
        bars=minute_5_bars(start,50)
        base=run_synth(tf,bars,slip=2)
        stress=run_synth(tf,bars,slip=5)
        self.assertLess(stress["marked_return_pct"],base["marked_return_pct"])

    def test_end_censored_open_not_fabricated_closed_trade(self):
        tf=48*m.M5
        start=m.PRE+tf
        bars=minute_5_bars(start,200)
        result=run_synth(tf,bars)
        self.assertTrue(result["end_position_open"])
        self.assertEqual(result["closed_trades"],0)

if __name__=="__main__":
    unittest.main()

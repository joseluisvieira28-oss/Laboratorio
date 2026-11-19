"""Offline invariants for price-only historic falsification. All fixtures synthetic."""
import datetime as dt
import pathlib
import sys
import unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import historical_price_audit as h

class Tests(unittest.TestCase):
    def setUp(self):
        self.start=h.START_TS
        self.data={self.start-30*3600+i*3600:(100.,1000.) for i in range(130)}
    def test_uses_only_fully_closed_hour(self):
        observation=self.start+2*3600+37*60
        self.data[self.start+2*3600]=(100000.,1000.)
        x=h.returns(self.data,observation)
        self.assertEqual(x[0],self.start+3600)
        self.assertAlmostEqual(x[1],0)
    def test_no_interpolation_missing_h6(self):
        observation=self.start+2*3600+37*60
        self.data.pop(self.start+3600-6*3600,None)
        self.assertIsNone(h.returns(self.data,observation))
    def test_horizons_only_after_signal(self):
        coin=dict(coin_id="synthetic")
        # A continuous price change makes retrospective 4h future return visible.
        for j in range(10):self.data[self.start+j*3600]=(100+j,1000)
        events,counts=h.evaluate_one(coin,self.data)
        b=[e for e in events if e["policy"]=="BASELINE_4H"]
        self.assertTrue(b)
        x=next(e for e in b if e["observed_at"]==self.start+4*3600+37*60)
        self.assertAlmostEqual(x["h4_gross_pct"],100*(108/104-1),places=3)
    def test_price_only_not_buyer_gate(self):
        summary=h.summarize([dict(policy="H_MOMENTUM_PRICE_ONLY",observed_at=self.start,
                         h4_gross_pct=8.,h24_gross_pct=None)])
        self.assertEqual(summary["H_MOMENTUM_PRICE_ONLY"]["h4"]["cost_5pct"]["mean_proxy_pct"],3.)
        self.assertEqual(summary["H_MOMENTUM_PRICE_ONLY"]["h4"]["missing"],0)
        self.assertEqual(summary["H_MOMENTUM_PRICE_ONLY"]["h24"]["missing"],1)
        self.assertEqual(summary["H_MOMENTUM_PRICE_ONLY"]["unverified_buyer_gate"],1)
    def test_original_thresholds_are_unchanged(self):
        coin=dict(coin_id="synthetic")
        # h1=+2%, h6=+6.0% precisely at observed 02:37 (anchor 01:00).
        anchor=self.start+3600
        self.data[anchor]=(106,100)
        self.data[anchor-3600]=(103,100)
        self.data[anchor-6*3600]=(100,100)
        events,_=h.evaluate_one(coin,self.data)
        signal=[e for e in events if e["observed_at"]==self.start+2*3600+37*60]
        self.assertTrue(any(e["policy"]=="H_MOMENTUM_PRICE_ONLY" for e in signal))
    def test_holdout_split_stays_frozen(self):
        self.assertEqual(h.SPLIT_TS,int(dt.datetime(2026,10,23,tzinfo=dt.timezone.utc).timestamp()))
        self.assertEqual(h.END_TS,int(dt.datetime(2026,11,15,tzinfo=dt.timezone.utc).timestamp()))

if __name__=="__main__":unittest.main()

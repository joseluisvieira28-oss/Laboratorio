import unittest
import numpy as np
import pandas as pd
import study as st

class Digi011Safety(unittest.TestCase):
    def bars(self,n=100):
        times=np.array([int(pd.Timestamp("2025-10-01",tz="UTC").timestamp()*1000)+i*3600000 for i in range(n)],dtype=np.int64)
        return pd.DataFrame({"time_ms":times,"open":[100.]*n,"high":[102.]*n,
            "low":[98.]*n,"close":[100.]*n,"volume":[10.]*n,
            "quote_volume":[1000.]*n,"atr":[2.]*n,"frame":[1]*n})
    def funding(self):
        return {"BTC":(np.array([],dtype=np.int64),np.array([0.]))}
    def test_chronological_phase(self):
        self.assertEqual(st.phase(int(pd.Timestamp("2025-05-05",tz="UTC").timestamp()*1000)),"validation")
        self.assertEqual(st.phase(int(pd.Timestamp("2026-04-05",tz="UTC").timestamp()*1000)),"test")
    def test_stop_is_first_if_both_touched(self):
        b=self.bars()
        b.loc[31,"high"]=110;b.loc[31,"low"]=90
        sig=np.zeros(len(b),dtype=np.int8);sig[30]=1
        rows,blocked=st.simulate(b,sig,"BTC",1,.0002,self.funding())
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["reason"],"stop")
        self.assertLess(rows[0]["net_return"],0)
    def test_skip_when_next_bar_missing(self):
        b=self.bars();b.loc[31:,"time_ms"]+=3600000
        sig=np.zeros(len(b),dtype=np.int8);sig[30]=1
        rows,blocked=st.simulate(b,sig,"BTC",1,.0002,self.funding())
        self.assertEqual(len(rows),0)
        self.assertEqual(blocked["no_consecutive_next_open"],1)
    def test_funding_direction(self):
        t0=int(pd.Timestamp("2026-01-01",tz="UTC").timestamp()*1000)
        fund={"BTC":(np.array([t0+3600000,t0+8*3600000],dtype=np.int64),
                     np.array([0,.0004,.0002]))}
        self.assertAlmostEqual(st.funding_for(fund,"BTC",t0,t0+7*3600000,1)[0],-.0004)
        self.assertAlmostEqual(st.funding_for(fund,"BTC",t0,t0+7*3600000,-1)[0],.0004)
    def test_four_hour_groups_complete_only(self):
        b=self.bars(80)
        b.loc[3,"time_ms"]+=3600000 # duplicate timestamp creates incomplete group
        a=st.bars_for_coin(b,4)
        self.assertTrue((a["time_ms"]%(4*3600000)==0).all())
        self.assertLess(len(a),20)
    def test_poc_uses_previous_completed_bars_only(self):
        b=self.bars(100);b["close"]=100+.01*np.arange(len(b))
        x=st.features(b,72)
        b.loc[90,"high"]=500;b.loc[90,"close"]=450
        y=st.features(b,72)
        self.assertTrue(np.isnan(x.loc[71,"poc_proxy"]))
        self.assertTrue(np.isfinite(x.loc[72,"poc_proxy"]))
        self.assertAlmostEqual(y.loc[90,"poc_proxy"],x.loc[90,"poc_proxy"],places=9)
    def test_fee_slippage_applied(self):
        b=self.bars(); sig=np.zeros(len(b),dtype=np.int8);sig[30]=1
        rows,_=st.simulate(b,sig,"BTC",1,.0002,self.funding())
        self.assertEqual(len(rows),1)
        self.assertGreater(rows[0]["fee_return"],.0009)
        self.assertLess(rows[0]["net_return"],-.001)
if __name__=="__main__":unittest.main()

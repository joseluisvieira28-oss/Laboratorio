import datetime as dt
import math
import unittest
import evaluate as e

def synthetic(n=100):
    result={k:[] for k in ("BTC","ETH","RATIO")}
    for i in range(n):
        date=str(dt.date(2018,1,1)+dt.timedelta(weeks=i))
        b=100*(1+.004*i)
        eth=12*(1+.001*i)
        for symbol,v in (("BTC",b),("ETH",eth),("RATIO",eth/b)):
            result[symbol].append({"date":date,"open":v,"high":v*1.05,
                "low":v*.95,"close":v*1.001})
    return result

class Controls(unittest.TestCase):
    def test_turnover_two_leg(self):
        self.assertAlmostEqual(e.turnover((1,0),(0,1)),1.)
        self.assertAlmostEqual(e.turnover((1,0),(0,1),True),2.)
        self.assertAlmostEqual(e.turnover((.5,.5),(0,0)),1.)
        self.assertAlmostEqual(e.turnover((0,0),(.5,.5)),1.)
        self.assertAlmostEqual(e.turnover((1.,0.),(.5,0.)),.5)
    def test_40w_trend_no_future(self):
        data=synthetic()
        outcome=e.trend40(data,55)
        data["BTC"][55]["close"]=1e10
        self.assertEqual(e.trend40(data,55),outcome)
        self.assertFalse(e.trend40(data,39))
    def test_12w_vol_no_future(self):
        data=synthetic()
        orig=e.annual_vol(data,"BTC",55)
        data["BTC"][55]["close"]=1e10
        self.assertAlmostEqual(e.annual_vol(data,"BTC",55),orig)
        self.assertIsNone(e.annual_vol(data,"BTC",12))
    def test_alloc_risk_limits_and_matured_pivots(self):
        data=synthetic()
        pos=e.b004.positions(data)
        for i in range(len(data["BTC"])):
            for system in e.SYSTEMS:
                b,eth=e.alloc(data,pos,system,i)
                self.assertGreaterEqual(min(b,eth),0)
                self.assertLessEqual(b+eth,1.)
        old=e.alloc(data,pos,"ROT_TREND40_VOL20",70)
        future=synthetic(110)
        future["RATIO"][105]["low"]=0.0000001
        fut=e.b004.positions(future)
        self.assertEqual(e.alloc(future,fut,"ROT_TREND40_VOL20",70),old)
    def test_no_free_cost_and_cash(self):
        data=synthetic()
        p=e.b004.positions(data)
        low,_=e.simulate(data,p,0,100,10)
        high,_=e.simulate(data,p,0,100,80)
        self.assertEqual(low["CASH"]["total_return_pct"],0.)
        self.assertEqual(low["CASH"]["max_drawdown_pct"],0.)
        self.assertGreater(low["FROZEN002"]["total_return_pct"],high["FROZEN002"]["total_return_pct"])
        self.assertAlmostEqual(low["HALF_ROT"]["mean_invested_weight_pct"],50.)
    def test_original_004_parity_from_sha_checked_archive(self):
        source,prior=e.load_inputs()
        for venue,data in source.items():
            pol=e.b004.positions(data)
            got,_=e.simulate(data,pol,0,464,10)
            ref=next(x for x in prior["venn"][venue]["comparisons"] if x["period"]=="2018-2026" and
                x["bps_per_leg"]==10 and not x["two_leg_swap_stress"])
            for name in ("FROZEN002","MOM8","BTC","ETH","MIX"):
                self.assertAlmostEqual(got[name]["total_return_pct"],
                    ref["portfolios"][name]["total_return_pct"],places=4)
    def test_deterministic_bootstrap(self):
        a=[.01,.03,-.04,.02]*8;b=[0.0]*32
        self.assertEqual(e.bootstrap(a,b),e.bootstrap(a,b))
if __name__=="__main__":unittest.main()

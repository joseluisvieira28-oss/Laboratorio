import datetime as dt
import math
import unittest
import analyze as m
import collect as c

def dummy(n=130):
    out={"BTC":[],"ETH":[],"RATIO":[]}
    for i in range(n):
        d=str(dt.date(2018,1,1)+dt.timedelta(weeks=i))
        bv=100.+i
        ev=10.+i/10
        rv=ev/bv
        for sym,p in (("BTC",bv),("ETH",ev),("RATIO",rv)):
            out[sym].append({"date":d,"open":p,"close":p*1.001,
                             "high":p*1.01,"low":p*.99})
    return out

class SourceGates(unittest.TestCase):
    def test_464_valid_weeks(self):
        d=dummy(464)
        m.check_data(d)
        d["BTC"].pop()
        with self.assertRaises(ValueError):m.check_data(d)
    def test_OHLC_invalid(self):
        c.validate(1.,2.,.9,1.5)
        with self.assertRaises(ValueError):c.validate(1.,.9,1.1,1.)
        with self.assertRaises(ValueError):c.validate(float("nan"),2.,.9,1.5)

class ModelTests(unittest.TestCase):
    def test_no_lookahead_after_append(self):
        data=dummy(130)
        prev=m.positions(data)
        extended=dummy(131)
        after=m.positions(extended)
        for k in m.CANDIDATES:
            self.assertEqual(prev[k],after[k][:130])
    def test_original_parity_with_002(self):
        d=dummy(130)
        original=m.positions(d)
        res,_=m.trade_model(d,original,0,130,10)
        raw,_switch,_=m.b002.simulate(d["BTC"],d["ETH"],m.b002.signals(d["RATIO"]),2018,2020,10)
        self.assertAlmostEqual(res["FROZEN002"]["total_return_pct"],raw["ROT"]["total_return_pct"],places=4)
        self.assertAlmostEqual(res["BTC"]["total_return_pct"],raw["BTC"]["total_return_pct"],places=4)
        self.assertAlmostEqual(res["MIX"]["total_return_pct"],raw["MIX"]["total_return_pct"],places=4)
    def test_cost_degrades_return(self):
        d=dummy(130);p=m.positions(d)
        low,_=m.trade_model(d,p,0,130,5)
        high,_=m.trade_model(d,p,0,130,35)
        self.assertGreater(low["FROZEN002"]["total_return_pct"],high["FROZEN002"]["total_return_pct"])
    def test_fold_selection_only_previous_weeks(self):
        d=dummy(130); p=m.positions(d)
        chosen,folds=m.historical_folds(d,p)
        self.assertEqual(folds[0]["training_start"],d["BTC"][0]["date"])
        self.assertEqual(folds[0]["test_start"],d["BTC"][104]["date"])
        self.assertEqual(len(folds),1)
        self.assertEqual(len(chosen["WF_SELECTED"]),130)
    def test_bootstrap_deterministic(self):
        a=[.03,-.01,.04,0.]*8;b=[.01,0.,-.01,0.]*8
        self.assertEqual(m.bootstrap(a,b),m.bootstrap(a,b))
if __name__=="__main__":unittest.main()

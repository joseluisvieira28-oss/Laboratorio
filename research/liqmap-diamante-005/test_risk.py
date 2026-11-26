import datetime as dt
import math
import unittest

import numpy as np
import pandas as pd

import risk as r

def fake(n=2952):
    # Deterministic synthetic OHLC ONLY for invariants, NEVER economic evidence.
    times=pd.date_range("2026-07-01T00:00:00Z",periods=n,freq="h")
    px=100*np.exp(np.arange(n)*.00015)
    return {"time":times,"open":px.copy(),"close":px.copy(),
        "high":px*1.002,"low":px*.998,
        "long":np.zeros(n),"short":np.zeros(n),
        "nlong":np.zeros(n),"nshort":np.zeros(n)}

class TemporalRiskTests(unittest.TestCase):
    def test_dynamic_risk_cutoff_uses_333_past_finished_windows(self):
        p=fake();ex=r.historical_excursions(p)
        i=400
        old= r.nearest_rank(ex[i-336:i-3],.9)
        # The future gigantic move changes the label ONLY, not the cutoff.
        p["high"][i+2]=p["high"][i+2]*2
        again=r.historical_excursions(p)
        new= r.nearest_rank(again[i-336:i-3],.9)
        self.assertAlmostEqual(old,new,12)
        self.assertGreater(again[i],ex[i])
        self.assertEqual(len(ex[i-336:i-3]),333)
    def test_training_and_two_fixed_holdouts(self):
        self.assertEqual(str(r.FIRST_TRAIN.date()),"2026-07-15")
        self.assertEqual(str(r.SEP.date()),"2026-09-01")
        self.assertEqual(str(r.OCT.date()),"2026-10-01")
        self.assertEqual(str(r.END.date()),"2026-11-01")
        self.assertEqual(r.HISTORY,336);self.assertEqual(r.FUTURE,4)
        self.assertEqual(r.CUT,.20)
    def test_features_known_when_closed_no_future_read(self):
        p=fake()
        for j in range(350,3000,123):
            if j<len(p["long"]):p["long"][j]=10000+j
        rr=r.market_dataset(p,"BTC-PERP")
        index=rr[20]["index"]
        oldfeatures=list(rr[20]["x"])
        oldthreshold=rr[20]["cutoff_excursion"]
        # Changing ONLY one future candle does not affect a past-time decision
        p["high"][index+2]*=4
        r2=r.market_dataset(p,"BTC-PERP")
        self.assertEqual(r2[20]["x"],oldfeatures)
        self.assertEqual(r2[20]["cutoff_excursion"],oldthreshold)
    def test_fee_cost_charged_on_position_changes_only(self):
        p=fake()
        # One aligned synthetic four-hour decision, no actual trading.
        dt0=p["time"][400]
        rows=[{"month":"2026-07","index":400,"utc":dt0.isoformat(),
               "prob_price":0.1,"prob_price_plus_liq":0.3}]
        base=r.utility_for_period(rows,p,"2026-07","price",10)
        extra=r.utility_for_period(rows,p,"2026-07","extended",10)
        self.assertEqual(base["position_switches_total"],2)
        self.assertEqual(extra["position_switches_total"],0)
        self.assertEqual(extra["ending_NAV"],1)
    def test_gate_requires_all_coins_and_all_criteria(self):
        make=lambda x:{"2026-09":{"brier_improvement":-0.001},
             "2026-10":{"n":700,"high_risk_count":100,
                "brier_improvement":x,
                "weekly_bootstrap_brier_improvement_CI95":{"low":-0.001}}}
        util=lambda:{"2026-09":{"10":{"price":{"ending_NAV":1},"extended":{"ending_NAV":1}}},
             "2026-10":{"10":{"price":{"ending_NAV":1},"extended":{"ending_NAV":1},
                               "passive":{"ending_NAV":1}}}}
        g=r.gate({"BTC-PERP":make(.006),"ETH-PERP":make(.006)},
                 {"BTC-PERP":util(),"ETH-PERP":util()})
        self.assertEqual(g["scientific_verdict"],"NO_GO_ADDITIONAL_LIQUIDATION_RISK_FEATURE")
        self.assertEqual(g["real_capital"],"NO_GO")
    def test_quantile_nearest_rank(self):
        self.assertEqual(r.nearest_rank(list(range(10)),.90),8)
        with self.assertRaises(ValueError):
            r.nearest_rank([],0.9)
if __name__=="__main__":unittest.main()

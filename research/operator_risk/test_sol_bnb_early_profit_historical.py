"""Synthetic testing for 5m SOL/BNB early exit historical translation. No internet."""
from pathlib import Path
from types import SimpleNamespace
import importlib.util
import unittest

MODULE=Path(__file__).with_name("sol_bnb_early_profit_historical.py")
spec=importlib.util.spec_from_file_location("sol_bnb_historical_synthetic",MODULE)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
ORIG_END=m.END
START=1672531200000
STEP=300000
TF=15*60*1000

def replay_fixture(edits=None, funds=None):
    points=[(100,101,99,100) for _ in range(12)]
    points[5]=(100,106,99,104.5)
    points[6]=(105,106,102,103.5)
    points[7]=(100,101,99,100)
    for n,vals in (edits or {}).items():
        points[n]=vals
    prices={START+i*STEP:dict(t=START+i*STEP,open=float(a),high=float(h),
               low=float(l),close=float(c),volume=500)
            for i,(a,h,l,c) in enumerate(points)}
    b=[prices[START]]
    fake=SimpleNamespace(load_parent=lambda:lambda bars:([True],{}))
    m.END=START+len(points)*STEP
    try:
        r=m.run_child("SOLUSDT",TF,b,prices,
                      {START+i*STEP:float(v) for i,v in (funds or {}).items()},
                      2,fake)
    finally:
        m.END=ORIG_END
    return r


class AltHistoricalSynthetic(unittest.TestCase):
    def test_1r_detection_next_open_half(self):
        x=replay_fixture()
        self.assertEqual(x["entries"],1)
        self.assertEqual(x["partially_realized_positions"],1)
        self.assertEqual(x["closed_trades"],1)
        legs=x["trade_legs"]
        self.assertEqual(legs[0]["reason"],"HALF_REALIZED")
        self.assertEqual(legs[0]["event_quote_t"],START+6*STEP)
        self.assertGreater(legs[0]["net"],0)
        self.assertEqual(legs[1]["reason"],"STOP_GAP")

    def test_stop_before_partial_on_adverse_gap(self):
        x=replay_fixture({6:(90,91,89,90)})
        self.assertEqual(x["partially_realized_positions"],0)
        self.assertEqual(x["exit_reasons"].get("STOP_GAP"),1)

    def test_extreme_high_is_not_proof_of_1r_close(self):
        x=replay_fixture({5:(100,110,99,103),
                          6:(103,104,100,102)})
        self.assertEqual(x["partially_realized_positions"],0)

    def test_half_net_gate_refuses_bad_next_open(self):
        x=replay_fixture({6:(100.5,103,99,102)})
        self.assertEqual(x["partially_realized_positions"],0)

    def test_funding_paid_refuses_unprofitable_half(self):
        x=replay_fixture(funds={5:0.04})
        self.assertEqual(x["partially_realized_positions"],0)
        self.assertLess(x["funding_paid_or_received"],0)

    def test_entry_on_strict_future_5m_bar(self):
        x=replay_fixture()
        self.assertTrue(all(l["entry_t"]==START+4*STEP for l in x["trade_legs"]))

    def test_cash_and_full_closed_legs_reconcile(self):
        x=replay_fixture()
        self.assertFalse(x["final_position_open"])
        self.assertAlmostEqual(x["cash_equity"],
            x["initial_equity"]+sum(l["net"] for l in x["trade_legs"]),places=5)

    def test_no_synthetic_inference_of_exchange_fills(self):
        x=replay_fixture()
        self.assertFalse(x["is_real_exchange_execution"])
        self.assertFalse(x["independent_oos"])


if __name__=="__main__":
    unittest.main()

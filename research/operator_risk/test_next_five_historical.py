"""Pre-market synthetic/frozen scope check for five early-exit variants."""
import unittest
from next_five_historical import CANDIDATES, M5, PARENT_COMMIT, COUNTS
from test_sol_bnb_early_profit_historical import replay_fixture


class NextFiveFixedScopeQA(unittest.TestCase):
    def test_pinned_five_and_no_asset_cherry_pick(self):
        self.assertEqual(tuple(CANDIDATES),("SOL5M","SOL4H","BNB30M","ETH1H","DOGE4H"))
        self.assertEqual(set(sym for sym,*_ in CANDIDATES.values()),
                         {"SOLUSDT","BNBUSDT","ETHUSDT","DOGEUSDT"})
    def test_native_5m_uses_5m_signal_not_1h(self):
        self.assertEqual(CANDIDATES["SOL5M"][1],M5)
        self.assertEqual(CANDIDATES["SOL5M"][3],182)
    def test_original_vendor_period_and_counts(self):
        self.assertEqual(COUNTS,{"5m":333216,"1h":27768,"funding":3288})
        self.assertEqual(PARENT_COMMIT,"42d6748864dd78b911b5f1fc775ff1950b556d2b")
    def test_all_parent_controls_have_both_fees(self):
        for _,(sym,tf,expected,n) in CANDIDATES.items():
            self.assertEqual(set(expected),{"BASE","STRESS"})
            self.assertTrue(all(0<x<100 for x in expected.values()))
            self.assertGreater(n,0)
            self.assertGreaterEqual(tf,M5)
            self.assertEqual(tf%M5,0)
    def test_historical_child_still_causal_exit_only(self):
        x=replay_fixture()
        self.assertEqual(x["partially_realized_positions"],1)
        self.assertEqual(x["trade_legs"][0]["reason"],"HALF_REALIZED")
        self.assertFalse(x["independent_oos"])
        self.assertFalse(x["is_real_exchange_execution"])

if __name__=="__main__": unittest.main()

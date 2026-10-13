"""Synthetic edge cases for path reconstruction, never past outcomes."""
import unittest
from research.btc_convex_1h_protection_20261013.trail_path_forensics import (
    FIVE,HOUR,audit_trade,summary)

T=1609545600000  # 2021-01-02 midnight UTC

def fixture(reset=False):
    prices={}
    last=24 if reset else 12
    for k in range(last):
        t=T+k*FIVE
        if k<12:
            close=110 if k==11 else 109
            prices[t]={"t":t,"open":100 if k==0 else 109,
                "high":112,"low":99 if k==0 else 106,"close":close}
        else:
            close=103 if k==23 else 105
            prices[t]={"t":t,"open":105,"high":110,"low":102,"close":close}
    stop=96. if reset else 112*.88
    prices[T+last*FIVE]={"t":T+last*FIVE,"open":102 if reset else 110,
           "high":110,"low":95,"close":101}
    row={"open_t":T,"close_t":T+(last+1)*FIVE,
         "entry_price":100.,"exit_price":stop*(1-.0002),
         "exit_reason":"STOP_INTRABAR","net_pnl":"-1","exit_year":"2021"}
    return prices,row

class TrailPathTests(unittest.TestCase):
    def test_effective_trailing_then_exit(self):
        bars,row=fixture(reset=False)
        p=audit_trade(row,bars,2)
        self.assertTrue(p["ever_close_activated_trail"])
        self.assertGreater(p["trail_closed_hours_with_stop_above_initial"],0)
        self.assertEqual(p["number_deactivations"],0)
        self.assertEqual(p["reset_weakened_protective_stop_count"],0)
        self.assertTrue(p["observed_model_exit_exact_parity"])

    def test_original_stop_reverts_after_close_falls_below_activation(self):
        bars,row=fixture(reset=True)
        p=audit_trade(row,bars,2)
        self.assertEqual(p["number_deactivations"],1)
        self.assertEqual(p["reset_weakened_protective_stop_count"],1)
        self.assertTrue(p["ever_close_activated_trail"])

    def test_wrong_exit_price_or_early_exit_blocks(self):
        bars,row=fixture(reset=True)
        row["exit_price"]=99.
        with self.assertRaisesRegex(ValueError,"EXACT_EXIT_PARITY_MISMATCH"):
            audit_trade(row,bars,2)

    def test_no_unobserved_high_on_exit_candle(self):
        bars,row=fixture(reset=True)
        bars[T+24*FIVE]["high"]=10000.
        p=audit_trade(row,bars,2)
        self.assertLess(p["price_runup_MFE_proxy_pct"],100)

    def test_aggregator_keeps_losing_activation_stats(self):
        bars,row=fixture(reset=True)
        p=audit_trade(row,bars,2)
        d=summary([p])
        self.assertEqual(d["count"],1)
        self.assertEqual(d["ever_trail_activated_and_lost"],1)
        self.assertEqual(d["trade_with_protective_stop_weakened"],1)

if __name__=="__main__":
    unittest.main()

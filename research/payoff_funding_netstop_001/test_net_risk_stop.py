"""Network-free QA for frozen funding-net-stop mathematical child."""
import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import net_risk_stop as risk

class NetStopTests(unittest.TestCase):
    BASE={"entry_fill":100.0,"qty":2.0,"initial_margin":100.0,
          "entry_fee_cash":0.16,"accrued_funding_cash":0.0}
    def stop(self,**kw):
        return risk.funding_adjusted_raw_stop(**{**self.BASE,**kw})

    def test_cash_exact_net_at_frozen_stop(self):
        for funding in (0.,-1.,-2.,-9.5,1.):
            price=self.stop(accrued_funding_cash=funding)
            net=risk.hypothetical_net_from_raw_exit(
                price,entry_fill=100.,qty=2.,entry_fee_cash=.16,
                accrued_funding_cash=funding,
                exit_fee_fraction=risk.FROZEN_EXIT_FEE_FRACTION,
                exit_slippage_fraction=risk.FROZEN_ADVERSE_EXIT_SLIPPAGE)
            self.assertAlmostEqual(net,-10.0,places=10)

    def test_negative_funding_moves_stop_up(self):
        a=self.stop(accrued_funding_cash=0)
        b=self.stop(accrued_funding_cash=-5)
        c=self.stop(accrued_funding_cash=-10)
        self.assertLess(a,b);self.assertLess(b,c)

    def test_positive_funding_moves_stop_down(self):
        self.assertLess(self.stop(accrued_funding_cash=3),
                        self.stop(accrued_funding_cash=0))

    def test_threshold_moves_above_entry_if_funding_bad_enough(self):
        self.assertGreater(self.stop(accrued_funding_cash=-20),100.)

    def test_initial_stop_stays_below_entry_for_zero_funding(self):
        self.assertLess(self.stop(),100.)

    def test_gap_exit_never_fabricates_stop_fill(self):
        threshold=self.stop()
        event=risk.next_observation_exit(threshold-2,threshold-3,threshold)
        self.assertEqual(event["decision"],"ADVERSE_STOP_GAP_AT_OPEN")
        self.assertEqual(event["hypothetical_raw_fill"],threshold-2)

    def test_stoptouch_not_guaranteed_real_fill(self):
        price=self.stop()
        hit=risk.next_observation_exit(price+1,price-1,price)
        self.assertEqual(hit["decision"],"STOP_TOUCHED_NO_FILL_GUARANTEE")

    def test_no_hit(self):
        price=self.stop()
        self.assertEqual(risk.next_observation_exit(price+3,price+1,price)["decision"],"NOT_TOUCHED")

    def test_invalid_input_fail_closed(self):
        for value in (float("nan"),float("inf"),0,-2):
            with self.assertRaises(risk.RiskInputBlocked):
                self.stop(qty=value)

    def test_margin_exceeds_notional_blocked(self):
        with self.assertRaisesRegex(risk.RiskInputBlocked,"MARGIN_GREATER"):
            self.stop(initial_margin=300.)

    def test_no_negative_fees_or_slippage(self):
        with self.assertRaises(risk.RiskInputBlocked):
            self.stop(exit_fee_fraction=-.001)
        with self.assertRaises(risk.RiskInputBlocked):
            self.stop(exit_slippage_fraction=-.1)

    def test_invalid_intrabar_data(self):
        with self.assertRaisesRegex(risk.RiskInputBlocked,"INVALID_BAR_LOW"):
            risk.next_observation_exit(100.,101.,99.)

if __name__=="__main__":unittest.main()

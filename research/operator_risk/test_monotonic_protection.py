"""Synthetic-only risk firewall regression, no broker or price feeds."""
import unittest
from decimal import Decimal
from monotonic_protection import (
    RiskRejected, size_with_stop, model_unit_stop_loss,
    cost_adjusted_breakeven, propose_completed_bar_trail
)


class PureRiskInvariants(unittest.TestCase):
    def size(self, **extra):
        opts=dict(
            side="LONG", equity="1000", remaining_global_risk="15",
            risk_fraction=".005", entry="100", stop="98",
            unit_step=".01", min_notional="10", available_margin="50",
            leverage="5", fee_entry_bps="8", fee_exit_bps="8",
            slip_entry_bps="2", slip_exit_bps="2", funding_reserve_bps="5")
        opts.update(extra)
        return size_with_stop(**opts)

    def trail(self, **extra):
        opts=dict(side="LONG", entry_fill="100", initial_stop="98",
                  acknowledged_stop="98", fresh_bbo="102.5",
                  observed_favorable_extreme="103", atr_confirmed="1",
                  atr_multiple="2", activation_r="1", breakeven="100.1",
                  tick=".1")
        opts.update(extra)
        return propose_completed_bar_trail(**opts)

    def test_long_loss_budget_and_adverse_fill_margin(self):
        s=self.size()
        self.assertGreater(s.units, 0)
        self.assertLessEqual(s.modeled_stop_loss_cash,Decimal("5"))
        self.assertLessEqual(s.initial_margin_estimate,Decimal("50"))
        self.assertEqual((s.units/Decimal(".01"))%1,0)

    def test_short_loss_budget(self):
        s=self.size(side="SHORT",stop="102")
        self.assertLessEqual(s.modeled_stop_loss_cash,Decimal("5"))

    def test_unsafe_min_contract_or_margin_rejected(self):
        with self.assertRaises(RiskRejected):
            self.size(min_notional="400")
        with self.assertRaises(RiskRejected):
            self.size(available_margin=".01")

    def test_unsafe_leverage_and_global_risk_rejected(self):
        with self.assertRaises(RiskRejected):
            self.size(leverage="10")
        with self.assertRaises(RiskRejected):
            self.size(remaining_global_risk=".0001")

    def test_wrong_side_stop_is_rejected(self):
        with self.assertRaises(RiskRejected):
            self.size(stop="105")
        with self.assertRaises(RiskRejected):
            model_unit_stop_loss("SHORT","100","98",8,8,2,2,5)

    def test_fee_and_signed_funding_breakeven_long(self):
        nofund=cost_adjusted_breakeven("LONG","100","2","0.16","0",8,5)
        paid=cost_adjusted_breakeven("LONG","100","2","0.16","-1",8,5)
        self.assertGreater(nofund,Decimal("100"))
        self.assertGreater(paid,nofund)

    def test_fee_and_signed_funding_breakeven_short(self):
        nofund=cost_adjusted_breakeven("SHORT","100","2","0.16","0",8,5)
        paid=cost_adjusted_breakeven("SHORT","100","2","0.16","-1",8,5)
        self.assertLess(nofund,Decimal("100"))
        self.assertLess(paid,nofund)

    def test_no_activation_no_change(self):
        self.assertEqual(self.trail(observed_favorable_extreme="101.9"),Decimal("98"))

    def test_long_monotonic_upgrade_and_no_reset(self):
        upgraded=self.trail()
        self.assertEqual(upgraded,Decimal("101"))
        kept=self.trail(acknowledged_stop=upgraded,observed_favorable_extreme="103",
                        atr_confirmed="2",fresh_bbo="102.5")
        self.assertEqual(kept,upgraded)

    def test_short_monotonic_upgrade(self):
        p=self.trail(side="SHORT",initial_stop="102",acknowledged_stop="102",
                     fresh_bbo="97.8",observed_favorable_extreme="97",
                     breakeven="99.9")
        self.assertEqual(p,Decimal("99"))

    def test_candidate_stop_crossed_by_fresh_market_fails(self):
        with self.assertRaisesRegex(RiskRejected,"NEW_STOP_ALREADY_CROSSED"):
            self.trail(fresh_bbo="99")
        with self.assertRaisesRegex(RiskRejected,"NEW_STOP_ALREADY_CROSSED"):
            self.trail(side="SHORT", initial_stop="102", acknowledged_stop="102",
                       fresh_bbo="100",observed_favorable_extreme="97",
                       breakeven="99.9")

    def test_prior_stop_already_crossed_fails(self):
        with self.assertRaisesRegex(RiskRejected,"UNPROTECTED_OR_CROSSED"):
            self.trail(fresh_bbo="97")

    def test_nonfinite_inputs_rejected(self):
        with self.assertRaises(RiskRejected):
            self.trail(atr_confirmed="NaN")
        with self.assertRaises(RiskRejected):
            self.size(equity="Infinity")


if __name__=="__main__":
    unittest.main()

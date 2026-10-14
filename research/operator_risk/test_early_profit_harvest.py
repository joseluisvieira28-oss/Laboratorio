"""Synthetic-only tests of operator-chosen early realisation; no live orders."""
import unittest
from decimal import Decimal
from early_profit_harvest import (
    propose_early_profit_close, propose_post_fill_breakeven_stop,
)
from monotonic_protection import RiskRejected


def base_close(**overrides):
    args=dict(side="LONG",entry_fill="100",initial_stop="98",
              full_quantity="2",original_entry_fee=".16",
              settled_signed_funding="0",modeled_initial_risk_cash="4.6",
              fresh_exit_quote="102.4",exit_fee_bps=8,exit_slip_bps=2,
              quantity_step=".01",minimum_close_quantity=".01",
              minimum_close_notional="10",quote_is_verified_fresh=True,
              broker_protective_stop_acknowledged=True)
    args.update(overrides)
    return propose_early_profit_close(**args)


def base_stop(**overrides):
    args=dict(side="LONG",entry_fill="100",initial_quantity="2",
              actually_closed_quantity="1",original_entry_fee=".16",
              signed_settled_funding_for_entire_trade="-.10",
              broker_acknowledged_prior_stop="98",
              actual_fresh_exit_quote="102.4",
              future_exit_fee_bps=8,future_exit_slip_bps=5,
              price_tick=".1",close_fill_independently_confirmed=True,
              remaining_stop_coverage_verified=True,
              quote_is_verified_fresh=True)
    args.update(overrides)
    return propose_post_fill_breakeven_stop(**args)


class EarlyHarvestSynthetic(unittest.TestCase):
    def test_long_half_close_after_plus_one_R(self):
        p=base_close()
        self.assertEqual(p.action,"HALF_CLOSE")
        self.assertEqual(p.quantity,Decimal("1"))
        self.assertEqual(p.remaining_units_if_filled,Decimal("1"))
        self.assertGreater(p.expected_realized_net,Decimal("1.15"))
        self.assertEqual(p.stage,"PROPOSAL_ONLY_NO_EXCHANGE_ORDER")

    def test_short_half_close_after_plus_one_R(self):
        p=base_close(side="SHORT",initial_stop="102",fresh_exit_quote="97.6")
        self.assertEqual(p.action,"HALF_CLOSE")
        self.assertGreater(p.expected_realized_net,p.minimum_realized_net)

    def test_not_yet_one_R(self):
        self.assertIsNone(base_close(fresh_exit_quote="101.99"))
        self.assertIsNone(base_close(side="SHORT",initial_stop="102",
                                      fresh_exit_quote="98.01"))

    def test_net_profit_gate_uses_signed_funding(self):
        self.assertIsNone(base_close(settled_signed_funding="-4"))
        self.assertIsNotNone(base_close(settled_signed_funding=".5"))

    def test_quote_and_broker_ack_required(self):
        with self.assertRaises(RiskRejected):
            base_close(quote_is_verified_fresh=False)
        with self.assertRaises(RiskRejected):
            base_close(broker_protective_stop_acknowledged=False)

    def test_full_exit_fallback_on_min_lot_half(self):
        p=base_close(full_quantity=".03",original_entry_fee=".0024",
                    modeled_initial_risk_cash=".07",
                    quantity_step=".01",minimum_close_quantity=".02",
                    minimum_close_notional="2")
        self.assertEqual(p.action,"FULL_CLOSE")
        self.assertEqual(p.remaining_units_if_filled,Decimal("0"))
        self.assertGreater(p.expected_realized_net,Decimal("0"))

    def test_reject_untradable_whole(self):
        with self.assertRaises(RiskRejected):
            base_close(full_quantity=".03",original_entry_fee=".0024",
                       modeled_initial_risk_cash=".07",
                       quantity_step=".01",minimum_close_quantity=".05",
                       minimum_close_notional="2")

    def test_invalid_risk_receipt_rejected(self):
        with self.assertRaisesRegex(RiskRejected,"MODEL_RISK_BELOW_PRICE_RISK"):
            base_close(modeled_initial_risk_cash="3")
        with self.assertRaises(RiskRejected):
            base_close(full_quantity="2.001")

    def test_long_postfill_net_break_even_monotonic(self):
        x=base_stop()
        self.assertGreater(x.proposed_stop,Decimal("100"))
        self.assertGreaterEqual(x.proposed_stop,Decimal("98"))
        self.assertLess(x.proposed_stop,Decimal("102.4"))
        self.assertTrue(x.still_unacknowledged)

    def test_short_postfill_net_break_even_monotonic(self):
        x=base_stop(side="SHORT",broker_acknowledged_prior_stop="102",
                    actual_fresh_exit_quote="97.6")
        self.assertLess(x.proposed_stop,Decimal("100"))
        self.assertLessEqual(x.proposed_stop,Decimal("102"))
        self.assertGreater(x.proposed_stop,Decimal("97.6"))

    def test_existing_tighter_long_stop_never_loosened(self):
        x=base_stop(broker_acknowledged_prior_stop="101")
        self.assertEqual(x.proposed_stop,Decimal("101"))

    def test_existing_tighter_short_stop_never_loosened(self):
        x=base_stop(side="SHORT",broker_acknowledged_prior_stop="99",
                    actual_fresh_exit_quote="97.6")
        self.assertEqual(x.proposed_stop,Decimal("99"))

    def test_no_postfill_stop_until_partial_fill_confirmed(self):
        for k in ("close_fill_independently_confirmed",
                  "remaining_stop_coverage_verified","quote_is_verified_fresh"):
            with self.assertRaises(RiskRejected):
                base_stop(**{k:False})

    def test_already_crossed_long_breakeven_refused(self):
        with self.assertRaisesRegex(RiskRejected,"CANDIDATE_STOP_ALREADY_CROSSED"):
            base_stop(actual_fresh_exit_quote="99")

    def test_already_crossed_short_breakeven_refused(self):
        with self.assertRaisesRegex(RiskRejected,"CANDIDATE_STOP_ALREADY_CROSSED"):
            base_stop(side="SHORT",broker_acknowledged_prior_stop="102",
                      actual_fresh_exit_quote="100")

    def test_no_remaining_qty(self):
        with self.assertRaisesRegex(RiskRejected,"NO_REMAINING_POSITION"):
            base_stop(actually_closed_quantity="2")

    def test_unrealized_book_profit_not_claimed(self):
        p=base_close()
        self.assertIn("PROPOSAL_ONLY",p.stage)
        self.assertTrue(base_stop().still_unacknowledged)


if __name__=="__main__":
    unittest.main()

"""All tests OFFLINE / SYNTHETIC, no exchange credentials or broker API."""
import json
import unittest
from decimal import Decimal
from pathlib import Path
from preflight_risk_only import (
    Blocked, preflight_config, modeled_long_quantity,
    check_collisions, diagnostic
)


class Prelive100DollarSafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads(
            Path(__file__).with_name("prelive_100usdt_configuration.json").read_text(encoding="utf-8")
        )

    def test_declared_equity_is_not_authenticated_account_equity(self):
        self.assertTrue(preflight_config(self.data))
        self.assertFalse(self.data["account_state_independently_verified"])
        self.assertEqual(self.data["operator_declared_existing_positions"] if "operator_declared_existing_positions" in self.data else self.data["operator_declared_open_positions"], 0)

    def test_no_live_status_always_even_with_synthetic_quotes(self):
        a=diagnostic(self.data,sample=True)
        self.assertEqual(a["result"],"NO_LIVE_GO")
        self.assertEqual(a["execution_authority"],"NONE")
        self.assertIn("SOL_USDT",a["synthetic_do_not_trade_examples"])

    def test_exactly_three_original_signals(self):
        a=diagnostic(self.data)
        self.assertEqual(tuple(x["tf_minutes"] for x in a["slots"]), (5,60,240))
        self.assertEqual(tuple(x["symbol"] for x in a["slots"]),("SOL_USDT","SOL_USDT","BNB_USDT"))

    def test_leverage_10_and_budgets_frozen(self):
        self.assertEqual(self.data["leverage_requested"],10)
        self.assertEqual(self.data["max_modeled_risk_per_trade_usdt"],"0.50")
        self.assertEqual(self.data["max_aggregate_modeled_risk_usdt"],"1.50")

    def test_synthetic_SOL_example_stays_below_half_USDT_budget(self):
        d=modeled_long_quantity(quote_ask="110",contract_step_base="0.1",
            minimum_contracts="1",maximum_contracts="100",
            fresh_contract_notional_min="1",equity_remaining_margin="100")
        self.assertLessEqual(Decimal(d["modeled_max_loss_at_stop_usdt"]),Decimal(".50"))
        self.assertLessEqual(Decimal(d["modeled_initial_margin_usdt"]),Decimal("100"))
        self.assertEqual(Decimal(d["base_quantity"]),Decimal(".1"))
        self.assertTrue(d["not_an_order"])

    def test_synthetic_BNB_example_is_quantized_correctly(self):
        d=modeled_long_quantity(quote_ask="750",contract_step_base="0.01",
            minimum_contracts="1",maximum_contracts="100",
            fresh_contract_notional_min="1",equity_remaining_margin="100")
        self.assertLessEqual(Decimal(d["modeled_max_loss_at_stop_usdt"]),Decimal(".50"))
        self.assertEqual(Decimal(d["base_quantity"]) % Decimal(".01"),0)

    def test_minimum_contract_that_breaks_budget_must_skip(self):
        with self.assertRaisesRegex(Blocked,"MIN_CONTRACT_EXCEEDS_RISK_OR_MARGIN"):
            modeled_long_quantity(quote_ask="110",contract_step_base="2",
                minimum_contracts="1",maximum_contracts="100",
                fresh_contract_notional_min="1",equity_remaining_margin="100")

    def test_minimum_notional_that_breaks_budget_must_skip(self):
        with self.assertRaisesRegex(Blocked,"MIN_NOTIONAL_EXCEEDS_RISK_BUDGET"):
            modeled_long_quantity(quote_ask="110",contract_step_base="0.1",
                minimum_contracts="1",maximum_contracts="100",
                fresh_contract_notional_min="100",equity_remaining_margin="100")

    def test_not_enough_initial_margin_must_skip(self):
        with self.assertRaises(Blocked):
            modeled_long_quantity(quote_ask="110",contract_step_base="0.1",
                minimum_contracts="1",maximum_contracts="100",
                fresh_contract_notional_min="1",equity_remaining_margin=".10")

    def test_unlimited_leverage_never_accepted(self):
        cfg=json.loads(json.dumps(self.data));cfg["leverage_requested"]=50
        with self.assertRaisesRegex(Blocked,"UNEXPECTED_LEVERAGE"):
            preflight_config(cfg)

    def test_cannot_arm_by_modifying_flag(self):
        cfg=json.loads(json.dumps(self.data));cfg["armed"]=True
        with self.assertRaisesRegex(Blocked,"UNARMED_ONLY"):
            preflight_config(cfg)

    def test_cannot_self_mark_actual_exchange_gates_green(self):
        cfg=json.loads(json.dumps(self.data))
        cfg["verified_live_gates"]["matching_broker_side_stop_ack"]=True
        with self.assertRaisesRegex(Blocked,"CANNOT_SELF_CERTIFY_LIVE_GATES"):
            preflight_config(cfg)

    def test_duplicate_SOL_physical_positions_blocked(self):
        with self.assertRaisesRegex(Blocked,"DUPLICATE_PHYSICAL_SYMBOL"):
            check_collisions([
                {"symbol":"SOL_USDT","risk_usdt":".50"},
                {"symbol":"SOL_USDT","risk_usdt":".50"}])

    def test_distinct_SOL_and_BNB_within_budget(self):
        d=check_collisions([
            {"symbol":"SOL_USDT","risk_usdt":".50"},
            {"symbol":"BNB_USDT","risk_usdt":".50"}])
        self.assertEqual(d["combined_risk_usdt"],"1.00")
        self.assertEqual(d["combined_SOL_risk_usdt"],".50")

    def test_over_budget_or_nonfinite_rejected(self):
        with self.assertRaises(Blocked):
            check_collisions([{"symbol":"BNB_USDT","risk_usdt":"NaN"}])
        with self.assertRaisesRegex(Blocked,"ACCOUNT_GLOBAL_OR_SYMBOL_RISK_LIMIT"):
            check_collisions([{"symbol":"BNB_USDT","risk_usdt":".51"}])

    def test_only_original_4_percent_price_stop_allowed(self):
        cfg=json.loads(json.dumps(self.data))
        cfg["strategy_slots"][0]["original_stop_price_fraction"]="0.02"
        with self.assertRaisesRegex(Blocked,"ORIGINAL_SCIENCE_CHANGED"):
            preflight_config(cfg)

    def test_fee_assumption_cannot_be_treated_as_account_proof(self):
        a=diagnostic(self.data)
        self.assertEqual(a["account_fee_schedule"],"NOT_CHECKED")
        self.assertEqual(a["stop_broker_ack"],"NOT_CHECKED")


if __name__=="__main__":
    unittest.main()

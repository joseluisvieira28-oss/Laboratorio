from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXEC = ROOT / "execution"


class OperatorFuturesPolicyTests(unittest.TestCase):
    def load(self, name):
        return json.loads((EXEC / name).read_text(encoding="utf-8"))

    def test_aggressive_policy_is_bound_without_science_credit(self):
        row = self.load("OPERATOR_FUTURES_BNB_CED1D_PREP_V01.json")
        self.assertEqual(
            row["governing_authorities"]["aggressive_policy"]["policy_id"],
            "ND-PROMOTION-POLICY-V3.0-FROZEN",
        )
        self.assertFalse(row["science_isolation"]["scientific_credit"])
        self.assertFalse(row["live_activation_authorized"])
        self.assertEqual(row["global_fail_closed"]["max_simultaneous_operator_positions"], 1)
        self.assertEqual(row["global_fail_closed"]["max_notional_usdt_per_operator_position"], 10)

    def test_fee_truth_uses_8bps_market_fill_floor_without_rewriting_science(self):
        row = self.load("MEXC_FUTURES_FEE_TRUTH_POLICY_V01.json")
        self.assertEqual(
            row["pre_entry_market_fee_model"]["mexc_api_futures_taker_floor_bps_per_fill"],
            8,
        )
        self.assertEqual(
            row["pre_entry_market_fee_model"]["single_leg_entry_exit_fee_only_roundtrip_bps"],
            16,
        )
        self.assertFalse(
            row["post_trade_accounting"]["real_receipts_may_rewrite_parent_scientific_cost_assumptions"]
        )

    def test_bnb_two_leg_synthetic_is_cost_blocked_against_stress30(self):
        row = self.load("MEXC_FUTURES_FEE_TRUTH_POLICY_V01.json")
        syn = row["route_diagnostics"]["BNB_BTC_relative_value_synthetic"]
        self.assertEqual(syn["fee_only_roundtrip_bps"], 32)
        self.assertGreater(syn["fee_only_roundtrip_bps"], syn["parent_stress_reference_bps"])
        self.assertEqual(syn["status"], "COST_BLOCKED_FOR_PARENT_EQUIVALENT_USE")

    def test_prearmed_authority_cannot_itself_submit_and_waits_for_runtime_gates(self):
        row = self.load("OPERATOR_FUTURES_BNB_CED1D_AUTHORITY_V01.json")
        self.assertEqual(row["status"], "PREARMED_LOCKED__NOT_ACTIVE_EXECUTION_AUTHORITY")
        self.assertFalse(row["activation_semantics"]["current_file_can_submit_order"])
        self.assertTrue(row["activation_semantics"]["no_arbitrary_forward_wait_after_all_gates_pass"])
        self.assertIn(
            "prior OPTIONS live trade CLOSED and POST_TRADE_RECONCILIATION present",
            row["activation_gates"],
        )


if __name__ == "__main__":
    unittest.main()

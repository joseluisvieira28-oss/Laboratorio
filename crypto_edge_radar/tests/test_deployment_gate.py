import unittest

from radar.deployment import (
    DeploymentGate,
    DeploymentMode,
    DeploymentProfile,
    RiskLimits,
    stop_based_position_size,
)


class DeploymentGateTests(unittest.TestCase):
    def test_tier4_is_blocked(self):
        decision = DeploymentGate.adjudicate(
            DeploymentProfile(
                strategy_id="STONE",
                scientific_tier=4,
                shadow_authorized=False,
                adapter_frozen=True,
                execution_instrument_frozen=True,
                cost_model_frozen=True,
                risk_model_frozen=True,
            )
        )
        self.assertEqual(decision.mode, DeploymentMode.BLOCKED)

    def test_tier3_is_shadow_only(self):
        decision = DeploymentGate.adjudicate(
            DeploymentProfile(
                strategy_id="WATCH",
                scientific_tier=3,
                shadow_authorized=True,
                adapter_frozen=True,
                execution_instrument_frozen=True,
                cost_model_frozen=True,
                risk_model_frozen=True,
            )
        )
        self.assertEqual(decision.mode, DeploymentMode.SHADOW_ONLY)

    def test_secondary_survivor_cannot_become_micro_live(self):
        decision = DeploymentGate.adjudicate(
            DeploymentProfile(
                strategy_id="SECONDARY",
                scientific_tier=2,
                shadow_authorized=True,
                adapter_frozen=True,
                execution_instrument_frozen=True,
                cost_model_frozen=True,
                risk_model_frozen=True,
                post_outcome_secondary=True,
            )
        )
        self.assertEqual(decision.mode, DeploymentMode.SHADOW_ONLY)

    def test_tier2_missing_risk_contract_remains_shadow(self):
        decision = DeploymentGate.adjudicate(
            DeploymentProfile(
                strategy_id="ETF-CME-INSTFLOW-001",
                scientific_tier=2,
                shadow_authorized=True,
                adapter_frozen=True,
                execution_instrument_frozen=True,
                cost_model_frozen=True,
                risk_model_frozen=False,
            )
        )
        self.assertEqual(decision.mode, DeploymentMode.SHADOW_ONLY)
        self.assertIn("RISK_MODEL", decision.reason)

    def test_complete_tier2_becomes_micro_live_advisory(self):
        decision = DeploymentGate.adjudicate(
            DeploymentProfile(
                strategy_id="ELIGIBLE",
                scientific_tier=2,
                shadow_authorized=True,
                adapter_frozen=True,
                execution_instrument_frozen=True,
                cost_model_frozen=True,
                risk_model_frozen=True,
            )
        )
        self.assertEqual(decision.mode, DeploymentMode.MICRO_LIVE_ADVISORY)

    def test_default_money_budgets(self):
        budgets = RiskLimits().money_budgets(5000.0)
        self.assertAlmostEqual(budgets["planned_risk_per_trade"], 5.0)
        self.assertAlmostEqual(budgets["max_simultaneous_planned_risk"], 15.0)
        self.assertAlmostEqual(budgets["daily_stop_amount"], 15.0)
        self.assertAlmostEqual(budgets["weekly_stop_amount"], 37.5)

    def test_stop_based_sizing(self):
        result = stop_based_position_size(
            account_equity=5000.0,
            entry_price=100.0,
            stop_price=98.0,
        )
        self.assertAlmostEqual(result["planned_risk"], 5.0)
        self.assertAlmostEqual(result["units"], 2.5)
        self.assertAlmostEqual(result["notional"], 250.0)

    def test_zero_stop_distance_fails_closed(self):
        with self.assertRaises(ValueError):
            stop_based_position_size(5000.0, 100.0, 100.0)


if __name__ == "__main__":
    unittest.main()

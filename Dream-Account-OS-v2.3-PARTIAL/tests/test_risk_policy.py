import unittest

from dream_account.config import Settings
from dream_account.risk_policy import RiskState, active_risk_pct, select_risk_state


class RiskPolicyTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()

    def test_frozen_policy_defaults(self):
        self.assertEqual(self.settings.normal_risk_pct, 1.0)
        self.assertEqual(self.settings.defensive_risk_pct, 0.5)
        self.assertFalse(hasattr(self.settings, "exceptional_risk_pct"))

    def test_normal_state(self):
        state = select_risk_state(4.99, 4, self.settings)
        self.assertIs(state, RiskState.NORMAL)
        self.assertEqual(active_risk_pct(state, self.settings), 1.0)

    def test_five_losses_activate_defensive(self):
        state = select_risk_state(0.0, 5, self.settings)
        self.assertIs(state, RiskState.DEFENSIVE)
        self.assertEqual(active_risk_pct(state, self.settings), 0.5)

    def test_five_percent_drawdown_activates_defensive(self):
        self.assertIs(select_risk_state(5.0, 0, self.settings), RiskState.DEFENSIVE)
        self.assertIs(select_risk_state(9.99, 0, self.settings), RiskState.DEFENSIVE)

    def test_ten_percent_drawdown_halts(self):
        state = select_risk_state(10.0, 0, self.settings)
        self.assertIs(state, RiskState.HALT)
        self.assertEqual(active_risk_pct(state, self.settings), 0.0)

    def test_a_plus_cannot_increase_risk(self):
        normal = active_risk_pct(select_risk_state(0.0, 0, self.settings), self.settings)
        a_plus = active_risk_pct(select_risk_state(0.0, 0, self.settings), self.settings)
        self.assertEqual(a_plus, normal)

    def test_invalid_state_inputs_fail_closed(self):
        for drawdown, losses in ((-0.1, 0), (0.0, -1), (None, 0)):
            with self.subTest(drawdown=drawdown, losses=losses), self.assertRaises(ValueError):
                select_risk_state(drawdown, losses, self.settings)


if __name__ == "__main__":
    unittest.main()

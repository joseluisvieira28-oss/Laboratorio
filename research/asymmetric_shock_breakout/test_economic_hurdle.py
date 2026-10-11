#!/usr/bin/env python3
"""Synthetic-only deterministic tests; no market outcomes."""
import unittest
from economic_hurdle import economic_hurdle


class EconomicHurdleTests(unittest.TestCase):
    def test_zero_cost_four_r(self):
        result = economic_hurdle(50, 4, fee_roundtrip_bps=0)
        self.assertAlmostEqual(result["breakeven_win_rate"], 0.2)
        self.assertEqual(result["net_win_r_if_target_filled"], 4)
        self.assertEqual(result["net_loss_r_if_stop_filled"], -1)

    def test_api_fee_hurdle_four_r(self):
        result = economic_hurdle(40, 4)
        self.assertAlmostEqual(result["cost_in_r"], .4)
        self.assertAlmostEqual(result["breakeven_win_rate"], .28)
        self.assertAlmostEqual(result["net_win_r_if_target_filled"], 3.6)

    def test_stress_and_slippage(self):
        result = economic_hurdle(40, 4, fee_roundtrip_bps=32, extra_execution_bps=8)
        self.assertAlmostEqual(result["breakeven_win_rate"], .4)

    def test_negative_edge_at_low_success_rate(self):
        result = economic_hurdle(40, 4, assumed_win_rate=.20)
        self.assertLess(result["hypothetical_expected_r"], 0)

    def test_nonpositive_net_target_flags_infeasibility(self):
        result = economic_hurdle(10, 1, fee_roundtrip_bps=16)
        self.assertFalse(result["target_net_positive_after_costs"])
        self.assertFalse(result["breakeven_feasible"])

    def test_bad_inputs_rejected(self):
        for args in [
            (0, 4, {}),
            (40, 0, {}),
            (40, 4, {"fee_roundtrip_bps": -1}),
            (40, 4, {"assumed_win_rate": 1.1}),
            (40, 4, {"extra_execution_bps": float("nan")}),
        ]:
            with self.assertRaises(ValueError):
                economic_hurdle(args[0], args[1], **args[2])


if __name__ == "__main__":
    unittest.main()

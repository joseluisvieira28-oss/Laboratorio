import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = ROOT / "research" / "market_reveal_confirmation_reaction_v01"
sys.path.insert(0, str(MODULE_DIR))

from measurements import (
    alignment_sign,
    log_return_bps,
    price_response_per_unit_flow,
    retracement_fraction,
    signed_flow_imbalance,
    state_vector,
)


class MetamorphicMeasurementTests(unittest.TestCase):
    def test_flow_imbalance_is_scale_invariant(self):
        a = signed_flow_imbalance(300.0, 100.0)
        b = signed_flow_imbalance(300_000.0, 100_000.0)
        self.assertAlmostEqual(a, b)

    def test_flow_swap_is_antisymmetric(self):
        a = signed_flow_imbalance(300.0, 100.0)
        b = signed_flow_imbalance(100.0, 300.0)
        self.assertAlmostEqual(a, -b)

    def test_alignment_preserved_under_simultaneous_sign_flip(self):
        self.assertEqual(alignment_sign(10.0, 0.5), 1)
        self.assertEqual(alignment_sign(-10.0, -0.5), 1)
        self.assertEqual(alignment_sign(10.0, -0.5), -1)
        self.assertEqual(alignment_sign(-10.0, 0.5), -1)

    def test_response_per_flow_preserved_under_simultaneous_sign_flip(self):
        positive = price_response_per_unit_flow(10.0, 0.5)
        negative = price_response_per_unit_flow(-10.0, -0.5)
        self.assertAlmostEqual(positive, negative)

    def test_price_scale_does_not_change_log_return(self):
        base = log_return_bps(100.0, 102.0)
        scaled = log_return_bps(1_000_000.0, 1_020_000.0)
        self.assertAlmostEqual(base, scaled, places=10)

    def test_price_scale_does_not_change_retracement_fraction(self):
        base = retracement_fraction(100.0, 104.0, 102.0)
        scaled = retracement_fraction(10_000.0, 10_400.0, 10_200.0)
        self.assertAlmostEqual(base, scaled)

    def test_state_vector_dimensionless_components_survive_joint_scale(self):
        base = state_vector(
            pre_mid=100.0,
            decision_mid=102.0,
            extreme_mid_to_decision=104.0,
            buy_notional=300.0,
            sell_notional=100.0,
            spread_pre=2.0,
            spread_now=3.0,
            max_spread_to_decision=4.0,
            depth_pre=1000.0,
            depth_now=800.0,
        )
        k = 1000.0
        scaled = state_vector(
            pre_mid=100.0 * k,
            decision_mid=102.0 * k,
            extreme_mid_to_decision=104.0 * k,
            buy_notional=300.0 * k,
            sell_notional=100.0 * k,
            spread_pre=2.0 * k,
            spread_now=3.0 * k,
            max_spread_to_decision=4.0 * k,
            depth_pre=1000.0 * k,
            depth_now=800.0 * k,
        )

        for key in (
            "flow_imbalance",
            "decision_return_bps",
            "price_response_per_unit_flow",
            "alignment_sign",
            "retracement_fraction",
            "spread_vs_pre",
            "spread_vs_max_to_decision",
            "depth_vs_pre",
        ):
            self.assertTrue(
                math.isclose(base[key], scaled[key], rel_tol=1e-12, abs_tol=1e-12),
                key,
            )

        self.assertTrue(
            math.isclose(
                scaled["effort_per_result"],
                base["effort_per_result"] * k,
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        )


if __name__ == "__main__":
    unittest.main()

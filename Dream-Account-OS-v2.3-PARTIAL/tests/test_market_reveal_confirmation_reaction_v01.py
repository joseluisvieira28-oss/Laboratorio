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


class MarketRevealMeasurementsTests(unittest.TestCase):
    def test_signed_flow_imbalance(self):
        self.assertAlmostEqual(signed_flow_imbalance(800.0, 200.0), 0.6)
        self.assertAlmostEqual(signed_flow_imbalance(200.0, 800.0), -0.6)
        self.assertIsNone(signed_flow_imbalance(0.0, 0.0))

    def test_alignment_is_symmetric(self):
        self.assertEqual(alignment_sign(10.0, 0.5), 1)
        self.assertEqual(alignment_sign(-10.0, -0.5), 1)
        self.assertEqual(alignment_sign(10.0, -0.5), -1)
        self.assertEqual(alignment_sign(-10.0, 0.5), -1)

    def test_retracement_positive_impulse(self):
        self.assertAlmostEqual(retracement_fraction(100.0, 101.0, 100.25), 0.75)

    def test_retracement_negative_impulse(self):
        self.assertAlmostEqual(retracement_fraction(100.0, 99.0, 99.75), 0.75)

    def test_response_per_flow(self):
        ret = log_return_bps(100.0, 101.0)
        flow = signed_flow_imbalance(800.0, 200.0)
        response = price_response_per_unit_flow(ret, flow)
        self.assertGreater(response, 0.0)

    def test_state_vector_contains_only_decision_state_measurements(self):
        vector = state_vector(
            pre_mid=100.0,
            decision_mid=100.5,
            extreme_mid_to_decision=100.8,
            buy_notional=700.0,
            sell_notional=300.0,
            spread_pre=1.0,
            spread_now=1.5,
            max_spread_to_decision=2.0,
            depth_pre=100.0,
            depth_now=80.0,
        )
        expected = {
            "flow_imbalance",
            "decision_return_bps",
            "price_response_per_unit_flow",
            "alignment_sign",
            "retracement_fraction",
            "spread_vs_pre",
            "spread_vs_max_to_decision",
            "depth_vs_pre",
            "effort_per_result",
        }
        self.assertEqual(set(vector.keys()), expected)

    def test_invalid_prices_fail_closed(self):
        with self.assertRaises(ValueError):
            log_return_bps(0.0, 100.0)


if __name__ == "__main__":
    unittest.main()

import math
import unittest

from research.ll0017_top_global_positioning_v01 import (
    aligned_return,
    net_bps,
    source_gate,
    threshold_cross_direction,
    top_account_global_diagnostic,
    top_global_divergence,
    top_size_skew_diagnostic,
)


class LL0017FrozenSemanticsTests(unittest.TestCase):
    def test_primary_divergence_is_log_ratio_difference(self):
        self.assertAlmostEqual(top_global_divergence(1.50, 1.00), math.log(1.5))

    def test_positive_cross_follows_top_positioning(self):
        self.assertEqual(threshold_cross_direction(1.51, 1.49), 1)

    def test_negative_cross_follows_top_positioning(self):
        self.assertEqual(threshold_cross_direction(-1.51, -1.49), -1)

    def test_state_without_new_cross_is_not_new_event(self):
        self.assertEqual(threshold_cross_direction(2.0, 1.8), 0)

    def test_alignment_and_cost(self):
        self.assertAlmostEqual(aligned_return(-1, -0.003), 0.003)
        self.assertAlmostEqual(net_bps(-1, -0.003, 14.0), 16.0)

    def test_diagnostics_do_not_change_primary_definition(self):
        self.assertAlmostEqual(top_account_global_diagnostic(1.2, 1.0), math.log(1.2))
        self.assertAlmostEqual(top_size_skew_diagnostic(1.5, 1.2), math.log(1.25))

    def test_source_gate_fail_closed(self):
        ok, reasons = source_gate(
            top_position_coverage=0.999,
            global_account_coverage=0.98,
            price_coverage=1.0,
            checksums_ok=True,
        )
        self.assertFalse(ok)
        self.assertEqual(reasons, ("global_account_coverage",))


if __name__ == "__main__":
    unittest.main()

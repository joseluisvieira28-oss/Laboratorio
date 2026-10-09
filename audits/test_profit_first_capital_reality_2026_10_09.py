"""Hermetic descriptive reconciliation against the already-public Oct 9 14-row CED1D sample.

Not an execution strategy, a backtest, or a source of new scientific authority.
"""
from __future__ import annotations
import unittest

BASE_REFERENCE_BPS = (
    -904.7633571872224,
    -82.3396703157782,
    456.81172207780963,
    144.0883777923428,
    26.26408973827207,
    -286.8087725178937,
    758.975056162407,
    -451.53028963568715,
    31.043501257432492,
    -190.49253515803107,
    292.65011375278254,
    -42.316762493255524,
    7.443912359309294,
    422.9148713721414,
)

class ProfitFirstCapitalReality(unittest.TestCase):
    def test_receipt_total_and_counts(self):
        self.assertEqual(len(BASE_REFERENCE_BPS), 14)
        self.assertEqual(sum(x > 0 for x in BASE_REFERENCE_BPS), 8)
        self.assertEqual(sum(x < 0 for x in BASE_REFERENCE_BPS), 6)
        self.assertAlmostEqual(sum(BASE_REFERENCE_BPS), 181.94025720462918, places=7)
        self.assertAlmostEqual(sum(BASE_REFERENCE_BPS) / 14, 12.995732657473512)

    def test_tail_risk_without_optimizing_strategy(self):
        self.assertAlmostEqual(min(BASE_REFERENCE_BPS), -904.7633571872224)
        self.assertAlmostEqual(max(BASE_REFERENCE_BPS), 758.975056162407)
        positives = sorted(BASE_REFERENCE_BPS, reverse=True)
        remaining = (sum(BASE_REFERENCE_BPS) - positives[0] - positives[1]) / 12
        self.assertAlmostEqual(remaining, -86.15387675296563)
        self.assertLess(remaining, 0)

    def test_small_notional_is_small_absolute_income(self):
        mean_pnl_usdt = (sum(BASE_REFERENCE_BPS) / 14) / 10_000 * 100
        self.assertAlmostEqual(mean_pnl_usdt, 0.12995732657473512)
        worst_100_usdt = min(BASE_REFERENCE_BPS) / 10_000 * 100
        self.assertLess(worst_100_usdt, -9.0)

    def test_losing_day_blocks_any_claim_of_fixed_ten_percent_margin_loss_at_high_leverage(self):
        worst_fraction = abs(min(BASE_REFERENCE_BPS)) / 10_000
        observed_best_fraction = max(BASE_REFERENCE_BPS) / 10_000
        leverage_to_make_best_win_40pct = 0.40 / observed_best_fraction
        implied_worst_margin_loss = worst_fraction * leverage_to_make_best_win_40pct
        self.assertGreater(leverage_to_make_best_win_40pct, 5)
        self.assertGreater(implied_worst_margin_loss, 0.45)


if __name__ == "__main__":
    unittest.main()

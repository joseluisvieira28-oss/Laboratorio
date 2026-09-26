import unittest

from dream_account.config import Settings
from dream_account.engines import (
    calculate_costs,
    confirmed_breakout_retest,
    depth_notional,
    estimated_slippage_pct,
    exchange_feasible_quantity,
    position_size,
    rvol,
    score_candidate,
    total_risk_position_size,
)
from dream_account.fixtures import candles, liquid_book
from dream_account.models import Candidate


class EngineTests(unittest.TestCase):
    def test_only_closed_candle_breakout_and_retest(self):
        active, evidence = confirmed_breakout_retest(candles(105.5, 107), 107, 106.5, 107)
        self.assertTrue(active)
        self.assertIn("breakout_close_time", evidence)

    def test_wick_is_not_breakout(self):
        data = candles(105.5)
        data[-2].high, data[-2].close = 108, 106.8
        active, _ = confirmed_breakout_retest(data, 107, 106.5, 107)
        self.assertFalse(active)

    def test_unclosed_candle_is_ignored(self):
        data = candles(105.5, 107)
        data[-2].closed = False
        active, _ = confirmed_breakout_retest(data, 107, 106.5, 107)
        self.assertFalse(active)

    def test_spread_and_depth(self):
        book = liquid_book()
        self.assertLess(book.spread_pct, 0.2)
        bid, ask = depth_notional(book, 0.5)
        self.assertGreater(bid, 0)
        self.assertGreater(ask, 0)

    def test_slippage(self):
        self.assertIsNotNone(estimated_slippage_pct(liquid_book(), "BUY", 50))

    def test_position_sizing_is_balance_capped(self):
        result = position_size(56, 2, 100, 98, 56)
        self.assertEqual(result["position_notional_chf"], 56)
        self.assertAlmostEqual(result["actual_risk_chf"], 1.12)

    def test_legacy_position_sizing_cannot_infer_leverage(self):
        result = position_size(56, 2, 100, 99.5, 1_000)
        self.assertEqual(result["position_notional_chf"], 56)

    def test_normal_percentage_point_contract(self):
        result = total_risk_position_size(56, 1.0, 100, 99, 0.0, 56)
        self.assertAlmostEqual(result["target_total_risk_chf"], 0.56)
        self.assertAlmostEqual(result["theoretical_notional_chf"], 56.0)
        self.assertAlmostEqual(result["position_notional_chf"], 56.0)
        self.assertAlmostEqual(result["price_risk_chf"], 0.56)
        self.assertAlmostEqual(result["actual_total_risk_chf"], 0.56)

    def test_spot_cap_accepts_lower_actual_risk_without_leverage(self):
        result = total_risk_position_size(56, 1.0, 100, 99.5, 0.0, 56)
        self.assertAlmostEqual(result["theoretical_notional_chf"], 112.0)
        self.assertAlmostEqual(result["position_notional_chf"], 56.0)
        self.assertAlmostEqual(result["price_risk_chf"], 0.28)
        self.assertTrue(result["capital_capped"])

    def test_costs_are_inside_total_risk_ceiling(self):
        result = total_risk_position_size(56, 1.0, 100, 99, 0.10, 56)
        self.assertLess(result["position_notional_chf"], 56)
        self.assertAlmostEqual(result["actual_total_risk_chf"], 0.56)
        self.assertLessEqual(result["actual_total_risk_chf"], result["target_total_risk_chf"])

    def test_missing_or_invalid_risk_inputs_fail_closed(self):
        for args in (
            (56, 1.0, 100, 100, 0.10, 56),
            (56, 1.0, 100, 99, None, 56),
            (56, 1.0, 100, 99, -0.1, 56),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                total_risk_position_size(*args)

    def test_exchange_minimum_never_enlarges_safe_order(self):
        sizing = total_risk_position_size(56, 0.5, 100, 99, 0.10, 56)
        with self.assertRaises(ValueError):
            exchange_feasible_quantity(
                sizing,
                entry=100,
                min_quantity=1.0,
                min_notional=100.0,
                quantity_step=0.01,
                tick_size=0.01,
            )

    def test_missing_exchange_precision_fails_closed(self):
        sizing = total_risk_position_size(56, 1.0, 100, 99, 0.10, 56)
        with self.assertRaises(ValueError):
            exchange_feasible_quantity(
                sizing,
                entry=100,
                min_quantity=0.01,
                min_notional=5.0,
                quantity_step=None,
                tick_size=0.01,
            )

    def test_costs_reduce_rr(self):
        result = calculate_costs(100, 98, 106, 0.1, 0.05, 0.02)
        self.assertGreater(result.gross_rr, result.net_rr)

    def test_rvol(self):
        data = candles(100)
        data[-1].volume = 4000
        self.assertGreater(rvol(data), 2)

    def test_hard_filter_overrides_score(self):
        candidate = Candidate("THINUSDT", "SPOT", 1, 100_000, 0.7, {"1h": 1, "24h": 2}, 2, "RISK_ON_TREND", "BREAKOUT_RETEST")
        candidate.status = "LONG_CANDIDATE"
        score_candidate(candidate, Settings(), 4, catalyst_confirmed=True, futures_available=True)
        self.assertEqual(candidate.status, "NO_TRADE")
        self.assertIn("spread_hard_reject", candidate.rejection_reasons)


if __name__ == "__main__":
    unittest.main()

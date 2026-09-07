import unittest

from dream_account.config import Settings
from dream_account.engines import calculate_costs, confirmed_breakout_retest, depth_notional, estimated_slippage_pct, position_size, rvol, score_candidate
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

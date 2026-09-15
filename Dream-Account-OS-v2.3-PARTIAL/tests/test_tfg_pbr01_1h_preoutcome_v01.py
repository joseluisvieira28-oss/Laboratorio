from __future__ import annotations

import unittest

from dream_account.models import Candle
from research.timeframe_gap.tfg_pbr01_1h_preoutcome_v01 import (
    CANDLES_PER_1H,
    FIFTEEN_MIN_MS,
    ONE_H_MS,
    OUTCOME_COMPUTATION_AUTHORIZED,
    RESEARCH_TIMEFRAME,
    ResearchParameters1H,
    aggregate_15m_to_1h,
    preoutcome_summary,
    split_1h_segments,
    validate_1h_candles,
)


def c15(open_time: int, o: float, h: float, l: float, c: float, v: float = 1.0) -> Candle:
    return Candle(open_time, o, h, l, c, v, open_time + FIFTEEN_MIN_MS - 1, True)


def c1h(open_time: int, px: float = 100.0) -> Candle:
    return Candle(open_time, px, px + 1, px - 1, px + 0.25, 4.0, open_time + ONE_H_MS - 1, True)


class TfgPbr011HPreoutcomeTests(unittest.TestCase):
    def test_outcomes_are_hard_blocked(self):
        self.assertFalse(OUTCOME_COMPUTATION_AUTHORIZED)

    def test_parameters_match_frozen_bar_count_transport(self):
        p = ResearchParameters1H()
        p.validate()
        self.assertEqual(p.timeframe, RESEARCH_TIMEFRAME)
        self.assertEqual(p.lookback_bars, 96)
        self.assertEqual(p.atr_length, 14)
        self.assertEqual(p.retest_window_bars, 2)
        self.assertEqual(p.max_holding_bars, 96)
        self.assertEqual(p.zone_atr_fraction, 0.25)
        self.assertEqual(p.stop_atr_fraction, 0.25)
        self.assertEqual(p.tp2_r_multiple, 3.0)
        self.assertEqual(p.min_net_rr, 2.0)

    def test_non_1h_parameter_is_rejected(self):
        with self.assertRaises(ValueError):
            ResearchParameters1H(timeframe="4h").validate()

    def test_exact_four_15m_candles_aggregate_to_one_hour(self):
        rows = [
            c15(0 * FIFTEEN_MIN_MS, 100, 103, 99, 102, 1),
            c15(1 * FIFTEEN_MIN_MS, 102, 105, 101, 104, 2),
            c15(2 * FIFTEEN_MIN_MS, 104, 106, 98, 99, 3),
            c15(3 * FIFTEEN_MIN_MS, 99, 101, 97, 100, 4),
        ]
        out = aggregate_15m_to_1h(rows)
        self.assertEqual(CANDLES_PER_1H, 4)
        self.assertEqual(len(out), 1)
        bar = out[0]
        self.assertEqual(bar.open_time, 0)
        self.assertEqual(bar.close_time, ONE_H_MS - 1)
        self.assertEqual(bar.open, 100)
        self.assertEqual(bar.high, 106)
        self.assertEqual(bar.low, 97)
        self.assertEqual(bar.close, 100)
        self.assertEqual(bar.volume, 10)

    def test_missing_15m_candle_drops_whole_hour(self):
        rows = [
            c15(0 * FIFTEEN_MIN_MS, 100, 101, 99, 100),
            c15(1 * FIFTEEN_MIN_MS, 100, 101, 99, 100),
            c15(3 * FIFTEEN_MIN_MS, 100, 101, 99, 100),
        ]
        self.assertEqual(aggregate_15m_to_1h(rows), [])

    def test_duplicate_15m_timestamp_fails_closed(self):
        row = c15(0, 100, 101, 99, 100)
        with self.assertRaises(ValueError):
            aggregate_15m_to_1h([row, row])

    def test_misaligned_1h_bar_is_rejected(self):
        bad = Candle(FIFTEEN_MIN_MS, 100, 101, 99, 100, 1, FIFTEEN_MIN_MS + ONE_H_MS - 1, True)
        with self.assertRaises(ValueError):
            validate_1h_candles([bad])

    def test_gap_splits_segments_without_bridging(self):
        bars = [c1h(0), c1h(ONE_H_MS), c1h(3 * ONE_H_MS)]
        segments, gaps = split_1h_segments(bars)
        self.assertEqual(gaps, 1)
        self.assertEqual([len(x) for x in segments], [2, 1])

    def test_preoutcome_summary_exposes_no_performance_metric(self):
        summary = preoutcome_summary([c1h(0), c1h(ONE_H_MS)])
        self.assertFalse(summary["outcome_computation_authorized"])
        forbidden = {"pnl", "expectancy", "profit_factor", "win_rate", "return", "net_r"}
        self.assertTrue(forbidden.isdisjoint(summary.keys()))


if __name__ == "__main__":
    unittest.main()

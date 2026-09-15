from __future__ import annotations

import unittest

from dream_account.models import Candle
from research.timeframe_gap.tfg_pbr01_1d_preoutcome_v01 import (
    CANDLES_PER_1D,
    FIFTEEN_MIN_MS,
    ONE_DAY_MS,
    OUTCOME_COMPUTATION_AUTHORIZED,
    RESEARCH_TIMEFRAME,
    ResearchParameters1D,
    aggregate_15m_to_1d,
    preoutcome_summary,
    split_1d_segments,
    validate_1d_candles,
)


def c15(open_time: int, o: float, h: float, l: float, c: float, v: float = 1.0) -> Candle:
    return Candle(open_time, o, h, l, c, v, open_time + FIFTEEN_MIN_MS - 1, True)


def c1d(open_time: int, px: float = 100.0) -> Candle:
    return Candle(open_time, px, px + 1, px - 1, px + 0.25, 96.0, open_time + ONE_DAY_MS - 1, True)


class TfgPbr011DPreoutcomeTests(unittest.TestCase):
    def test_outcomes_are_hard_blocked(self):
        self.assertFalse(OUTCOME_COMPUTATION_AUTHORIZED)

    def test_parameters_match_frozen_bar_count_transport(self):
        p = ResearchParameters1D()
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

    def test_non_1d_parameter_is_rejected(self):
        with self.assertRaises(ValueError):
            ResearchParameters1D(timeframe="4h").validate()

    def test_exact_96_15m_candles_aggregate_to_one_utc_day(self):
        rows = []
        for i in range(CANDLES_PER_1D):
            o = 100.0 + i * 0.01
            rows.append(c15(i * FIFTEEN_MIN_MS, o, o + 1, o - 1, o + 0.25, 1.0))
        out = aggregate_15m_to_1d(rows)
        self.assertEqual(CANDLES_PER_1D, 96)
        self.assertEqual(len(out), 1)
        bar = out[0]
        self.assertEqual(bar.open_time, 0)
        self.assertEqual(bar.close_time, ONE_DAY_MS - 1)
        self.assertEqual(bar.open, rows[0].open)
        self.assertEqual(bar.high, max(x.high for x in rows))
        self.assertEqual(bar.low, min(x.low for x in rows))
        self.assertEqual(bar.close, rows[-1].close)
        self.assertEqual(bar.volume, 96.0)

    def test_missing_single_15m_candle_drops_whole_day(self):
        rows = [c15(i * FIFTEEN_MIN_MS, 100, 101, 99, 100) for i in range(CANDLES_PER_1D) if i != 37]
        self.assertEqual(aggregate_15m_to_1d(rows), [])

    def test_partial_last_day_is_dropped_not_filled(self):
        complete = [c15(i * FIFTEEN_MIN_MS, 100, 101, 99, 100) for i in range(CANDLES_PER_1D)]
        partial = [c15(ONE_DAY_MS + i * FIFTEEN_MIN_MS, 100, 101, 99, 100) for i in range(65)]
        out = aggregate_15m_to_1d(complete + partial)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].open_time, 0)

    def test_duplicate_15m_timestamp_fails_closed(self):
        row = c15(0, 100, 101, 99, 100)
        with self.assertRaises(ValueError):
            aggregate_15m_to_1d([row, row])

    def test_misaligned_daily_bar_is_rejected(self):
        bad = Candle(FIFTEEN_MIN_MS, 100, 101, 99, 100, 1, FIFTEEN_MIN_MS + ONE_DAY_MS - 1, True)
        with self.assertRaises(ValueError):
            validate_1d_candles([bad])

    def test_gap_splits_daily_segments_without_bridging(self):
        bars = [c1d(0), c1d(ONE_DAY_MS), c1d(3 * ONE_DAY_MS)]
        segments, gaps = split_1d_segments(bars)
        self.assertEqual(gaps, 1)
        self.assertEqual([len(x) for x in segments], [2, 1])

    def test_preoutcome_summary_exposes_no_performance_metric(self):
        summary = preoutcome_summary([c1d(0), c1d(ONE_DAY_MS)])
        self.assertFalse(summary["outcome_computation_authorized"])
        forbidden = {"pnl", "expectancy", "profit_factor", "win_rate", "return", "net_r"}
        self.assertTrue(forbidden.isdisjoint(summary.keys()))


if __name__ == "__main__":
    unittest.main()

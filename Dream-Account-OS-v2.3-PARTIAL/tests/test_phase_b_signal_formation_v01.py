import math
from pathlib import Path
import unittest

from dream_account.models import Candle
from research.phase_b_signal_formation_v01 import (
    CostAssumptions,
    ResearchParameters,
    derive_signal_geometries,
    simulate_outcome,
    validate_candles,
)


STEP = 15 * 60 * 1000
ROOT = Path(__file__).resolve().parents[1]


def candle(index, open_, high, low, close, *, closed=True, open_time=None):
    timestamp = index * STEP if open_time is None else open_time
    return Candle(
        open_time=timestamp,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1_000.0,
        close_time=timestamp + STEP - 1,
        closed=closed,
    )


def base_series():
    return [
        candle(0, 97.5, 98.0, 97.0, 97.8),
        candle(1, 97.8, 99.0, 97.5, 98.8),
        candle(2, 98.8, 100.0, 98.5, 99.5),
        candle(3, 99.5, 99.8, 99.0, 99.4),
        candle(4, 99.8, 101.2, 99.7, 101.0),
        candle(5, 101.0, 101.1, 99.8, 100.1),
        candle(6, 100.2, 101.0, 100.0, 100.6),
        candle(7, 100.6, 103.0, 100.4, 102.7),
    ]


def params(**overrides):
    values = dict(
        timeframe="15m",
        lookback_bars=4,
        atr_length=2,
        zone_atr_fraction=0.25,
        retest_window_bars=2,
        stop_atr_fraction=0.25,
        tp1_r_multiple=1.0,
        tp2_r_multiple=3.0,
        min_net_rr=2.0,
        max_holding_bars=2,
        require_bullish_breakout_body=True,
    )
    values.update(overrides)
    return ResearchParameters(**values)


def base_costs():
    return CostAssumptions("BASE_SENSITIVITY", 0.05, 0.05, 0.025)


def first_signal(series=None, p=None, costs=None):
    signals = derive_signal_geometries(series or base_series(), p or params(), costs or base_costs())
    if not signals:
        raise AssertionError("synthetic fixture did not create a signal")
    return signals[0]


class PhaseBSignalFormationV01Tests(unittest.TestCase):
    def test_base_fixture_forms_geometry_but_never_authorizes_trade(self):
        signal = first_signal()
        self.assertEqual(signal.geometry_status, "GEOMETRY_READY")
        self.assertFalse(signal.full_trade_authorized)
        self.assertFalse(signal.submitted_to_exchange)
        self.assertTrue(signal.full_trade_blockers)

    def test_reference_level_excludes_breakout_candle(self):
        series = base_series()
        series[4] = candle(4, 99.8, 120.0, 99.7, 101.0)
        signal = first_signal(series)
        self.assertAlmostEqual(signal.resistance, 100.0)

    def test_unclosed_future_candle_does_not_change_signal(self):
        baseline = first_signal()
        series = base_series() + [candle(8, 1_000.0, 2_000.0, 1.0, 1_500.0, closed=False)]
        signal = first_signal(series)
        self.assertEqual(signal.fingerprint, baseline.fingerprint)

    def test_wick_only_breakout_is_rejected(self):
        series = base_series()
        series[4] = candle(4, 99.8, 101.2, 99.7, 99.9)
        self.assertEqual(derive_signal_geometries(series, params(), base_costs()), [])

    def test_bearish_body_breakout_is_rejected_when_required(self):
        series = base_series()
        series[4] = candle(4, 101.1, 101.3, 100.2, 100.5)
        self.assertEqual(derive_signal_geometries(series, params(), base_costs()), [])

    def test_defended_retest_is_first_touch_and_is_accepted(self):
        signal = first_signal()
        self.assertEqual(signal.retest_open_time, 5 * STEP)
        self.assertGreaterEqual(signal.retest_low, signal.zone_low)
        self.assertGreaterEqual(signal.retest_close, signal.zone_high)

    def test_retest_breaking_zone_low_invalidates_setup(self):
        series = base_series()
        series[5] = candle(5, 101.0, 101.1, 99.0, 100.1)
        self.assertEqual(derive_signal_geometries(series, params(), base_costs()), [])

    def test_first_zone_touch_closing_below_reclaimed_level_invalidates_setup(self):
        series = base_series()
        series[5] = candle(5, 101.0, 101.1, 99.8, 99.9)
        series[6] = candle(6, 100.3, 100.8, 99.9, 100.4)
        self.assertEqual(derive_signal_geometries(series, params(), base_costs()), [])

    def test_retest_after_frozen_window_is_not_accepted(self):
        series = base_series()
        series[5] = candle(5, 101.0, 101.1, 100.2, 100.8)
        series[6] = candle(6, 100.8, 101.0, 100.3, 100.7)
        series[7] = candle(7, 100.7, 101.0, 99.8, 100.2)
        self.assertEqual(derive_signal_geometries(series, params(retest_window_bars=2), base_costs()), [])

    def test_entry_is_next_bar_open_not_retest_close(self):
        signal = first_signal()
        self.assertEqual(signal.entry_open_time, 6 * STEP)
        self.assertAlmostEqual(signal.entry, 100.2)
        self.assertNotAlmostEqual(signal.entry, signal.retest_close)

    def test_reclaimed_level_lost_before_entry_cancels_setup(self):
        series = base_series()
        series[6] = candle(6, 99.9, 100.5, 99.7, 100.2)
        self.assertEqual(derive_signal_geometries(series, params(), base_costs()), [])

    def test_stop_is_structurally_below_zone(self):
        signal = first_signal()
        self.assertLess(signal.stop, signal.zone_low)
        self.assertGreater(signal.entry, signal.stop)

    def test_targets_are_exact_r_multiples(self):
        signal = first_signal()
        r_value = signal.entry - signal.stop
        self.assertAlmostEqual(signal.tp1, signal.entry + r_value)
        self.assertAlmostEqual(signal.tp2, signal.entry + 3.0 * r_value)
        self.assertAlmostEqual(signal.gross_rr_tp2, 3.0)

    def test_cost_scenario_is_explicit_and_matches_20_bps_total(self):
        costs = base_costs()
        self.assertAlmostEqual(costs.round_trip_cost_pct, 0.20)
        signal = first_signal(costs=costs)
        self.assertAlmostEqual(signal.estimated_round_trip_cost_pct, 0.20)

    def test_invalid_cost_inputs_fail_closed(self):
        bad = CostAssumptions("BAD", 0.05, -0.01, 0.0)
        with self.assertRaises(ValueError):
            derive_signal_geometries(base_series(), params(), bad)

    def test_net_rr_below_two_is_explicit_rejection(self):
        severe = CostAssumptions("VERY_HIGH_COST", 0.25, 0.50, 0.25)
        signal = first_signal(costs=severe)
        self.assertLess(signal.net_rr_tp2, 2.0)
        self.assertEqual(signal.geometry_status, "REJECTED_NET_RR")

    def test_insufficient_history_produces_no_signal(self):
        self.assertEqual(derive_signal_geometries(base_series()[:5], params(), base_costs()), [])

    def test_fingerprint_is_deterministic(self):
        first = first_signal()
        second = first_signal()
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertEqual(len(first.fingerprint), 64)

    def test_malformed_ohlc_fails_closed(self):
        series = base_series()
        series[1] = candle(1, 98.0, 97.0, 97.5, 98.5)
        with self.assertRaises(ValueError):
            validate_candles(series)

    def test_duplicate_or_irregular_interval_fails_closed(self):
        series = base_series()
        series[3] = candle(3, 99.5, 99.8, 99.0, 99.4, open_time=series[2].open_time)
        with self.assertRaises(ValueError):
            validate_candles(series)

        series = base_series()
        series[3] = candle(3, 99.5, 99.8, 99.0, 99.4, open_time=series[2].open_time + 2 * STEP)
        with self.assertRaises(ValueError):
            validate_candles(series)

    def test_v01_rejects_non_15m_timeframe(self):
        with self.assertRaises(ValueError):
            params(timeframe="5m").validate()

    def test_same_bar_stop_and_tp2_is_scored_as_stop(self):
        signal = first_signal()
        series = base_series()
        series[6] = candle(6, signal.entry, signal.tp2 + 0.5, signal.stop - 0.1, signal.entry)
        outcome = simulate_outcome(signal, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "STOP_AMBIGUOUS_SAME_BAR")
        self.assertTrue(outcome.same_bar_stop_target_ambiguity)
        self.assertAlmostEqual(outcome.net_r, -1.0)

    def test_adverse_gap_through_stop_can_lose_more_than_one_r(self):
        signal = first_signal()
        series = base_series()
        series[7] = candle(7, signal.stop - 0.5, signal.stop - 0.2, signal.stop - 0.8, signal.stop - 0.4)
        outcome = simulate_outcome(signal, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "STOP_GAP")
        self.assertLess(outcome.net_r, -1.0)

    def test_tp2_outcome_net_r_matches_geometry_net_rr(self):
        signal = first_signal()
        outcome = simulate_outcome(signal, base_series(), base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "TP2")
        self.assertTrue(outcome.tp1_reached)
        self.assertAlmostEqual(outcome.net_r, signal.net_rr_tp2)
        self.assertFalse(outcome.submitted_to_exchange)

    def test_time_exit_uses_next_bar_open(self):
        signal = first_signal()
        series = base_series()
        series[6] = candle(6, signal.entry, signal.entry + 0.1, signal.entry - 0.1, signal.entry)
        series[7] = candle(7, signal.entry + 0.05, signal.entry + 0.2, signal.entry - 0.1, signal.entry + 0.1)
        outcome = simulate_outcome(signal, series, base_costs(), max_holding_bars=1)
        self.assertEqual(outcome.exit_reason, "TIME_EXIT_NEXT_OPEN")
        self.assertEqual(outcome.exit_open_time, 7 * STEP)
        self.assertAlmostEqual(outcome.exit_price, series[7].open)

    def test_end_of_data_time_exit_is_explicitly_unresolved(self):
        signal = first_signal()
        series = base_series()
        series[6] = candle(6, signal.entry, signal.entry + 0.1, signal.entry - 0.1, signal.entry)
        series[7] = candle(7, signal.entry, signal.entry + 0.1, signal.entry - 0.1, signal.entry)
        outcome = simulate_outcome(signal, series, base_costs(), max_holding_bars=2)
        self.assertEqual(outcome.exit_reason, "UNRESOLVED_END_OF_DATA")
        self.assertIsNone(outcome.net_r)
        self.assertIsNone(outcome.exit_price)

    def test_research_module_has_no_network_or_exchange_mutation_client(self):
        text = (ROOT / "research" / "phase_b_signal_formation_v01.py").read_text(encoding="utf-8")
        lowered = text.lower()
        for forbidden in ("import requests", "import urllib", "import websockets", ".post(", ".put(", ".patch(", ".delete("):
            self.assertNotIn(forbidden, lowered)
        self.assertNotIn("mexc_client", lowered)
        self.assertNotIn("execution_layer", lowered)

    def test_all_numeric_geometry_outputs_are_finite(self):
        signal = first_signal()
        for value in (
            signal.resistance,
            signal.atr_before_breakout,
            signal.zone_low,
            signal.zone_high,
            signal.entry,
            signal.stop,
            signal.tp1,
            signal.tp2,
            signal.stop_distance_pct,
            signal.net_rr_tp2,
        ):
            self.assertTrue(math.isfinite(value))


if __name__ == "__main__":
    unittest.main()

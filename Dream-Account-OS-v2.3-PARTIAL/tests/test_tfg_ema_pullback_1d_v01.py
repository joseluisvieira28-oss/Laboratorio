from __future__ import annotations

import unittest

from research.tfg_ema_pullback_1d_discovery_runner_v01 import (
    BASE_COST_PCT,
    DAY_MS,
    FIFTEEN_MIN_MS,
    Candle,
    BootstrapInterval,
    EvaluationMetrics,
    Signal,
    StressMetrics,
    aggregate_15m_to_1d,
    classify,
    ema_series,
    parse_ms,
    simulate,
)


class FrozenEmaPullback1DTests(unittest.TestCase):
    def test_ema_constant_series(self) -> None:
        values = ema_series([7.0] * 60, 20)
        self.assertEqual(values[19], 7.0)
        self.assertEqual(values[-1], 7.0)

    def test_daily_aggregation_drops_incomplete_bucket(self) -> None:
        start = parse_ms("2024-01-01T00:00:00.000Z")
        rows = []
        for i in range(192):
            t = start + i * FIFTEEN_MIN_MS
            rows.append(Candle(t, 100.0, 101.0, 99.0, 100.5, 1.0, t + FIFTEEN_MIN_MS - 1))
        complete, incomplete = aggregate_15m_to_1d(rows)
        self.assertEqual(len(complete), 2)
        self.assertEqual(incomplete, 0)
        dropped, incomplete = aggregate_15m_to_1d(rows[1:])
        self.assertEqual(len(dropped), 1)
        self.assertEqual(incomplete, 1)

    def test_same_bar_stop_target_is_stop_first(self) -> None:
        start = parse_ms("2024-01-01T00:00:00.000Z")
        segment = [
            Candle(start, 100.0, 125.0, 85.0, 100.0, 1.0, start + DAY_MS - 1),
            Candle(start + DAY_MS, 100.0, 101.0, 99.0, 100.0, 1.0, start + 2 * DAY_MS - 1),
        ]
        signal = Signal(
            symbol="BTCUSDT",
            signal_open_time=start - DAY_MS,
            entry_open_time=start,
            ema20=95.0,
            ema50=90.0,
            atr14=10.0,
            signal_low=92.5,
            signal_close=96.0,
            entry=100.0,
            stop=90.0,
            target=120.0,
            initial_risk_fraction=0.10,
            fingerprint="synthetic",
        )
        outcome = simulate(signal, segment, BASE_COST_PCT)
        self.assertEqual(outcome.exit_reason, "STOP_AMBIGUOUS_SAME_BAR")
        self.assertTrue(outcome.same_bar_stop_target_ambiguity)

    def test_minimum_sample_gate_cannot_be_bypassed_by_positive_metrics(self) -> None:
        base = EvaluationMetrics(
            cost_scenario="BASE_0.20PCT_RT",
            raw_trigger_count=99,
            pre_entry_cancelled_count=0,
            selected_trade_count=99,
            overlap_skipped_count=0,
            unresolved_trade_count=0,
            resolved_trade_count=99,
            net_expectancy_r=0.5,
            median_net_r=0.2,
            win_rate=0.6,
            loss_rate=0.4,
            profit_factor_r=2.0,
            target_reach_rate=0.5,
            same_bar_ambiguity_rate=0.0,
            time_exit_rate=0.0,
            stop_gap_rate=0.0,
            signal_frequency_per_30d=5.0,
            symbol_distribution={"BTCUSDT": 99},
            contiguous_segment_count=1,
            detected_gap_count=0,
        )
        stress = StressMetrics("STRESS_0.30PCT_RT", "BASE_SELECTED_TFG_EMA_PULLBACK_1D_TRADES", 99, 99, 0, 0.4, 0.1, 1.8)
        bootstrap = BootstrapInterval("UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP", 5000, 230911, 0.95, 99, 0.1, 0.5, 0.9, None)
        decision = classify(base, stress, bootstrap)
        self.assertEqual(decision.classification, "INSUFFICIENT_SAMPLE")
        self.assertFalse(decision.validation_unlock_eligible)


if __name__ == "__main__":
    unittest.main()

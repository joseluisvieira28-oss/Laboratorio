from __future__ import annotations

import json
from pathlib import Path
import unittest

from dream_account.models import Candle
from research.phase_b_research_evaluator_v01 import BootstrapInterval, EvaluationMetrics, FixedCohortCostMetrics
from research.tfg_pbr01_4h_v01 import FOUR_H_MS, FIFTEEN_MIN_MS, ResearchParameters4H, aggregate_15m_to_4h, classify_discovery_4h, split_4h_segments, validate_4h_candles


ROOT = Path(__file__).resolve().parents[1]
FREEZE = ROOT / "research" / "TFG_PBR01_4H_PROSPECTIVE_FREEZE_V0.1.json"


def c15(i: int, *, base: float = 100.0) -> Candle:
    t = i * FIFTEEN_MIN_MS
    return Candle(t, base + i * 0.01, base + 1 + i * 0.01, base - 1 + i * 0.01, base + 0.5 + i * 0.01, 10.0 + i, t + FIFTEEN_MIN_MS - 1, True)


def c4(i: int, *, base: float = 100.0) -> Candle:
    t = i * FOUR_H_MS
    return Candle(t, base, base + 1, base - 1, base + 0.25, 100.0, t + FOUR_H_MS - 1, True)


class TFGPBR014HTests(unittest.TestCase):
    def test_freeze_identity_and_only_timeframe_transport(self) -> None:
        payload = json.loads(FREEZE.read_text(encoding="utf-8"))
        self.assertEqual(payload["status"], "FROZEN_BEFORE_ANY_4H_OUTCOME_EVALUATION")
        self.assertEqual(payload["lab_id"], "TFG-PBR01-4H-001")
        self.assertEqual(payload["scientific_position"]["only_intended_strategy_change"], "TIMEFRAME_15M_TO_4H")
        self.assertTrue(payload["scientific_position"]["parent_verdict_immutable"])
        self.assertFalse(payload["final_holdout"]["access_allowed_now"])

    def test_parameters_are_exact_parent_bar_geometry(self) -> None:
        p = ResearchParameters4H()
        self.assertEqual((p.lookback_bars, p.atr_length, p.zone_atr_fraction, p.retest_window_bars), (96, 14, 0.25, 2))
        self.assertEqual((p.stop_atr_fraction, p.tp1_r_multiple, p.tp2_r_multiple, p.min_net_rr, p.max_holding_bars), (0.25, 1.0, 3.0, 2.0, 96))
        p.validate()

    def test_parameters_reject_non_4h(self) -> None:
        with self.assertRaises(ValueError):
            ResearchParameters4H(timeframe="1h").validate()

    def test_complete_16x15m_bucket_aggregates_exactly(self) -> None:
        source = [c15(i) for i in range(16)]
        out = aggregate_15m_to_4h(source)
        self.assertEqual(len(out), 1)
        bar = out[0]
        self.assertEqual(bar.open_time, 0)
        self.assertEqual(bar.close_time, FOUR_H_MS - 1)
        self.assertEqual(bar.open, source[0].open)
        self.assertEqual(bar.close, source[-1].close)
        self.assertEqual(bar.high, max(x.high for x in source))
        self.assertEqual(bar.low, min(x.low for x in source))
        self.assertAlmostEqual(bar.volume, sum(x.volume for x in source))

    def test_missing_15m_candle_drops_entire_4h_bucket(self) -> None:
        source = [c15(i) for i in range(32) if i != 5]
        out = aggregate_15m_to_4h(source)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].open_time, FOUR_H_MS)

    def test_duplicate_15m_timestamp_fails_closed(self) -> None:
        source = [c15(i) for i in range(16)] + [c15(5)]
        with self.assertRaises(ValueError):
            aggregate_15m_to_4h(source)

    def test_4h_alignment_is_utc_strict(self) -> None:
        bad = Candle(FOUR_H_MS + FIFTEEN_MIN_MS, 100, 101, 99, 100, 1, FOUR_H_MS + FIFTEEN_MIN_MS + FOUR_H_MS - 1, True)
        with self.assertRaises(ValueError):
            validate_4h_candles([bad])

    def test_gap_splits_segments_no_bridge(self) -> None:
        bars = [c4(0), c4(1), c4(3), c4(4)]
        segments, gaps = split_4h_segments(bars)
        self.assertEqual(gaps, 1)
        self.assertEqual([len(x) for x in segments], [2, 2])

    def test_classifier_returns_insufficient_sample_below_100(self) -> None:
        base = EvaluationMetrics(cost_scenario="BASE_SENSITIVITY", raw_geometry_count=20, net_rr_rejected_count=0, selected_trade_count=20, overlap_skipped_count=0, unresolved_trade_count=0, resolved_trade_count=20, net_expectancy_r=1.0, median_net_r=1.0, win_rate=1.0, loss_rate=0.0, profit_factor_r=2.0, tp1_reach_rate=1.0, same_bar_ambiguity_rate=0.0, time_exit_rate=0.0, stop_gap_rate=0.0, signal_frequency_per_30d=1.0, symbol_distribution={"BTCUSDT": 20}, contiguous_segment_count=1, detected_gap_count=0)
        stress = FixedCohortCostMetrics(cost_scenario="STRESS", cohort_source="BASE_SENSITIVITY_SELECTED_TFG_PBR01_4H_TRADES", selected_trade_count=20, resolved_trade_count=20, unresolved_trade_count=0, net_expectancy_r=0.5, median_net_r=0.5, profit_factor_r=1.5, net_rr_below_minimum_count=0, net_rr_violation_rate=0.0)
        boot = BootstrapInterval(method="UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP", repetitions=5000, seed=230911, confidence=0.95, sample_days=20, lower=0.1, point_estimate=1.0, upper=2.0, undefined_reason=None)
        decision = classify_discovery_4h(base, stress, boot)
        self.assertEqual(decision.classification, "INSUFFICIENT_SAMPLE")
        self.assertFalse(decision.validation_unlock_eligible)

    def test_classifier_requires_all_positive_gates_at_n100(self) -> None:
        base = EvaluationMetrics(cost_scenario="BASE_SENSITIVITY", raw_geometry_count=100, net_rr_rejected_count=0, selected_trade_count=100, overlap_skipped_count=0, unresolved_trade_count=0, resolved_trade_count=100, net_expectancy_r=0.1, median_net_r=0.1, win_rate=0.55, loss_rate=0.45, profit_factor_r=1.1, tp1_reach_rate=0.6, same_bar_ambiguity_rate=0.0, time_exit_rate=0.1, stop_gap_rate=0.0, signal_frequency_per_30d=2.0, symbol_distribution={"BTCUSDT": 100}, contiguous_segment_count=1, detected_gap_count=0)
        stress = FixedCohortCostMetrics(cost_scenario="STRESS", cohort_source="BASE_SENSITIVITY_SELECTED_TFG_PBR01_4H_TRADES", selected_trade_count=100, resolved_trade_count=100, unresolved_trade_count=0, net_expectancy_r=0.01, median_net_r=0.01, profit_factor_r=1.01, net_rr_below_minimum_count=0, net_rr_violation_rate=0.0)
        boot = BootstrapInterval(method="UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP", repetitions=5000, seed=230911, confidence=0.95, sample_days=50, lower=-0.001, point_estimate=0.1, upper=0.2, undefined_reason=None)
        decision = classify_discovery_4h(base, stress, boot)
        self.assertEqual(decision.classification, "NO_EDGE")
        self.assertIn("bootstrap_lower_95_not_positive", decision.failed_conditions)
        self.assertFalse(decision.validation_unlock_eligible)


if __name__ == "__main__":
    unittest.main()

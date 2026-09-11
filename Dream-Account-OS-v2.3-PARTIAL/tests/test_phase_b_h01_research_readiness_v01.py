import json
from pathlib import Path
import unittest

from dream_account.models import Candle
from research.phase_b_h01_research_evaluator_v01 import (
    BASE_COHORT_SOURCE,
    EXCHANGE_MUTATION_AUTHORIZED,
    HYPOTHESIS_ID,
    LIVE_AUTHORIZED,
    day_block_bootstrap_expectancy,
    evaluate_h01_symbol,
    evaluate_h01_universe,
    reprice_h01_fixed_cohort,
)
from research.phase_b_h01_stage_classifier_v01 import (
    HOLDOUT_2026_AUTHORIZED,
    H01ResearchStage,
    H01StageClassification,
    classify_h01_stage,
)
from research.phase_b_research_evaluator_v01 import (
    BootstrapInterval,
    EvaluationMetrics,
    FixedCohortCostMetrics,
)
from research.phase_b_signal_formation_v01 import (
    CostAssumptions,
    ResearchParameters,
    derive_signal_geometries,
    simulate_outcome,
)


STEP = 15 * 60 * 1000
ROOT = Path(__file__).resolve().parents[1]
FREEZE_PATH = ROOT / "research" / "PHASE_B_H01_PROTECT_AFTER_TP1_PROSPECTIVE_FREEZE_V0.1.json"
EVALUATOR_PATH = ROOT / "research" / "phase_b_h01_research_evaluator_v01.py"
CLASSIFIER_PATH = ROOT / "research" / "phase_b_h01_stage_classifier_v01.py"
P00_CLASSIFIER_PATH = ROOT / "research" / "phase_b_stage_classifier_v01.py"
EXPECTED_FREEZE_FINGERPRINT = "5229b820df2fc40036fe064e2b25361f3905b63345732f960eb7d9e457033d0b"


def candle(index, open_, high, low, close):
    timestamp = index * STEP
    return Candle(
        open_time=timestamp,
        open=open_,
        high=high,
        low=low,
        close=close,
        volume=1_000.0,
        close_time=timestamp + STEP - 1,
        closed=True,
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


def parameters():
    return ResearchParameters(
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


def base_costs():
    return CostAssumptions("BASE_SENSITIVITY", 0.05, 0.05, 0.025)


def stress_costs():
    return CostAssumptions("STRESS", 0.05, 0.10, 0.05)


def managed_fixture():
    original = base_series()
    signals = derive_signal_geometries(original, parameters(), base_costs())
    if not signals:
        raise AssertionError("synthetic fixture did not create a P00-formation signal")
    signal = signals[0]
    series = base_series()
    series[6] = candle(
        6,
        signal.entry,
        signal.tp1 + 0.05,
        signal.entry - 0.05,
        signal.entry + 0.10,
    )
    series[7] = candle(
        7,
        signal.entry + 0.10,
        signal.entry + 0.20,
        signal.entry - 0.01,
        signal.entry + 0.05,
    )
    return signal, series


def metrics(
    *,
    resolved=100,
    expectancy=0.20,
    profit_factor=1.20,
):
    return EvaluationMetrics(
        cost_scenario="BASE_SENSITIVITY",
        raw_geometry_count=resolved,
        net_rr_rejected_count=0,
        selected_trade_count=resolved,
        overlap_skipped_count=0,
        unresolved_trade_count=0,
        resolved_trade_count=resolved,
        net_expectancy_r=expectancy,
        median_net_r=expectancy,
        win_rate=0.55,
        loss_rate=0.45,
        profit_factor_r=profit_factor,
        tp1_reach_rate=0.60,
        same_bar_ambiguity_rate=0.0,
        time_exit_rate=0.0,
        stop_gap_rate=0.0,
        signal_frequency_per_30d=5.0,
        symbol_distribution={"BTCUSDT": resolved},
        contiguous_segment_count=1,
        detected_gap_count=0,
    )


def stress_metrics(*, resolved=100, expectancy=0.10, cohort_source=BASE_COHORT_SOURCE):
    return FixedCohortCostMetrics(
        cost_scenario="STRESS",
        cohort_source=cohort_source,
        selected_trade_count=resolved,
        resolved_trade_count=resolved,
        unresolved_trade_count=0,
        net_expectancy_r=expectancy,
        median_net_r=expectancy,
        profit_factor_r=1.10,
        net_rr_below_minimum_count=0,
        net_rr_violation_rate=0.0,
    )


def bootstrap(*, lower=0.05, point=0.20, upper=0.35):
    return BootstrapInterval(
        method="UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP",
        repetitions=5000,
        seed=230911,
        confidence=0.95,
        sample_days=50,
        lower=lower,
        point_estimate=point,
        upper=upper,
        undefined_reason=None,
    )


class PhaseBH01EvaluatorReadinessTests(unittest.TestCase):
    def test_h01_evaluator_uses_next_bar_protection_not_p00_outcome(self):
        signal, series = managed_fixture()
        records, diagnostics = evaluate_h01_symbol(
            "BTCUSDT",
            series,
            parameters(),
            base_costs(),
        )
        record = next(
            item for item in records if item.signal.entry_open_time == signal.entry_open_time
        )
        self.assertEqual(record.outcome.exit_reason, "PROTECTIVE_STOP")
        self.assertAlmostEqual(record.outcome.exit_price, signal.entry)
        self.assertTrue(record.outcome.tp1_reached)
        self.assertLess(record.outcome.net_r, 0.0)
        self.assertGreaterEqual(diagnostics["raw_geometry_count"], 1)

        p00_outcome = simulate_outcome(
            signal,
            series,
            base_costs(),
            max_holding_bars=2,
        )
        self.assertEqual(p00_outcome.exit_reason, "UNRESOLVED_END_OF_DATA")

    def test_universe_metrics_and_fixed_cohort_are_h01_specific(self):
        _, series = managed_fixture()
        records, result = evaluate_h01_universe(
            {"BTCUSDT": series},
            parameters(),
            base_costs(),
        )
        self.assertGreaterEqual(result.selected_trade_count, 1)
        self.assertGreaterEqual(result.resolved_trade_count, 1)
        self.assertEqual(result.cost_scenario, "BASE_SENSITIVITY")

        stress = reprice_h01_fixed_cohort(
            records,
            stress_costs(),
            min_net_rr=parameters().min_net_rr,
        )
        self.assertEqual(stress.cohort_source, BASE_COHORT_SOURCE)
        self.assertEqual(stress.selected_trade_count, result.selected_trade_count)
        self.assertEqual(stress.resolved_trade_count, result.resolved_trade_count)

    def test_h01_bootstrap_reuses_only_frozen_day_block_semantics(self):
        _, series = managed_fixture()
        records, _ = evaluate_h01_universe(
            {"BTCUSDT": series},
            parameters(),
            base_costs(),
        )
        interval = day_block_bootstrap_expectancy(
            records,
            repetitions=5000,
            seed=230911,
            confidence=0.95,
        )
        self.assertEqual(interval.method, "UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP")
        self.assertEqual(interval.repetitions, 5000)
        self.assertEqual(interval.seed, 230911)
        self.assertEqual(interval.confidence, 0.95)

    def test_h01_evaluator_is_offline_and_does_not_load_market_files(self):
        text = EVALUATOR_PATH.read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests",
            "import urllib",
            "import websockets",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
            "mexc_client",
            "execution_layer",
            "path(",
            "open(",
            "read_text(",
            "read_bytes(",
        ):
            self.assertNotIn(forbidden, text)
        self.assertFalse(LIVE_AUTHORIZED)
        self.assertFalse(EXCHANGE_MUTATION_AUTHORIZED)


class PhaseBH01ClassifierReadinessTests(unittest.TestCase):
    def test_freeze_binding_and_data_authority_remain_locked(self):
        freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))
        self.assertEqual(freeze["hypothesis_id"], HYPOTHESIS_ID)
        self.assertEqual(freeze["fingerprint"], EXPECTED_FREEZE_FINGERPRINT)
        self.assertFalse(freeze["authority_boundary"]["this_file_authorizes_2025_data_access"])
        self.assertTrue(freeze["origin"]["confirmatory_reuse_of_2023_2024_forbidden"])

    def test_discovery_survives_only_when_every_frozen_condition_passes(self):
        decision = classify_h01_stage(
            H01ResearchStage.DISCOVERY,
            metrics(),
            stress_metrics(),
            bootstrap(),
        )
        self.assertEqual(decision.classification, H01StageClassification.SURVIVES.value)
        self.assertEqual(decision.hypothesis_id, HYPOTHESIS_ID)
        self.assertEqual(decision.minimum_required_trades, 100)
        self.assertTrue(decision.validation_unlock_eligible)
        self.assertFalse(decision.holdout_2026_unlock_eligible)
        self.assertFalse(decision.live_authorized)
        self.assertFalse(decision.exchange_mutation_authorized)
        self.assertFalse(decision.submitted_to_exchange)

    def test_discovery_below_100_is_insufficient_sample(self):
        decision = classify_h01_stage(
            H01ResearchStage.DISCOVERY,
            metrics(resolved=99),
            stress_metrics(resolved=99),
            bootstrap(),
        )
        self.assertEqual(
            decision.classification,
            H01StageClassification.INSUFFICIENT_SAMPLE.value,
        )
        self.assertFalse(decision.validation_unlock_eligible)

    def test_any_failed_survival_condition_is_no_edge(self):
        cases = (
            (metrics(expectancy=0.0), stress_metrics(), bootstrap()),
            (metrics(profit_factor=1.0), stress_metrics(), bootstrap()),
            (metrics(), stress_metrics(), bootstrap(lower=0.0)),
            (metrics(), stress_metrics(expectancy=0.0), bootstrap()),
        )
        for base, stress, interval in cases:
            with self.subTest(base=base, stress=stress, interval=interval):
                decision = classify_h01_stage(
                    H01ResearchStage.DISCOVERY,
                    base,
                    stress,
                    interval,
                )
                self.assertEqual(decision.classification, H01StageClassification.NO_EDGE.value)
                self.assertFalse(decision.validation_unlock_eligible)

    def test_p00_fixed_cohort_cannot_be_substituted_for_h01(self):
        with self.assertRaisesRegex(ValueError, "H01 cohort"):
            classify_h01_stage(
                H01ResearchStage.DISCOVERY,
                metrics(),
                stress_metrics(cohort_source="BASE_SENSITIVITY_SELECTED_P00_TRADES"),
                bootstrap(),
            )

    def test_validation_classification_requires_discovery_survives(self):
        with self.assertRaises(PermissionError):
            classify_h01_stage(
                H01ResearchStage.VALIDATION,
                metrics(resolved=30),
                stress_metrics(resolved=30),
                bootstrap(),
            )

        decision = classify_h01_stage(
            H01ResearchStage.VALIDATION,
            metrics(resolved=30),
            stress_metrics(resolved=30),
            bootstrap(),
            discovery_classification=H01StageClassification.SURVIVES,
        )
        self.assertEqual(decision.minimum_required_trades, 30)
        self.assertEqual(decision.classification, H01StageClassification.SURVIVES.value)
        self.assertFalse(decision.validation_unlock_eligible)
        self.assertFalse(decision.holdout_2026_unlock_eligible)

    def test_classifier_has_no_holdout_stage_or_live_route(self):
        self.assertEqual(
            {stage.value for stage in H01ResearchStage},
            {"DISCOVERY", "VALIDATION"},
        )
        self.assertFalse(HOLDOUT_2026_AUTHORIZED)
        text = CLASSIFIER_PATH.read_text(encoding="utf-8").lower()
        for forbidden in (
            "import requests",
            "import urllib",
            "import websockets",
            ".post(",
            ".put(",
            ".patch(",
            ".delete(",
            "mexc_client",
            "execution_layer",
        ):
            self.assertNotIn(forbidden, text)

    def test_p00_classifier_remains_p00_only(self):
        p00 = P00_CLASSIFIER_PATH.read_text(encoding="utf-8")
        self.assertIn('PRIMARY_PROFILE_ID = "P00_PRIMARY"', p00)
        self.assertIn('"BASE_SENSITIVITY_SELECTED_P00_TRADES"', p00)
        self.assertNotIn(HYPOTHESIS_ID, p00)


if __name__ == "__main__":
    unittest.main()

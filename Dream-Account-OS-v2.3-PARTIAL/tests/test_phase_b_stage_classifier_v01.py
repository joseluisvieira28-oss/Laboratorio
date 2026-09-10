from dataclasses import replace
import json
from pathlib import Path
import unittest

from research.phase_b_research_evaluator_v01 import (
    BootstrapInterval,
    EvaluationMetrics,
    FixedCohortCostMetrics,
)
from research.phase_b_stage_classifier_v01 import (
    DISCOVERY_MIN_RESOLVED_TRADES,
    VALIDATION_MIN_RESOLVED_TRADES,
    ResearchStage,
    StageClassification,
    assert_stage_access,
    classify_stage,
)


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research" / "PHASE_B_PRE_DATA_RESEARCH_FREEZE_V0.1.json"


def base_metrics(*, n=100, expectancy=0.20, pf=1.40):
    return EvaluationMetrics(
        cost_scenario="BASE_SENSITIVITY",
        raw_geometry_count=n,
        net_rr_rejected_count=0,
        selected_trade_count=n,
        overlap_skipped_count=0,
        unresolved_trade_count=0,
        resolved_trade_count=n,
        net_expectancy_r=expectancy,
        median_net_r=0.10,
        win_rate=0.50,
        loss_rate=0.50,
        profit_factor_r=pf,
        tp1_reach_rate=0.60,
        same_bar_ambiguity_rate=0.01,
        time_exit_rate=0.10,
        stop_gap_rate=0.01,
        signal_frequency_per_30d=10.0,
        symbol_distribution={"BTCUSDT": n},
        contiguous_segment_count=1,
        detected_gap_count=0,
    )


def stress_metrics(*, n=100, expectancy=0.05):
    return FixedCohortCostMetrics(
        cost_scenario="STRESS",
        cohort_source="BASE_SENSITIVITY_SELECTED_P00_TRADES",
        selected_trade_count=n,
        resolved_trade_count=n,
        unresolved_trade_count=0,
        net_expectancy_r=expectancy,
        median_net_r=0.02,
        profit_factor_r=1.10,
        net_rr_below_minimum_count=5,
        net_rr_violation_rate=0.05,
    )


def bootstrap(*, lower=0.01, point=0.20, upper=0.40):
    return BootstrapInterval(
        method="UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP",
        repetitions=5000,
        seed=230911,
        confidence=0.95,
        sample_days=80,
        lower=lower,
        point_estimate=point,
        upper=upper,
        undefined_reason=None,
    )


class PhaseBStageClassifierTests(unittest.TestCase):
    def test_discovery_is_accessible_before_results(self):
        assert_stage_access(ResearchStage.DISCOVERY)

    def test_validation_is_locked_without_discovery_survival(self):
        for status in (None, StageClassification.INSUFFICIENT_SAMPLE, StageClassification.NO_EDGE):
            with self.assertRaises(PermissionError):
                assert_stage_access(ResearchStage.VALIDATION, discovery_classification=status)

    def test_validation_unlocks_only_after_discovery_survives(self):
        assert_stage_access(
            ResearchStage.VALIDATION,
            discovery_classification=StageClassification.SURVIVES,
        )

    def test_discovery_below_100_is_insufficient_sample(self):
        decision = classify_stage(
            ResearchStage.DISCOVERY,
            base_metrics(n=99),
            stress_metrics(n=99),
            bootstrap(),
        )
        self.assertEqual(decision.classification, "INSUFFICIENT_SAMPLE")
        self.assertFalse(decision.next_stage_unlocked)
        self.assertFalse(decision.live_authorized)
        self.assertFalse(decision.submitted_to_exchange)

    def test_validation_below_30_is_insufficient_sample(self):
        decision = classify_stage(
            ResearchStage.VALIDATION,
            base_metrics(n=29),
            stress_metrics(n=29),
            bootstrap(),
        )
        self.assertEqual(decision.classification, "INSUFFICIENT_SAMPLE")
        self.assertFalse(decision.next_stage_unlocked)

    def test_all_frozen_conditions_required_for_survival(self):
        decision = classify_stage(
            ResearchStage.DISCOVERY,
            base_metrics(),
            stress_metrics(),
            bootstrap(),
        )
        self.assertEqual(decision.classification, "SURVIVES")
        self.assertTrue(decision.next_stage_unlocked)
        self.assertEqual(decision.failed_conditions, ())

    def test_zero_or_negative_base_expectancy_is_no_edge(self):
        for expectancy in (0.0, -0.01):
            decision = classify_stage(
                ResearchStage.DISCOVERY,
                base_metrics(expectancy=expectancy),
                stress_metrics(),
                bootstrap(),
            )
            self.assertEqual(decision.classification, "NO_EDGE")
            self.assertIn("base_net_expectancy_not_positive", decision.failed_conditions)

    def test_profit_factor_must_be_strictly_above_one(self):
        decision = classify_stage(
            ResearchStage.DISCOVERY,
            base_metrics(pf=1.0),
            stress_metrics(),
            bootstrap(),
        )
        self.assertEqual(decision.classification, "NO_EDGE")
        self.assertIn("base_profit_factor_not_above_1", decision.failed_conditions)

    def test_bootstrap_lower_bound_must_be_strictly_positive(self):
        decision = classify_stage(
            ResearchStage.DISCOVERY,
            base_metrics(),
            stress_metrics(),
            bootstrap(lower=0.0),
        )
        self.assertEqual(decision.classification, "NO_EDGE")
        self.assertIn("base_bootstrap_lower_95_not_positive", decision.failed_conditions)

    def test_fixed_cohort_stress_expectancy_must_be_positive(self):
        decision = classify_stage(
            ResearchStage.DISCOVERY,
            base_metrics(),
            stress_metrics(expectancy=0.0),
            bootstrap(),
        )
        self.assertEqual(decision.classification, "NO_EDGE")
        self.assertIn("fixed_cohort_stress_expectancy_not_positive", decision.failed_conditions)

    def test_missing_required_evidence_fails_closed_once_sample_threshold_met(self):
        with self.assertRaises(ValueError):
            classify_stage(
                ResearchStage.DISCOVERY,
                replace(base_metrics(), net_expectancy_r=None),
                stress_metrics(),
                bootstrap(),
            )
        with self.assertRaises(ValueError):
            classify_stage(
                ResearchStage.DISCOVERY,
                base_metrics(),
                stress_metrics(),
                replace(bootstrap(), lower=None),
            )

    def test_wrong_cost_scenario_or_cohort_fails_closed(self):
        with self.assertRaises(ValueError):
            classify_stage(
                ResearchStage.DISCOVERY,
                replace(base_metrics(), cost_scenario="FEE_FLOOR"),
                stress_metrics(),
                bootstrap(),
            )
        with self.assertRaises(ValueError):
            classify_stage(
                ResearchStage.DISCOVERY,
                base_metrics(),
                replace(stress_metrics(), cohort_source="RESELECTED"),
                bootstrap(),
            )

    def test_cohort_count_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            classify_stage(
                ResearchStage.DISCOVERY,
                base_metrics(n=100),
                replace(stress_metrics(n=100), selected_trade_count=99),
                bootstrap(),
            )

    def test_only_primary_profile_can_be_classified(self):
        with self.assertRaises(ValueError):
            classify_stage(
                ResearchStage.DISCOVERY,
                base_metrics(),
                stress_metrics(),
                bootstrap(),
                profile_id="P09_TP2_25R",
            )

    def test_bootstrap_protocol_mismatch_fails_closed(self):
        with self.assertRaises(ValueError):
            classify_stage(
                ResearchStage.DISCOVERY,
                base_metrics(),
                stress_metrics(),
                replace(bootstrap(), repetitions=4999),
            )
        with self.assertRaises(ValueError):
            classify_stage(
                ResearchStage.DISCOVERY,
                base_metrics(),
                stress_metrics(),
                replace(bootstrap(), seed=1),
            )

    def test_decision_fingerprint_is_deterministic_and_evidence_sensitive(self):
        first = classify_stage(ResearchStage.DISCOVERY, base_metrics(), stress_metrics(), bootstrap())
        second = classify_stage(ResearchStage.DISCOVERY, base_metrics(), stress_metrics(), bootstrap())
        changed = classify_stage(
            ResearchStage.DISCOVERY,
            base_metrics(expectancy=0.21),
            stress_metrics(),
            bootstrap(point=0.21),
        )
        self.assertEqual(first.fingerprint, second.fingerprint)
        self.assertNotEqual(first.fingerprint, changed.fingerprint)
        self.assertEqual(len(first.fingerprint), 64)

    def test_classifier_thresholds_match_machine_readable_manifest(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        policy = data["decision_policy"]
        self.assertEqual(DISCOVERY_MIN_RESOLVED_TRADES, policy["discovery_min_resolved_trades"])
        self.assertEqual(VALIDATION_MIN_RESOLVED_TRADES, policy["validation_min_resolved_trades"])
        self.assertEqual(data["data_contract"]["validation"]["status"], "LOCKED_UNTIL_DISCOVERY_SURVIVES")

    def test_classifier_source_contains_no_holdout_unlock_or_network_client(self):
        text = (ROOT / "research" / "phase_b_stage_classifier_v01.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("2026-", text)
        self.assertNotIn("requests", text)
        self.assertNotIn("urllib", text)
        self.assertNotIn("websockets", text)
        self.assertNotIn("mexc_client", text)
        self.assertNotIn("submitted_to_exchange = true", text)


if __name__ == "__main__":
    unittest.main()

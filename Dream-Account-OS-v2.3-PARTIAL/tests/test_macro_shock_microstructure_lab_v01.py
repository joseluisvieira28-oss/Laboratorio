import sys
from datetime import datetime, timezone
from pathlib import Path
import unittest

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH_DIR))

import macro_shock_microstructure_lab_v01 as msm


class MacroShockV01CoreTests(unittest.TestCase):
    def test_normalized_flow_and_sign(self):
        self.assertAlmostEqual(msm.normalized_taker_flow(60, 40), 0.2)
        self.assertAlmostEqual(msm.normalized_taker_flow(40, 60), -0.2)
        self.assertEqual(msm.normalized_taker_flow(0, 0), 0.0)
        self.assertEqual(msm.sign(0.2), 1)
        self.assertEqual(msm.sign(-0.2), -1)
        self.assertEqual(msm.sign(0.0), 0)

    def test_persistence_requires_nonzero_same_sign(self):
        self.assertEqual(msm.persistent_flow_sign(0.2, 0.1), 1)
        self.assertEqual(msm.persistent_flow_sign(-0.2, -0.1), -1)
        self.assertEqual(msm.persistent_flow_sign(0.2, -0.1), 0)
        self.assertEqual(msm.persistent_flow_sign(0.0, 0.1), 0)

    def test_outcome_and_zero_return_rule(self):
        self.assertEqual(msm.continuation_success(100, 101, 1), 1)
        self.assertEqual(msm.continuation_success(100, 99, -1), 1)
        self.assertEqual(msm.continuation_success(100, 100, 1), 0)
        self.assertEqual(msm.continuation_success(100, 99, 1), 0)

    def test_control_candidates_use_frozen_lags(self):
        event = datetime(2025, 8, 12, 12, 30, tzinfo=timezone.utc)
        controls = msm.candidate_control_timestamps(event)
        self.assertEqual(len(controls), 8)
        self.assertEqual((event - controls[0]).days, 7)
        self.assertEqual((event - controls[-1]).days, 56)
        self.assertTrue(all(c.weekday() == event.weekday() for c in controls))
        self.assertTrue(all((c.hour, c.minute) == (event.hour, event.minute) for c in controls))

    def test_control_overlap_exclusion(self):
        event = datetime(2025, 8, 12, 12, 30, tzinfo=timezone.utc)
        blocked = event.replace(day=5)  # exactly 7 days before
        valid = msm.filter_valid_controls(event, [blocked])
        self.assertEqual(len(valid), 7)
        self.assertNotIn(blocked, valid)
        self.assertTrue(msm.control_adequacy_pass(len(valid)))
        self.assertFalse(msm.control_adequacy_pass(3))

    def test_primary_statistic(self):
        # Event 75%, controls 50% => +25 percentage points.
        diff = msm.continuation_rate_difference([1, 1, 1, 0], [1, 0, 1, 0])
        self.assertAlmostEqual(diff, 0.25)

    def test_cluster_bootstrap_is_deterministic_and_uses_5000(self):
        records = [
            msm.ClusterRecord("2025-01-01", (1, 1), (0, 1, 0, 1)),
            msm.ClusterRecord("2025-02-01", (1, 0), (0, 0, 1, 0)),
            msm.ClusterRecord("2025-03-01", (1, 1), (1, 0, 0, 0)),
        ]
        a = msm.cluster_bootstrap_difference(records)
        b = msm.cluster_bootstrap_difference(records)
        self.assertEqual(a, b)
        self.assertGreater(a[0], 0)
        with self.assertRaises(msm.ContractViolation):
            msm.cluster_bootstrap_difference(records, repetitions=1000)

    def test_classification_contract(self):
        self.assertEqual(
            msm.classify(
                data_integrity_pass=False,
                resolved_event_symbol_cases=100,
                distinct_macro_event_dates=50,
                point_estimate=0.2,
                ci_lower_bound=0.1,
            ).classification,
            "TECHNICAL_OR_DATA_FAILURE",
        )
        self.assertEqual(
            msm.classify(
                data_integrity_pass=True,
                resolved_event_symbol_cases=29,
                distinct_macro_event_dates=20,
                point_estimate=0.2,
                ci_lower_bound=0.1,
            ).classification,
            "INSUFFICIENT_SAMPLE",
        )
        self.assertEqual(
            msm.classify(
                data_integrity_pass=True,
                resolved_event_symbol_cases=30,
                distinct_macro_event_dates=20,
                point_estimate=0.2,
                ci_lower_bound=0.01,
            ).classification,
            "SURVIVES",
        )
        self.assertEqual(
            msm.classify(
                data_integrity_pass=True,
                resolved_event_symbol_cases=30,
                distinct_macro_event_dates=20,
                point_estimate=0.2,
                ci_lower_bound=0.0,
            ).classification,
            "NO_EDGE",
        )
        self.assertEqual(
            msm.classify(
                data_integrity_pass=True,
                resolved_event_symbol_cases=30,
                distinct_macro_event_dates=20,
                point_estimate=-0.1,
                ci_lower_bound=-0.2,
            ).classification,
            "NO_EDGE",
        )

    def test_fail_closed_preholdout_receipt(self):
        receipt = msm.preholdout_governance_receipt()
        self.assertFalse(receipt["holdout_2026_accessed"])
        self.assertFalse(receipt["mexc_2025_09_through_2025_12_accessed"])
        self.assertFalse(receipt["live_trading_authorized"])
        self.assertFalse(receipt["exchange_mutation_authorized"])
        self.assertFalse(receipt["network_access_in_this_module"])

    def test_frozen_constants(self):
        self.assertEqual(msm.ALLOWED_SYMBOLS, ("BTCUSDT", "ETHUSDT"))
        self.assertEqual(msm.ALLOWED_EVENT_FAMILIES, ("US_CPI", "US_NFP", "US_FOMC"))
        self.assertEqual(msm.CONTROL_LAGS_DAYS, (7, 14, 21, 28, 35, 42, 49, 56))
        self.assertEqual(msm.MIN_VALID_CONTROLS_PER_EVENT_SYMBOL, 4)
        self.assertEqual(msm.MIN_RESOLVED_EVENT_SYMBOL_CASES, 30)
        self.assertEqual(msm.MIN_DISTINCT_EVENT_DATES, 20)
        self.assertEqual(msm.BOOTSTRAP_REPETITIONS, 5000)


if __name__ == "__main__":
    unittest.main()

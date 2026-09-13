from pathlib import Path
import sys
import tempfile
import unittest

RESEARCH_DIR = Path(__file__).resolve().parents[1] / "research"
sys.path.insert(0, str(RESEARCH_DIR))

import microstructure_collector_offline_preparation_v01 as prep
import microstructure_collector_readiness_drill_v01 as drill


class MicrostructureCollectorReadinessDrillV01Tests(unittest.TestCase):
    def _run(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return drill.run_full_readiness_drill(Path(td.name) / "drill")

    def test_full_drill_passes_and_repeat_is_deterministic(self):
        receipt = self._run()
        self.assertEqual(receipt["status"], drill.PASS_LABEL)
        self.assertTrue(receipt["deterministic_repeat_equal"])
        self.assertTrue(receipt["operational_checks_pass"])
        self.assertTrue(receipt["mirrored_checks_equal"])
        self.assertEqual(receipt["run_a_fingerprint"], receipt["run_b_fingerprint"])
        self.assertEqual(len(receipt["readiness_closeout_fingerprint"]), 64)

    def test_complete_frozen_scope_is_covered(self):
        receipt = self._run()
        run = receipt["run_a"]
        completeness = run["complete_scope"]["completeness_receipt"]
        self.assertEqual(receipt["required_observation_key_count"], 14)
        self.assertEqual(completeness["required_key_count"], 14)
        self.assertEqual(completeness["observed_key_count"], 14)
        self.assertEqual(completeness["missing_keys"], [])
        self.assertTrue(completeness["complete"])
        self.assertEqual(len(run["complete_scope"]["manifest_fingerprints"]), 14)
        self.assertEqual(len(run["complete_scope"]["segment_receipt_fingerprints"]), 14)

    def test_gap_and_resync_fail_closed_for_both_venues(self):
        receipt = self._run()
        continuity = receipt["run_a"]["continuity"]
        self.assertEqual(continuity["binance"]["gap_status"], "GAP_FAIL_CLOSED")
        self.assertTrue(continuity["binance"]["blocked_after_gap"])
        self.assertTrue(continuity["binance"]["resynchronized_after_explicit_resync"])
        self.assertEqual(
            continuity["coinbase"]["connection_gap_status"],
            "GAP_OR_REORDER_FAIL_CLOSED",
        )
        self.assertTrue(continuity["coinbase"]["blocked_after_gap"])
        self.assertEqual(
            continuity["coinbase"]["book_regression_status"],
            "REGRESSION_FAIL_CLOSED",
        )
        self.assertTrue(continuity["coinbase"]["resynchronized_after_explicit_resync"])

    def test_clock_fault_injection_is_detected_without_threshold_tuning(self):
        receipt = self._run()
        clocks = receipt["run_a"]["clock_diagnostics"]
        self.assertTrue(clocks["clean_clock"]["valid_for_receive_time_ordering"])
        self.assertGreater(clocks["fault_injection_clock"]["wall_regressions"], 0)
        self.assertGreater(clocks["fault_injection_clock"]["monotonic_nonincreasing"], 0)
        self.assertFalse(clocks["fault_injection_clock"]["valid_for_receive_time_ordering"])
        self.assertTrue(clocks["fault_detected"])

    def test_abrupt_interruption_cannot_be_mistaken_for_closed_or_overwritten(self):
        receipt = self._run()
        crash = receipt["run_a"]["crash_restart"]
        self.assertTrue(crash["open_segment_rejected_as_closed"])
        self.assertTrue(crash["same_segment_index_overwrite_blocked"])
        self.assertTrue(crash["interrupted_bytes_preserved"])
        self.assertEqual(crash["restart_used_new_segment_index"], 1)
        self.assertEqual(len(crash["restart_closed_segment_fingerprint"]), 64)
        self.assertEqual(crash["reconnect_count"], 1)
        self.assertEqual(crash["resync_count"], 1)

    def test_closed_segment_tamper_is_detected(self):
        receipt = self._run()
        tamper = receipt["run_a"]["tamper_detection"]
        self.assertTrue(tamper["deliberate_synthetic_tamper_detected"])
        self.assertTrue(tamper["tampered_fixture_excluded_from_valid_segments"])
        self.assertEqual(len(tamper["pre_tamper_receipt_fingerprint"]), 64)

    def test_frozen_event_windows_are_half_open_and_exact(self):
        receipt = self._run()
        windows = receipt["run_a"]["event_windows"]
        self.assertEqual(
            windows["half_open_counts"],
            {"prebaseline": 2, "primary_state": 2, "recovery_descriptive": 2},
        )
        self.assertTrue(windows["exactly_plus_60m_excluded"])
        self.assertEqual(len(windows["event_window_extraction_fingerprint"]), 64)

    def test_drill_never_authorizes_target_observation_or_market_classification(self):
        receipt = self._run()
        run = receipt["run_a"]
        self.assertFalse(receipt["target_observation_started"])
        self.assertFalse(receipt["target_outcomes_evaluated"])
        self.assertFalse(receipt["directional_signals_generated"])
        self.assertEqual(receipt["h02_status"], "NOT_AUTHORIZED")
        self.assertFalse(receipt["complete_official_2027_calendar_frozen"])
        self.assertFalse(receipt["separate_explicit_target_observation_authorization"])
        self.assertFalse(receipt["live_trading_authorized"])
        self.assertFalse(receipt["exchange_mutation_authorized"])
        self.assertFalse(receipt["mexc_2025_09_through_2025_12_accessed"])
        self.assertFalse(receipt["holdout_2026_reused"])
        self.assertIsNone(receipt["scientific_classification"])
        self.assertEqual(
            run["synthetic_observation_receipt"]["status"],
            "SYNTHETIC_DRILL_ONLY_NOT_A_TARGET_OBSERVATION",
        )
        self.assertFalse(run["preflight"]["target_observation_may_start"])
        self.assertEqual(run["preflight"]["status"], "OFFLINE_READY_TARGET_OBSERVATION_BLOCKED")

    def test_storage_planning_is_descriptive_only_and_positive(self):
        receipt = self._run()
        storage = receipt["run_a"]["storage_planning_descriptive_only"]
        self.assertGreater(storage["observed_bytes"], 0)
        self.assertGreater(storage["bytes_per_second"], 0)
        self.assertGreater(storage["baseline_bytes"], 0)
        self.assertGreater(storage["planning_2x_bytes"], storage["baseline_bytes"])

    def test_governance_constants_remain_fail_closed(self):
        self.assertEqual(prep.H02_STATUS, "NOT_AUTHORIZED")
        self.assertFalse(prep.TARGET_OBSERVATION_AUTHORIZED)
        self.assertEqual(drill.DRILL_SCOPE, "SYNTHETIC_OFFLINE_NON_DIRECTIONAL_COLLECTOR_READINESS_ONLY")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

import json
import unittest
from dataclasses import asdict
from pathlib import Path

from research.phase_b_p00_discovery_runner_v01 import FREEZE_PATH, _parameters_from_freeze
from research.phase_b_p00_sensitivity_matrix_v01 import (
    EXPECTED_PROFILE_IDS,
    _parameters_for_profile,
    _validate_sensitivity_freeze,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "phase_b_p00_sensitivity_matrix_v01.py"
LAUNCHER = ROOT / "research" / "run_phase_b_p00_sensitivity_matrix_windows.bat"


class PhaseBP00SensitivityMatrixTests(unittest.TestCase):
    def setUp(self) -> None:
        self.freeze = json.loads(FREEZE_PATH.read_text(encoding="utf-8"))

    def test_frozen_profile_set_is_exact_and_one_factor_at_a_time(self) -> None:
        profiles = _validate_sensitivity_freeze(self.freeze)
        self.assertEqual(tuple(item["profile_id"] for item in profiles), EXPECTED_PROFILE_IDS)
        self.assertEqual(len(profiles), 12)
        for profile in profiles:
            self.assertEqual(len(profile["change_only"]), 1)

    def test_each_profile_changes_exactly_one_base_parameter(self) -> None:
        base = _parameters_from_freeze(self.freeze)
        base_dict = asdict(base)
        for profile in _validate_sensitivity_freeze(self.freeze):
            changed = _parameters_for_profile(base, profile)
            changed_dict = asdict(changed)
            differing = [key for key in base_dict if base_dict[key] != changed_dict[key]]
            self.assertEqual(differing, list(profile["change_only"].keys()))
            key = differing[0]
            self.assertEqual(changed_dict[key], profile["change_only"][key])

    def test_sensitivity_policy_forbids_rescue_winner_and_posthoc_tuning(self) -> None:
        policy = self.freeze["sensitivity_policy"]
        self.assertEqual(policy["method"], "ONE_FACTOR_AT_A_TIME")
        self.assertIs(policy["may_replace_primary_after_results"], False)
        self.assertIs(policy["may_be_selected_as_winner"], False)
        self.assertIs(policy["parameter_tuning_after_outcome_inspection"], False)

    def test_runner_contains_no_classifier_or_live_network_mutation_route(self) -> None:
        text = SOURCE.read_text(encoding="utf-8").lower()
        for forbidden in (
            "classify_stage",
            "requests",
            "urllib",
            "websockets",
            "socket",
            "/api/v3/order",
            "submit_order",
            "place_order",
            "cancel_order",
        ):
            self.assertNotIn(forbidden, text)
        self.assertIn("classification=None", SOURCE.read_text(encoding="utf-8"))
        self.assertIn("promotion_eligible=False", SOURCE.read_text(encoding="utf-8"))
        self.assertIn("may_rescue_p00=False", SOURCE.read_text(encoding="utf-8"))

    def test_windows_launcher_is_diagnostic_only_and_secret_free(self) -> None:
        text = LAUNCHER.read_text(encoding="utf-8").lower()
        self.assertIn("diagnostic-only", text)
        self.assertIn("p00 remains closed no_edge", text)
        self.assertIn("no winner is selected", text)
        for forbidden in (
            "api_key",
            "secret_key",
            "mexc_api",
            "curl ",
            "powershell invoke-webrequest",
            "/api/v3/order",
        ):
            self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()

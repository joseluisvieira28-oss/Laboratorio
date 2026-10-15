from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from dream_account.execution_phase_a_campaign_summary import (
    build_operational_summary,
    render_text,
)


class _FakeCampaign:
    def sanitized_dict(self):
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "successful_cycles": 4,
            "remaining_successful_cycles": 96,
            "calendar_days_observed": 1,
            "remaining_calendar_days": 6,
            "attempted_cycles": 4,
            "blocked_cycles": 0,
            "first_observed_at_utc": "2026-09-10T19:20:36+00:00",
            "last_observed_at_utc": "2026-09-10T19:53:35+00:00",
            "fingerprint": "abc123",
            "blocking_reasons": [],
            "aggregate_metrics": {
                "SafetyIntegrityRate": {"value": 1.0},
                "ReconciliationCleanRate": {"value": 1.0},
                "ObservationFailureRate": {"value": 0.0},
            },
        }


class GateKPhaseACampaignSummaryTests(unittest.TestCase):
    def test_compact_summary_is_read_only_projection(self):
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / "phase_a.sqlite3"
            journal.write_bytes(b"placeholder")
            with mock.patch(
                "dream_account.execution_phase_a_campaign_summary.summarize_journal",
                return_value=_FakeCampaign(),
            ) as summarize:
                result = build_operational_summary(str(journal))

            summarize.assert_called_once_with(str(journal.resolve()))
            self.assertEqual(result["runner_mode"], "LOCAL_READ_ONLY_SUMMARY")
            self.assertEqual(result["successful_cycles"], 4)
            self.assertEqual(result["required_successful_cycles"], 100)
            self.assertEqual(result["calendar_days_observed"], 1)
            self.assertEqual(result["required_calendar_days"], 7)
            self.assertEqual(result["safety_integrity_rate"], 1.0)
            self.assertEqual(result["reconciliation_clean_rate"], 1.0)
            self.assertEqual(result["observation_failure_rate"], 0.0)

    def test_missing_journal_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.sqlite3"
            with self.assertRaises(FileNotFoundError):
                build_operational_summary(str(missing))

    def test_text_render_is_compact_and_contains_core_gate_state(self):
        text = render_text(_FakeCampaign().sanitized_dict() | {
            "campaign_status": "INSUFFICIENT_EVIDENCE",
            "required_successful_cycles": 100,
            "required_calendar_days": 7,
            "safety_integrity_rate": 1.0,
            "reconciliation_clean_rate": 1.0,
            "observation_failure_rate": 0.0,
            "campaign_fingerprint": "abc123",
        })
        self.assertIn("Successful cycles: 4/100", text)
        self.assertIn("Calendar days: 1/7", text)
        self.assertIn("Safety integrity rate: 1.000", text)
        self.assertIn("Reconciliation clean rate: 1.000", text)
        self.assertIn("Blocking reasons: NONE", text)

    def test_windows_launcher_is_summary_only_and_contains_no_credentials(self):
        launcher = Path(__file__).resolve().parents[1] / "show_gate_k_phase_a_summary_windows.bat"
        text = launcher.read_text(encoding="utf-8")
        lowered = text.lower()
        self.assertIn("execution_phase_a_campaign_summary", text)
        self.assertNotIn("execution_phase_a_campaign_runner", text)
        self.assertNotIn("execution_phase_a_campaign_batch", text)
        self.assertNotIn("mexc_readonly_access_key", lowered)
        self.assertNotIn("mexc_readonly_secret_key", lowered)
        self.assertNotIn(" post ", lowered)
        self.assertNotIn(" put ", lowered)
        self.assertNotIn(" patch ", lowered)
        self.assertNotIn(" delete ", lowered)


if __name__ == "__main__":
    unittest.main()

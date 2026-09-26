from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dream_account.execution_phase_a_campaign_runner import (
    run_one_local_campaign_cycle,
    validate_persistent_journal_path,
)
from dream_account.execution_shadow_rehearsal import (
    OBSERVATION_JOURNAL_ENV,
    SHADOW_REHEARSAL_ENABLE_ENV,
    ShadowProposalBlocked,
)


class _FakeReport:
    def sanitized_dict(self):
        return {"status": "PASS_NO_ACTIONABLE_LIVE_SIGNAL", "fingerprint": "report-fp"}


class _FakeCampaign:
    def sanitized_dict(self):
        return {
            "status": "INSUFFICIENT_EVIDENCE",
            "successful_cycles": 1,
            "calendar_days_observed": 1,
            "fingerprint": "campaign-fp",
        }


class GateKPhaseACampaignRunnerTests(unittest.TestCase):
    def test_memory_sqlite_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_persistent_journal_path(":memory:")

    def test_blank_journal_path_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_persistent_journal_path("   ")

    def test_directory_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):
                validate_persistent_journal_path(directory)

    def test_parent_directory_is_created_for_persistent_file(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "nested" / "phase-a.sqlite3"
            resolved = validate_persistent_journal_path(str(target))
            self.assertTrue(resolved.parent.exists())
            self.assertEqual(resolved, target.resolve())

    def test_explicit_shadow_enable_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            target = str(Path(directory) / "phase-a.sqlite3")
            with patch.dict(os.environ, {}, clear=True):
                with self.assertRaises(ShadowProposalBlocked):
                    run_one_local_campaign_cycle(target)

    def test_runner_sets_requested_journal_and_restores_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            target = str((Path(directory) / "phase-a.sqlite3").resolve())
            seen = {}

            def fake_rehearsal():
                seen["journal"] = os.environ.get(OBSERVATION_JOURNAL_ENV)
                return _FakeReport()

            with patch.dict(
                os.environ,
                {
                    SHADOW_REHEARSAL_ENABLE_ENV: "1",
                    OBSERVATION_JOURNAL_ENV: "previous.sqlite3",
                },
                clear=True,
            ):
                with patch(
                    "dream_account.execution_phase_a_campaign_runner.run_shadow_rehearsal",
                    side_effect=fake_rehearsal,
                ), patch(
                    "dream_account.execution_phase_a_campaign_runner.summarize_journal",
                    return_value=_FakeCampaign(),
                ) as summarize:
                    result = run_one_local_campaign_cycle(target)

                self.assertEqual(seen["journal"], target)
                self.assertEqual(os.environ.get(OBSERVATION_JOURNAL_ENV), "previous.sqlite3")
                summarize.assert_called_once_with(target)
                self.assertEqual(result["runner_mode"], "LOCAL_ONE_SHOT")
                self.assertEqual(result["campaign"]["status"], "INSUFFICIENT_EVIDENCE")

    def test_runner_removes_temporary_journal_env_when_none_existed(self):
        with tempfile.TemporaryDirectory() as directory:
            target = str((Path(directory) / "phase-a.sqlite3").resolve())
            with patch.dict(os.environ, {SHADOW_REHEARSAL_ENABLE_ENV: "1"}, clear=True):
                with patch(
                    "dream_account.execution_phase_a_campaign_runner.run_shadow_rehearsal",
                    return_value=_FakeReport(),
                ), patch(
                    "dream_account.execution_phase_a_campaign_runner.summarize_journal",
                    return_value=_FakeCampaign(),
                ):
                    run_one_local_campaign_cycle(target)
                self.assertNotIn(OBSERVATION_JOURNAL_ENV, os.environ)


if __name__ == "__main__":
    unittest.main()

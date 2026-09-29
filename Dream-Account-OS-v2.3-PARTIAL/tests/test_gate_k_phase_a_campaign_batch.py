from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from dream_account.execution_phase_a_campaign_batch import (
    MAX_CYCLES_PER_BATCH,
    MAX_INTERVAL_SECONDS,
    MIN_INTERVAL_SECONDS,
    run_campaign_batch,
    validate_campaign_plan,
)


class GateKPhaseACampaignBatchTests(unittest.TestCase):
    def test_rejects_too_many_cycles(self):
        with self.assertRaises(ValueError):
            validate_campaign_plan(MAX_CYCLES_PER_BATCH + 1, MIN_INTERVAL_SECONDS)

    def test_rejects_absurdly_fast_interval(self):
        with self.assertRaises(ValueError):
            validate_campaign_plan(2, MIN_INTERVAL_SECONDS - 1)

    def test_rejects_excessive_interval(self):
        with self.assertRaises(ValueError):
            validate_campaign_plan(2, MAX_INTERVAL_SECONDS + 1)

    def test_valid_plan_is_preserved(self):
        self.assertEqual(validate_campaign_plan(15, 1800), (15, 1800))

    def test_batch_reuses_one_shot_runner_and_same_journal(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = str(Path(directory) / "phase-a.sqlite3")
            calls = []
            sleeps = []

            def fake_cycle(path: str):
                calls.append(path)
                number = len(calls)
                return {
                    "runner_mode": "LOCAL_ONE_SHOT",
                    "journal_path": path,
                    "shadow_rehearsal": {"status": "PASS_NO_ACTIONABLE_LIVE_SIGNAL"},
                    "campaign": {
                        "status": "INSUFFICIENT_EVIDENCE",
                        "successful_cycles": number,
                        "blocked_cycles": 0,
                        "calendar_days_observed": 1,
                        "remaining_successful_cycles": 100 - number,
                        "remaining_calendar_days": 6,
                    },
                }

            with patch(
                "dream_account.execution_phase_a_campaign_batch.run_one_local_campaign_cycle",
                side_effect=fake_cycle,
            ):
                result = run_campaign_batch(
                    journal,
                    cycles=3,
                    interval_seconds=MIN_INTERVAL_SECONDS,
                    sleep_fn=lambda seconds: sleeps.append(seconds),
                )

            resolved = str(Path(journal).resolve())
            self.assertEqual(calls, [resolved, resolved, resolved])
            self.assertEqual(sleeps, [MIN_INTERVAL_SECONDS, MIN_INTERVAL_SECONDS])
            self.assertEqual(result["completed_cycles_this_batch"], 3)
            self.assertFalse(result["stopped_early"])
            self.assertEqual(result["last_campaign_summary"]["successful_cycles"], 3)

    def test_blocked_campaign_stops_without_sleeping_or_retrying(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = str(Path(directory) / "phase-a.sqlite3")
            calls = []
            sleeps = []

            def fake_cycle(path: str):
                calls.append(path)
                return {
                    "runner_mode": "LOCAL_ONE_SHOT",
                    "journal_path": path,
                    "shadow_rehearsal": {"status": "PASS_NO_ACTIONABLE_LIVE_SIGNAL"},
                    "campaign": {"status": "BLOCKED"},
                }

            with patch(
                "dream_account.execution_phase_a_campaign_batch.run_one_local_campaign_cycle",
                side_effect=fake_cycle,
            ):
                result = run_campaign_batch(
                    journal,
                    cycles=5,
                    interval_seconds=MIN_INTERVAL_SECONDS,
                    sleep_fn=lambda seconds: sleeps.append(seconds),
                )

            self.assertEqual(len(calls), 1)
            self.assertEqual(sleeps, [])
            self.assertTrue(result["stopped_early"])
            self.assertEqual(result["last_campaign_summary"]["status"], "BLOCKED")

    def test_latest_cycle_receipt_is_overwritten_with_last_completed_cycle(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = str(Path(directory) / "phase-a.sqlite3")
            receipt = Path(directory) / "latest.json"
            counter = {"value": 0}

            def fake_cycle(path: str):
                counter["value"] += 1
                return {
                    "runner_mode": "LOCAL_ONE_SHOT",
                    "journal_path": path,
                    "shadow_rehearsal": {"status": "PASS_NO_ACTIONABLE_LIVE_SIGNAL"},
                    "campaign": {
                        "status": "INSUFFICIENT_EVIDENCE",
                        "successful_cycles": counter["value"],
                    },
                }

            with patch(
                "dream_account.execution_phase_a_campaign_batch.run_one_local_campaign_cycle",
                side_effect=fake_cycle,
            ):
                run_campaign_batch(
                    journal,
                    cycles=2,
                    interval_seconds=MIN_INTERVAL_SECONDS,
                    latest_cycle_output=str(receipt),
                    sleep_fn=lambda _: None,
                )

            text = receipt.read_text(encoding="utf-8")
            self.assertIn('"successful_cycles": 2', text)
            self.assertNotIn('"successful_cycles": 1,', text)


if __name__ == "__main__":
    unittest.main()

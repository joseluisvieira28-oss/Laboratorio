from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from tempfile import TemporaryDirectory
from pathlib import Path

from dream_account.execution_journal import ExecutionJournal
from dream_account.execution_phase_a_campaign import record_and_summarize_cycle, summarize_campaign
from dream_account.execution_shadow_rehearsal import build_phase_a_observation


def _obs(index: int, day_offset: int = 0, **overrides):
    base = dict(
        run_id=f"run-{index}",
        observed_at=datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc) + timedelta(days=day_offset, minutes=index),
        collector_gate_status="PASS",
        expected_symbols=10,
        verified_symbols=10,
        data_quality_rejection_counts={},
        candidates=[],
        deep_pass_count=0,
        reconciliation_status="PASS_CLEAN",
        reconciliation_symbols_queried=10,
        reconciliation_daos_open_orders=0,
        reconciliation_daos_recent_trades=0,
        exchange_mutation_routes=0,
        submitted_to_exchange=False,
        live_trade_proposals_created=0,
    )
    base.update(overrides)
    return build_phase_a_observation(**base)


class GateKPhaseACampaignTests(unittest.TestCase):
    def test_campaign_is_insufficient_before_100_cycles_and_7_days(self):
        summary = summarize_campaign([_obs(1)])
        self.assertEqual(summary.status, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(summary.successful_cycles, 1)
        self.assertEqual(summary.calendar_days_observed, 1)
        self.assertEqual(summary.remaining_successful_cycles, 99)
        self.assertEqual(summary.remaining_calendar_days, 6)

    def test_campaign_pass_requires_both_cycle_and_calendar_day_thresholds(self):
        records = [_obs(i, day_offset=i % 7) for i in range(100)]
        summary = summarize_campaign(records)
        self.assertEqual(summary.status, "PASS")
        self.assertEqual(summary.successful_cycles, 100)
        self.assertEqual(summary.calendar_days_observed, 7)
        self.assertEqual(summary.remaining_successful_cycles, 0)
        self.assertEqual(summary.remaining_calendar_days, 0)

    def test_campaign_does_not_pass_100_cycles_on_one_day(self):
        summary = summarize_campaign([_obs(i) for i in range(100)])
        self.assertEqual(summary.status, "INSUFFICIENT_EVIDENCE")
        self.assertEqual(summary.successful_cycles, 100)
        self.assertEqual(summary.calendar_days_observed, 1)

    def test_mutation_route_blocks_campaign(self):
        summary = summarize_campaign([_obs(1, exchange_mutation_routes=1)])
        self.assertEqual(summary.status, "BLOCKED")
        self.assertIn("exchange_mutation_route_present", summary.blocking_reasons)

    def test_exchange_submission_claim_blocks_campaign(self):
        summary = summarize_campaign([_obs(1, submitted_to_exchange=True)])
        self.assertEqual(summary.status, "BLOCKED")
        self.assertIn("exchange_submission_claim_present", summary.blocking_reasons)

    def test_live_trade_proposal_blocks_campaign(self):
        summary = summarize_campaign([_obs(1, live_trade_proposals_created=1)])
        self.assertEqual(summary.status, "BLOCKED")
        self.assertIn("live_trade_proposal_present", summary.blocking_reasons)

    def test_unexplained_daos_activity_blocks_campaign(self):
        summary = summarize_campaign([_obs(1, reconciliation_daos_open_orders=1)])
        self.assertEqual(summary.status, "BLOCKED")
        self.assertIn("unexpected_daos_open_order_activity", summary.blocking_reasons)

    def test_campaign_fingerprint_is_deterministic(self):
        records = [_obs(1), _obs(2, day_offset=1)]
        a = summarize_campaign(records)
        b = summarize_campaign(reversed(records))
        self.assertEqual(a.fingerprint, b.fingerprint)

    def test_changed_evidence_changes_campaign_fingerprint(self):
        a = summarize_campaign([_obs(1)])
        b = summarize_campaign([_obs(1, verified_symbols=9)])
        self.assertNotEqual(a.fingerprint, b.fingerprint)

    def test_record_and_summarize_is_idempotent(self):
        with TemporaryDirectory() as directory:
            journal = ExecutionJournal(str(Path(directory) / "phase-a.sqlite3"))
            try:
                observation = _obs(1)
                first = record_and_summarize_cycle(journal, observation)
                second = record_and_summarize_cycle(journal, observation)
                self.assertEqual(first.fingerprint, second.fingerprint)
                self.assertEqual(len(journal.phase_a_observations()), 1)
                self.assertEqual(journal.integrity_check(), ["ok"])
            finally:
                journal.close()

    def test_empty_campaign_is_explicitly_insufficient_and_metrics_undefined(self):
        summary = summarize_campaign([])
        self.assertEqual(summary.status, "INSUFFICIENT_EVIDENCE")
        self.assertIsNone(summary.aggregate_metrics["DataCoverageRate"]["value"])
        self.assertIsNone(summary.aggregate_metrics["SafetyIntegrityRate"]["value"])


if __name__ == "__main__":
    unittest.main()

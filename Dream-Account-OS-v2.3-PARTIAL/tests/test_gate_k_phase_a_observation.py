import tempfile
import unittest
from datetime import datetime, timezone

from dream_account.execution_journal import ExecutionJournal, ObservationConflict
from dream_account.execution_shadow_rehearsal import (
    ShadowProposalBlocked,
    aggregate_phase_a_observations,
    build_phase_a_observation,
    build_shadow_proposal,
)
from dream_account.models import Candidate


NOW = datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc)


def candidate(*, tier="REJECT", status="NO_TRADE", reasons=()):
    row = Candidate("BTCUSDT", "SPOT", 100.0, 1_000_000.0, 0.05, {}, 1.0, "UNVERIFIED")
    row.tier = tier
    row.status = status
    row.rejection_reasons = list(reasons)
    return row


def observation(**overrides):
    values = dict(
        run_id="run-1", observed_at=NOW, collector_gate_status="PASS", expected_symbols=2,
        verified_symbols=2, data_quality_rejection_counts={}, candidates=[candidate(reasons=("filter_b", "filter_a"))],
        deep_pass_count=0, reconciliation_status="PASS_CLEAN", reconciliation_symbols_queried=10,
        reconciliation_daos_open_orders=0, reconciliation_daos_recent_trades=0,
    )
    values.update(overrides)
    return build_phase_a_observation(**values)


class GateKPhaseAObservationTests(unittest.TestCase):
    def test_successful_record_schema_and_explicit_unavailable_summaries(self):
        row = observation(candidates=[])
        payload = row.sanitized_dict()
        required = {"observation_id", "run_id", "observed_at_utc", "collector_gate_status",
                    "expected_symbols", "verified_symbols", "data_coverage_pct", "candidate_count",
                    "deep_pass_count", "actionable_readiness_count", "candidate_tier_distribution",
                    "candidate_status_distribution", "candidate_rejection_reason_counts",
                    "readiness_block_reason_counts", "spread_summary", "volume_summary",
                    "reconciliation_status", "reconciliation_symbols_queried",
                    "reconciliation_daos_open_orders", "reconciliation_daos_recent_trades",
                    "exchange_mutation_routes", "submitted_to_exchange", "live_trade_proposals_created", "fingerprint"}
        self.assertTrue(required <= payload.keys())
        self.assertIsNone(payload["spread_summary"]["mean"])
        self.assertEqual(payload["spread_summary"]["unavailable_reason"], "no_observed_candidates")

    def test_fingerprint_is_deterministic_and_evidence_sensitive(self):
        self.assertEqual(observation().fingerprint(), observation().fingerprint())
        self.assertNotEqual(observation().fingerprint(), observation(verified_symbols=1).fingerprint())

    def test_zero_denominators_are_explicit(self):
        metrics = aggregate_phase_a_observations([])
        for name in ("DataCoverageRate", "CandidateYield", "DeepPassRate", "ReadinessRate",
                     "ReconciliationCleanRate", "SafetyIntegrityRate", "ObservationFailureRate"):
            self.assertIsNone(metrics[name]["value"])
            self.assertTrue(metrics[name]["undefined_reason"])

    def test_block_reason_aggregation_is_sorted_and_deterministic(self):
        metrics = aggregate_phase_a_observations([observation(), observation(run_id="run-2")])
        keys = list(metrics["BlockReasonDistribution"])
        self.assertEqual(keys, sorted(keys))
        self.assertEqual(metrics["BlockReasonDistribution"]["filter_a"], 2)

    def test_safety_integrity_requires_all_three_invariants(self):
        rows = [observation(), observation(run_id="r2", exchange_mutation_routes=1),
                observation(run_id="r3", submitted_to_exchange=True)]
        self.assertEqual(aggregate_phase_a_observations(rows)["SafetyIntegrityRate"]["value"], 1 / 3)

    def test_mutation_submission_and_daos_activity_block(self):
        self.assertEqual(observation(exchange_mutation_routes=1).status, "BLOCKED")
        self.assertEqual(observation(submitted_to_exchange=True).status, "BLOCKED")
        self.assertEqual(observation(reconciliation_status="DIVERGENCE_BLOCKED",
                                     reconciliation_daos_open_orders=1).status, "BLOCKED")

    def test_incomplete_candidate_cannot_become_trade_proposal(self):
        with self.assertRaises(ShadowProposalBlocked):
            build_shadow_proposal(candidate(), quantity=1, max_slippage_bps=1, risk_allocation_id="x")

    def test_missing_required_inputs_fail_closed(self):
        with self.assertRaises(ShadowProposalBlocked):
            observation(run_id="")
        row = observation(expected_symbols=None, verified_symbols=None, candidates=None, deep_pass_count=None)
        self.assertIsNone(row.data_coverage_pct)
        self.assertIsNone(row.candidate_count)

    def test_observation_journal_is_durable_idempotent_and_immutable(self):
        row = observation()
        with tempfile.TemporaryDirectory() as directory:
            journal = ExecutionJournal(f"{directory}/journal.sqlite3")
            try:
                journal.record_phase_a_observation(row.observation_id, row.fingerprint(), row.evidence_dict())
                journal.record_phase_a_observation(row.observation_id, row.fingerprint(), row.evidence_dict())
                self.assertEqual(len(journal.phase_a_observations()), 1)
                with self.assertRaises(ObservationConflict):
                    journal.record_phase_a_observation(row.observation_id, "different", row.evidence_dict())
                self.assertEqual(journal.integrity_check(), ["ok"])
            finally:
                journal.close()


if __name__ == "__main__":
    unittest.main()

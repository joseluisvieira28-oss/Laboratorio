import tempfile
import unittest
from datetime import datetime, timezone

from dream_account.config import Settings
from dream_account.execution_coordinator import ShadowExecutionCoordinator
from dream_account.execution_journal import ExecutionJournal
from dream_account.execution_layer import MockMEXCExecutionAdapter, SafetyContext
from dream_account.engines import calculate_costs, total_risk_position_size
from dream_account.execution_shadow_rehearsal import (
    ShadowProposalBlocked,
    _execution_fixture_candidate,
    build_shadow_proposal,
    candidate_readiness,
)
from dream_account.models import Candidate


class GateKShadowRehearsalTests(unittest.TestCase):
    def test_current_live_style_candidate_is_not_proposal_ready(self):
        candidate = Candidate(
            "BTCUSDT", "SPOT", 100.0, 10_000_000.0, 0.05, {}, 0.0, "UNVERIFIED"
        )
        readiness = candidate_readiness(candidate)
        self.assertFalse(readiness.ready)
        self.assertIn("status_not_long_candidate", readiness.reasons)
        self.assertIn("missing_setup", readiness.reasons)
        self.assertIn("missing_entry", readiness.reasons)
        self.assertIn("missing_stop", readiness.reasons)

    def test_rejected_candidate_cannot_be_promoted_by_bridge(self):
        candidate = _execution_fixture_candidate(Settings())
        candidate.rejection_reasons.append("manual_block")
        with self.assertRaises(ShadowProposalBlocked):
            build_shadow_proposal(
                candidate,
                quantity=0.5,
                max_slippage_bps=25.0,
                risk_allocation_id="TEST",
            )

    def test_spot_short_is_blocked_in_gate_k_bridge(self):
        candidate = _execution_fixture_candidate(Settings())
        candidate.status = "SHORT_CANDIDATE"
        readiness = candidate_readiness(candidate)
        self.assertFalse(readiness.ready)
        self.assertIn("status_not_long_candidate", readiness.reasons)

    def test_missing_explicit_quantity_is_blocked(self):
        candidate = _execution_fixture_candidate(Settings())
        with self.assertRaises(ShadowProposalBlocked):
            build_shadow_proposal(
                candidate,
                quantity=0.0,
                max_slippage_bps=25.0,
                risk_allocation_id="TEST",
            )

    def test_fixture_candidate_is_ready_without_mutating_strategy(self):
        candidate = _execution_fixture_candidate(Settings())
        readiness = candidate_readiness(candidate)
        self.assertTrue(readiness.ready, readiness.reasons)
        self.assertEqual(candidate.status, "LONG_CANDIDATE")
        self.assertIn(candidate.tier, {"A", "A+"})
        self.assertEqual(candidate.rejection_reasons, [])

    def test_full_shadow_handoff_is_idempotent_and_never_submits(self):
        candidate = _execution_fixture_candidate(Settings())
        now = datetime.now(timezone.utc)
        costs = calculate_costs(candidate.entry, candidate.stop, candidate.tp1, 0.1, 0.05, 0.02)
        sizing = total_risk_position_size(56, 1.0, candidate.entry, candidate.stop, costs.estimated_cost_pct, 56)
        proposal = build_shadow_proposal(
            candidate,
            quantity=sizing["position_notional_chf"] / candidate.entry,
            max_slippage_bps=25.0,
            risk_allocation_id="FIXTURE-RISK-V2-NORMAL-TOTAL-RISK",
            created_at=now,
        )
        safety = SafetyContext(
            market_data_timestamp_utc=proposal.created_at_utc,
            api_tradable=True,
            precision_valid=True,
            minimum_valid=True,
            observed_slippage_bps=0.0,
            reconciliation_clear=True,
            storage_safe=True,
            auth_healthy=True,
            clock_skew_ms=0,
        )
        with tempfile.TemporaryDirectory() as directory:
            journal = ExecutionJournal(f"{directory}/execution.sqlite3")
            try:
                adapter = MockMEXCExecutionAdapter()
                coordinator = ShadowExecutionCoordinator(journal, adapter)
                first = coordinator.execute(proposal, safety, now_utc=now)
                second = coordinator.execute(proposal, safety, now_utc=now)
                self.assertEqual(first, second)
                self.assertFalse(first.submitted_to_exchange)
                self.assertEqual(len(adapter.receipts), 1)
                self.assertEqual(journal.integrity_check(), ["ok"])
            finally:
                journal.close()

    def test_proposal_namespace_is_shadow_specific(self):
        candidate = _execution_fixture_candidate(Settings())
        proposal = build_shadow_proposal(
            candidate,
            quantity=0.25,
            max_slippage_bps=25.0,
            risk_allocation_id="TEST",
        )
        self.assertTrue(proposal.proposal_id.startswith("DAOS-SHADOW-"))
        self.assertEqual(proposal.execution_mode.value, "SHADOW")
        self.assertEqual(proposal.order_type, "MARKET_SHADOW")


if __name__ == "__main__":
    unittest.main()

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import tempfile
import unittest
from pathlib import Path

from dream_account.execution_coordinator import (
    ReconciliationBlocked,
    ShadowExecutionCoordinator,
)
from dream_account.execution_journal import (
    ExecutionJournal,
    InvalidExecutionTransition,
    ProposalConflict,
)
from dream_account.execution_layer import (
    ExecutionMode,
    MockMEXCExecutionAdapter,
    OrderState,
    SafetyContext,
    ShadowReceipt,
    TradeProposal,
    create_shadow_intent,
)


NOW = datetime(2026, 9, 10, 12, 0, 0, tzinfo=timezone.utc)


def proposal(**overrides) -> TradeProposal:
    payload = dict(
        proposal_id="persist-001",
        authority_id="AUTH-FROZEN-001",
        evidence_fingerprint="fingerprint-001",
        created_at_utc=(NOW - timedelta(seconds=1)).isoformat(),
        expires_at_utc=(NOW + timedelta(minutes=5)).isoformat(),
        symbol="BTCUSDT",
        market_type="SPOT",
        side="BUY",
        order_type="LIMIT",
        reference_price=100.0,
        quantity=0.01,
        stop_spec={"type": "price", "value": 95.0},
        exit_spec={"type": "price", "value": 110.0},
        max_slippage_bps=10.0,
        risk_allocation_id="RISK-001",
        execution_mode=ExecutionMode.SHADOW,
    )
    payload.update(overrides)
    return TradeProposal(**payload)


def safety(**overrides) -> SafetyContext:
    payload = dict(market_data_timestamp_utc=(NOW - timedelta(seconds=2)).isoformat())
    payload.update(overrides)
    return SafetyContext(**payload)


class CountingMockAdapter(MockMEXCExecutionAdapter):
    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def submit(self, proposal, intent):
        self.calls += 1
        return super().submit(proposal, intent)


class UnsafeClaimAdapter:
    def submit(self, proposal, intent):
        return ShadowReceipt(
            proposal_id=proposal.proposal_id,
            idempotency_key=intent.idempotency_key,
            state=OrderState.SHADOW_RECORDED,
            submitted_to_exchange=True,
        )


class GateKPersistentExecutionTests(unittest.TestCase):
    def test_shadow_receipt_survives_restart_and_prevents_duplicate_submit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "execution.sqlite3")
            first_journal = ExecutionJournal(path)
            first_adapter = CountingMockAdapter()
            first = ShadowExecutionCoordinator(first_journal, first_adapter).execute(
                proposal(), safety(), now_utc=NOW
            )
            self.assertEqual(first.state, OrderState.SHADOW_RECORDED)
            self.assertEqual(first_adapter.calls, 1)
            self.assertEqual(first_journal.integrity_check(), ["ok"])
            first_journal.close()

            second_journal = ExecutionJournal(path)
            second_adapter = CountingMockAdapter()
            second = ShadowExecutionCoordinator(second_journal, second_adapter).execute(
                proposal(), safety(), now_utc=NOW
            )
            self.assertEqual(second, first)
            self.assertEqual(second_adapter.calls, 0)
            intent = create_shadow_intent(proposal())
            self.assertEqual(second_journal.get_intent(intent.idempotency_key).state, OrderState.SHADOW_RECORDED)
            self.assertEqual(second_journal.integrity_check(), ["ok"])
            second_journal.close()

    def test_crash_before_adapter_call_fails_closed_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "execution.sqlite3")
            journal = ExecutionJournal(path)
            adapter = CountingMockAdapter()
            coordinator = ShadowExecutionCoordinator(journal, adapter)

            def crash(state):
                if state is OrderState.SUBMITTING:
                    raise RuntimeError("simulated process death")

            with self.assertRaisesRegex(RuntimeError, "simulated process death"):
                coordinator.execute(proposal(), safety(), now_utc=NOW, crash_hook=crash)
            self.assertEqual(adapter.calls, 0)
            intent = create_shadow_intent(proposal())
            self.assertEqual(journal.get_intent(intent.idempotency_key).state, OrderState.SUBMITTING)
            journal.close()

            restarted = ExecutionJournal(path)
            restarted_coordinator = ShadowExecutionCoordinator(restarted, CountingMockAdapter())
            self.assertEqual(restarted_coordinator.reconcile_after_restart(), 1)
            self.assertEqual(
                restarted.get_intent(intent.idempotency_key).state,
                OrderState.RECONCILIATION_REQUIRED,
            )
            with self.assertRaises(ReconciliationBlocked):
                restarted_coordinator.execute(proposal(), safety(), now_utc=NOW)
            self.assertEqual(restarted_coordinator.adapter.calls, 0)
            self.assertEqual(len(restarted.unresolved_reconciliation()), 1)
            restarted.close()

    def test_crash_after_adapter_return_before_receipt_commit_requires_reconciliation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "execution.sqlite3")
            journal = ExecutionJournal(path)
            adapter = CountingMockAdapter()
            coordinator = ShadowExecutionCoordinator(journal, adapter)

            def crash(state):
                if state is OrderState.ACKNOWLEDGED:
                    raise RuntimeError("simulated crash after adapter return")

            with self.assertRaisesRegex(RuntimeError, "after adapter return"):
                coordinator.execute(proposal(), safety(), now_utc=NOW, crash_hook=crash)
            self.assertEqual(adapter.calls, 1)
            key = create_shadow_intent(proposal()).idempotency_key
            self.assertEqual(journal.get_intent(key).state, OrderState.SUBMITTING)
            self.assertIsNone(journal.get_receipt(key))
            journal.close()

            restarted = ExecutionJournal(path)
            new_adapter = CountingMockAdapter()
            restarted_coordinator = ShadowExecutionCoordinator(restarted, new_adapter)
            self.assertEqual(restarted_coordinator.reconcile_after_restart(), 1)
            self.assertEqual(restarted.get_intent(key).state, OrderState.RECONCILIATION_REQUIRED)
            with self.assertRaises(ReconciliationBlocked):
                restarted_coordinator.execute(proposal(), safety(), now_utc=NOW)
            self.assertEqual(new_adapter.calls, 0)
            restarted.close()

    def test_crash_after_durable_receipt_recovers_without_resubmit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "execution.sqlite3")
            journal = ExecutionJournal(path)
            adapter = CountingMockAdapter()
            coordinator = ShadowExecutionCoordinator(journal, adapter)

            def crash(state):
                if state is OrderState.SHADOW_RECORDED:
                    raise RuntimeError("simulated crash after receipt commit")

            with self.assertRaisesRegex(RuntimeError, "after receipt commit"):
                coordinator.execute(proposal(), safety(), now_utc=NOW, crash_hook=crash)
            self.assertEqual(adapter.calls, 1)
            intent = create_shadow_intent(proposal())
            self.assertEqual(journal.get_intent(intent.idempotency_key).state, OrderState.SUBMITTING)
            self.assertIsNotNone(journal.get_receipt(intent.idempotency_key))
            journal.close()

            restarted = ExecutionJournal(path)
            new_adapter = CountingMockAdapter()
            restarted_coordinator = ShadowExecutionCoordinator(restarted, new_adapter)
            self.assertEqual(restarted_coordinator.reconcile_after_restart(), 1)
            self.assertEqual(restarted.get_intent(intent.idempotency_key).state, OrderState.SHADOW_RECORDED)
            receipt = restarted_coordinator.execute(proposal(), safety(), now_utc=NOW)
            self.assertFalse(receipt.submitted_to_exchange)
            self.assertEqual(new_adapter.calls, 0)
            restarted.close()

    def test_same_proposal_id_with_mutated_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = ExecutionJournal(str(Path(directory) / "execution.sqlite3"))
            journal.record_proposal(proposal())
            with self.assertRaises(ProposalConflict):
                journal.record_proposal(proposal(quantity=0.02))
            journal.close()

    def test_state_machine_blocks_transition_out_of_terminal_shadow_state(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = ExecutionJournal(str(Path(directory) / "execution.sqlite3"))
            adapter = CountingMockAdapter()
            ShadowExecutionCoordinator(journal, adapter).execute(proposal(), safety(), now_utc=NOW)
            key = create_shadow_intent(proposal()).idempotency_key
            with self.assertRaises(InvalidExecutionTransition):
                journal.transition(key, OrderState.VALIDATED, "illegal_reopen")
            journal.close()

    def test_entry_and_exit_legs_have_separate_durable_idempotency_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = ExecutionJournal(str(Path(directory) / "execution.sqlite3"))
            adapter = CountingMockAdapter()
            coordinator = ShadowExecutionCoordinator(journal, adapter)
            entry = coordinator.execute(proposal(), safety(), logical_leg="ENTRY", now_utc=NOW)
            exit_receipt = coordinator.execute(proposal(), safety(), logical_leg="EXIT", now_utc=NOW)
            self.assertNotEqual(entry.idempotency_key, exit_receipt.idempotency_key)
            self.assertEqual(adapter.calls, 2)
            self.assertEqual(journal.get_intent(entry.idempotency_key).state, OrderState.SHADOW_RECORDED)
            self.assertEqual(journal.get_intent(exit_receipt.idempotency_key).state, OrderState.SHADOW_RECORDED)
            journal.close()

    def test_adapter_claiming_exchange_submission_is_quarantined(self):
        with tempfile.TemporaryDirectory() as directory:
            journal = ExecutionJournal(str(Path(directory) / "execution.sqlite3"))
            coordinator = ShadowExecutionCoordinator(journal, UnsafeClaimAdapter())
            with self.assertRaises(ReconciliationBlocked):
                coordinator.execute(proposal(), safety(), now_utc=NOW)
            key = create_shadow_intent(proposal()).idempotency_key
            self.assertEqual(journal.get_intent(key).state, OrderState.RECONCILIATION_REQUIRED)
            self.assertIsNone(journal.get_receipt(key))
            journal.close()

    def test_transition_audit_trail_is_persistent(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "execution.sqlite3")
            journal = ExecutionJournal(path)
            ShadowExecutionCoordinator(journal, CountingMockAdapter()).execute(
                proposal(), safety(), now_utc=NOW
            )
            key = create_shadow_intent(proposal()).idempotency_key
            expected = [
                (OrderState.PROPOSED, OrderState.VALIDATED, "intent_created"),
                (OrderState.VALIDATED, OrderState.SUBMITTING, "shadow_submit_boundary"),
                (OrderState.SUBMITTING, OrderState.SHADOW_RECORDED, "shadow_receipt_committed"),
            ]
            self.assertEqual(journal.transitions(key), expected)
            journal.close()
            reopened = ExecutionJournal(path)
            self.assertEqual(reopened.transitions(key), expected)
            reopened.close()


if __name__ == "__main__":
    unittest.main()

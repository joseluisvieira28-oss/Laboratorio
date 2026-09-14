from __future__ import annotations

from datetime import datetime
from typing import Callable

from .execution_journal import ExecutionJournal
from .execution_layer import (
    ExecutionAdapter,
    OrderState,
    SafetyContext,
    ShadowReceipt,
    TradeProposal,
    create_shadow_intent,
    validate_proposal,
)


class ReconciliationBlocked(RuntimeError):
    pass


class ShadowExecutionRejected(RuntimeError):
    pass


CrashHook = Callable[[OrderState], None]


class ShadowExecutionCoordinator:
    """Durable Gate K shadow coordinator.

    The coordinator deliberately accepts only the Gate K adapter protocol. It does
    not contain credentials or network code. Durable state is committed before the
    mock submission boundary, then a receipt is committed before terminal state.
    """

    def __init__(self, journal: ExecutionJournal, adapter: ExecutionAdapter):
        self.journal = journal
        self.adapter = adapter

    def reconcile_after_restart(self) -> int:
        return len(self.journal.reconcile_after_restart())

    def execute(
        self,
        proposal: TradeProposal,
        safety: SafetyContext,
        *,
        logical_leg: str = "ENTRY",
        now_utc: datetime | None = None,
        crash_hook: CrashHook | None = None,
    ) -> ShadowReceipt:
        self.journal.record_proposal(proposal)
        validation = validate_proposal(proposal, safety, now_utc=now_utc)
        if not validation.accepted:
            raise ShadowExecutionRejected(",".join(validation.reasons))

        intent = create_shadow_intent(proposal, logical_leg)
        durable, _created = self.journal.create_or_get_intent(intent)

        persisted_receipt = self.journal.get_receipt(intent.idempotency_key)
        if persisted_receipt is not None:
            if persisted_receipt.submitted_to_exchange:
                raise ReconciliationBlocked("Gate K receipt unexpectedly claims exchange submission")
            return persisted_receipt

        if durable.state is OrderState.RECONCILIATION_REQUIRED:
            raise ReconciliationBlocked("durable intent requires reconciliation before retry")
        if durable.state in {
            OrderState.SUBMITTING,
            OrderState.ACKNOWLEDGED,
            OrderState.PARTIALLY_FILLED,
            OrderState.FILLED,
            OrderState.EXIT_PENDING,
        }:
            self.journal.transition(
                intent.idempotency_key,
                OrderState.RECONCILIATION_REQUIRED,
                "retry_encountered_uncertain_state",
            )
            raise ReconciliationBlocked("uncertain durable state: automatic retry blocked")
        if durable.state is OrderState.SHADOW_RECORDED:
            raise ReconciliationBlocked("terminal shadow state has no durable receipt")
        if durable.state is not OrderState.VALIDATED:
            raise ReconciliationBlocked(f"intent state {durable.state.value} is not executable")

        self.journal.transition(intent.idempotency_key, OrderState.SUBMITTING, "shadow_submit_boundary")
        if crash_hook is not None:
            crash_hook(OrderState.SUBMITTING)

        receipt = self.adapter.submit(proposal, intent)
        # This hook models the dangerous future-live boundary where an adapter may
        # have returned but its receipt has not yet been durably committed.
        if crash_hook is not None:
            crash_hook(OrderState.ACKNOWLEDGED)

        if receipt.submitted_to_exchange:
            self.journal.transition(
                intent.idempotency_key,
                OrderState.RECONCILIATION_REQUIRED,
                "gate_k_exchange_submission_claim",
            )
            raise ReconciliationBlocked("Gate K adapter claimed a real exchange submission")
        if receipt.proposal_id != proposal.proposal_id or receipt.idempotency_key != intent.idempotency_key:
            self.journal.transition(
                intent.idempotency_key,
                OrderState.RECONCILIATION_REQUIRED,
                "receipt_identity_mismatch",
            )
            raise ReconciliationBlocked("adapter receipt identity mismatch")
        if receipt.state is not OrderState.SHADOW_RECORDED:
            self.journal.transition(
                intent.idempotency_key,
                OrderState.RECONCILIATION_REQUIRED,
                "unexpected_shadow_receipt_state",
            )
            raise ReconciliationBlocked("unexpected Gate K receipt state")

        self.journal.record_receipt(receipt)
        if crash_hook is not None:
            crash_hook(OrderState.SHADOW_RECORDED)
        self.journal.transition(intent.idempotency_key, OrderState.SHADOW_RECORDED, "shadow_receipt_committed")
        return receipt

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from .execution_layer import ExecutionMode, OrderIntent, OrderState, ShadowReceipt, TradeProposal


SCHEMA = """
CREATE TABLE IF NOT EXISTS execution_proposals(
    proposal_id TEXT PRIMARY KEY,
    authority_id TEXT NOT NULL,
    evidence_fingerprint TEXT NOT NULL,
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS execution_intents(
    idempotency_key TEXT PRIMARY KEY,
    proposal_id TEXT NOT NULL,
    logical_leg TEXT NOT NULL,
    state TEXT NOT NULL,
    execution_mode TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    receipt_payload TEXT,
    UNIQUE(proposal_id, logical_leg),
    FOREIGN KEY(proposal_id) REFERENCES execution_proposals(proposal_id)
);
CREATE TABLE IF NOT EXISTS execution_transitions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    idempotency_key TEXT NOT NULL,
    from_state TEXT NOT NULL,
    to_state TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    reason TEXT NOT NULL,
    FOREIGN KEY(idempotency_key) REFERENCES execution_intents(idempotency_key)
);
CREATE INDEX IF NOT EXISTS idx_execution_intents_state ON execution_intents(state);
CREATE INDEX IF NOT EXISTS idx_execution_transitions_key ON execution_transitions(idempotency_key, id);
"""


TERMINAL_STATES = {
    OrderState.SHADOW_RECORDED,
    OrderState.CLOSED,
    OrderState.REJECTED,
    OrderState.EXPIRED,
    OrderState.CANCELLED,
    OrderState.KILL_SWITCHED,
}

UNCERTAIN_AFTER_RESTART = {
    OrderState.SUBMITTING,
    OrderState.ACKNOWLEDGED,
    OrderState.PARTIALLY_FILLED,
    OrderState.FILLED,
    OrderState.EXIT_PENDING,
}

ALLOWED_TRANSITIONS: dict[OrderState, set[OrderState]] = {
    OrderState.PROPOSED: {
        OrderState.VALIDATED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
        OrderState.KILL_SWITCHED,
    },
    OrderState.VALIDATED: {
        OrderState.SUBMITTING,
        OrderState.SHADOW_RECORDED,
        OrderState.REJECTED,
        OrderState.EXPIRED,
        OrderState.CANCELLED,
        OrderState.KILL_SWITCHED,
    },
    OrderState.SUBMITTING: {
        OrderState.ACKNOWLEDGED,
        OrderState.SHADOW_RECORDED,
        OrderState.REJECTED,
        OrderState.RECONCILIATION_REQUIRED,
    },
    OrderState.ACKNOWLEDGED: {
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.REJECTED,
        OrderState.RECONCILIATION_REQUIRED,
    },
    OrderState.PARTIALLY_FILLED: {
        OrderState.FILLED,
        OrderState.CANCELLED,
        OrderState.RECONCILIATION_REQUIRED,
    },
    OrderState.FILLED: {
        OrderState.EXIT_PENDING,
        OrderState.CLOSED,
        OrderState.RECONCILIATION_REQUIRED,
    },
    OrderState.EXIT_PENDING: {
        OrderState.CLOSED,
        OrderState.CANCELLED,
        OrderState.RECONCILIATION_REQUIRED,
    },
    OrderState.RECONCILIATION_REQUIRED: {
        OrderState.SHADOW_RECORDED,
        OrderState.ACKNOWLEDGED,
        OrderState.PARTIALLY_FILLED,
        OrderState.FILLED,
        OrderState.CLOSED,
        OrderState.CANCELLED,
    },
}


class ExecutionJournalError(RuntimeError):
    pass


class InvalidExecutionTransition(ExecutionJournalError):
    pass


class ProposalConflict(ExecutionJournalError):
    pass


@dataclass(frozen=True)
class IntentRecord:
    idempotency_key: str
    proposal_id: str
    logical_leg: str
    state: OrderState
    execution_mode: ExecutionMode
    created_at: str
    updated_at: str
    receipt_payload: str | None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _proposal_payload(proposal: TradeProposal) -> str:
    payload = asdict(proposal)
    payload["execution_mode"] = proposal.execution_mode.value
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _receipt_payload(receipt: ShadowReceipt) -> str:
    payload = asdict(receipt)
    payload["state"] = receipt.state.value
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


class ExecutionJournal:
    """Durable execution state for Gate K, with no exchange/network code."""

    def __init__(self, path: str):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, timeout=30.0)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript(SCHEMA)
        self.connection.commit()

    def close(self) -> None:
        self.connection.close()

    def integrity_check(self) -> list[str]:
        return [row[0] for row in self.connection.execute("PRAGMA integrity_check").fetchall()]

    def record_proposal(self, proposal: TradeProposal) -> None:
        payload = _proposal_payload(proposal)
        existing = self.connection.execute(
            "SELECT payload FROM execution_proposals WHERE proposal_id=?", (proposal.proposal_id,)
        ).fetchone()
        if existing is not None:
            if existing[0] != payload:
                raise ProposalConflict("proposal_id already exists with different immutable content")
            return
        with self.connection:
            self.connection.execute(
                "INSERT INTO execution_proposals(proposal_id,authority_id,evidence_fingerprint,payload,created_at) VALUES(?,?,?,?,?)",
                (proposal.proposal_id, proposal.authority_id, proposal.evidence_fingerprint, payload, _now()),
            )

    def create_or_get_intent(self, intent: OrderIntent) -> tuple[IntentRecord, bool]:
        now = _now()
        try:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO execution_intents(idempotency_key,proposal_id,logical_leg,state,execution_mode,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                    (
                        intent.idempotency_key,
                        intent.proposal_id,
                        intent.logical_leg,
                        intent.state.value,
                        intent.execution_mode.value,
                        now,
                        now,
                    ),
                )
                self.connection.execute(
                    "INSERT INTO execution_transitions(idempotency_key,from_state,to_state,observed_at,reason) VALUES(?,?,?,?,?)",
                    (
                        intent.idempotency_key,
                        OrderState.PROPOSED.value,
                        intent.state.value,
                        now,
                        "intent_created",
                    ),
                )
            return self.get_intent(intent.idempotency_key), True
        except sqlite3.IntegrityError:
            existing = self.get_intent(intent.idempotency_key)
            if (
                existing.proposal_id != intent.proposal_id
                or existing.logical_leg != intent.logical_leg
                or existing.execution_mode is not intent.execution_mode
            ):
                raise ExecutionJournalError("idempotency-key collision with different intent")
            return existing, False

    def get_intent(self, idempotency_key: str) -> IntentRecord:
        row = self.connection.execute(
            "SELECT idempotency_key,proposal_id,logical_leg,state,execution_mode,created_at,updated_at,receipt_payload FROM execution_intents WHERE idempotency_key=?",
            (idempotency_key,),
        ).fetchone()
        if row is None:
            raise KeyError(idempotency_key)
        return IntentRecord(
            idempotency_key=row[0],
            proposal_id=row[1],
            logical_leg=row[2],
            state=OrderState(row[3]),
            execution_mode=ExecutionMode(row[4]),
            created_at=row[5],
            updated_at=row[6],
            receipt_payload=row[7],
        )

    def transition(self, idempotency_key: str, to_state: OrderState, reason: str) -> IntentRecord:
        current = self.get_intent(idempotency_key)
        if current.state == to_state:
            return current
        if current.state in TERMINAL_STATES:
            raise InvalidExecutionTransition(f"terminal state {current.state.value} cannot transition")
        if to_state not in ALLOWED_TRANSITIONS.get(current.state, set()):
            raise InvalidExecutionTransition(f"{current.state.value} -> {to_state.value} is not allowed")
        now = _now()
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE execution_intents SET state=?,updated_at=? WHERE idempotency_key=? AND state=?",
                (to_state.value, now, idempotency_key, current.state.value),
            )
            if cursor.rowcount != 1:
                raise ExecutionJournalError("concurrent execution-state change detected")
            self.connection.execute(
                "INSERT INTO execution_transitions(idempotency_key,from_state,to_state,observed_at,reason) VALUES(?,?,?,?,?)",
                (idempotency_key, current.state.value, to_state.value, now, reason),
            )
        return self.get_intent(idempotency_key)

    def record_receipt(self, receipt: ShadowReceipt) -> None:
        current = self.get_intent(receipt.idempotency_key)
        if current.proposal_id != receipt.proposal_id:
            raise ExecutionJournalError("receipt proposal does not match durable intent")
        payload = _receipt_payload(receipt)
        if current.receipt_payload is not None and current.receipt_payload != payload:
            raise ExecutionJournalError("immutable receipt conflict")
        with self.connection:
            self.connection.execute(
                "UPDATE execution_intents SET receipt_payload=?,updated_at=? WHERE idempotency_key=?",
                (payload, _now(), receipt.idempotency_key),
            )

    def get_receipt(self, idempotency_key: str) -> ShadowReceipt | None:
        record = self.get_intent(idempotency_key)
        if record.receipt_payload is None:
            return None
        payload = json.loads(record.receipt_payload)
        return ShadowReceipt(
            proposal_id=payload["proposal_id"],
            idempotency_key=payload["idempotency_key"],
            state=OrderState(payload["state"]),
            submitted_to_exchange=bool(payload["submitted_to_exchange"]),
        )

    def transitions(self, idempotency_key: str) -> list[tuple[OrderState, OrderState, str]]:
        rows = self.connection.execute(
            "SELECT from_state,to_state,reason FROM execution_transitions WHERE idempotency_key=? ORDER BY id",
            (idempotency_key,),
        ).fetchall()
        return [(OrderState(a), OrderState(b), reason) for a, b, reason in rows]

    def reconcile_after_restart(self) -> list[IntentRecord]:
        """Resolve proven shadow receipts; fail closed on every uncertain boundary."""
        placeholders = ",".join("?" for _ in UNCERTAIN_AFTER_RESTART)
        rows = self.connection.execute(
            f"SELECT idempotency_key FROM execution_intents WHERE state IN ({placeholders}) ORDER BY idempotency_key",
            tuple(state.value for state in UNCERTAIN_AFTER_RESTART),
        ).fetchall()
        updated: list[IntentRecord] = []
        for (key,) in rows:
            receipt = self.get_receipt(key)
            if (
                receipt is not None
                and receipt.state is OrderState.SHADOW_RECORDED
                and not receipt.submitted_to_exchange
            ):
                updated.append(self.transition(key, OrderState.SHADOW_RECORDED, "restart_durable_shadow_receipt"))
            else:
                updated.append(self.transition(key, OrderState.RECONCILIATION_REQUIRED, "restart_uncertain_boundary"))
        return updated

    def unresolved_reconciliation(self) -> list[IntentRecord]:
        rows = self.connection.execute(
            "SELECT idempotency_key FROM execution_intents WHERE state=? ORDER BY idempotency_key",
            (OrderState.RECONCILIATION_REQUIRED.value,),
        ).fetchall()
        return [self.get_intent(row[0]) for row in rows]

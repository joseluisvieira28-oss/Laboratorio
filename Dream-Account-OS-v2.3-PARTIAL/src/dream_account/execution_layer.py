from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol


class ExecutionMode(str, Enum):
    SHADOW = "SHADOW"
    MICRO_LIVE = "MICRO_LIVE"
    CONTROLLED_LIVE = "CONTROLLED_LIVE"


class OrderState(str, Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    SHADOW_RECORDED = "SHADOW_RECORDED"
    SUBMITTING = "SUBMITTING"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    EXIT_PENDING = "EXIT_PENDING"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    RECONCILIATION_REQUIRED = "RECONCILIATION_REQUIRED"
    KILL_SWITCHED = "KILL_SWITCHED"


@dataclass(frozen=True)
class TradeProposal:
    proposal_id: str
    authority_id: str
    evidence_fingerprint: str
    created_at_utc: str
    expires_at_utc: str
    symbol: str
    market_type: str
    side: str
    order_type: str
    reference_price: float
    quantity: float
    stop_spec: dict[str, Any]
    exit_spec: dict[str, Any] = field(default_factory=dict)
    max_slippage_bps: float = 0.0
    risk_allocation_id: str = ""
    execution_mode: ExecutionMode = ExecutionMode.SHADOW


@dataclass(frozen=True)
class SafetyContext:
    market_data_timestamp_utc: str
    api_tradable: bool = True
    precision_valid: bool = True
    minimum_valid: bool = True
    spread_bps: float = 0.0
    observed_slippage_bps: float = 0.0
    kill_switch: bool = False
    daily_loss_locked: bool = False
    reconciliation_clear: bool = True
    storage_safe: bool = True
    auth_healthy: bool = True
    clock_skew_ms: int = 0
    max_clock_skew_ms: int = 5_000
    max_market_age_seconds: int = 30


@dataclass(frozen=True)
class ValidationResult:
    accepted: bool
    state: OrderState
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True)
class OrderIntent:
    proposal_id: str
    logical_leg: str
    idempotency_key: str
    state: OrderState
    execution_mode: ExecutionMode


@dataclass(frozen=True)
class ShadowReceipt:
    proposal_id: str
    idempotency_key: str
    state: OrderState
    submitted_to_exchange: bool = False


class ExecutionAdapter(Protocol):
    def submit(self, proposal: TradeProposal, intent: OrderIntent) -> ShadowReceipt:
        ...


class MockMEXCExecutionAdapter:
    """Gate K adapter. Records a shadow receipt and never touches a network."""

    def __init__(self) -> None:
        self.receipts: dict[str, ShadowReceipt] = {}

    def submit(self, proposal: TradeProposal, intent: OrderIntent) -> ShadowReceipt:
        existing = self.receipts.get(intent.idempotency_key)
        if existing:
            return existing
        receipt = ShadowReceipt(
            proposal_id=proposal.proposal_id,
            idempotency_key=intent.idempotency_key,
            state=OrderState.SHADOW_RECORDED,
            submitted_to_exchange=False,
        )
        self.receipts[intent.idempotency_key] = receipt
        return receipt


class MEXCAuthenticatedAdapter:
    """Deliberately disabled Gate K skeleton. Real submission is unreachable."""

    def submit(self, proposal: TradeProposal, intent: OrderIntent) -> ShadowReceipt:
        raise RuntimeError("Gate K is SHADOW_ONLY: live MEXC submission is disabled")


def _parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must be timezone-aware UTC")
    return parsed.astimezone(timezone.utc)


def make_idempotency_key(proposal_id: str, logical_leg: str = "ENTRY") -> str:
    payload = f"{proposal_id}|{logical_leg}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_proposal(
    proposal: TradeProposal,
    safety: SafetyContext,
    *,
    now_utc: datetime | None = None,
) -> ValidationResult:
    now = (now_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    reasons: list[str] = []

    required_text = {
        "proposal_id": proposal.proposal_id,
        "authority_id": proposal.authority_id,
        "evidence_fingerprint": proposal.evidence_fingerprint,
        "symbol": proposal.symbol,
        "market_type": proposal.market_type,
        "side": proposal.side,
        "order_type": proposal.order_type,
        "risk_allocation_id": proposal.risk_allocation_id,
    }
    for name, value in required_text.items():
        if not str(value).strip():
            reasons.append(f"missing_{name}")

    if proposal.execution_mode is not ExecutionMode.SHADOW:
        reasons.append("gate_k_shadow_only")
    if proposal.reference_price <= 0:
        reasons.append("invalid_reference_price")
    if proposal.quantity <= 0:
        reasons.append("invalid_quantity")
    if not proposal.stop_spec:
        reasons.append("missing_stop_spec")
    if proposal.max_slippage_bps < 0:
        reasons.append("invalid_slippage_limit")

    try:
        created = _parse_utc(proposal.created_at_utc)
        expires = _parse_utc(proposal.expires_at_utc)
        market_ts = _parse_utc(safety.market_data_timestamp_utc)
    except (TypeError, ValueError):
        return ValidationResult(False, OrderState.REJECTED, ("invalid_timestamp",))

    if expires <= created:
        reasons.append("invalid_expiry_window")
    if now >= expires:
        reasons.append("expired")
    if (now - market_ts).total_seconds() > safety.max_market_age_seconds:
        reasons.append("stale_market_data")
    if market_ts > now:
        reasons.append("future_market_data")
    if not safety.api_tradable:
        reasons.append("symbol_not_api_tradable")
    if not safety.precision_valid:
        reasons.append("precision_invalid")
    if not safety.minimum_valid:
        reasons.append("minimum_invalid")
    if safety.observed_slippage_bps > proposal.max_slippage_bps:
        reasons.append("slippage_breach")
    if safety.kill_switch:
        reasons.append("kill_switch")
    if safety.daily_loss_locked:
        reasons.append("daily_loss_lock")
    if not safety.reconciliation_clear:
        reasons.append("reconciliation_required")
    if not safety.storage_safe:
        reasons.append("storage_unsafe")
    if not safety.auth_healthy:
        reasons.append("auth_unhealthy")
    if abs(safety.clock_skew_ms) > safety.max_clock_skew_ms:
        reasons.append("clock_skew")

    if reasons:
        state = OrderState.KILL_SWITCHED if "kill_switch" in reasons else (
            OrderState.EXPIRED if "expired" in reasons else OrderState.REJECTED
        )
        return ValidationResult(False, state, tuple(reasons))
    return ValidationResult(True, OrderState.VALIDATED, ())


def create_shadow_intent(proposal: TradeProposal, logical_leg: str = "ENTRY") -> OrderIntent:
    if proposal.execution_mode is not ExecutionMode.SHADOW:
        raise RuntimeError("Gate K cannot create live order intents")
    return OrderIntent(
        proposal_id=proposal.proposal_id,
        logical_leg=logical_leg,
        idempotency_key=make_idempotency_key(proposal.proposal_id, logical_leg),
        state=OrderState.VALIDATED,
        execution_mode=ExecutionMode.SHADOW,
    )

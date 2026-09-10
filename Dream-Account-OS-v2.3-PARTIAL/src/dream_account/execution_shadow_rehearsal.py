from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable

from .config import Settings
from .database import Journal
from .engines import calculate_costs, score_candidate
from .execution_coordinator import ShadowExecutionCoordinator
from .execution_journal import ExecutionJournal
from .execution_layer import ExecutionMode, MockMEXCExecutionAdapter, SafetyContext, TradeProposal
from .execution_mexc_reconciliation_probe import load_guarded_client_from_env, run_reconciliation
from .mexc_client import MEXCClient
from .models import Candidate
from .scanner import Scanner


SHADOW_REHEARSAL_ENABLE_ENV = "MEXC_SHADOW_REHEARSAL_ENABLE"
AUTHORITY_ID = "DREAM-ACCOUNT-OS-GATE-K-SHADOW-REHEARSAL-V0.1"
MAX_SLIPPAGE_BPS_FIXTURE = 25.0
FIXTURE_RISK_PERCENT = 2.0
FIXTURE_BALANCE_QUOTE = 56.0


class ShadowProposalBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class ProposalReadiness:
    ready: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ShadowRehearsalReport:
    status: str
    live_scan_status: str
    live_pairs_scanned: int
    live_fast_pass: int
    live_deep_pass: int
    live_candidate_count: int
    live_actionable_count: int
    live_trade_proposals_created: int
    live_block_reason_counts: dict[str, int]
    fixture_pipeline_state: str
    fixture_submitted_to_exchange: bool
    fixture_journal_integrity: str
    fixture_idempotent_replay: bool
    reconciliation_status: str
    reconciliation_symbols_queried: int
    reconciliation_daos_open_orders: int
    reconciliation_daos_recent_trades: int
    exchange_mutation_routes: int
    risk_semantics_note: str
    note: str

    def fingerprint(self) -> str:
        payload = json.dumps(asdict(self), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def sanitized_dict(self) -> dict[str, object]:
        payload = asdict(self)
        payload["fingerprint"] = self.fingerprint()
        return payload


def candidate_readiness(candidate: Candidate) -> ProposalReadiness:
    reasons: list[str] = []
    if candidate.market_type.upper() != "SPOT":
        reasons.append("market_not_spot")
    if candidate.status != "LONG_CANDIDATE":
        reasons.append("status_not_long_candidate")
    if candidate.tier not in {"A", "A+"}:
        reasons.append("tier_below_a")
    if candidate.rejection_reasons:
        reasons.append("candidate_rejected")
    if candidate.setup == "NONE":
        reasons.append("missing_setup")
    if candidate.entry is None or candidate.entry <= 0:
        reasons.append("missing_entry")
    if candidate.stop is None or candidate.stop <= 0:
        reasons.append("missing_stop")
    if candidate.tp1 is None or candidate.tp1 <= 0:
        reasons.append("missing_tp1")
    if candidate.tp2 is None or candidate.tp2 <= 0:
        reasons.append("missing_tp2")
    if candidate.entry is not None and candidate.stop is not None and candidate.stop >= candidate.entry:
        reasons.append("invalid_long_stop_geometry")
    if candidate.entry is not None and candidate.tp1 is not None and candidate.tp1 <= candidate.entry:
        reasons.append("invalid_long_tp1_geometry")
    if candidate.entry is not None and candidate.tp2 is not None and candidate.tp2 <= candidate.entry:
        reasons.append("invalid_long_tp2_geometry")
    return ProposalReadiness(not reasons, tuple(reasons))


def candidate_evidence_fingerprint(candidate: Candidate) -> str:
    payload = json.dumps(candidate.as_dict(), sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def build_shadow_proposal(
    candidate: Candidate,
    *,
    quantity: float,
    max_slippage_bps: float,
    risk_allocation_id: str,
    created_at: datetime | None = None,
) -> TradeProposal:
    readiness = candidate_readiness(candidate)
    if not readiness.ready:
        raise ShadowProposalBlocked(",".join(readiness.reasons))
    if quantity <= 0:
        raise ShadowProposalBlocked("invalid_quantity")
    if max_slippage_bps < 0:
        raise ShadowProposalBlocked("invalid_slippage_limit")
    if not risk_allocation_id.strip():
        raise ShadowProposalBlocked("missing_risk_allocation_id")

    now = (created_at or datetime.now(timezone.utc)).astimezone(timezone.utc)
    evidence = candidate_evidence_fingerprint(candidate)
    proposal_id_material = f"{AUTHORITY_ID}|{candidate.symbol}|{candidate.observed_at}|{evidence}".encode("utf-8")
    proposal_id = "DAOS-SHADOW-" + hashlib.sha256(proposal_id_material).hexdigest()[:24]
    return TradeProposal(
        proposal_id=proposal_id,
        authority_id=AUTHORITY_ID,
        evidence_fingerprint=evidence,
        created_at_utc=now.isoformat(),
        expires_at_utc=(now + timedelta(seconds=30)).isoformat(),
        symbol=candidate.symbol,
        market_type="SPOT",
        side="BUY",
        order_type="MARKET_SHADOW",
        reference_price=float(candidate.entry),
        quantity=float(quantity),
        stop_spec={"type": "PRICE", "price": float(candidate.stop)},
        exit_spec={"tp1": float(candidate.tp1), "tp2": float(candidate.tp2)},
        max_slippage_bps=float(max_slippage_bps),
        risk_allocation_id=risk_allocation_id,
        execution_mode=ExecutionMode.SHADOW,
    )


def _live_block_counts(candidates: Iterable[Candidate]) -> tuple[int, Counter[str]]:
    actionable = 0
    reasons: Counter[str] = Counter()
    for candidate in candidates:
        readiness = candidate_readiness(candidate)
        if readiness.ready:
            actionable += 1
        else:
            reasons.update(readiness.reasons)
            reasons.update(candidate.rejection_reasons)
    return actionable, reasons


def _execution_fixture_candidate(settings: Settings) -> Candidate:
    """Create a deterministic infrastructure fixture, not a market claim.

    The geometry is chosen only to exercise the existing scoring/cost/sizing handoff
    with a candidate that passes the already-existing V2.1 rules. It is never emitted
    as a real signal and never reaches a network mutation path.
    """
    entry, stop, tp1, tp2 = 100.0, 98.0, 106.0, 108.0
    costs = calculate_costs(entry, stop, tp1, 0.1, 0.05, 0.02)
    candidate = Candidate(
        "FIXTUREUSDT",
        "SPOT",
        entry,
        20_000_000.0,
        0.05,
        {"15m": 0.2, "1h": 0.4, "24h": 1.0},
        1.8,
        "RISK_ON_TREND",
        "BREAKOUT_RETEST",
        entry,
        stop,
        tp1,
        tp2,
    )
    candidate.status = "LONG_CANDIDATE"
    score_candidate(candidate, settings, costs.net_rr, catalyst_confirmed=True)
    return candidate


def _fixture_pipeline() -> tuple[str, bool, str, bool]:
    settings = Settings()
    with tempfile.TemporaryDirectory() as directory:
        execution_journal = ExecutionJournal(os.path.join(directory, "execution.sqlite3"))
        try:
            candidate = _execution_fixture_candidate(settings)
            readiness = candidate_readiness(candidate)
            if not readiness.ready:
                raise ShadowProposalBlocked("execution fixture not proposal-ready: " + ",".join(readiness.reasons))

            # Preserve the already-tested V2.1 sizing semantics used by test_engines:
            # 2 percent risk with a balance-capped 56 quote-notional unit fixture.
            # This intentionally does NOT reinterpret Settings.normal_risk_pct=0.02.
            quantity = FIXTURE_BALANCE_QUOTE / float(candidate.entry)
            proposal = build_shadow_proposal(
                candidate,
                quantity=quantity,
                max_slippage_bps=MAX_SLIPPAGE_BPS_FIXTURE,
                risk_allocation_id="FIXTURE-RISK-2PCT-BALANCE-CAPPED",
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
            coordinator = ShadowExecutionCoordinator(execution_journal, MockMEXCExecutionAdapter())
            first = coordinator.execute(proposal, safety)
            second = coordinator.execute(proposal, safety)
            integrity = execution_journal.integrity_check()
            return (
                first.state.value,
                bool(first.submitted_to_exchange),
                "ok" if integrity == ["ok"] else "fail",
                first == second,
            )
        finally:
            execution_journal.close()


def run_shadow_rehearsal() -> ShadowRehearsalReport:
    if os.getenv(SHADOW_REHEARSAL_ENABLE_ENV) != "1":
        raise ShadowProposalBlocked(f"set {SHADOW_REHEARSAL_ENABLE_ENV}=1 for one-shot rehearsal")

    settings = Settings()
    with tempfile.TemporaryDirectory() as directory:
        live_journal = Journal(os.path.join(directory, "live-scan.sqlite3"))
        try:
            live_scan = Scanner(MEXCClient(settings.request_timeout_seconds), settings, live_journal).live_scan()
        finally:
            live_journal.close()

    actionable, reason_counts = _live_block_counts(live_scan.candidates)

    # Gate K must not invent quantity/risk or manufacture a signal. Real proposals
    # are created only when the upstream signal object is complete and a separately
    # frozen sizing input exists. The current live scanner supplies neither a complete
    # actionable signal nor a sizing authority, so the live proposal count is zero.
    live_proposals_created = 0

    fixture_state, fixture_submitted, fixture_integrity, fixture_replay = _fixture_pipeline()
    reconciliation = run_reconciliation(load_guarded_client_from_env())

    if reconciliation.status != "PASS_CLEAN":
        status = "BLOCKED_RECONCILIATION"
    elif fixture_submitted:
        status = "BLOCKED_EXCHANGE_MUTATION"
    elif fixture_state != "SHADOW_RECORDED" or fixture_integrity != "ok" or not fixture_replay:
        status = "BLOCKED_SHADOW_PIPELINE"
    elif live_scan.status != "PASS":
        status = "BLOCKED_LIVE_DATA"
    elif actionable:
        status = "PASS_SIGNAL_PRESENT_SIZING_NOT_FROZEN"
    else:
        status = "PASS_NO_ACTIONABLE_LIVE_SIGNAL"

    return ShadowRehearsalReport(
        status=status,
        live_scan_status=live_scan.status,
        live_pairs_scanned=live_scan.pairs_scanned,
        live_fast_pass=live_scan.fast_pass,
        live_deep_pass=live_scan.deep_pass,
        live_candidate_count=len(live_scan.candidates),
        live_actionable_count=actionable,
        live_trade_proposals_created=live_proposals_created,
        live_block_reason_counts=dict(sorted(reason_counts.items())),
        fixture_pipeline_state=fixture_state,
        fixture_submitted_to_exchange=fixture_submitted,
        fixture_journal_integrity=fixture_integrity,
        fixture_idempotent_replay=fixture_replay,
        reconciliation_status=reconciliation.status,
        reconciliation_symbols_queried=reconciliation.symbols_queried,
        reconciliation_daos_open_orders=reconciliation.daos_open_order_count,
        reconciliation_daos_recent_trades=reconciliation.daos_recent_trade_count,
        exchange_mutation_routes=0,
        risk_semantics_note=(
            "Gate K intentionally does not auto-size real orders. Existing code has Settings.normal_risk_pct=0.02 "
            "while position_size consumes percent units and V2.1 tests use 2.0 for two percent. This ambiguity must "
            "be frozen before any live-sizing authority is created."
        ),
        note=(
            "Real-market scan is observational. Gate K never manufactures setup/entry/stop/targets/quantity. "
            "Deterministic infrastructure fixture exercises proposal->validation->journal->idempotency->shadow receipt. "
            "MEXC reconciliation remains authenticated GET-only."
        ),
    )


def main() -> int:
    try:
        report = run_shadow_rehearsal()
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": f"{type(exc).__name__}: {exc}"}, sort_keys=True))
        return 2
    print(json.dumps(report.sanitized_dict(), sort_keys=True))
    return 0 if report.status.startswith("PASS_") else 3


if __name__ == "__main__":
    raise SystemExit(main())

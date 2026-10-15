from __future__ import annotations

import hashlib
import json
import os
import tempfile
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from statistics import fmean, median
from typing import Iterable

from .collector import MEXCDataCollector
from .config import Settings
from .engines import calculate_costs, score_candidate, total_risk_position_size
from .execution_coordinator import ShadowExecutionCoordinator
from .execution_journal import ExecutionJournal
from .execution_layer import ExecutionMode, MockMEXCExecutionAdapter, SafetyContext, TradeProposal
from .execution_mexc_reconciliation_probe import load_guarded_client_from_env, run_reconciliation
from .live_engine import DreamAccountEngine
from .mexc_client import MEXCClient
from .models import Candidate


SHADOW_REHEARSAL_ENABLE_ENV = "MEXC_SHADOW_REHEARSAL_ENABLE"
AUTHORITY_ID = "DREAM-ACCOUNT-OS-GATE-K-SHADOW-REHEARSAL-V0.1"
MAX_SLIPPAGE_BPS_FIXTURE = 25.0
FIXTURE_BALANCE_QUOTE = 56.0
OBSERVATION_JOURNAL_ENV = "GATE_K_OBSERVATION_JOURNAL"


class ShadowProposalBlocked(RuntimeError):
    pass


@dataclass(frozen=True)
class ProposalReadiness:
    ready: bool
    reasons: tuple[str, ...]


def _canonical_fingerprint(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _numeric_summary(values: Iterable[float]) -> dict[str, object]:
    observed = sorted(float(value) for value in values)
    if not observed:
        return {"available": False, "count": 0, "min": None, "median": None, "mean": None,
                "max": None, "unavailable_reason": "no_observed_candidates"}
    return {"available": True, "count": len(observed), "min": observed[0], "median": median(observed),
            "mean": fmean(observed), "max": observed[-1], "unavailable_reason": None}


def _rate(numerator: int, denominator: int, denominator_name: str) -> dict[str, object]:
    if denominator == 0:
        return {"value": None, "numerator": numerator, "denominator": denominator,
                "undefined_reason": f"{denominator_name}_is_zero"}
    return {"value": numerator / denominator, "numerator": numerator, "denominator": denominator,
            "undefined_reason": None}


@dataclass(frozen=True)
class PhaseAObservation:
    observation_id: str
    run_id: str
    observed_at_utc: str
    status: str
    collector_gate_status: str
    expected_symbols: int | None
    verified_symbols: int | None
    data_coverage_pct: float | None
    data_quality_rejection_counts: dict[str, int] | None
    candidate_count: int | None
    deep_pass_count: int | None
    actionable_readiness_count: int | None
    candidate_tier_distribution: dict[str, int] | None
    candidate_status_distribution: dict[str, int] | None
    candidate_rejection_reason_counts: dict[str, int] | None
    readiness_block_reason_counts: dict[str, int] | None
    spread_summary: dict[str, object]
    volume_summary: dict[str, object]
    reconciliation_status: str
    reconciliation_symbols_queried: int | None
    reconciliation_daos_open_orders: int | None
    reconciliation_daos_recent_trades: int | None
    exchange_mutation_routes: int
    submitted_to_exchange: bool
    live_trade_proposals_created: int

    def evidence_dict(self) -> dict[str, object]:
        return asdict(self)

    def fingerprint(self) -> str:
        return _canonical_fingerprint(self.evidence_dict())

    def sanitized_dict(self) -> dict[str, object]:
        payload = self.evidence_dict()
        payload["fingerprint"] = self.fingerprint()
        return payload


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
    phase_a_observation: dict[str, object]
    aggregate_metrics: dict[str, object]
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


def build_phase_a_observation(*, run_id: str, observed_at: datetime, collector_gate_status: str,
                              expected_symbols: int | None, verified_symbols: int | None,
                              data_quality_rejection_counts: dict[str, int] | None,
                              candidates: Iterable[Candidate] | None, deep_pass_count: int | None,
                              reconciliation_status: str, reconciliation_symbols_queried: int | None,
                              reconciliation_daos_open_orders: int | None,
                              reconciliation_daos_recent_trades: int | None,
                              exchange_mutation_routes: int = 0, submitted_to_exchange: bool = False,
                              live_trade_proposals_created: int = 0) -> PhaseAObservation:
    if not run_id.strip() or observed_at.tzinfo is None or not collector_gate_status or not reconciliation_status:
        raise ShadowProposalBlocked("missing required Phase A observation identity/status input")
    observed_at_utc = observed_at.astimezone(timezone.utc).isoformat()
    candidate_list = None if candidates is None else list(candidates)
    coverage = None if expected_symbols in {None, 0} or verified_symbols is None else 100.0 * verified_symbols / expected_symbols
    if candidate_list is None:
        candidate_count = actionable = None
        tiers = statuses = rejection_counts = readiness_counts = None
        spreads: list[float] = []
        volumes: list[float] = []
    else:
        candidate_count = len(candidate_list)
        actionable, readiness_counter = _live_block_counts(candidate_list)
        tiers = dict(sorted(Counter(row.tier for row in candidate_list).items()))
        statuses = dict(sorted(Counter(row.status for row in candidate_list).items()))
        rejection_counts = dict(sorted(Counter(reason for row in candidate_list for reason in row.rejection_reasons).items()))
        readiness_counts = dict(sorted(readiness_counter.items()))
        spreads = [row.spread_pct for row in candidate_list]
        volumes = [row.volume_24h_usd for row in candidate_list]
    blocked = (exchange_mutation_routes != 0 or submitted_to_exchange or live_trade_proposals_created != 0 or
               reconciliation_status != "PASS_CLEAN" or collector_gate_status != "PASS")
    identity = f"{run_id}|{observed_at_utc}"
    return PhaseAObservation(
        observation_id="DAOS-OBS-" + hashlib.sha256(identity.encode()).hexdigest()[:24], run_id=run_id,
        observed_at_utc=observed_at_utc, status="BLOCKED" if blocked else "PASS",
        collector_gate_status=collector_gate_status, expected_symbols=expected_symbols,
        verified_symbols=verified_symbols, data_coverage_pct=coverage,
        data_quality_rejection_counts=None if data_quality_rejection_counts is None else dict(sorted(data_quality_rejection_counts.items())),
        candidate_count=candidate_count, deep_pass_count=deep_pass_count, actionable_readiness_count=actionable,
        candidate_tier_distribution=tiers, candidate_status_distribution=statuses,
        candidate_rejection_reason_counts=rejection_counts, readiness_block_reason_counts=readiness_counts,
        spread_summary=_numeric_summary(spreads), volume_summary=_numeric_summary(volumes),
        reconciliation_status=reconciliation_status, reconciliation_symbols_queried=reconciliation_symbols_queried,
        reconciliation_daos_open_orders=reconciliation_daos_open_orders,
        reconciliation_daos_recent_trades=reconciliation_daos_recent_trades,
        exchange_mutation_routes=exchange_mutation_routes, submitted_to_exchange=submitted_to_exchange,
        live_trade_proposals_created=live_trade_proposals_created,
    )


def aggregate_phase_a_observations(records: Iterable[PhaseAObservation | dict]) -> dict[str, object]:
    rows = [row.evidence_dict() if isinstance(row, PhaseAObservation) else dict(row) for row in records]
    total = len(rows)
    successful = [row for row in rows if row.get("status") == "PASS"]
    expected = sum(int(row["expected_symbols"]) for row in rows if row.get("expected_symbols") is not None)
    verified = sum(int(row["verified_symbols"]) for row in rows if row.get("verified_symbols") is not None)
    candidates = sum(int(row["candidate_count"]) for row in rows if row.get("candidate_count") is not None)
    deep = sum(int(row["deep_pass_count"]) for row in rows if row.get("deep_pass_count") is not None)
    ready = sum(int(row["actionable_readiness_count"]) for row in rows if row.get("actionable_readiness_count") is not None)
    reasons = Counter()
    for row in rows:
        reasons.update(row.get("readiness_block_reason_counts") or {})
    clean = sum(row.get("reconciliation_status") == "PASS_CLEAN" for row in successful)
    safe = sum(row.get("exchange_mutation_routes") == 0 and row.get("submitted_to_exchange") is False and
               row.get("live_trade_proposals_created") == 0 for row in rows)
    return {
        "DataCoverageRate": _rate(verified, expected, "expected_symbols"),
        "CandidateYield": _rate(candidates, verified, "verified_symbols"),
        "DeepPassRate": _rate(deep, candidates, "candidate_count"),
        "ReadinessRate": _rate(ready, candidates, "candidate_count"),
        "BlockReasonDistribution": dict(sorted(reasons.items())),
        "ReconciliationCleanRate": _rate(clean, len(successful), "successful_cycles"),
        "SafetyIntegrityRate": _rate(safe, total, "attempted_cycles"),
        "ObservationFailureRate": _rate(total - len(successful), total, "attempted_cycles"),
    }


def _execution_fixture_candidate(settings: Settings) -> Candidate:
    """Deterministic infrastructure fixture, never a market claim or real signal."""
    entry, stop, tp1, tp2 = 100.0, 98.0, 106.0, 108.0
    costs = calculate_costs(entry, stop, tp1, 0.1, 0.05, 0.02)
    candidate = Candidate(
        "FIXTUREUSDT", "SPOT", entry, 20_000_000.0, 0.05,
        {"15m": 0.2, "1h": 0.4, "24h": 1.0}, 1.8,
        "RISK_ON_TREND", "BREAKOUT_RETEST", entry, stop, tp1, tp2,
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

            costs = calculate_costs(
                float(candidate.entry), float(candidate.stop), float(candidate.tp1), 0.1, 0.05, 0.02
            )
            sizing = total_risk_position_size(
                FIXTURE_BALANCE_QUOTE,
                settings.normal_risk_pct,
                float(candidate.entry),
                float(candidate.stop),
                costs.estimated_cost_pct,
                FIXTURE_BALANCE_QUOTE,
            )
            quantity = float(sizing["position_notional_chf"]) / float(candidate.entry)
            proposal = build_shadow_proposal(
                candidate,
                quantity=quantity,
                max_slippage_bps=MAX_SLIPPAGE_BPS_FIXTURE,
                risk_allocation_id="FIXTURE-RISK-V2-NORMAL-TOTAL-RISK",
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


def _production_equivalent_market_observation(settings: Settings) -> tuple[str, str, int, int, dict[str, int], int, list[Candidate]]:
    """Run the same bulk collector + normalized engine path used in production.

    This deliberately keeps regime='UNVERIFIED', matching runtime_service.collect_once.
    It is observational only and never manufactures setup geometry or sizing.
    """
    client = MEXCClient(settings.request_timeout_seconds)
    collector = MEXCDataCollector(client)
    engine = DreamAccountEngine(settings)
    batch = collector.collect_spot()
    quality_counts = dict(sorted(Counter(batch.failed_symbols.values()).items()))
    if not batch.gate_passed:
        return batch.timestamp_utc, "FAIL_CLOSED", batch.expected_symbols, len(batch.verified), quality_counts, 0, []
    candidates = engine.evaluate(batch, "UNVERIFIED")
    deep_pass = len([candidate for candidate in candidates if not candidate.rejection_reasons])
    return batch.timestamp_utc, "PASS", batch.expected_symbols, len(batch.verified), quality_counts, deep_pass, candidates


def run_shadow_rehearsal() -> ShadowRehearsalReport:
    if os.getenv(SHADOW_REHEARSAL_ENABLE_ENV) != "1":
        raise ShadowProposalBlocked(f"set {SHADOW_REHEARSAL_ENABLE_ENV}=1 for one-shot rehearsal")

    settings = Settings()
    observed_at_raw, live_status, pairs_scanned, verified_count, quality_counts, deep_pass, live_candidates = _production_equivalent_market_observation(settings)
    actionable, reason_counts = _live_block_counts(live_candidates)

    # No real proposal may be created until upstream emits a complete trade object
    # with complete exchange/cost/precision inputs. Current production engine does
    # not emit that complete object, so real proposal creation remains exactly zero.
    live_proposals_created = 0

    fixture_state, fixture_submitted, fixture_integrity, fixture_replay = _fixture_pipeline()
    reconciliation = run_reconciliation(load_guarded_client_from_env())
    observed_at = datetime.fromisoformat(observed_at_raw.replace("Z", "+00:00"))
    run_id = os.getenv("GITHUB_RUN_ID", "manual-one-shot")
    observation = build_phase_a_observation(
        run_id=run_id, observed_at=observed_at, collector_gate_status=live_status,
        expected_symbols=pairs_scanned, verified_symbols=verified_count,
        data_quality_rejection_counts=quality_counts, candidates=live_candidates,
        deep_pass_count=deep_pass, reconciliation_status=reconciliation.status,
        reconciliation_symbols_queried=reconciliation.symbols_queried,
        reconciliation_daos_open_orders=reconciliation.daos_open_order_count,
        reconciliation_daos_recent_trades=reconciliation.daos_recent_trade_count,
        exchange_mutation_routes=0, submitted_to_exchange=False,
        live_trade_proposals_created=live_proposals_created,
    )
    journal_path = os.getenv(OBSERVATION_JOURNAL_ENV)
    if journal_path:
        observation_journal = ExecutionJournal(journal_path)
        try:
            observation_journal.record_phase_a_observation(
                observation.observation_id, observation.fingerprint(), observation.evidence_dict()
            )
            aggregates = aggregate_phase_a_observations(observation_journal.phase_a_observations())
        finally:
            observation_journal.close()
    else:
        aggregates = aggregate_phase_a_observations([observation])

    if reconciliation.status != "PASS_CLEAN":
        status = "BLOCKED_RECONCILIATION"
    elif fixture_submitted:
        status = "BLOCKED_EXCHANGE_MUTATION"
    elif fixture_state != "SHADOW_RECORDED" or fixture_integrity != "ok" or not fixture_replay:
        status = "BLOCKED_SHADOW_PIPELINE"
    elif live_status != "PASS":
        status = "BLOCKED_LIVE_DATA"
    elif actionable:
        status = "PASS_SIGNAL_PRESENT_NO_COMPLETE_TRADE_OBJECT"
    else:
        status = "PASS_NO_ACTIONABLE_LIVE_SIGNAL"

    return ShadowRehearsalReport(
        status=status,
        live_scan_status=live_status,
        live_pairs_scanned=pairs_scanned,
        live_fast_pass=len(live_candidates),
        live_deep_pass=deep_pass,
        live_candidate_count=len(live_candidates),
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
        phase_a_observation=observation.sanitized_dict(),
        aggregate_metrics=aggregates,
        risk_semantics_note=(
            "Prospective Numerical Risk Policy V2 uses percentage points: NORMAL=1.0 and DEFENSIVE=0.5; A+ does not "
            "increase risk. Total projected risk includes bounded costs and remains capital-capped. This shadow "
            "rehearsal does not create live-derived proposals or authorize real execution."
        ),
        note=(
            "Real market observation uses the same MEXCDataCollector + DreamAccountEngine path as production with "
            "regime UNVERIFIED. Gate K never manufactures setup/entry/stop/targets/quantity. Deterministic infrastructure "
            "fixture exercises proposal->validation->journal->idempotency->shadow receipt. MEXC reconciliation remains "
            "authenticated GET-only."
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

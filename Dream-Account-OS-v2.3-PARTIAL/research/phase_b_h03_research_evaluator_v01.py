from __future__ import annotations

"""Pure H03 evaluator: frozen H01 geometry/management + frozen H02 session gate.

This module consumes already-audited Candle objects only. It opens no files, has no
network route, authorizes no stage, and never submits to an exchange.
"""

from collections import Counter
from math import isfinite
from statistics import mean, median
from typing import Iterable, Mapping

from dream_account.engines import calculate_costs
from dream_account.models import Candle
from research.phase_b_h01_protect_after_tp1_v01 import simulate_h01_managed_outcome
from research.phase_b_h02_us_eu_overlap_session_gate_v01 import is_h02_signal_eligible
from research.phase_b_research_evaluator_v01 import (
    EvaluationMetrics,
    FixedCohortCostMetrics,
    ResearchTradeRecord,
    day_block_bootstrap_expectancy,
    split_contiguous_segments,
)
from research.phase_b_signal_formation_v01 import (
    TIMEFRAME_MS,
    CostAssumptions,
    ResearchParameters,
    derive_signal_geometries,
)


HYPOTHESIS_ID = "H03_BINANCE_CROSS_VENUE_US_EU_OVERLAP_REPLICATION"
FAMILY_ID = "PBR04_CROSS_VENUE_SESSION_GATED_MANAGED_BREAKOUT_RETEST_LONG"
BASE_COHORT_SOURCE = "BASE_SENSITIVITY_SELECTED_H03_BINANCE_TRADES"
LIVE_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False
HOLDOUT_2026_AUTHORIZED = False
MEXC_VALIDATION_2025_AUTHORIZED = False


def _profit_factor(values: list[float]) -> float | None:
    gains = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    return None if losses <= 0 else gains / losses


def _safe_rate(n: int, d: int) -> float | None:
    return n / d if d else None


def _exit_boundary(record: ResearchTradeRecord, segment: list[Candle]) -> int:
    return record.outcome.exit_open_time if record.outcome.exit_open_time is not None else segment[-1].open_time


def evaluate_h03_symbol(
    symbol: str,
    candles: Iterable[Candle],
    parameters: ResearchParameters,
    costs: CostAssumptions,
) -> tuple[list[ResearchTradeRecord], dict[str, int]]:
    """Evaluate one symbol; session eligibility is applied before overlap selection."""

    if not symbol or not isinstance(symbol, str):
        raise ValueError("symbol is required")
    parameters.validate()
    costs.validate()
    segments, gap_count = split_contiguous_segments(candles)
    records: list[ResearchTradeRecord] = []
    totals = Counter()

    for segment in segments:
        signals = derive_signal_geometries(segment, parameters, costs, require_regular_spacing=True)
        totals["raw_geometry_count"] += len(signals)
        totals["net_rr_rejected_count"] += sum(s.geometry_status == "REJECTED_NET_RR" for s in signals)
        ready = [s for s in signals if s.geometry_status == "GEOMETRY_READY"]
        session_eligible = [s for s in ready if is_h02_signal_eligible(s)]
        totals["session_rejected_ready_count"] += len(ready) - len(session_eligible)
        active_until: int | None = None
        for signal in session_eligible:
            if active_until is not None and signal.entry_open_time <= active_until:
                totals["overlap_skipped_count"] += 1
                continue
            outcome = simulate_h01_managed_outcome(
                signal,
                segment,
                costs,
                max_holding_bars=parameters.max_holding_bars,
                require_regular_spacing=True,
            )
            record = ResearchTradeRecord(symbol=symbol, signal=signal, outcome=outcome)
            records.append(record)
            active_until = _exit_boundary(record, segment)

    totals["contiguous_segment_count"] = len(segments)
    totals["detected_gap_count"] = gap_count
    totals["session_selected_trade_count"] = len(records)
    return records, dict(totals)


def evaluate_h03_universe(
    candles_by_symbol: Mapping[str, Iterable[Candle]],
    parameters: ResearchParameters,
    costs: CostAssumptions,
) -> tuple[list[ResearchTradeRecord], EvaluationMetrics, dict[str, int]]:
    if not candles_by_symbol:
        raise ValueError("candles_by_symbol must not be empty")
    records: list[ResearchTradeRecord] = []
    totals = Counter()
    data_times: list[int] = []

    for symbol in sorted(candles_by_symbol):
        raw = list(candles_by_symbol[symbol])
        data_times.extend(c.open_time for c in raw if c.closed)
        symbol_records, diagnostics = evaluate_h03_symbol(symbol, raw, parameters, costs)
        records.extend(symbol_records)
        totals.update(diagnostics)

    records.sort(key=lambda r: (r.signal.entry_open_time, r.symbol, r.signal.fingerprint))
    resolved = [r for r in records if r.outcome.net_r is not None]
    values = [float(r.outcome.net_r) for r in resolved]
    if any(not isfinite(v) for v in values):
        raise ValueError("non-finite net R encountered")
    resolved_count = len(resolved)
    outcomes = [r.outcome for r in resolved]
    frequency = None
    if data_times and records:
        span_days = (max(data_times) - min(data_times) + TIMEFRAME_MS) / 86_400_000
        if span_days > 0:
            frequency = len(records) / span_days * 30.0

    metrics = EvaluationMetrics(
        cost_scenario=costs.name,
        raw_geometry_count=totals["raw_geometry_count"],
        net_rr_rejected_count=totals["net_rr_rejected_count"],
        selected_trade_count=len(records),
        overlap_skipped_count=totals["overlap_skipped_count"],
        unresolved_trade_count=len(records) - resolved_count,
        resolved_trade_count=resolved_count,
        net_expectancy_r=mean(values) if values else None,
        median_net_r=median(values) if values else None,
        win_rate=_safe_rate(sum(v > 0 for v in values), resolved_count),
        loss_rate=_safe_rate(sum(v < 0 for v in values), resolved_count),
        profit_factor_r=_profit_factor(values),
        tp1_reach_rate=_safe_rate(sum(o.tp1_reached for o in outcomes), resolved_count),
        same_bar_ambiguity_rate=_safe_rate(sum(o.same_bar_stop_target_ambiguity for o in outcomes), resolved_count),
        time_exit_rate=_safe_rate(sum(o.exit_reason == "TIME_EXIT_NEXT_OPEN" for o in outcomes), resolved_count),
        stop_gap_rate=_safe_rate(sum(o.exit_reason in {"STOP_GAP", "PROTECTIVE_STOP_GAP"} for o in outcomes), resolved_count),
        signal_frequency_per_30d=frequency,
        symbol_distribution=dict(sorted(Counter(r.symbol for r in resolved).items())),
        contiguous_segment_count=totals["contiguous_segment_count"],
        detected_gap_count=totals["detected_gap_count"],
    )
    return records, metrics, dict(totals)


def reprice_h03_fixed_cohort(
    base_selected_records: Iterable[ResearchTradeRecord],
    alternative_costs: CostAssumptions,
    *,
    min_net_rr: float = 2.0,
) -> FixedCohortCostMetrics:
    alternative_costs.validate()
    records = list(base_selected_records)
    values: list[float] = []
    rr_violations = 0
    resolved_count = 0
    for record in records:
        signal = record.signal
        alt_rr = calculate_costs(
            entry=signal.entry,
            stop=signal.stop,
            target=signal.tp2,
            fee_pct_each_side=alternative_costs.fee_pct_each_side,
            spread_pct=alternative_costs.spread_pct,
            slippage_pct_each_side=alternative_costs.slippage_pct_each_side,
            funding_pct=0.0,
        ).net_rr
        if alt_rr < min_net_rr:
            rr_violations += 1
        if record.outcome.gross_return_pct is None:
            continue
        gross_fraction = record.outcome.gross_return_pct / 100.0
        stop_fraction = (signal.entry - signal.stop) / signal.entry
        cost_fraction = alternative_costs.round_trip_cost_pct / 100.0
        denominator = stop_fraction + cost_fraction
        if stop_fraction <= 0 or denominator <= 0:
            raise ValueError("invalid signal risk geometry")
        net_r = (gross_fraction - cost_fraction) / denominator
        if not isfinite(net_r):
            raise ValueError("non-finite repriced net R")
        values.append(net_r)
        resolved_count += 1

    return FixedCohortCostMetrics(
        cost_scenario=alternative_costs.name,
        cohort_source=BASE_COHORT_SOURCE,
        selected_trade_count=len(records),
        resolved_trade_count=resolved_count,
        unresolved_trade_count=len(records) - resolved_count,
        net_expectancy_r=mean(values) if values else None,
        median_net_r=median(values) if values else None,
        profit_factor_r=_profit_factor(values),
        net_rr_below_minimum_count=rr_violations,
        net_rr_violation_rate=_safe_rate(rr_violations, len(records)),
    )


__all__ = [
    "BASE_COHORT_SOURCE",
    "HYPOTHESIS_ID",
    "evaluate_h03_symbol",
    "evaluate_h03_universe",
    "reprice_h03_fixed_cohort",
    "day_block_bootstrap_expectancy",
]

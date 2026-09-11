from __future__ import annotations

"""H01-specific offline evaluator.

This module intentionally does not load files, authorize stages, access a network, or
submit anything to an exchange. Signal formation remains the frozen P00 geometry;
only outcome management is replaced by H01's next-bar protection after a +1R touch.
"""

from collections import Counter
from math import isfinite
from statistics import mean, median
from typing import Iterable, Mapping

from dream_account.engines import calculate_costs
from dream_account.models import Candle
from research.phase_b_h01_protect_after_tp1_v01 import simulate_h01_managed_outcome
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


HYPOTHESIS_ID = "H01_PROTECT_AFTER_TP1_NEXT_BAR"
FAMILY_ID = "PBR02_MANAGED_BREAKOUT_RETEST_LONG"
BASE_COHORT_SOURCE = "BASE_SENSITIVITY_SELECTED_H01_TRADES"
LIVE_AUTHORIZED = False
EXCHANGE_MUTATION_AUTHORIZED = False


def _outcome_exit_boundary(record: ResearchTradeRecord, segment: list[Candle]) -> int:
    if record.outcome.exit_open_time is not None:
        return record.outcome.exit_open_time
    return segment[-1].open_time


def _safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _profit_factor(values: list[float]) -> float | None:
    gains = sum(value for value in values if value > 0)
    losses = -sum(value for value in values if value < 0)
    if losses <= 0:
        return None
    return gains / losses


def evaluate_h01_symbol(
    symbol: str,
    candles: Iterable[Candle],
    parameters: ResearchParameters,
    costs: CostAssumptions,
) -> tuple[list[ResearchTradeRecord], dict[str, int]]:
    """Evaluate one symbol with unchanged P00 geometry and frozen H01 management."""

    if not symbol or not isinstance(symbol, str):
        raise ValueError("symbol is required")
    parameters.validate()
    costs.validate()
    segments, gap_count = split_contiguous_segments(candles)
    records: list[ResearchTradeRecord] = []
    raw_geometry_count = 0
    net_rr_rejected_count = 0
    overlap_skipped_count = 0

    for segment in segments:
        signals = derive_signal_geometries(
            segment,
            parameters,
            costs,
            require_regular_spacing=True,
        )
        raw_geometry_count += len(signals)
        ready = [signal for signal in signals if signal.geometry_status == "GEOMETRY_READY"]
        net_rr_rejected_count += sum(
            signal.geometry_status == "REJECTED_NET_RR" for signal in signals
        )
        active_until: int | None = None
        for signal in ready:
            if active_until is not None and signal.entry_open_time <= active_until:
                overlap_skipped_count += 1
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
            active_until = _outcome_exit_boundary(record, segment)

    diagnostics = {
        "raw_geometry_count": raw_geometry_count,
        "net_rr_rejected_count": net_rr_rejected_count,
        "overlap_skipped_count": overlap_skipped_count,
        "contiguous_segment_count": len(segments),
        "detected_gap_count": gap_count,
    }
    return records, diagnostics


def evaluate_h01_universe(
    candles_by_symbol: Mapping[str, Iterable[Candle]],
    parameters: ResearchParameters,
    costs: CostAssumptions,
) -> tuple[list[ResearchTradeRecord], EvaluationMetrics]:
    """Aggregate H01 records without changing signal formation or selecting post-hoc filters."""

    if not candles_by_symbol:
        raise ValueError("candles_by_symbol must not be empty")
    all_records: list[ResearchTradeRecord] = []
    totals = Counter()
    data_open_times: list[int] = []

    for symbol in sorted(candles_by_symbol):
        raw = list(candles_by_symbol[symbol])
        closed = [candle for candle in raw if candle.closed]
        data_open_times.extend(candle.open_time for candle in closed)
        records, diagnostics = evaluate_h01_symbol(symbol, raw, parameters, costs)
        all_records.extend(records)
        totals.update(diagnostics)

    all_records.sort(
        key=lambda record: (
            record.signal.entry_open_time,
            record.symbol,
            record.signal.fingerprint,
        )
    )
    resolved = [record for record in all_records if record.outcome.net_r is not None]
    values = [float(record.outcome.net_r) for record in resolved]
    if any(not isfinite(value) for value in values):
        raise ValueError("non-finite net R encountered")

    selected_count = len(all_records)
    resolved_count = len(resolved)
    unresolved_count = selected_count - resolved_count
    symbol_distribution = dict(sorted(Counter(record.symbol for record in resolved).items()))
    frequency: float | None = None
    if data_open_times and selected_count:
        span_ms = max(data_open_times) - min(data_open_times) + TIMEFRAME_MS
        span_days = span_ms / 86_400_000
        if span_days > 0:
            frequency = selected_count / span_days * 30.0

    outcomes = [record.outcome for record in resolved]
    stop_gap_reasons = {"STOP_GAP", "PROTECTIVE_STOP_GAP"}
    metrics = EvaluationMetrics(
        cost_scenario=costs.name,
        raw_geometry_count=totals["raw_geometry_count"],
        net_rr_rejected_count=totals["net_rr_rejected_count"],
        selected_trade_count=selected_count,
        overlap_skipped_count=totals["overlap_skipped_count"],
        unresolved_trade_count=unresolved_count,
        resolved_trade_count=resolved_count,
        net_expectancy_r=mean(values) if values else None,
        median_net_r=median(values) if values else None,
        win_rate=_safe_rate(sum(value > 0 for value in values), resolved_count),
        loss_rate=_safe_rate(sum(value < 0 for value in values), resolved_count),
        profit_factor_r=_profit_factor(values),
        tp1_reach_rate=_safe_rate(sum(outcome.tp1_reached for outcome in outcomes), resolved_count),
        same_bar_ambiguity_rate=_safe_rate(
            sum(outcome.same_bar_stop_target_ambiguity for outcome in outcomes),
            resolved_count,
        ),
        time_exit_rate=_safe_rate(
            sum(outcome.exit_reason == "TIME_EXIT_NEXT_OPEN" for outcome in outcomes),
            resolved_count,
        ),
        stop_gap_rate=_safe_rate(
            sum(outcome.exit_reason in stop_gap_reasons for outcome in outcomes),
            resolved_count,
        ),
        signal_frequency_per_30d=frequency,
        symbol_distribution=symbol_distribution,
        contiguous_segment_count=totals["contiguous_segment_count"],
        detected_gap_count=totals["detected_gap_count"],
    )
    return all_records, metrics


def reprice_h01_fixed_cohort(
    base_selected_records: Iterable[ResearchTradeRecord],
    alternative_costs: CostAssumptions,
    *,
    min_net_rr: float = 2.0,
) -> FixedCohortCostMetrics:
    """Reprice the unchanged BASE-selected H01 cohort under another cost scenario.

    H01 protection, entry, stop and targets are price-defined and remain fixed. This
    function changes only transaction-cost arithmetic; it never reselects trades or
    recomputes an outcome path under the alternative cost scenario.
    """

    alternative_costs.validate()
    if (
        not isinstance(min_net_rr, (int, float))
        or isinstance(min_net_rr, bool)
        or not isfinite(min_net_rr)
        or min_net_rr <= 0
    ):
        raise ValueError("min_net_rr must be a finite positive number")

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
            raise ValueError("invalid signal risk geometry in fixed cohort")
        net_r = (gross_fraction - cost_fraction) / denominator
        if not isfinite(net_r):
            raise ValueError("non-finite repriced net R encountered")
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
    "EXCHANGE_MUTATION_AUTHORIZED",
    "FAMILY_ID",
    "HYPOTHESIS_ID",
    "LIVE_AUTHORIZED",
    "day_block_bootstrap_expectancy",
    "evaluate_h01_symbol",
    "evaluate_h01_universe",
    "reprice_h01_fixed_cohort",
]

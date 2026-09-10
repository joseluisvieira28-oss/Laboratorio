from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from math import isfinite
from random import Random
from statistics import mean, median
from typing import Iterable, Mapping

from dream_account.engines import calculate_costs
from dream_account.models import Candle
from research.phase_b_signal_formation_v01 import (
    TIMEFRAME_MS,
    CostAssumptions,
    ResearchParameters,
    SignalGeometry,
    TradeOutcome,
    derive_signal_geometries,
    simulate_outcome,
    validate_candles,
)


@dataclass(frozen=True)
class ResearchTradeRecord:
    symbol: str
    signal: SignalGeometry
    outcome: TradeOutcome


@dataclass(frozen=True)
class EvaluationMetrics:
    cost_scenario: str
    raw_geometry_count: int
    net_rr_rejected_count: int
    selected_trade_count: int
    overlap_skipped_count: int
    unresolved_trade_count: int
    resolved_trade_count: int
    net_expectancy_r: float | None
    median_net_r: float | None
    win_rate: float | None
    loss_rate: float | None
    profit_factor_r: float | None
    tp1_reach_rate: float | None
    same_bar_ambiguity_rate: float | None
    time_exit_rate: float | None
    stop_gap_rate: float | None
    signal_frequency_per_30d: float | None
    symbol_distribution: dict[str, int]
    contiguous_segment_count: int
    detected_gap_count: int


@dataclass(frozen=True)
class FixedCohortCostMetrics:
    cost_scenario: str
    cohort_source: str
    selected_trade_count: int
    resolved_trade_count: int
    unresolved_trade_count: int
    net_expectancy_r: float | None
    median_net_r: float | None
    profit_factor_r: float | None
    net_rr_below_minimum_count: int
    net_rr_violation_rate: float | None


@dataclass(frozen=True)
class BootstrapInterval:
    method: str
    repetitions: int
    seed: int
    confidence: float
    sample_days: int
    lower: float | None
    point_estimate: float | None
    upper: float | None
    undefined_reason: str | None


def split_contiguous_segments(candles: Iterable[Candle]) -> tuple[list[list[Candle]], int]:
    """Validate OHLC/timestamp order and split at missing 15m intervals; never interpolate."""

    series = validate_candles(candles, require_regular_spacing=False)
    if not series:
        return [], 0
    segments: list[list[Candle]] = [[series[0]]]
    gaps = 0
    for candle in series[1:]:
        if candle.open_time - segments[-1][-1].open_time == TIMEFRAME_MS:
            segments[-1].append(candle)
        else:
            gaps += 1
            segments.append([candle])
    return segments, gaps


def _outcome_exit_boundary(outcome: TradeOutcome, segment: list[Candle]) -> int:
    if outcome.exit_open_time is not None:
        return outcome.exit_open_time
    return segment[-1].open_time


def evaluate_symbol(
    symbol: str,
    candles: Iterable[Candle],
    parameters: ResearchParameters,
    costs: CostAssumptions,
) -> tuple[list[ResearchTradeRecord], dict[str, int]]:
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
        signals = derive_signal_geometries(segment, parameters, costs, require_regular_spacing=True)
        raw_geometry_count += len(signals)
        ready = [signal for signal in signals if signal.geometry_status == "GEOMETRY_READY"]
        net_rr_rejected_count += sum(signal.geometry_status == "REJECTED_NET_RR" for signal in signals)
        active_until: int | None = None
        for signal in ready:
            if active_until is not None and signal.entry_open_time <= active_until:
                overlap_skipped_count += 1
                continue
            outcome = simulate_outcome(
                signal,
                segment,
                costs,
                max_holding_bars=parameters.max_holding_bars,
                require_regular_spacing=True,
            )
            records.append(ResearchTradeRecord(symbol=symbol, signal=signal, outcome=outcome))
            active_until = _outcome_exit_boundary(outcome, segment)

    diagnostics = {
        "raw_geometry_count": raw_geometry_count,
        "net_rr_rejected_count": net_rr_rejected_count,
        "overlap_skipped_count": overlap_skipped_count,
        "contiguous_segment_count": len(segments),
        "detected_gap_count": gap_count,
    }
    return records, diagnostics


def _safe_rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _profit_factor(values: list[float]) -> float | None:
    gains = sum(value for value in values if value > 0)
    losses = -sum(value for value in values if value < 0)
    if losses <= 0:
        return None
    return gains / losses


def evaluate_universe(
    candles_by_symbol: Mapping[str, Iterable[Candle]],
    parameters: ResearchParameters,
    costs: CostAssumptions,
) -> tuple[list[ResearchTradeRecord], EvaluationMetrics]:
    if not candles_by_symbol:
        raise ValueError("candles_by_symbol must not be empty")
    all_records: list[ResearchTradeRecord] = []
    totals = Counter()
    data_open_times: list[int] = []

    for symbol in sorted(candles_by_symbol):
        raw = list(candles_by_symbol[symbol])
        closed = [c for c in raw if c.closed]
        data_open_times.extend(c.open_time for c in closed)
        records, diagnostics = evaluate_symbol(symbol, raw, parameters, costs)
        all_records.extend(records)
        totals.update(diagnostics)

    all_records.sort(key=lambda record: (record.signal.entry_open_time, record.symbol, record.signal.fingerprint))
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
            sum(outcome.same_bar_stop_target_ambiguity for outcome in outcomes), resolved_count
        ),
        time_exit_rate=_safe_rate(sum(outcome.exit_reason == "TIME_EXIT_NEXT_OPEN" for outcome in outcomes), resolved_count),
        stop_gap_rate=_safe_rate(sum(outcome.exit_reason == "STOP_GAP" for outcome in outcomes), resolved_count),
        signal_frequency_per_30d=frequency,
        symbol_distribution=symbol_distribution,
        contiguous_segment_count=totals["contiguous_segment_count"],
        detected_gap_count=totals["detected_gap_count"],
    )
    return all_records, metrics


def reprice_fixed_cohort(
    base_selected_records: Iterable[ResearchTradeRecord],
    alternative_costs: CostAssumptions,
    *,
    min_net_rr: float = 2.0,
) -> FixedCohortCostMetrics:
    """Reprice the unchanged BASE-selected trade cohort under another cost scenario.

    Signal selection, entry/stop/targets and exit path are intentionally held fixed.
    This prevents a harsher cost assumption from improving results simply by
    selecting a different subset of trades. It does not authorize any live trade.
    """

    alternative_costs.validate()
    if not isinstance(min_net_rr, (int, float)) or isinstance(min_net_rr, bool) or not isfinite(min_net_rr) or min_net_rr <= 0:
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
        cohort_source="BASE_SENSITIVITY_SELECTED_P00_TRADES",
        selected_trade_count=len(records),
        resolved_trade_count=resolved_count,
        unresolved_trade_count=len(records) - resolved_count,
        net_expectancy_r=mean(values) if values else None,
        median_net_r=median(values) if values else None,
        profit_factor_r=_profit_factor(values),
        net_rr_below_minimum_count=rr_violations,
        net_rr_violation_rate=_safe_rate(rr_violations, len(records)),
    )


def _percentile(sorted_values: list[float], probability: float) -> float:
    if not sorted_values:
        raise ValueError("cannot calculate percentile of empty list")
    if probability <= 0:
        return sorted_values[0]
    if probability >= 1:
        return sorted_values[-1]
    position = (len(sorted_values) - 1) * probability
    lower_index = int(position)
    upper_index = min(lower_index + 1, len(sorted_values) - 1)
    fraction = position - lower_index
    return sorted_values[lower_index] * (1 - fraction) + sorted_values[upper_index] * fraction


def day_block_bootstrap_expectancy(
    records: Iterable[ResearchTradeRecord],
    *,
    repetitions: int = 5000,
    seed: int = 230911,
    confidence: float = 0.95,
) -> BootstrapInterval:
    if not isinstance(repetitions, int) or isinstance(repetitions, bool) or repetitions <= 0:
        raise ValueError("repetitions must be a positive integer")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between zero and one")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise ValueError("seed must be an integer")

    grouped: dict[str, list[float]] = defaultdict(list)
    for record in records:
        if record.outcome.net_r is None:
            continue
        day = datetime.fromtimestamp(record.signal.entry_open_time / 1000, tz=timezone.utc).date().isoformat()
        grouped[day].append(float(record.outcome.net_r))

    days = sorted(grouped)
    point_values = [value for day in days for value in grouped[day]]
    if not point_values:
        return BootstrapInterval(
            method="UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP",
            repetitions=repetitions,
            seed=seed,
            confidence=confidence,
            sample_days=0,
            lower=None,
            point_estimate=None,
            upper=None,
            undefined_reason="NO_RESOLVED_TRADES",
        )

    rng = Random(seed)
    draws: list[float] = []
    for _ in range(repetitions):
        sampled_values: list[float] = []
        for _ in range(len(days)):
            sampled_day = days[rng.randrange(len(days))]
            sampled_values.extend(grouped[sampled_day])
        draws.append(mean(sampled_values))

    draws.sort()
    tail = (1.0 - confidence) / 2.0
    return BootstrapInterval(
        method="UTC_CALENDAR_DAY_BLOCK_BOOTSTRAP",
        repetitions=repetitions,
        seed=seed,
        confidence=confidence,
        sample_days=len(days),
        lower=_percentile(draws, tail),
        point_estimate=mean(point_values),
        upper=_percentile(draws, 1.0 - tail),
        undefined_reason=None,
    )


def records_as_dict(records: Iterable[ResearchTradeRecord]) -> list[dict]:
    return [
        {"symbol": record.symbol, "signal": asdict(record.signal), "outcome": asdict(record.outcome)}
        for record in records
    ]

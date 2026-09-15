from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from statistics import mean, median
from typing import Iterable, Mapping

from dream_account.engines import atr, calculate_costs
from dream_account.models import Candle
from research.phase_b_research_evaluator_v01 import BootstrapInterval, EvaluationMetrics, FixedCohortCostMetrics
from research.phase_b_signal_formation_v01 import CostAssumptions, SignalGeometry, TradeOutcome

LAB_ID = "TFG-PBR01-4H-001"
SETUP_ID = "PBR05_TIMEFRAME_TRANSPORT_BREAKOUT_RETEST_LONG_4H"
RESEARCH_TIMEFRAME = "4h"
FIFTEEN_MIN_MS = 15 * 60 * 1000
FOUR_H_MS = 4 * 60 * 60 * 1000
CANDLES_PER_4H = 16
LIVE_AUTHORIZED = False


@dataclass(frozen=True)
class ResearchParameters4H:
    timeframe: str = RESEARCH_TIMEFRAME
    lookback_bars: int = 96
    atr_length: int = 14
    zone_atr_fraction: float = 0.25
    retest_window_bars: int = 2
    stop_atr_fraction: float = 0.25
    tp1_r_multiple: float = 1.0
    tp2_r_multiple: float = 3.0
    min_net_rr: float = 2.0
    max_holding_bars: int = 96
    require_bullish_breakout_body: bool = True

    def validate(self) -> None:
        if self.timeframe != RESEARCH_TIMEFRAME:
            raise ValueError("TFG PBR01 transport is frozen to 4h only")
        integer_fields = {
            "lookback_bars": self.lookback_bars,
            "atr_length": self.atr_length,
            "retest_window_bars": self.retest_window_bars,
            "max_holding_bars": self.max_holding_bars,
        }
        for name, value in integer_fields.items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.lookback_bars < 2 or self.atr_length < 2:
            raise ValueError("lookback and ATR length must be at least 2")
        numeric_fields = {
            "zone_atr_fraction": self.zone_atr_fraction,
            "stop_atr_fraction": self.stop_atr_fraction,
            "tp1_r_multiple": self.tp1_r_multiple,
            "tp2_r_multiple": self.tp2_r_multiple,
            "min_net_rr": self.min_net_rr,
        }
        for name, value in numeric_fields.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.zone_atr_fraction < 0 or self.stop_atr_fraction < 0:
            raise ValueError("ATR fractions must be non-negative")
        if self.tp1_r_multiple <= 0 or self.tp2_r_multiple <= self.tp1_r_multiple:
            raise ValueError("TP2 must be strictly above positive TP1")
        if self.min_net_rr <= 0:
            raise ValueError("min_net_rr must be positive")


@dataclass(frozen=True)
class ResearchTradeRecord4H:
    symbol: str
    signal: SignalGeometry
    outcome: TradeOutcome


@dataclass(frozen=True)
class DiscoveryDecision4H:
    lab_id: str
    stage: str
    classification: str
    resolved_trade_count: int
    minimum_required_trades: int
    base_net_expectancy_r: float | None
    base_profit_factor_r: float | None
    base_bootstrap_lower_95: float | None
    fixed_cohort_stress_net_expectancy_r: float | None
    failed_conditions: tuple[str, ...]
    validation_unlock_eligible: bool
    live_authorized: bool
    submitted_to_exchange: bool
    fingerprint: str


def _canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def validate_4h_candles(candles: Iterable[Candle], *, require_regular_spacing: bool = True) -> list[Candle]:
    series = [c for c in candles if c.closed]
    previous_open: int | None = None
    previous_close: int | None = None
    for candle in series:
        values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
        if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not isfinite(v) for v in values):
            raise ValueError("candle numeric fields must be finite")
        if candle.open <= 0 or candle.high <= 0 or candle.low <= 0 or candle.close <= 0 or candle.volume < 0:
            raise ValueError("invalid OHLCV")
        if candle.high < max(candle.open, candle.close, candle.low) or candle.low > min(candle.open, candle.close, candle.high):
            raise ValueError("OHLC ordering violation")
        if candle.open_time % FOUR_H_MS != 0:
            raise ValueError("4h candle is not UTC-bucket aligned")
        if candle.close_time != candle.open_time + FOUR_H_MS - 1:
            raise ValueError("4h close_time mismatch")
        if previous_open is not None:
            if candle.open_time <= previous_open or candle.close_time <= (previous_close or -1):
                raise ValueError("timestamps must be strictly increasing")
            if require_regular_spacing and candle.open_time - previous_open != FOUR_H_MS:
                raise ValueError("4h candle series contains a gap")
        previous_open = candle.open_time
        previous_close = candle.close_time
    return series


def aggregate_15m_to_4h(candles: Iterable[Candle]) -> list[Candle]:
    closed = sorted((c for c in candles if c.closed), key=lambda c: c.open_time)
    if not closed:
        return []
    seen: set[int] = set()
    buckets: dict[int, list[Candle]] = {}
    for candle in closed:
        if candle.open_time in seen:
            raise ValueError("duplicate 15m open_time")
        seen.add(candle.open_time)
        if candle.open_time % FIFTEEN_MIN_MS != 0:
            raise ValueError("15m candle alignment violation")
        if candle.close_time != candle.open_time + FIFTEEN_MIN_MS - 1:
            raise ValueError("15m close_time mismatch")
        bucket = candle.open_time - (candle.open_time % FOUR_H_MS)
        buckets.setdefault(bucket, []).append(candle)

    output: list[Candle] = []
    for bucket_start in sorted(buckets):
        items = sorted(buckets[bucket_start], key=lambda c: c.open_time)
        expected = [bucket_start + i * FIFTEEN_MIN_MS for i in range(CANDLES_PER_4H)]
        if len(items) != CANDLES_PER_4H or [c.open_time for c in items] != expected:
            continue
        output.append(Candle(
            bucket_start,
            items[0].open,
            max(c.high for c in items),
            min(c.low for c in items),
            items[-1].close,
            sum(c.volume for c in items),
            bucket_start + FOUR_H_MS - 1,
            True,
        ))
    return validate_4h_candles(output, require_regular_spacing=False)


def split_4h_segments(candles: Iterable[Candle]) -> tuple[list[list[Candle]], int]:
    series = validate_4h_candles(candles, require_regular_spacing=False)
    if not series:
        return [], 0
    segments: list[list[Candle]] = [[series[0]]]
    gaps = 0
    for candle in series[1:]:
        if candle.open_time - segments[-1][-1].open_time == FOUR_H_MS:
            segments[-1].append(candle)
        else:
            gaps += 1
            segments.append([candle])
    return segments, gaps


def derive_signal_geometries_4h(candles: Iterable[Candle], parameters: ResearchParameters4H, costs: CostAssumptions) -> list[SignalGeometry]:
    parameters.validate()
    costs.validate()
    series = validate_4h_candles(candles, require_regular_spacing=True)
    minimum_history = max(parameters.lookback_bars, parameters.atr_length + 1)
    if len(series) < minimum_history + parameters.retest_window_bars + 2:
        return []
    output: list[SignalGeometry] = []
    for breakout_index in range(minimum_history, len(series) - 2):
        breakout = series[breakout_index]
        prior = series[:breakout_index]
        resistance = max(c.high for c in prior[-parameters.lookback_bars:])
        atr_value = atr(prior, parameters.atr_length)
        if atr_value <= 0 or not isfinite(atr_value):
            continue
        if breakout.close <= resistance:
            continue
        if parameters.require_bullish_breakout_body and breakout.close < breakout.open:
            continue
        zone_high = resistance
        zone_low = resistance - parameters.zone_atr_fraction * atr_value
        if zone_low <= 0:
            continue
        retest_index: int | None = None
        invalidated = False
        window_end = min(len(series) - 1, breakout_index + parameters.retest_window_bars)
        for index in range(breakout_index + 1, window_end + 1):
            candidate = series[index]
            if candidate.low < zone_low:
                invalidated = True
                break
            if candidate.low <= zone_high:
                if candidate.low >= zone_low and candidate.close >= zone_high:
                    retest_index = index
                else:
                    invalidated = True
                break
        if invalidated or retest_index is None:
            continue
        entry_index = retest_index + 1
        if entry_index >= len(series):
            continue
        retest = series[retest_index]
        entry_candle = series[entry_index]
        entry = entry_candle.open
        if entry < zone_high:
            continue
        stop = zone_low - parameters.stop_atr_fraction * atr_value
        if stop <= 0 or entry <= stop:
            continue
        r_value = entry - stop
        tp1 = entry + parameters.tp1_r_multiple * r_value
        tp2 = entry + parameters.tp2_r_multiple * r_value
        cost_result = calculate_costs(entry=entry, stop=stop, target=tp2, fee_pct_each_side=costs.fee_pct_each_side, spread_pct=costs.spread_pct, slippage_pct_each_side=costs.slippage_pct_each_side, funding_pct=0.0)
        geometry_status = "GEOMETRY_READY" if cost_result.net_rr >= parameters.min_net_rr else "REJECTED_NET_RR"
        payload = {
            "setup_id": SETUP_ID, "timeframe": RESEARCH_TIMEFRAME,
            "breakout_open_time": breakout.open_time, "breakout_close_time": breakout.close_time,
            "retest_open_time": retest.open_time, "retest_close_time": retest.close_time,
            "entry_open_time": entry_candle.open_time, "resistance": resistance,
            "atr_before_breakout": atr_value, "zone_low": zone_low, "zone_high": zone_high,
            "breakout_close": breakout.close, "retest_low": retest.low, "retest_close": retest.close,
            "entry": entry, "stop": stop, "tp1": tp1, "tp2": tp2,
            "stop_distance_pct": (r_value / entry) * 100,
            "gross_rr_tp2": cost_result.gross_rr, "net_rr_tp2": cost_result.net_rr,
            "estimated_round_trip_cost_pct": cost_result.estimated_cost_pct,
            "geometry_status": geometry_status, "full_trade_authorized": LIVE_AUTHORIZED,
            "submitted_to_exchange": False, "full_trade_blockers": ("research_only_no_live_authority",),
        }
        output.append(SignalGeometry(**payload, fingerprint=_canonical_hash(payload)))
    return output


def simulate_outcome_4h(signal: SignalGeometry, candles: Iterable[Candle], costs: CostAssumptions, *, max_holding_bars: int) -> TradeOutcome:
    costs.validate()
    series = validate_4h_candles(candles, require_regular_spacing=True)
    entry_index = next((i for i, c in enumerate(series) if c.open_time == signal.entry_open_time), None)
    if entry_index is None:
        raise ValueError("entry candle missing")
    if abs(series[entry_index].open - signal.entry) > max(1e-12, abs(signal.entry) * 1e-12):
        raise ValueError("entry price mismatch")
    cost_fraction = costs.round_trip_cost_pct / 100
    stop_fraction = (signal.entry - signal.stop) / signal.entry
    denominator = stop_fraction + cost_fraction
    if stop_fraction <= 0 or denominator <= 0:
        raise ValueError("invalid risk geometry")

    def finish(reason: str, candle: Candle, price: float, bars_held: int, tp1_reached: bool, ambiguity: bool) -> TradeOutcome:
        gross_fraction = (price - signal.entry) / signal.entry
        return TradeOutcome(setup_fingerprint=signal.fingerprint, exit_reason=reason, exit_open_time=candle.open_time, exit_price=price, bars_held=bars_held, gross_return_pct=gross_fraction * 100, net_r=(gross_fraction - cost_fraction) / denominator, tp1_reached=tp1_reached, same_bar_stop_target_ambiguity=ambiguity)

    tp1_reached = False
    last_index = min(len(series) - 1, entry_index + max_holding_bars - 1)
    for index in range(entry_index, last_index + 1):
        candle = series[index]
        bars_held = index - entry_index + 1
        if candle.open <= signal.stop:
            return finish("STOP_GAP", candle, candle.open, bars_held, tp1_reached, False)
        if candle.open >= signal.tp2:
            return finish("TP2", candle, signal.tp2, bars_held, True, False)
        if candle.open >= signal.tp1:
            tp1_reached = True
        stop_hit = candle.low <= signal.stop
        target_hit = candle.high >= signal.tp2
        if stop_hit and target_hit:
            return finish("STOP_AMBIGUOUS_SAME_BAR", candle, signal.stop, bars_held, tp1_reached, True)
        if stop_hit:
            return finish("STOP", candle, signal.stop, bars_held, tp1_reached, False)
        if target_hit:
            return finish("TP2", candle, signal.tp2, bars_held, True, False)
        if candle.high >= signal.tp1:
            tp1_reached = True
    time_exit_index = entry_index + max_holding_bars
    if time_exit_index >= len(series):
        return TradeOutcome(setup_fingerprint=signal.fingerprint, exit_reason="UNRESOLVED_END_OF_DATA", exit_open_time=None, exit_price=None, bars_held=None, gross_return_pct=None, net_r=None, tp1_reached=tp1_reached, same_bar_stop_target_ambiguity=False)
    candle = series[time_exit_index]
    return finish("TIME_EXIT_NEXT_OPEN", candle, candle.open, max_holding_bars, tp1_reached, False)


def _safe_rate(n: int, d: int) -> float | None:
    return n / d if d else None


def _profit_factor(values: list[float]) -> float | None:
    gains = sum(v for v in values if v > 0)
    losses = -sum(v for v in values if v < 0)
    return gains / losses if losses > 0 else None


def evaluate_symbol_4h(symbol: str, candles: Iterable[Candle], parameters: ResearchParameters4H, costs: CostAssumptions):
    segments, gap_count = split_4h_segments(candles)
    records: list[ResearchTradeRecord4H] = []
    raw_geometry_count = net_rr_rejected_count = overlap_skipped_count = 0
    for segment in segments:
        signals = derive_signal_geometries_4h(segment, parameters, costs)
        raw_geometry_count += len(signals)
        net_rr_rejected_count += sum(s.geometry_status == "REJECTED_NET_RR" for s in signals)
        active_until: int | None = None
        for signal in (s for s in signals if s.geometry_status == "GEOMETRY_READY"):
            if active_until is not None and signal.entry_open_time <= active_until:
                overlap_skipped_count += 1
                continue
            outcome = simulate_outcome_4h(signal, segment, costs, max_holding_bars=parameters.max_holding_bars)
            records.append(ResearchTradeRecord4H(symbol, signal, outcome))
            active_until = outcome.exit_open_time if outcome.exit_open_time is not None else segment[-1].open_time
    return records, {"raw_geometry_count": raw_geometry_count, "net_rr_rejected_count": net_rr_rejected_count, "overlap_skipped_count": overlap_skipped_count, "contiguous_segment_count": len(segments), "detected_gap_count": gap_count}


def evaluate_universe_4h(candles_by_symbol: Mapping[str, Iterable[Candle]], parameters: ResearchParameters4H, costs: CostAssumptions):
    all_records: list[ResearchTradeRecord4H] = []
    totals = Counter()
    data_open_times: list[int] = []
    for symbol in sorted(candles_by_symbol):
        raw = list(candles_by_symbol[symbol])
        data_open_times.extend(c.open_time for c in raw if c.closed)
        records, diagnostics = evaluate_symbol_4h(symbol, raw, parameters, costs)
        all_records.extend(records)
        totals.update(diagnostics)
    all_records.sort(key=lambda r: (r.signal.entry_open_time, r.symbol, r.signal.fingerprint))
    resolved = [r for r in all_records if r.outcome.net_r is not None]
    values = [float(r.outcome.net_r) for r in resolved]
    selected_count, resolved_count = len(all_records), len(resolved)
    frequency = None
    if data_open_times and selected_count:
        span_days = (max(data_open_times) - min(data_open_times) + FOUR_H_MS) / 86_400_000
        if span_days > 0:
            frequency = selected_count / span_days * 30.0
    outcomes = [r.outcome for r in resolved]
    metrics = EvaluationMetrics(cost_scenario=costs.name, raw_geometry_count=totals["raw_geometry_count"], net_rr_rejected_count=totals["net_rr_rejected_count"], selected_trade_count=selected_count, overlap_skipped_count=totals["overlap_skipped_count"], unresolved_trade_count=selected_count - resolved_count, resolved_trade_count=resolved_count, net_expectancy_r=mean(values) if values else None, median_net_r=median(values) if values else None, win_rate=_safe_rate(sum(v > 0 for v in values), resolved_count), loss_rate=_safe_rate(sum(v < 0 for v in values), resolved_count), profit_factor_r=_profit_factor(values), tp1_reach_rate=_safe_rate(sum(o.tp1_reached for o in outcomes), resolved_count), same_bar_ambiguity_rate=_safe_rate(sum(o.same_bar_stop_target_ambiguity for o in outcomes), resolved_count), time_exit_rate=_safe_rate(sum(o.exit_reason == "TIME_EXIT_NEXT_OPEN" for o in outcomes), resolved_count), stop_gap_rate=_safe_rate(sum(o.exit_reason == "STOP_GAP" for o in outcomes), resolved_count), signal_frequency_per_30d=frequency, symbol_distribution=dict(sorted(Counter(r.symbol for r in resolved).items())), contiguous_segment_count=totals["contiguous_segment_count"], detected_gap_count=totals["detected_gap_count"])
    return all_records, metrics


def reprice_fixed_cohort_4h(records: Iterable[ResearchTradeRecord4H], costs: CostAssumptions, *, min_net_rr: float = 2.0) -> FixedCohortCostMetrics:
    costs.validate()
    rows = list(records)
    values: list[float] = []
    violations = 0
    for record in rows:
        signal = record.signal
        alt_rr = calculate_costs(entry=signal.entry, stop=signal.stop, target=signal.tp2, fee_pct_each_side=costs.fee_pct_each_side, spread_pct=costs.spread_pct, slippage_pct_each_side=costs.slippage_pct_each_side, funding_pct=0.0).net_rr
        if alt_rr < min_net_rr:
            violations += 1
        if record.outcome.gross_return_pct is None:
            continue
        gross_fraction = record.outcome.gross_return_pct / 100
        stop_fraction = (signal.entry - signal.stop) / signal.entry
        cost_fraction = costs.round_trip_cost_pct / 100
        values.append((gross_fraction - cost_fraction) / (stop_fraction + cost_fraction))
    return FixedCohortCostMetrics(cost_scenario=costs.name, cohort_source="BASE_SENSITIVITY_SELECTED_TFG_PBR01_4H_TRADES", selected_trade_count=len(rows), resolved_trade_count=len(values), unresolved_trade_count=len(rows) - len(values), net_expectancy_r=mean(values) if values else None, median_net_r=median(values) if values else None, profit_factor_r=_profit_factor(values), net_rr_below_minimum_count=violations, net_rr_violation_rate=_safe_rate(violations, len(rows)))


def classify_discovery_4h(base: EvaluationMetrics, stress: FixedCohortCostMetrics, bootstrap: BootstrapInterval) -> DiscoveryDecision4H:
    minimum = 100
    resolved = base.resolved_trade_count
    failures: list[str] = []
    if resolved < minimum:
        classification = "INSUFFICIENT_SAMPLE"
        failures.append("resolved_trade_count_below_100")
    else:
        checks = ((base.net_expectancy_r, 0.0, "base_net_expectancy_not_positive"), (base.profit_factor_r, 1.0, "base_profit_factor_not_above_1"), (bootstrap.lower, 0.0, "bootstrap_lower_95_not_positive"), (stress.net_expectancy_r, 0.0, "fixed_cohort_stress_expectancy_not_positive"))
        for value, threshold, reason in checks:
            if value is None or not isfinite(float(value)) or float(value) <= threshold:
                failures.append(reason)
        classification = "NO_EDGE" if failures else "SURVIVES"
    payload = {"lab_id": LAB_ID, "stage": "DISCOVERY", "classification": classification, "resolved_trade_count": resolved, "minimum_required_trades": minimum, "base_net_expectancy_r": base.net_expectancy_r, "base_profit_factor_r": base.profit_factor_r, "base_bootstrap_lower_95": bootstrap.lower, "fixed_cohort_stress_net_expectancy_r": stress.net_expectancy_r, "failed_conditions": tuple(failures), "validation_unlock_eligible": classification == "SURVIVES", "live_authorized": False, "submitted_to_exchange": False}
    return DiscoveryDecision4H(**payload, fingerprint=_canonical_hash(payload))


def records_as_dict_4h(records: Iterable[ResearchTradeRecord4H]) -> list[dict]:
    return [{"symbol": r.symbol, "signal": asdict(r.signal), "outcome": asdict(r.outcome)} for r in records]

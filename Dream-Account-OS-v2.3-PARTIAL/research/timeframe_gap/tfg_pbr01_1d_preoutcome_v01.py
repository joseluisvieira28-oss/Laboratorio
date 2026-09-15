from __future__ import annotations

"""Outcome-blind PBR01 1D preparation engine.

This module aggregates the already-authorized P00 MEXC 15m Discovery corpus
into strict UTC daily bars and may form the frozen PBR01 signal geometry. It
contains no outcome simulator, PnL evaluator, bootstrap, validation unlock,
network code, or exchange action. TFG-PBR01-1D-001 remains activation-blocked.
"""

from dataclasses import dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Iterable

from dream_account.engines import atr, calculate_costs
from dream_account.models import Candle
from research.phase_b_signal_formation_v01 import CostAssumptions, SignalGeometry

LAB_ID = "TFG-PBR01-1D-001"
SETUP_ID = "PBR01_BREAKOUT_RETEST_LONG__TFG_1D"
RESEARCH_TIMEFRAME = "1d"
FIFTEEN_MIN_MS = 15 * 60 * 1000
ONE_DAY_MS = 24 * 60 * 60 * 1000
CANDLES_PER_1D = 96
LIVE_AUTHORIZED = False
OUTCOME_COMPUTATION_AUTHORIZED = False


@dataclass(frozen=True)
class ResearchParameters1D:
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
            raise ValueError("TFG-PBR01-1D-001 is frozen to 1d")
        for name, value in {
            "lookback_bars": self.lookback_bars,
            "atr_length": self.atr_length,
            "retest_window_bars": self.retest_window_bars,
            "max_holding_bars": self.max_holding_bars,
        }.items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.lookback_bars < 2 or self.atr_length < 2:
            raise ValueError("lookback and ATR length must be >= 2")
        for name, value in {
            "zone_atr_fraction": self.zone_atr_fraction,
            "stop_atr_fraction": self.stop_atr_fraction,
            "tp1_r_multiple": self.tp1_r_multiple,
            "tp2_r_multiple": self.tp2_r_multiple,
            "min_net_rr": self.min_net_rr,
        }.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
                raise ValueError(f"{name} must be finite")
        if self.zone_atr_fraction < 0 or self.stop_atr_fraction < 0:
            raise ValueError("ATR fractions must be non-negative")
        if self.tp1_r_multiple <= 0 or self.tp2_r_multiple <= self.tp1_r_multiple:
            raise ValueError("TP2 must be above positive TP1")
        if self.min_net_rr <= 0:
            raise ValueError("min_net_rr must be positive")


def _hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def _validate_ohlcv(candle: Candle) -> None:
    values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not isfinite(v) for v in values):
        raise ValueError("candle numeric fields must be finite")
    if candle.open <= 0 or candle.high <= 0 or candle.low <= 0 or candle.close <= 0 or candle.volume < 0:
        raise ValueError("invalid OHLCV")
    if candle.high < max(candle.open, candle.close, candle.low):
        raise ValueError("OHLC high ordering violation")
    if candle.low > min(candle.open, candle.close, candle.high):
        raise ValueError("OHLC low ordering violation")


def validate_1d_candles(candles: Iterable[Candle], *, require_regular_spacing: bool = True) -> list[Candle]:
    series = [c for c in candles if c.closed]
    previous_open: int | None = None
    previous_close: int | None = None
    for candle in series:
        _validate_ohlcv(candle)
        if candle.open_time % ONE_DAY_MS != 0:
            raise ValueError("1d candle is not UTC midnight aligned")
        if candle.close_time != candle.open_time + ONE_DAY_MS - 1:
            raise ValueError("1d close_time mismatch")
        if previous_open is not None:
            if candle.open_time <= previous_open or candle.close_time <= (previous_close or -1):
                raise ValueError("timestamps must be strictly increasing")
            if require_regular_spacing and candle.open_time - previous_open != ONE_DAY_MS:
                raise ValueError("1d series contains a gap")
        previous_open = candle.open_time
        previous_close = candle.close_time
    return series


def aggregate_15m_to_1d(candles: Iterable[Candle]) -> list[Candle]:
    """Create only complete 96-candle UTC days; incomplete days are dropped."""
    source = sorted((c for c in candles if c.closed), key=lambda c: c.open_time)
    if not source:
        return []
    seen: set[int] = set()
    buckets: dict[int, list[Candle]] = {}
    for candle in source:
        _validate_ohlcv(candle)
        if candle.open_time in seen:
            raise ValueError("duplicate 15m open_time")
        seen.add(candle.open_time)
        if candle.open_time % FIFTEEN_MIN_MS != 0:
            raise ValueError("15m alignment violation")
        if candle.close_time != candle.open_time + FIFTEEN_MIN_MS - 1:
            raise ValueError("15m close_time mismatch")
        bucket_start = candle.open_time - candle.open_time % ONE_DAY_MS
        buckets.setdefault(bucket_start, []).append(candle)

    output: list[Candle] = []
    for bucket_start in sorted(buckets):
        items = sorted(buckets[bucket_start], key=lambda c: c.open_time)
        expected = [bucket_start + i * FIFTEEN_MIN_MS for i in range(CANDLES_PER_1D)]
        if len(items) != CANDLES_PER_1D or [c.open_time for c in items] != expected:
            continue
        output.append(Candle(
            bucket_start,
            items[0].open,
            max(c.high for c in items),
            min(c.low for c in items),
            items[-1].close,
            sum(c.volume for c in items),
            bucket_start + ONE_DAY_MS - 1,
            True,
        ))
    return validate_1d_candles(output, require_regular_spacing=False)


def split_1d_segments(candles: Iterable[Candle]) -> tuple[list[list[Candle]], int]:
    series = validate_1d_candles(candles, require_regular_spacing=False)
    if not series:
        return [], 0
    segments: list[list[Candle]] = [[series[0]]]
    gaps = 0
    for candle in series[1:]:
        if candle.open_time - segments[-1][-1].open_time == ONE_DAY_MS:
            segments[-1].append(candle)
        else:
            gaps += 1
            segments.append([candle])
    return segments, gaps


def derive_signal_geometries_1d(
    candles: Iterable[Candle],
    parameters: ResearchParameters1D,
    costs: CostAssumptions,
) -> list[SignalGeometry]:
    """Form frozen daily PBR01 geometry only. No trade outcome is inspected."""
    parameters.validate()
    costs.validate()
    series = validate_1d_candles(candles, require_regular_spacing=True)
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
        risk = entry - stop
        tp1 = entry + parameters.tp1_r_multiple * risk
        tp2 = entry + parameters.tp2_r_multiple * risk
        cost = calculate_costs(
            entry=entry,
            stop=stop,
            target=tp2,
            fee_pct_each_side=costs.fee_pct_each_side,
            spread_pct=costs.spread_pct,
            slippage_pct_each_side=costs.slippage_pct_each_side,
            funding_pct=0.0,
        )
        status = "GEOMETRY_READY" if cost.net_rr >= parameters.min_net_rr else "REJECTED_NET_RR"
        payload = {
            "setup_id": SETUP_ID,
            "timeframe": RESEARCH_TIMEFRAME,
            "breakout_open_time": breakout.open_time,
            "breakout_close_time": breakout.close_time,
            "retest_open_time": retest.open_time,
            "retest_close_time": retest.close_time,
            "entry_open_time": entry_candle.open_time,
            "resistance": resistance,
            "atr_before_breakout": atr_value,
            "zone_low": zone_low,
            "zone_high": zone_high,
            "breakout_close": breakout.close,
            "retest_low": retest.low,
            "retest_close": retest.close,
            "entry": entry,
            "stop": stop,
            "tp1": tp1,
            "tp2": tp2,
            "stop_distance_pct": risk / entry * 100,
            "gross_rr_tp2": cost.gross_rr,
            "net_rr_tp2": cost.net_rr,
            "estimated_round_trip_cost_pct": cost.estimated_cost_pct,
            "geometry_status": status,
            "full_trade_authorized": False,
            "submitted_to_exchange": False,
            "full_trade_blockers": ("research_only_no_live_authority", "outcome_computation_not_authorized"),
        }
        output.append(SignalGeometry(**payload, fingerprint=_hash(payload)))
    return output


def preoutcome_summary(candles: Iterable[Candle]) -> dict:
    """Safe structural audit only: daily bar/segment counts, never performance."""
    series = validate_1d_candles(candles, require_regular_spacing=False)
    segments, gaps = split_1d_segments(series)
    return {
        "lab_id": LAB_ID,
        "timeframe": RESEARCH_TIMEFRAME,
        "closed_1d_candle_count": len(series),
        "contiguous_segment_count": len(segments),
        "detected_1d_gap_count": gaps,
        "first_open_time": series[0].open_time if series else None,
        "last_open_time": series[-1].open_time if series else None,
        "outcome_computation_authorized": False,
        "live_authorized": False,
        "submitted_to_exchange": False,
    }

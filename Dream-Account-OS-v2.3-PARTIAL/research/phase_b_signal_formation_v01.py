from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import isfinite
from typing import Iterable

from dream_account.engines import atr, calculate_costs
from dream_account.models import Candle


SETUP_ID = "PBR01_BREAKOUT_RETEST_LONG"
RESEARCH_TIMEFRAME = "15m"
TIMEFRAME_MS = 15 * 60 * 1000
LIVE_AUTHORIZED = False
CATALYST_RESEARCH_RULE = "NOT_REQUIRED_FOR_RESEARCH_ONLY"
FULL_TRADE_BLOCKERS = (
    "phase_b_live_authority_absent",
    "live_regime_validation_not_supplied_by_research_harness",
    "live_liquidity_validation_not_supplied_by_research_harness",
    "live_catalyst_policy_not_frozen",
    "exchange_precision_and_minimums_not_supplied_by_research_harness",
    "live_risk_state_and_allocation_not_supplied_by_research_harness",
)


@dataclass(frozen=True)
class ResearchParameters:
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
            raise ValueError("Phase B V0.1 research is frozen to 15m only")
        integer_fields = {
            "lookback_bars": self.lookback_bars,
            "atr_length": self.atr_length,
            "retest_window_bars": self.retest_window_bars,
            "max_holding_bars": self.max_holding_bars,
        }
        for name, value in integer_fields.items():
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.lookback_bars < 2:
            raise ValueError("lookback_bars must be at least 2")
        if self.atr_length < 2:
            raise ValueError("atr_length must be at least 2")
        numeric_fields = {
            "zone_atr_fraction": self.zone_atr_fraction,
            "stop_atr_fraction": self.stop_atr_fraction,
            "tp1_r_multiple": self.tp1_r_multiple,
            "tp2_r_multiple": self.tp2_r_multiple,
            "min_net_rr": self.min_net_rr,
        }
        for name, value in numeric_fields.items():
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value):
                raise ValueError(f"{name} must be a finite number")
        if self.zone_atr_fraction < 0 or self.stop_atr_fraction < 0:
            raise ValueError("ATR fractions must be non-negative")
        if self.tp1_r_multiple <= 0 or self.tp2_r_multiple <= self.tp1_r_multiple:
            raise ValueError("TP2 must be strictly above positive TP1")
        if self.min_net_rr <= 0:
            raise ValueError("min_net_rr must be positive")


@dataclass(frozen=True)
class CostAssumptions:
    name: str
    fee_pct_each_side: float
    spread_pct: float
    slippage_pct_each_side: float

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("cost scenario name is required")
        for name, value in (
            ("fee_pct_each_side", self.fee_pct_each_side),
            ("spread_pct", self.spread_pct),
            ("slippage_pct_each_side", self.slippage_pct_each_side),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative percentage")

    @property
    def round_trip_cost_pct(self) -> float:
        self.validate()
        return 2 * self.fee_pct_each_side + self.spread_pct + 2 * self.slippage_pct_each_side


@dataclass(frozen=True)
class SignalGeometry:
    setup_id: str
    timeframe: str
    breakout_open_time: int
    breakout_close_time: int
    retest_open_time: int
    retest_close_time: int
    entry_open_time: int
    resistance: float
    atr_before_breakout: float
    zone_low: float
    zone_high: float
    breakout_close: float
    retest_low: float
    retest_close: float
    entry: float
    stop: float
    tp1: float
    tp2: float
    stop_distance_pct: float
    gross_rr_tp2: float
    net_rr_tp2: float
    estimated_round_trip_cost_pct: float
    geometry_status: str
    full_trade_authorized: bool
    submitted_to_exchange: bool
    full_trade_blockers: tuple[str, ...]
    fingerprint: str


@dataclass(frozen=True)
class TradeOutcome:
    setup_fingerprint: str
    exit_reason: str
    exit_open_time: int | None
    exit_price: float | None
    bars_held: int | None
    gross_return_pct: float | None
    net_r: float | None
    tp1_reached: bool
    same_bar_stop_target_ambiguity: bool
    submitted_to_exchange: bool = False


def _canonical_hash(payload: dict) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha256(encoded).hexdigest()


def validate_candles(candles: Iterable[Candle], *, require_regular_spacing: bool = True) -> list[Candle]:
    closed = [c for c in candles if c.closed]
    if not closed:
        return []
    previous_open_time: int | None = None
    previous_close_time: int | None = None
    for candle in closed:
        values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
        if any(not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) for value in values):
            raise ValueError("candle numeric fields must be finite")
        if candle.open <= 0 or candle.high <= 0 or candle.low <= 0 or candle.close <= 0 or candle.volume < 0:
            raise ValueError("candle prices must be positive and volume non-negative")
        if candle.high < max(candle.open, candle.close, candle.low):
            raise ValueError("candle high violates OHLC ordering")
        if candle.low > min(candle.open, candle.close, candle.high):
            raise ValueError("candle low violates OHLC ordering")
        if not isinstance(candle.open_time, int) or isinstance(candle.open_time, bool):
            raise ValueError("open_time must be an integer timestamp")
        if not isinstance(candle.close_time, int) or isinstance(candle.close_time, bool):
            raise ValueError("close_time must be an integer timestamp")
        if candle.close_time <= candle.open_time:
            raise ValueError("close_time must be after open_time")
        if previous_open_time is not None:
            if candle.open_time <= previous_open_time or candle.close_time <= (previous_close_time or -1):
                raise ValueError("candle timestamps must be strictly increasing")
            if require_regular_spacing and candle.open_time - previous_open_time != TIMEFRAME_MS:
                raise ValueError("15m candle series contains a gap or duplicate interval")
        previous_open_time = candle.open_time
        previous_close_time = candle.close_time
    return closed


def _signal_fingerprint(payload: dict) -> str:
    safe = dict(payload)
    safe.pop("fingerprint", None)
    return _canonical_hash(safe)


def derive_signal_geometries(
    candles: Iterable[Candle],
    parameters: ResearchParameters,
    costs: CostAssumptions,
    *,
    require_regular_spacing: bool = True,
) -> list[SignalGeometry]:
    """Derive prospective LONG breakout/retest geometry from closed candles only.

    This is an offline research function. It has no market-data client, exchange client,
    order route, risk allocator, or live authorization path.
    """

    parameters.validate()
    costs.validate()
    series = validate_candles(candles, require_regular_spacing=require_regular_spacing)
    minimum_history = max(parameters.lookback_bars, parameters.atr_length + 1)
    if len(series) < minimum_history + parameters.retest_window_bars + 2:
        return []

    output: list[SignalGeometry] = []
    for breakout_index in range(minimum_history, len(series) - 2):
        breakout = series[breakout_index]
        prior = series[:breakout_index]
        level_window = prior[-parameters.lookback_bars :]
        resistance = max(c.high for c in level_window)

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
                # The first touch is decisive. A close below the reclaimed level is a failed retest.
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

        # A reclaimed level that is lost before the next-bar entry cancels the setup.
        if entry < zone_high:
            continue

        stop = zone_low - parameters.stop_atr_fraction * atr_value
        if stop <= 0 or entry <= stop:
            continue
        r_value = entry - stop
        tp1 = entry + parameters.tp1_r_multiple * r_value
        tp2 = entry + parameters.tp2_r_multiple * r_value
        cost_result = calculate_costs(
            entry=entry,
            stop=stop,
            target=tp2,
            fee_pct_each_side=costs.fee_pct_each_side,
            spread_pct=costs.spread_pct,
            slippage_pct_each_side=costs.slippage_pct_each_side,
            funding_pct=0.0,
        )
        geometry_status = "GEOMETRY_READY" if cost_result.net_rr >= parameters.min_net_rr else "REJECTED_NET_RR"
        payload = {
            "setup_id": SETUP_ID,
            "timeframe": parameters.timeframe,
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
            "stop_distance_pct": (r_value / entry) * 100,
            "gross_rr_tp2": cost_result.gross_rr,
            "net_rr_tp2": cost_result.net_rr,
            "estimated_round_trip_cost_pct": cost_result.estimated_cost_pct,
            "geometry_status": geometry_status,
            "full_trade_authorized": LIVE_AUTHORIZED,
            "submitted_to_exchange": False,
            "full_trade_blockers": FULL_TRADE_BLOCKERS,
        }
        fingerprint = _signal_fingerprint(payload)
        output.append(SignalGeometry(**payload, fingerprint=fingerprint))
    return output


def simulate_outcome(
    signal: SignalGeometry,
    candles: Iterable[Candle],
    costs: CostAssumptions,
    *,
    max_holding_bars: int,
    require_regular_spacing: bool = True,
) -> TradeOutcome:
    """Conservative OHLC research outcome; never submits or simulates an exchange order.

    Intrabar path is unknowable from OHLC. If stop and TP2 are both touched in the
    same candle, STOP wins. TP1 is informational only; no partial exit is assumed.
    A gap through the stop exits at the adverse opening price. A favorable gap above
    TP2 is capped at TP2. If the time exit needs a next-bar open that is unavailable,
    the result is explicit UNRESOLVED_END_OF_DATA.
    """

    costs.validate()
    if not isinstance(max_holding_bars, int) or isinstance(max_holding_bars, bool) or max_holding_bars <= 0:
        raise ValueError("max_holding_bars must be a positive integer")
    series = validate_candles(candles, require_regular_spacing=require_regular_spacing)
    entry_index = next((i for i, candle in enumerate(series) if candle.open_time == signal.entry_open_time), None)
    if entry_index is None:
        raise ValueError("entry candle is missing from series")
    if abs(series[entry_index].open - signal.entry) > max(1e-12, abs(signal.entry) * 1e-12):
        raise ValueError("entry price does not match entry candle open")

    cost_fraction = costs.round_trip_cost_pct / 100
    stop_fraction = (signal.entry - signal.stop) / signal.entry
    total_risk_fraction = stop_fraction + cost_fraction
    if stop_fraction <= 0 or total_risk_fraction <= 0:
        raise ValueError("signal has invalid risk geometry")

    def finish(
        reason: str,
        open_time: int,
        price: float,
        bars_held: int,
        tp1_reached: bool,
        ambiguity: bool,
    ) -> TradeOutcome:
        gross_fraction = (price - signal.entry) / signal.entry
        net_r = (gross_fraction - cost_fraction) / total_risk_fraction
        return TradeOutcome(
            setup_fingerprint=signal.fingerprint,
            exit_reason=reason,
            exit_open_time=open_time,
            exit_price=price,
            bars_held=bars_held,
            gross_return_pct=gross_fraction * 100,
            net_r=net_r,
            tp1_reached=tp1_reached,
            same_bar_stop_target_ambiguity=ambiguity,
        )

    tp1_reached = False
    last_index = min(len(series) - 1, entry_index + max_holding_bars - 1)
    for index in range(entry_index, last_index + 1):
        candle = series[index]
        bars_held = index - entry_index + 1

        if candle.open <= signal.stop:
            return finish("STOP_GAP", candle.open_time, candle.open, bars_held, tp1_reached, False)
        if candle.open >= signal.tp2:
            return finish("TP2", candle.open_time, signal.tp2, bars_held, True, False)
        if candle.open >= signal.tp1:
            tp1_reached = True

        stop_hit = candle.low <= signal.stop
        target_hit = candle.high >= signal.tp2
        if stop_hit and target_hit:
            return finish("STOP_AMBIGUOUS_SAME_BAR", candle.open_time, signal.stop, bars_held, tp1_reached, True)
        if stop_hit:
            return finish("STOP", candle.open_time, signal.stop, bars_held, tp1_reached, False)
        if target_hit:
            return finish("TP2", candle.open_time, signal.tp2, bars_held, True, False)
        if candle.high >= signal.tp1:
            tp1_reached = True

    time_exit_index = entry_index + max_holding_bars
    if time_exit_index >= len(series):
        return TradeOutcome(
            setup_fingerprint=signal.fingerprint,
            exit_reason="UNRESOLVED_END_OF_DATA",
            exit_open_time=None,
            exit_price=None,
            bars_held=None,
            gross_return_pct=None,
            net_r=None,
            tp1_reached=tp1_reached,
            same_bar_stop_target_ambiguity=False,
        )
    time_exit = series[time_exit_index]
    return finish("TIME_EXIT_NEXT_OPEN", time_exit.open_time, time_exit.open, max_holding_bars, tp1_reached, False)


def geometry_as_dict(signal: SignalGeometry) -> dict:
    return asdict(signal)

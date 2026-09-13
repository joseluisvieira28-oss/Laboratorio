"""Offline/synthetic-only non-directional measurement core for Macro Shock State Lab V0.1."""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, isfinite, log, sqrt
from statistics import median
from typing import Iterable, Sequence

from microstructure_state_schema_v01 import BBOObservation, SchemaViolation, TradeObservation

SECOND_NS = 1_000_000_000
MINUTE_NS = 60 * SECOND_NS
MAX_SKEW_NS = 2 * SECOND_NS
H02_STATUS = "NOT_AUTHORIZED"
TARGET_OBSERVATION_AUTHORIZED = False


@dataclass(frozen=True)
class WindowSpec:
    name: str
    start_offset_ns: int
    end_offset_ns: int


PRE_BASELINE = WindowSpec("PRE_BASELINE", -30 * MINUTE_NS, 0)
PRIMARY_EVENT_STATE = WindowSpec("PRIMARY_EVENT_STATE", 0, 30 * MINUTE_NS)
RECOVERY_STATE = WindowSpec("RECOVERY_STATE", 30 * MINUTE_NS, 60 * MINUTE_NS)
WINDOWS = (PRE_BASELINE, PRIMARY_EVENT_STATE, RECOVERY_STATE)


@dataclass(frozen=True)
class BBOSummary:
    count: int
    median_spread_bps: float | None
    p90_spread_bps: float | None
    median_bid_qty: float | None
    median_ask_qty: float | None
    median_abs_top_imbalance: float | None
    realized_volatility: float | None


@dataclass(frozen=True)
class TradeSummary:
    trade_count: int
    base_quantity: float
    quote_notional: float
    trades_per_minute: float
    notional_per_minute: float
    absolute_normalized_signed_flow: float | None


def classify_event_relative_window(relative_ns: int) -> str | None:
    for window in WINDOWS:
        if window.start_offset_ns <= relative_ns < window.end_offset_ns:
            return window.name
    return None


def _ceil_to_second(ns: int) -> int:
    return ((int(ns) + SECOND_NS - 1) // SECOND_NS) * SECOND_NS


def canonical_grid(start_ns: int, end_ns: int) -> tuple[int, ...]:
    if end_ns <= start_ns:
        raise SchemaViolation("end_ns must be greater than start_ns")
    first = _ceil_to_second(start_ns)
    if first >= end_ns:
        return ()
    return tuple(range(first, int(end_ns), SECOND_NS))


def resample_bbo_backward_asof(
    records: Sequence[BBOObservation],
    *,
    start_ns: int,
    end_ns: int,
    max_skew_ns: int = MAX_SKEW_NS,
) -> tuple[BBOObservation | None, ...]:
    if max_skew_ns != MAX_SKEW_NS:
        raise SchemaViolation("V0.1 max_skew_ns is frozen at 2 seconds")
    valid: list[BBOObservation] = []
    for record in records:
        record.validate()
        if record.clock.exchange_ts_ns is not None:
            valid.append(record)
    valid.sort(key=lambda x: (int(x.clock.exchange_ts_ns), int(x.clock.source_order)))
    grid = canonical_grid(start_ns, end_ns)
    out: list[BBOObservation | None] = []
    idx = 0
    latest: BBOObservation | None = None
    for t in grid:
        while idx < len(valid) and int(valid[idx].clock.exchange_ts_ns) <= t:
            latest = valid[idx]
            idx += 1
        if latest is None:
            out.append(None)
            continue
        skew = t - int(latest.clock.exchange_ts_ns)
        out.append(latest if 0 <= skew <= MAX_SKEW_NS else None)
    return tuple(out)


def nearest_rank_p90(values: Sequence[float]) -> float | None:
    clean = sorted(float(v) for v in values if isfinite(float(v)))
    if not clean:
        return None
    rank = ceil(0.90 * len(clean))
    return clean[rank - 1]


def _abs_imbalance(obs: BBOObservation) -> float:
    denom = float(obs.best_bid_quantity) + float(obs.best_ask_quantity)
    if denom <= 0:
        raise SchemaViolation("top-of-book quantity denominator must be positive")
    return abs((float(obs.best_bid_quantity) - float(obs.best_ask_quantity)) / denom)


def realized_volatility_from_grid(samples: Sequence[BBOObservation | None]) -> float | None:
    squared: list[float] = []
    prior: BBOObservation | None = None
    for sample in samples:
        if sample is None:
            prior = None
            continue
        sample.validate()
        if prior is not None:
            r = log(sample.mid / prior.mid)
            squared.append(r * r)
        prior = sample
    if not squared:
        return None
    return sqrt(sum(squared))


def summarize_bbo_grid(samples: Sequence[BBOObservation | None]) -> BBOSummary:
    valid = [x for x in samples if x is not None]
    for obs in valid:
        obs.validate()
    if not valid:
        return BBOSummary(0, None, None, None, None, None, None)
    spreads = [obs.spread_bps for obs in valid]
    bids = [float(obs.best_bid_quantity) for obs in valid]
    asks = [float(obs.best_ask_quantity) for obs in valid]
    imbalances = [_abs_imbalance(obs) for obs in valid]
    return BBOSummary(
        count=len(valid),
        median_spread_bps=float(median(spreads)),
        p90_spread_bps=nearest_rank_p90(spreads),
        median_bid_qty=float(median(bids)),
        median_ask_qty=float(median(asks)),
        median_abs_top_imbalance=float(median(imbalances)),
        realized_volatility=realized_volatility_from_grid(samples),
    )


def summarize_trades(trades: Iterable[TradeObservation], *, window_minutes: float) -> TradeSummary:
    if not isfinite(window_minutes) or window_minutes <= 0:
        raise SchemaViolation("window_minutes must be finite and > 0")
    rows = list(trades)
    buy = 0.0
    sell = 0.0
    base = 0.0
    quote = 0.0
    side_complete = True
    for trade in rows:
        trade.validate()
        q = float(trade.quantity)
        n = float(trade.price) * q
        base += q
        quote += n
        if trade.aggressor_side == "BUY":
            buy += n
        elif trade.aggressor_side == "SELL":
            sell += n
        else:
            side_complete = False
    flow = None
    if side_complete and quote > 0:
        flow = abs(buy - sell) / (buy + sell)
    return TradeSummary(
        trade_count=len(rows),
        base_quantity=base,
        quote_notional=quote,
        trades_per_minute=len(rows) / window_minutes,
        notional_per_minute=quote / window_minutes,
        absolute_normalized_signed_flow=flow,
    )


def median_control_reference(values: Sequence[float | None]) -> float | None:
    clean = [float(v) for v in values if v is not None and isfinite(float(v))]
    if len(clean) < 3:
        return None
    return float(median(clean))


def event_control_comparison(event_value: float | None, control_values: Sequence[float | None]) -> dict[str, float | None]:
    control = median_control_reference(control_values)
    if event_value is None or control is None or not isfinite(float(event_value)):
        return {"event": event_value, "control_median": control, "difference": None, "ratio": None}
    event = float(event_value)
    ratio = event / control if control > 0 else None
    return {
        "event": event,
        "control_median": control,
        "difference": event - control,
        "ratio": ratio,
    }

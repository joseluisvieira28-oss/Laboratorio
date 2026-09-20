from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional, Sequence, Tuple

TOL_BPS = 10.0
TOL_FRAC = TOL_BPS / 10000.0
PIVOT_RADIUS = 3
MIN_ANCHOR_SEP_H = 12
MAX_ANCHOR_SEP_H = 168
LINE_LIFE_H = 336
PRIMARY_H = 6
DIAGNOSTIC_HORIZONS = (1, 3, 12, 24)
WARMUP_END_TS_MS = 1610668800000  # 2021-01-15T00:00:00Z


@dataclass(frozen=True)
class Bar:
    ts_ms: int
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


@dataclass
class Pivot:
    idx: int
    price: float
    confirm_idx: int


@dataclass
class LineState:
    side: str
    p1_idx: int
    p2_idx: int
    p1_price: float
    p2_price: float
    confirm_idx: int
    expiry_idx: int

    def price_at(self, idx: int) -> float:
        denom = self.p2_idx - self.p1_idx
        if denom <= 0:
            raise ValueError("non-positive anchor separation")
        slope = (self.p2_price - self.p1_price) / denom
        return self.p1_price + slope * (idx - self.p1_idx)


@dataclass(frozen=True)
class Event:
    side: str
    direction: int
    idx: int
    ts_ms: int
    event_close: float
    line_price: float
    p1_idx: int
    p2_idx: int
    p1_price: float
    p2_price: float


def _strict_pivot_low(bars: Sequence[Bar], p: int) -> bool:
    x = bars[p].low
    for j in range(p - PIVOT_RADIUS, p + PIVOT_RADIUS + 1):
        if j == p:
            continue
        if not (x < bars[j].low):
            return False
    return True


def _strict_pivot_high(bars: Sequence[Bar], p: int) -> bool:
    x = bars[p].high
    for j in range(p - PIVOT_RADIUS, p + PIVOT_RADIUS + 1):
        if j == p:
            continue
        if not (x > bars[j].high):
            return False
    return True


def _band(line_price: float) -> Tuple[float, float]:
    return line_price * (1.0 - TOL_FRAC), line_price * (1.0 + TOL_FRAC)


def discover_events_in_segment(bars: Sequence[Bar]) -> Tuple[List[Event], Dict[str, int]]:
    events: List[Event] = []
    stats: Dict[str, int] = {
        "pivot_lows_confirmed": 0,
        "pivot_highs_confirmed": 0,
        "support_lines_created": 0,
        "resistance_lines_created": 0,
        "support_invalidated": 0,
        "resistance_invalidated": 0,
        "lines_expired": 0,
        "lines_replaced": 0,
        "suppressed_overlap": 0,
        "ambiguous_both_sides": 0,
        "accepted_events": 0,
    }
    if len(bars) < 2 * PIVOT_RADIUS + 2:
        return events, stats

    last_low: Optional[Pivot] = None
    last_high: Optional[Pivot] = None
    support: Optional[LineState] = None
    resistance: Optional[LineState] = None
    cooldown_until_idx = -1

    for t in range(len(bars)):
        if support is not None and t > support.expiry_idx:
            support = None
            stats["lines_expired"] += 1
        if resistance is not None and t > resistance.expiry_idx:
            resistance = None
            stats["lines_expired"] += 1

        support_candidate = False
        resistance_candidate = False
        support_lp = None
        resistance_lp = None

        if t >= 1 and support is not None and t > support.confirm_idx:
            support_lp = support.price_at(t)
            cur_lo, cur_hi = _band(support_lp)
            prev_lp = support.price_at(t - 1)
            _, prev_hi = _band(prev_lp)
            support_candidate = (
                bars[t - 1].close > prev_hi
                and bars[t].high >= cur_lo
                and bars[t].low <= cur_hi
            )

        if t >= 1 and resistance is not None and t > resistance.confirm_idx:
            resistance_lp = resistance.price_at(t)
            cur_lo, cur_hi = _band(resistance_lp)
            prev_lp = resistance.price_at(t - 1)
            prev_lo, _ = _band(prev_lp)
            resistance_candidate = (
                bars[t - 1].close < prev_lo
                and bars[t].high >= cur_lo
                and bars[t].low <= cur_hi
            )

        if support_candidate and resistance_candidate:
            stats["ambiguous_both_sides"] += 1
            support = None
            resistance = None
        elif support_candidate:
            line = support
            support = None
            if t <= cooldown_until_idx:
                stats["suppressed_overlap"] += 1
            elif bars[t].ts_ms >= WARMUP_END_TS_MS:
                assert line is not None and support_lp is not None
                events.append(
                    Event(
                        side="support",
                        direction=1,
                        idx=t,
                        ts_ms=bars[t].ts_ms,
                        event_close=bars[t].close,
                        line_price=support_lp,
                        p1_idx=line.p1_idx,
                        p2_idx=line.p2_idx,
                        p1_price=line.p1_price,
                        p2_price=line.p2_price,
                    )
                )
                stats["accepted_events"] += 1
                cooldown_until_idx = t + PRIMARY_H
        elif resistance_candidate:
            line = resistance
            resistance = None
            if t <= cooldown_until_idx:
                stats["suppressed_overlap"] += 1
            elif bars[t].ts_ms >= WARMUP_END_TS_MS:
                assert line is not None and resistance_lp is not None
                events.append(
                    Event(
                        side="resistance",
                        direction=-1,
                        idx=t,
                        ts_ms=bars[t].ts_ms,
                        event_close=bars[t].close,
                        line_price=resistance_lp,
                        p1_idx=line.p1_idx,
                        p2_idx=line.p2_idx,
                        p1_price=line.p1_price,
                        p2_price=line.p2_price,
                    )
                )
                stats["accepted_events"] += 1
                cooldown_until_idx = t + PRIMARY_H

        if support is not None and t > support.confirm_idx:
            lp = support.price_at(t)
            lo, _ = _band(lp)
            if bars[t].close < lo:
                support = None
                stats["support_invalidated"] += 1

        if resistance is not None and t > resistance.confirm_idx:
            lp = resistance.price_at(t)
            _, hi = _band(lp)
            if bars[t].close > hi:
                resistance = None
                stats["resistance_invalidated"] += 1

        p = t - PIVOT_RADIUS
        if p >= PIVOT_RADIUS:
            if _strict_pivot_low(bars, p):
                stats["pivot_lows_confirmed"] += 1
                cur = Pivot(idx=p, price=bars[p].low, confirm_idx=t)
                if last_low is not None:
                    sep = cur.idx - last_low.idx
                    if MIN_ANCHOR_SEP_H <= sep <= MAX_ANCHOR_SEP_H and cur.price > last_low.price:
                        if support is not None:
                            stats["lines_replaced"] += 1
                        support = LineState(
                            side="support",
                            p1_idx=last_low.idx,
                            p2_idx=cur.idx,
                            p1_price=last_low.price,
                            p2_price=cur.price,
                            confirm_idx=t,
                            expiry_idx=t + LINE_LIFE_H,
                        )
                        stats["support_lines_created"] += 1
                last_low = cur

            if _strict_pivot_high(bars, p):
                stats["pivot_highs_confirmed"] += 1
                cur = Pivot(idx=p, price=bars[p].high, confirm_idx=t)
                if last_high is not None:
                    sep = cur.idx - last_high.idx
                    if MIN_ANCHOR_SEP_H <= sep <= MAX_ANCHOR_SEP_H and cur.price < last_high.price:
                        if resistance is not None:
                            stats["lines_replaced"] += 1
                        resistance = LineState(
                            side="resistance",
                            p1_idx=last_high.idx,
                            p2_idx=cur.idx,
                            p1_price=last_high.price,
                            p2_price=cur.price,
                            confirm_idx=t,
                            expiry_idx=t + LINE_LIFE_H,
                        )
                        stats["resistance_lines_created"] += 1
                last_high = cur

    return events, stats


def evaluate_event_responses(
    bars: Sequence[Bar], events: Sequence[Event], horizons: Sequence[int] = (1, 3, 6, 12, 24)
) -> List[Dict[str, object]]:
    out: List[Dict[str, object]] = []
    for e in events:
        row: Dict[str, object] = {
            "side": e.side,
            "direction": e.direction,
            "idx": e.idx,
            "ts_ms": e.ts_ms,
            "event_close": e.event_close,
            "line_price": e.line_price,
            "p1_idx": e.p1_idx,
            "p2_idx": e.p2_idx,
            "p1_price": e.p1_price,
            "p2_price": e.p2_price,
        }
        for h in horizons:
            key = f"response_{h}h_bps"
            if e.idx + h < len(bars):
                future_close = bars[e.idx + h].close
                row[key] = e.direction * 10000.0 * (future_close / e.event_close - 1.0)
            else:
                row[key] = None
        out.append(row)
    return out


def utc_year_month(ts_ms: int) -> Tuple[int, int]:
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    return dt.year, dt.month


def utc_iso_week(ts_ms: int) -> Tuple[int, int]:
    dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
    iso = dt.isocalendar()
    return int(iso.year), int(iso.week)

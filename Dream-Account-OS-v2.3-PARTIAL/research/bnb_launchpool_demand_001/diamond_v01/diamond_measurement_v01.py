#!/usr/bin/env python3
"""Deterministic, offline-only causal measurements for BNB Launchpool Diamond V0.2.

No network access. No orders. No authentication. No strategy selection.
Inputs must already be public/read-only 1m kline records normalized as dicts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Bar:
    open_time: datetime
    open: float
    close: float
    quote_volume: float


def _utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        raise ValueError("timezone-aware UTC datetime required")
    return dt.astimezone(timezone.utc)


def first_complete_minute_strictly_after(signal_time: datetime) -> datetime:
    t = _utc(signal_time)
    floored = t.replace(second=0, microsecond=0)
    return floored + timedelta(minutes=1)


def _index(bars: Sequence[Bar]) -> dict[datetime, Bar]:
    out = {}
    for b in bars:
        t = _utc(b.open_time)
        if t in out:
            raise ValueError(f"duplicate bar {t.isoformat()}")
        out[t] = b
    return out


def exact_window(bars: Sequence[Bar], start: datetime, minutes: int) -> list[Bar]:
    idx = _index(bars)
    start = _utc(start)
    expected = [start + timedelta(minutes=i) for i in range(minutes)]
    missing = [t for t in expected if t not in idx]
    if missing:
        raise ValueError(f"incomplete window: {len(missing)} missing bars")
    return [idx[t] for t in expected]


def simple_return(window: Sequence[Bar]) -> float:
    if not window or window[0].open <= 0:
        raise ValueError("invalid return window")
    return window[-1].close / window[0].open - 1.0


def quote_volume(window: Sequence[Bar]) -> float:
    if any(b.quote_volume < 0 for b in window):
        raise ValueError("negative quote volume")
    return sum(b.quote_volume for b in window)


def prior_same_clock_volume_baseline(
    bars: Sequence[Bar],
    event_start: datetime,
    *,
    valid_days: int = 20,
    max_lookback_days: int = 40,
) -> tuple[float, list[str]]:
    if valid_days != 20 or max_lookback_days != 40:
        raise ValueError("Diamond V0.2 baseline constants are frozen at 20/40")
    event_start = _utc(event_start)
    vals: list[float] = []
    dates: list[str] = []
    for d in range(1, max_lookback_days + 1):
        candidate = event_start - timedelta(days=d)
        try:
            w = exact_window(bars, candidate, 60)
        except ValueError:
            continue
        vals.append(quote_volume(w))
        dates.append(candidate.date().isoformat())
        if len(vals) == valid_days:
            break
    if len(vals) != valid_days:
        raise ValueError("MECHANISM_DATA_BLOCKED: fewer than 20 complete prior same-clock days")
    return float(median(vals)), dates


def measure_event(
    signal_time: datetime,
    bnbbtc_1m: Sequence[Bar],
    bnbusdt_1m: Sequence[Bar],
    btcusdt_1m: Sequence[Bar],
) -> dict:
    start = first_complete_minute_strictly_after(signal_time)
    out = {"signal_time_utc": _utc(signal_time).isoformat(), "aligned_start_utc": start.isoformat()}
    for symbol, bars in (("BNBBTC", bnbbtc_1m), ("BNBUSDT", bnbusdt_1m), ("BTCUSDT", btcusdt_1m)):
        w15 = exact_window(bars, start, 15)
        w60 = exact_window(bars, start, 60)
        out[f"{symbol.lower()}_ret_15m"] = simple_return(w15)
        out[f"{symbol.lower()}_ret_60m"] = simple_return(w60)
    event_vol = quote_volume(exact_window(bnbusdt_1m, start, 60))
    baseline, baseline_dates = prior_same_clock_volume_baseline(bnbusdt_1m, start)
    out["bnbusdt_quote_volume_60m"] = event_vol
    out["bnbusdt_quote_volume_baseline_median_prior20"] = baseline
    out["bnbusdt_volume_shock_ratio"] = event_vol / baseline if baseline > 0 else None
    out["baseline_dates_utc"] = baseline_dates
    return out


def causal_summary(events: Iterable[dict]) -> dict:
    rows = list(events)
    if len(rows) != 25:
        raise ValueError("final Diamond V0.2 causal summary requires exactly 25 complete events")
    r60 = [float(x["bnbbtc_ret_60m"]) for x in rows]
    vr = [float(x["bnbusdt_volume_shock_ratio"]) for x in rows]
    positive_r60 = sum(x > 0 for x in r60)
    volume_gt_one = sum(x > 1 for x in vr)
    return {
        "n": 25,
        "positive_bnbbtc_60m_events": positive_r60,
        "median_bnbbtc_60m_return": float(median(r60)),
        "volume_shock_ratio_gt_one_events": volume_gt_one,
        "median_volume_shock_ratio": float(median(vr)),
        "causal_gate_pass": (
            positive_r60 >= 17
            and median(r60) > 0
            and volume_gt_one >= 17
            and median(vr) > 1
        ),
    }

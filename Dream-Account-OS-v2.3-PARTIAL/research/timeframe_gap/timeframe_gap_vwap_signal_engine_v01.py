#!/usr/bin/env python3
"""Outcome-blind VWAP signal-formation engine for timeframe-gap preparation.

This module performs only causal VWAP construction, target-timeframe aggregation,
and reclaim/loss signal labeling. It deliberately contains no PnL, return,
profit-factor, bootstrap, validation unlock, or protected-phase access logic.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SUPPORTED = {
    "15m": {"rule": "15min", "minutes": 15, "hold_bars": 16},
    "30m": {"rule": "30min", "minutes": 30, "hold_bars": 8},
}


class SignalEngineError(RuntimeError):
    pass


def hold_bars_for_four_hours(timeframe: str) -> int:
    try:
        return int(SUPPORTED[timeframe]["hold_bars"])
    except KeyError as exc:
        raise SignalEngineError(f"unsupported timeframe: {timeframe}") from exc


def _validate_minute_frame(df: pd.DataFrame) -> pd.DataFrame:
    required = {"ts", "open", "high", "low", "close", "volume"}
    missing = required.difference(df.columns)
    if missing:
        raise SignalEngineError(f"missing columns: {sorted(missing)}")
    d = df[list(required)].copy()
    d["ts"] = pd.to_datetime(d["ts"], utc=True, errors="coerce")
    if d["ts"].isna().any():
        raise SignalEngineError("invalid timestamp")
    d.sort_values("ts", inplace=True)
    if d["ts"].duplicated().any():
        raise SignalEngineError("duplicate timestamp")
    for c in ("open", "high", "low", "close", "volume"):
        d[c] = pd.to_numeric(d[c], errors="coerce")
    if d[["open", "high", "low", "close", "volume"]].isna().any().any():
        raise SignalEngineError("invalid numeric row")
    if (d["volume"] <= 0).any():
        raise SignalEngineError("non-positive volume")
    return d.set_index("ts")


def causal_daily_vwap_from_1m(df: pd.DataFrame) -> pd.DataFrame:
    """Return validated 1m rows with a causal daily UTC VWAP and session flag."""
    d = _validate_minute_frame(df)
    day = d.index.floor("D")
    minute_of_day = d.index.hour * 60 + d.index.minute

    counts = pd.Series(1, index=d.index).groupby(day).cumsum().to_numpy()
    expected = minute_of_day.to_numpy() + 1
    sequential = counts == expected
    session_ok = pd.Series(sequential, index=d.index).groupby(day).cummin().astype(bool)

    typical = (d["high"] + d["low"] + d["close"]) / 3.0
    pv = typical * d["volume"]
    cum_pv = pv.groupby(day).cumsum()
    cum_vol = d["volume"].groupby(day).cumsum()
    d["vwap"] = (cum_pv / cum_vol).where(session_ok)
    d["session_ok"] = session_ok
    return d


def aggregate_signal_bars(df_1m: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Aggregate completed 1m rows into causal 15m/30m signal bars."""
    if timeframe not in SUPPORTED:
        raise SignalEngineError(f"unsupported timeframe: {timeframe}")
    spec = SUPPORTED[timeframe]
    d = causal_daily_vwap_from_1m(df_1m)
    bars = d.resample(spec["rule"], label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        volume=("volume", "sum"),
        minute_count=("close", "count"),
        vwap=("vwap", "last"),
        session_ok=("session_ok", "last"),
    )
    bars["bar_ok"] = (
        (bars["minute_count"] == int(spec["minutes"]))
        & bars["session_ok"].fillna(False)
        & bars[["open", "close", "vwap"]].notna().all(axis=1)
    )
    return bars


def label_reclaim_loss_signals(bars: pd.DataFrame) -> pd.DataFrame:
    """Label completed-bar VWAP crosses only; +1 long, -1 short, 0 none."""
    required = {"close", "vwap", "bar_ok"}
    missing = required.difference(bars.columns)
    if missing:
        raise SignalEngineError(f"missing bar columns: {sorted(missing)}")
    b = bars.copy()
    prev_ok = b["bar_ok"].shift(1).eq(True)
    cur_ok = b["bar_ok"].fillna(False).astype(bool)
    long_sig = prev_ok & cur_ok & (b["close"].shift(1) <= b["vwap"].shift(1)) & (b["close"] > b["vwap"])
    short_sig = prev_ok & cur_ok & (b["close"].shift(1) >= b["vwap"].shift(1)) & (b["close"] < b["vwap"])
    direction = pd.Series(0, index=b.index, dtype="int8")
    direction[long_sig] = 1
    direction[short_sig] = -1
    b["signal_direction"] = direction
    return b


def build_signal_frame(df_1m: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    """Convenience composition used by future runners and synthetic tests."""
    return label_reclaim_loss_signals(aggregate_signal_bars(df_1m, timeframe))

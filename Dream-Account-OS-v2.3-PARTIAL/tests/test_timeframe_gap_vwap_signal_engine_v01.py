from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd

MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "timeframe_gap"
    / "timeframe_gap_vwap_signal_engine_v01.py"
)
SPEC = importlib.util.spec_from_file_location("timeframe_gap_vwap_signal_engine_v01", MODULE_PATH)
assert SPEC and SPEC.loader
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


def synthetic_day() -> pd.DataFrame:
    ts = pd.date_range("2022-01-01T00:00:00Z", periods=1440, freq="1min")
    base = 100.0 + np.arange(1440, dtype=float) * 0.001
    return pd.DataFrame(
        {
            "ts": ts,
            "open": base,
            "high": base + 0.02,
            "low": base - 0.02,
            "close": base + 0.005,
            "volume": np.full(1440, 10.0),
        }
    )


def test_four_hour_hold_mapping_is_frozen():
    assert m.hold_bars_for_four_hours("15m") == 16
    assert m.hold_bars_for_four_hours("30m") == 8


def test_complete_day_aggregates_to_expected_bar_counts():
    df = synthetic_day()
    b15 = m.aggregate_signal_bars(df, "15m")
    b30 = m.aggregate_signal_bars(df, "30m")
    assert len(b15) == 96
    assert len(b30) == 48
    assert b15["bar_ok"].all()
    assert b30["bar_ok"].all()
    assert (b15["minute_count"] == 15).all()
    assert (b30["minute_count"] == 30).all()


def test_future_minutes_cannot_change_first_completed_bar_vwap():
    df = synthetic_day()
    first_before = float(m.aggregate_signal_bars(df, "15m")["vwap"].iloc[0])

    changed = df.copy()
    future = changed["ts"] >= pd.Timestamp("2022-01-01T00:15:00Z")
    changed.loc[future, ["open", "high", "low", "close"]] += 5000.0
    changed.loc[future, "volume"] *= 100.0

    first_after = float(m.aggregate_signal_bars(changed, "15m")["vwap"].iloc[0])
    assert first_after == first_before


def test_missing_minute_fails_closed_for_remaining_utc_session():
    df = synthetic_day()
    df = df[df["ts"] != pd.Timestamp("2022-01-01T00:05:00Z")].copy()
    b15 = m.aggregate_signal_bars(df, "15m")
    assert not bool(b15["bar_ok"].any())


def test_reclaim_and_loss_use_completed_previous_and_current_bars_only():
    idx = pd.date_range("2022-01-01T00:00:00Z", periods=4, freq="15min")
    bars = pd.DataFrame(
        {
            "close": [99.0, 101.0, 102.0, 98.0],
            "vwap": [100.0, 100.0, 100.0, 100.0],
            "bar_ok": [True, True, True, True],
        },
        index=idx,
    )
    out = m.label_reclaim_loss_signals(bars)
    assert out["signal_direction"].tolist() == [0, 1, 0, -1]

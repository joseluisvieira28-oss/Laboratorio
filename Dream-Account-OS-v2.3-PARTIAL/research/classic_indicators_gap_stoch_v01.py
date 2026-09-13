#!/usr/bin/env python3
"""CIGL-STOCH-01 — frozen slow Stochastic 14-3-3 extreme-zone K/D crossover.

Prospective implementation: Discovery 2022-2023 is primary 1H; 4H is
robustness-only. 2024 can open only after the frozen pooled 1H gate passes.
2025+ is never requested. No post-outcome tuning is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from classic_indicators_gap_v01 import (
    BASE_COST_BPS,
    STRESS_COST_BPS,
    HOLD_BARS,
    SYMBOLS,
    DISCOVERY_MONTHS,
    VALIDATION_MONTHS,
    FORBIDDEN_START,
    summarize,
    discovery_gate,
    validation_gate,
)
from classic_indicators_gap_vwap_data_vision_v01 import load_symbol_phase, json_safe

RAW_K_LENGTH = 14
SLOW_K_SMA = 3
D_SMA = 3
LOWER = 20.0
UPPER = 80.0


def aggregate_exact(minute: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    rule, expected = ("1h", 60) if timeframe == "1H" else ("4h", 240)
    d = minute.copy().set_index("ts").sort_index()
    h = d.resample(rule, label="left", closed="left").agg(
        open=("open", "first"),
        high=("high", "max"),
        low=("low", "min"),
        close=("close", "last"),
        minute_count=("close", "count"),
    )
    h["bar_ok"] = (h["minute_count"] == expected) & h[["open", "high", "low", "close"]].notna().all(axis=1)
    return h


def add_stochastic(bars: pd.DataFrame) -> pd.DataFrame:
    """Compute frozen slow stochastic independently inside each complete-bar segment."""
    out = bars.copy()
    out["raw_k14"] = np.nan
    out["slow_k"] = np.nan
    out["stoch_d"] = np.nan

    valid = out["bar_ok"].fillna(False).to_numpy(bool)
    size = len(out)
    i = 0
    while i < size:
        if not valid[i]:
            i += 1
            continue
        j = i
        while j < size and valid[j]:
            j += 1

        seg = out.iloc[i:j]
        lows = seg["low"].rolling(RAW_K_LENGTH, min_periods=RAW_K_LENGTH).min()
        highs = seg["high"].rolling(RAW_K_LENGTH, min_periods=RAW_K_LENGTH).max()
        denom = highs - lows
        raw = 100.0 * (seg["close"] - lows) / denom
        raw = raw.where(denom > 0.0)
        slow = raw.rolling(SLOW_K_SMA, min_periods=SLOW_K_SMA).mean()
        dline = slow.rolling(D_SMA, min_periods=D_SMA).mean()

        idx = out.index[i:j]
        out.loc[idx, "raw_k14"] = raw.to_numpy(float)
        out.loc[idx, "slow_k"] = slow.to_numpy(float)
        out.loc[idx, "stoch_d"] = dline.to_numpy(float)
        i = j
    return out


def make_trades(bars: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    h = bars.copy()
    prev_ok = h["bar_ok"].shift(1).eq(True)
    cur_ok = h["bar_ok"].fillna(False)
    eligible = (
        prev_ok
        & cur_ok
        & h[["slow_k", "stoch_d"]].notna().all(axis=1)
        & h[["slow_k", "stoch_d"]].shift(1).notna().all(axis=1)
    )

    long_sig = (
        eligible
        & (h["slow_k"].shift(1) <= h["stoch_d"].shift(1))
        & (h["slow_k"] > h["stoch_d"])
        & (h["slow_k"] <= LOWER)
        & (h["stoch_d"] <= LOWER)
    )
    short_sig = (
        eligible
        & (h["slow_k"].shift(1) >= h["stoch_d"].shift(1))
        & (h["slow_k"] < h["stoch_d"])
        & (h["slow_k"] >= UPPER)
        & (h["stoch_d"] >= UPPER)
    )

    direction = pd.Series(0, index=h.index, dtype="int8")
    direction[long_sig] = 1
    direction[short_sig] = -1

    rows = []
    next_free = -1
    idx = h.index
    for pos, sigv in enumerate(direction.to_numpy()):
        if sigv == 0:
            continue
        entry = pos + 1
        exit_ = entry + HOLD_BARS
        if entry <= next_free or exit_ >= len(h):
            continue
        if not bool(h["bar_ok"].iloc[entry:exit_].fillna(False).all()):
            continue
        et, xt = idx[entry], idx[exit_]
        if xt >= FORBIDDEN_START:
            continue
        ep, xp = float(h["open"].iloc[entry]), float(h["open"].iloc[exit_])
        if not (ep > 0 and xp > 0 and math.isfinite(ep) and math.isfinite(xp)):
            continue
        gross = float(sigv * math.log(xp / ep) * 10000.0)
        rows.append(
            {
                "symbol": symbol,
                "timeframe": timeframe,
                "signal_time": idx[pos],
                "entry_time": et,
                "exit_time": xt,
                "direction": int(sigv),
                "signal_raw_k14": float(h["raw_k14"].iloc[pos]),
                "signal_slow_k": float(h["slow_k"].iloc[pos]),
                "signal_d": float(h["stoch_d"].iloc[pos]),
                "entry_price": ep,
                "exit_price": xp,
                "gross_bps": gross,
                "net10_bps": gross - BASE_COST_BPS,
                "net14_bps": gross - STRESS_COST_BPS,
            }
        )
        next_free = exit_ - 1
    return pd.DataFrame(rows)


def evaluate(months, phase: str, prov: list) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    parts = {"1H": [], "4H": []}
    cov = {}
    for symbol in SYMBOLS:
        minute = load_symbol_phase(symbol, months, phase, prov)
        cov[symbol] = {"minute_rows": len(minute)}
        for tf in ("1H", "4H"):
            bars = add_stochastic(aggregate_exact(minute, tf))
            trades = make_trades(bars, symbol, tf)
            cov[symbol][tf] = {
                "valid_bars": int(bars.bar_ok.sum()),
                "eligible_signal_bars": int(bars.stoch_d.notna().sum()),
                "trades": len(trades),
            }
            print(
                f"[{phase}] {symbol} {tf}: valid={cov[symbol][tf]['valid_bars']} "
                f"eligible={cov[symbol][tf]['eligible_signal_bars']} trades={len(trades)}",
                flush=True,
            )
            if len(trades):
                parts[tf].append(trades)

    def combine(xs):
        if not xs:
            return pd.DataFrame()
        t = pd.concat(xs, ignore_index=True)
        for c in ["signal_time", "entry_time", "exit_time"]:
            t[c] = pd.to_datetime(t[c], utc=True)
        return t.sort_values(["entry_time", "symbol"]).reset_index(drop=True)

    return combine(parts["1H"]), combine(parts["4H"]), cov


def assert_freeze(f: dict) -> None:
    if f.get("experiment_id") != "CIGL-STOCH-01":
        raise RuntimeError("Stochastic identity mismatch")
    s = f.get("stochastic", {})
    e = f.get("execution", {})
    g = f.get("phase_gates", {}).get("discovery_1h", {})
    if (s.get("raw_k_length"), s.get("slow_k_sma"), s.get("d_sma")) != (14, 3, 3):
        raise RuntimeError("Stochastic 14-3-3 mismatch")
    if (s.get("lower_threshold"), s.get("upper_threshold")) != (20.0, 80.0):
        raise RuntimeError("Stochastic 20/80 threshold mismatch")
    if s.get("orientation") != "extreme_zone_mean_reversion_kd_crossover":
        raise RuntimeError("Stochastic orientation mismatch")
    if s.get("zero_range_policy") != "raw_K14 ineligible when highest_high_14 == lowest_low_14; no replacement value":
        raise RuntimeError("Stochastic zero-range policy mismatch")
    if e.get("holding_bars") != 4 or e.get("base_roundtrip_cost_bps") != 10.0 or e.get("stress_roundtrip_cost_bps") != 14.0:
        raise RuntimeError("execution mismatch")
    if g.get("min_trades") != 300 or g.get("net10_mean_bps_gt") != 0.0 or g.get("profit_factor_gt") != 1.0:
        raise RuntimeError("gate mismatch")


def self_test(freeze: dict) -> None:
    assert_freeze(freeze)
    n = 60
    ix = pd.date_range("2020-01-01", periods=n, freq="1h", tz="UTC")
    close = np.arange(100.0, 100.0 + n)
    bars = pd.DataFrame(
        {
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "bar_ok": True,
        },
        index=ix,
    )
    bars.iloc[20, bars.columns.get_loc("bar_ok")] = False
    out = add_stochastic(bars)
    # Segment 1 starts at 0: D first eligible at index 17 (14 + 3 + 3 - 3).
    if out["stoch_d"].iloc[:17].notna().any() or not math.isfinite(float(out["stoch_d"].iloc[17])):
        raise RuntimeError("Stochastic warmup self-test failed before gap")
    # Gap at 20 forces fresh segment from 21: first D at 21 + 17 = 38.
    if out["stoch_d"].iloc[20:38].notna().any() or not math.isfinite(float(out["stoch_d"].iloc[38])):
        raise RuntimeError("Stochastic gap-reset self-test failed")
    print("CIGL-STOCH-01 deterministic self-test: PASS", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ap.add_argument("--freeze", type=Path, required=True)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    freeze_bytes = args.freeze.read_bytes()
    freeze = json.loads(freeze_bytes)
    assert_freeze(freeze)

    if args.self_test:
        self_test(freeze)
        return
    if args.out is None:
        raise SystemExit("--out is required unless --self-test is used")

    args.out.mkdir(parents=True, exist_ok=True)
    prov = []
    d1, d4, covd = evaluate(DISCOVERY_MONTHS, "DISCOVERY", prov)
    d1.to_csv(args.out / "CIGL_STOCH_01_DISCOVERY_1H_TRADES.csv", index=False)
    d4.to_csv(args.out / "CIGL_STOCH_01_DISCOVERY_4H_ROBUSTNESS_TRADES.csv", index=False)

    s1, s4 = summarize(d1), summarize(d4)
    dg = discovery_gate(s1)
    opened = bool(dg["pass"])
    vs1 = vs4 = vg = covv = None

    if opened:
        print("STOCH DISCOVERY 1H PASS — opening frozen 2024 once", flush=True)
        v1, v4, covv = evaluate(VALIDATION_MONTHS, "VALIDATION_2024", prov)
        v1.to_csv(args.out / "CIGL_STOCH_01_VALIDATION_2024_1H_TRADES.csv", index=False)
        v4.to_csv(args.out / "CIGL_STOCH_01_VALIDATION_2024_4H_ROBUSTNESS_TRADES.csv", index=False)
        vs1, vs4 = summarize(v1), summarize(v4)
        vg = validation_gate(vs1)
        status = "MVE_1_REPLICATION_READY" if vg["pass"] else "OOS_FAIL_STOCH_CLOSED"
    else:
        status = "DISCOVERY_FAIL_STOCH_CLOSED"
        print("STOCH DISCOVERY 1H FAIL — 2024 remains unopened", flush=True)

    closeout = json_safe(
        {
            "lab": "CLASSIC_INDICATORS_GAP_LAB_V0.1",
            "experiment_id": "CIGL-STOCH-01",
            "status": status,
            "implementation_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
            "discovery_1h_summary": s1,
            "discovery_1h_gate": dg,
            "discovery_4h_robustness_summary": s4,
            "opened_2024": opened,
            "validation_1h_summary": vs1,
            "validation_1h_gate": vg,
            "validation_4h_robustness_summary": vs4,
            "coverage_discovery": covd,
            "coverage_validation": covv,
            "accessed_2025": False,
            "accessed_2026": False,
            "live_trading": False,
            "exchange_mutation": False,
            "post_result_parameter_change": False,
        }
    )
    (args.out / "CIGL_STOCH_01_CLOSEOUT.json").write_text(json.dumps(closeout, indent=2, sort_keys=True))
    (args.out / "CIGL_STOCH_01_DATA_PROVENANCE.json").write_text(json.dumps(json_safe(prov), indent=2, sort_keys=True))

    p, r = closeout["discovery_1h_summary"], closeout["discovery_4h_robustness_summary"]
    lines = [
        "# CIGL-STOCH-01 — CLOSEOUT",
        "",
        f"Status: **{status}**",
        "",
        "## 1H Discovery",
        f"- Trades: {p.get('n')}",
        f"- Gross mean: {p.get('gross_mean_bps')} bps",
        f"- NET10 mean: {p.get('net10_mean_bps')} bps",
        f"- NET14 mean: {p.get('net14_mean_bps')} bps",
        f"- PF NET10: {p.get('pf_net10')}",
        f"- Gate pass: {dg['pass']}",
        "",
        "## 4H robustness",
        f"- Trades: {r.get('n')}",
        f"- NET10 mean: {r.get('net10_mean_bps')} bps",
        f"- PF NET10: {r.get('pf_net10')}",
        "",
        f"2024 opened: **{opened}**",
        "2025 accessed: **False**",
        "2026 accessed: **False**",
    ]
    if vs1:
        lines += [
            "",
            "## 2024 OOS",
            f"- Trades: {vs1.get('n')}",
            f"- NET10 mean: {vs1.get('net10_mean_bps')} bps",
            f"- PF NET10: {vs1.get('pf_net10')}",
            f"- Gate pass: {vg['pass']}",
        ]
    (args.out / "CIGL_STOCH_01_SUMMARY.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(closeout, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

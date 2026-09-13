#!/usr/bin/env python3
"""CIGL-SUPERTREND-01 — frozen Supertrend ATR10 x3 direction-flip experiment.

Research only. Discovery 2022-2023 opens first. 2024 can open only after the
frozen pooled 1H gate passes. 4H is robustness-only and cannot rescue 1H.
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

ATR_N = 10
MULT = 3.0


def aggregate_exact(minute: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "1H":
        rule, expected = "1h", 60
    elif timeframe == "4H":
        rule, expected = "4h", 240
    else:
        raise ValueError(timeframe)
    d = minute.copy().set_index("ts").sort_index()
    h = d.resample(rule, label="left", closed="left").agg(
        open=("open", "first"), high=("high", "max"), low=("low", "min"),
        close=("close", "last"), minute_count=("close", "count"),
    )
    h["bar_ok"] = (h["minute_count"] == expected) & h[["open", "high", "low", "close"]].notna().all(axis=1)
    return h


def add_supertrend(bars: pd.DataFrame) -> pd.DataFrame:
    out = bars.copy()
    for c in ["true_range", "atr10", "final_upper", "final_lower", "supertrend"]:
        out[c] = np.nan
    out["state"] = 0
    out["flip"] = 0

    valid = out["bar_ok"].fillna(False).to_numpy(bool)
    nrows = len(out)
    i = 0
    while i < nrows:
        if not valid[i]:
            i += 1
            continue
        j = i
        while j < nrows and valid[j]:
            j += 1
        m = j - i
        if m >= ATR_N + 2:
            hi = out["high"].iloc[i:j].to_numpy(float)
            lo = out["low"].iloc[i:j].to_numpy(float)
            cl = out["close"].iloc[i:j].to_numpy(float)
            tr = np.full(m, np.nan)
            for k in range(1, m):
                tr[k] = max(hi[k] - lo[k], abs(hi[k] - cl[k - 1]), abs(lo[k] - cl[k - 1]))
            atr = np.full(m, np.nan)
            atr[ATR_N] = float(np.mean(tr[1:ATR_N + 1]))
            for k in range(ATR_N + 1, m):
                atr[k] = (atr[k - 1] * (ATR_N - 1) + tr[k]) / ATR_N

            fu = np.full(m, np.nan)
            fl = np.full(m, np.nan)
            st = np.full(m, np.nan)
            state = np.zeros(m, dtype=np.int8)
            flip = np.zeros(m, dtype=np.int8)
            k0 = ATR_N
            hl2 = (hi + lo) / 2.0
            bu = hl2 + MULT * atr
            bl = hl2 - MULT * atr
            fu[k0] = bu[k0]
            fl[k0] = bl[k0]
            state[k0] = 1 if cl[k0] >= hl2[k0] else -1
            st[k0] = fl[k0] if state[k0] == 1 else fu[k0]

            for k in range(k0 + 1, m):
                fu[k] = bu[k] if (bu[k] < fu[k - 1] or cl[k - 1] > fu[k - 1]) else fu[k - 1]
                fl[k] = bl[k] if (bl[k] > fl[k - 1] or cl[k - 1] < fl[k - 1]) else fl[k - 1]
                prev = int(state[k - 1])
                if prev == -1:
                    state[k] = 1 if cl[k] > fu[k] else -1
                else:
                    state[k] = -1 if cl[k] < fl[k] else 1
                if state[k] != prev:
                    flip[k] = int(state[k])
                st[k] = fl[k] if state[k] == 1 else fu[k]

            target = out.index[i:j]
            out.loc[target, "true_range"] = tr
            out.loc[target, "atr10"] = atr
            out.loc[target, "final_upper"] = fu
            out.loc[target, "final_lower"] = fl
            out.loc[target, "supertrend"] = st
            out.loc[target, "state"] = state
            out.loc[target, "flip"] = flip
        i = j
    return out


def make_trades(bars: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    h = bars.copy()
    direction = h["flip"].astype("int8")
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
        rows.append({
            "symbol": symbol, "timeframe": timeframe,
            "signal_time": idx[pos], "entry_time": et, "exit_time": xt,
            "direction": int(sigv), "signal_atr10": float(h["atr10"].iloc[pos]),
            "signal_final_upper": float(h["final_upper"].iloc[pos]),
            "signal_final_lower": float(h["final_lower"].iloc[pos]),
            "entry_price": ep, "exit_price": xp,
            "gross_bps": gross, "net10_bps": gross - BASE_COST_BPS,
            "net14_bps": gross - STRESS_COST_BPS,
        })
        next_free = exit_ - 1
    return pd.DataFrame(rows)


def evaluate(months, phase: str, provenance: list):
    parts = {"1H": [], "4H": []}
    coverage = {}
    for symbol in SYMBOLS:
        minute = load_symbol_phase(symbol, months, phase, provenance)
        coverage[symbol] = {"minute_rows": int(len(minute))}
        for tf in ("1H", "4H"):
            bars = add_supertrend(aggregate_exact(minute, tf))
            trades = make_trades(bars, symbol, tf)
            coverage[symbol][tf] = {
                "valid_bars": int(bars["bar_ok"].sum()),
                "atr_bars": int(bars["atr10"].notna().sum()),
                "flips": int((bars["flip"] != 0).sum()),
                "trades": int(len(trades)),
            }
            print(f"[{phase}] {symbol} {tf}: valid={coverage[symbol][tf]['valid_bars']} atr={coverage[symbol][tf]['atr_bars']} flips={coverage[symbol][tf]['flips']} trades={len(trades)}", flush=True)
            if len(trades):
                parts[tf].append(trades)

    def combine(xs):
        if not xs:
            return pd.DataFrame()
        t = pd.concat(xs, ignore_index=True)
        for c in ["signal_time", "entry_time", "exit_time"]:
            t[c] = pd.to_datetime(t[c], utc=True)
        return t.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    return combine(parts["1H"]), combine(parts["4H"]), coverage


def assert_freeze(f: dict) -> None:
    if f.get("experiment_id") != "CIGL-SUPERTREND-01":
        raise RuntimeError("Supertrend identity mismatch")
    s = f.get("supertrend", {})
    if s.get("atr_style") != "Wilder" or s.get("atr_length") != 10 or s.get("multiplier") != 3.0:
        raise RuntimeError("Supertrend ATR10 x3 mismatch")
    if s.get("signal") != "completed-bar direction flip only":
        raise RuntimeError("Supertrend signal mismatch")
    e = f.get("execution", {})
    g = f.get("phase_gates", {}).get("discovery_1h", {})
    if e.get("holding_bars") != 4 or e.get("base_roundtrip_cost_bps") != 10.0 or e.get("stress_roundtrip_cost_bps") != 14.0:
        raise RuntimeError("execution mismatch")
    if g.get("min_trades") != 300 or g.get("net10_mean_bps_gt") != 0.0 or g.get("profit_factor_gt") != 1.0:
        raise RuntimeError("gate mismatch")


def self_test(freeze: dict) -> None:
    assert_freeze(freeze)
    n = 80
    ix = pd.date_range("2020-01-01", periods=n, freq="1h", tz="UTC")
    close = 100.0 + np.sin(np.arange(n) / 2.0) * 8.0 + np.arange(n) * 0.1
    bars = pd.DataFrame({"open": close, "high": close + 1.5, "low": close - 1.5, "close": close, "bar_ok": True}, index=ix)
    bars.iloc[30, bars.columns.get_loc("bar_ok")] = False
    out = add_supertrend(bars)
    # First segment starts at 0; ATR/state first eligible at index 10, and seed emits no flip.
    if out["atr10"].iloc[:10].notna().any() or not math.isfinite(float(out["atr10"].iloc[10])) or int(out["flip"].iloc[10]) != 0:
        raise RuntimeError("Supertrend first-segment warmup/seed self-test failed")
    # Gap at 30 forces fresh segment from 31; first new ATR/state at 41, with no seed signal.
    if out["atr10"].iloc[30:41].notna().any() or not math.isfinite(float(out["atr10"].iloc[41])) or int(out["flip"].iloc[41]) != 0:
        raise RuntimeError("Supertrend gap reset self-test failed")
    if out.loc[out["atr10"].notna(), ["final_upper", "final_lower", "supertrend"]].isna().any().any():
        raise RuntimeError("Supertrend band completeness self-test failed")
    print("CIGL-SUPERTREND-01 deterministic self-test: PASS", flush=True)


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
    d1.to_csv(args.out / "CIGL_SUPERTREND_01_DISCOVERY_1H_TRADES.csv", index=False)
    d4.to_csv(args.out / "CIGL_SUPERTREND_01_DISCOVERY_4H_ROBUSTNESS_TRADES.csv", index=False)
    s1, s4 = summarize(d1), summarize(d4)
    dg = discovery_gate(s1)
    opened = bool(dg["pass"])
    vs1 = vs4 = vg = covv = None
    if opened:
        print("SUPERTREND DISCOVERY 1H PASS — opening frozen 2024 once", flush=True)
        v1, v4, covv = evaluate(VALIDATION_MONTHS, "VALIDATION_2024", prov)
        v1.to_csv(args.out / "CIGL_SUPERTREND_01_VALIDATION_2024_1H_TRADES.csv", index=False)
        v4.to_csv(args.out / "CIGL_SUPERTREND_01_VALIDATION_2024_4H_ROBUSTNESS_TRADES.csv", index=False)
        vs1, vs4 = summarize(v1), summarize(v4)
        vg = validation_gate(vs1)
        status = "MVE_1_REPLICATION_READY" if vg["pass"] else "OOS_FAIL_SUPERTREND_CLOSED"
    else:
        print("SUPERTREND DISCOVERY 1H FAIL — 2024 remains unopened", flush=True)
        status = "DISCOVERY_FAIL_SUPERTREND_CLOSED"

    closeout = json_safe({
        "lab":"CLASSIC_INDICATORS_GAP_LAB_V0.1","experiment_id":"CIGL-SUPERTREND-01","status":status,
        "implementation_freeze_sha256":hashlib.sha256(freeze_bytes).hexdigest(),
        "parameters":{"atr_style":"Wilder","atr_length":10,"multiplier":3.0,"signal":"direction_flip_only"},
        "discovery_1h_summary":s1,"discovery_1h_gate":dg,"discovery_4h_robustness_summary":s4,
        "opened_2024":opened,"validation_1h_summary":vs1,"validation_1h_gate":vg,"validation_4h_robustness_summary":vs4,
        "coverage_discovery":covd,"coverage_validation":covv,"accessed_2025":False,"accessed_2026":False,
        "live_trading":False,"exchange_mutation":False,"post_result_parameter_change":False,
    })
    (args.out / "CIGL_SUPERTREND_01_CLOSEOUT.json").write_text(json.dumps(closeout, indent=2, sort_keys=True))
    (args.out / "CIGL_SUPERTREND_01_DATA_PROVENANCE.json").write_text(json.dumps(json_safe(prov), indent=2, sort_keys=True))
    p, r = s1, s4
    lines = ["# CIGL-SUPERTREND-01 — CLOSEOUT","",f"Status: **{status}**","","## 1H Discovery",f"- Trades: {p.get('n')}",f"- NET10 mean: {p.get('net10_mean_bps')} bps",f"- NET14 mean: {p.get('net14_mean_bps')} bps",f"- PF NET10: {p.get('pf_net10')}",f"- Gate pass: {dg['pass']}","","## 4H robustness",f"- Trades: {r.get('n')}",f"- NET10 mean: {r.get('net10_mean_bps')} bps",f"- PF NET10: {r.get('pf_net10')}","",f"2024 opened: **{opened}**","2025 accessed: **False**","2026 accessed: **False**"]
    if vs1:
        lines += ["","## 2024 OOS",f"- Trades: {vs1.get('n')}",f"- NET10 mean: {vs1.get('net10_mean_bps')} bps",f"- PF NET10: {vs1.get('pf_net10')}",f"- Gate pass: {vg['pass']}"]
    (args.out / "CIGL_SUPERTREND_01_SUMMARY.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(closeout, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

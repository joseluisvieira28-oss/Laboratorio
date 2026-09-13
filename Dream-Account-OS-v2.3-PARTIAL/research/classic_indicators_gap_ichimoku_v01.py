#!/usr/bin/env python3
"""CIGL-ICHIMOKU-01 — frozen canonical 9/26/52 visible-cloud breakout experiment.

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

TENKAN_N = 9
KIJUN_N = 26
SENKOU_B_N = 52
DISPLACEMENT = 26


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


def _midpoint(high: np.ndarray, low: np.ndarray, window: int) -> np.ndarray:
    s_hi = pd.Series(high)
    s_lo = pd.Series(low)
    return ((s_hi.rolling(window, min_periods=window).max() + s_lo.rolling(window, min_periods=window).min()) / 2.0).to_numpy(float)


def add_ichimoku(bars: pd.DataFrame) -> pd.DataFrame:
    out = bars.copy()
    cols = [
        "tenkan9", "kijun26", "raw_senkou_a", "raw_senkou_b",
        "visible_senkou_a", "visible_senkou_b", "cloud_top", "cloud_bottom",
    ]
    for c in cols:
        out[c] = np.nan
    out["signal"] = 0

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
        if m >= 1:
            hi = out["high"].iloc[i:j].to_numpy(float)
            lo = out["low"].iloc[i:j].to_numpy(float)
            cl = out["close"].iloc[i:j].to_numpy(float)

            tenkan = _midpoint(hi, lo, TENKAN_N)
            kijun = _midpoint(hi, lo, KIJUN_N)
            raw_a = (tenkan + kijun) / 2.0
            raw_b = _midpoint(hi, lo, SENKOU_B_N)

            vis_a = np.full(m, np.nan)
            vis_b = np.full(m, np.nan)
            if m > DISPLACEMENT:
                vis_a[DISPLACEMENT:] = raw_a[:-DISPLACEMENT]
                vis_b[DISPLACEMENT:] = raw_b[:-DISPLACEMENT]
            cloud_top = np.maximum(vis_a, vis_b)
            cloud_bottom = np.minimum(vis_a, vis_b)

            signal = np.zeros(m, dtype=np.int8)
            eligible = np.isfinite(cloud_top) & np.isfinite(cloud_bottom)
            for k in range(1, m):
                if not (eligible[k - 1] and eligible[k]):
                    continue
                if cl[k - 1] <= cloud_top[k - 1] and cl[k] > cloud_top[k]:
                    signal[k] = 1
                elif cl[k - 1] >= cloud_bottom[k - 1] and cl[k] < cloud_bottom[k]:
                    signal[k] = -1

            target = out.index[i:j]
            out.loc[target, "tenkan9"] = tenkan
            out.loc[target, "kijun26"] = kijun
            out.loc[target, "raw_senkou_a"] = raw_a
            out.loc[target, "raw_senkou_b"] = raw_b
            out.loc[target, "visible_senkou_a"] = vis_a
            out.loc[target, "visible_senkou_b"] = vis_b
            out.loc[target, "cloud_top"] = cloud_top
            out.loc[target, "cloud_bottom"] = cloud_bottom
            out.loc[target, "signal"] = signal
        i = j
    return out


def make_trades(bars: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    h = bars.copy()
    direction = h["signal"].astype("int8")
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
            "direction": int(sigv),
            "signal_cloud_top": float(h["cloud_top"].iloc[pos]),
            "signal_cloud_bottom": float(h["cloud_bottom"].iloc[pos]),
            "signal_visible_senkou_a": float(h["visible_senkou_a"].iloc[pos]),
            "signal_visible_senkou_b": float(h["visible_senkou_b"].iloc[pos]),
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
            bars = add_ichimoku(aggregate_exact(minute, tf))
            trades = make_trades(bars, symbol, tf)
            coverage[symbol][tf] = {
                "valid_bars": int(bars["bar_ok"].sum()),
                "cloud_eligible_bars": int((bars["cloud_top"].notna() & bars["cloud_bottom"].notna()).sum()),
                "signals": int((bars["signal"] != 0).sum()),
                "trades": int(len(trades)),
            }
            print(
                f"[{phase}] {symbol} {tf}: valid={coverage[symbol][tf]['valid_bars']} "
                f"cloud={coverage[symbol][tf]['cloud_eligible_bars']} "
                f"signals={coverage[symbol][tf]['signals']} trades={len(trades)}",
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

    return combine(parts["1H"]), combine(parts["4H"]), coverage


def assert_freeze(f: dict) -> None:
    if f.get("experiment_id") != "CIGL-ICHIMOKU-01":
        raise RuntimeError("Ichimoku identity mismatch")
    s = f.get("ichimoku", {})
    expected = (s.get("tenkan_period"), s.get("kijun_period"), s.get("senkou_b_period"), s.get("displacement"))
    if expected != (9, 26, 52, 26):
        raise RuntimeError("Ichimoku 9/26/52/26 mismatch")
    if s.get("chikou_used") is not False or s.get("tenkan_kijun_confirmation") is not False or s.get("cloud_color_filter") is not False:
        raise RuntimeError("Ichimoku forbidden confirmation mismatch")
    e = f.get("execution", {})
    g = f.get("phase_gates", {}).get("discovery_1h", {})
    if e.get("holding_bars") != 4 or e.get("base_roundtrip_cost_bps") != 10.0 or e.get("stress_roundtrip_cost_bps") != 14.0:
        raise RuntimeError("execution mismatch")
    if g.get("min_trades") != 300 or g.get("net10_mean_bps_gt") != 0.0 or g.get("profit_factor_gt") != 1.0:
        raise RuntimeError("gate mismatch")
    fw = f.get("firewall", {})
    if fw.get("open_2025") is not False or fw.get("open_2026") is not False or fw.get("live_trading") is not False or fw.get("exchange_mutation") is not False:
        raise RuntimeError("firewall mismatch")


def self_test(freeze: dict) -> None:
    assert_freeze(freeze)
    n = 210
    ix = pd.date_range("2020-01-01", periods=n, freq="1h", tz="UTC")
    base = 100.0 + np.arange(n) * 0.2 + np.sin(np.arange(n) / 5.0)
    bars = pd.DataFrame({
        "open": base,
        "high": base + 2.0 + (np.arange(n) % 7) * 0.05,
        "low": base - 2.0 - (np.arange(n) % 5) * 0.05,
        "close": base + np.sin(np.arange(n) / 3.0),
        "bar_ok": True,
    }, index=ix)
    bars.iloc[100, bars.columns.get_loc("bar_ok")] = False
    out = add_ichimoku(bars)

    # In a fresh segment raw Senkou B first exists at index 51, so the visible
    # displaced cloud can first exist only at 51+26 = 77.
    if out["cloud_top"].iloc[:77].notna().any() or not math.isfinite(float(out["cloud_top"].iloc[77])):
        raise RuntimeError("Ichimoku first-segment displacement warmup self-test failed")
    if not math.isclose(float(out["visible_senkou_a"].iloc[77]), float(out["raw_senkou_a"].iloc[51]), rel_tol=0, abs_tol=1e-12):
        raise RuntimeError("Ichimoku Senkou A displacement self-test failed")
    if not math.isclose(float(out["visible_senkou_b"].iloc[77]), float(out["raw_senkou_b"].iloc[51]), rel_tol=0, abs_tol=1e-12):
        raise RuntimeError("Ichimoku Senkou B displacement self-test failed")

    # Gap at 100 terminates state. New segment starts at 101 and visible cloud
    # first becomes eligible at 101+77 = 178; nothing may cross the gap.
    if out["cloud_top"].iloc[100:178].notna().any() or not math.isfinite(float(out["cloud_top"].iloc[178])):
        raise RuntimeError("Ichimoku gap-reset displacement self-test failed")
    if not math.isclose(float(out["visible_senkou_b"].iloc[178]), float(out["raw_senkou_b"].iloc[152]), rel_tol=0, abs_tol=1e-12):
        raise RuntimeError("Ichimoku post-gap Senkou B displacement self-test failed")
    if int(out["signal"].iloc[77]) != 0 or int(out["signal"].iloc[178]) != 0:
        raise RuntimeError("Ichimoku first eligible cloud bar must not signal without eligible predecessor")
    print("CIGL-ICHIMOKU-01 deterministic self-test: PASS", flush=True)


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
    d1.to_csv(args.out / "CIGL_ICHIMOKU_01_DISCOVERY_1H_TRADES.csv", index=False)
    d4.to_csv(args.out / "CIGL_ICHIMOKU_01_DISCOVERY_4H_ROBUSTNESS_TRADES.csv", index=False)
    s1, s4 = summarize(d1), summarize(d4)
    dg = discovery_gate(s1)
    opened = bool(dg["pass"])
    vs1 = vs4 = vg = covv = None

    if opened:
        print("ICHIMOKU DISCOVERY 1H PASS — opening frozen 2024 once", flush=True)
        v1, v4, covv = evaluate(VALIDATION_MONTHS, "VALIDATION_2024", prov)
        v1.to_csv(args.out / "CIGL_ICHIMOKU_01_VALIDATION_2024_1H_TRADES.csv", index=False)
        v4.to_csv(args.out / "CIGL_ICHIMOKU_01_VALIDATION_2024_4H_ROBUSTNESS_TRADES.csv", index=False)
        vs1, vs4 = summarize(v1), summarize(v4)
        vg = validation_gate(vs1)
        status = "MVE_1_REPLICATION_READY" if vg["pass"] else "OOS_FAIL_ICHIMOKU_CLOSED"
    else:
        print("ICHIMOKU DISCOVERY 1H FAIL — 2024 remains unopened", flush=True)
        status = "DISCOVERY_FAIL_ICHIMOKU_CLOSED"

    closeout = json_safe({
        "lab": "CLASSIC_INDICATORS_GAP_LAB_V0.1",
        "experiment_id": "CIGL-ICHIMOKU-01",
        "status": status,
        "implementation_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "parameters": {
            "tenkan_period": 9, "kijun_period": 26, "senkou_b_period": 52,
            "displacement": 26, "signal": "visible_cloud_breakout_only",
            "chikou_used": False,
        },
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
    })
    (args.out / "CIGL_ICHIMOKU_01_CLOSEOUT.json").write_text(json.dumps(closeout, indent=2, sort_keys=True))
    (args.out / "CIGL_ICHIMOKU_01_DATA_PROVENANCE.json").write_text(json.dumps(json_safe(prov), indent=2, sort_keys=True))

    p, r = s1, s4
    lines = [
        "# CIGL-ICHIMOKU-01 — CLOSEOUT", "", f"Status: **{status}**", "",
        "## 1H Discovery", f"- Trades: {p.get('n')}",
        f"- NET10 mean: {p.get('net10_mean_bps')} bps",
        f"- NET14 mean: {p.get('net14_mean_bps')} bps",
        f"- PF NET10: {p.get('pf_net10')}", f"- Gate pass: {dg['pass']}", "",
        "## 4H robustness", f"- Trades: {r.get('n')}",
        f"- NET10 mean: {r.get('net10_mean_bps')} bps",
        f"- PF NET10: {r.get('pf_net10')}", "",
        f"2024 opened: **{opened}**", "2025 accessed: **False**", "2026 accessed: **False**",
        "Live trading: **False**", "Exchange mutation: **False**",
    ]
    if vs1:
        lines += ["", "## 2024 OOS", f"- Trades: {vs1.get('n')}",
                  f"- NET10 mean: {vs1.get('net10_mean_bps')} bps",
                  f"- PF NET10: {vs1.get('pf_net10')}", f"- Gate pass: {vg['pass']}"]
    (args.out / "CIGL_ICHIMOKU_01_CLOSEOUT.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(closeout, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

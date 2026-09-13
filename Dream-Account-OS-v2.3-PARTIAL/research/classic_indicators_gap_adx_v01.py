#!/usr/bin/env python3
"""CIGL-ADX-01 — frozen Wilder ADX/DMI experiment.

Runs 2022-2023 Discovery first on checksum-verified official Binance USD-M
1-minute archives. 2024 is fetched only if the frozen pooled 1H Discovery gate
passes. 4H is predeclared robustness only and can never rescue 1H. 2025+ is
never requested.
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

N = 14
THRESHOLD = 25.0


def aggregate_exact(minute: pd.DataFrame, timeframe: str) -> pd.DataFrame:
    if timeframe == "1H":
        rule, expected = "1h", 60
    elif timeframe == "4H":
        rule, expected = "4h", 240
    else:
        raise ValueError(timeframe)
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


def add_wilder_adx(bars: pd.DataFrame, n: int = N) -> pd.DataFrame:
    out = bars.copy()
    out["plus_di"] = np.nan
    out["minus_di"] = np.nan
    out["adx"] = np.nan
    valid = out["bar_ok"].fillna(False).to_numpy(dtype=bool)
    size = len(out)
    i = 0
    while i < size:
        if not valid[i]:
            i += 1
            continue
        j = i
        while j < size and valid[j]:
            j += 1
        seg_len = j - i
        if seg_len >= 2 * n:
            hi = out["high"].iloc[i:j].to_numpy(float)
            lo = out["low"].iloc[i:j].to_numpy(float)
            cl = out["close"].iloc[i:j].to_numpy(float)
            tr = np.full(seg_len, np.nan)
            pdm = np.full(seg_len, np.nan)
            mdm = np.full(seg_len, np.nan)
            for k in range(1, seg_len):
                up = hi[k] - hi[k - 1]
                down = lo[k - 1] - lo[k]
                pdm[k] = up if up > down and up > 0 else 0.0
                mdm[k] = down if down > up and down > 0 else 0.0
                tr[k] = max(hi[k] - lo[k], abs(hi[k] - cl[k - 1]), abs(lo[k] - cl[k - 1]))

            str_ = np.full(seg_len, np.nan)
            spdm = np.full(seg_len, np.nan)
            smdm = np.full(seg_len, np.nan)
            str_[n] = float(np.sum(tr[1:n + 1]))
            spdm[n] = float(np.sum(pdm[1:n + 1]))
            smdm[n] = float(np.sum(mdm[1:n + 1]))
            for k in range(n + 1, seg_len):
                str_[k] = str_[k - 1] - str_[k - 1] / n + tr[k]
                spdm[k] = spdm[k - 1] - spdm[k - 1] / n + pdm[k]
                smdm[k] = smdm[k - 1] - smdm[k - 1] / n + mdm[k]

            plus = np.full(seg_len, np.nan)
            minus = np.full(seg_len, np.nan)
            good_tr = np.isfinite(str_) & (str_ > 0)
            plus[good_tr] = 100.0 * spdm[good_tr] / str_[good_tr]
            minus[good_tr] = 100.0 * smdm[good_tr] / str_[good_tr]
            denom = plus + minus
            dx = np.full(seg_len, np.nan)
            good_di = np.isfinite(denom) & (denom > 0)
            dx[good_di] = 100.0 * np.abs(plus[good_di] - minus[good_di]) / denom[good_di]

            adx = np.full(seg_len, np.nan)
            first_adx = 2 * n - 1
            if first_adx < seg_len and np.isfinite(dx[n:first_adx + 1]).all():
                adx[first_adx] = float(np.mean(dx[n:first_adx + 1]))
                for k in range(first_adx + 1, seg_len):
                    if not np.isfinite(dx[k]):
                        break
                    adx[k] = (adx[k - 1] * (n - 1) + dx[k]) / n

            target_idx = out.index[i:j]
            out.loc[target_idx, "plus_di"] = plus
            out.loc[target_idx, "minus_di"] = minus
            out.loc[target_idx, "adx"] = adx
        i = j
    return out


def make_adx_trades(bars: pd.DataFrame, symbol: str, timeframe: str) -> pd.DataFrame:
    h = bars.copy()
    eligible = h["bar_ok"].fillna(False) & h[["adx", "plus_di", "minus_di"]].notna().all(axis=1)
    long_sig = eligible & (h["adx"] >= THRESHOLD) & (h["plus_di"] > h["minus_di"])
    short_sig = eligible & (h["adx"] >= THRESHOLD) & (h["minus_di"] > h["plus_di"])
    direction = pd.Series(0, index=h.index, dtype="int8")
    direction[long_sig] = 1
    direction[short_sig] = -1

    rows: list[dict] = []
    next_free_entry_pos = -1
    idx = h.index
    for signal_pos, sig in enumerate(direction.to_numpy()):
        if sig == 0:
            continue
        entry_pos = signal_pos + 1
        exit_pos = entry_pos + HOLD_BARS
        if entry_pos <= next_free_entry_pos or exit_pos >= len(h):
            continue
        # Immediate next clock bar must be valid, and all four holding bars must be complete.
        if not bool(h["bar_ok"].iloc[entry_pos:exit_pos].fillna(False).all()):
            continue
        entry_t, exit_t = idx[entry_pos], idx[exit_pos]
        if exit_t >= FORBIDDEN_START:
            continue
        entry_px = float(h["open"].iloc[entry_pos])
        exit_px = float(h["open"].iloc[exit_pos])
        if not (math.isfinite(entry_px) and math.isfinite(exit_px) and entry_px > 0 and exit_px > 0):
            continue
        gross = float(sig * math.log(exit_px / entry_px) * 10000.0)
        rows.append({
            "symbol": symbol,
            "timeframe": timeframe,
            "signal_time": idx[signal_pos],
            "entry_time": entry_t,
            "exit_time": exit_t,
            "direction": int(sig),
            "entry_price": entry_px,
            "exit_price": exit_px,
            "signal_adx": float(h["adx"].iloc[signal_pos]),
            "signal_plus_di": float(h["plus_di"].iloc[signal_pos]),
            "signal_minus_di": float(h["minus_di"].iloc[signal_pos]),
            "gross_bps": gross,
            "net10_bps": gross - BASE_COST_BPS,
            "net14_bps": gross - STRESS_COST_BPS,
        })
        next_free_entry_pos = exit_pos - 1
    return pd.DataFrame(rows)


def evaluate_phase(months: list[str], phase: str, provenance: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    tf_trades: dict[str, list[pd.DataFrame]] = {"1H": [], "4H": []}
    coverage: dict[str, dict] = {}
    for symbol in SYMBOLS:
        minute = load_symbol_phase(symbol, months, phase, provenance)
        coverage[symbol] = {"minute_rows": int(len(minute))}
        for tf in ("1H", "4H"):
            bars = add_wilder_adx(aggregate_exact(minute, tf))
            trades = make_adx_trades(bars, symbol, tf)
            coverage[symbol][tf] = {
                "bars": int(len(bars)),
                "valid_bars": int(bars["bar_ok"].sum()),
                "adx_eligible_bars": int(bars["adx"].notna().sum()),
                "trades": int(len(trades)),
            }
            print(
                f"[{phase}] {symbol} {tf}: valid_bars={coverage[symbol][tf]['valid_bars']} "
                f"adx_eligible={coverage[symbol][tf]['adx_eligible_bars']} trades={len(trades)}",
                flush=True,
            )
            if len(trades):
                tf_trades[tf].append(trades)

    def combine(parts: list[pd.DataFrame]) -> pd.DataFrame:
        if not parts:
            return pd.DataFrame()
        t = pd.concat(parts, ignore_index=True)
        for c in ["signal_time", "entry_time", "exit_time"]:
            t[c] = pd.to_datetime(t[c], utc=True)
        return t.sort_values(["entry_time", "symbol"]).reset_index(drop=True)

    return combine(tf_trades["1H"]), combine(tf_trades["4H"]), coverage


def assert_freeze(freeze: dict) -> None:
    if freeze.get("experiment_id") != "CIGL-ADX-01":
        raise RuntimeError("ADX freeze identity mismatch")
    adx = freeze.get("adx", {})
    if adx.get("style") != "Wilder" or adx.get("length") != 14 or adx.get("threshold") != 25.0:
        raise RuntimeError("ADX frozen parameters mismatch")
    ex = freeze.get("execution", {})
    if ex.get("holding_bars") != 4 or ex.get("base_roundtrip_cost_bps") != 10.0 or ex.get("stress_roundtrip_cost_bps") != 14.0:
        raise RuntimeError("ADX frozen execution mismatch")
    gate = freeze.get("phase_gates", {}).get("discovery_1h", {})
    if gate.get("min_trades") != 300 or gate.get("net10_mean_bps_gt") != 0.0 or gate.get("profit_factor_gt") != 1.0:
        raise RuntimeError("ADX frozen Discovery gate mismatch")


def write_summary(path: Path, closeout: dict) -> None:
    p = closeout["discovery_1h_summary"]
    r = closeout["discovery_4h_robustness_summary"]
    lines = [
        "# CIGL-ADX-01 — CLOSEOUT", "",
        f"Status: **{closeout['status']}**", "",
        "## Primary Discovery 1H — 2022–2023",
        f"- Trades: {p.get('n')}",
        f"- Gross mean: {p.get('gross_mean_bps')} bps",
        f"- NET10 mean: {p.get('net10_mean_bps')} bps",
        f"- NET14 mean: {p.get('net14_mean_bps')} bps",
        f"- PF NET10: {p.get('pf_net10')}",
        f"- Gate pass: {closeout['discovery_1h_gate']['pass']}", "",
        "## Predeclared 4H robustness — cannot rescue 1H",
        f"- Trades: {r.get('n')}",
        f"- NET10 mean: {r.get('net10_mean_bps')} bps",
        f"- PF NET10: {r.get('pf_net10')}", "",
        f"2024 opened: **{closeout['opened_2024']}**",
        "2025 accessed: **False**",
        "2026 accessed: **False**",
    ]
    if closeout.get("validation_1h_summary"):
        v = closeout["validation_1h_summary"]
        lines += [
            "", "## 2024 Internal OOS — primary 1H",
            f"- Trades: {v.get('n')}",
            f"- NET10 mean: {v.get('net10_mean_bps')} bps",
            f"- PF NET10: {v.get('pf_net10')}",
            f"- Gate pass: {closeout['validation_1h_gate']['pass']}",
        ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--freeze", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    freeze_bytes = args.freeze.read_bytes()
    freeze = json.loads(freeze_bytes)
    assert_freeze(freeze)

    provenance: list[dict] = []
    d1, d4, coverage_d = evaluate_phase(DISCOVERY_MONTHS, "DISCOVERY", provenance)
    d1.to_csv(args.out / "CIGL_ADX_01_DISCOVERY_1H_TRADES.csv", index=False)
    d4.to_csv(args.out / "CIGL_ADX_01_DISCOVERY_4H_ROBUSTNESS_TRADES.csv", index=False)
    d1sum = summarize(d1)
    d4sum = summarize(d4)
    dgate = discovery_gate(d1sum)

    opened_2024 = bool(dgate["pass"])
    v1sum = None
    v4sum = None
    vgate = None
    coverage_v = None
    if opened_2024:
        print("ADX DISCOVERY 1H PASS — opening frozen 2024 once", flush=True)
        v1, v4, coverage_v = evaluate_phase(VALIDATION_MONTHS, "VALIDATION_2024", provenance)
        v1.to_csv(args.out / "CIGL_ADX_01_VALIDATION_2024_1H_TRADES.csv", index=False)
        v4.to_csv(args.out / "CIGL_ADX_01_VALIDATION_2024_4H_ROBUSTNESS_TRADES.csv", index=False)
        v1sum = summarize(v1)
        v4sum = summarize(v4)
        vgate = validation_gate(v1sum)
        status = "MVE_1_REPLICATION_READY" if vgate["pass"] else "OOS_FAIL_ADX_CLOSED"
    else:
        print("ADX DISCOVERY 1H FAIL — 2024 remains unopened", flush=True)
        status = "DISCOVERY_FAIL_ADX_CLOSED"

    closeout = json_safe({
        "lab": "CLASSIC_INDICATORS_GAP_LAB_V0.1",
        "experiment_id": "CIGL-ADX-01",
        "status": status,
        "implementation_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "parameters": {"style": "Wilder", "length": 14, "threshold": 25.0},
        "data_source": "Binance Data Vision USD-M Futures monthly 1m klines",
        "discovery_1h_summary": d1sum,
        "discovery_1h_gate": dgate,
        "discovery_4h_robustness_summary": d4sum,
        "opened_2024": opened_2024,
        "validation_1h_summary": v1sum,
        "validation_1h_gate": vgate,
        "validation_4h_robustness_summary": v4sum,
        "coverage_discovery": coverage_d,
        "coverage_validation": coverage_v,
        "accessed_2025": False,
        "accessed_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
        "threshold_changed_after_outcome": False,
        "robustness_4h_can_rescue_1h": False,
    })
    (args.out / "CIGL_ADX_01_CLOSEOUT.json").write_text(json.dumps(closeout, indent=2, sort_keys=True), encoding="utf-8")
    (args.out / "CIGL_ADX_01_DATA_PROVENANCE.json").write_text(json.dumps(json_safe(provenance), indent=2, sort_keys=True), encoding="utf-8")
    write_summary(args.out / "CIGL_ADX_01_SUMMARY.md", closeout)
    print(json.dumps(closeout, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

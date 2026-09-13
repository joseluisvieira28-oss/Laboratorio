#!/usr/bin/env python3
"""MVE-ICHIMOKU4H-01 — prospective one-shot 2024 OOS runner.

Research only. New hypothesis generated from the predeclared 4H diagnostic of
CIGL-ICHIMOKU-01. The failed 1H parent remains immutable. This runner reads
2024 only, evaluates 4H only, never opens 2025/2026 and never mutates an
exchange. No post-outcome tuning or rerun is permitted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from classic_indicators_gap_v01 import SYMBOLS, VALIDATION_MONTHS, summarize, validation_gate
from classic_indicators_gap_vwap_data_vision_v01 import load_symbol_phase, json_safe
from classic_indicators_gap_ichimoku_v01 import aggregate_exact, add_ichimoku, make_trades

EXPERIMENT = "MVE-ICHIMOKU4H-01"
PARENT = "CIGL-ICHIMOKU-01"
TF = "4H"


def assert_freeze(f: dict) -> None:
    if f.get("experiment_id") != EXPERIMENT:
        raise RuntimeError("MVE Ichimoku4H identity mismatch")
    if f.get("parent_experiment_id") != PARENT:
        raise RuntimeError("parent lineage mismatch")
    if f.get("parent_verdict_immutable") != "DISCOVERY_FAIL_ICHIMOKU_CLOSED":
        raise RuntimeError("parent verdict immutability mismatch")
    md = f.get("market_data", {})
    if md.get("oos") != "2024" or md.get("protected_final_holdout") != "2025" or md.get("locked_from") != "2026":
        raise RuntimeError("sample firewall mismatch")
    if md.get("symbols") != SYMBOLS:
        raise RuntimeError("symbol universe mismatch")
    s = f.get("ichimoku", {})
    if s.get("timeframe") != TF:
        raise RuntimeError("timeframe mismatch")
    if (s.get("tenkan_period"), s.get("kijun_period"), s.get("senkou_b_period"), s.get("displacement")) != (9, 26, 52, 26):
        raise RuntimeError("Ichimoku 9/26/52/26 mismatch")
    if s.get("chikou_used") is not False or s.get("tenkan_kijun_confirmation") is not False or s.get("cloud_color_filter") is not False:
        raise RuntimeError("forbidden confirmation mismatch")
    e = f.get("execution", {})
    if e.get("holding_bars") != 4 or e.get("base_roundtrip_cost_bps") != 10.0 or e.get("stress_roundtrip_cost_bps") != 14.0:
        raise RuntimeError("execution mismatch")
    g = f.get("oos_gate", {})
    if g.get("min_trades") != 150 or g.get("net10_mean_bps_gt") != 0.0 or g.get("profit_factor_gt") != 1.0:
        raise RuntimeError("OOS economic gate mismatch")
    if g.get("max_single_asset_positive_pnl_share_lte") != 0.70 or g.get("max_single_quarter_positive_pnl_share_lte") != 0.70:
        raise RuntimeError("OOS concentration gate mismatch")
    fw = f.get("firewall", {})
    required_false = ("open_2025", "open_2026", "live_trading", "exchange_mutation", "merge_main", "outcome_driven_rerun")
    if any(fw.get(k) is not False for k in required_false):
        raise RuntimeError("firewall mismatch")
    if fw.get("open_2024_exactly_once") is not True:
        raise RuntimeError("one-shot OOS mismatch")


def self_test(freeze: dict) -> None:
    assert_freeze(freeze)
    n = 210
    ix = pd.date_range("2020-01-01", periods=n, freq="4h", tz="UTC")
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
    # Senkou B needs 52 bars, then the visible cloud is displaced by 26 bars.
    if out["cloud_top"].iloc[:77].notna().any() or not math.isfinite(float(out["cloud_top"].iloc[77])):
        raise RuntimeError("first-segment displacement warmup failed")
    if not math.isclose(float(out["visible_senkou_a"].iloc[77]), float(out["raw_senkou_a"].iloc[51]), rel_tol=0, abs_tol=1e-12):
        raise RuntimeError("Senkou A displacement failed")
    if not math.isclose(float(out["visible_senkou_b"].iloc[77]), float(out["raw_senkou_b"].iloc[51]), rel_tol=0, abs_tol=1e-12):
        raise RuntimeError("Senkou B displacement failed")
    # Gap at 100 must reset the whole state; fresh segment begins at 101.
    if out["cloud_top"].iloc[100:178].notna().any() or not math.isfinite(float(out["cloud_top"].iloc[178])):
        raise RuntimeError("gap-reset displacement failed")
    if int(out["signal"].iloc[77]) != 0 or int(out["signal"].iloc[178]) != 0:
        raise RuntimeError("first eligible cloud bar signalled without eligible predecessor")
    print("MVE-ICHIMOKU4H-01 deterministic self-test: PASS", flush=True)


def combine(parts: list[pd.DataFrame]) -> pd.DataFrame:
    if not parts:
        return pd.DataFrame()
    t = pd.concat(parts, ignore_index=True)
    for c in ("signal_time", "entry_time", "exit_time"):
        t[c] = pd.to_datetime(t[c], utc=True)
    return t.sort_values(["entry_time", "symbol"]).reset_index(drop=True)


def run_oos() -> tuple[pd.DataFrame, dict, list]:
    provenance: list = []
    parts: list[pd.DataFrame] = []
    coverage: dict = {}
    for symbol in SYMBOLS:
        minute = load_symbol_phase(symbol, VALIDATION_MONTHS, "MVE_ICHIMOKU4H_01_OOS_2024", provenance)
        bars = add_ichimoku(aggregate_exact(minute, TF))
        trades = make_trades(bars, symbol, TF)
        coverage[symbol] = {
            "minute_rows": int(len(minute)),
            "valid_4h_bars": int(bars["bar_ok"].sum()),
            "cloud_eligible_4h_bars": int((bars["cloud_top"].notna() & bars["cloud_bottom"].notna()).sum()),
            "signals": int((bars["signal"] != 0).sum()),
            "trades": int(len(trades)),
        }
        print(
            f"[OOS_2024] {symbol}: minute_rows={len(minute)} valid4h={coverage[symbol]['valid_4h_bars']} "
            f"cloud={coverage[symbol]['cloud_eligible_4h_bars']} signals={coverage[symbol]['signals']} trades={len(trades)}",
            flush=True,
        )
        if len(trades):
            parts.append(trades)
    return combine(parts), coverage, provenance


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", type=Path, required=True)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    freeze_bytes = args.freeze.read_bytes()
    freeze = json.loads(freeze_bytes)
    assert_freeze(freeze)
    if args.self_test:
        self_test(freeze)
        return
    if args.out is None:
        raise SystemExit("--out required unless --self-test")

    args.out.mkdir(parents=True, exist_ok=True)
    trades, coverage, provenance = run_oos()
    trades_path = args.out / "MVE_ICHIMOKU4H_01_OOS_2024_TRADES.csv"
    trades.to_csv(trades_path, index=False)
    metrics = summarize(trades)
    gate = validation_gate(metrics)
    status = "MVE_2_OOS_POSITIVE" if gate["pass"] else "MVE_CLOSED_NO_EDGE"

    parent_impl = Path(__file__).with_name("classic_indicators_gap_ichimoku_v01.py")
    closeout = json_safe({
        "program": "MVE_HUNT_V0.1",
        "experiment_id": EXPERIMENT,
        "parent_experiment_id": PARENT,
        "parent_verdict_immutable": "DISCOVERY_FAIL_ICHIMOKU_CLOSED",
        "status": status,
        "oos_period": "2024",
        "timeframe": TF,
        "implementation_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "reused_parent_implementation_sha256": hashlib.sha256(parent_impl.read_bytes()).hexdigest(),
        "parameters": {
            "tenkan_period": 9,
            "kijun_period": 26,
            "senkou_b_period": 52,
            "displacement": 26,
            "signal": "visible_cloud_breakout_only",
            "holding_bars": 4,
            "base_roundtrip_cost_bps": 10.0,
            "stress_roundtrip_cost_bps": 14.0,
        },
        "oos_2024_summary": metrics,
        "oos_gate": gate,
        "coverage": coverage,
        "provenance": provenance,
        "opened_2024": True,
        "accessed_2025": False,
        "accessed_2026": False,
        "post_result_parameter_change": False,
        "outcome_driven_rerun": False,
        "live_trading": False,
        "exchange_mutation": False,
        "merge_main": False,
    })
    (args.out / "MVE_ICHIMOKU4H_01_CLOSEOUT.json").write_text(
        json.dumps(closeout, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    summary = [
        "# MVE-ICHIMOKU4H-01 — OOS 2024 CLOSEOUT",
        "",
        f"Status: {status}",
        f"N: {metrics.get('n')}",
        f"Gross mean bps: {metrics.get('gross_mean_bps')}",
        f"NET10 mean bps: {metrics.get('net10_mean_bps')}",
        f"NET14 mean bps: {metrics.get('net14_mean_bps')}",
        f"PF NET10: {metrics.get('pf_net10')}",
        f"OOS gate pass: {gate.get('pass')}",
        "2025 accessed: false",
        "2026 accessed: false",
        "Live trading: false",
        "Exchange mutation: false",
        "",
        "The failed 1H parent remains immutable. A PASS is MVE-2 only and does not authorize live trading.",
    ]
    (args.out / "MVE_ICHIMOKU4H_01_CLOSEOUT.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    print(json.dumps(closeout, indent=2, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()

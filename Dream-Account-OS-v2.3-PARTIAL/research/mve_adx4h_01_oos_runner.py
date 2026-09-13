#!/usr/bin/env python3
"""MVE-ADX4H-01 — one-shot independent 2024 OOS replication.

This runner never reads 2022-2023 outcomes and never requests 2025+. It applies
exactly the unchanged six-asset 4H Wilder-14 / ADX>=25 rule frozen after the
predeclared CIGL-ADX-01 4H diagnostic was observed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from classic_indicators_gap_v01 import SYMBOLS, VALIDATION_MONTHS, summarize, validation_gate
from classic_indicators_gap_vwap_data_vision_v01 import load_symbol_phase, json_safe
from classic_indicators_gap_adx_v01 import aggregate_exact, add_wilder_adx, make_adx_trades


def assert_freeze(f: dict) -> None:
    if f.get("hypothesis_id") != "MVE-ADX4H-01":
        raise RuntimeError("Hypothesis identity mismatch")
    if f.get("independent_oos") != "2024-01-01T00:00:00Z/2024-12-31T23:59:59Z":
        raise RuntimeError("OOS block mismatch")
    if f.get("universe") != SYMBOLS:
        raise RuntimeError("Frozen universe mismatch")
    adx = f.get("adx", {})
    if adx.get("style") != "Wilder" or adx.get("length") != 14 or adx.get("threshold") != 25.0:
        raise RuntimeError("Frozen ADX semantics mismatch")
    bars = f.get("bars", {})
    if bars.get("timeframe") != "4H" or bars.get("minutes_required") != 240 or bars.get("adx_state_after_invalid_bar") != "RESET":
        raise RuntimeError("Frozen bar semantics mismatch")
    ex = f.get("execution", {})
    if ex.get("holding_bars") != 4 or ex.get("base_roundtrip_cost_bps") != 10.0 or ex.get("stress_roundtrip_cost_bps") != 14.0:
        raise RuntimeError("Frozen execution/cost mismatch")
    gate = f.get("oos_pass_gate", {})
    if gate.get("min_trades") != 150 or gate.get("net10_mean_bps_gt") != 0.0 or gate.get("pf_net10_gt") != 1.0:
        raise RuntimeError("Frozen OOS gate mismatch")
    if gate.get("max_single_asset_positive_pnl_share") != 0.70 or gate.get("max_single_quarter_positive_pnl_share") != 0.70:
        raise RuntimeError("Frozen concentration gate mismatch")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    freeze_bytes = args.freeze.read_bytes()
    freeze = json.loads(freeze_bytes)
    assert_freeze(freeze)

    provenance: list[dict] = []
    trades_parts = []
    coverage = {}
    for symbol in SYMBOLS:
        minute = load_symbol_phase(symbol, VALIDATION_MONTHS, "MVE_ADX4H_OOS_2024", provenance)
        bars = add_wilder_adx(aggregate_exact(minute, "4H"))
        t = make_adx_trades(bars, symbol, "4H")
        coverage[symbol] = {
            "minute_rows": int(len(minute)),
            "bars": int(len(bars)),
            "valid_bars": int(bars["bar_ok"].sum()),
            "adx_eligible_bars": int(bars["adx"].notna().sum()),
            "trades": int(len(t)),
        }
        print(
            f"[OOS2024] {symbol}: rows={len(minute)} valid_4h={coverage[symbol]['valid_bars']} "
            f"adx_eligible={coverage[symbol]['adx_eligible_bars']} trades={len(t)}",
            flush=True,
        )
        if len(t):
            trades_parts.append(t)

    if trades_parts:
        trades = pd.concat(trades_parts, ignore_index=True)
        for c in ["signal_time", "entry_time", "exit_time"]:
            trades[c] = pd.to_datetime(trades[c], utc=True)
        trades = trades.sort_values(["entry_time", "symbol"]).reset_index(drop=True)
    else:
        trades = pd.DataFrame()

    trades.to_csv(args.out / "MVE_ADX4H_01_OOS_2024_TRADES.csv", index=False)
    summary = summarize(trades)
    gate = validation_gate(summary)
    status = "MVE_2_OOS_POSITIVE" if gate["pass"] else "OOS_FAIL_CLOSE_PERMANENTLY"
    closeout = json_safe({
        "hypothesis_id": "MVE-ADX4H-01",
        "status": status,
        "action_freeze_sha256": hashlib.sha256(freeze_bytes).hexdigest(),
        "sample": "2024-01-01T00:00:00Z/2024-12-31T23:59:59Z",
        "summary": summary,
        "oos_gate": gate,
        "coverage": coverage,
        "data_source": "Binance Data Vision USD-M Futures monthly 1m klines",
        "accessed_2022_2023_by_this_runner": False,
        "accessed_2025": False,
        "accessed_2026": False,
        "live_trading": False,
        "exchange_mutation": False,
        "post_oos_parameter_change": False
    })
    (args.out / "MVE_ADX4H_01_OOS_CLOSEOUT.json").write_text(json.dumps(closeout, indent=2, sort_keys=True), encoding="utf-8")
    (args.out / "MVE_ADX4H_01_OOS_DATA_PROVENANCE.json").write_text(json.dumps(json_safe(provenance), indent=2, sort_keys=True), encoding="utf-8")
    lines = [
        "# MVE-ADX4H-01 — 2024 OOS CLOSEOUT", "",
        f"Status: **{status}**", "",
        f"Trades: {summary.get('n')}",
        f"Gross mean: {summary.get('gross_mean_bps')} bps",
        f"NET10 mean: {summary.get('net10_mean_bps')} bps",
        f"NET14 mean: {summary.get('net14_mean_bps')} bps",
        f"PF NET10: {summary.get('pf_net10')}",
        f"Gate pass: {gate['pass']}", "",
        "2025 accessed: False",
        "2026 accessed: False",
        "Live trading: False",
    ]
    (args.out / "MVE_ADX4H_01_OOS_SUMMARY.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(closeout, indent=2, sort_keys=True), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

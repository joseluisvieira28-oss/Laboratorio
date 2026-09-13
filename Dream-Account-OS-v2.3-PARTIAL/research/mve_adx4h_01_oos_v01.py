#!/usr/bin/env python3
from __future__ import annotations

"""MVE-ADX4H-01 — frozen one-shot 2024 OOS runner.

This runner is a new replication harness only. It imports the already frozen
CIGL ADX implementation and common evaluation code byte-for-byte, acquires
ONLY the authorized 2024 Binance USD-M Futures monthly 1m corpus, evaluates
ONLY the frozen 4H rule, and never opens 2025 or 2026.
"""

import argparse
import json
import math
from pathlib import Path

import pandas as pd

import cigl_adx_01_action_v01 as adx
import classic_indicators_gap_v01 as common

EXPERIMENT = "MVE-ADX4H-01"
FREEZE_DRIVE_ID = "1mgNZ1Wve4biSN-xUYGAGti_ShF84m_KERICAgmEEDpg"
SOURCE_BRANCH_HEAD = "61205c7fa207c5705d275e89a92cb1e235c6d223"
COMMON_BLOB = "21398ba193d10d465c10b392e1dc8461270a0491"
PROTOCOL_BLOB = "0ac36b01d682064576b6d1279d26a1d7056c780f"
ADX_RUNNER_BLOB = "bd8cd57e3ea7b25df1eab5a4c8c80fbe7fd5694c"
MIN_TRADES = 150
MAX_POSITIVE_PNL_SHARE = 0.70


def _pf(values: pd.Series) -> float | None:
    pos = float(values[values > 0].sum())
    neg = float(-values[values < 0].sum())
    if neg == 0:
        return None if pos == 0 else float("inf")
    return pos / neg


def _max_cum_drawdown(values: pd.Series) -> float | None:
    if values.empty:
        return None
    eq = values.cumsum()
    return float((eq - eq.cummax()).min())


def _bootstrap_day_mean(trades: pd.DataFrame, reps: int = 5000, seed: int = 20260913) -> dict | None:
    import numpy as np
    if trades.empty:
        return None
    d = trades.copy()
    d["day"] = d["entry_time"].dt.floor("D")
    agg = d.groupby("day")["net10_bps"].agg(["sum", "count"])
    if len(agg) < 2:
        return None
    arr = agg[["sum", "count"]].to_numpy(float)
    rng = np.random.default_rng(seed)
    vals = np.empty(reps, dtype=float)
    for i in range(reps):
        sample = arr[rng.integers(0, len(arr), size=len(arr))].sum(axis=0)
        vals[i] = sample[0] / sample[1]
    return {
        "reps": reps,
        "seed": seed,
        "mean_bps": float(vals.mean()),
        "ci95_low_bps": float(np.quantile(vals, 0.025)),
        "ci95_high_bps": float(np.quantile(vals, 0.975)),
    }


def summarize(trades: pd.DataFrame) -> dict:
    if trades.empty:
        return {"n": 0}
    t = trades.sort_values(["entry_time", "symbol"]).copy()
    pos = t["net10_bps"].clip(lower=0)
    total_positive = float(pos.sum())

    per_asset = {}
    for symbol, g in t.groupby("symbol"):
        per_asset[symbol] = {
            "n": int(len(g)),
            "gross_mean_bps": float(g["gross_bps"].mean()),
            "net10_mean_bps": float(g["net10_bps"].mean()),
            "net14_mean_bps": float(g["net14_bps"].mean()),
            "pf_net10": _pf(g["net10_bps"]),
        }

    tq = t.assign(quarter=t["entry_time"].dt.to_period("Q").astype(str))
    quarterly = {}
    for q, g in tq.groupby("quarter"):
        quarterly[q] = {
            "n": int(len(g)),
            "net10_mean_bps": float(g["net10_bps"].mean()),
            "positive_net10_pnl_bps": float(g["net10_bps"].clip(lower=0).sum()),
        }

    by_asset_positive = t.assign(positive=pos).groupby("symbol")["positive"].sum()
    by_quarter_positive = tq.assign(positive=tq["net10_bps"].clip(lower=0)).groupby("quarter")["positive"].sum()
    max_asset_share = None if total_positive <= 0 else float(by_asset_positive.max() / total_positive)
    max_quarter_share = None if total_positive <= 0 else float(by_quarter_positive.max() / total_positive)

    loo = {}
    for symbol in adx.SYMBOLS:
        g = t[t["symbol"] != symbol]
        if not g.empty:
            loo[symbol] = float(g["net10_bps"].mean())

    return {
        "n": int(len(t)),
        "gross_mean_bps": float(t["gross_bps"].mean()),
        "gross_median_bps": float(t["gross_bps"].median()),
        "net10_mean_bps": float(t["net10_bps"].mean()),
        "net10_median_bps": float(t["net10_bps"].median()),
        "net14_mean_bps": float(t["net14_bps"].mean()),
        "net14_median_bps": float(t["net14_bps"].median()),
        "pf_net10": _pf(t["net10_bps"]),
        "win_rate_net10": float((t["net10_bps"] > 0).mean()),
        "cumulative_net10_bps": float(t["net10_bps"].sum()),
        "max_cumulative_drawdown_net10_bps": _max_cum_drawdown(t["net10_bps"]),
        "positive_trade_fraction": float((t["net10_bps"] > 0).mean()),
        "per_asset": per_asset,
        "quarterly": quarterly,
        "leave_one_asset_out_net10_mean_bps": loo,
        "bootstrap_day_net10_mean": _bootstrap_day_mean(t),
        "max_asset_positive_pnl_share": max_asset_share,
        "max_quarter_positive_pnl_share": max_quarter_share,
    }


def gate(metrics: dict) -> dict:
    pf = metrics.get("pf_net10")
    asset_share = metrics.get("max_asset_positive_pnl_share")
    quarter_share = metrics.get("max_quarter_positive_pnl_share")
    checks = {
        "n_ge_150": metrics.get("n", 0) >= MIN_TRADES,
        "pooled_net10_mean_gt_0": metrics.get("net10_mean_bps", -math.inf) > 0,
        "pf_net10_gt_1": pf is not None and pf > 1.0,
        "max_asset_positive_pnl_share_le_0_70": asset_share is not None and asset_share <= MAX_POSITIVE_PNL_SHARE,
        "max_quarter_positive_pnl_share_le_0_70": quarter_share is not None and quarter_share <= MAX_POSITIVE_PNL_SHARE,
    }
    return {"checks": checks, "pass": all(checks.values())}


def run(work: Path) -> dict:
    normalized_dir = work / "normalized_2024"
    outputs = work / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)

    acquisition = adx.acquire_phase(
        normalized_dir,
        "VALIDATION_2024",
        adx.VALIDATION_YMS,
        append=False,
    )

    all_trades = []
    audits = []
    for symbol in adx.SYMBOLS:
        minute, audit = common.load_symbol(
            normalized_dir,
            symbol,
            adx.VALIDATION_YMS,
            common.FORBIDDEN_START,
        )
        audits.append(audit.__dict__)
        h4 = adx.hourly_ohlc(minute, "4h")
        trades = adx.make_trades(h4, symbol, "4h")
        if not trades.empty:
            all_trades.append(trades)

    trades = pd.concat(all_trades, ignore_index=True) if all_trades else pd.DataFrame()
    metrics = summarize(trades)
    decision = gate(metrics)
    classification = "MVE-2 OOS POSITIVE" if decision["pass"] else "MVE_CLOSED_NO_EDGE"

    closeout = {
        "experiment": EXPERIMENT,
        "status": "COMPLETE_ONE_SHOT_2024_OOS",
        "freeze_drive_id": FREEZE_DRIVE_ID,
        "source_branch_head": SOURCE_BRANCH_HEAD,
        "frozen_source_blobs": {
            "classic_indicators_gap_v01.py": COMMON_BLOB,
            "CLASSIC_INDICATORS_GAP_LAB_V01_PROTOCOL.json": PROTOCOL_BLOB,
            "cigl_adx_01_action_v01.py": ADX_RUNNER_BLOB,
        },
        "source": "Official Binance USD-M Futures monthly 1m archives",
        "window": {"start": "2024-01-01T00:00:00Z", "end": "2025-01-01T00:00:00Z"},
        "timeframe": "4H",
        "universe": adx.SYMBOLS,
        "rule": {
            "indicator": "Wilder ADX/DMI",
            "length": 14,
            "threshold": 25,
            "long": "ADX>=25 and +DI>-DI",
            "short": "ADX>=25 and -DI>+DI",
            "entry": "next 4H bar open",
            "exit": "open four completed 4H bars after entry",
            "one_same_asset_position_at_a_time": True,
            "base_round_trip_cost_bps": 10.0,
            "stress_round_trip_cost_bps": 14.0,
        },
        "acquisition": acquisition,
        "audits": audits,
        "metrics": metrics,
        "frozen_gate": decision,
        "classification": classification,
        "locks": {
            "2025_opened": False,
            "2026_opened": False,
            "live_trading": False,
            "exchange_mutation": False,
            "main_merge": False,
            "render_deploy": False,
        },
    }

    (outputs / "MVE_ADX4H_01_OOS_2024_CLOSEOUT.json").write_text(
        json.dumps(closeout, indent=2, sort_keys=True), encoding="utf-8"
    )
    if not trades.empty:
        trades.to_csv(outputs / "MVE_ADX4H_01_OOS_2024_TRADES.csv", index=False)

    print("MVE_ADX4H_OOS_CLOSEOUT_JSON=" + json.dumps(closeout, sort_keys=True), flush=True)
    return closeout


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--work", type=Path, required=True)
    args = ap.parse_args()
    result = run(args.work)
    if result["classification"] == "MVE_CLOSED_NO_EDGE":
        print("MVE-ADX4H-01 2024 OOS: CLOSED_NO_EDGE", flush=True)
    else:
        print("MVE-ADX4H-01 2024 OOS: MVE-2 OOS POSITIVE", flush=True)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""OPTIONS-SPOTPERP-001 V2.1 — frozen causal risk-scaling development runner.

Research-only. Reads only already-acquired 2021-04-01..2024-12-31 source bytes.
Never requests network data and never opens 2025 or 2026.
No parameter search or rescue is implemented.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import math
import statistics
import zipfile
from pathlib import Path
from typing import Any

from discovery_runner_v01 import (
    AUTHORITY_SHA256,
    END,
    START,
    build_signal,
    load_and_bind_receipt,
    load_source_manifest,
    sha256_file,
)

LAB_ID = "OPTIONS-SPOTPERP-001"
VERSION = "V2.1"
BASE_COST_BPS = 10.0
STRESS_COST_BPS = 20.0
RV_WINDOW = 20
MIN_RV_HISTORY = 60
UTC = dt.timezone.utc


def load_btc_daily(root: Path, receipt: dict[str, Any]) -> dict[dt.date, dict[str, float]]:
    out: dict[dt.date, dict[str, float]] = {}
    entries = receipt.get("btc_price_raw_archives", [])
    if len(entries) != 45:
        raise RuntimeError(f"expected 45 BTC monthly archives, got {len(entries)}")
    bdir = root / "raw_binance_btcusdt_1d"
    for e in entries:
        name = str(e["file"])
        if "2025" in name or "2026" in name:
            raise RuntimeError("protected BTC archive referenced")
        p = bdir / name
        if not p.exists() or sha256_file(p) != e.get("sha256"):
            raise RuntimeError(f"BTC archive integrity failure: {name}")
        with zipfile.ZipFile(p) as zf:
            members = [n for n in zf.namelist() if not n.endswith("/")]
            if len(members) != 1:
                raise RuntimeError(f"unexpected BTC ZIP members: {name}")
            with zf.open(members[0]) as raw:
                for row in csv.reader(io.TextIOWrapper(raw, encoding="utf-8", newline="")):
                    if not row:
                        continue
                    ms = int(row[0])
                    day = dt.datetime.fromtimestamp(ms / 1000, tz=UTC).date()
                    if day < START or day > END:
                        raise RuntimeError(f"BTC row outside frozen window: {day}")
                    op = float(row[1]); cl = float(row[4])
                    if not all(math.isfinite(x) and x > 0 for x in (op, cl)):
                        raise RuntimeError(f"invalid BTC OHLC on {day}")
                    if day in out:
                        raise RuntimeError(f"duplicate BTC day {day}")
                    out[day] = {"open": op, "close": cl}
    return out


def rv20_series(btc: dict[dt.date, dict[str, float]]) -> dict[dt.date, float]:
    days = sorted(btc)
    rets: list[tuple[dt.date, float]] = []
    for i in range(1, len(days)):
        d0, d1 = days[i-1], days[i]
        if (d1-d0).days != 1:
            raise RuntimeError(f"BTC daily continuity failure: {d0} -> {d1}")
        r = math.log(btc[d1]["close"] / btc[d0]["close"])
        rets.append((d1, r))
    out: dict[dt.date, float] = {}
    for i in range(RV_WINDOW-1, len(rets)):
        sample = [rets[j][1] for j in range(i-RV_WINDOW+1, i+1)]
        rv = statistics.stdev(sample)
        if not math.isfinite(rv) or rv <= 0:
            raise RuntimeError(f"invalid RV20 on {rets[i][0]}")
        out[rets[i][0]] = float(rv)
    return out


def causal_weights(rv: dict[dt.date, float]) -> dict[dt.date, float]:
    out: dict[dt.date, float] = {}
    history: list[float] = []
    for day in sorted(rv):
        x = rv[day]
        history.append(x)
        if len(history) < MIN_RV_HISTORY:
            continue
        baseline = float(statistics.median(history))
        w = min(1.0, baseline / x)
        if not math.isfinite(w) or w <= 0 or w > 1.0:
            raise RuntimeError(f"invalid causal weight on {day}: {w}")
        out[day] = w
    return out


def max_drawdown(net_logs: list[float]) -> float:
    wealth = peak = 1.0
    mdd = 0.0
    for r in net_logs:
        wealth *= math.exp(r)
        peak = max(peak, wealth)
        mdd = min(mdd, wealth / peak - 1.0)
    return mdd


def metrics(rows: list[dict[str, Any]], cost_bps: float) -> dict[str, Any]:
    entered = [r for r in rows if r["position"] != 0 and r["weight"] > 0]
    gross = [r["aligned_unscaled_gross_bps"] * r["weight"] for r in entered]
    cost = [cost_bps * r["weight"] for r in entered]
    net = [g-c for g,c in zip(gross,cost)]
    weights = [r["weight"] for r in entered]
    pos = sum(x for x in net if x > 0); neg = -sum(x for x in net if x < 0)
    pf = pos/neg if neg > 0 else (float("inf") if pos > 0 else 0.0)
    annual: dict[str, dict[str, Any]] = {}
    for y in (2021, 2022, 2023, 2024):
        rr = [r for r in entered if r["signal_date"].year == y]
        gv = [r["aligned_unscaled_gross_bps"]*r["weight"] for r in rr]
        nv = [g-cost_bps*r["weight"] for g,r in zip(gv,rr)]
        annual[str(y)] = {
            "n": len(rr),
            "mean_weight": sum(r["weight"] for r in rr)/len(rr) if rr else None,
            "gross_pnl_bps": sum(gv),
            "net_pnl_bps": sum(nv),
            "net_mean_bps": sum(nv)/len(nv) if nv else None,
        }
    positive_gross = {y:max(0.0,float(v["gross_pnl_bps"])) for y,v in annual.items()}
    total_positive = sum(positive_gross.values())
    concentration = max(positive_gross.values())/total_positive if total_positive > 0 else 1.0
    total_weight = sum(weights)
    return {
        "entered_scaled_trades": len(entered),
        "average_executed_notional": total_weight/len(weights) if weights else 0.0,
        "total_executed_notional_units": total_weight,
        "long_count": sum(1 for r in entered if r["position"] > 0),
        "short_count": sum(1 for r in entered if r["position"] < 0),
        "gross_mean_bps_per_parent_opportunity": sum(gross)/len(gross) if gross else None,
        "net_mean_bps_per_parent_opportunity": sum(net)/len(net) if net else None,
        "gross_bps_per_unit_executed_notional": sum(gross)/total_weight if total_weight else None,
        "net_bps_per_unit_executed_notional": sum(net)/total_weight if total_weight else None,
        "profit_factor": pf,
        "cumulative_net_return": math.exp(sum(x/10000.0 for x in net))-1.0 if net else 0.0,
        "max_drawdown": max_drawdown([x/10000.0 for x in net]),
        "win_rate": sum(1 for x in net if x > 0)/len(net) if net else None,
        "annual": annual,
        "single_year_max_share_of_total_positive_gross_pnl": concentration,
    }


def sanitize(x: Any) -> Any:
    if isinstance(x,float) and not math.isfinite(x): return None
    if isinstance(x,dict): return {k:sanitize(v) for k,v in x.items()}
    if isinstance(x,list): return [sanitize(v) for v in x]
    return x


def run(root: Path, output: Path) -> dict[str, Any]:
    freeze = json.loads((Path(__file__).with_name("RISK_SCALING_V21_FREEZE.json")).read_text(encoding="utf-8"))
    if freeze.get("status") != "FROZEN_PRE_OUTCOME":
        raise RuntimeError("V2.1 freeze not active")
    if freeze.get("parent_authority_sha256") != AUTHORITY_SHA256:
        raise RuntimeError("parent authority mismatch")
    if freeze.get("protected_periods") != {"2025":"LOCKED","2026":"LOCKED"}:
        raise RuntimeError("protected-period freeze mismatch")

    receipt = load_and_bind_receipt(root)
    manifest = load_source_manifest(root)
    signal, signal_audit = build_signal(root, manifest)
    btc = load_btc_daily(root, receipt)
    rv = rv20_series(btc)
    weights = causal_weights(rv)

    rows: list[dict[str, Any]] = []
    for day in sorted(signal):
        entry_day = day + dt.timedelta(days=1); exit_day = day + dt.timedelta(days=2)
        if entry_day > END or exit_day > END:
            continue
        if entry_day not in btc or exit_day not in btc:
            raise RuntimeError(f"missing BTC outcome price for {day}")
        skew = signal[day]
        pos = 1 if skew > 0 else (-1 if skew < 0 else 0)
        fwd = math.log(btc[exit_day]["open"] / btc[entry_day]["open"])
        w = float(weights.get(day, 0.0))
        rows.append({
            "signal_date": day,
            "skew": skew,
            "position": pos,
            "forward_log_return": fwd,
            "aligned_unscaled_gross_bps": pos*fwd*10000.0,
            "rv20": rv.get(day),
            "weight": w,
        })

    base = metrics(rows, BASE_COST_BPS); stress = metrics(rows, STRESS_COST_BPS)
    nonnegative_years = sum(1 for v in base["annual"].values() if v["n"] > 0 and v["net_mean_bps"] is not None and v["net_mean_bps"] >= 0)
    gates = {
        "A_provenance_leakage_pass": True,
        "B_scaled_trades_ge_300": base["entered_scaled_trades"] >= 300,
        "C_average_executed_notional_ge_0_40": base["average_executed_notional"] >= 0.40,
        "D_net10_mean_positive": (base["net_mean_bps_per_parent_opportunity"] or -1e99) > 0,
        "E_pf10_gt_1": base["profit_factor"] > 1.0,
        "F_cumulative_net10_return_gt_5pct": base["cumulative_net_return"] > 0.05,
        "G_max_drawdown_le_50pct": base["max_drawdown"] >= -0.50,
        "H_at_least_3_of_4_years_nonnegative": nonnegative_years >= 3,
        "I_no_single_year_gt_60pct_positive_gross_pnl": base["single_year_max_share_of_total_positive_gross_pnl"] <= 0.60,
    }
    survives = all(gates.values())
    result = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "classification": "RISK_SCALING_DEV_SURVIVES" if survives else "RISK_SCALING_DEV_FAIL",
        "freeze_drive_id": freeze["drive_freeze_id"],
        "parent_discovery_run_id": freeze["parent_discovery_run_id"],
        "parent_final_source_gate_run_id": freeze["parent_final_source_gate_run_id"],
        "parent_monthly_raw_run_id": freeze["parent_monthly_raw_run_id"],
        "window": freeze["window"],
        "source_signal_audit": signal_audit,
        "parent_evaluable_opportunities": len(rows),
        "base_10bps": base,
        "stress_20bps": stress,
        "nonnegative_years": nonnegative_years,
        "gates": gates,
        "holdout_2025_accessed": False,
        "year_2026_accessed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "notes": ["Development-only; survival does not itself promote to Tier 2.", "No post-outcome rescue is authorized."],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output/"OPTIONS_SPOTPERP_001_RISK_SCALING_V21_CLOSEOUT.json").write_text(json.dumps(sanitize(result),indent=2,sort_keys=True),encoding="utf-8")
    with (output/"OPTIONS_SPOTPERP_001_RISK_SCALING_V21_LEDGER.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f); w.writerow(["signal_date","skew","position","forward_log_return","aligned_unscaled_gross_bps","rv20","weight"])
        for r in rows:
            w.writerow([r["signal_date"].isoformat(),r["skew"],r["position"],r["forward_log_return"],r["aligned_unscaled_gross_bps"],r["rv20"],r["weight"]])
    return result


def main() -> int:
    ap=argparse.ArgumentParser(); ap.add_argument("--source-root",required=True); ap.add_argument("--output",required=True); args=ap.parse_args()
    result=run(Path(args.source_root).resolve(),Path(args.output).resolve())
    print(result["classification"]); print(json.dumps({"gates":result["gates"],"holdout_2025_accessed":False,"year_2026_accessed":False},sort_keys=True))
    return 0 if result["classification"]=="RISK_SCALING_DEV_SURVIVES" else 3

if __name__=="__main__": raise SystemExit(main())

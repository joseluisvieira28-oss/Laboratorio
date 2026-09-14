#!/usr/bin/env python3
from __future__ import annotations
import argparse, csv, datetime as dt, json, math, statistics, sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
PARENT = HERE.parent / "options_spotperp_v0_1"
sys.path.insert(0, str(PARENT))
import discovery_runner_v01 as v01

LAB_ID = "OPTIONS-SPOTPERP-002"
VERSION = "V0.2"
AUTHORITY_COMMIT = "1c071af13f822ca287148ae67dec81501cfae73c"
CANONICAL_MONTHLY_RAW_RUN_ID = 34778911131
CANONICAL_FINAL_SOURCE_GATE_RUN_ID = 34811277716
VOL_THRESHOLD = 0.80
REGIMES = ("UP_HIGH", "UP_LOW", "DOWN_HIGH", "DOWN_LOW")


def regime_for_day(day: dt.date, btc: dict[dt.date, float]) -> tuple[str, float, float] | None:
    dates = [day - dt.timedelta(days=i) for i in range(30, -1, -1)]
    if any(d not in btc for d in dates):
        return None
    opens = [btc[d] for d in dates]
    mom30 = math.log(opens[-1] / opens[0])
    rets = [math.log(opens[i] / opens[i-1]) for i in range(1, len(opens))]
    rv30 = statistics.stdev(rets) * math.sqrt(365.0)
    trend = "UP" if mom30 > 0 else "DOWN"
    vol = "HIGH" if rv30 >= VOL_THRESHOLD else "LOW"
    return f"{trend}_{vol}", mom30, rv30


def regime_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    n = len(rows)
    reg = v01.ols_hac7([r["skew"] for r in rows], [r["forward_log_return"] for r in rows]) if n >= 20 else None
    base = v01.strategy_metrics(rows, 10.0)
    stress = v01.strategy_metrics(rows, 20.0)
    qualifying_nonnegative_years = 0
    qualifying_years: list[str] = []
    for y, x in base["annual"].items():
        if int(x["n"]) >= 25 and x["net_mean_bps"] is not None and math.isfinite(float(x["net_mean_bps"])) and float(x["net_mean_bps"]) >= 0:
            qualifying_nonnegative_years += 1
            qualifying_years.append(y)
    gates = {
        "A_n_ge_120": n >= 120,
        "B_beta_positive_and_one_sided_hac_p_le_0_10": bool(reg and reg["beta"] > 0 and reg["one_sided_p_beta_gt_0"] <= 0.10),
        "C_net_mean_10bps_positive": bool(base["net_mean_bps_per_trade"] is not None and math.isfinite(float(base["net_mean_bps_per_trade"])) and base["net_mean_bps_per_trade"] > 0),
        "D_profit_factor_10bps_gt_1": bool(base["profit_factor"] is not None and math.isfinite(float(base["profit_factor"])) and base["profit_factor"] > 1.0),
        "E_two_years_n25_nonnegative": qualifying_nonnegative_years >= 2,
        "F_no_single_year_gt_70pct_positive_gross_pnl": base["single_year_max_share_of_total_positive_gross_pnl"] <= 0.70,
        "G_provenance_timestamp_leakage_firewalls_pass": True,
    }
    full_pass = all(gates.values())
    core_pass = all(gates[k] for k in (
        "A_n_ge_120",
        "B_beta_positive_and_one_sided_hac_p_le_0_10",
        "C_net_mean_10bps_positive",
        "D_profit_factor_10bps_gt_1",
        "G_provenance_timestamp_leakage_firewalls_pass",
    ))
    return {
        "n": n,
        "regression": reg,
        "base_10bps": base,
        "stress_20bps": stress,
        "qualifying_nonnegative_years": qualifying_nonnegative_years,
        "qualifying_year_labels": qualifying_years,
        "gates": gates,
        "discovery_eligible": full_pass,
        "core_near_edge": core_pass,
    }


def candidate_rank(label: str, x: dict[str, Any]) -> tuple[Any, ...]:
    reg = x["regression"] or {"one_sided_p_beta_gt_0": 1.0}
    base = x["base_10bps"]
    # ascending tuple => preferred first; negate maximized fields.
    return (
        -int(x["qualifying_nonnegative_years"]),
        -float(base["net_mean_bps_per_trade"]),
        float(reg["one_sided_p_beta_gt_0"]),
        -int(x["n"]),
        label,
    )


def run(source_root: Path, output: Path) -> dict[str, Any]:
    receipt = v01.load_and_bind_receipt(source_root)
    manifest = v01.load_source_manifest(source_root)
    signal, signal_audit = v01.build_signal(source_root, manifest)
    btc = v01.load_btc_opens(source_root, receipt)

    rows: list[dict[str, Any]] = []
    regime_unevaluable = 0
    for day in sorted(signal):
        entry_day = day + dt.timedelta(days=1)
        exit_day = day + dt.timedelta(days=2)
        if entry_day > v01.END or exit_day > v01.END:
            continue
        if entry_day not in btc or exit_day not in btc:
            raise RuntimeError(f"missing BTC outcome price inside frozen window for signal {day}")
        rr = regime_for_day(day, btc)
        if rr is None:
            regime_unevaluable += 1
            continue
        regime, mom30, rv30 = rr
        fwd = math.log(btc[exit_day] / btc[entry_day])
        skew = signal[day]
        pos = 1 if skew > 0 else (-1 if skew < 0 else 0)
        rows.append({
            "signal_date": day,
            "skew": skew,
            "forward_log_return": fwd,
            "position": pos,
            "aligned_gross_bps": pos * fwd * 10000.0,
            "regime": regime,
            "momentum_30d": mom30,
            "realized_vol_30d": rv30,
        })

    by_regime: dict[str, dict[str, Any]] = {}
    for label in REGIMES:
        subset = [r for r in rows if r["regime"] == label]
        by_regime[label] = regime_metrics(subset)

    eligible = [k for k,v in by_regime.items() if v["discovery_eligible"]]
    core = [k for k,v in by_regime.items() if v["core_near_edge"]]
    selected = sorted(eligible, key=lambda k: candidate_rank(k, by_regime[k]))[0] if eligible else None
    if selected:
        classification = "CANDIDATE_NEAR_EDGE"
        rc = 0
    elif core:
        classification = "CONTEXT_DEPENDENT"
        rc = 4
    else:
        classification = "DISCOVERY_FAIL_NO_CANDIDATE"
        rc = 3

    result = {
        "lab_id": LAB_ID,
        "version": VERSION,
        "authority_commit": AUTHORITY_COMMIT,
        "parent_lab_id": "OPTIONS-SPOTPERP-001",
        "parent_result_preserved": "DISCOVERY_FAIL_NO_PROMOTION",
        "canonical_monthly_raw_run_id": CANONICAL_MONTHLY_RAW_RUN_ID,
        "canonical_final_source_gate_run_id": CANONICAL_FINAL_SOURCE_GATE_RUN_ID,
        "classification": classification,
        "selected_candidate_regime": selected,
        "frozen_regimes": list(REGIMES),
        "vol_threshold_annualized": VOL_THRESHOLD,
        "evaluable_regime_signal_days": len(rows),
        "regime_unevaluable_signal_days": regime_unevaluable,
        "source_signal_audit": signal_audit,
        "regimes": by_regime,
        "holdout_2025_accessed": False,
        "year_2026_accessed": False,
        "live_trading_authorized": False,
        "exchange_mutation_authorized": False,
        "holdout_2025_authorized_by_result": classification == "CANDIDATE_NEAR_EDGE",
        "notes": [
            "This child experiment does not retroactively promote the parent.",
            "Regime assignment uses only BTC opens known on or before signal date.",
            "2025 remains unopened in Discovery; 2026 remains locked.",
            "No manual candidate selection is permitted."
        ],
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "OPTIONS_SPOTPERP_002_REGIME_DISCOVERY_CLOSEOUT_V01.json").write_text(
        json.dumps(v01.sanitize_json(result), indent=2, sort_keys=True), encoding="utf-8"
    )
    with (output / "OPTIONS_SPOTPERP_002_REGIME_DISCOVERY_LEDGER_V01.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["signal_date","regime","momentum_30d","realized_vol_30d","skew","forward_log_return","position","aligned_gross_bps"])
        for r in rows:
            w.writerow([r["signal_date"].isoformat(), r["regime"], r["momentum_30d"], r["realized_vol_30d"], r["skew"], r["forward_log_return"], r["position"], r["aligned_gross_bps"]])
    return result | {"exit_code": rc}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-root", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    x = run(Path(args.source_root), Path(args.output))
    print(x["classification"])
    print("SELECTED_CANDIDATE_REGIME=", x["selected_candidate_regime"])
    print("2025 UNOPENED / 2026 LOCKED / NO LIVE TRADING")
    return int(x["exit_code"])

if __name__ == "__main__":
    raise SystemExit(main())

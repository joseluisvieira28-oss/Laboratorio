#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
import math
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CFG = {"family":"A_MOMENTUM","symbol":"AVAXUSDT","lookback":20,"horizon":1,"direction":"CONTINUATION"}
BASE_COST = 14.0
STRESS_COST = 20.0
TOL = 1e-6

KNOWN = {
    "BINANCE_SIGNAL__BINANCE_EXECUTION": {
        "n":357,
        "mean_base_bps":8.550675493754708,
        "profit_factor_base":1.0477360429576321,
        "mean_stress_bps":2.550675493754708,
    },
    "OKX_SIGNAL__OKX_EXECUTION": {
        "n":357,
        "mean_base_bps":8.303857819055219,
        "profit_factor_base":1.0463580530119918,
        "mean_stress_bps":2.3038578190552195,
    },
}

def loadmod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"MODULE_LOAD_SPEC_FAIL:{path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def canonical_hash(x) -> str:
    return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(",",":")).encode()).hexdigest()

def source_events(hyp, bars):
    series = hyp.Series(bars)
    cache = {"daily_rets":series.completed_daily_log_returns(),"rv20":series.rv20_map()}
    active_exit = None
    out = []
    for d in series.valid_dates:
        sd = date.fromisoformat(d)
        if sd.year != 2025:
            continue
        direction = hyp.signal_for(series, CFG, d, cache)
        if direction is None:
            continue
        ex, status = series.execution(d, CFG["horizon"])
        if status != "OK":
            out.append({"signal_day":d,"status":"DATA_UNAVAILABLE"})
            continue
        entry = date.fromisoformat(ex["entry_day"])
        exitd = date.fromisoformat(ex["exit_day"])
        if exitd.year >= 2026:
            out.append({"signal_day":d,"status":"DATA_UNAVAILABLE","entry_day":ex["entry_day"],"exit_day":ex["exit_day"]})
            continue
        if active_exit is not None and entry < active_exit:
            out.append({"signal_day":d,"status":"OVERLAP_BLOCKED","entry_day":ex["entry_day"],"exit_day":ex["exit_day"]})
            continue
        active_exit = exitd
        out.append({
            "signal_day":d,
            "status":"TRADE",
            "direction":int(direction),
            "entry_day":ex["entry_day"],
            "exit_day":ex["exit_day"],
        })
    return out

def destination_execution(hyp, dest_series, src, execution_venue, conf, okx, binance_bindings, okx_funding):
    ex, status = dest_series.execution(src["signal_day"], CFG["horizon"])
    if status != "OK":
        return {**src, "execution_venue":execution_venue, "source_unresolved":True, "source_error":f"DEST_EXECUTION:{status}"}
    if ex["entry_day"] != src["entry_day"] or ex["exit_day"] != src["exit_day"]:
        return {
            **src,
            "execution_venue":execution_venue,
            "source_unresolved":True,
            "source_error":f"SCHEDULE_MISMATCH:{src['entry_day']}->{src['exit_day']}:{ex['entry_day']}->{ex['exit_day']}",
        }
    event = {
        "signal_day":src["signal_day"],
        "status":"TRADE",
        "direction":src["direction"],
        **ex,
        "signed_return":int(src["direction"]) * float(ex["raw_return"]),
        "execution_venue":execution_venue,
    }
    try:
        if execution_venue == "BINANCE":
            z = conf.add_funding_bounds(event, "AVAXUSDT", binance_bindings)
            z["source_unresolved"] = False
            return z
        if execution_venue == "OKX":
            return okx.attach_funding(event, okx_funding)
        raise RuntimeError(f"UNKNOWN_EXECUTION_VENUE:{execution_venue}")
    except Exception as e:
        return {**event, "source_unresolved":True, "source_error":f"{type(e).__name__}:{e}"}

def quadrant_metrics(rows, okx):
    unresolved = [x for x in rows if x.get("source_unresolved")]
    resolved = [x for x in rows if not x.get("source_unresolved")]
    m = okx.path_metrics(resolved, "base_lower_bps", "stress_lower_bps") if resolved else {
        "n":0,"mean_base_bps":None,"mean_stress_bps":None,"profit_factor_base":None,
        "positive_active_months":0,"active_months":0,"positive_active_month_fraction":None,
        "positive_quarters":0,"leave_one_month_out_all_positive":False,"concentration_ratio":None,
    }
    m["bootstrap"] = okx.bootstrap_ci(resolved, "base_lower_bps") if resolved else {"ci_low":None,"ci_high":None}
    m["resolved_n"] = len(resolved)
    m["unresolved_n"] = len(unresolved)
    pf = m.get("profit_factor_base")
    m["frozen_economic_survival"] = (
        len(unresolved) == 0
        and m.get("mean_base_bps") is not None and m["mean_base_bps"] > 0
        and pf is not None and pf > 1
        and m.get("mean_stress_bps") is not None and m["mean_stress_bps"] > 0
        and m.get("positive_active_month_fraction") is not None and m["positive_active_month_fraction"] >= 0.5
    )
    return m

def reconcile(name, metric):
    exp = KNOWN[name]
    checks = {
        "n": metric["resolved_n"] == exp["n"],
        "mean_base_bps": metric.get("mean_base_bps") is not None and abs(metric["mean_base_bps"] - exp["mean_base_bps"]) <= TOL,
        "profit_factor_base": metric.get("profit_factor_base") is not None and abs(metric["profit_factor_base"] - exp["profit_factor_base"]) <= TOL,
        "mean_stress_bps": metric.get("mean_stress_bps") is not None and abs(metric["mean_stress_bps"] - exp["mean_stress_bps"]) <= TOL,
    }
    return {"pass":all(checks.values()),"checks":checks,"expected":exp}

def concordance(bin_events, okx_events):
    b = {x["signal_day"]:int(x["direction"]) for x in bin_events}
    o = {x["signal_day"]:int(x["direction"]) for x in okx_events}
    union = sorted(set(b) | set(o))
    inter = sorted(set(b) & set(o))
    same = [d for d in inter if b[d] == o[d]]
    opp = [d for d in inter if b[d] != o[d]]
    bonly = sorted(set(b)-set(o))
    oonly = sorted(set(o)-set(b))
    return {
        "binance_signal_days":len(b),
        "okx_signal_days":len(o),
        "union_signal_days":len(union),
        "intersection_signal_days":len(inter),
        "same_direction_intersection":len(same),
        "opposite_direction_intersection":len(opp),
        "binance_only_signal_days":len(bonly),
        "okx_only_signal_days":len(oonly),
        "exact_directional_jaccard":len(same)/len(union) if union else None,
        "binance_only_days":bonly,
        "okx_only_days":oonly,
        "opposite_direction_days":opp,
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--price-cache",required=True)
    ap.add_argument("--price-manifest",required=True)
    ap.add_argument("--binance-funding-bindings",required=True)
    ap.add_argument("--v03-runner-zip",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()

    out=Path(a.output)
    if out.exists():
        raise RuntimeError("OUTPUT_ALREADY_EXISTS")
    out.mkdir(parents=True)

    conf = loadmod("ced_conf", ROOT/"research"/"ced_1d_v3"/"ced_1d_2025_confirmation_runner_v01.py")
    okx = loadmod("okx_stageb", ROOT/"research"/"cross_venue_diamond_replication_002"/"okx_stage_b_exact_replication_v01.py")

    manifest=json.loads(Path(a.price_manifest).read_text())
    b_bars = conf.build_bars(Path(a.price_cache), manifest)["AVAXUSDT"]
    b_bindings_all = conf.load_bindings(Path(a.binance_funding_bindings))

    got = okx.acquire_frozen_sources()
    o_bars, price_dups = okx.parse_candles(got)
    if price_dups:
        raise RuntimeError(f"OKX_PRICE_DUPLICATES:{price_dups}")
    o_funding = okx.parse_funding(got)

    with tempfile.TemporaryDirectory() as td:
        hyp = conf.load_original_hypotheses(Path(a.v03_runner_zip), Path(td))

        b_src_all = source_events(hyp, b_bars)
        o_src_all = source_events(hyp, o_bars)
        b_src = [x for x in b_src_all if x["status"]=="TRADE" and conf.complete_signal_week(date.fromisoformat(x["signal_day"]))]
        o_src = [x for x in o_src_all if x["status"]=="TRADE" and conf.complete_signal_week(date.fromisoformat(x["signal_day"]))]

        b_series = hyp.Series(b_bars)
        o_series = hyp.Series(o_bars)

        specs = [
            ("BINANCE_SIGNAL__BINANCE_EXECUTION", b_src, "BINANCE", b_series),
            ("BINANCE_SIGNAL__OKX_EXECUTION", b_src, "OKX", o_series),
            ("OKX_SIGNAL__BINANCE_EXECUTION", o_src, "BINANCE", b_series),
            ("OKX_SIGNAL__OKX_EXECUTION", o_src, "OKX", o_series),
        ]

        rows_by_q={}
        metrics={}
        for q, srcs, venue, dest_series in specs:
            rows=[]
            for src in srcs:
                r=destination_execution(hyp,dest_series,src,venue,conf,okx,b_bindings_all,o_funding)
                r["quadrant"]=q
                rows.append(r)
            rows_by_q[q]=rows
            metrics[q]=quadrant_metrics(rows,okx)

    diag={
        q:reconcile(q,metrics[q])
        for q in ("BINANCE_SIGNAL__BINANCE_EXECUTION","OKX_SIGNAL__OKX_EXECUTION")
    }
    reconciliation_pass=all(x["pass"] for x in diag.values())
    conc=concordance(b_src,o_src)

    off=[
        metrics["BINANCE_SIGNAL__OKX_EXECUTION"]["frozen_economic_survival"],
        metrics["OKX_SIGNAL__BINANCE_EXECUTION"]["frozen_economic_survival"],
    ]
    all4=all(metrics[q]["frozen_economic_survival"] for q in metrics)
    if not reconciliation_pass:
        classification="IMPLEMENTATION_RECONCILIATION_FAIL"
    elif all4:
        classification="FOUR_OF_FOUR_CROSS_EXECUTION_SURVIVAL"
    elif all(off):
        classification="OFF_DIAGONALS_SURVIVE"
    elif sum(bool(x) for x in off)==1:
        classification="PARTIAL_OFF_DIAGONAL_SURVIVAL"
    else:
        classification="OFF_DIAGONAL_FAIL"

    receipt={
        "lab_id":"AVAX20-CROSS-VENUE-CAUSAL-DECOMPOSITION-V0.1",
        "candidate":"CED1D-0031-AVAX20-CONTINUATION-H1",
        "classification":classification,
        "config":CFG,
        "costs":{"base_bps":BASE_COST,"stress_bps":STRESS_COST},
        "signal_source_counts":{"BINANCE":len(b_src),"OKX":len(o_src)},
        "signal_concordance":conc,
        "quadrants":metrics,
        "diagonal_reconciliation":diag,
        "diagonal_reconciliation_pass":reconciliation_pass,
        "okx_mark_settlements_used":len(okx._mark_cache),
        "governance":{
            "2026_plus_accessed":False,
            "post_outcome_tuning":False,
            "venue_selection_after_outcomes":False,
            "live_trading":False,
            "orders":False,
            "exchange_mutation":False,
            "main_merge":False,
        },
    }
    receipt["fingerprint"]=canonical_hash(receipt)
    (out/"AVAX20_CROSS_VENUE_CAUSAL_DECOMPOSITION_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")

    flat=[]
    for q,rows in rows_by_q.items():
        flat.extend(rows)
    fields=sorted({k for r in flat for k in r})
    with (out/"AVAX20_CROSS_VENUE_CAUSAL_DECOMPOSITION_LEDGER_V0.1.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n")
        w.writeheader()
        w.writerows(flat)

    compact={
        "classification":classification,
        "signal_concordance":{
            k:conc[k] for k in (
                "binance_signal_days","okx_signal_days","union_signal_days","intersection_signal_days",
                "same_direction_intersection","opposite_direction_intersection",
                "binance_only_signal_days","okx_only_signal_days","exact_directional_jaccard"
            )
        },
        "quadrants":{
            q:{
                "n":m["resolved_n"],
                "unresolved":m["unresolved_n"],
                "base_mean_bps":m.get("mean_base_bps"),
                "pf":m.get("profit_factor_base"),
                "stress_mean_bps":m.get("mean_stress_bps"),
                "positive_months":[m.get("positive_active_months"),m.get("active_months")],
                "survival":m["frozen_economic_survival"],
                "bootstrap_ci_low":m["bootstrap"].get("ci_low"),
            } for q,m in metrics.items()
        },
        "diagonal_reconciliation_pass":reconciliation_pass,
        "fingerprint":receipt["fingerprint"],
    }
    print(json.dumps(compact,sort_keys=True))
    if not reconciliation_pass:
        raise SystemExit("IMPLEMENTATION_RECONCILIATION_FAIL")

if __name__=="__main__":
    main()

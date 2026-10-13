#!/usr/bin/env python3
"""Observed 2021–25 Parent 1h trail path diagnostics, NOT a new strategy."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import datetime,timezone
from pathlib import Path

from research.btc_convex_1h_forensics_20261013.forensics import (
    EXPECTED, locate, read_source
)
from research.btc_convex_multifront_v01 import retrospective_diagnostic as src
from research.btc_convex_timeframe_matrix_20261013 import matrix

MONTHS=[f"{y:04}-{mo:02}" for y in range(2021,2026) for mo in range(1,13)]
FIVE=matrix.M5
HOUR=matrix.HOUR

def source_5m(original):
    archive_market={}
    manifests=[]
    published={(x["kind"],x["month"]):x["sha256"]
               for x in original.get("provenance",[])}
    if len([k for k in published if k[0]=="5m" and k[1] in MONTHS])!=60:
        raise ValueError("ORIGINAL_5M_MONTH_SOURCE_MANIFEST_INCOMPLETE")
    for ym in MONTHS:
        raw,receipt=src.collect("5m",ym)
        expected=published.get(("5m",ym))
        if receipt["sha256"]!=expected:
            raise ValueError(f"ORIGINAL_5M_MANIFEST_SHA256_CHANGED:{ym}")
        b=src.candles(raw,FIVE)
        if len(set(archive_market)&set(b)):
            raise ValueError("OVERLAPPING_OFFICIAL_MONTHS")
        archive_market.update(b)
        manifests.append(receipt)
        print("PRICE_PATH_PROVENANCE_OK",ym,flush=True)
    if len(archive_market)!=525888 or set(archive_market)!=set(range(matrix.START,matrix.END,FIVE)):
        raise ValueError("HISTORICAL_FIVE_MINUTE_PRICE_PATH_GAPS")
    return archive_market,manifests

def audit_trade(row,bars,slip_bps):
    ent_t=int(row["open_t"])
    exit_t=int(row["close_t"])
    entry=float(row["entry_price"])
    recorded_exit=float(row["exit_price"])
    if ent_t%FIVE!=0 or exit_t%FIVE!=0:
        raise ValueError("LEDGER_TIMESTAMP_NOT_FIVE_MINUTE")
    stop=entry*.96
    initial=stop
    peak=entry
    best_high=entry
    highest_close_profit=-1e99
    current_active=False
    ever_active=False
    activation=0
    deactivation=0
    weakened=0
    effective_protection=0
    maximum_stop=initial
    first_active_t=None
    first_effective_stop_t=None
    actual_exit=None
    raw_reason=None
    for t in range(ent_t,exit_t,FIVE):
        b=bars.get(t)
        if b is None:raise ValueError("TRADE_PRICE_SOURCE_MISSING")
        if b["open"]<=stop:
            raw=b["open"]; raw_reason="STOP_OPEN_GAP"
        elif b["low"]<=stop:
            raw=stop;raw_reason="STOP_INTRABAR"
        else:
            raw=None
        if raw is not None:
            actual_exit=t+FIVE
            model_exit=raw*(1-slip_bps/10000)
            if actual_exit!=exit_t or abs(model_exit-recorded_exit)>max(.00001,abs(recorded_exit)*1e-8):
                raise ValueError(
                    f"EXACT_EXIT_PARITY_MISMATCH:{ent_t}:seen={actual_exit},expected={exit_t},"
                    f"modeled_exit={model_exit},recorded_exit={recorded_exit}")
            if raw_reason!=row["exit_reason"]:
                raise ValueError("EXIT_REASON_RECONSTRUCTION_MISMATCH")
            break
        peak=max(peak,b["high"])
        best_high=max(best_high,b["high"])
        if (t+FIVE)%HOUR==0:
            latest_profit=(b["close"]-entry)/entry
            highest_close_profit=max(highest_close_profit,latest_profit)
            activation_mode=(latest_profit>=.05)
            next_stop=max(initial,peak*.88) if activation_mode else initial
            if activation_mode and not current_active:
                activation+=1
                ever_active=True
                if first_active_t is None:first_active_t=t+FIVE
            if current_active and not activation_mode:
                deactivation+=1
                if next_stop+1e-8<stop:
                    weakened+=1
            if next_stop>initial+1e-8:
                effective_protection+=1
                if first_effective_stop_t is None:
                    first_effective_stop_t=t+FIVE
            current_active=activation_mode
            stop=next_stop
            maximum_stop=max(maximum_stop,stop)
    if actual_exit is None:
        raise ValueError(f"RECORDED_EXIT_NOT_OBSERVED_IN_FIVE_MINUTE_SOURCE:{ent_t}")
    profit=float(row["net_pnl"])
    is_winner=profit>0
    mfe=(best_high/entry-1)*100
    exit_px_return=(recorded_exit/entry-1)*100
    return {
        "open_t":ent_t,"exit_t":exit_t,
        "year":int(row["exit_year"]),"winner":is_winner,
        "net_pnl_usdt":profit,
        "price_runup_MFE_proxy_pct":mfe,
        "exit_price_return_after_slip_pct":exit_px_return,
        "peak_to_exit_giveback_pct_points":mfe-exit_px_return,
        "ever_close_activated_trail":ever_active,
        "number_activations":activation,
        "number_deactivations":deactivation,
        "reset_weakened_protective_stop_count":weakened,
        "trail_closed_hours_with_stop_above_initial":effective_protection,
        "maximum_stored_stop_relative_entry_pct":(maximum_stop/entry-1)*100,
        "first_activation_t":first_active_t,
        "first_effective_stop_t":first_effective_stop_t,
        "best_completed_1h_profit_pct":highest_close_profit*100 if highest_close_profit>-1e99 else None,
        "exit_reason":raw_reason,
        "observed_model_exit_exact_parity":True
    }

def summary(rows):
    total=len(rows)
    if not total:return {"count":0}
    sorted_g=sorted(z["peak_to_exit_giveback_pct_points"] for z in rows)
    won=[r for r in rows if r["winner"]]
    lost=[r for r in rows if not r["winner"]]
    reverts=[r for r in rows if r["number_deactivations"]>0]
    weak=[r for r in rows if r["reset_weakened_protective_stop_count"]>0]
    return {
        "count":total,
        "closed_winners":len(won),"closed_nonwinners":len(lost),
        "ever_trail_activated":sum(r["ever_close_activated_trail"] for r in rows),
        "ever_trail_activated_and_lost":sum(r["ever_close_activated_trail"] and not r["winner"] for r in rows),
        "trade_with_trail_deactivations":len(reverts),
        "deactivation_events":sum(r["number_deactivations"] for r in rows),
        "trade_with_protective_stop_weakened":len(weak),
        "protective_stop_weakening_events":sum(r["reset_weakened_protective_stop_count"] for r in rows),
        "trades_with_trailing_stop_above_initial":sum(r["trail_closed_hours_with_stop_above_initial"]>0 for r in rows),
        "trades_MFE_above_10pct_then_net_loss":sum(r["price_runup_MFE_proxy_pct"]>=10 and not r["winner"] for r in rows),
        "median_peak_to_exit_giveback_pp":sorted_g[total//2],
        "max_peak_to_exit_giveback_pp":max(sorted_g),
        "median_giveback_of_winning_trades_pp":sorted([r["peak_to_exit_giveback_pct_points"] for r in won])[len(won)//2] if won else None,
        "mean_peak_MFE_proxy_pct":sum(z["price_runup_MFE_proxy_pct"] for z in rows)/total,
        "top3_winners_by_NET":[r for r in sorted(won,key=lambda t:t["net_pnl_usdt"],reverse=True)[:3]],
        "per_year": {str(y):{
           "trades":len(yr),"trailing_activated":sum(r["ever_close_activated_trail"] for r in yr),
           "deactivated_trades":sum(r["number_deactivations"]>0 for r in yr),
           "weakened_stop_trades":sum(r["reset_weakened_protective_stop_count"]>0 for r in yr),
           "net_pnl_usdt":sum(r["net_pnl_usdt"] for r in yr)}
           for y in range(2021,2026) if (yr:=[r for r in rows if r["year"]==y])}
    }

def main():
    arg=argparse.ArgumentParser()
    arg.add_argument("--source-dir",type=Path,required=True)
    arg.add_argument("--output-dir",type=Path,required=True)
    args=arg.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    report={"status":"PATH_SOURCE_BLOCKED",
            "scope":"ALREADY_OBSERVED_2021_2025_PARENT_1H_ONLY",
            "economic_promotion_credit":"NONE","orders":0,
            "source_parent_artifact":"38426153613/11828479302"}
    try:
        parent, arms, file_hashes=read_source(args.source_dir)
        report["original_artifact_hashes"]=file_hashes
        prices,manifest=source_5m(parent)
        report["source_5m_zip_checksums"]={x["month"]:x["sha256"] for x in manifest}
        report["scenarios"]={}
        for label in EXPECTED:
            _,trade_rows=arms[label]
            bps=2 if label=="1h_BASE" else 5
            audited=[audit_trade(tr,prices,bps) for tr in trade_rows]
            if sum(r["net_pnl_usdt"] for r in audited)!=sum(float(x["net_pnl"]) for x in trade_rows):
                raise AssertionError("LEDGER_RECONSTRUCTION_PNL_MUTATION")
            report["scenarios"][label]=summary(audited)
            (args.output_dir/(label+"_TRAILING_PATH_AUDIT.json")).write_text(
                json.dumps(audited,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        report["status"]="ORIGINAL_TRAIL_PATH_PARITY_PASS_NO_NEW_ALPHA"
    except Exception as exc:
        report["block_reason"]=type(exc).__name__+":"+str(exc)
    (args.output_dir/"PATH_AUDIT_RESULT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("PATH_AUDIT_SUMMARY",json.dumps({
        "status":report["status"],"block_reason":report.get("block_reason"),
        "scenarios":report.get("scenarios")},sort_keys=True))
    if report["status"]!="ORIGINAL_TRAIL_PATH_PARITY_PASS_NO_NEW_ALPHA":
        raise SystemExit(2)

if __name__=="__main__":
    main()

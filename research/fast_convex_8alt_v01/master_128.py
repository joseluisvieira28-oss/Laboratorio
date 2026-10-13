#!/usr/bin/env python3
"""Immutable 128-arm FAST-CONVEX historical diagnostic master: no market rerun."""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import defaultdict,Counter
from pathlib import Path

ASSETS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
TF=("5m","15m","30m","1h")
HORIZON=("FAST8H","FAST24H")
COST=("BASE","STRESS")
RUN_ID=38446416504
EXPECTED={"5m":333216,"1h":27768,"funding":3288}
SUCCESS="FAST_CONVEX_FULL_HISTORICAL_DIAGNOSTIC_ONLY"

def combine(root):
    source={}
    for path in root.rglob("FAST_RESULT.json"):
        d=json.loads(path.read_text(encoding="utf8"))
        sym=d.get("symbol")
        if sym not in ASSETS or sym in source:
            raise ValueError("DUPLICATE_INVALID_FAST_SYMBOL")
        source[sym]=(path,d)
    if set(source)!=set(ASSETS):
        raise ValueError(f"ALL_EIGHT_SOURCE_RECEIPTS_REQUIRED:{set(ASSETS)-set(source)}")
    allrows=[]
    gates=[]
    statuses={}
    source_hashes={}
    for sym in ASSETS:
        path,d=source[sym]
        status=d.get("status")
        if d.get("trading_authority")!="NONE":
            raise ValueError("UNAUTHORIZED_TRADING_CLAIM")
        if status!=SUCCESS:
            if status!="SOURCE_BLOCKED":raise ValueError("UNRECOGNIZED_SOURCE_STATUS")
            statuses[sym]={"status":status,"reason":d.get("block_reason")}
        else:
            if d.get("source_counts")!=EXPECTED or len(d.get("source_manifest",[]))!=112:
                raise ValueError("BINANCE_SOURCE_MANIFEST_COVERAGE_INVALID:"+sym)
            expected_keys={tf+"_"+h+"_"+c for tf in TF for h in HORIZON for c in COST}
            if set(d.get("models",{}))!=expected_keys or len(d.get("scientific_gates",{}))!=8:
                raise ValueError("SOURCE_COVERED_BUT_ARM_COUNT_MISSING:"+sym)
            csvs={q.stem for q in path.parent.glob("*_TRADES.csv")}
            expected_csv={key for key in expected_keys if d["models"][key]["closed_trades"]>0}
            if csvs!=expected_csv:raise ValueError("LEDGER_CSV_COVERAGE_MISSING_OR_EXTRA:"+sym)
            statuses[sym]={"status":status,
                           "source_1h_signal_divergences":d.get("source_1h_entry_signal_divergences"),
                           "independent_1h_archive_conflicts":d.get("official_1h_source_conflicts",{}).get("official_1h_bar_mismatch_count")}
        source_hashes[sym]=hashlib.sha256(path.read_bytes()).hexdigest()
        for tf in TF:
            for h in HORIZON:
                for c in COST:
                    key=tf+"_"+h+"_"+c
                    row={"symbol":sym,"timeframe":tf,"max_hold":h,
                         "cost":c,"source_status":status,
                         "blocked_reason":d.get("block_reason"),
                         "OOS_proven":False,"venue_execution_proven":False}
                    if status==SUCCESS:
                        m=d["models"][key]
                        row.update({
                            "net_terminal_mark_pct":m["marked_return_pct"],
                            "three_year_model_CAGR_pct":m["approx_CAGR_3y_pct"],
                            "closed_trades":m["closed_trades"],
                            "trades_per_week":m["trades_per_week"],
                            "signals_per_week":m["signal_opportunities_per_week"],
                            "win_rate_pct":m["winrate_pct"],
                            "PF":m["profit_factor"],
                            "model_low_DD_pct":m["max_5m_low_model_dd_pct"],
                            "median_hold_hours":m["median_hold_hours"],
                            "max_hold_hours":m["max_hold_hours_observed"],
                            "fees_usdt":m["fees_total_usdt"],
                            "funding_usdt":m["funding_total_usdt"],
                            "closed_net_pnl_usdt":m["closed_net_pnl_usdt"],
                            "cash_equity_usdt":m["cash_equity_usdt"],
                            "open_end_position":m["end_position_open"],
                            "top3_share_positive_net_pnl_pct":m["top3_share_positive_net_pnl_pct"],
                            "remaining_closed_pnl_static_without_top3_usdt":m["static_closed_pnl_without_top3_usdt"],
                            **{f"{year}_closed_trades":m["annual_closed_trades"].get(str(year),0) for year in (2023,2024,2025)},
                            **{f"{year}_closed_pnl_usdt":m["annual_closed_pnl_usdt"].get(str(year),0) for year in (2023,2024,2025)}
                        })
                    allrows.append(row)
                if status==SUCCESS:
                    gate=d["scientific_gates"][tf+"_"+h]
                    b=d["models"][tf+"_"+h+"_BASE"]
                    s=d["models"][tf+"_"+h+"_STRESS"]
                    gates.append({"symbol":sym,"timeframe":tf,"horizon":h,
                                  "BASE_net_pct":b["marked_return_pct"],
                                  "STRESS_net_pct":s["marked_return_pct"],
                                  "BASE_closed_trades":b["closed_trades"],
                                  "BASE_weekly_trades":b["trades_per_week"],
                                  "BASE_PF":b["profit_factor"],"STRESS_PF":s["profit_factor"],
                                  "DD_model_pct":b["max_5m_low_model_dd_pct"],
                                  "BASE_three_year_CAGR_pct":b["approx_CAGR_3y_pct"],
                                  "positive_years":sum(v>0 for v in b["annual_closed_pnl_usdt"].values()),
                                  "annual_trades":b["annual_closed_trades"],
                                  "top3_omission_closed_static":b["static_closed_pnl_without_top3_usdt"],
                                  "passes_all_preregistered":gate["all_gates_descriptive_pass"],
                                  "failed_gates":[k for k,v in gate["gates"].items() if not v],
                                  "historical_alpha_go":False})
    if len(allrows)!=128:raise ValueError("NO_128_CASES")
    descending_by_net=sorted(gates,key=lambda x:x["BASE_net_pct"],reverse=True)
    descending_by_weekly=sorted(gates,key=lambda x:x["BASE_weekly_trades"],reverse=True)
    win_candidates=[x for x in gates if x["passes_all_preregistered"]]
    return {"status":"FAST_RETROSPECTIVE_COMPLETE_IF_SOURCE_PASS" if len(gates)==64 else "FAST_SOURCE_QUALIFIED_INCOMPLETE",
            "source_run":RUN_ID,"all_eight_sources":statuses,
            "original_result_sha256_by_symbol":source_hashes,
            "number_of_128_economic_rows":sum(x.get("net_terminal_mark_pct") is not None for x in allrows),
            "total_128_predeclared_rows":128,
            "all_128_rows":allrows,
            "fixed_historical_gate_results":gates,
            "all_gate_pass_count":len(win_candidates),
            "all_gate_pass_historical_candidate_only":win_candidates,
            "rank_by_net_return":descending_by_net,
            "rank_by_weekly_trade_frequency":descending_by_weekly,
            "source_oos_never_independent":True,
            "historical_stress_not_venue_fill":True,
            "real_execution_proven":False,
            "trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",required=True,type=Path)
    p.add_argument("--output-dir",required=True,type=Path)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    result=combine(a.source_dir)
    (a.output_dir/"FAST_128_MASTER.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    keys=list(dict.fromkeys(k for row in result["all_128_rows"] for k in row))
    with (a.output_dir/"FAST_128_ALL_UNFILTERED.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(result["all_128_rows"])
    print("FAST_MASTER",json.dumps({"status":result["status"],
        "source":result["all_eight_sources"],"observed_rows":result["number_of_128_economic_rows"],
        "strict_gate_pass_count":result["all_gate_pass_count"],
        "strict_gate_pass":result["all_gate_pass_historical_candidate_only"],
        "top_15_return":result["rank_by_net_return"][:15],
        "top_15_frequency":result["rank_by_weekly_trade_frequency"][:15]
    },sort_keys=True),flush=True)
    if result["number_of_128_economic_rows"]!=128:raise SystemExit(2)
if __name__=="__main__":main()

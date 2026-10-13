#!/usr/bin/env python3
"""Read-only reconciliation of existing immutable first SHORT-REJECTION-SCALP-001 producer.
No new outcomes, no price requests, no trading or edits to model decisions.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from pathlib import Path
SYMS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
ARMS=("BASE","STRESS","DELAY_6H_BASE")
EXPECTED_5M=333216;EXPECTED_1H=27768;EXPECTED_FUNDING=3288
SOURCE_RUN=38446411938
def aggregate(source):
    records={}
    for p in source.rglob("RESULT.json"):
        d=json.loads(p.read_text(encoding="utf8"))
        sym=d.get("symbol")
        if sym not in SYMS or sym in records:raise ValueError("UNEXPECTED_OR_DUPLICATE_SYMBOL_RECEIPT")
        records[sym]=(p,d)
    if set(records)!=set(SYMS):
        raise ValueError("MISSING_OR_BLOCKED_SOURCE_RECEIPT:"+str(set(SYMS)-set(records)))
    rows=[];manifest={};negative_control={}
    for symbol in SYMS:
        p,d=records[symbol]
        if d.get("status")!="HISTORICAL_SCALP_COMPLETED_NO_OOS":
            raise ValueError("SOURCE_MODEL_BLOCKED:"+symbol+":"+str(d.get("error")))
        if d.get("source_counts")!={"5m":EXPECTED_5M,"1h":EXPECTED_1H,"funding":EXPECTED_FUNDING}:
            raise ValueError("FIVE_MIN_HOUR_FUNDING_COVERAGE_FAIL:"+symbol)
        if len(d.get("official_5m_market_checksum_manifest",[]))!=112:
            raise ValueError("CHECKSUM_MANIFEST_REQUIRED:"+symbol)
        if len(d.get("official_1m_checksum_manifest",[]))!=d.get("one_minute_loaded_months"):
            raise ValueError("ONE_MIN_SOURCE_MANIFEST_BAD:"+symbol)
        if set(d.get("model",{}))!=set(ARMS):
            raise ValueError("THREE_FROZEN_ARMS_REQUIRED:"+symbol)
        if d.get("independent_oos") is not False or d.get("trading_authority")!="NONE":
            raise ValueError("INVALID_AUTHORITY_CLAIM")
        seen_names=set()
        for row in d["official_1m_checksum_manifest"]:
            m=row["month"]
            if m in seen_names:raise ValueError("DUPLICATE_MONTH_IN_1M_ARCHIVE")
            seen_names.add(m)
            if len(row["sha256"])!=64 or not ("2023-01"<=m<="2025-12"):
                raise ValueError("UNVERIFIED_1M_SOURCE_RECORD")
        manifest[symbol]={"source_result_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                          "verified_minute_months":len(seen_names),
                          "five_hour_funding_source_counts":d["source_counts"],
                          "one_minute_5minute_revision_qualified":d["source_revision_qualified"],
                          "signal_decisions":d["signal_audit"]["signal_decisions"]}
        for arm in ARMS:
            x=d["model"][arm]
            if x["status"]!="RETROSPECTIVE_1M_SHORT_SCALP_MODEL_ONLY":
                raise ValueError("MODEL_NOT_RETROSPECTIVE_ONLY")
            if x["closed_trades"] and not (p.parent/(arm+"_TRADES.csv")).exists():
                raise ValueError("TRADE_LEDGER_MISSING:"+symbol+":"+arm)
            v=x["marked_return_pct"]
            if not math.isfinite(v):raise ValueError("NONFINITE_RETURN:"+symbol)
            annual=x["annual_closed_pnl_usdt"]
            if abs(x["price_pnl_closed_usdt"]-x["fees_closed_usdt"]+x["funding_closed_usdt"]-x["closed_net_usdt"])>.0001:
                raise ValueError("CLOSED_COST_CASH_RECONCILIATION_FAIL")
            rows.append({"symbol":symbol,"arm":arm,
                "cumulative_net_pct":v,
                "closed_trades":x["closed_trades"],
                "wins":x["wins"],"win_rate_pct":x["win_rate_pct"],
                "profit_factor":x["profit_factor"],
                "max_closed_drawdown_pct":x["max_closed_dd_pct"],
                "worst_single_trade_1m_high_mark_dd_pct":x["worst_1m_high_mark_dd_trade_pct"],
                "fees_closed_usdt":x["fees_closed_usdt"],
                "funding_closed_usdt":x["funding_closed_usdt"],
                "closed_price_pnl_usdt":x["price_pnl_closed_usdt"],
                "closed_net_pnl_usdt":x["closed_net_usdt"],
                "year_2023_usdt":annual.get("2023",0.),
                "year_2024_usdt":annual.get("2024",0.),
                "year_2025_usdt":annual.get("2025",0.),
                "positive_closed_years":x["positive_exit_years_count"],
                "top3_win_share_pct":x["winner_top3_share_pct"],
                "static_closed_pnl_without_top3_usdt":x["closed_net_minus_top3_static_usdt"],
                "setup_signals":x["signals_in_period"],
                "skipped_occupied":x["skipped_while_occupied"],
                "open_end_position":x["has_open_end_position"]})
    if len(rows)!=24:raise ValueError("NOT_ALL_24_PREREGISTERED_ARMS")
    by={(r["symbol"],r["arm"]):r for r in rows}
    comparisons=[]
    for symbol in SYMS:
        b=by[(symbol,"BASE")];s=by[(symbol,"STRESS")]
        n=by[(symbol,"DELAY_6H_BASE")]
        comparisons.append({"symbol":symbol,
            "base_net_pct":b["cumulative_net_pct"],
            "stress_net_pct":s["cumulative_net_pct"],
            "delayed_placebo_base_net_pct":n["cumulative_net_pct"],
            "base_minus_placebo_net_pct_points":b["cumulative_net_pct"]-n["cumulative_net_pct"],
            "base_closed_trades":b["closed_trades"],
            "base_profit_factor":b["profit_factor"],
            "base_closed_winrate_pct":b["win_rate_pct"],
            "base_model_fees_usdt":b["fees_closed_usdt"],
            "base_model_funding_usdt":b["funding_closed_usdt"],
            "base_price_pnl_after_slippage_before_fees_usdt":b["closed_price_pnl_usdt"],
            "base_model_closed_net_usdt":b["closed_net_pnl_usdt"],
            "base_static_closed_net_if_fees_zero_usdt":b["closed_price_pnl_usdt"]+b["funding_closed_usdt"],
            "positive_base_stress_pf":(b["cumulative_net_pct"]>0 and s["cumulative_net_pct"]>0 and
                                      (b["profit_factor"] or 0)>1 and (s["profit_factor"] or 0)>1),
            "model_only_not_statistically_proven":True})
    comparisons.sort(key=lambda x:x["base_net_pct"],reverse=True)
    return {"status":"SOURCE_VERIFIED_24_OF_24_HISTORICAL_RESEARCH_ONLY",
        "producer_run":SOURCE_RUN,"source_manifest_by_symbol":manifest,
        "all_24_rows":rows,"comparisons":comparisons,
        "independent_oos":False,"real_execution_proven":False,
        "trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args();a.output_dir.mkdir(parents=True,exist_ok=True)
    d=aggregate(a.source_dir)
    (a.output_dir/"SHORT_SCALP_MASTER_24.json").write_text(json.dumps(d,indent=2,sort_keys=True)+"\n",encoding="utf8")
    with (a.output_dir/"SHORT_SCALP_MASTER_24.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=d["all_24_rows"][0].keys())
        w.writeheader();w.writerows(d["all_24_rows"])
    print("SHORT_SCALP_MASTER",json.dumps({"status":d["status"],
        "comparisons":d["comparisons"],
        "sources":d["source_manifest_by_symbol"]},sort_keys=True),flush=True)
if __name__=="__main__":main()

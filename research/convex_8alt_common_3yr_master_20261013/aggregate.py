"""Combine all previously executed 2023-25 common 8-alt receipts, no reruns."""
import argparse,csv,hashlib,json,math
from pathlib import Path

SYMS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
      "DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
TFS=("15m","30m","1h","4h")
COSTS=("BASE","STRESS")
RUN=38432883246
EXPECTED_STATUS="COMMON_2023_25_8ALT_COMPLETED_NO_OOS_CREDIT"
SOURCE={"5m":333216,"1h":27768,"funding":3288}

def aggregate(root):
    files=list(root.rglob("RESULT.json"))
    input_by_symbol={}
    for p in files:
        doc=json.loads(p.read_text(encoding="utf8"))
        name=doc.get("symbol")
        if name not in SYMS or name in input_by_symbol:
            raise ValueError("INVALID_OR_DUPLICATE_SYMBOL")
        input_by_symbol[name]=(p,doc)
    if set(input_by_symbol)!=set(SYMS):
        raise ValueError("EIGHT_SOURCE_SYMBOLS_REQUIRED:"+str(set(SYMS)-set(input_by_symbol)))
    matrix=[]
    receipts={}
    for name in SYMS:
        path,d=input_by_symbol[name]
        if d.get("status")!=EXPECTED_STATUS:raise ValueError("SOURCE_GATE_BLOCKED:"+name+":"+str(d.get("blocked_reason")))
        if d.get("source_counts")!=SOURCE:raise ValueError("SOURCE_COUNTS_MISMATCH:"+name)
        if len(d.get("source_manifest",[]))!=112:raise ValueError("SOURCE_SHA_ARCHIVE_COVERAGE:"+name)
        if d.get("period_start")!="2023-01-01T00:00:00Z" or d.get("period_end_exclusive")!="2026-01-01T00:00:00Z":
            raise ValueError("WINDOW_MISMATCH:"+name)
        if d.get("independent_OOS") is not False or d.get("actual_venue_fills") is not False:
            raise ValueError("NON_SCIENTIFIC_ALPHA_CLAIM:"+name)
        if set(d.get("model",{}))!={tf+"_"+cost for tf in TFS for cost in COSTS}:
            raise ValueError("MISSING_EXACT_8_CASES:"+name)
        if len(list(path.parent.glob("*_TRADES.csv")))!=8:
            raise ValueError("TRADE_LEDGER_EIGHT_EXPECTED:"+name)
        receipts[name]={"result_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
                        "source_1h_entry_signal_disagreement_count":d["source_signal_disagreement_count_1h"],
                        "source_1h_market_bar_discrepancies":d["source_audit"]["official_1h_bar_mismatch_count"]}
        for tf in TFS:
            for cost in COSTS:
                m=d["model"][tf+"_"+cost]
                net=m["marked_return_pct"]
                if not math.isfinite(net):raise ValueError("NONFINITE_RETURN:"+name)
                annual=m["annual_closed_trade_pnl_usdt"]
                row={"symbol":name,"timeframe":tf,"cost":cost,
                     "net_terminal_marked_return_pct":net,
                     "cagr_3year_approx_pct":100*((1+net/100)**(1/3)-1) if net>-100 else None,
                     "closed_trades":m["closed_trades"],"wins":m["wins"],
                     "winrate_pct":m["win_rate_pct"],"profit_factor":m["profit_factor"],
                     "drawdown_5m_low_model_pct":m["max_5m_low_stress_dd_pct"],
                     "fees_usdt":m["fees_usdt"],"funding_usdt":m["funding_usdt"],
                     "top3_win_share_of_winner_pnl_pct":m["top3_winner_share_of_gross_positive_pct"],
                     "remove_top3_static_closed_pnl_usdt":m["removed_3_biggest_net_pnl_sum_usdt"],
                     "positive_pnl_year_count":sum(annual.get(str(y),0)>0 for y in (2023,2024,2025)),
                     "year_2023_usdt":annual.get("2023",0),
                     "year_2024_usdt":annual.get("2024",0),
                     "year_2025_usdt":annual.get("2025",0),
                     "end_position_open":m["end_position_open"],
                     "signal_opportunities":m["signal_bars"],
                     "skipped_while_active":m["skipped_signals_active_slot"]}
                matrix.append(row)
    if len(matrix)!=64:raise ValueError("SIXTY_FOUR_UNFILTERED_REQUIRED")
    b=[r for r in matrix if r["cost"]=="BASE"]
    s={(r["symbol"],r["timeframe"]):r for r in matrix if r["cost"]=="STRESS"}
    ranking=sorted(b,key=lambda r:r["net_terminal_marked_return_pct"],reverse=True)
    both=[]
    for r in ranking:
        t=s[(r["symbol"],r["timeframe"])]
        if r["net_terminal_marked_return_pct"]>0 and t["net_terminal_marked_return_pct"]>0 and (r["profit_factor"] or 0)>1 and (t["profit_factor"] or 0)>1:
            both.append({"symbol":r["symbol"],"tf":r["timeframe"],
                         "base_net_pct":r["net_terminal_marked_return_pct"],
                         "stress_net_pct":t["net_terminal_marked_return_pct"],
                         "base_pf":r["profit_factor"],
                         "base_dd_pct":r["drawdown_5m_low_model_pct"],
                         "positive_years_of_three":r["positive_pnl_year_count"],
                         "static_pnl_minus_three_top_winners_usdt":r["remove_top3_static_closed_pnl_usdt"],
                         "classification":"DESCRIPTIVE_NOT_CERTIFIED_EDGE"})
    return {"status":"COMPLETE_SAME_3YEAR_WINDOW_64_CASES_RESEARCH_ONLY",
            "run":RUN,"source_counts_per_asset":SOURCE,"verified_source_receipts":receipts,
            "all_64_unfiltered_cases":matrix,
            "historical_base_return_ranking":[{"symbol":r["symbol"],"tf":r["timeframe"],
                    "return_pct":r["net_terminal_marked_return_pct"],
                    "dd":r["drawdown_5m_low_model_pct"],
                    "profit_factor":r["profit_factor"]} for r in ranking],
            "descriptive_positive_base_and_stress":both,
            "independent_OOS":False,"real_exchange_fills_proven":False,
            "2026_protected_holdout_opened":False,"trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    d=aggregate(a.source_dir)
    (a.output_dir/"COMMON_3YEAR_MASTER.json").write_text(json.dumps(d,indent=2,sort_keys=True)+"\n")
    with (a.output_dir/"COMMON_3YEAR_64_CASES.csv").open("w",newline="",encoding="utf8") as f:
        rows=d["all_64_unfiltered_cases"]
        w=csv.DictWriter(f,fieldnames=rows[0].keys());w.writeheader();w.writerows(rows)
    print("MASTER_3YEAR",json.dumps({k:v for k,v in d.items() if k not in ("all_64_unfiltered_cases","historical_base_return_ranking")},sort_keys=True))
if __name__=="__main__":main()

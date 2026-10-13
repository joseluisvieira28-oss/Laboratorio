"""Consolidate immutable already-produced 8-symbol ETH..AVAX historical artifacts.
No market fetch, trading or new economic outcomes. Missing symbols remain BLOCKED.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

SYMS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
      "DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
TFS=("15m","30m","1h","4h")
COSTS=("BASE","STRESS")
SOURCE_RUN=38430847396

def combine(root):
    found={}
    for path in root.rglob("RESULT.json"):
        d=json.loads(path.read_text(encoding="utf8"))
        s=d.get("symbol")
        if s not in SYMS or s in found:
            raise ValueError("SYMBOL_MISSING_OR_DUPLICATE")
        found[s]=(path,d)
    if set(found)!=set(SYMS):
        raise ValueError("ALL_EIGHT_SOURCE_RECEIPTS_REQUIRED:"+str(set(SYMS)-set(found)))
    rows=[]
    audit={}
    for symbol in SYMS:
        path,d=found[symbol]
        status=d["status"]
        if d.get("independent_OOS") is not False or d.get("actual_venue_fills") is not False:
            raise ValueError("INVALID_OOS_EXECUTABLE_CLAIM")
        complete=status=="HISTORICAL_MULTI_ALT_4TF_COMPLETED_NO_OOS_CREDIT"
        if complete:
            if d["source_counts"]!={"5m":543456,"1h":45288,"funding":5478}:
                raise ValueError("SOURCE_COUNTS_COVERAGE_UNVERIFIED:"+symbol)
            if len(d.get("source_manifest",[]))!=184:
                raise ValueError("OFFICIAL_CHECKSUM_MANIFEST_COVERAGE_BAD:"+symbol+":"+str(len(d.get("source_manifest",[]))))
            if set(d.get("model",{}))!={tf+"_"+c for tf in TFS for c in COSTS}:
                raise ValueError("MISSING_TIMEFRAME_OR_COST:"+symbol)
            ledger_count=len(list(path.parent.glob("*_TRADES.csv")))
            if ledger_count!=8:raise ValueError("MISSING_AUDIT_LEDGER:"+symbol+":"+str(ledger_count))
        elif status!="SOURCE_BLOCKED":
            raise ValueError("UNKNOWN_SYMBOL_CLASSIFICATION:"+symbol+":"+status)
        audit[symbol]={"status":status,"block_reason":d.get("blocked_reason"),
            "source_counts":d.get("source_counts"),
            "official_1h_5m_mismatches":d.get("source_audit",{}).get("official_1h_bar_mismatch_count"),
            "source_signal_disagreements":d.get("source_signal_disagreement_count_1h"),
            "source_result_sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
        for tf in TFS:
            for cost in COSTS:
                m=d.get("model",{}).get(tf+"_"+cost)
                row={"symbol":symbol,"timeframe":tf,"cost":cost,
                     "status":status,"blocked_reason":d.get("blocked_reason"),
                     "research_only":True,
                     "independent_oos":False,
                     "live_authority":False}
                if m is not None:
                    net=m["marked_return_pct"]
                    if not math.isfinite(net):raise ValueError("NAN_MARKED_RETURN")
                    annual=m["annual_closed_trade_pnl_usdt"]
                    row.update({
                        "return_pct":net,
                        "CAGR_5Y_approx_pct":100*((1+net/100)**(1/5)-1) if net>-100 else None,
                        "closed_trades":m["closed_trades"],
                        "wins":m["wins"],
                        "win_rate_pct":m["win_rate_pct"],
                        "PF":m["profit_factor"],
                        "max_5m_low_stress_dd_pct":m["max_5m_low_stress_dd_pct"],
                        "fees_usdt":m["fees_usdt"],
                        "funding_usdt":m["funding_usdt"],
                        "top3_share_of_gross_positive_pct":m["top3_winner_share_of_gross_positive_pct"],
                        "remove_top3_static_closed_pnl_usdt":m["removed_3_biggest_net_pnl_sum_usdt"],
                        "positive_closed_years":sum(annual.get(str(y),0)>0 for y in range(2021,2026)),
                        "open_end_position":m["end_position_open"],
                        "signal_bars":m["signal_bars"],
                        "signals_skipped_due_open_slot":m["skipped_signals_active_slot"],
                        "terminal_marked_equity_usdt":m["terminal_marked_equity_usdt"],
                        **{f"closed_pnl_{y}_usdt":annual.get(str(y),0) for y in range(2021,2026)}
                    })
                rows.append(row)
    if len(rows)!=64:raise ValueError("ALL_64_CASES_REQUIRED")
    # A ranking is a DEsCRIPTIVE sorted retrospective table, not a GO criterion.
    comparable=[r for r in rows if r["cost"]=="BASE" and r.get("return_pct") is not None]
    comparable.sort(key=lambda x:(x["return_pct"],x["symbol"],x["timeframe"]),reverse=True)
    positive_both=[]
    for r in comparable:
        twin=next(z for z in rows if z["symbol"]==r["symbol"] and z["timeframe"]==r["timeframe"] and z["cost"]=="STRESS")
        if r["return_pct"]>0 and twin.get("return_pct",float("-inf"))>0 and r.get("PF",0)>1 and twin.get("PF",0)>1:
            positive_both.append({
                "symbol":r["symbol"],"timeframe":r["timeframe"],
                "base_pct":r["return_pct"],"stress_pct":twin["return_pct"],
                "PF_BASE":r["PF"],"DD_BASE":r["max_5m_low_stress_dd_pct"],
                "positive_closed_years":r["positive_closed_years"],
                "top3_static_net_remaining_usdt":r["remove_top3_static_closed_pnl_usdt"],
                "candidate_status":"DESCRIPTIVE_POSITIVE_NOT_A_PROVEN_EDGE"
            })
    return {"status":"CONSOLIDATED_SOURCE_QUALIFIED_RETROSPECTIVE_ONLY" if any(
            v["status"]=="SOURCE_BLOCKED" for v in audit.values()) else "COMPLETE_RETROSPECTIVE_ONLY",
            "original_workflow_run":SOURCE_RUN,
            "scope":list(SYMS),"source_statuses":audit,
            "rows":rows,"complete_symbols":[s for s in SYMS if audit[s]["status"]!="SOURCE_BLOCKED"],
            "blocked_symbols":[s for s in SYMS if audit[s]["status"]=="SOURCE_BLOCKED"],
            "complete_economic_cases":sum("return_pct" in r for r in rows),
            "all_requested_cases":64,
            "descriptive_BASE_ranking":[{"symbol":r["symbol"],"timeframe":r["timeframe"],
                                         "return_pct":r["return_pct"],
                                         "PF":r["PF"],"DD":r["max_5m_low_stress_dd_pct"]}
                                        for r in comparable],
            "positive_BASE_and_STRESS_arms":positive_both,
            "new_independent_OOS_evidence":False,
            "real_venue_fills_verified":False,
            "live_trading_authority":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    result=combine(a.source_dir)
    result_path=a.output_dir/"MULTIALT_AGGREGATE.json"
    result_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf8")
    with (a.output_dir/"MULTIALT_MATRIX.csv").open("w",encoding="utf8",newline="") as f:
        keys=list(dict.fromkeys(k for row in result["rows"] for k in row.keys()))
        w=csv.DictWriter(f,fieldnames=keys)
        w.writeheader();w.writerows(result["rows"])
    print("MASTER_MATRIX",json.dumps({k:v for k,v in result.items() if k not in ("rows","descriptive_BASE_ranking")},sort_keys=True))
    print("FILES",result_path)
if __name__=="__main__":
    main()

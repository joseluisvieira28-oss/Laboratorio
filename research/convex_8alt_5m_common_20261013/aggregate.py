"""Consolidate only finished immutable native-5m source receipts for all 8 alts."""
from __future__ import annotations
import argparse, csv, hashlib, json, math
from pathlib import Path

SYMS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
      "DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
RUN=38435206427
EXPECTED={"5m":333216,"1h":27768,"funding":3288}
STATUS="HISTORICAL_NATIVE_5M_COMPLETE_NO_OOS_CREDIT"
def aggregate(root):
    records={}
    for f in root.rglob("RESULT.json"):
        d=json.loads(f.read_text(encoding="utf8"))
        s=d.get("symbol")
        if s not in SYMS or s in records:
            raise ValueError("UNKNOWN_OR_DUPLICATE_SOURCE_SYMBOL")
        records[s]=(f,d)
    if set(records)!=set(SYMS):
        raise ValueError("EIGHT_SOURCES_REQUIRED:"+str(set(SYMS)-set(records)))
    rows=[]
    source={}
    for symbol in SYMS:
        p,d=records[symbol]
        if d.get("status")!=STATUS:
            raise ValueError(f"SOURCE_BLOCKED:{symbol}:{d.get('block_reason')}")
        if d.get("source_counts")!=EXPECTED:raise ValueError("ORIGINAL_SOURCE_COUNT_MISMATCH:"+symbol)
        if len(d.get("source_manifest",[]))!=112:
            raise ValueError("OFFICIAL_MANIFEST_COUNT_MISMATCH:"+symbol)
        if set(d.get("models",{}))!={"BASE","STRESS"}:
            raise ValueError("BOTH_COST_CASES_REQUIRED:"+symbol)
        if not all((p.parent/(c+"_TRADES.csv")).exists() for c in ("BASE","STRESS")):
            raise ValueError("MISSING_TRADE_RECEIPTS:"+symbol)
        if d.get("independent_oos") is not False or d.get("actual_exchange_fills") is not False or d.get("trading_authority")!="NONE":
            raise ValueError("BAD_UNVERIFIED_ALPHA_AUTHORITY")
        source[symbol]={"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                        "source_1h_price_volume_disagreements":d["official_1h_discrepancy"]["official_1h_bar_mismatch_count"],
                        "binary_1h_signal_divergence":d["hourly_entry_signal_disagreement_count"]}
        for cost in ("BASE","STRESS"):
            m=d["models"][cost]
            net=m["marked_return_pct"]
            if not math.isfinite(net):raise ValueError("NONFINITE_ECONOMIC_METRIC")
            years=m["annual_closed_trade_pnl_usdt"]
            rows.append({"symbol":symbol,"timeframe":"5m","cost":cost,
                         "net_return_pct":net,
                         "implied_3y_cagr_pct":100*((1+net/100)**(1/3)-1) if net>-100 else None,
                         "closed_trades":m["closed_trades"],
                         "wins":m["wins"],"winrate_pct":m["win_rate_pct"],
                         "profit_factor":m["profit_factor"],
                         "dd_5m_low_model_pct":m["max_5m_low_stress_dd_pct"],
                         "fees_usdt":m["fees_usdt"],"funding_usdt":m["funding_usdt"],
                         "top3_gross_win_share_pct":m["top3_winner_share_of_gross_positive_pct"],
                         "closed_pnl_minus_top3_winners_usdt":m["removed_3_biggest_net_pnl_sum_usdt"],
                         "net_closed_2023_usdt":years.get("2023",0),
                         "net_closed_2024_usdt":years.get("2024",0),
                         "net_closed_2025_usdt":years.get("2025",0),
                         "positive_closed_years":sum(years.get(str(y),0)>0 for y in (2023,2024,2025)),
                         "signals":m["signal_bars"],
                         "signals_skipped_one_slot":m["skipped_signals_active_slot"],
                         "end_open_position":m["end_position_open"]})
    if len(rows)!=16:raise ValueError("ALL_16_CELLS_REQUIRED")
    base=sorted([r for r in rows if r["cost"]=="BASE"],key=lambda x:x["net_return_pct"],reverse=True)
    stress={r["symbol"]:r for r in rows if r["cost"]=="STRESS"}
    qualified=[r["symbol"] for r in base if r["net_return_pct"]>0 and (r["profit_factor"] or 0)>1 and
               stress[r["symbol"]]["net_return_pct"]>0 and (stress[r["symbol"]]["profit_factor"] or 0)>1]
    return {"status":"16_16_NATIVE5M_COMPLETE_HISTORICAL_ONLY","run":RUN,
            "source_receipts":source,"rows":rows,
            "ranked_BASE":base,"base_stress_historical_positive_only":qualified,
            "independent_forward":False,"execution_authenticated":False,
            "trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    a.output_dir.mkdir(parents=True,exist_ok=True)
    doc=aggregate(a.source_dir)
    (a.output_dir/"NATIVE_5M_16_CASES.json").write_text(json.dumps(doc,indent=2,sort_keys=True)+"\n")
    with (a.output_dir/"NATIVE_5M_16_CASES.csv").open("w",encoding="utf8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=doc["rows"][0].keys())
        w.writeheader();w.writerows(doc["rows"])
    print("NATIVE5M_MASTER",json.dumps({"status":doc["status"],"source_receipts":doc["source_receipts"],
        "ranked":doc["ranked_BASE"],"both_positive":doc["base_stress_historical_positive_only"]},sort_keys=True))
if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Combine exactly 8 original frozen SHORT producer artifacts, 80 historical arms."""
import argparse,csv,hashlib,json,math
from pathlib import Path
SYMS=("ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","ADAUSDT","LINKUSDT","AVAXUSDT")
TFS=("5m","15m","30m","1h","4h")
COSTS=("BASE","STRESS")
SOURCE_RUN=38437548175
EXPECTED_COUNTS={"5m":333216,"1h":27768,"funding":3288}
EXPECTED_STATUS="SHORT_10_ARMS_COMPLETED_RETROSPECTIVE_ONLY"

def aggregate(root):
    sources={}
    for p in root.rglob("SHORT_RESULT.json"):
        d=json.loads(p.read_text(encoding="utf8"))
        s=d.get("symbol")
        if s not in SYMS or s in sources:raise ValueError("UNKNOWN_OR_DUPLICATED_SYMBOL")
        sources[s]=(p,d)
    if set(sources)!=set(SYMS):raise ValueError("MISSING_8_SYMBOLS:"+str(set(SYMS)-set(sources)))
    audit={}
    rows=[]
    for s in SYMS:
        p,d=sources[s]
        if d.get("status")!=EXPECTED_STATUS:
            raise ValueError(f"SOURCE_OR_MODEL_NOT_COMPLETE:{s}:{d.get('blocked_reason')}")
        if d.get("source_counts")!=EXPECTED_COUNTS:raise ValueError("SOURCE_COUNT_MISMATCH:"+s)
        if len(d.get("source_manifest",[]))!=112:raise ValueError("SOURCE_MANIFEST_COUNT_MISMATCH:"+s)
        if d.get("independent_oos") is not False or d.get("live_authority")!="NONE":
            raise ValueError("INVALID_AUTHORITY")
        if set(d.get("model",{}))!={tf+"_"+cost for tf in TFS for cost in COSTS}:
            raise ValueError("NOT_TEN_ARMS:"+s)
        for key,model in d["model"].items():
            if model["closed_trades"] and not (p.parent/(key+"_TRADES.csv")).exists():
                raise ValueError("CLOSED_TRADE_CSV_MISSING:"+s+key)
        audit[s]={"result_sha256":hashlib.sha256(p.read_bytes()).hexdigest(),
                  "official_hourly_disagreement_count":d["official_hourly_discrepancy"]["official_1h_bar_mismatch_count"],
                  "source_counts":d["source_counts"]}
        for tf in TFS:
            for cost in COSTS:
                m=d["model"][tf+"_"+cost]
                v=m["marked_return_pct"]
                if not math.isfinite(v):raise ValueError("NONFINITE_RETURN:"+s+tf+cost)
                yearly=m["annual_closed_trade_pnl_usdt"]
                rows.append({"symbol":s,"tf":tf,"cost":cost,
                             "net_return_pct":v,
                             "closed_trades":m["closed_trades"],
                             "wins":m["wins"],"win_pct":m["win_rate_pct"],
                             "profit_factor":m["profit_factor"],
                             "max_5m_high_drawdown_pct":m["max_5m_high_stress_dd_pct"],
                             "funding_usdt":m["funding_usdt"],
                             "fees_usdt":m["fees_usdt"],
                             "positive_closed_years":sum(yearly.get(str(y),0)>0 for y in (2023,2024,2025)),
                             "pnl_2023_usdt":yearly.get("2023",0),
                             "pnl_2024_usdt":yearly.get("2024",0),
                             "pnl_2025_usdt":yearly.get("2025",0),
                             "top3_winner_share_pct":m["top3_winner_share_gross_positive_pct"],
                             "closed_pnl_without_top3_static_usdt":m["remaining_closed_pnl_without_top3_static_usdt"],
                             "open_end":m["end_position_open"],
                             "signal_opportunities":m["signal_bars"],
                             "slot_skips":m["skipped_signals_active_slot"]})
    if len(rows)!=80:raise ValueError("NOT_80_UNFILTERED_SHORT_CASES")
    base=sorted((r for r in rows if r["cost"]=="BASE"),
                key=lambda x:x["net_return_pct"],reverse=True)
    stress={(r["symbol"],r["tf"]):r for r in rows if r["cost"]=="STRESS"}
    survived=[]
    for r in base:
        match=stress[(r["symbol"],r["tf"])]
        if (r["net_return_pct"]>0 and match["net_return_pct"]>0 and
             (r["profit_factor"] or 0)>1 and (match["profit_factor"] or 0)>1):
            survived.append({"symbol":r["symbol"],"tf":r["tf"],
                            "base_return_pct":r["net_return_pct"],
                            "stress_return_pct":match["net_return_pct"],
                            "pf":r["profit_factor"],
                            "dd":r["max_5m_high_drawdown_pct"],
                            "positive_years":r["positive_closed_years"],
                            "top3_static_residual":r["closed_pnl_without_top3_static_usdt"]})
    return {"status":"SHORT_80_OF_80_COMPLETED_HISTORICAL_NO_OOS",
            "frozen_source_run":SOURCE_RUN,
            "sources":audit,
            "all80":rows,"base_return_ranking":base,
            "base_and_stress_positive":survived,
            "independent_oos":False,"live_trading_authority":"NONE",
            "venue_funding_settlement_mark_verified":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    args=p.parse_args()
    args.output_dir.mkdir(parents=True,exist_ok=True)
    r=aggregate(args.source_dir)
    (args.output_dir/"SHORT_ALL_80_MASTER.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
    with (args.output_dir/"SHORT_ALL_80_MASTER.csv").open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=r["all80"][0].keys())
        w.writeheader();w.writerows(r["all80"])
    print("SHORT_MASTER_FINAL",json.dumps({"status":r["status"],"sources":r["sources"],
        "top_15":r["base_return_ranking"][:15],
        "base_stress_positive":r["base_and_stress_positive"]},sort_keys=True),flush=True)
if __name__=="__main__":
    main()

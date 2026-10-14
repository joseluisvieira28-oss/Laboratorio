#!/usr/bin/env python3
"""FIVE frozen early-profit 2023-25 retrospective cases. Source and Parent immutable.

Imports already tested original 5m-causal child from source-frozen research branch;
no live exchange, authentication or sealed 2026 market outcomes.
"""
import argparse
from pathlib import Path
import json
import math

from sol_bnb_early_profit_historical import old_code, run_child, M5, END

# Pre-child outcome freeze b3c93b8; parent publications ~two decimal pp.
CANDIDATES={
    "SOL5M": ("SOLUSDT", M5, {"BASE":59.99, "STRESS":57.77}, 182),
    "SOL4H": ("SOLUSDT", 14_400_000, {"BASE":35.90, "STRESS":35.42}, 44),
    "BNB30M": ("BNBUSDT", 1_800_000, {"BASE":19.67, "STRESS":18.17}, 51),
    "ETH1H": ("ETHUSDT", 3_600_000, {"BASE":18.77, "STRESS":18.34}, 47),
    "DOGE4H": ("DOGEUSDT", 14_400_000, {"BASE":15.66, "STRESS":15.26}, 44),
}
PARENT_COMMIT="42d6748864dd78b911b5f1fc775ff1950b556d2b"
COUNTS={"5m":333216,"1h":27768,"funding":3288}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--symbol",choices=["SOLUSDT","BNBUSDT","ETHUSDT","DOGEUSDT"],required=True)
    parser.add_argument("--outdir",type=Path,required=True)
    opt=parser.parse_args()
    opt.outdir.mkdir(parents=True,exist_ok=True)
    report={
        "state":"SOURCE_OR_PARENT_PARITY_BLOCKED",
        "symbol":opt.symbol,"frozen_policy":"b3c93b8163e5ab4b0c13a550a048812f52018b62",
        "original_source_git_sha":PARENT_COMMIT,"independent_oos":False,
        "live_trading_authority":False,
        "period":"2023-01-01..2025-12-31 UTC, 2022-11 warmup",
        "actual_exchange_fills":False,
    }
    try:
        orig,old,base,source=old_code()
        price5,price1,fd,manifest=old.fetch_all(opt.symbol)
        counts={"5m":len(price5),"1h":len(price1),"funding":len(fd)}
        report["source_counts"]=counts
        if counts!=COUNTS:
            raise ValueError("SOURCE_COUNTS_MISMATCH_"+str(counts))
        hourly=base.resample(price5,3_600_000)
        report["hourly_source_parity"]=base.verify_one_hour_parity(hourly,price1)
        report["publisher_zip_checksum_manifest"]=manifest
        report["scenarios"]={}
        ordered=[(cid,tup) for cid,tup in CANDIDATES.items() if tup[0]==opt.symbol]
        assert ordered
        for cid,(symbol,tf,expected,n) in ordered:
            price_bars=([price5[t] for t in sorted(price5)] if tf==M5
                        else base.resample(price5,tf))
            arms={}
            for name,slip in (("BASE",2),("STRESS",5)):
                parent=base.simulate(tf,price_bars,price5,fd,slip,include_trades=True)
                parent_return=parent["marked_return_pct"]
                if not math.isfinite(parent_return) or abs(parent_return-expected[name])>0.08:
                    raise ValueError("PARENT_ECONOMIC_PARITY_FAIL_"+cid+"_"+name+":"+str(parent_return))
                if name=="BASE" and parent["closed_trades"]!=n:
                    raise ValueError("PARENT_TRADE_COUNT_PARITY_FAIL_"+cid+":"+str(parent["closed_trades"]))
                child=run_child(symbol,tf,price_bars,price5,fd,slip,source)
                legs=child.pop("trade_legs")
                fname=f"{cid}_{name}_EARLY_CHILD_LEGS.json"
                (opt.outdir/fname).write_text(json.dumps(legs,sort_keys=True)+"\n")
                if child["closed_trades"]!=child["exit_reasons"].get("STOP_GAP",0)+child["exit_reasons"].get("STOP_INTRABAR",0)+child["exit_reasons"].get("BE_ALREADY_CROSSED_NEXT_OPEN",0):
                    raise ValueError("CHILD_CLOSED_EXIT_REASON_MISMATCH_"+cid+"_"+name)
                if child["exit_legs_count"] != child["closed_trades"]+child["partially_realized_positions"]:
                    raise ValueError("CHILD_PARTIAL_LEDGER_MISMATCH_"+cid+"_"+name)
                original_trades=parent.pop("trades")
                if len(original_trades)!=parent["closed_trades"]:
                    raise ValueError("PARENT_TRADES_AND_CLOSED_COUNT_MISMATCH_"+cid+"_"+name)
                arms[name]={
                    "parent":parent,"child":child,
                    "delta_terminal_marked_pp":child["marked_return_pct"]-parent_return,
                    "delta_closed_cash_pp":child["cash_return_pct"]-parent["realized_cash_return_pct"],
                    "parent_publication_approx_pct":expected[name]
                }
                print("NEXTFIVE_ECONOMIC",cid,name,json.dumps({
                    "parent_marked_pct":parent_return,
                    "child_marked_pct":child["marked_return_pct"],
                    "delta_pp":arms[name]["delta_terminal_marked_pp"],
                    "parent_closed":parent["closed_trades"],
                    "child_closed":child["closed_trades"],
                    "child_partials":child["partially_realized_positions"],
                    "parent_pf":parent["profit_factor"],
                    "child_pf":child["closed_profit_factor"],
                    "parent_low_dd":parent["max_5m_low_stress_dd_pct"],
                    "child_low_dd":child["5m_low_mtm_max_dd_pct"],
                    "no_oos":True
                },sort_keys=True),flush=True)
            report["scenarios"][cid]=arms
        report["state"]="HISTORICAL_5M_PROXY_COMPLETED_NO_NEW_OOS"
    except Exception as exc:
        report["block_reason"]=type(exc).__name__+":"+str(exc)
        print("NEXTFIVE_FAIL_CLOSED",opt.symbol,report["block_reason"],flush=True)
    (opt.outdir/"REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    if report["state"]!="HISTORICAL_5M_PROXY_COMPLETED_NO_NEW_OOS":
        raise SystemExit(2)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Reproducible, strictly descriptive attribution from PR195 frozen artifact.
No order/exchange/account requests and NO retuning or independent OOS claims.
"""
import argparse,datetime as dt,json,math,statistics
from collections import Counter
from pathlib import Path
UTC=dt.timezone.utc
H=3600000
YEARS=(2022,2025)
MODELS=("PARENT","4R")
SCENARIOS={"BASE":.0008,"STRESS":.001}
def year(ts):return dt.datetime.fromtimestamp(int(ts)/1000,UTC).year
def median(nums):return statistics.median(nums) if nums else None

def partition(trades,fee):
    tr=sorted(trades,key=lambda t:(t["exit_t"],t["entry_t"]))
    total={"trades":len(tr),"wins":0,"losses":0,"gross_price_usdt":0.,
           "fees_usdt":0.,"funding_usdt":0.,"net_usdt":0.,
           "gap_exit_count":0,"worst_stop_gap_on_margin":None,
           "maximum_consecutive_losses":0,"exit_reasons":dict(Counter(t["reason"] for t in tr))}
    durations=[];streak=0
    for t in tr:
        e=float(t["fill"]);p=float(t["exit_fill"]);q=float(t["qty"])
        gross=(p-e)*q
        fees=float(t["entry_fee"])+p*q*fee
        fund=float(t["funding_cash"])
        net=gross-fees+fund
        if not math.isclose(net,float(t["net_pnl"]),rel_tol=1e-11,abs_tol=1e-7):
            raise ValueError("LEDGER_CASH_IDENTITY_MISMATCH")
        if min(e,p,q)<=0 or t["exit_t"]<t["entry_t"]:
            raise ValueError("INVALID_TRADE")
        durations.append((t["exit_t"]-t["entry_t"])/H)
        total["gross_price_usdt"]+=gross;total["fees_usdt"]+=fees
        total["funding_usdt"]+=fund;total["net_usdt"]+=net
        if net>0:total["wins"]+=1;streak=0
        else:total["losses"]+=1;streak+=1
        total["maximum_consecutive_losses"]=max(streak,total["maximum_consecutive_losses"])
        if "GAP" in t["reason"]:
            total["gap_exit_count"]+=1
            if "STOP" in t["reason"]:
                r=float(t["margin_net_return"])
                prev=total["worst_stop_gap_on_margin"]
                total["worst_stop_gap_on_margin"]=r if prev is None else min(prev,r)
    total["median_duration_hours"]=median(durations)
    total["max_duration_hours"]=max(durations) if durations else None
    return total

def run(data):
    if data.get("classification")!="EXPLORATORY_IN_SAMPLE_ZERO_PROMOTION":
        raise ValueError("SOURCE_CLASSIFICATION_MISMATCH")
    result={"verdict":"RETRO_FAILURE_DIAGNOSTIC_ONLY","live_authority":"NONE",
            "execution_validation":"MODEL_COSTS_ONLY_NOT_REAL_FILL",
            "models":{},"explanatory_features_status":"NO_MARKET_BAR_SOURCE_ATTACHED"}
    for scenario,fee in SCENARIOS.items():
        result["models"][scenario]={}
        for model in MODELS:
            record=data["scenarios"][scenario][model]
            ledger=record["ledger"]
            if len(ledger)!=record["closed"]:raise ValueError("LEDGER_COUNT_MISMATCH")
            segments={}
            for axis in ("entry_t","exit_t"):
                segments[axis]={
                    str(y):partition([t for t in ledger if year(t[axis])==y],fee)
                    for y in range(2020,2026)}
            result["models"][scenario][model]={
                "by_entry_year":segments["entry_t"],"by_exit_year":segments["exit_t"],
                "overall":partition(ledger,fee),
                "published_yearly_equity_returns":record["historical_year_cash_returns"],
                "open_at_right_edge_count":len(record["unresolved_at_cutoff"]),
                "replay_mark_liquidation_warning_hours":record["mark_liquidation_warning_hours"]}
    return result

def report(data):
    lines=["# BTC PAYOFF 4R vs Parent — failure mechanism audit","",
           "**RETROSPECTIVE only. No live trading, no regime-filter promotion.**","",
           "Numbers use the original PR195 public-source event ledgers; slippage is embedded in simulated entry/exit fills, not separable as an observed execution fee. Monetary yearly decomposition is grouped by *exit year*, not equity-year return. All closed trades included.","",
           "|Scenario|Model|Exit year|Trades|Winners|Gross price USDT|Fees USDT|Funding USDT|Net USDT|Max losing streak|Median duration (hours)|",
           "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for s in SCENARIOS:
        for m in MODELS:
            for year in YEARS:
                t=data["models"][s][m]["by_exit_year"][str(year)]
                lines.append("|"+ "|".join([s,m,str(year),str(t["trades"]),str(t["wins"]),
                    f"{t['gross_price_usdt']:.2f}",f"{-t['fees_usdt']:.2f}",
                    f"{t['funding_usdt']:.2f}",f"{t['net_usdt']:.2f}",
                    str(t["maximum_consecutive_losses"]),str(t["median_duration_hours"] or 0)])+"|")
    lines+=["","**Attribution:** 2022 and 2025 negative equity results are primarily linked to adverse price moves in the *already-executed hypothetical positions*, not just venue costs. It does not establish which pre-entry regime feature caused the losses.","",
            "**Limits:** original 2020–25 BTC outcomes already studied; venue-specific depth, spread, historic minimum order, liquidation ladder, mark execution and personal fee rates are unverified. No filters tested or adopted.",""]
    return "\n".join(lines)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--diagnostic",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--report",type=Path,required=True)
    a=p.parse_args()
    d=json.loads(a.diagnostic.read_text())
    result=run(d);a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    a.report.write_text(report(result)+"\n")
    print(report(result))
if __name__=="__main__":main()

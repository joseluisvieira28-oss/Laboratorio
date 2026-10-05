#!/usr/bin/env python3
import json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_INTRADAY_SHOCK_RULE_V1.2.json").read_text())
B=json.loads((HERE/"MEXC_INTRADAY_SHOCK_SOURCE_BINDING_V1.2.json").read_text())
IN=Path("artifacts/mexc_global_assets/intraday_shock_v12/assets");OUT=Path("artifacts/mexc_global_assets/intraday_shock_v12")
def mean(x):return sum(x)/len(x) if x else None
def med(x):return statistics.median(x) if x else None
def binom(w,n):return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def main():
    rec=[json.loads(p.read_text()) for p in IN.glob("*.json")]
    exp={x["target"] for x in B["candidates"]}
    if {x["target"] for x in rec}!=exp:raise SystemExit("FAIL_CLOSED_RECEIPT_SET")
    days={}
    all_events=[]
    for x in rec:
        for e in x["events"]:
            days.setdefault(e["date"],[]).append(e)
            all_events.append({"target":x["target"],**e})
    daily=[]
    for d in sorted(days):
        vals=[e["gross_bps"] for e in days[d]]
        daily.append({"date":d,"trade_count":len(vals),"gross_bps":mean(vals),"net16_bps":mean(vals)-16})
    gross=[x["gross_bps"] for x in daily];net16=[x["net16_bps"] for x in daily]
    n=len(gross);wins=sum(x>0 for x in gross);k=n//2
    halves=[mean(gross[:k]),mean(gross[k:])] if n>=2 else [None,None]
    g=R["scientific_gate"]
    sci=bool(len(all_events)>=g["min_total_triggered_trades"] and n>=g["min_triggered_days"] and mean(gross)>0 and med(gross)>0 and wins/n>g["win_day_rate_gt"] and all(x is not None and x>0 for x in halves) and binom(wins,n)<g["exact_one_sided_binomial_p_lt"])
    robust=bool(sci and mean(net16)>0 and med(net16)>0)
    verdict="INTRADAY_SHOCK_ROBUST_API_FEE_SURVIVOR__EXECUTION_VALIDATION_REQUIRED" if robust else ("INTRADAY_SHOCK_SCIENTIFIC_PASS__API_FEE_BLOCKED" if sci else ("INTRADAY_SHOCK_UNDERPOWERED_AT_FROZEN_V12_GATE" if len(all_events)<g["min_total_triggered_trades"] or n<g["min_triggered_days"] else "INTRADAY_SHOCK_NO_EDGE_AT_FROZEN_V12_GATE"))
    rep={"overall_verdict":verdict,"total_trades":len(all_events),"triggered_days":n,"winning_days":wins,
         "win_day_rate":wins/n if n else None,"mean_daily_gross_bps":mean(gross),"median_daily_gross_bps":med(gross),
         "half_means_bps":halves,"p_one_sided_binomial":binom(wins,n),"mean_daily_net16_bps":mean(net16),"median_daily_net16_bps":med(net16),
         "scientific_pass":sci,"robust_api_fee_survivor":robust,"daily":daily,"events":all_events,
         "orders":False,"live_trading":False}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"MEXC_INTRADAY_SHOCK_CLOSEOUT_V12.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({k:rep[k] for k in ["overall_verdict","total_trades","triggered_days","winning_days","win_day_rate","mean_daily_gross_bps","median_daily_gross_bps","half_means_bps","p_one_sided_binomial","mean_daily_net16_bps","median_daily_net16_bps","scientific_pass","robust_api_fee_survivor"]},indent=2))
if __name__=="__main__":main()

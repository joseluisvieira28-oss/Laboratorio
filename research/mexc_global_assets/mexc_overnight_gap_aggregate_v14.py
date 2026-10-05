#!/usr/bin/env python3
import json,math,statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_OVERNIGHT_GAP_RULE_V1.4.json").read_text())
B=json.loads((HERE/"MEXC_OVERNIGHT_GAP_SOURCE_BINDING_V1.4.json").read_text())
IN=Path("artifacts/mexc_global_assets/overnight_gap_v14/assets")
OUT=Path("artifacts/mexc_global_assets/overnight_gap_v14")

def mean(x): return sum(x)/len(x) if x else None
def med(x): return statistics.median(x) if x else None
def halves(v):
    n=len(v); k=n//2
    return [mean(v[:k]),mean(v[k:])] if n>=2 else [None,None]
def binom(w,n): return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None

def main():
    expected={x["target"] for x in B["candidates"]}
    rec=[json.loads(p.read_text()) for p in IN.glob("*.json")]
    got={x["target"] for x in rec}
    if got!=expected: raise SystemExit(f"FAIL_CLOSED_RECEIPTS missing={sorted(expected-got)} extra={sorted(got-expected)}")
    bydate={}; total=0
    for x in rec:
        for o in x["triggered_observations"]:
            bydate.setdefault(o["date"],[]).append({"target":x["target"],**o}); total+=1
    days=[]
    for ds in sorted(bydate):
        xs=bydate[ds]; gross=mean([x["signed_gross_30m_bps"] for x in xs])
        days.append({"date":ds,"triggered_assets":len(xs),"gross_basket_bps":gross,
                     "median_trade_gross_bps":med([x["signed_gross_30m_bps"] for x in xs]),
                     "assets":[x["target"] for x in xs],
                     "net_basket_bps":{str(c):gross-c for c in R["cost_scenarios_roundtrip_bps"]}})
    vals=[x["gross_basket_bps"] for x in days]
    n=len(vals); w=sum(x>0 for x in vals); h=halves(vals); mg=mean(vals); md=med(vals); p=binom(w,n)
    g=R["scientific_gate"]
    sci=bool(total>=g["min_total_triggered_trades"] and n>=g["min_triggered_days"] and
             mg is not None and mg>0 and md is not None and md>0 and
             w/n>g["winning_day_rate_gt"] and all(x is not None and x>0 for x in h) and
             p<g["exact_one_sided_binomial_p_lt"])
    mean_net={str(c):mean([x["net_basket_bps"][str(c)] for x in days]) for c in R["cost_scenarios_roundtrip_bps"]} if days else {}
    med_net={str(c):med([x["net_basket_bps"][str(c)] for x in days]) for c in R["cost_scenarios_roundtrip_bps"]} if days else {}
    robust=bool(sci and mean_net["16"]>0 and med_net["16"]>0)
    if total<g["min_total_triggered_trades"] or n<g["min_triggered_days"]:
        verdict="OVERNIGHT_GAP_UNDERPOWERED_AT_FROZEN_V14_GATE"
    elif robust:
        verdict="OVERNIGHT_GAP_ROBUST_API_FEE_SURVIVOR__EXECUTION_VALIDATION_REQUIRED"
    elif sci:
        verdict="OVERNIGHT_GAP_SCIENTIFIC_PASS__API_FEE_BLOCKED"
    else:
        verdict="NO_OVERNIGHT_GAP_SURVIVOR_AT_FROZEN_V14_GATE"
    metrics={"total_triggered_trades":total,"triggered_days":n,"mean_daily_gross_bps":mg,
             "median_daily_gross_bps":md,"winning_days":w,"win_day_rate":w/n if n else None,
             "half_means_bps":h,"p_one_sided_binomial":p,"mean_daily_net_bps":mean_net,
             "median_daily_net_bps":med_net,"scientific_pass":sci,"robust_api_fee_survivor":robust}
    report={"overall_verdict":verdict,"metrics":metrics,"daily_baskets":days,
            "private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading_authorized":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_OVERNIGHT_GAP_CLOSEOUT_V14.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps(report,indent=2))

if __name__=="__main__": main()

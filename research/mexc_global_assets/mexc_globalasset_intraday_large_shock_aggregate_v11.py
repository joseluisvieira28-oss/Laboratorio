#!/usr/bin/env python3
from __future__ import annotations
import json,math,statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_GLOBALASSET_INTRADAY_LARGE_SHOCK_RULE_V1.1.json").read_text())
B=json.loads((HERE/"MEXC_GLOBALASSET_INTRADAY_LARGE_SHOCK_SOURCE_BINDING_V1.1.json").read_text())
IN=Path("artifacts/mexc_global_assets/intraday_large_shock_v11/assets")
OUT=Path("artifacts/mexc_global_assets/intraday_large_shock_v11")

def mean(x):return sum(x)/len(x) if x else None
def med(x):return statistics.median(x) if x else None
def binom(w,n):return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def halves(v):
    n=len(v); k=n//2
    return [mean(v[:k]),mean(v[k:])] if n>=2 else [None,None]

def main():
    expected={x["target"] for x in B["candidates"]}
    receipts=[json.loads(p.read_text()) for p in IN.glob("*.json")]
    got={x["target"] for x in receipts}
    if got!=expected:raise SystemExit(f"FAIL_CLOSED_RECEIPT_SET missing={sorted(expected-got)} extra={sorted(got-expected)}")
    raw=[]
    for rec in receipts:
        for e in rec["raw_triggers"]:
            x=dict(e);x["target"]=rec["target"];raw.append(x)
    by_ts={}
    for x in raw:by_ts.setdefault(x["timestamp"],[]).append(x)
    admitted=[];last=None;cool=R["global_cooldown_min"]*60
    for t in sorted(by_ts):
        if last is not None and t-last<cool:continue
        xs=by_ts[t];gross=mean([x["gross_signed_bps"] for x in xs])
        admitted.append({"timestamp":t,"signal_utc":xs[0]["signal_utc"],"date":xs[0]["date"],
                         "triggered_assets":len(xs),"gross_event_basket_bps":gross,
                         "assets":[x["target"] for x in xs],
                         "net_event_basket_bps":{str(c):gross-float(c) for c in R["cost_scenarios_roundtrip_bps"]}})
        last=t
    by_day={}
    for e in admitted:by_day.setdefault(e["date"],[]).append(e)
    daily=[]
    for d in sorted(by_day):
        vals=[e["gross_event_basket_bps"] for e in by_day[d]]
        gross=mean(vals)
        daily.append({"date":d,"event_baskets":len(vals),"gross_daily_basket_bps":gross,
                      "net_daily_basket_bps":{str(c):gross-float(c) for c in R["cost_scenarios_roundtrip_bps"]}})
    vals=[x["gross_daily_basket_bps"] for x in daily]
    wins=sum(x>0 for x in vals);g=R["scientific_gate"]
    metrics={"raw_trigger_rows":len(raw),"admitted_event_baskets":len(admitted),"triggered_days":len(daily),
             "mean_daily_gross_bps":mean(vals),"median_daily_gross_bps":med(vals),
             "winning_days":wins,"win_day_rate":wins/len(vals) if vals else None,
             "half_means_bps":halves(vals),"p_one_sided_binomial":binom(wins,len(vals)),
             "mean_daily_net_bps":{str(c):(mean(vals)-float(c) if vals else None) for c in R["cost_scenarios_roundtrip_bps"]},
             "median_daily_net_bps":{str(c):(med(vals)-float(c) if vals else None) for c in R["cost_scenarios_roundtrip_bps"]}}
    enough=metrics["admitted_event_baskets"]>=g["min_admitted_event_baskets"] and metrics["triggered_days"]>=g["min_triggered_days"]
    sci=bool(enough and metrics["mean_daily_gross_bps"]>0 and metrics["median_daily_gross_bps"]>0 and
             metrics["win_day_rate"]>g["win_day_rate_gt"] and
             all(x is not None and x>0 for x in metrics["half_means_bps"]) and
             metrics["p_one_sided_binomial"]<g["exact_one_sided_binomial_p_lt"])
    robust=bool(sci and metrics["mean_daily_net_bps"]["16"]>0 and metrics["median_daily_net_bps"]["16"]>0)
    metrics["scientific_pass"]=sci;metrics["robust_api_fee_survivor"]=robust
    if not enough:verdict="UNDERPOWERED"
    elif robust:verdict="ROBUST_API_FEE_SURVIVOR"
    elif sci:verdict="SCIENTIFIC_PASS_FEE_BLOCKED"
    else:verdict="NO_EDGE"
    rep={"family_id":R["family_id"],"overall_verdict":verdict,"metrics":metrics,
         "daily_baskets":daily,"admitted_event_baskets":admitted,"raw_trigger_rows":raw,
         "post_outcome_tuning":False,"orders":False,"account_reads":False,
         "private_endpoints_used":False,"live_trading":False}
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/"MEXC_GLOBALASSET_INTRADAY_LARGE_SHOCK_CLOSEOUT_V11.json"
    p.write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps({"overall_verdict":verdict,"metrics":metrics,"daily_baskets":daily},indent=2,sort_keys=True))
if __name__=="__main__":main()

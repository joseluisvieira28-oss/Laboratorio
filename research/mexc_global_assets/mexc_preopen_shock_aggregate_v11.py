#!/usr/bin/env python3
from __future__ import annotations
import json,math,statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_PREOPEN_SHOCK_RULE_V1.1.json").read_text())
B=json.loads((HERE/"MEXC_PREOPEN_SHOCK_SOURCE_BINDING_V1.1.json").read_text())
IN=Path("artifacts/mexc_global_assets/preopen_shock_v11/assets")
OUT=Path("artifacts/mexc_global_assets/preopen_shock_v11")

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
    by_day={}
    all_trades=[]
    for rec in receipts:
        for e in rec["events"]:
            if not e.get("triggered"):continue
            x={"target":rec["target"],"date":e["date"],"gross_signed_bps":e["gross_signed_bps"],
               "external_60m_bps":e["external_60m_bps"],"mexc_60m_bps":e["mexc_60m_bps"],"lag_gap_bps":e["lag_gap_bps"]}
            all_trades.append(x);by_day.setdefault(e["date"],[]).append(x)
    daily=[]
    for d in sorted(by_day):
        vals=[x["gross_signed_bps"] for x in by_day[d]]
        gross=mean(vals)
        daily.append({"date":d,"triggered_assets":len(vals),"gross_basket_bps":gross,
          "median_trade_gross_bps":med(vals),"assets":[x["target"] for x in by_day[d]],
          "net_basket_bps":{str(c):gross-float(c) for c in R["cost_scenarios_roundtrip_bps"]}})
    vals=[x["gross_basket_bps"] for x in daily]
    wins=sum(x>0 for x in vals);g=R["scientific_gate"]
    metrics={"total_triggered_trades":len(all_trades),"triggered_days":len(daily),
      "mean_daily_gross_bps":mean(vals),"median_daily_gross_bps":med(vals),
      "winning_days":wins,"win_day_rate":wins/len(vals) if vals else None,
      "half_means_bps":halves(vals),"p_one_sided_binomial":binom(wins,len(vals)),
      "mean_daily_net_bps":{str(c):(mean(vals)-float(c) if vals else None) for c in R["cost_scenarios_roundtrip_bps"]},
      "median_daily_net_bps":{str(c):(med(vals)-float(c) if vals else None) for c in R["cost_scenarios_roundtrip_bps"]}}
    enough=metrics["total_triggered_trades"]>=g["min_total_triggered_trades"] and metrics["triggered_days"]>=g["min_triggered_days"]
    sci=bool(enough and metrics["mean_daily_gross_bps"]>0 and metrics["median_daily_gross_bps"]>0 and
      metrics["win_day_rate"]>g["win_day_rate_gt"] and all(x is not None and x>0 for x in metrics["half_means_bps"]) and
      metrics["p_one_sided_binomial"]<g["exact_one_sided_binomial_p_lt"])
    robust=bool(sci and metrics["mean_daily_net_bps"]["16"]>0 and metrics["median_daily_net_bps"]["16"]>0)
    metrics["scientific_pass"]=sci;metrics["robust_api_fee_survivor"]=robust
    if not enough:verdict="PREOPEN_SHOCK_UNDERPOWERED_AT_FROZEN_V11_GATE"
    elif robust:verdict="PREOPEN_SHOCK_ROBUST_API_FEE_SURVIVOR__EXECUTION_VALIDATION_REQUIRED"
    elif sci:verdict="PREOPEN_SHOCK_SCIENTIFIC_PASS__API_FEE_BLOCKED"
    else:verdict="NO_PREOPEN_SHOCK_EDGE_AT_FROZEN_V11_GATE"
    report={"family_id":R["family_id"],"overall_verdict":verdict,"metrics":metrics,
            "daily_baskets":daily,"triggered_trades":all_trades,
            "post_outcome_tuning":False,"orders":False,"account_reads":False,"live_trading":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_PREOPEN_SHOCK_CLOSEOUT_V11.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({"overall_verdict":verdict,"metrics":metrics,
      "daily_baskets":daily},indent=2))
if __name__=="__main__":main()

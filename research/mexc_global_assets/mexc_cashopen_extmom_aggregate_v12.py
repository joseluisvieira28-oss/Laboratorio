#!/usr/bin/env python3
import json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_CASHOPEN_EXTMOM_RULE_V1.2.json").read_text())
B=json.loads((HERE/"MEXC_CASHOPEN_EXTMOM_SOURCE_BINDING_V1.2.json").read_text())
IN=Path("artifacts/mexc_global_assets/cashopen_extmom_v12/assets");OUT=Path("artifacts/mexc_global_assets/cashopen_extmom_v12")
def mean(x):return sum(x)/len(x) if x else None
def med(x):return statistics.median(x) if x else None
def halves(v):
 n=len(v);k=n//2
 return [mean(v[:k]),mean(v[k:])] if n>=2 else [None,None]
def binom(w,n):return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def main():
 expected={x["target"] for x in B["candidates"]};files=list(IN.glob("*.json"));rec=[json.loads(p.read_text()) for p in files]
 got={x["target"] for x in rec}
 if got!=expected:raise SystemExit(f"FAIL_CLOSED_RECEIPT_SET missing={sorted(expected-got)} extra={sorted(got-expected)}")
 bydate={}
 for x in rec:
  for o in x["observations"]:
   bydate.setdefault(o["date"],[]).append({"target":x["target"],**o})
 days=[]
 for ds in sorted(bydate):
  xs=bydate[ds];gross=mean([x["signed_gross_bps"] for x in xs])
  days.append({"date":ds,"asset_count":len(xs),"gross_basket_bps":gross,
               "median_asset_gross_bps":med([x["signed_gross_bps"] for x in xs]),
               "net_basket_bps":{str(c):gross-c for c in R["cost_scenarios_roundtrip_bps"]}})
 vals=[x["gross_basket_bps"] for x in days];n=len(vals);w=sum(x>0 for x in vals);h=halves(vals);mg=mean(vals);md=med(vals);p=binom(w,n)
 g=R["scientific_gate"]
 sci=bool(n>=g["min_complete_basket_days"] and mg>0 and md>0 and w/n>g["winning_day_rate_gt"] and all(x is not None and x>0 for x in h) and p<g["exact_one_sided_binomial_p_lt"])
 robust=bool(sci and mean([x["net_basket_bps"]["16"] for x in days])>0 and med([x["net_basket_bps"]["16"] for x in days])>0)
 metrics={"basket_days":n,"mean_assets_per_day":mean([x["asset_count"] for x in days]),"min_assets_per_day":min([x["asset_count"] for x in days]) if days else None,
 "mean_daily_gross_bps":mg,"median_daily_gross_bps":md,"winning_days":w,"win_day_rate":w/n if n else None,"half_means_bps":h,
 "p_one_sided_binomial":p,"mean_daily_net_bps":{str(c):mean([x["net_basket_bps"][str(c)] for x in days]) for c in R["cost_scenarios_roundtrip_bps"]},
 "median_daily_net_bps":{str(c):med([x["net_basket_bps"][str(c)] for x in days]) for c in R["cost_scenarios_roundtrip_bps"]},
 "scientific_pass":sci,"robust_api_fee_survivor":robust}
 verdict="CASHOPEN_EXTMOM_ROBUST_API_FEE_SURVIVOR__EXECUTION_VALIDATION_REQUIRED" if robust else ("CASHOPEN_EXTMOM_SCIENTIFIC_PASS__API_FEE_BLOCKED" if sci else "NO_CASHOPEN_EXTMOM_BASKET_SURVIVOR_AT_FROZEN_V12_GATE")
 report={"overall_verdict":verdict,"metrics":metrics,"daily_baskets":days,"live_trading_authorized":False,"orders":False}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"MEXC_CASHOPEN_EXTMOM_CLOSEOUT_V12.json").write_text(json.dumps(report,indent=2,sort_keys=True))
 print(json.dumps(report,indent=2))
if __name__=="__main__":main()

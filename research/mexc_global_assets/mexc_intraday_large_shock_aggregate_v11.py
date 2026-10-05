#!/usr/bin/env python3
import json,math,statistics
from pathlib import Path
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_INTRADAY_LARGE_SHOCK_RULE_V1.1.json").read_text());IN=Path("artifacts/mexc_global_assets/intraday_large_shock_v11/assets");OUT=IN.parent
def mean(x):return sum(x)/len(x) if x else None
def med(x):return statistics.median(x) if x else None
def binom(w,n):return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def main():
 rec=[json.loads(p.read_text()) for p in IN.glob("*.json")];tr=[dict(x,target=r["target"]) for r in rec for x in r["trades"]];by={}
 for x in tr:by.setdefault(x["date"],[]).append(x["gross_bps"])
 daily=[{"date":d,"gross_bps":mean(v),"n":len(v)} for d,v in sorted(by.items())];v=[x["gross_bps"] for x in daily];n=len(v);w=sum(x>0 for x in v);k=n//2;halves=[mean(v[:k]),mean(v[k:])] if n>=2 else [None,None]
 mg=mean(v);md=med(v);p=binom(w,n);G=R["scientific_gate"];E=R["economic_gate"]
 sci=bool(len(tr)>=G["min_total_trades"] and n>=G["min_triggered_days"] and mg is not None and mg>0 and md>0 and w/n>G["win_day_rate_gt"] and all(x is not None and x>0 for x in halves) and p<G["exact_one_sided_binomial_p_lt"])
 econ=bool(sci and mg>E["mean_daily_gross_gt_bps"] and md>E["median_daily_gross_gt_bps"])
 verdict="ROBUST_16BPS_INTRADAY_SURVIVOR__EXECUTION_VALIDATION_REQUIRED" if econ else ("SCIENTIFIC_INTRADAY_SURVIVOR__FEE_BLOCKED" if sci else ("INTRADAY_LARGE_SHOCK_UNDERPOWERED" if len(tr)<G["min_total_trades"] or n<G["min_triggered_days"] else "NO_INTRADAY_LARGE_SHOCK_EDGE_AT_FROZEN_V11_GATE"))
 rep={"verdict":verdict,"total_trades":len(tr),"triggered_days":n,"winning_days":w,"win_day_rate":w/n if n else None,"mean_daily_gross_bps":mg,"median_daily_gross_bps":md,"halves":halves,"p":p,"scientific_pass":sci,"economic_16bps_pass":econ,"net_after_16_mean":mg-16 if mg is not None else None,"net_after_16_median":md-16 if md is not None else None,"daily":daily,"orders":False,"live_trading":False}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"MEXC_INTRADAY_LARGE_SHOCK_CLOSEOUT_V11.json").write_text(json.dumps(rep,indent=2,sort_keys=True));print(json.dumps({k:rep[k] for k in ["verdict","total_trades","triggered_days","winning_days","win_day_rate","mean_daily_gross_bps","median_daily_gross_bps","halves","p","scientific_pass","economic_16bps_pass","net_after_16_mean","net_after_16_median"]},indent=2))
if __name__=="__main__":main()

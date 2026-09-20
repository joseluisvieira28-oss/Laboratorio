#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.parse, urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

BASE="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
START="2018-01-01"; END="2025-12-31"

def fetch():
    q=urllib.parse.urlencode({
      "assets":"btc","metrics":"CapMVRVCur,PriceUSD","frequency":"1d",
      "start_time":START,"end_time":END,"page_size":"10000"
    })
    req=urllib.request.Request(BASE+"?"+q,headers={"User-Agent":"CryptoLab-BMV-Discovery/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r:
        obj=json.loads(r.read())
    d=pd.DataFrame(obj.get("data",[]))
    need=["time","CapMVRVCur","PriceUSD"]
    if not set(need).issubset(d.columns):
        raise RuntimeError("missing source columns")
    d["time"]=pd.to_datetime(d["time"],utc=True,errors="coerce")
    for c in ["CapMVRVCur","PriceUSD"]: d[c]=pd.to_numeric(d[c],errors="coerce")
    d=d.dropna(subset=need).copy()
    d=d[(d["CapMVRVCur"]>0)&(d["PriceUSD"]>0)].sort_values("time").drop_duplicates("time",keep="last")
    return d

def fit_hac(d):
    X=sm.add_constant(d["x"].astype(float)); y=d["y"].astype(float)
    fit=sm.OLS(y,X).fit(cov_type="HAC",cov_kwds={"maxlags":30})
    return {
      "alpha":float(fit.params["const"]),"beta":float(fit.params["x"]),
      "beta_t_hac":float(fit.tvalues["x"]),"beta_p_hac":float(fit.pvalues["x"]),
      "r2":float(fit.rsquared),"n":int(fit.nobs)
    }

def spread_stats(d,cuts=None):
    z=d.copy()
    if cuts is None:
        q=np.quantile(z["x"],[.2,.4,.6,.8])
    else:
        q=np.asarray(cuts,float)
    z["q"]=np.searchsorted(q,z["x"].to_numpy(float),side="right")+1
    low=z[z["q"]==1]["y"]; high=z[z["q"]==5]["y"]
    spread=float(low.mean()-high.mean()) if len(low) and len(high) else float("nan")
    yearly={}
    for yr,g in z.groupby(z["time"].dt.year):
        lo=g[g["q"]==1]["y"]; hi=g[g["q"]==5]["y"]
        yearly[str(int(yr))]=None if not len(lo) or not len(hi) else float(lo.mean()-hi.mean())
    pos=sum(v is not None and v>0 for v in yearly.values())
    return {"cuts":[float(v) for v in q],"low_N":int(len(low)),"high_N":int(len(high)),
            "low_mean":float(low.mean()) if len(low) else None,
            "high_mean":float(high.mean()) if len(high) else None,
            "low_minus_high_spread":spread,"year_spreads":yearly,
            "positive_year_spread_count":int(pos)}

def main():
    d=fetch()
    expected=len(pd.date_range(START,END,freq="D",tz="UTC"))
    cov=d["time"].dt.floor("D").nunique()/expected
    if cov<.95:
        out={"verdict":"BLOCKED_SOURCE","coverage":cov,"holdout_opened":False,"year_2026_opened":False}
        Path("bmv_final_receipt_v01.json").write_text(json.dumps(out,indent=2)+"\n")
        print(json.dumps(out)); return 2

    d["x"]=np.log(d["CapMVRVCur"])
    px=d.set_index("time")["PriceUSD"]
    d["exit_time"]=d["time"]+pd.Timedelta(days=30)
    d["exit_price"]=d["exit_time"].map(px)
    d["y"]=np.log(d["exit_price"]/d["PriceUSD"])

    disc=d[(d["time"]>=pd.Timestamp("2019-01-01",tz="UTC"))&
           (d["time"]<=pd.Timestamp("2023-12-31",tz="UTC"))].dropna(subset=["x","y"]).copy()
    if len(disc)<1500:
        out={"verdict":"INSUFFICIENT_SAMPLE","discovery_N":len(disc),"holdout_opened":False,"year_2026_opened":False}
        Path("bmv_final_receipt_v01.json").write_text(json.dumps(out,indent=2)+"\n")
        print(json.dumps(out)); return 0

    ds=fit_hac(disc); sp=spread_stats(disc)
    dg={
      "N_gte_1500":len(disc)>=1500,
      "beta_lt_0":ds["beta"]<0,
      "HAC_t_lte_minus_2":ds["beta_t_hac"]<=-2.0,
      "R2_gte_0_01":ds["r2"]>=.01,
      "low_minus_high_spread_gt_0":sp["low_minus_high_spread"]>0,
      "positive_year_spreads_gte_3":sp["positive_year_spread_count"]>=3
    }
    dpass=all(dg.values())
    discovery={"sample":"2019-2023","regression":ds,"quintile":sp,"gates":dg,
               "verdict":"DISCOVERY_PASS" if dpass else "DISCOVERY_FAIL_NO_PROMOTION"}
    Path("bmv_discovery_receipt_v01.json").write_text(json.dumps(discovery,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"discovery":discovery},sort_keys=True))
    if not dpass:
        out={"lab_id":"BTC-MVRV-VALUATION-001","verdict":"DISCOVERY_FAIL_NO_PROMOTION",
             "discovery":discovery,"holdout_opened":False,"year_2026_opened":False}
        Path("bmv_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        return 0

    hold=d[(d["time"]>=pd.Timestamp("2024-01-01",tz="UTC"))&
           (d["time"]<=pd.Timestamp("2025-12-01",tz="UTC"))].dropna(subset=["x","y"]).copy()
    hs=fit_hac(hold); hsp=spread_stats(hold,sp["cuts"])
    hold["pred"]=ds["alpha"]+ds["beta"]*hold["x"]
    bench=float(disc["y"].mean())
    sse=float(((hold["y"]-hold["pred"])**2).sum())
    sseb=float(((hold["y"]-bench)**2).sum())
    oos=1-sse/sseb if sseb>0 else float("nan")
    rmse=float(np.sqrt(np.mean((hold["y"]-hold["pred"])**2)))
    rmseb=float(np.sqrt(np.mean((hold["y"]-bench)**2)))
    acc=float((np.sign(hold["pred"])==np.sign(hold["y"])).mean())
    hg={
      "N_gte_650":len(hold)>=650,
      "fixed_model_OOS_R2_gt_0":oos>0,
      "fixed_model_sign_accuracy_gt_0_50":acc>.50,
      "frozen_low_minus_high_spread_gt_0":hsp["low_minus_high_spread"]>0,
      "holdout_beta_lt_0":hs["beta"]<0,
      "holdout_HAC_t_lte_minus_1_645":hs["beta_t_hac"]<=-1.645
    }
    hpass=all(hg.values())
    verdict="SURVIVES_2024_2025_HOLDOUT" if hpass else "DISCOVERY_PASS_HOLDOUT_FAIL"
    out={"lab_id":"BTC-MVRV-VALUATION-001","experiment_id":"BMV-30D-VALUATION-001",
         "verdict":verdict,"source_coverage":float(cov),"discovery":discovery,
         "holdout_2024_2025":{"N":int(len(hold)),"regression":hs,"quintile":hsp,
                              "fixed_model_oos_r2":float(oos),"fixed_model_sign_accuracy":acc,
                              "rmse_model":rmse,"rmse_benchmark":rmseb,"gates":hg},
         "holdout_opened":True,"year_2026_opened":False,"pnl_opened":False}
    Path("bmv_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    disc.to_csv("bmv_discovery_rows_v01.csv",index=False)
    hold.to_csv("bmv_holdout_rows_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())

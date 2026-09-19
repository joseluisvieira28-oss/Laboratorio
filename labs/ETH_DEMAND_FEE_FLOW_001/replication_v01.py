#!/usr/bin/env python3
from __future__ import annotations
import json, math, urllib.parse, urllib.request
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

BASE="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
START="2023-11-01"; END="2025-12-31"
METRICS=["FeeTotNtv","SplyCur","PriceUSD"]

def fetch():
    q=urllib.parse.urlencode({
      "assets":"eth","metrics":",".join(METRICS),"frequency":"1d",
      "start_time":START,"end_time":END,"page_size":"10000"
    })
    req=urllib.request.Request(BASE+"?"+q,headers={"User-Agent":"CryptoLab-EDFF-Replication/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: obj=json.loads(r.read())
    d=pd.DataFrame(obj.get("data",[]))
    d["time"]=pd.to_datetime(d["time"],utc=True,errors="coerce")
    for c in METRICS:d[c]=pd.to_numeric(d[c],errors="coerce")
    d=d.dropna(subset=["time"]+METRICS).sort_values("time").drop_duplicates("time",keep="last")
    d=d[(d["FeeTotNtv"]>0)&(d["SplyCur"]>0)&(d["PriceUSD"]>0)].copy()
    return d

def ols_hac(d):
    X=sm.add_constant(d["fd"].astype(float))
    y=d["fwd45"].astype(float)
    fit=sm.OLS(y,X).fit(cov_type="HAC",cov_kwds={"maxlags":45})
    return {
      "alpha":float(fit.params["const"]),
      "beta":float(fit.params["fd"]),
      "beta_t_hac":float(fit.tvalues["fd"]),
      "beta_p_hac":float(fit.pvalues["fd"]),
      "r2":float(fit.rsquared),
      "n":int(fit.nobs)
    }

def main():
    d=fetch()
    expected=len(pd.date_range(START,END,freq="D",tz="UTC"))
    coverage=d["time"].dt.floor("D").nunique()/expected
    if coverage<.95 or len(d)<700:
        out={"classification":"REPLICATION_BLOCKED","coverage":coverage,"rows":len(d),"year_2026_opened":False}
        Path("edff_replication_receipt_v01.json").write_text(json.dumps(out,indent=2)+"\n")
        print(json.dumps(out)); return 2

    d["fi"]=d["FeeTotNtv"]/d["SplyCur"]
    d["fi_sma30"]=d["fi"].rolling(30,min_periods=30).mean()
    d["fi_med90"]=d["fi"].rolling(90,min_periods=90).median()
    d["fd"]=np.log(d["fi_sma30"]/d["fi_med90"])
    p=d.set_index("time")["PriceUSD"]
    d["exit_time"]=d["time"]+pd.Timedelta(days=45)
    d["exit_price"]=d["exit_time"].map(p)
    d["fwd45"]=np.log(d["exit_price"]/d["PriceUSD"])

    disc=d[(d["time"]>=pd.Timestamp("2024-03-13",tz="UTC"))&
           (d["time"]<=pd.Timestamp("2024-12-31",tz="UTC"))].dropna(subset=["fd","fwd45"]).copy()
    hold=d[(d["time"]>=pd.Timestamp("2025-01-01",tz="UTC"))&
           (d["time"]<=pd.Timestamp("2025-11-16",tz="UTC"))].dropna(subset=["fd","fwd45"]).copy()
    if len(disc)<200 or len(hold)<250:
        out={"classification":"REPLICATION_BLOCKED","coverage":coverage,"discovery_N":len(disc),"holdout_N":len(hold),"year_2026_opened":False}
        Path("edff_replication_receipt_v01.json").write_text(json.dumps(out,indent=2)+"\n")
        print(json.dumps(out)); return 2

    ds=ols_hac(disc)
    hs=ols_hac(hold)

    hold["pred"]=ds["alpha"]+ds["beta"]*hold["fd"]
    benchmark=float(disc["fwd45"].mean())
    sse_model=float(((hold["fwd45"]-hold["pred"])**2).sum())
    sse_bench=float(((hold["fwd45"]-benchmark)**2).sum())
    oos_r2=1-sse_model/sse_bench if sse_bench>0 else float("nan")
    dir_acc=float((np.sign(hold["pred"])==np.sign(hold["fwd45"])).mean())

    pos=hold[hold["fd"]>0]["fwd45"]
    neg=hold[hold["fd"]<=0]["fwd45"]
    spread=float(pos.mean()-neg.mean()) if len(pos) and len(neg) else float("nan")

    gates={
      "discovery_N_gte_200":len(disc)>=200,
      "discovery_beta_gt_0":ds["beta"]>0,
      "discovery_HAC_t_gte_2":ds["beta_t_hac"]>=2.0,
      "discovery_R2_gt_0":ds["r2"]>0,
      "holdout_N_gte_250":len(hold)>=250,
      "holdout_OOS_R2_gt_0":oos_r2>0,
      "holdout_direction_accuracy_gt_0_50":dir_acc>0.50,
      "positive_minus_nonpositive_FD_return_spread_gt_0":spread>0
    }
    core=list(gates.values())
    if all(core): cls="LITERATURE_REPLICATION_PASS"
    elif sum(core)>=5: cls="LITERATURE_REPLICATION_MIXED"
    else: cls="LITERATURE_REPLICATION_FAIL"

    out={
      "lab_id":"ETH-DEMAND-FEE-FLOW-001",
      "experiment_id":"EDFF-45D-CM-REPLICATION-001",
      "classification":cls,
      "source_coverage":float(coverage),
      "formula":{"fi":"FeeTotNtv/SplyCur","smooth_days":30,"reference_median_days":90,"horizon_days":45},
      "discovery_2024":ds,
      "holdout_2025":{
        **hs,
        "fixed_2024_model_oos_r2":float(oos_r2),
        "fixed_2024_model_direction_accuracy":dir_acc,
        "benchmark_2024_mean_log_return":benchmark,
        "fd_positive_N":int(len(pos)),
        "fd_nonpositive_N":int(len(neg)),
        "fd_positive_mean_fwd45":float(pos.mean()) if len(pos) else None,
        "fd_nonpositive_mean_fwd45":float(neg.mean()) if len(neg) else None,
        "positive_minus_nonpositive_spread":spread
      },
      "gates":gates,
      "year_2026_opened":False,
      "pnl_opened":False,
      "tradable_strategy_claimed":False
    }
    Path("edff_replication_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    pd.concat([disc.assign(sample="DISCOVERY_2024"),hold.assign(sample="HOLDOUT_2025")]).to_csv("edff_replication_rows_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())

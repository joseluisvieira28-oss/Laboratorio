#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures, io, json, math, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=["BTCUSDT","ETHUSDT"]
BASE="https://data.binance.vision/data/futures/um/monthly/klines"
DISC_MONTHS=pd.period_range("2021-01","2024-12",freq="M").astype(str).tolist()
HOLD_MONTHS=pd.period_range("2025-01","2025-12",freq="M").astype(str).tolist()

def fetch_one(args):
    sym,m=args
    u=f"{BASE}/{sym}/5m/{sym}-5m-{m}.zip"
    try:
        req=urllib.request.Request(u,headers={"User-Agent":"CryptoLab-CIRV/0.1"})
        with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            data=z.read(z.namelist()[0])
        d=pd.read_csv(io.BytesIO(data),header=None)
        if d.shape[1] < 7: raise RuntimeError("kline schema")
        d=d.iloc[:,:12].copy()
        d.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
        d=d[["open_time","close"]]
        d["symbol"]=sym; d["source_month"]=m
        return sym,m,d,len(raw),None
    except Exception as e:
        return sym,m,None,0,f"{type(e).__name__}:{str(e)[:220]}"

def ptime(s):
    n=pd.to_numeric(s,errors="coerce")
    med=float(n.dropna().abs().median()) if n.notna().any() else 0
    if med>1e14: unit="us"
    elif med>1e11: unit="ms"
    else: unit="s"
    return pd.to_datetime(n,unit=unit,utc=True,errors="coerce").astype("datetime64[ns, UTC]")

def load_months(months):
    rec=[]; frames=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for sym,m,d,n,e in ex.map(fetch_one,[(s,m) for s in ASSETS for m in months]):
            rec.append({"symbol":sym,"month":m,"ok":d is not None,"zip_bytes":n,"error":e})
            if d is not None: frames.append(d)
    return rec,frames

def build_daily(frames):
    raw=pd.concat(frames,ignore_index=True)
    raw["ts"]=ptime(raw["open_time"])
    raw["close"]=pd.to_numeric(raw["close"],errors="coerce")
    raw=raw[raw["ts"].notna()&(raw["close"]>0)].sort_values(["symbol","ts"]).drop_duplicates(["symbol","ts"],keep="last")
    raw["prev_ts"]=raw.groupby("symbol")["ts"].shift(1)
    raw["prev_close"]=raw.groupby("symbol")["close"].shift(1)
    gap=(raw["ts"]-raw["prev_ts"]).dt.total_seconds()/60
    raw["ret"]=np.where(gap.eq(5),np.log(raw["close"]/raw["prev_close"]),np.nan)
    raw["date"]=raw["ts"].dt.floor("D")
    daily=raw.groupby(["symbol","date"]).agg(
      rv=("ret",lambda x:float(np.nansum(np.square(x.to_numpy(dtype=float))))),
      nret=("ret",lambda x:int(np.isfinite(x.to_numpy(dtype=float)).sum()))
    ).reset_index()
    daily=daily[(daily["nret"]>=270)&(daily["rv"]>0)].copy()
    return daily

def source_receipt(rec,daily,start,end,label):
    expected=len(pd.date_range(start,end,freq="D",tz="UTC"))
    cov={}
    for s in ASSETS:
        okm=[r["month"] for r in rec if r["symbol"]==s and r["ok"]]
        x=daily[(daily["symbol"]==s)&(daily["date"]>=pd.Timestamp(start,tz="UTC"))&(daily["date"]<=pd.Timestamp(end,tz="UTC"))]
        cov[s]={
          "months_ok":len(okm),
          "valid_days":int(x["date"].nunique()),
          "expected_days":expected,
          "daily_coverage":float(x["date"].nunique()/expected),
          "min_nret":int(x["nret"].min()) if len(x) else None,
          "max_nret":int(x["nret"].max()) if len(x) else None
        }
    full=all(cov[s]["daily_coverage"]>=.95 for s in ASSETS)
    return {"label":label,"classification":"CIRV_SOURCE_FULL" if full else "CIRV_SOURCE_BLOCKED","coverage":cov,"records":rec}

def make_features(daily,sym):
    x=daily[daily["symbol"]==sym].sort_values("date").copy().set_index("date")
    # Require consecutive calendar days for target.
    x["next_date"]=x.index.to_series().shift(-1)
    x["next_rv"]=x["rv"].shift(-1)
    x["target_ok"]=(x["next_date"]-x.index.to_series()).dt.days.eq(1)
    x["x1"]=np.log(x["rv"])
    x["x5"]=np.log(x["rv"].rolling(5,min_periods=5).mean())
    x["x22"]=np.log(x["rv"].rolling(22,min_periods=22).mean())
    x["y"]=np.log(x["next_rv"])
    x["target_date"]=x["next_date"]
    x["target_dow"]=x["target_date"].dt.weekday
    x=x[x["target_ok"]].dropna(subset=["x1","x5","x22","y","target_date"]).copy()
    return x

def design(row_or_df,dow=False):
    if isinstance(row_or_df,pd.Series):
        a=np.array([1.0,row_or_df["x1"],row_or_df["x5"],row_or_df["x22"]],float)
        if not dow:return a
        ds=np.array([1.0 if int(row_or_df["target_dow"])==k else 0.0 for k in range(1,7)],float)
        return np.r_[a,ds]
    d=row_or_df
    A=np.column_stack([np.ones(len(d)),d["x1"],d["x5"],d["x22"]])
    if not dow:return A
    D=np.column_stack([(d["target_dow"].astype(int).to_numpy()==k).astype(float) for k in range(1,7)])
    return np.column_stack([A,D])

def forecast_asset(features,start,end):
    rows=[]
    f=features.reset_index(drop=False).sort_values("target_date").reset_index(drop=True)
    for i,r in f.iterrows():
        td=r["target_date"]
        if td<pd.Timestamp(start,tz="UTC") or td>pd.Timestamp(end,tz="UTC"): continue
        train=f.iloc[max(0,i-730):i]
        train=train[train["target_date"]<td]
        if len(train)<500: continue
        y=train["y"].to_numpy(float)
        X0=design(train,False); X1=design(train,True)
        b0=np.linalg.lstsq(X0,y,rcond=None)[0]
        b1=np.linalg.lstsq(X1,y,rcond=None)[0]
        p0=float(design(r,False)@b0)
        p1=float(design(r,True)@b1)
        rv=float(np.exp(r["y"]))
        frv0=float(np.exp(p0)); frv1=float(np.exp(p1))
        q0=float(np.log(frv0)+rv/frv0); q1=float(np.log(frv1)+rv/frv1)
        m0=float((r["y"]-p0)**2); m1=float((r["y"]-p1)**2)
        rows.append({"target_date":td.isoformat(),"rv":rv,"pred_har":frv0,"pred_har_dow":frv1,
                     "qlike_har":q0,"qlike_dow":q1,"logmse_har":m0,"logmse_dow":m1})
    return pd.DataFrame(rows)

def nw_t(diff,lag=7):
    x=np.asarray(diff,float); n=len(x)
    if n<20:return float("nan")
    mu=float(np.mean(x)); z=x-mu
    gamma0=float(np.dot(z,z)/n); var=gamma0
    for k in range(1,min(lag,n-1)+1):
        g=float(np.dot(z[k:],z[:-k])/n)
        w=1-k/(lag+1)
        var += 2*w*g
    se=math.sqrt(max(var,1e-30)/n)
    return mu/se

def asset_stats(d):
    q0=float(d["qlike_har"].mean()); q1=float(d["qlike_dow"].mean())
    m0=float(d["logmse_har"].mean()); m1=float(d["logmse_dow"].mean())
    return {
      "N":int(len(d)),
      "qlike_har":q0,"qlike_har_dow":q1,
      "qlike_reduction":float((q0-q1)/abs(q0)) if q0!=0 else None,
      "logmse_har":m0,"logmse_har_dow":m1,
      "logmse_reduction":float((m0-m1)/m0) if m0>0 else None,
      "dm_t_qlike_baseline_minus_dow":float(nw_t(d["qlike_har"]-d["qlike_dow"],7))
    }

def eval_discovery(all_daily):
    res={}; frames={}
    for s in ASSETS:
        f=make_features(all_daily,s)
        z=forecast_asset(f,"2023-01-01","2024-12-31")
        frames[s]=z; res[s]=asset_stats(z) if len(z) else {"N":0}
    qbase=sum(res[s].get("qlike_har",0)*res[s].get("N",0) for s in ASSETS)
    qdow=sum(res[s].get("qlike_har_dow",0)*res[s].get("N",0) for s in ASSETS)
    nt=sum(res[s].get("N",0) for s in ASSETS)
    pooled=(qbase-qdow)/abs(qbase) if qbase!=0 else float("nan")
    gates={
      "N_gte_650_both":all(res[s]["N"]>=650 for s in ASSETS),
      "qlike_improvement_both":all(res[s].get("qlike_reduction",-9)>0 for s in ASSETS),
      "logmse_improvement_both":all(res[s].get("logmse_reduction",-9)>0 for s in ASSETS),
      "pooled_qlike_reduction_gte_1pct":pooled>=.01,
      "dm_t_gte_1_645_at_least_one":any(res[s].get("dm_t_qlike_baseline_minus_dow",-9)>=1.645 for s in ASSETS),
      "dm_t_positive_both":all(res[s].get("dm_t_qlike_baseline_minus_dow",-9)>0 for s in ASSETS)
    }
    passed=all(gates.values())
    return {"assets":res,"pooled_qlike_reduction":float(pooled),"gates":gates,
            "verdict":"DISCOVERY_PASS" if passed else ("INSUFFICIENT_SAMPLE" if not gates["N_gte_650_both"] else "DISCOVERY_FAIL_NO_PROMOTION")},frames

def eval_holdout(all_daily):
    res={}; frames={}
    for s in ASSETS:
        f=make_features(all_daily,s)
        z=forecast_asset(f,"2025-01-01","2025-12-31")
        frames[s]=z; res[s]=asset_stats(z) if len(z) else {"N":0}
    qbase=sum(res[s].get("qlike_har",0)*res[s].get("N",0) for s in ASSETS)
    qdow=sum(res[s].get("qlike_har_dow",0)*res[s].get("N",0) for s in ASSETS)
    pooled=(qbase-qdow)/abs(qbase) if qbase!=0 else float("nan")
    gates={
      "N_gte_330_both":all(res[s]["N"]>=330 for s in ASSETS),
      "qlike_improvement_both":all(res[s].get("qlike_reduction",-9)>0 for s in ASSETS),
      "logmse_improvement_both":all(res[s].get("logmse_reduction",-9)>0 for s in ASSETS),
      "pooled_qlike_reduction_gt_0":pooled>0,
      "dm_t_positive_both":all(res[s].get("dm_t_qlike_baseline_minus_dow",-9)>0 for s in ASSETS)
    }
    passed=all(gates.values())
    return {"assets":res,"pooled_qlike_reduction":float(pooled),"gates":gates,
            "verdict":"SURVIVES_2025_HOLDOUT" if passed else "DISCOVERY_PASS_HOLDOUT_FAIL"},frames

def main():
    rec,frames=load_months(DISC_MONTHS)
    daily=build_daily(frames)
    src=source_receipt(rec,daily,"2021-01-01","2024-12-31","DISCOVERY_SOURCE")
    Path("cirv_source_receipt_v01.json").write_text(json.dumps(src,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"source":src},sort_keys=True))
    if src["classification"]!="CIRV_SOURCE_FULL":
        out={"lab_id":"CRYPTO-INTRAWEEK-RV-001","verdict":"BLOCKED_SOURCE","holdout_2025_opened":False,"year_2026_opened":False}
        Path("cirv_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); return 2

    disc,dframes=eval_discovery(daily)
    Path("cirv_discovery_receipt_v01.json").write_text(json.dumps(disc,indent=2,sort_keys=True)+"\n")
    for s,z in dframes.items(): z.to_csv(f"cirv_{s.lower()}_discovery_forecasts_v01.csv",index=False)
    print(json.dumps({"discovery":disc},sort_keys=True))
    if disc["verdict"]!="DISCOVERY_PASS":
        out={"lab_id":"CRYPTO-INTRAWEEK-RV-001","mve_id":"CIRV-HAR-DOW-BTCETH-001",
             "verdict":disc["verdict"],"discovery":disc,"holdout_2025_opened":False,
             "pnl_opened":False,"year_2026_opened":False}
        Path("cirv_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); return 0

    hrec,hframes=load_months(HOLD_MONTHS)
    hdaily=build_daily(hframes)
    hsrc=source_receipt(hrec,hdaily,"2025-01-01","2025-12-31","HOLDOUT_2025_SOURCE")
    Path("cirv_holdout_source_receipt_v01.json").write_text(json.dumps(hsrc,indent=2,sort_keys=True)+"\n")
    if hsrc["classification"]!="CIRV_SOURCE_FULL":
        out={"lab_id":"CRYPTO-INTRAWEEK-RV-001","verdict":"DISCOVERY_PASS_HOLDOUT_SOURCE_BLOCKED",
             "discovery":disc,"holdout_2025_opened":False,"year_2026_opened":False}
        Path("cirv_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n"); return 0

    all_daily=pd.concat([daily,hdaily],ignore_index=True).sort_values(["symbol","date"]).drop_duplicates(["symbol","date"],keep="last")
    hold,hframes2=eval_holdout(all_daily)
    for s,z in hframes2.items(): z.to_csv(f"cirv_{s.lower()}_holdout2025_forecasts_v01.csv",index=False)
    out={"lab_id":"CRYPTO-INTRAWEEK-RV-001","mve_id":"CIRV-HAR-DOW-BTCETH-001",
         "verdict":hold["verdict"],"discovery":disc,"holdout_2025":hold,
         "holdout_2025_opened":True,"pnl_opened":False,"year_2026_opened":False}
    Path("cirv_final_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())

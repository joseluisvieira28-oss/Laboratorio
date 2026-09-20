#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures, hashlib, io, json, sys, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=["BTCUSDT","ETHUSDT"]
BASE="https://data.binance.vision/data/futures/um"
BOUNDARY=pd.Timestamp("2026-09-20",tz="UTC")
FIRST_TARGET=pd.Timestamp("2026-09-21",tz="UTC")

def fetch_zip(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CIRV-Forward/0.1"})
    with urllib.request.urlopen(req,timeout=90) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        data=z.read(z.namelist()[0])
    return raw,data

def parse_kline(data,sym):
    d=pd.read_csv(io.BytesIO(data),header=None)
    if d.shape[1]<7: raise RuntimeError("kline schema")
    d=d.iloc[:,:12].copy()
    d.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    d=d[["open_time","close"]]; d["symbol"]=sym
    return d

def ptime(s):
    n=pd.to_numeric(s,errors="coerce")
    med=float(n.dropna().abs().median()) if n.notna().any() else 0
    unit="us" if med>1e14 else ("ms" if med>1e11 else "s")
    return pd.to_datetime(n,unit=unit,utc=True,errors="coerce").astype("datetime64[ns, UTC]")

def fetch_history_through(cutoff):
    # Monthly archives through previous completed month; daily archives for current month.
    start=pd.Period(cutoff-pd.Timedelta(days=900),freq="M")
    end_prev=pd.Period((cutoff.replace(day=1)-pd.Timedelta(days=1)),freq="M")
    monthly=pd.period_range(start,end_prev,freq="M").astype(str).tolist()
    first_current=cutoff.replace(day=1)
    daily=pd.date_range(first_current,cutoff,freq="D",tz="UTC")
    frames=[]; hashes=[]
    tasks=[]
    for s in ASSETS:
        for m in monthly:
            tasks.append((s,f"{BASE}/monthly/klines/{s}/5m/{s}-5m-{m}.zip"))
        for dt in daily:
            ds=dt.strftime("%Y-%m-%d")
            tasks.append((s,f"{BASE}/daily/klines/{s}/5m/{s}-5m-{ds}.zip"))
    def one(t):
        s,u=t
        raw,data=fetch_zip(u)
        return parse_kline(data,s),hashlib.sha256(raw).hexdigest(),u
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for d,h,u in ex.map(one,tasks):
            frames.append(d); hashes.append((u,h))
    return pd.concat(frames,ignore_index=True),hashes

def daily_rv(raw):
    raw["ts"]=ptime(raw["open_time"]); raw["close"]=pd.to_numeric(raw["close"],errors="coerce")
    raw=raw[raw["ts"].notna()&(raw["close"]>0)].sort_values(["symbol","ts"]).drop_duplicates(["symbol","ts"],keep="last")
    raw["prev_ts"]=raw.groupby("symbol")["ts"].shift(1); raw["prev_close"]=raw.groupby("symbol")["close"].shift(1)
    gap=(raw["ts"]-raw["prev_ts"]).dt.total_seconds()/60
    raw["ret"]=np.where(gap.eq(5),np.log(raw["close"]/raw["prev_close"]),np.nan)
    raw["date"]=raw["ts"].dt.floor("D")
    d=raw.groupby(["symbol","date"]).agg(rv=("ret",lambda x:float(np.nansum(np.square(x.to_numpy(float))))),
                                         nret=("ret",lambda x:int(np.isfinite(x.to_numpy(float)).sum()))).reset_index()
    return d[(d["nret"]>=270)&(d["rv"]>0)].copy()

def features(daily,sym,target):
    x=daily[daily["symbol"]==sym].sort_values("date").copy().set_index("date")
    x["x1"]=np.log(x["rv"])
    x["x5"]=np.log(x["rv"].rolling(5,min_periods=5).mean())
    x["x22"]=np.log(x["rv"].rolling(22,min_periods=22).mean())
    train=x.dropna(subset=["x1","x5","x22"]).copy()
    train["next_date"]=train.index.to_series().shift(-1)
    train["y"]=np.log(train["rv"].shift(-1))
    train["target_dow"]=train["next_date"].dt.weekday
    train=train[(train["next_date"]-train.index.to_series()).dt.days.eq(1)].dropna(subset=["y","target_dow"])
    train=train[train["next_date"]<target].tail(730)
    prev=target-pd.Timedelta(days=1)
    if prev not in x.index: raise RuntimeError(f"{sym} missing previous-day RV")
    r=x.loc[prev]
    if any(pd.isna(r[c]) for c in ["x1","x5","x22"]): raise RuntimeError(f"{sym} incomplete predictors")
    return train,r

def design_df(d,dow):
    A=np.column_stack([np.ones(len(d)),d["x1"],d["x5"],d["x22"]])
    if not dow:return A
    D=np.column_stack([(d["target_dow"].astype(int).to_numpy()==k).astype(float) for k in range(1,7)])
    return np.column_stack([A,D])

def design_row(r,target_dow,dow):
    a=np.array([1.0,r["x1"],r["x5"],r["x22"]],float)
    if not dow:return a
    ds=np.array([1.0 if target_dow==k else 0.0 for k in range(1,7)],float)
    return np.r_[a,ds]

def main():
    mode=sys.argv[1] if len(sys.argv)>1 else "preflight"
    if mode=="preflight":
        cutoff=pd.Timestamp("2026-09-19",tz="UTC")
        raw,hashes=fetch_history_through(cutoff)
        d=daily_rv(raw)
        out={"forward_id":"CIRV-BTCETH-FORWARD-001","mode":"PREFLIGHT_ONLY",
             "cutoff":cutoff.isoformat(),"first_eligible_target":FIRST_TARGET.isoformat(),
             "assets":{},"preboundary_target_outcomes_opened":False}
        for s in ASSETS:
            z=d[d["symbol"]==s]
            out["assets"][s]={"valid_days":int(len(z)),"date_min":z["date"].min().isoformat(),"date_max":z["date"].max().isoformat()}
        Path("cirv_forward_preflight_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print(json.dumps(out,sort_keys=True)); return 0

    target=pd.Timestamp(mode,tz="UTC")
    if target<FIRST_TARGET:
        raise SystemExit("target forbidden by forward boundary")
    cutoff=target-pd.Timedelta(days=1)
    raw,hashes=fetch_history_through(cutoff)
    d=daily_rv(raw)
    digest=hashlib.sha256(("\n".join(u+" "+h for u,h in sorted(hashes))).encode()).hexdigest()
    forecasts=[]
    for s in ASSETS:
        tr,r=features(d,s,target)
        if len(tr)<500: raise RuntimeError(f"{s} insufficient training rows")
        y=tr["y"].to_numpy(float)
        X0=design_df(tr,False); X1=design_df(tr,True)
        b0=np.linalg.lstsq(X0,y,rcond=None)[0]; b1=np.linalg.lstsq(X1,y,rcond=None)[0]
        dow=int(target.weekday())
        p0=float(design_row(r,dow,False)@b0); p1=float(design_row(r,dow,True)@b1)
        forecasts.append({"target_date":target.date().isoformat(),"asset":s,
                          "forecast_har_rv":float(np.exp(p0)),"forecast_har_dow_rv":float(np.exp(p1)),
                          "model_training_end_date":cutoff.date().isoformat(),"training_rows":int(len(tr)),
                          "source_digest":digest})
    out={"forward_id":"CIRV-BTCETH-FORWARD-001","mode":"FORECAST","target_date":target.date().isoformat(),
         "generated_without_target_outcome":True,"forecasts":forecasts}
    Path(f"cirv_forward_forecast_{target.date().isoformat()}.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True)); return 0

if __name__=="__main__": raise SystemExit(main())

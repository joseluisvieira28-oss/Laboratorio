#!/usr/bin/env python3
from __future__ import annotations
import io,json,math,urllib.request,zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm

BINANCE="https://data.binance.vision/data/spot/monthly/klines/ETHUSDT/1d"
HORIZONS=[30,45,60]

def fetch_zip(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-EDFF-Discovery/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names=z.namelist()
        if not names: raise RuntimeError("empty zip")
        data=z.read(names[0])
    return data

def get_prices():
    frames=[]
    for y in (2023,2024):
        for m in range(1,13):
            ym=f"{y:04d}-{m:02d}"
            u=f"{BINANCE}/ETHUSDT-1d-{ym}.zip"
            raw=fetch_zip(u)
            d=pd.read_csv(io.BytesIO(raw),header=None)
            if d.shape[1]<7: raise RuntimeError("bad Binance kline schema "+ym)
            d=d.iloc[:,:12].copy()
            d.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
            frames.append(d[["open_time","open"]])
    p=pd.concat(frames,ignore_index=True)
    p["open_time"]=pd.to_numeric(p["open_time"],errors="coerce")
    med=float(p["open_time"].dropna().abs().median())
    unit="us" if med>1e14 else ("ms" if med>1e11 else "s")
    p["date"]=pd.to_datetime(p["open_time"],unit=unit,utc=True,errors="coerce").dt.floor("D")
    p["open"]=pd.to_numeric(p["open"],errors="coerce")
    p=p[p["date"].notna()&(p["open"]>0)].drop_duplicates("date",keep="last").sort_values("date")
    if p["date"].max()>pd.Timestamp("2024-12-31T00:00:00Z"):
        raise RuntimeError("protected date boundary violated")
    return p.set_index("date")["open"]

def hac_reg(x,y,lags=45):
    z=pd.DataFrame({"x":x,"y":y}).dropna()
    X=sm.add_constant(z["x"])
    fit=sm.OLS(z["y"],X).fit(cov_type="HAC",cov_kwds={"maxlags":lags})
    return {
      "N":int(len(z)),
      "alpha":float(fit.params["const"]),
      "beta":float(fit.params["x"]),
      "HAC_t":float(fit.tvalues["x"]),
      "HAC_two_sided_p":float(fit.pvalues["x"]),
      "R2":float(fit.rsquared)
    }

def evaluate_window(sig,prices,start,end,h):
    rows=[]
    for r in sig.itertuples(index=False):
        t=r.date
        if t<pd.Timestamp(start,tz="UTC") or t>pd.Timestamp(end,tz="UTC"): continue
        entry=t+pd.Timedelta(days=1)
        exit_=entry+pd.Timedelta(days=h)
        if entry not in prices.index or exit_ not in prices.index: continue
        y=math.log(float(prices.loc[exit_])/float(prices.loc[entry]))
        rows.append({"date":t,"FD":float(r.FD),"future_log_return":y,
                     "entry":float(prices.loc[entry]),"exit":float(prices.loc[exit_])})
    d=pd.DataFrame(rows)
    if d.empty:return {"N":0},d
    reg=hac_reg(d["FD"],d["future_log_return"],lags=h)
    reg["directional_accuracy"]=float((np.sign(d["FD"])==np.sign(d["future_log_return"])).mean())
    pos=d[d["FD"]>0]["future_log_return"]; neg=d[d["FD"]<0]["future_log_return"]
    reg["mean_future_return_when_FD_positive"]=float(pos.mean()) if len(pos) else None
    reg["mean_future_return_when_FD_negative"]=float(neg.mean()) if len(neg) else None
    return reg,d

def main():
    src=json.loads(Path("edff_source_receipt_v02.json").read_text())
    if src["classification"]=="EDFF_SOURCE_BLOCKED":
        raise SystemExit("source gate blocked; refusing outcomes")
    f=pd.read_csv("edff_fee_supply_bounded_v02.csv")
    f["date"]=pd.to_datetime(f["time"],utc=True,errors="coerce").dt.floor("D")
    f["FeeTotNtv"]=pd.to_numeric(f["FeeTotNtv"],errors="coerce")
    f["SplyCur"]=pd.to_numeric(f["SplyCur"],errors="coerce")
    f=f[f["date"].notna()&(f["FeeTotNtv"]>0)&(f["SplyCur"]>0)].sort_values("date").drop_duplicates("date",keep="last")
    f["FI"]=f["FeeTotNtv"]/f["SplyCur"]
    f["FI_smooth30"]=f["FI"].rolling(30,min_periods=30).mean()
    f["FI_ref90_past_median"]=f["FI"].shift(1).rolling(90,min_periods=90).median()
    f["FD"]=np.log(f["FI_smooth30"]/f["FI_ref90_past_median"])
    sig=f[["date","FD"]].dropna().copy()
    prices=get_prices()

    primary,primary_df=evaluate_window(sig,prices,"2024-03-13","2024-11-15",45)
    placebo,placebo_df=evaluate_window(sig,prices,"2023-03-13","2023-11-15",45)
    sec={}
    for h in (30,60):
        last=(pd.Timestamp("2024-12-31",tz="UTC")-pd.Timedelta(days=h+1)).strftime("%Y-%m-%d")
        sec[str(h)],_=evaluate_window(sig,prices,"2024-03-13",last,h)

    n=primary.get("N",0)
    if n<150:
        classification="INSUFFICIENT_REPLICATION_SAMPLE"
    elif primary["beta"]<=0:
        classification="REPLICATION_DOES_NOT_SUPPORT"
    else:
        supports=(n>=200 and primary["HAC_two_sided_p"]<.05 and primary["directional_accuracy"]>.50
                  and sec["30"].get("beta",-1)>0 and sec["60"].get("beta",-1)>0)
        classification="REPLICATION_SUPPORTS_MECHANISM" if supports else "REPLICATION_MIXED"

    out={
      "lab_id":"ETH-DEMAND-FEE-FLOW-001","mve_id":"EDFF-FD45-REPLICATION-001",
      "classification":classification,"source_classification":src["classification"],
      "primary_post_dencun_2024":primary,"placebo_2023":placebo,
      "secondary_post_dencun_2024":{"30d":sec["30"],"60d":sec["60"]},
      "signal_definition":{"FI":"FeeTotNtv/SplyCur","smooth_days":30,"reference_days":90,
                           "reference_past_only":True,"FD":"ln(FI_smooth30/FI_ref90_past_median)"},
      "market_source":"Binance ETHUSDT spot monthly 1d public archives",
      "protected_2025_2026_opened":False,
      "pnl_computed":False,"trading_strategy_claimed":False
    }
    Path("edff_replication_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    primary_df.to_csv("edff_primary_2024_observations_v01.csv",index=False)
    placebo_df.to_csv("edff_placebo_2023_observations_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())

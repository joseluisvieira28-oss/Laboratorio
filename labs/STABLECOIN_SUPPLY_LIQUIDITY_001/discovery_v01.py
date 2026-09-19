#!/usr/bin/env python3
from __future__ import annotations
import io, json, math, urllib.parse, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

CM="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
ASSETS=["usdt","usdc"]
BINANCE="https://data.binance.vision/data/spot/monthly/klines"
SEED=230925; REPS=10000; BLOCK=3

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-SSLI/0.1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))

def cm_supply(asset):
    p={"assets":asset,"metrics":"SplyCur","frequency":"1d",
       "start_time":"2020-06-01","end_time":"2024-12-31","page_size":"10000"}
    url=CM+"?"+urllib.parse.urlencode(p)
    js=get_json(url)
    if js.get("next_page_token"): raise RuntimeError("unexpected Coin Metrics pagination")
    d=pd.DataFrame(js.get("data",[]))
    return url,d

def source_gate():
    rec={}; frames=[]; full=limited=0
    for a in ASSETS:
        try:
            url,d=cm_supply(a)
            if not {"time","SplyCur"}.issubset(d.columns):
                rec[a]={"classification":"BLOCKED","columns":list(d.columns),"row_count":len(d),"url":url}; continue
            d["date"]=pd.to_datetime(d["time"],utc=True,errors="coerce").dt.floor("D")
            d["supply"]=pd.to_numeric(d["SplyCur"],errors="coerce")
            d=d[(d["date"]>=pd.Timestamp("2020-06-01",tz="UTC"))&(d["date"]<=pd.Timestamp("2024-12-31",tz="UTC"))]
            d=d.sort_values("date").drop_duplicates("date",keep="last")
            n=len(d); nn=float(d["supply"].notna().mean()) if n else 0; pos=float((d["supply"]>0).mean()) if n else 0
            mn=d["date"].min(); mx=d["date"].max()
            checks={"rows_gte_1600":n>=1600,"nonnull_gte_0_98":nn>=.98,"positive_gte_0_98":pos>=.98,
                    "min_time_lte_2020_06_03":bool(pd.notna(mn) and mn<=pd.Timestamp("2020-06-03",tz="UTC")),
                    "max_time_gte_2024_12_29":bool(pd.notna(mx) and mx>=pd.Timestamp("2024-12-29",tz="UTC")),
                    "max_time_lte_2024_12_31":bool(pd.notna(mx) and mx<=pd.Timestamp("2024-12-31",tz="UTC"))}
            if all(checks.values()): cls="FULL"; full+=1
            elif n>=1400 and nn>=.95 and pos>=.95 and pd.notna(mx) and mx<=pd.Timestamp("2024-12-31",tz="UTC"):
                cls="LIMITED"; limited+=1
            else: cls="BLOCKED"
            rec[a]={"classification":cls,"row_count":n,"nonnull_fraction":nn,"positive_fraction":pos,
                    "date_min":mn.isoformat() if pd.notna(mn) else None,
                    "date_max":mx.isoformat() if pd.notna(mx) else None,"checks":checks,"url":url}
            if cls!="BLOCKED":
                d["asset"]=a; frames.append(d[["asset","date","supply"]])
        except Exception as e:
            rec[a]={"classification":"BLOCKED","error":f"{type(e).__name__}:{str(e)[:400]}"}
    final="SSLI_SOURCE_FULL" if full==2 else ("SSLI_SOURCE_LIMITED" if full+limited==2 else "SSLI_SOURCE_BLOCKED")
    out={"lab_id":"STABLECOIN-SUPPLY-LIQUIDITY-001","source_gate_id":"SSLI-COINMETRICS-SUPPLY-001",
         "classification":final,"assets":rec,"credentials_used":False,"cash_spend_usd":0,
         "outcomes_opened":False,"returns_computed":False,"protected_2025_2026_requested":False}
    Path("ssli_source_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    if frames: pd.concat(frames,ignore_index=True).to_csv("ssli_supply_bounded_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return out

def fetch_zip(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-SSLI-Discovery/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        return z.read(z.namelist()[0])

def price_series(symbol):
    fs=[]
    # Exact price boundary required by frozen Discovery only: 2020-12 through 2023-12.
    for y,m0,m1 in [(2020,12,12),(2021,1,12),(2022,1,12),(2023,1,12)]:
        for m in range(m0,m1+1):
            ym=f"{y:04d}-{m:02d}"
            u=f"{BINANCE}/{symbol}/1d/{symbol}-1d-{ym}.zip"
            d=pd.read_csv(io.BytesIO(fetch_zip(u)),header=None)
            if d.shape[1]<7: raise RuntimeError("bad kline schema "+symbol+" "+ym)
            d=d.iloc[:,:12].copy()
            d.columns=["open_time","open","h","l","c","v","ct","q","n","tb","tq","i"]
            fs.append(d[["open_time","open"]])
    p=pd.concat(fs,ignore_index=True)
    n=pd.to_numeric(p["open_time"],errors="coerce"); med=float(n.dropna().abs().median())
    unit="us" if med>1e14 else ("ms" if med>1e11 else "s")
    p["date"]=pd.to_datetime(n,unit=unit,utc=True,errors="coerce").dt.floor("D")
    p["open"]=pd.to_numeric(p["open"],errors="coerce")
    p=p[p["date"].notna()&(p["open"]>0)].drop_duplicates("date",keep="last").sort_values("date")
    if p["date"].max()>pd.Timestamp("2023-12-31",tz="UTC"):
        raise RuntimeError("2024 price boundary violated")
    return p.set_index("date")["open"]

def streak(x):
    m=c=0
    for v in x:
        if v<0:c+=1;m=max(m,c)
        else:c=0
    return m

def boot(x):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(SEED); out=np.empty(REPS); nb=math.ceil(n/BLOCK)
    for i in range(REPS):
        vals=[]
        for s in rng.integers(0,n,size=nb): vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        out[i]=np.mean(vals[:n])
    return [float(np.quantile(out,.025)),float(np.quantile(out,.975))]

def discovery(src):
    if src["classification"]=="SSLI_SOURCE_BLOCKED":
        raise SystemExit("source gate blocked; refusing market outcomes")
    s=pd.read_csv("ssli_supply_bounded_v01.csv")
    s["date"]=pd.to_datetime(s["date"],utc=True,errors="coerce").dt.floor("D")
    s["supply"]=pd.to_numeric(s["supply"],errors="coerce")
    w=s.pivot(index="date",columns="asset",values="supply").sort_index().dropna()
    if not {"usdt","usdc"}.issubset(w.columns): raise RuntimeError("both stablecoins required")
    w["agg"]=w["usdt"]+w["usdc"]
    w["g7"]=np.log(w["agg"]/w["agg"].shift(7))
    w["q90"]=w["g7"].shift(1).rolling(180,min_periods=120).quantile(.90)
    sig=w[(w["g7"]>0)&(w["g7"]>=w["q90"])].copy()
    sig=sig[(sig.index>=pd.Timestamp("2021-01-01",tz="UTC"))&(sig.index<=pd.Timestamp("2023-12-22",tz="UTC"))]
    btc=price_series("BTCUSDT"); eth=price_series("ETHUSDT")
    events=[]; active_until=None
    for t,r in sig.iterrows():
        if active_until is not None and t<active_until: continue
        entry=t+pd.Timedelta(days=1); exit_=t+pd.Timedelta(days=8); prior=t-pd.Timedelta(days=7)
        needed=[entry,exit_,t,prior]
        if any(x not in btc.index or x not in eth.index for x in needed): continue
        rb=math.log(float(btc.loc[exit_])/float(btc.loc[entry]))
        re=math.log(float(eth.loc[exit_])/float(eth.loc[entry]))
        future=.5*(rb+re)
        pb=math.log(float(btc.loc[t])/float(btc.loc[prior]))
        pe=math.log(float(eth.loc[t])/float(eth.loc[prior]))
        prior_ret=.5*(pb+pe)
        events.append({"signal_date":t.isoformat(),"entry":entry.isoformat(),"exit":exit_.isoformat(),
                       "g7_supply":float(r.g7),"q90_past":float(r.q90),
                       "future_7d_market_return":future,"prior_7d_market_return":prior_ret,
                       "btc_future":rb,"eth_future":re})
        active_until=exit_
    d=pd.DataFrame(events); n=len(d)
    if n:
        d["year"]=pd.to_datetime(d["signal_date"],utc=True,format="mixed").dt.year
        years={str(int(y)):float(v) for y,v in d.groupby("year")["future_7d_market_return"].mean().items()}
        counts={str(int(y)):int(v) for y,v in d["year"].value_counts().sort_index().items()}
        ci=boot(d["future_7d_market_return"].to_numpy())
        st={"N":n,"mean_future_7d_return":float(d.future_7d_market_return.mean()),
            "median_future_7d_return":float(d.future_7d_market_return.median()),
            "hit_rate":float((d.future_7d_market_return>0).mean()),
            "bootstrap_95_ci_mean":ci,"year_means":years,
            "positive_year_count":int(sum(v>0 for v in years.values())),
            "mean_prior_7d_return":float(d.prior_7d_market_return.mean()),
            "event_count_by_year":counts,
            "max_losing_streak":int(streak(d.future_7d_market_return.to_numpy()))}
    else: st={"N":0}
    gates={"N_gte_30":n>=30,
           "mean_gt_0":n>0 and st["mean_future_7d_return"]>0,
           "bootstrap_lower_gt_0":n>0 and st["bootstrap_95_ci_mean"][0]>0,
           "positive_years_gte_2":n>0 and st["positive_year_count"]>=2,
           "hit_rate_gt_0_50":n>0 and st["hit_rate"]>.50}
    if n<30: verdict="INSUFFICIENT_SAMPLE"
    elif all(gates.values()): verdict="DISCOVERY_PASS_LIQUIDITY_IMPULSE"
    else: verdict="DISCOVERY_FAIL_NO_PROMOTION"
    out={"lab_id":"STABLECOIN-SUPPLY-LIQUIDITY-001","mve_id":"SSLI-USDTUSDC-7D-IMPULSE-001",
         "source_classification":src["classification"],"verdict":verdict,"stats":st,"gates":gates,
         "replication_2024_opened":False,"pnl_computed":False,"execution_claimed":False,
         "protected_2025_2026_opened":False}
    Path("ssli_discovery_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    d.to_csv("ssli_discovery_events_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))

def main():
    src=source_gate()
    discovery(src)

if __name__=="__main__": main()

#!/usr/bin/env python3
from __future__ import annotations
import calendar, concurrent.futures, io, json, math, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

ASSETS=["SOLUSDT","BNBUSDT"]
START="2022-01"; END="2024-12"
MONTHLY="https://data.binance.vision/data/futures/um/monthly"
DAILY="https://data.binance.vision/data/futures/um/daily"
SEED=230919; BOOT=10000; BLOCK=5

def months():
    return pd.period_range(START,END,freq="M").astype(str).tolist()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PCU-XAsset/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        n=z.namelist()[0]; data=z.read(n)
    return data,len(raw)

def parse_metrics(data):
    df=pd.read_csv(io.BytesIO(data))
    if not {"create_time","sum_open_interest"}.issubset(df.columns): raise RuntimeError("metrics schema")
    keep=[c for c in ["create_time","symbol","sum_open_interest","sum_open_interest_value"] if c in df.columns]
    return df[keep]

def parse_funding(data):
    df=pd.read_csv(io.BytesIO(data))
    if not {"calc_time","last_funding_rate"}.issubset(df.columns): raise RuntimeError("funding schema")
    return df[["calc_time","last_funding_rate"]]

def parse_klines(data):
    df=pd.read_csv(io.BytesIO(data),header=None)
    if df.shape[1]<7: raise RuntimeError("kline schema")
    df=df.iloc[:,:12].copy()
    df.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    return df[["open_time","open","close"]]

def parse_time(s):
    n=pd.to_numeric(s,errors="coerce")
    if n.notna().any() and n.notna().mean()>0.8:
        med=float(n.dropna().abs().median()); unit="ms" if med>1e11 else "s"
        out=pd.to_datetime(n,unit=unit,utc=True,errors="coerce")
    else:
        out=pd.to_datetime(s,utc=True,errors="coerce")
    return out.astype("datetime64[ns, UTC]")

def pf(x):
    x=np.asarray(x,float); p=x[x>0].sum(); n=-x[x<0].sum()
    return float(p/n) if n>0 else (float("inf") if p>0 else 0.0)

def streak(x):
    m=c=0
    for v in x:
        if v<0:c+=1;m=max(m,c)
        else:c=0
    return m

def boot_ci(x,seed_offset):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(SEED+seed_offset); out=np.empty(BOOT)
    nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        for s in rng.integers(0,n,size=nb): vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        out[i]=np.mean(vals[:n])
    return [float(np.quantile(out,.025)),float(np.quantile(out,.975))]

def metric_day(symbol,ds):
    u=f"{DAILY}/metrics/{symbol}/{symbol}-metrics-{ds}.zip"
    try:
        data,n=fetch(u); d=parse_metrics(data); d["source_date"]=ds
        return ds,d,n,None
    except Exception as e:
        return ds,None,0,f"{type(e).__name__}:{str(e)[:160]}"

def acquire_asset(symbol):
    mets=[]; funds=[]; ks=[]; rec=[]
    for m in months():
        y,mo=map(int,m.split("-")); nd=calendar.monthrange(y,mo)[1]
        dates=[f"{y:04d}-{mo:02d}-{d:02d}" for d in range(1,nd+1)]
        out=[]; errs=[]
        with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
            for ds,d,n,e in ex.map(lambda z:metric_day(symbol,z),dates):
                if d is not None: out.append(d)
                else: errs.append({"date":ds,"error":e})
        ratio=len(out)/nd
        row={"month":m,"metric_days_ok":len(out),"calendar_days":nd,"metric_ratio":ratio,
             "metrics_full":ratio>=.95,"metrics_usable":ratio>=.80,"metric_errors":errs}
        if out:
            z=pd.concat(out,ignore_index=True); z["source_month"]=m; mets.append(z); row["metrics_rows"]=len(z)
        for kind,url in {
          "funding":f"{MONTHLY}/fundingRate/{symbol}/{symbol}-fundingRate-{m}.zip",
          "kline":f"{MONTHLY}/klines/{symbol}/1h/{symbol}-1h-{m}.zip"
        }.items():
            try:
                data,_=fetch(url); row[kind+"_ok"]=True
                if kind=="funding":
                    z=parse_funding(data); z["source_month"]=m; funds.append(z); row["funding_rows"]=len(z)
                else:
                    z=parse_klines(data); z["source_month"]=m; ks.append(z); row["kline_rows"]=len(z)
            except Exception as e:
                row[kind+"_ok"]=False; row[kind+"_error"]=f"{type(e).__name__}:{str(e)[:180]}"
        rec.append(row)
    full=[r["month"] for r in rec if r.get("metrics_full") and r.get("funding_ok") and r.get("kline_ok")]
    use=[r["month"] for r in rec if r.get("metrics_usable") and r.get("funding_ok") and r.get("kline_ok")]
    fy={str(y):sum(x.startswith(str(y)+"-") for x in full) for y in range(2022,2025)}
    uy={str(y):sum(x.startswith(str(y)+"-") for x in use) for y in range(2022,2025)}
    cls="FULL" if len(full)>=35 and min(fy.values())>=11 else ("LIMITED" if len(use)>=30 and min(uy.values())>=8 else "BLOCKED")
    data={
      "coverage_classification":cls,"full_month_count":len(full),"usable_month_count":len(use),
      "full_months_by_year":fy,"usable_months_by_year":uy,"records":rec
    }
    if cls=="BLOCKED":
        return data,None,None,None
    return data,pd.concat(mets,ignore_index=True),pd.concat(funds,ignore_index=True),pd.concat(ks,ignore_index=True)

def run_asset(symbol,m,f,k,seed_offset):
    m["ts"]=parse_time(m["create_time"]); m["oi"]=pd.to_numeric(m["sum_open_interest"],errors="coerce")
    m=m[m["ts"].notna()&(m["oi"]>0)].sort_values("ts").drop_duplicates("ts",keep="last")
    f["ts"]=parse_time(f["calc_time"]); f["funding"]=pd.to_numeric(f["last_funding_rate"],errors="coerce")
    f=f[f["ts"].notna()&f["funding"].notna()].sort_values("ts").drop_duplicates("ts",keep="last")
    f=f[(f["ts"]>=pd.Timestamp("2022-01-01",tz="UTC"))&(f["ts"]<pd.Timestamp("2025-01-01",tz="UTC"))]
    k["ts"]=parse_time(k["open_time"]); k["open"]=pd.to_numeric(k["open"],errors="coerce")
    k=k[k["ts"].notna()&(k["open"]>0)].sort_values("ts").drop_duplicates("ts",keep="last"); px=k.set_index("ts")["open"]

    ev=f[["ts","funding"]].copy().sort_values("ts")
    ev=pd.merge_asof(ev,m[["ts","oi"]],on="ts",direction="backward",tolerance=pd.Timedelta("15min"))
    prev=ev[["ts"]].copy(); prev["target"]=prev["ts"]-pd.Timedelta(hours=24); prev=prev.sort_values("target")
    pm=m[["ts","oi"]].rename(columns={"ts":"m_ts","oi":"oi_prev"}).sort_values("m_ts")
    prev=pd.merge_asof(prev,pm,left_on="target",right_on="m_ts",direction="backward",tolerance=pd.Timedelta("15min"))
    ev["oi_prev"]=prev.set_index("ts").reindex(ev["ts"])["oi_prev"].to_numpy()
    ev["oi_growth_24h"]=ev["oi"]/ev["oi_prev"]-1
    ev["q95"]=ev["funding"].shift(1).rolling(540,min_periods=270).quantile(.95)
    ev["q05"]=ev["funding"].shift(1).rolling(540,min_periods=270).quantile(.05)
    ev["oq80"]=ev["oi_growth_24h"].shift(1).rolling(540,min_periods=270).quantile(.80)
    ev["side"]=0
    ev.loc[(ev["funding"]>=ev["q95"])&(ev["oi_growth_24h"]>=ev["oq80"]),"side"]=-1
    ev.loc[(ev["funding"]<=ev["q05"])&(ev["oi_growth_24h"]>=ev["oq80"]),"side"]=1
    ev=ev[ev["side"]!=0]

    trades=[]; active=None
    for r in ev.itertuples(index=False):
        t=r.ts
        if active is not None and t<active: continue
        et=t.floor("h"); xt=et+pd.Timedelta(hours=24)
        if et not in px.index or xt not in px.index: continue
        en=float(px.loc[et]); ex=float(px.loc[xt]); gross=int(r.side)*(ex/en-1)
        trades.append({"ts":t.isoformat(),"side":int(r.side),"gross":gross,"net10":gross-.001,"net20":gross-.002})
        active=xt
    d=pd.DataFrame(trades); n=len(d)
    if not n:
        return {"N":0},{"N_gte_60":False},False,d
    d["year"]=pd.to_datetime(d["ts"],utc=True,format="mixed").dt.year
    years={str(int(y)):float(v) for y,v in d.groupby("year")["net10"].mean().items()}
    ci=boot_ci(d["net10"].to_numpy(),seed_offset)
    s={"N":n,"long_N":int((d.side==1).sum()),"short_N":int((d.side==-1).sum()),
       "mean_net10":float(d.net10.mean()),"median_net10":float(d.net10.median()),
       "hit_rate":float((d.net10>0).mean()),"profit_factor_net10":pf(d.net10),
       "bootstrap_95_ci_mean_net10":ci,"mean_net20":float(d.net20.mean()),
       "profit_factor_net20":pf(d.net20),"year_means_net10":years,
       "positive_year_count":int(sum(v>0 for v in years.values())),"max_losing_streak":streak(d.net10)}
    g={"N_gte_60":n>=60,"mean_net10_gt_0":s["mean_net10"]>0,"pf_net10_gte_1_10":s["profit_factor_net10"]>=1.10,
       "bootstrap_lower_gt_0":ci[0]>0,"positive_years_gte_3":s["positive_year_count"]>=3,
       "mean_net20_gt_0":s["mean_net20"]>0,"pf_net20_gt_1":s["profit_factor_net20"]>1}
    return s,g,all(g.values()),d

def main():
    Path("xasset_out").mkdir(exist_ok=True)
    results={}; passes={}
    for i,symbol in enumerate(ASSETS):
        cov,m,f,k=acquire_asset(symbol)
        if cov["coverage_classification"]=="BLOCKED":
            results[symbol]={"coverage":cov,"verdict":"BLOCKED_SOURCE_COVERAGE"}; passes[symbol]=False; continue
        st,g,p,d=run_asset(symbol,m,f,k,i+1)
        verdict="DISCOVERY_PASS_CROWDING_UNWIND_SIGNAL" if p else ("INSUFFICIENT_EXECUTABLE_SAMPLE" if st.get("N",0)<60 else "DISCOVERY_FAIL_NO_PROMOTION")
        results[symbol]={"coverage":cov,"verdict":verdict,"stats":st,"gates":g}
        passes[symbol]=p
        d.to_csv(f"xasset_out/{symbol}_trades.csv",index=False)

    strong=all(passes.get(a,False) for a in ASSETS)
    partial=False
    if not strong:
        winners=[a for a in ASSETS if passes.get(a,False)]
        if len(winners)==1:
            other=[a for a in ASSETS if a not in winners][0]
            r=results.get(other,{})
            st=r.get("stats",{})
            partial=(st.get("mean_net10",-1)>0 and st.get("profit_factor_net10",0)>1 and
                     st.get("mean_net20",-1)>0 and st.get("profit_factor_net20",0)>1)
    family="REPLICATION_STRONG" if strong else ("REPLICATION_PARTIAL" if partial else "REPLICATION_FAIL")
    out={"lab_id":"PERP-CROWDING-UNWIND-XASSET-001","family_verdict":family,"assets":results,
         "btc_eth_results_rewritten":False,"protected_2025_2026_opened":False}
    Path("xasset_replication_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))

if __name__=="__main__": raise SystemExit(main())

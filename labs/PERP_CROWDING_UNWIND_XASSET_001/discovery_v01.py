#!/usr/bin/env python3
from __future__ import annotations
import calendar, concurrent.futures, io, json, math, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

SYMBOLS=["SOLUSDT","BNBUSDT"]
START="2022-01"; END="2024-12"
MONTHLY="https://data.binance.vision/data/futures/um/monthly"
DAILY="https://data.binance.vision/data/futures/um/daily"
SEED=230922; BOOT=10000; BLOCK=5

def months(): return pd.period_range(START,END,freq="M").astype(str).tolist()

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PCU-XASSET/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        n=z.namelist()[0]; data=z.read(n)
    return n,data,len(raw)

def parse_metrics(data):
    df=pd.read_csv(io.BytesIO(data))
    keep=[c for c in ["create_time","symbol","sum_open_interest","sum_open_interest_value"] if c in df.columns]
    if "create_time" not in keep or "sum_open_interest" not in keep: raise RuntimeError("metrics schema")
    return df[keep]

def parse_funding(data):
    df=pd.read_csv(io.BytesIO(data))
    if not {"calc_time","last_funding_rate"}.issubset(df.columns): raise RuntimeError("funding schema")
    return df[["calc_time","last_funding_rate"]]

def parse_kline(data):
    df=pd.read_csv(io.BytesIO(data),header=None)
    if df.shape[1]<7: raise RuntimeError("kline schema")
    df=df.iloc[:,:12].copy()
    df.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    return df[["open_time","open"]]

def fetch_metric_day(args):
    symbol,ds=args
    u=f"{DAILY}/metrics/{symbol}/{symbol}-metrics-{ds}.zip"
    try:
        _,data,n=fetch(u); d=parse_metrics(data); d["source_date"]=ds
        return ds,d,n,None
    except Exception as e:
        return ds,None,0,f"{type(e).__name__}:{str(e)[:160]}"

def metric_month(symbol,m):
    y,mo=map(int,m.split("-")); nd=calendar.monthrange(y,mo)[1]
    dates=[f"{y:04d}-{mo:02d}-{d:02d}" for d in range(1,nd+1)]
    out=[]; errs=[]; total=0
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for ds,d,n,e in ex.map(fetch_metric_day,[(symbol,ds) for ds in dates]):
            if d is not None: out.append(d); total+=n
            else: errs.append({"date":ds,"error":e})
    ratio=len(out)/nd
    return (pd.concat(out,ignore_index=True) if out else None),{
      "metric_days_ok":len(out),"calendar_days":nd,"metric_day_ratio":ratio,
      "metrics_full":ratio>=.95,"metrics_usable":ratio>=.80,"metric_errors":errs,
      "metrics_zip_bytes_total":total}

def ptime(s):
    n=pd.to_numeric(s,errors="coerce")
    if n.notna().any() and n.notna().mean()>0.8:
        med=float(n.dropna().abs().median()); unit="ms" if med>1e11 else "s"
        x=pd.to_datetime(n,unit=unit,utc=True,errors="coerce")
    else:x=pd.to_datetime(s,utc=True,errors="coerce")
    return x.astype("datetime64[ns, UTC]")

def pf(x):
    x=np.asarray(x,float); p=x[x>0].sum(); n=-x[x<0].sum()
    return float(p/n) if n>0 else (float("inf") if p>0 else 0.0)

def streak(x):
    m=c=0
    for v in x:
        if v<0:c+=1;m=max(m,c)
        else:c=0
    return m

def boot_ci(x,seed):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(seed); out=np.empty(BOOT); nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        for s in rng.integers(0,n,size=nb): vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        out[i]=np.mean(vals[:n])
    return [float(np.quantile(out,.025)),float(np.quantile(out,.975))]

def source_for(symbol):
    rec=[]; ms=[]; fs=[]; ks=[]
    for m in months():
        row={"month":m}
        md,mstat=metric_month(symbol,m); row.update(mstat)
        if md is not None:
            md["source_month"]=m; ms.append(md); row["metrics_rows"]=len(md)
        for kind,u in {
          "funding":f"{MONTHLY}/fundingRate/{symbol}/{symbol}-fundingRate-{m}.zip",
          "kline":f"{MONTHLY}/klines/{symbol}/1h/{symbol}-1h-{m}.zip"
        }.items():
            try:
                _,data,n=fetch(u); row[kind+"_ok"]=True; row[kind+"_zip_bytes"]=n
                if kind=="funding":
                    d=parse_funding(data); d["source_month"]=m; fs.append(d); row["funding_rows"]=len(d)
                else:
                    d=parse_kline(data); d["source_month"]=m; ks.append(d); row["kline_rows"]=len(d)
            except Exception as e:
                row[kind+"_ok"]=False; row[kind+"_error"]=f"{type(e).__name__}:{str(e)[:200]}"
        rec.append(row)
    full=[r["month"] for r in rec if r.get("metrics_full") and r.get("funding_ok") and r.get("kline_ok")]
    cls="FULL" if len(full)==36 else "BLOCKED"
    return {
      "classification":cls,"full_month_count":len(full),"records":rec,
      "metrics":pd.concat(ms,ignore_index=True) if ms else pd.DataFrame(),
      "funding":pd.concat(fs,ignore_index=True) if fs else pd.DataFrame(),
      "klines":pd.concat(ks,ignore_index=True) if ks else pd.DataFrame()
    }

def discover(symbol,src,seed):
    m=src["metrics"].copy(); f=src["funding"].copy(); k=src["klines"].copy()
    m["ts"]=ptime(m["create_time"]); m["oi"]=pd.to_numeric(m["sum_open_interest"],errors="coerce")
    m=m[m["ts"].notna()&(m["oi"]>0)].sort_values("ts").drop_duplicates("ts",keep="last")
    f["ts"]=ptime(f["calc_time"]); f["funding"]=pd.to_numeric(f["last_funding_rate"],errors="coerce")
    f=f[f["ts"].notna()&f["funding"].notna()].sort_values("ts").drop_duplicates("ts",keep="last")
    f=f[(f["ts"]>=pd.Timestamp("2022-01-01",tz="UTC"))&(f["ts"]<pd.Timestamp("2025-01-01",tz="UTC"))]
    k["ts"]=ptime(k["open_time"]); k["open"]=pd.to_numeric(k["open"],errors="coerce")
    k=k[k["ts"].notna()&(k["open"]>0)].sort_values("ts").drop_duplicates("ts",keep="last"); px=k.set_index("ts")["open"]

    ev=f[["ts","funding"]].copy().sort_values("ts")
    ev=pd.merge_asof(ev,m[["ts","oi"]],on="ts",direction="backward",tolerance=pd.Timedelta("15min"))
    prev=ev[["ts"]].copy(); prev["target"]=prev["ts"]-pd.Timedelta(hours=24); prev=prev.sort_values("target")
    pm=m[["ts","oi"]].rename(columns={"ts":"m_ts","oi":"oi_prev"}).sort_values("m_ts")
    prev=pd.merge_asof(prev,pm,left_on="target",right_on="m_ts",direction="backward",tolerance=pd.Timedelta("15min"))
    ev["oi_prev"]=prev.set_index("ts").reindex(ev["ts"])["oi_prev"].to_numpy()
    ev["oi_growth_24h"]=ev["oi"]/ev["oi_prev"]-1
    ev["fund_q95"]=ev["funding"].shift(1).rolling(540,min_periods=270).quantile(.95)
    ev["fund_q05"]=ev["funding"].shift(1).rolling(540,min_periods=270).quantile(.05)
    ev["oi_q80"]=ev["oi_growth_24h"].shift(1).rolling(540,min_periods=270).quantile(.80)
    ev["side"]=0
    ev.loc[(ev["funding"]>=ev["fund_q95"])&(ev["oi_growth_24h"]>=ev["oi_q80"]),"side"]=-1
    ev.loc[(ev["funding"]<=ev["fund_q05"])&(ev["oi_growth_24h"]>=ev["oi_q80"]),"side"]=1
    ev=ev[ev["side"]!=0].copy()

    trades=[]; active_until=None
    for r in ev.itertuples(index=False):
        t=r.ts
        if active_until is not None and t<active_until: continue
        e=t.floor("h"); x=e+pd.Timedelta(hours=24)
        if e not in px.index or x not in px.index: continue
        p0=float(px.loc[e]); p1=float(px.loc[x]); gross=int(r.side)*(p1/p0-1)
        trades.append({"ts":t.isoformat(),"side":int(r.side),"funding":float(r.funding),
                       "oi_growth_24h":float(r.oi_growth_24h),"entry":p0,"exit":p1,
                       "gross":gross,"net10":gross-.001,"net20":gross-.002})
        active_until=x
    d=pd.DataFrame(trades); n=len(d)
    if n:
        d["year"]=pd.to_datetime(d["ts"],utc=True,format="mixed").dt.year
        years={str(int(y)):float(v) for y,v in d.groupby("year")["net10"].mean().items()}
        ci=boot_ci(d["net10"].to_numpy(),seed)
        s={"N":n,"long_N":int((d.side==1).sum()),"short_N":int((d.side==-1).sum()),
           "mean_net10":float(d.net10.mean()),"median_net10":float(d.net10.median()),
           "hit_rate":float((d.net10>0).mean()),"profit_factor_net10":pf(d.net10),
           "bootstrap_95_ci_mean_net10":ci,"mean_net20":float(d.net20.mean()),
           "profit_factor_net20":pf(d.net20),"year_means_net10":years,
           "positive_year_count":int(sum(v>0 for v in years.values())),
           "max_losing_streak":int(streak(d.net10.to_numpy()))}
    else:s={"N":0}
    g={"N_gte_60":n>=60,"mean_net10_gt_0":n>0 and s["mean_net10"]>0,
       "pf_net10_gte_1_10":n>0 and s["profit_factor_net10"]>=1.10,
       "bootstrap_lower_gt_0":n>0 and s["bootstrap_95_ci_mean_net10"][0]>0,
       "positive_years_gte_3":n>0 and s["positive_year_count"]>=3,
       "mean_net20_gt_0":n>0 and s["mean_net20"]>0,
       "pf_net20_gt_1":n>0 and s["profit_factor_net20"]>1}
    verdict="DISCOVERY_PASS_CROWDING_UNWIND_SIGNAL" if n>=60 and all(g.values()) else ("INSUFFICIENT_SAMPLE" if n<60 else "DISCOVERY_FAIL_NO_PROMOTION")
    return {"symbol":symbol,"verdict":verdict,"stats":s,"gates":g,"trades":d}

def main():
    sources={}
    source_receipt={"lab_id":"PERP-CROWDING-UNWIND-XASSET-001","symbols":{},"outcomes_opened":False}
    for sym in SYMBOLS:
        s=source_for(sym); sources[sym]=s
        source_receipt["symbols"][sym]={"classification":s["classification"],"full_month_count":s["full_month_count"],"records":s["records"]}
    Path("pcu_xasset_source_receipt_v01.json").write_text(json.dumps(source_receipt,indent=2,sort_keys=True)+"\n")
    if any(sources[s]["classification"]!="FULL" for s in SYMBOLS):
        print(json.dumps({"source":{s:sources[s]["classification"] for s in SYMBOLS},"outcomes_opened":False},sort_keys=True))
        return 2

    results={}
    for i,sym in enumerate(SYMBOLS):
        r=discover(sym,sources[sym],SEED+i)
        r["trades"].to_csv(f"pcu_xasset_{sym.lower()}_trades_v01.csv",index=False)
        results[sym]={"verdict":r["verdict"],"stats":r["stats"],"gates":r["gates"]}
    any_pass=any(results[s]["verdict"]=="DISCOVERY_PASS_CROWDING_UNWIND_SIGNAL" for s in SYMBOLS)
    family_status="XASSET_HAS_INDEPENDENT_PASS" if any_pass else "XASSET_NO_INDEPENDENT_PASS_CLOSE_FAMILY"
    out={"lab_id":"PERP-CROWDING-UNWIND-XASSET-001","results":results,"family_status":family_status,
         "btc_eth_rewritten":False,"protected_2025_2026_opened":False}
    Path("pcu_xasset_discovery_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())

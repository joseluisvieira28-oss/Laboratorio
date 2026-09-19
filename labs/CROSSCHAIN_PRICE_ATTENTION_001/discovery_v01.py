#!/usr/bin/env python3
from __future__ import annotations
import concurrent.futures, io, json, math, urllib.request, zipfile
from pathlib import Path
import numpy as np
import pandas as pd

TRADE=["ETHUSDT","SOLUSDT","BNBUSDT","AVAXUSDT"]
MONTHS=pd.period_range("2022-01","2025-12",freq="M").astype(str).tolist()
BASE="https://data.binance.vision/data/futures/um/monthly"
SEED=230925; BOOT=10000; BLOCK=5

def fetch_zip(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CPA/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name=z.namelist()[0]; data=z.read(name)
    return data,len(raw)

def parse_kline(data):
    d=pd.read_csv(io.BytesIO(data),header=None)
    if d.shape[1]<7: raise RuntimeError("kline schema")
    d=d.iloc[:,:12].copy()
    d.columns=["open_time","open","high","low","close","volume","close_time","quote_volume","trades","taker_base","taker_quote","ignore"]
    return d[["open_time","open"]]

def parse_funding(data):
    d=pd.read_csv(io.BytesIO(data))
    if not {"calc_time","last_funding_rate"}.issubset(d.columns): raise RuntimeError("funding schema")
    return d[["calc_time","last_funding_rate"]]

def fetch_one(args):
    sym,m,kind=args
    if kind=="kline":
        u=f"{BASE}/klines/{sym}/1h/{sym}-1h-{m}.zip"
    else:
        u=f"{BASE}/fundingRate/{sym}/{sym}-fundingRate-{m}.zip"
    try:
        data,n=fetch_zip(u)
        d=parse_kline(data) if kind=="kline" else parse_funding(data)
        d["symbol"]=sym; d["source_month"]=m
        return sym,m,kind,d,n,None
    except Exception as e:
        return sym,m,kind,None,0,f"{type(e).__name__}:{str(e)[:220]}"

def ptime(s):
    n=pd.to_numeric(s,errors="coerce")
    if n.notna().any():
        med=float(n.dropna().abs().median())
        unit="ns" if med>1e17 else ("us" if med>1e14 else ("ms" if med>1e11 else "s"))
        x=pd.to_datetime(n,unit=unit,utc=True,errors="coerce")
    else:
        x=pd.to_datetime(s,utc=True,errors="coerce")
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

def summary(d,col,seed):
    x=d[col].to_numpy(float)
    yrs={str(int(y)):float(v) for y,v in d.groupby("year")[col].mean().items()}
    return {"N":int(len(d)),"mean":float(x.mean()),"median":float(np.median(x)),
            "hit_rate":float(np.mean(x>0)),"profit_factor":pf(x),
            "bootstrap95":boot_ci(x,seed),"year_means":yrs,
            "positive_year_count":int(sum(v>0 for v in yrs.values())),
            "max_losing_streak":int(streak(x))}

def main():
    rec=[]; kd=[]; fd=[]
    jobs=[(s,m,k) for s in TRADE for m in MONTHS for k in ("kline","funding")]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as ex:
        for sym,m,kind,d,n,e in ex.map(fetch_one,jobs):
            rec.append({"symbol":sym,"month":m,"kind":kind,"ok":d is not None,"zip_bytes":n,"error":e})
            if d is not None:
                (kd if kind=="kline" else fd).append(d)

    cov={}
    for s in TRADE:
        by={}
        for kind in ("kline","funding"):
            ok=[r["month"] for r in rec if r["symbol"]==s and r["kind"]==kind and r["ok"]]
            yc={str(y):sum(m.startswith(str(y)+"-") for m in ok) for y in range(2022,2026)}
            by[kind]={"months":len(ok),"by_year":yc}
        cov[s]=by
    full=all(cov[s][k]["months"]>=46 and min(cov[s][k]["by_year"].values())>=11 for s in TRADE for k in ("kline","funding"))
    source_cls="CPA_SOURCE_FULL" if full else "CPA_SOURCE_BLOCKED"
    Path("cpa_source_receipt_v01.json").write_text(json.dumps({"classification":source_cls,"coverage":cov,"records":rec,"outcomes_opened":False},indent=2,sort_keys=True)+"\n")
    print(json.dumps({"source_classification":source_cls,"coverage":cov},sort_keys=True))
    if not full:return 2

    k=pd.concat(kd,ignore_index=True); f=pd.concat(fd,ignore_index=True)
    k["ts"]=ptime(k["open_time"]); k["open"]=pd.to_numeric(k["open"],errors="coerce")
    k=k[k["ts"].notna()&(k["open"]>0)].drop_duplicates(["symbol","ts"],keep="last")
    f["ts"]=ptime(f["calc_time"]); f["rate"]=pd.to_numeric(f["last_funding_rate"],errors="coerce")
    f=f[f["ts"].notna()&f["rate"].notna()].drop_duplicates(["symbol","ts"],keep="last")

    px=k.pivot(index="ts",columns="symbol",values="open").sort_index()
    half=px[px.index.hour.isin([0,12])].copy()
    ret=np.log(half[TRADE]/half[TRADE].shift(1))
    gap=half.index.to_series().diff().dt.total_seconds()/3600
    ret.loc[~gap.eq(12),:]=np.nan
    q95=ret.shift(1).rolling(180,min_periods=120).quantile(.95)
    sd=ret.shift(1).rolling(180,min_periods=120).std(ddof=1)
    fr={s:f[f["symbol"]==s].set_index("ts")["rate"].sort_index() for s in TRADE}

    events=[]; active_until=None
    for t in ret.index:
        eligible=[]
        for s in TRADE:
            r=ret.at[t,s]; q=q95.at[t,s]; v=sd.at[t,s]
            if pd.notna(r) and pd.notna(q) and pd.notna(v) and v>0 and r>0 and r>=q:
                eligible.append((s,float(r/v),float(r),float(q)))
        if not eligible: continue
        eligible.sort(key=lambda x:(-x[1],x[0]))
        winner,z,shock,q=eligible[0]
        entry=t+pd.Timedelta(hours=1); exit_t=t+pd.Timedelta(hours=13)
        if active_until is not None and entry<active_until: continue
        if entry not in px.index or exit_t not in px.index: continue
        if any(pd.isna(px.at[entry,s]) or pd.isna(px.at[exit_t,s]) for s in TRADE): continue
        rivals=[s for s in TRADE if s!=winner]
        fut={s:float(np.log(px.at[exit_t,s]/px.at[entry,s])) for s in TRADE}
        price_component=fut[winner]-float(np.mean([fut[s] for s in rivals]))

        weights={winner:1.0, **{s:-1/3 for s in rivals}}
        funding_component=0.0
        funding_count=0
        for s,w in weights.items():
            qf=fr[s][(fr[s].index>entry)&(fr[s].index<=exit_t)]
            funding_count+=len(qf)
            funding_component+=float((-w*qf).sum())
        gross=price_component+funding_component
        events.append({"signal_ts":t.isoformat(),"entry_ts":entry.isoformat(),"exit_ts":exit_t.isoformat(),
                       "winner":winner,"shock_ret12h":shock,"shock_z":z,"shock_q95":q,
                       "price_component":price_component,"funding_component":funding_component,
                       "funding_settlement_leg_count":int(funding_count),
                       "gross":gross,"net20":gross-.002,"net40":gross-.004})
        active_until=exit_t

    d=pd.DataFrame(events)
    if d.empty:
        final={"verdict":"INSUFFICIENT_SAMPLE","N":0,"holdout_2025_opened":False,"protected_2026_opened":False}
        Path("cpa_final_receipt_v01.json").write_text(json.dumps(final,indent=2)+"\n"); print(json.dumps(final)); return 0
    d["dt"]=pd.to_datetime(d["signal_ts"],utc=True,format="mixed"); d["year"]=d["dt"].dt.year
    disc=d[(d["dt"]>=pd.Timestamp("2022-01-01",tz="UTC"))&(d["dt"]<pd.Timestamp("2025-01-01",tz="UTC"))].copy()
    s20=summary(disc,"net20",SEED); s40=summary(disc,"net40",SEED+1)
    gates={"N_gte_60":len(disc)>=60,"mean_net20_gt_0":len(disc)>0 and s20["mean"]>0,
           "pf_net20_gte_1_10":len(disc)>0 and s20["profit_factor"]>=1.10,
           "bootstrap_lower_net20_gt_0":len(disc)>0 and s20["bootstrap95"][0]>0,
           "positive_years_gte_2":len(disc)>0 and s20["positive_year_count"]>=2,
           "mean_net40_gt_0":len(disc)>0 and s40["mean"]>0,
           "pf_net40_gt_1":len(disc)>0 and s40["profit_factor"]>1}
    dp=len(disc)>=60 and all(gates.values())
    disc_receipt={"stats_net20":s20,"stats_net40":s40,"gates":gates,
                  "event_counts_by_winner":disc["winner"].value_counts().to_dict(),
                  "verdict":"DISCOVERY_PASS" if dp else ("INSUFFICIENT_SAMPLE" if len(disc)<60 else "DISCOVERY_FAIL_NO_PROMOTION")}
    Path("cpa_discovery_receipt_v01.json").write_text(json.dumps(disc_receipt,indent=2,sort_keys=True)+"\n")
    disc.to_csv("cpa_discovery_trades_v01.csv",index=False)
    print(json.dumps({"discovery":disc_receipt},sort_keys=True))
    if not dp:
        final={"lab_id":"CROSSCHAIN-PRICE-ATTENTION-001","verdict":disc_receipt["verdict"],
               "holdout_2025_opened":False,"protected_2026_opened":False}
        Path("cpa_final_receipt_v01.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
        return 0

    hold=d[(d["dt"]>=pd.Timestamp("2025-01-01",tz="UTC"))&(d["dt"]<pd.Timestamp("2026-01-01",tz="UTC"))].copy()
    h20=summary(hold,"net20",SEED+2) if len(hold) else {"N":0}
    h40=summary(hold,"net40",SEED+3) if len(hold) else {"N":0}
    hg={"N_gte_20":len(hold)>=20,"mean_net20_gt_0":len(hold)>0 and h20["mean"]>0,
        "pf_net20_gt_1":len(hold)>0 and h20["profit_factor"]>1,
        "bootstrap_lower_net20_gt_0":len(hold)>0 and h20["bootstrap95"][0]>0,
        "mean_net40_gt_0":len(hold)>0 and h40["mean"]>0}
    hp=len(hold)>=20 and all(hg.values())
    verdict="SURVIVES_2025_HOLDOUT" if hp else "DISCOVERY_PASS_HOLDOUT_FAIL"
    final={"lab_id":"CROSSCHAIN-PRICE-ATTENTION-001","verdict":verdict,"discovery":disc_receipt,
           "holdout_2025":{"stats_net20":h20,"stats_net40":h40,"gates":hg,
                           "event_counts_by_winner":hold["winner"].value_counts().to_dict()},
           "holdout_2025_opened":True,"protected_2026_opened":False}
    Path("cpa_final_receipt_v01.json").write_text(json.dumps(final,indent=2,sort_keys=True)+"\n")
    hold.to_csv("cpa_holdout_2025_trades_v01.csv",index=False)
    print(json.dumps(final,sort_keys=True))
    return 0

if __name__=="__main__": raise SystemExit(main())

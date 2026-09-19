#!/usr/bin/env python3
from __future__ import annotations
import io,json,math,urllib.request,zipfile
from pathlib import Path
import numpy as np
import pandas as pd

MAP={"ETH":"ETHUSDT","SOL":"SOLUSDT","AVAX":"AVAXUSDT"}
SEED=230924; REPS=10000; BLOCK=5

def fetch_zip(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CAR-Discovery/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z: return z.read(z.namelist()[0])

def prices(symbol):
    fs=[]
    for y in (2022,2023,2024):
      for m in range(1,13):
        ym=f"{y:04d}-{m:02d}"
        u=f"https://data.binance.vision/data/spot/monthly/klines/{symbol}/1d/{symbol}-1d-{ym}.zip"
        raw=fetch_zip(u); d=pd.read_csv(io.BytesIO(raw),header=None)
        if d.shape[1]<7: raise RuntimeError("bad kline "+symbol+" "+ym)
        d=d.iloc[:,:12]; d.columns=["open_time","open","h","l","c","v","ct","q","n","tb","tq","i"]
        fs.append(d[["open_time","open"]])
    p=pd.concat(fs,ignore_index=True)
    n=pd.to_numeric(p["open_time"],errors="coerce"); med=float(n.dropna().abs().median())
    unit="us" if med>1e14 else ("ms" if med>1e11 else "s")
    p["date"]=pd.to_datetime(n,unit=unit,utc=True,errors="coerce").dt.floor("D")
    p["open"]=pd.to_numeric(p["open"],errors="coerce")
    p=p[p["date"].notna()&(p["open"]>0)].drop_duplicates("date",keep="last")
    if p["date"].max()>pd.Timestamp("2024-12-31",tz="UTC"): raise RuntimeError("protected boundary")
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

def main():
    src=json.loads(Path("car_v02_source_receipt.json").read_text())
    if src["classification"]!="CAR_SOURCE_FULL_V02": raise SystemExit("source blocked; no outcomes")
    a=pd.read_csv("car_v02_activity.csv")
    a["date"]=pd.to_datetime(a["date"],utc=True,errors="coerce").dt.floor("D")
    a["activity"]=pd.to_numeric(a["activity"],errors="coerce")
    a=a[a["activity"]>0].copy(); a["log_activity"]=np.log(a["activity"])
    outs=[]
    for chain,g in a.groupby("chain"):
        g=g.sort_values("date").copy()
        g["mu28"]=g["log_activity"].shift(1).rolling(28,min_periods=28).mean()
        g["sd28"]=g["log_activity"].shift(1).rolling(28,min_periods=28).std(ddof=1)
        g["z"]=(g["log_activity"]-g["mu28"])/g["sd28"]
        outs.append(g[["chain","date","z"]])
    z=pd.concat(outs).pivot(index="date",columns="chain",values="z").dropna().sort_index()
    ps={c:prices(s) for c,s in MAP.items()}

    events=[]; active_until=None
    for t,row in z.iterrows():
        if active_until is not None and t<active_until: continue
        vals=row.to_dict(); leader=max(vals,key=vals.get); others=[c for c in MAP if c!=leader]
        med=float(np.median([vals[c] for c in others])); leadz=float(vals[leader])
        if leadz<1.5 or leadz-med<.75: continue
        e=t+pd.Timedelta(days=1); x=e+pd.Timedelta(days=3)
        if any(e not in ps[c].index or x not in ps[c].index for c in MAP): continue
        rr={c:math.log(float(ps[c].loc[x])/float(ps[c].loc[e])) for c in MAP}
        rel=rr[leader]-float(np.mean([rr[c] for c in others]))
        events.append({"signal_date":t.isoformat(),"entry":e.isoformat(),"exit":x.isoformat(),
                       "leader":leader,"leader_z":leadz,"peer_median_z":med,
                       "relative_return":rel,**{f"ret_{c}":rr[c] for c in MAP}})
        active_until=x
    d=pd.DataFrame(events); n=len(d)
    if n:
        d["year"]=pd.to_datetime(d["signal_date"],utc=True,format="mixed").dt.year
        years={str(int(y)):float(v) for y,v in d.groupby("year")["relative_return"].mean().items()}
        counts={str(k):int(v) for k,v in d["leader"].value_counts().items()}
        ci=boot(d["relative_return"].to_numpy())
        st={"N":n,"mean_relative_return":float(d.relative_return.mean()),
            "median_relative_return":float(d.relative_return.median()),
            "leader_win_rate":float((d.relative_return>0).mean()),
            "bootstrap_95_ci_mean":ci,"year_means":years,
            "positive_year_count":int(sum(v>0 for v in years.values())),
            "event_counts_by_leader":counts,
            "max_losing_streak":int(streak(d.relative_return.to_numpy()))}
    else: st={"N":0}
    gates={"N_gte_60":n>=60,
           "mean_gt_0":n>0 and st["mean_relative_return"]>0,
           "median_gt_0":n>0 and st["median_relative_return"]>0,
           "bootstrap_lower_gt_0":n>0 and st["bootstrap_95_ci_mean"][0]>0,
           "positive_years_gte_2":n>0 and st["positive_year_count"]>=2,
           "leader_win_rate_gt_0_50":n>0 and st["leader_win_rate"]>.50}
    if n<60: verdict="INSUFFICIENT_SAMPLE"
    elif all(gates.values()): verdict="DISCOVERY_PASS_ATTENTION_REALLOCATION"
    else: verdict="DISCOVERY_FAIL_NO_PROMOTION"
    out={"lab_id":"CROSSCHAIN-ATTENTION-REALLOCATION-001","mve_id":"CAR-3CHAIN-ACTIVITY-LEADER-3D-001",
         "verdict":verdict,"stats":st,"gates":gates,"pnl_computed":False,
         "execution_claimed":False,"protected_2025_2026_opened":False}
    Path("car_v02_discovery_receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    d.to_csv("car_v02_events.csv",index=False)
    print(json.dumps(out,sort_keys=True))

if __name__=="__main__": raise SystemExit(main())

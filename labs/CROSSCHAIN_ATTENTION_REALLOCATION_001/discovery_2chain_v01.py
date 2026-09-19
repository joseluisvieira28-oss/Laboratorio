#!/usr/bin/env python3
from __future__ import annotations
import io,json,math,urllib.parse,urllib.request,zipfile
from pathlib import Path
import numpy as np
import pandas as pd

REPS=10000; BLOCK=5; SEED=230926
PRICE_BASE="https://data.binance.vision/data/spot/monthly/klines"

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CAR-2CHAIN/0.1","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as r: return json.loads(r.read().decode("utf-8"))

def eth_activity():
    p={"assets":"eth","metrics":"TxCnt","frequency":"1d","start_time":"2022-01-01","end_time":"2024-12-31","page_size":"10000"}
    u="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?"+urllib.parse.urlencode(p)
    js=get_json(u); d=pd.DataFrame(js.get("data",[]))
    if not {"time","TxCnt"}.issubset(d.columns): raise RuntimeError("ETH schema")
    return d.rename(columns={"time":"date","TxCnt":"activity"})[["date","activity"]]

def avax_activity():
    p={"startTimestamp":1640995200,"endTimestamp":1735689599,"timeInterval":"day","pageSize":2160}
    u="https://metrics.avax.network/v2/chains/43114/metrics/txCount?"+urllib.parse.urlencode(p)
    js=get_json(u); d=pd.DataFrame(js.get("results",[]))
    if not {"timestamp","value"}.issubset(d.columns): raise RuntimeError("AVAX schema")
    d["date"]=pd.to_datetime(pd.to_numeric(d["timestamp"],errors="coerce"),unit="s",utc=True,errors="coerce")
    return d.rename(columns={"value":"activity"})[["date","activity"]]

def clean(d,chain):
    d=d.copy(); d["date"]=pd.to_datetime(d["date"],utc=True,errors="coerce").dt.floor("D")
    d["activity"]=pd.to_numeric(d["activity"],errors="coerce")
    d=d[(d["date"]>=pd.Timestamp("2022-01-01",tz="UTC"))&(d["date"]<=pd.Timestamp("2024-12-31",tz="UTC"))]
    d=d[d["activity"]>0].sort_values("date").drop_duplicates("date",keep="last")
    d["chain"]=chain
    return d

def source_gate():
    e=clean(eth_activity(),"ETH"); a=clean(avax_activity(),"AVAX")
    rec={}
    for name,d in [("ETH",e),("AVAX",a)]:
        n=len(d); mn=d.date.min(); mx=d.date.max()
        full=n>=1000 and mn<=pd.Timestamp("2022-01-03",tz="UTC") and mx>=pd.Timestamp("2024-12-29",tz="UTC") and mx<=pd.Timestamp("2024-12-31",tz="UTC")
        rec[name]={"classification":"FULL" if full else "BLOCKED","row_count":n,
                   "date_min":mn.isoformat() if pd.notna(mn) else None,
                   "date_max":mx.isoformat() if pd.notna(mx) else None}
    cls="CAR_2CHAIN_SOURCE_FULL" if all(rec[c]["classification"]=="FULL" for c in rec) else "CAR_2CHAIN_SOURCE_BLOCKED"
    out={"classification":cls,"chains":rec,"outcomes_opened":False,"cash_spend_usd":0,
         "protected_2025_2026_requested":False}
    Path("car_2chain_source_receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    pd.concat([e,a],ignore_index=True).to_csv("car_2chain_activity.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return out

def fetch_zip(u):
    req=urllib.request.Request(u,headers={"User-Agent":"CryptoLab-CAR-2CHAIN/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r: raw=r.read()
    with zipfile.ZipFile(io.BytesIO(raw)) as z: return z.read(z.namelist()[0])

def price(symbol):
    fs=[]
    for y in (2022,2023):
        for m in range(1,13):
            ym=f"{y:04d}-{m:02d}"; u=f"{PRICE_BASE}/{symbol}/1d/{symbol}-1d-{ym}.zip"
            d=pd.read_csv(io.BytesIO(fetch_zip(u)),header=None)
            if d.shape[1]<7: raise RuntimeError("price schema "+symbol+" "+ym)
            d=d.iloc[:,:12]; d.columns=["ot","open","h","l","c","v","ct","q","n","tb","tq","i"]
            fs.append(d[["ot","open"]])
    p=pd.concat(fs,ignore_index=True); n=pd.to_numeric(p.ot,errors="coerce")
    med=float(n.dropna().abs().median()); unit="us" if med>1e14 else ("ms" if med>1e11 else "s")
    p["date"]=pd.to_datetime(n,unit=unit,utc=True,errors="coerce").dt.floor("D")
    p["open"]=pd.to_numeric(p.open,errors="coerce")
    p=p[p.date.notna()&(p.open>0)].sort_values("date").drop_duplicates("date",keep="last")
    if p.date.max()>pd.Timestamp("2023-12-31",tz="UTC"): raise RuntimeError("2024 boundary")
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
    if src["classification"]!="CAR_2CHAIN_SOURCE_FULL": raise SystemExit("source blocked")
    a=pd.read_csv("car_2chain_activity.csv")
    a["date"]=pd.to_datetime(a.date,utc=True,errors="coerce").dt.floor("D")
    a["activity"]=pd.to_numeric(a.activity,errors="coerce")
    outs=[]
    for chain,g in a.groupby("chain"):
        g=g[g.activity>0].sort_values("date").copy(); g["la"]=np.log(g.activity)
        g["mu"]=g.la.shift(1).rolling(28,min_periods=28).mean()
        g["sd"]=g.la.shift(1).rolling(28,min_periods=28).std(ddof=1)
        g["z"]=(g.la-g.mu)/g.sd; outs.append(g[["chain","date","z"]])
    z=pd.concat(outs).pivot(index="date",columns="chain",values="z").dropna().sort_index()
    z=z[(z.index>=pd.Timestamp("2022-02-01",tz="UTC"))&(z.index<=pd.Timestamp("2023-12-27",tz="UTC"))]
    px={"ETH":price("ETHUSDT"),"AVAX":price("AVAXUSDT")}
    ev=[]; active_until=None
    for t,r in z.iterrows():
        vals={"ETH":float(r["ETH"]),"AVAX":float(r["AVAX"])}
        leader=max(vals,key=vals.get); follower="AVAX" if leader=="ETH" else "ETH"
        if vals[leader]<1.5 or vals[leader]-vals[follower]<1.0: continue
        if active_until is not None and t<active_until: continue
        entry=t+pd.Timedelta(days=1); exit_=t+pd.Timedelta(days=4)
        if any(entry not in px[c].index or exit_ not in px[c].index for c in px): continue
        rl=math.log(float(px[leader].loc[exit_])/float(px[leader].loc[entry]))
        rf=math.log(float(px[follower].loc[exit_])/float(px[follower].loc[entry]))
        rel=rl-rf
        ev.append({"signal_date":t.isoformat(),"leader":leader,"follower":follower,
                   "leader_z":vals[leader],"follower_z":vals[follower],
                   "leader_return":rl,"follower_return":rf,"relative_return":rel})
        active_until=exit_
    d=pd.DataFrame(ev); n=len(d)
    if n:
        d["year"]=pd.to_datetime(d.signal_date,utc=True,format="mixed").dt.year
        yrs={str(int(y)):float(v) for y,v in d.groupby("year").relative_return.mean().items()}
        cnt={str(k):int(v) for k,v in d.leader.value_counts().items()}
        ci=boot(d.relative_return.to_numpy())
        st={"N":n,"mean_relative_return":float(d.relative_return.mean()),
            "median_relative_return":float(d.relative_return.median()),
            "leader_win_rate":float((d.relative_return>0).mean()),
            "bootstrap_95_ci_mean":ci,"year_means":yrs,
            "positive_year_count":int(sum(v>0 for v in yrs.values())),
            "event_counts_by_leader":cnt,"max_losing_streak":int(streak(d.relative_return.to_numpy()))}
    else: st={"N":0}
    gates={"N_gte_40":n>=40,"mean_gt_0":n>0 and st["mean_relative_return"]>0,
           "bootstrap_lower_gt_0":n>0 and st["bootstrap_95_ci_mean"][0]>0,
           "positive_years_eq_2":n>0 and st["positive_year_count"]==2,
           "leader_win_rate_gt_0_50":n>0 and st["leader_win_rate"]>.50}
    if n<40: verdict="INSUFFICIENT_SAMPLE"
    elif all(gates.values()): verdict="DISCOVERY_PASS_ATTENTION_REALLOCATION"
    else: verdict="DISCOVERY_FAIL_NO_PROMOTION"
    out={"lab_id":"CROSSCHAIN-ATTENTION-REALLOCATION-001","mve_id":"CAR-ETHAVAX-ACTIVITY-LEADER-3D-001",
         "verdict":verdict,"stats":st,"gates":gates,"replication_2024_opened":False,
         "pnl_computed":False,"execution_claimed":False,"protected_2025_2026_opened":False}
    Path("car_2chain_discovery_receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    d.to_csv("car_2chain_events.csv",index=False)
    print(json.dumps(out,sort_keys=True))

def main():
    src=source_gate(); discovery(src)

if __name__=="__main__": main()

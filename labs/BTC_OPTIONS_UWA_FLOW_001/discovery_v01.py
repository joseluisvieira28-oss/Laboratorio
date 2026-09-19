#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,math
from pathlib import Path
import numpy as np
import pandas as pd

SEED=230920; BOOT=10000; BLOCK=5

def pf(x):
    x=np.asarray(x,float); p=x[x>0].sum(); n=-x[x<0].sum()
    return float(p/n) if n>0 else (float("inf") if p>0 else 0.0)

def streak(x):
    m=c=0
    for v in x:
        if v<0:c+=1;m=max(m,c)
        else:c=0
    return m

def boot(x):
    x=np.asarray(x,float); n=len(x); rng=np.random.default_rng(SEED); out=np.empty(BOOT); nb=math.ceil(n/BLOCK)
    for i in range(BOOT):
        vals=[]
        for s in rng.integers(0,n,size=nb): vals.extend(x[(s+np.arange(BLOCK))%n].tolist())
        out[i]=np.mean(vals[:n])
    return [float(np.quantile(out,.025)),float(np.quantile(out,.975))]

def main(path):
    df=pd.read_csv(path,low_memory=False)
    req={"time_trade","direction","amount","price_USD","type","index_price"}
    if not req.issubset(df.columns):
        raise SystemExit("BLOCKED_SOURCE_SEMANTICS missing "+repr(sorted(req-set(df.columns))))
    df["ts"]=pd.to_datetime(df["time_trade"],utc=True,errors="coerce")
    for c in ["amount","price_USD","index_price"]: df[c]=pd.to_numeric(df[c],errors="coerce")
    df=df[df["ts"].notna()&(df["amount"]>=0)&(df["price_USD"]>0)&(df["index_price"]>0)]
    df=df[(df["ts"]>=pd.Timestamp("2017-01-01",tz="UTC"))&(df["ts"]<pd.Timestamp("2019-01-01",tz="UTC"))].copy()
    key=df["direction"].astype(str).str.lower()+"_"+df["type"].astype(str).str.lower()
    mp={"buy_call":1,"sell_call":-1,"buy_put":-1,"sell_put":1}
    df["sgn"]=key.map(mp)
    df=df[df["sgn"].notna()].copy()
    df["w"]=df["amount"]*df["price_USD"]
    df["sw"]=df["sgn"]*df["w"]
    df=df.sort_values("ts")
    df["bin"]=df["ts"].dt.floor("4h")
    g=df.groupby("bin").agg(sw=("sw","sum"),activity=("w","sum"),last_ts=("ts","max"),px=("index_price","last"),trades=("ts","size")).reset_index()
    g["imbalance"]=g["sw"]/g["activity"]
    g["bin_end"]=g["bin"]+pd.Timedelta(hours=4)
    g["fresh_minutes"]=(g["bin_end"]-g["last_ts"]).dt.total_seconds()/60
    g=g[g["fresh_minutes"]<=30].copy().sort_values("bin")
    g["absimb"]=g["imbalance"].abs()
    g["q90"]=g["absimb"].shift(1).rolling(360,min_periods=180).quantile(.90)
    g["act50"]=g["activity"].shift(1).rolling(360,min_periods=180).quantile(.50)
    g["signal"]=(g["absimb"]>=g["q90"])&(g["activity"]>=g["act50"])
    lookup=g.set_index("bin")
    trades=[]; active_until=None
    for r in g[g["signal"]].itertuples(index=False):
        t=r.bin
        if active_until is not None and t<active_until: continue
        exit_bin=t+pd.Timedelta(hours=24)
        if exit_bin not in lookup.index: continue
        ex=lookup.loc[exit_bin]
        if isinstance(ex,pd.DataFrame): ex=ex.iloc[-1]
        if float(ex["fresh_minutes"])>30: continue
        side=1 if r.imbalance>0 else -1
        gross=side*(float(ex["px"])/float(r.px)-1)
        trades.append({"bin":t.isoformat(),"exit_bin":exit_bin.isoformat(),"side":side,"imbalance":float(r.imbalance),
                       "activity":float(r.activity),"entry":float(r.px),"exit":float(ex["px"]),
                       "gross":gross,"net10":gross-.001,"net20":gross-.002})
        active_until=exit_bin
    d=pd.DataFrame(trades); n=len(d)
    if n:
        d["year"]=pd.to_datetime(d["bin"],utc=True).dt.year
        years={str(int(y)):float(v) for y,v in d.groupby("year")["net10"].mean().items()}
        ci=boot(d["net10"].to_numpy())
        s={"N":n,"mean_net10":float(d.net10.mean()),"median_net10":float(d.net10.median()),
           "hit_rate":float((d.net10>0).mean()),"profit_factor_net10":pf(d.net10),
           "bootstrap_95_ci_mean_net10":ci,"mean_net20":float(d.net20.mean()),
           "profit_factor_net20":pf(d.net20),"year_means":years,
           "positive_year_count":int(sum(v>0 for v in years.values())),
           "max_losing_streak":int(streak(d.net10.to_numpy()))}
    else:s={"N":0}
    gates={
      "N_gte_60":n>=60,
      "mean_net10_gt_0":n>0 and s["mean_net10"]>0,
      "pf_net10_gte_1_10":n>0 and s["profit_factor_net10"]>=1.10,
      "bootstrap_lower_gt_0":n>0 and s["bootstrap_95_ci_mean_net10"][0]>0,
      "positive_years_eq_2":n>0 and s["positive_year_count"]==2,
      "mean_net20_gt_0":n>0 and s["mean_net20"]>0,
      "pf_net20_gt_1":n>0 and s["profit_factor_net20"]>1
    }
    verdict="DISCOVERY_PASS_SIGNED_OPTION_FLOW" if n>=60 and all(gates.values()) else ("INSUFFICIENT_SAMPLE" if n<60 else "DISCOVERY_FAIL_NO_PROMOTION")
    out={"lab_id":"BTC-OPTIONS-UWA-FLOW-001","mve_id":"UWA-SIGNED-OPTION-FLOW-24H-001","verdict":verdict,"stats":s,"gates":gates,
         "replication_2019_opened":False,"year_2020_opened":False,"index_price_is_research_proxy":True}
    Path("uwa_flow_discovery_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    d.to_csv("uwa_flow_discovery_trades_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("csv"); a=ap.parse_args(); main(a.csv)

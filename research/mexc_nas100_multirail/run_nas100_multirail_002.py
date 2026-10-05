#!/usr/bin/env python3
import json,time
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd
import numpy as np

BASE="https://contract.mexc.com/api/v1/contract"
OUT=Path("research/mexc_nas100_multirail/results_002")
RAW=OUT/"raw"
OUT.mkdir(parents=True,exist_ok=True); RAW.mkdir(parents=True,exist_ok=True)
SYMS=["NAS100_USDT","NAS100_USD1"]
START=pd.Timestamp("2026-06-25T14:00:00Z")
END=pd.Timestamp.now(tz="UTC").floor("min")
DISC_END=pd.Timestamp("2026-08-15T23:59:00Z")
OOS1_END=pd.Timestamp("2026-09-15T23:59:00Z")
UA={"User-Agent":"CryptoLab-NAS100-MULTIRAIL-002/1.0"}

PAIR_TRIGGER=40.0
ONE_TRIGGER=20.0
OTHER_MAX=5.0
PAIR_FEE=32.0
ONE_FEE=16.0

def req(url,params=None,tries=4):
    err=None
    for i in range(tries):
        try:
            r=requests.get(url,params=params,timeout=20,headers=UA)
            if r.status_code==200:
                j=r.json()
                if isinstance(j,dict) and j.get("success") is False:
                    raise RuntimeError(str(j))
                return j,r.url
            err=f"HTTP {r.status_code} {r.text[:200]}"
        except Exception as e: err=repr(e)
        time.sleep(.5*(i+1))
    raise RuntimeError(f"GET failed {url}: {err}")

def fetch(symbol,kind):
    if kind=="last": path=f"/kline/{symbol}"
    elif kind=="index": path=f"/kline/index_price/{symbol}"
    else: path=f"/kline/fair_price/{symbol}"
    cur=int(START.timestamp()); stop=int(END.timestamp()); chunk=1900*60
    frames=[]; nreq=0
    while cur<=stop:
        e=min(stop,cur+chunk-60)
        j,_=req(BASE+path,{"interval":"Min1","start":cur,"end":e}); nreq+=1
        d=j.get("data") or {}; t=d.get("time") or []; o=d.get("open") or []; c=d.get("close") or []
        n=min(len(t),len(o),len(c))
        if n:
            frames.append(pd.DataFrame({"ts":[int(x) for x in t[:n]],f"{kind}_open":[float(x) for x in o[:n]],f"{kind}_close":[float(x) for x in c[:n]]}))
        cur=e+60; time.sleep(.02)
    if not frames: return pd.DataFrame(),nreq
    return pd.concat(frames,ignore_index=True).drop_duplicates("ts").sort_values("ts"),nreq

def split(ts):
    t=pd.to_datetime(ts,unit="s",utc=True)
    if t<=DISC_END:return "DISCOVERY"
    if t<=OOS1_END:return "OOS1"
    return "OOS2"

def bps(px1,px0): return (px1/px0-1)*10000.0

def suppress(sig,hold):
    if sig.empty:return sig
    rows=[]; until=-1
    for _,r in sig.sort_values("ts").iterrows():
        t=int(r["ts"])
        if t>=until:
            rows.append(r); until=t+hold*60
    return pd.DataFrame(rows)

def pair_events(df,hold):
    sig=suppress(df[df["premium_spread_bps"].abs()>=PAIR_TRIGGER][["ts","premium_spread_bps"]],15)
    by=df.set_index("ts"); out=[]
    for _,r in sig.iterrows():
        t=int(r["ts"]); ent=t+60; ex=ent+hold*60
        if ent not in by.index or ex not in by.index: continue
        a=by.loc[ent]; z=by.loc[ex]
        if isinstance(a,pd.DataFrame):a=a.iloc[0]
        if isinstance(z,pd.DataFrame):z=z.iloc[0]
        s=1 if float(r["premium_spread_bps"])>0 else -1
        ru=bps(float(z["usdt_last_close"]),float(a["usdt_last_open"]))
        rd=bps(float(z["usd1_last_close"]),float(a["usd1_last_open"]))
        gross=s*(rd-ru)
        out.append({"ts":t,"split":split(t),"gross_bps":gross,"net_bps":gross-PAIR_FEE,"date":pd.to_datetime(t,unit="s",utc=True).date().isoformat(),"signal_bps":float(r["premium_spread_bps"])})
    return pd.DataFrame(out)

def one_events(df,rail,anchor,hold):
    pcol=f"{rail}_{anchor}_premium_bps"
    other="usd1" if rail=="usdt" else "usdt"
    ocol=f"{other}_{anchor}_premium_bps"
    sig=suppress(df[(df[pcol].abs()>=ONE_TRIGGER)&(df[ocol].abs()<=OTHER_MAX)][["ts",pcol]],1)
    by=df.set_index("ts"); out=[]
    for _,r in sig.iterrows():
        t=int(r["ts"]); ent=t+60; ex=ent+hold*60
        if ent not in by.index or ex not in by.index: continue
        a=by.loc[ent]; z=by.loc[ex]
        if isinstance(a,pd.DataFrame):a=a.iloc[0]
        if isinstance(z,pd.DataFrame):z=z.iloc[0]
        prem=float(r[pcol]); direction=-1 if prem>0 else 1
        gross=direction*bps(float(z[f"{rail}_last_close"]),float(a[f"{rail}_last_open"]))
        out.append({"ts":t,"split":split(t),"gross_bps":gross,"net_bps":gross-ONE_FEE,"date":pd.to_datetime(t,unit="s",utc=True).date().isoformat(),"signal_bps":prem})
    return pd.DataFrame(out)

def summarize(name,horizon,ev):
    out=[]
    for sp in ["DISCOVERY","OOS1","OOS2"]:
        g=ev[ev["split"]==sp] if not ev.empty else pd.DataFrame()
        if g.empty:
            out.append({"hypothesis":name,"horizon_min":horizon,"split":sp,"n":0});continue
        gross=g["gross_bps"];net=g["net_bps"]
        day=g.groupby("date")["gross_bps"].sum()
        total=float(gross.sum())
        conc=float(day.clip(lower=0).max()/total) if total>0 and len(day) else np.nan
        out.append({"hypothesis":name,"horizon_min":horizon,"split":sp,"n":int(len(g)),
                    "gross_mean_bps":float(gross.mean()),"gross_median_bps":float(gross.median()),"gross_total_bps":total,
                    "net_mean_bps":float(net.mean()),"net_median_bps":float(net.median()),"net_total_bps":float(net.sum()),
                    "win_rate_net":float((net>0).mean()),"max_single_positive_day_share":conc})
    return out

def verdict(name,metrics,primary_h):
    rows={r["split"]:r for r in metrics if r["hypothesis"]==name and r["horizon_min"]==primary_h}
    if any(rows.get(s,{}).get("n",0)==0 for s in ["OOS1","OOS2"]): return "NO_EDGE"
    a,b=rows["OOS1"],rows["OOS2"]; n=a["n"]+b["n"]
    checks=[a["net_mean_bps"]>=5,b["net_mean_bps"]>=5,a["net_median_bps"]>=0,b["net_median_bps"]>=0,n>=20]
    for q in [a,b]:
        x=q.get("max_single_positive_day_share")
        if x is not None and np.isfinite(x): checks.append(x<=.35)
    return "SURVIVES_CANDLE_EXECUTION_PENDING" if all(checks) else "NO_EDGE"

# Architecture
j,_=req(BASE+"/detail"); data=j.get("data") or []
arch={}
for s in SYMS:
    x=next((q for q in data if q.get("symbol")==s),None)
    arch[s]={k:x.get(k) for k in ["symbol","contractSize","maxLeverage","priceUnit","settleCoin","quoteCoin","indexOrigin","state"]} if x else None
(OUT/"architecture.json").write_text(json.dumps(arch,indent=2),encoding="utf-8")
if any(v is None for v in arch.values()):
    summary={"study":"MEXC-NAS100-MULTIRAIL-002","verdict":"BLOCKED","reason":"missing contract architecture","architecture":arch}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));raise SystemExit

frames={}
requests_meta={}
for s in SYMS:
    parts=[];requests_meta[s]={}
    for k in ["last","index","fair"]:
        f,n=fetch(s,k);parts.append(f);requests_meta[s][k]={"rows":int(len(f)),"requests":n}
    x=parts[0]
    for p in parts[1:]:x=x.merge(p,on="ts",how="inner")
    frames[s]=x.sort_values("ts").drop_duplicates("ts")
    frames[s].to_csv(RAW/f"{s}_1m.csv.gz",index=False,compression="gzip")

u=frames["NAS100_USDT"].rename(columns={c:"usdt_"+c for c in frames["NAS100_USDT"].columns if c!="ts"})
d=frames["NAS100_USD1"].rename(columns={c:"usd1_"+c for c in frames["NAS100_USD1"].columns if c!="ts"})
m=u.merge(d,on="ts",how="inner").sort_values("ts").reset_index(drop=True)
ratio=len(m)/min(len(u),len(d)) if min(len(u),len(d)) else 0
if ratio<.95:
    summary={"study":"MEXC-NAS100-MULTIRAIL-002","verdict":"BLOCKED","reason":"common futures coverage below 95%","coverage":{"usdt":len(u),"usd1":len(d),"common":len(m),"ratio":ratio}}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2));raise SystemExit

m["usdt_index_premium_bps"]=(m["usdt_last_close"]/m["usdt_index_close"]-1)*10000
m["usd1_index_premium_bps"]=(m["usd1_last_close"]/m["usd1_index_close"]-1)*10000
m["premium_spread_bps"]=m["usdt_index_premium_bps"]-m["usd1_index_premium_bps"]
m["usdt_fair_premium_bps"]=(m["usdt_last_close"]/m["usdt_fair_close"]-1)*10000
m["usd1_fair_premium_bps"]=(m["usd1_last_close"]/m["usd1_fair_close"]-1)*10000
m.to_csv(RAW/"aligned_index_residuals.csv.gz",index=False,compression="gzip")

events={
"H5_pair_15":pair_events(m,15),
"H5_pair_60":pair_events(m,60),
"H6_usdt_1":one_events(m,"usdt","index",1),
"H6_usdt_5":one_events(m,"usdt","index",5),
"H7_usd1_1":one_events(m,"usd1","index",1),
"H7_usd1_5":one_events(m,"usd1","index",5),
"H8_usdt_fair_1":one_events(m,"usdt","fair",1),
"H8_usdt_fair_5":one_events(m,"usdt","fair",5),
"H8_usd1_fair_1":one_events(m,"usd1","fair",1),
"H8_usd1_fair_5":one_events(m,"usd1","fair",5),
}
for k,v in events.items():v.to_csv(RAW/f"{k}.csv.gz",index=False,compression="gzip")
metrics=[]
for nm,h,key in [
("H5_pair",15,"H5_pair_15"),("H5_pair",60,"H5_pair_60"),
("H6_usdt_index",1,"H6_usdt_1"),("H6_usdt_index",5,"H6_usdt_5"),
("H7_usd1_index",1,"H7_usd1_1"),("H7_usd1_index",5,"H7_usd1_5"),
("H8_usdt_fair",1,"H8_usdt_fair_1"),("H8_usdt_fair",5,"H8_usdt_fair_5"),
("H8_usd1_fair",1,"H8_usd1_fair_1"),("H8_usd1_fair",5,"H8_usd1_fair_5")]:
    metrics+=summarize(nm,h,events[key])
mdf=pd.DataFrame(metrics);mdf.to_csv(OUT/"hypothesis_metrics.csv",index=False)

desc={}
for col in ["usdt_index_premium_bps","usd1_index_premium_bps","premium_spread_bps","usdt_fair_premium_bps","usd1_fair_premium_bps"]:
    s=m[col].abs().dropna()
    desc[col]={"n":int(len(s)),"median_abs":float(s.median()),"p95_abs":float(s.quantile(.95)),"p99_abs":float(s.quantile(.99)),"max_abs":float(s.max()),"count_ge20":int((s>=20).sum()),"count_ge40":int((s>=40).sum())}

vs={
"H5_pair":verdict("H5_pair",metrics,15),
"H6_usdt_index":verdict("H6_usdt_index",metrics,1),
"H7_usd1_index":verdict("H7_usd1_index",metrics,1),
"H8_usdt_fair":verdict("H8_usdt_fair",metrics,1),
"H8_usd1_fair":verdict("H8_usd1_fair",metrics,1),
}
global_v="SURVIVES_CANDLE_EXECUTION_PENDING" if any(v.startswith("SURVIVES") for v in vs.values()) else "NO_EDGE"
summary={"study":"MEXC-NAS100-MULTIRAIL-002","verdict":global_v,"hypothesis_verdicts":vs,
         "coverage":{"usdt":len(u),"usd1":len(d),"common":len(m),"ratio":ratio},
         "architecture":arch,"descriptives":desc,
         "costs":{"one_leg_taker_rt_bps":16,"pair_taker_rt_bps":32},
         "important_limit":"1m candle screen only; no L1/L2 fill claims."}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
(OUT/"manifest.json").write_text(json.dumps({"created_at_utc":datetime.now(timezone.utc).isoformat(),"requests":requests_meta},indent=2),encoding="utf-8")
print("=== SUMMARY ===");print(json.dumps(summary,indent=2));print("\n=== METRICS ===");print(mdf.to_string(index=False))

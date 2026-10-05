#!/usr/bin/env python3
import json, math, os, sys, time
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd
import numpy as np

BASE="https://contract.mexc.com/api/v1/contract"
OUT=Path("research/mexc_gold_risk_window/results")
RAW=OUT/"raw"
RAW.mkdir(parents=True, exist_ok=True)

SYMBOLS=["XAU_USDT","XAUT_USDT","XAG_USDT"]
EVENTS={
    "SEP11_2026_CPI":{
        "macro":"2026-09-11T12:30:00Z",
        "cut":"2026-09-11T12:20:00Z",
        "restore":"2026-09-11T12:35:00Z",
        "start":"2026-09-11T11:30:00Z",
        "end":"2026-09-11T13:30:00Z",
        "source":"MEXC Sep 11 2026 leverage adjustment; CPI 12:30 UTC"
    },
    "SEP16_2026_FOMC":{
        "macro":"2026-09-16T18:00:00Z",
        "cut":"2026-09-16T17:50:00Z",
        "restore":"2026-09-16T18:05:00Z",
        "start":"2026-09-16T17:00:00Z",
        "end":"2026-09-16T19:00:00Z",
        "source":"MEXC Sep 16 2026 leverage adjustment; FOMC 18:00 UTC"
    },
}

API_TAKER_BPS_PER_SIDE=8.0
SINGLE_LEG_RT_BPS=16.0
PAIR_RT_BPS=32.0

def iso_dt(s):
    return datetime.fromisoformat(s.replace("Z","+00:00"))

def sec(s):
    return int(iso_dt(s).timestamp())

def get_json(url, params=None, tries=5):
    err=None
    for i in range(tries):
        try:
            r=requests.get(url, params=params, timeout=30, headers={"User-Agent":"CryptoLab-GOLD-RISK-WINDOW-001A/1.0"})
            if r.status_code==200:
                j=r.json()
                if isinstance(j,dict) and j.get("success") is False:
                    raise RuntimeError(f"MEXC success=false code={j.get('code')} message={j.get('message')}")
                return j, r.url
            err=f"HTTP {r.status_code}: {r.text[:300]}"
        except Exception as e:
            err=repr(e)
        time.sleep(1.5*(i+1))
    raise RuntimeError(f"GET failed {url} params={params}: {err}")

def fetch_kline(symbol, kind, start_s, end_s):
    if kind=="last":
        url=f"{BASE}/kline/{symbol}"
    elif kind=="index":
        url=f"{BASE}/kline/index_price/{symbol}"
    elif kind=="fair":
        url=f"{BASE}/kline/fair_price/{symbol}"
    else:
        raise ValueError(kind)
    j, final_url=get_json(url, {"interval":"Min1","start":start_s,"end":end_s})
    return j, final_url

def parse_kline(j, kind):
    d=j.get("data") or {}
    times=d.get("time") or []
    closes=d.get("close") or []
    opens=d.get("open") or []
    highs=d.get("high") or []
    lows=d.get("low") or []
    vols=d.get("vol") or [None]*len(times)
    amounts=d.get("amount") or [None]*len(times)
    n=min(map(len,[times,opens,closes,highs,lows]))
    rows=[]
    for i in range(n):
        rows.append({
            "ts":int(times[i]),
            f"{kind}_open":float(opens[i]),
            f"{kind}_high":float(highs[i]),
            f"{kind}_low":float(lows[i]),
            f"{kind}_close":float(closes[i]),
            f"{kind}_vol": None if i>=len(vols) or vols[i] is None else float(vols[i]),
            f"{kind}_amount": None if i>=len(amounts) or amounts[i] is None else float(amounts[i]),
        })
    return pd.DataFrame(rows)

def fetch_funding(symbol):
    j, final_url=get_json(f"{BASE}/funding_rate/history", {"symbol":symbol,"page_num":1,"page_size":1000})
    return j, final_url

def parse_funding(j):
    rows=((j.get("data") or {}).get("resultList") or [])
    out=[]
    for x in rows:
        try:
            out.append({"settleTime":int(x["settleTime"]),"fundingRate":float(x["fundingRate"])})
        except Exception:
            pass
    return pd.DataFrame(out)

def label_window(ts, e):
    macro=sec(e["macro"]); cut=sec(e["cut"]); restore=sec(e["restore"]); end=sec(e["end"])
    if ts < cut: return "PRE"
    if ts < macro: return "RESTRICTED_PRE"
    if ts < restore: return "SHOCK_RESTRICTED"
    if ts <= end: return "RESTORED_POST"
    return "OUT"

def robust_summary(series):
    s=pd.Series(series).dropna().astype(float)
    if s.empty:
        return {"n":0}
    return {
        "n":int(len(s)),
        "mean":float(s.mean()),
        "median":float(s.median()),
        "p95":float(s.quantile(.95)),
        "max":float(s.max()),
    }

manifest={"created_at_utc":datetime.now(timezone.utc).isoformat(),"events":{},"api_base":BASE}
frames={}
funding_rows=[]

for event_id,e in EVENTS.items():
    start_s,end_s=sec(e["start"]),sec(e["end"])
    manifest["events"][event_id]={"event":e,"symbols":{}}
    for symbol in SYMBOLS:
        dfs=[]
        smeta={}
        for kind in ["last","index","fair"]:
            try:
                j,u=fetch_kline(symbol,kind,start_s,end_s)
                (RAW/f"{event_id}__{symbol}__{kind}.json").write_text(json.dumps(j,indent=2),encoding="utf-8")
                df=parse_kline(j,kind)
                dfs.append(df)
                smeta[kind]={"url":u,"rows":int(len(df)),"success":True}
            except Exception as ex:
                smeta[kind]={"success":False,"error":repr(ex)}
        if dfs:
            df=dfs[0]
            for other in dfs[1:]:
                df=df.merge(other,on="ts",how="outer")
            df=df.sort_values("ts").reset_index(drop=True)
            df["utc"]=pd.to_datetime(df["ts"],unit="s",utc=True)
            df["event_id"]=event_id
            df["symbol"]=symbol
            df["window"]=df["ts"].map(lambda x: label_window(int(x),e))
            if {"last_close","index_close"}.issubset(df.columns):
                df["last_index_bps"]=(df["last_close"]/df["index_close"]-1.0)*10000.0
                df["abs_last_index_bps"]=df["last_index_bps"].abs()
            if {"fair_close","index_close"}.issubset(df.columns):
                df["fair_index_bps"]=(df["fair_close"]/df["index_close"]-1.0)*10000.0
                df["abs_fair_index_bps"]=df["fair_index_bps"].abs()
            frames[(event_id,symbol)]=df
            df.to_csv(OUT/f"{event_id}__{symbol}__aligned_1m.csv",index=False)
        try:
            fj,fu=fetch_funding(symbol)
            (RAW/f"{event_id}__{symbol}__funding.json").write_text(json.dumps(fj,indent=2),encoding="utf-8")
            fdf=parse_funding(fj)
            lo=(start_s-86400)*1000; hi=(end_s+86400)*1000
            if not fdf.empty:
                fdf=fdf[(fdf["settleTime"]>=lo)&(fdf["settleTime"]<=hi)].copy()
                for _,r in fdf.iterrows():
                    funding_rows.append({"event_id":event_id,"symbol":symbol,"settleTime":int(r["settleTime"]),"fundingRate":float(r["fundingRate"])})
            smeta["funding"]={"url":fu,"rows_near_event":int(len(fdf)),"success":True}
        except Exception as ex:
            smeta["funding"]={"success":False,"error":repr(ex)}
        manifest["events"][event_id]["symbols"][symbol]=smeta

# Cross-rail XAU-XAUT basis
cross_frames={}
for event_id in EVENTS:
    a=frames.get((event_id,"XAU_USDT"))
    b=frames.get((event_id,"XAUT_USDT"))
    if a is not None and b is not None and "last_close" in a and "last_close" in b:
        x=a[["ts","utc","window","last_close"]].rename(columns={"last_close":"xau_last"})
        y=b[["ts","last_close"]].rename(columns={"last_close":"xaut_last"})
        z=x.merge(y,on="ts",how="inner").sort_values("ts")
        z["xau_xaut_basis_bps"]=(z["xau_last"]/z["xaut_last"]-1.0)*10000.0
        pre=z.loc[z["window"]=="PRE","xau_xaut_basis_bps"]
        pre_med=float(pre.median()) if len(pre) else np.nan
        z["basis_dev_from_pre_bps"]=z["xau_xaut_basis_bps"]-pre_med
        z["abs_basis_dev_bps"]=z["basis_dev_from_pre_bps"].abs()
        cross_frames[event_id]=z
        z.to_csv(OUT/f"{event_id}__XAU_XAUT_basis_1m.csv",index=False)

# Metrics
rows=[]
for (event_id,symbol),df in frames.items():
    for w,g in df.groupby("window",dropna=False):
        if w=="OUT": continue
        row={"event_id":event_id,"symbol":symbol,"window":w,"n":int(len(g))}
        if "abs_last_index_bps" in g: row.update({f"last_index_abs_{k}":v for k,v in robust_summary(g["abs_last_index_bps"]).items()})
        if "abs_fair_index_bps" in g: row.update({f"fair_index_abs_{k}":v for k,v in robust_summary(g["abs_fair_index_bps"]).items()})
        rows.append(row)

basis_rows=[]
for event_id,z in cross_frames.items():
    for w,g in z.groupby("window"):
        if w=="OUT": continue
        s=robust_summary(g["abs_basis_dev_bps"])
        basis_rows.append({"event_id":event_id,"window":w,**{f"basis_dev_abs_{k}":v for k,v in s.items()}})

# Restoration compression exact: 5 min before restore vs 10 min after restore
restoration=[]
for (event_id,symbol),df in frames.items():
    e=EVENTS[event_id]; r=sec(e["restore"])
    before=df[(df["ts"]>=r-5*60)&(df["ts"]<r)]
    after=df[(df["ts"]>=r)&(df["ts"]<r+10*60)]
    for metric in ["abs_last_index_bps","abs_fair_index_bps"]:
        if metric in df:
            b=float(before[metric].median()) if len(before) and before[metric].notna().any() else np.nan
            a=float(after[metric].median()) if len(after) and after[metric].notna().any() else np.nan
            comp=(1-a/b) if (np.isfinite(b) and b>0 and np.isfinite(a)) else np.nan
            restoration.append({"event_id":event_id,"symbol":symbol,"metric":metric,"pre_restore_median":b,"post_restore_median":a,"compression_ratio":comp})

for event_id,z in cross_frames.items():
    r=sec(EVENTS[event_id]["restore"])
    before=z[(z["ts"]>=r-5*60)&(z["ts"]<r)]
    after=z[(z["ts"]>=r)&(z["ts"]<r+10*60)]
    metric="abs_basis_dev_bps"
    b=float(before[metric].median()) if len(before) and before[metric].notna().any() else np.nan
    a=float(after[metric].median()) if len(after) and after[metric].notna().any() else np.nan
    comp=(1-a/b) if (np.isfinite(b) and b>0 and np.isfinite(a)) else np.nan
    restoration.append({"event_id":event_id,"symbol":"XAU_XAUT_PAIR","metric":metric,"pre_restore_median":b,"post_restore_median":a,"compression_ratio":comp})

metrics=pd.DataFrame(rows)
basis=pd.DataFrame(basis_rows)
rest=pd.DataFrame(restoration)
fund=pd.DataFrame(funding_rows)
metrics.to_csv(OUT/"window_metrics.csv",index=False)
basis.to_csv(OUT/"basis_metrics.csv",index=False)
rest.to_csv(OUT/"restoration_compression.csv",index=False)
fund.to_csv(OUT/"funding_near_events.csv",index=False)

# Conservative magnitude screen — not a fill simulation.
all_last=[]
for df in frames.values():
    if "abs_last_index_bps" in df: all_last.extend(df["abs_last_index_bps"].dropna().tolist())
all_pair=[]
for z in cross_frames.values():
    all_pair.extend(z["abs_basis_dev_bps"].dropna().tolist())
max_last=float(max(all_last)) if all_last else None
max_pair=float(max(all_pair)) if all_pair else None

coverage_ok=True
coverage_issues=[]
for event_id in EVENTS:
    for symbol in SYMBOLS:
        df=frames.get((event_id,symbol))
        if df is None:
            coverage_ok=False; coverage_issues.append(f"{event_id}/{symbol}: no aligned frame"); continue
        expected=121
        n=int(df["ts"].nunique())
        if n < 100:
            coverage_ok=False; coverage_issues.append(f"{event_id}/{symbol}: only {n} unique minutes")

if not coverage_ok:
    verdict="BLOCKED_DATA_COVERAGE"
elif max_last is not None and max_last < SINGLE_LEG_RT_BPS and (max_pair is None or max_pair < PAIR_RT_BPS):
    verdict="NO_EDGE_1M_MAGNITUDE_SCREEN"
else:
    verdict="HISTORICAL_MAGNITUDE_CANDIDATE_NEEDS_EXECUTION_DATA"

summary={
    "study":"MEXC-GOLD-RISK-WINDOW-001A",
    "verdict":verdict,
    "important_limit":"1m close-based Last/Index/Fair data cannot prove executable fills; any candidate requires L1/L2 forward validation.",
    "fees_assumed_bps":{"api_taker_per_side":API_TAKER_BPS_PER_SIDE,"single_leg_round_trip":SINGLE_LEG_RT_BPS,"xau_xaut_pair_round_trip":PAIR_RT_BPS},
    "max_abs_last_index_close_bps":max_last,
    "max_abs_xau_xaut_basis_deviation_from_pre_median_bps":max_pair,
    "coverage_ok":coverage_ok,
    "coverage_issues":coverage_issues,
    "events":EVENTS,
}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")

print("=== GOLD-RISK-WINDOW-001A SUMMARY ===")
print(json.dumps(summary,indent=2))
print("\n=== WINDOW METRICS ===")
print(metrics.to_string(index=False) if len(metrics) else "NO METRICS")
print("\n=== BASIS METRICS ===")
print(basis.to_string(index=False) if len(basis) else "NO BASIS METRICS")
print("\n=== RESTORATION COMPRESSION ===")
print(rest.to_string(index=False) if len(rest) else "NO RESTORATION METRICS")
print("\n=== FUNDING NEAR EVENTS ===")
print(fund.to_string(index=False) if len(fund) else "NO FUNDING ROWS")

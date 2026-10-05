#!/usr/bin/env python3
import json, math, os, time
from pathlib import Path
from datetime import datetime, timezone
import requests
import pandas as pd
import numpy as np

BASE_FUT="https://contract.mexc.com/api/v1/contract"
BASE_SPOT="https://api.mexc.com/api/v3"
OUT=Path("research/mexc_nas100_multirail/results")
RAW=OUT/"raw"
OUT.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

SYMS=["NAS100_USDT","NAS100_USD1"]
START=pd.Timestamp("2026-06-25T14:00:00Z")
END=pd.Timestamp.now(tz="UTC").floor("min")

DISC_END=pd.Timestamp("2026-08-15T23:59:00Z")
OOS1_END=pd.Timestamp("2026-09-15T23:59:00Z")

TAKER_SIDE_BPS=8.0
MAKER_SIDE_BPS=6.0
ONELEG_TAKER_RT=16.0
PAIR_TAKER_RT=32.0
ONELEG_MAKER_RT=12.0
PAIR_MAKER_RT=24.0

H1_H2_TRIGGER_BPS=40.0
H1_H2_HOLD_PRIMARY=15
H1_H2_HOLD_DIAG=60
H3_H4_LEADER_BPS=20.0
H3_H4_RATIO=0.5
NEAR_ZERO_BPS=2.0
H3_H4_HOLD_PRIMARY=1
H3_H4_HOLD_DIAG=5

UA={"User-Agent":"CryptoLab-NAS100-MULTIRAIL-001/1.0"}

def req_json(url, params=None, tries=4, timeout=20):
    err=None
    for i in range(tries):
        try:
            r=requests.get(url, params=params, timeout=timeout, headers=UA)
            if r.status_code==200:
                j=r.json()
                if isinstance(j,dict) and j.get("success") is False:
                    raise RuntimeError(f"success=false code={j.get('code')} msg={j.get('message')}")
                return j, r.url
            err=f"HTTP {r.status_code}: {r.text[:300]}"
        except Exception as e:
            err=repr(e)
        time.sleep(0.5*(i+1))
    raise RuntimeError(f"GET failed {url} params={params}: {err}")

def ts_sec(x):
    return int(pd.Timestamp(x).timestamp())

def fetch_fut_klines(symbol, kind, start, end):
    if kind=="last": path=f"/kline/{symbol}"
    elif kind=="index": path=f"/kline/index_price/{symbol}"
    elif kind=="fair": path=f"/kline/fair_price/{symbol}"
    else: raise ValueError(kind)
    chunk=1900*60
    cur=ts_sec(start)
    stop=ts_sec(end)
    frames=[]
    urls=[]
    while cur<=stop:
        e=min(stop, cur+chunk-60)
        j,u=req_json(BASE_FUT+path,{"interval":"Min1","start":cur,"end":e})
        urls.append(u)
        d=j.get("data") or {}
        t=d.get("time") or []
        o=d.get("open") or []
        h=d.get("high") or []
        l=d.get("low") or []
        c=d.get("close") or []
        n=min(len(t),len(o),len(h),len(l),len(c))
        if n:
            fr=pd.DataFrame({
                "ts":[int(x) for x in t[:n]],
                f"{kind}_open":[float(x) for x in o[:n]],
                f"{kind}_high":[float(x) for x in h[:n]],
                f"{kind}_low":[float(x) for x in l[:n]],
                f"{kind}_close":[float(x) for x in c[:n]],
            })
            frames.append(fr)
        cur=e+60
        time.sleep(0.03)
    if not frames:
        return pd.DataFrame(), urls
    df=pd.concat(frames,ignore_index=True).drop_duplicates("ts").sort_values("ts")
    return df, urls

def fetch_spot_klines(symbol, start, end):
    cur=int(pd.Timestamp(start).timestamp()*1000)
    stop=int(pd.Timestamp(end).timestamp()*1000)
    frames=[]; urls=[]
    while cur<=stop:
        # 1000 x 1m bars
        e=min(stop,cur+999*60_000)
        j,u=req_json(BASE_SPOT+"/klines",{"symbol":symbol,"interval":"1m","startTime":cur,"endTime":e,"limit":1000})
        urls.append(u)
        if not isinstance(j,list):
            raise RuntimeError(f"Unexpected spot kline payload: {type(j)}")
        if j:
            rows=[]
            for x in j:
                if len(x)>=6:
                    rows.append({
                        "ts":int(x[0]//1000),
                        "fx_open":float(x[1]),
                        "fx_high":float(x[2]),
                        "fx_low":float(x[3]),
                        "fx_close":float(x[4]),
                        "fx_vol":float(x[5]),
                    })
            if rows: frames.append(pd.DataFrame(rows))
        cur=e+60_000
        time.sleep(0.03)
    if not frames:
        return pd.DataFrame(), urls
    df=pd.concat(frames,ignore_index=True).drop_duplicates("ts").sort_values("ts")
    return df, urls

def fetch_funding(symbol):
    # page_size 1000 is sufficient for overlap at 4h/8h settlement; fail closed if totalCount > 1000.
    j,u=req_json(BASE_FUT+"/funding_rate/history",{"symbol":symbol,"page_num":1,"page_size":1000})
    d=j.get("data") or {}
    total=int(d.get("totalCount") or 0)
    rows=d.get("resultList") or []
    fr=[]
    for x in rows:
        try:
            fr.append({"settleTime":int(x["settleTime"]),"fundingRate":float(x["fundingRate"]),"collectCycle":x.get("collectCycle")})
        except Exception:
            pass
    return pd.DataFrame(fr),u,total

def current_architecture():
    j,u=req_json(BASE_FUT+"/detail")
    data=j.get("data") or []
    keep={}
    fields=[
        "symbol","displayNameEn","contractSize","minLeverage","maxLeverage",
        "countryConfigContractMaxLeverage","priceScale","priceUnit","volUnit",
        "minVol","maxVol","takerFeeRate","makerFeeRate","maintenanceMarginRate",
        "initialMarginRate","indexOrigin","state","riskLimitType","maxNumOrders",
        "marketOrderMaxLevel","settleCoin","quoteCoin","baseCoin","futureType"
    ]
    for s in SYMS:
        row=next((x for x in data if x.get("symbol")==s),None)
        if row is None:
            keep[s]=None
        else:
            keep[s]={k:row.get(k) for k in fields}
    return keep,u

def split_label(ts):
    t=pd.to_datetime(ts,unit="s",utc=True)
    if t<=DISC_END: return "DISCOVERY"
    if t<=OOS1_END: return "OOS1"
    return "OOS2"

def bps_ret(exit_px,entry_px):
    return (exit_px/entry_px-1.0)*10000.0

def suppress_overlap(events, hold_min):
    if events.empty: return events
    out=[]; last_until=None
    for _,r in events.sort_values("ts").iterrows():
        if last_until is None or int(r["ts"])>=last_until:
            out.append(r)
            last_until=int(r["ts"])+hold_min*60
    return pd.DataFrame(out)

def simulate_pair(df, basis_col, hold_min, fee_bps):
    sig=df.loc[df[basis_col].abs()>=H1_H2_TRIGGER_BPS,["ts",basis_col]].copy()
    sig=suppress_overlap(sig,15)  # freeze anti-overlap uses primary holding period for triggers
    rows=[]
    byts=df.set_index("ts")
    for _,r in sig.iterrows():
        t=int(r["ts"]); s=1 if float(r[basis_col])>0 else -1
        ent=t+60; ex=ent+hold_min*60
        if ent not in byts.index or ex not in byts.index: continue
        a=byts.loc[ent]; z=byts.loc[ex]
        if isinstance(a,pd.DataFrame): a=a.iloc[0]
        if isinstance(z,pd.DataFrame): z=z.iloc[0]
        ru=bps_ret(float(z["usdt_last_close"]),float(a["usdt_last_open"]))
        rd=bps_ret(float(z["usd1_last_close"]),float(a["usd1_last_open"]))
        gross=s*(rd-ru)
        rows.append({
            "ts":t,"split":split_label(t),"signal_bps":float(r[basis_col]),
            "gross_bps":gross,"net_taker_bps":gross-fee_bps,
            "date":pd.to_datetime(t,unit="s",utc=True).date().isoformat()
        })
    return pd.DataFrame(rows)

def simulate_lead(df, leader, hold_min, fee_bps):
    # leader in {"USDT","USD1"}
    rows=[]
    byts=df.set_index("ts")
    tmp=df.copy()
    if leader=="USDT":
        lr=tmp["r_usdt_bps"]; lag=tmp["r_usd1norm_bps"]; trade="USD1"
    else:
        lr=tmp["r_usd1norm_bps"]; lag=tmp["r_usdt_bps"]; trade="USDT"
    same=(np.sign(lr)==np.sign(lag)) | (lag.abs()<=NEAR_ZERO_BPS)
    mask=(lr.abs()>=H3_H4_LEADER_BPS) & (lag.abs()<=H3_H4_RATIO*lr.abs()) & same
    sig=tmp.loc[mask,["ts"]].copy()
    sig=suppress_overlap(sig,1)
    for _,rr in sig.iterrows():
        t=int(rr["ts"]); ent=t+60; ex=ent+hold_min*60
        if ent not in byts.index or ex not in byts.index: continue
        base=byts.loc[t]; a=byts.loc[ent]; z=byts.loc[ex]
        if isinstance(base,pd.DataFrame): base=base.iloc[0]
        if isinstance(a,pd.DataFrame): a=a.iloc[0]
        if isinstance(z,pd.DataFrame): z=z.iloc[0]
        leader_ret=float(base["r_usdt_bps"] if leader=="USDT" else base["r_usd1norm_bps"])
        direction=1 if leader_ret>0 else -1
        if trade=="USD1":
            trade_ret=bps_ret(float(z["usd1_last_close"]),float(a["usd1_last_open"]))
        else:
            trade_ret=bps_ret(float(z["usdt_last_close"]),float(a["usdt_last_open"]))
        gross=direction*trade_ret
        rows.append({
            "ts":t,"split":split_label(t),"leader":leader,"trade":trade,
            "leader_return_bps":leader_ret,
            "lagger_return_bps":float(base["r_usd1norm_bps"] if leader=="USDT" else base["r_usdt_bps"]),
            "gross_bps":gross,"net_taker_bps":gross-fee_bps,
            "date":pd.to_datetime(t,unit="s",utc=True).date().isoformat()
        })
    return pd.DataFrame(rows)

def metric_rows(name,horizon,ev):
    rows=[]
    for split in ["DISCOVERY","OOS1","OOS2"]:
        g=ev[ev["split"]==split] if not ev.empty else pd.DataFrame()
        if g.empty:
            rows.append({"hypothesis":name,"horizon_min":horizon,"split":split,"n":0})
            continue
        gross=g["gross_bps"].astype(float); net=g["net_taker_bps"].astype(float)
        day=g.groupby("date")["gross_bps"].sum()
        total=float(gross.sum())
        if total>0 and len(day):
            concentration=float(day.clip(lower=0).max()/total) if total!=0 else np.nan
        else:
            concentration=np.nan
        rows.append({
            "hypothesis":name,"horizon_min":horizon,"split":split,"n":int(len(g)),
            "gross_mean_bps":float(gross.mean()),"gross_median_bps":float(gross.median()),
            "gross_total_bps":total,"net_mean_bps":float(net.mean()),
            "net_median_bps":float(net.median()),"net_total_bps":float(net.sum()),
            "win_rate_net":float((net>0).mean()),"max_single_positive_day_share":concentration
        })
    return rows

def eval_primary(name, metrics, required_n=20):
    m={r["split"]:r for r in metrics if r["hypothesis"]==name and r["horizon_min"] in [15,1]}
    if "OOS1" not in m or "OOS2" not in m: return "BLOCKED"
    a,b=m["OOS1"],m["OOS2"]
    n=int(a.get("n",0))+int(b.get("n",0))
    if int(a.get("n",0))==0 or int(b.get("n",0))==0:
        return "NO_EDGE"
    checks=[
        float(a.get("net_mean_bps",-1e9))>=5.0,
        float(b.get("net_mean_bps",-1e9))>=5.0,
        float(a.get("net_median_bps",-1e9))>=0.0,
        float(b.get("net_median_bps",-1e9))>=0.0,
        n>=required_n,
    ]
    ca=a.get("max_single_positive_day_share",np.nan)
    cb=b.get("max_single_positive_day_share",np.nan)
    if np.isfinite(ca): checks.append(float(ca)<=0.35)
    if np.isfinite(cb): checks.append(float(cb)<=0.35)
    return "SURVIVES_CANDLE_EXECUTION_PENDING" if all(checks) else "NO_EDGE"

manifest={"created_at_utc":datetime.now(timezone.utc).isoformat(),"start":START.isoformat(),"end":END.isoformat(),"sources":{}}

arch,detail_url=current_architecture()
manifest["sources"]["contract_detail"]=detail_url
(OUT/"architecture.json").write_text(json.dumps(arch,indent=2),encoding="utf-8")
if any(arch.get(s) is None for s in SYMS):
    summary={"study":"MEXC-NAS100-MULTIRAIL-001","verdict":"BLOCKED","reason":"one or both futures symbols absent from contract/detail","architecture":arch}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2)); raise SystemExit(0)

frames={}
for sym in SYMS:
    parts=[]
    manifest["sources"][sym]={}
    for kind in ["last","index","fair"]:
        df,urls=fetch_fut_klines(sym,kind,START,END)
        manifest["sources"][sym][kind]={"rows":int(len(df)),"requests":len(urls),"first_url":urls[0] if urls else None,"last_url":urls[-1] if urls else None}
        parts.append(df)
    x=parts[0]
    for p in parts[1:]: x=x.merge(p,on="ts",how="outer")
    x=x.sort_values("ts").drop_duplicates("ts")
    frames[sym]=x
    x.to_csv(RAW/f"{sym}_1m.csv.gz",index=False,compression="gzip")
    fund,u,total=fetch_funding(sym)
    manifest["sources"][sym]["funding"]={"rows":int(len(fund)),"totalCount":total,"url":u}
    fund.to_csv(RAW/f"{sym}_funding.csv.gz",index=False,compression="gzip")

fx,fxurls=fetch_spot_klines("USD1USDT",START,END)
manifest["sources"]["USD1USDT"]={"rows":int(len(fx)),"requests":len(fxurls),"first_url":fxurls[0] if fxurls else None,"last_url":fxurls[-1] if fxurls else None}
fx.to_csv(RAW/"USD1USDT_1m.csv.gz",index=False,compression="gzip")

u=frames["NAS100_USDT"].rename(columns={c:"usdt_"+c for c in frames["NAS100_USDT"].columns if c!="ts"})
d=frames["NAS100_USD1"].rename(columns={c:"usd1_"+c for c in frames["NAS100_USD1"].columns if c!="ts"})
m_raw=u.merge(d,on="ts",how="inner").sort_values("ts").reset_index(drop=True)
m_raw["utc"]=pd.to_datetime(m_raw["ts"],unit="s",utc=True)
m_raw["split"]=m_raw["ts"].map(split_label)

# Technical coverage QC: compare rail intersection to actual futures bars, not wall-clock calendar.
usdt_n=int(frames["NAS100_USDT"]["ts"].nunique())
usd1_n=int(frames["NAS100_USD1"]["ts"].nunique())
common_n=int(m_raw["ts"].nunique())
futures_common_ratio=common_n/min(usdt_n,usd1_n) if min(usdt_n,usd1_n)>0 else 0.0

# Strict known-at-T FX normalization: latest USD1USDT print no older than 5 minutes.
fx_asof=fx[["ts","fx_open","fx_close"]].copy().rename(columns={"ts":"fx_ts"}).sort_values("fx_ts")
m_fx=pd.merge_asof(
    m_raw.sort_values("ts"), fx_asof,
    left_on="ts", right_on="fx_ts",
    direction="backward", tolerance=300
)
m_fx["fx_age_sec"]=m_fx["ts"]-m_fx["fx_ts"]
m_fx_valid=m_fx[m_fx["fx_close"].notna()].copy()
fx_valid_n=int(len(m_fx_valid))
fx_valid_ratio=fx_valid_n/common_n if common_n else 0.0

coverage={
    "calendar_expected_minutes":int((END-START).total_seconds()/60)+1,
    "usdt_futures_minutes":usdt_n,
    "usd1_futures_minutes":usd1_n,
    "common_futures_minutes":common_n,
    "futures_common_ratio":futures_common_ratio,
    "usd1usdt_print_minutes":int(fx["ts"].nunique()),
    "fx_asof_valid_minutes_5m":fx_valid_n,
    "fx_valid_ratio_of_common_futures":fx_valid_ratio,
}
manifest["coverage"]=coverage

if futures_common_ratio<0.95:
    summary={"study":"MEXC-NAS100-MULTIRAIL-001","verdict":"BLOCKED","reason":"futures timestamp intersection below 95%","coverage":coverage,"architecture":arch}
    (OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(summary,indent=2)); raise SystemExit(0)

# H1 raw basis does not require USD1USDT.
m_raw["basis_raw_bps"]=(m_raw["usdt_last_close"]/m_raw["usd1_last_close"]-1.0)*10000.0
m_raw["index_basis_raw_bps"]=(m_raw["usdt_index_close"]/m_raw["usd1_index_close"]-1.0)*10000.0
m_raw["fair_basis_raw_bps"]=(m_raw["usdt_fair_close"]/m_raw["usd1_fair_close"]-1.0)*10000.0
m_raw.to_csv(RAW/"aligned_futures_1m.csv.gz",index=False,compression="gzip")

events={}
events["H1_raw_pair_15m"]=simulate_pair(m_raw,"basis_raw_bps",15,PAIR_TAKER_RT)
events["H1_raw_pair_60m"]=simulate_pair(m_raw,"basis_raw_bps",60,PAIR_TAKER_RT)

metrics=[]
metrics += metric_rows("H1_raw_pair",15,events["H1_raw_pair_15m"])
metrics += metric_rows("H1_raw_pair",60,events["H1_raw_pair_60m"])

fx_hypotheses_enabled = fx_valid_ratio>=0.80
if fx_hypotheses_enabled:
    m=m_fx_valid.copy()
    m["usd1_last_close_usdt"]=m["usd1_last_close"]*m["fx_close"]
    m["usd1_last_open_usdt"]=m["usd1_last_open"]*m["fx_open"]
    m["basis_fx_bps"]=(m["usdt_last_close"]/m["usd1_last_close_usdt"]-1.0)*10000.0

    # Exact previous-minute returns only; no return is computed across session/data gaps.
    prev=m[["ts","usdt_last_close","usd1_last_close_usdt"]].copy()
    prev["ts"]=prev["ts"]+60
    prev=prev.rename(columns={"usdt_last_close":"prev_usdt_close","usd1_last_close_usdt":"prev_usd1norm_close"})
    m=m.merge(prev,on="ts",how="left")
    m["r_usdt_bps"]=(m["usdt_last_close"]/m["prev_usdt_close"]-1.0)*10000.0
    m["r_usd1norm_bps"]=(m["usd1_last_close_usdt"]/m["prev_usd1norm_close"]-1.0)*10000.0
    m.to_csv(RAW/"aligned_fx_normalized_1m.csv.gz",index=False,compression="gzip")

    events["H2_fx_pair_15m"]=simulate_pair(m,"basis_fx_bps",15,PAIR_TAKER_RT)
    events["H2_fx_pair_60m"]=simulate_pair(m,"basis_fx_bps",60,PAIR_TAKER_RT)
    events["H3_USDT_leads_1m"]=simulate_lead(m,"USDT",1,ONELEG_TAKER_RT)
    events["H3_USDT_leads_5m"]=simulate_lead(m,"USDT",5,ONELEG_TAKER_RT)
    events["H4_USD1_leads_1m"]=simulate_lead(m,"USD1",1,ONELEG_TAKER_RT)
    events["H4_USD1_leads_5m"]=simulate_lead(m,"USD1",5,ONELEG_TAKER_RT)

    metrics += metric_rows("H2_fx_pair",15,events["H2_fx_pair_15m"])
    metrics += metric_rows("H2_fx_pair",60,events["H2_fx_pair_60m"])
    metrics += metric_rows("H3_USDT_leads",1,events["H3_USDT_leads_1m"])
    metrics += metric_rows("H3_USDT_leads",5,events["H3_USDT_leads_5m"])
    metrics += metric_rows("H4_USD1_leads",1,events["H4_USD1_leads_1m"])
    metrics += metric_rows("H4_USD1_leads",5,events["H4_USD1_leads_5m"])

for n,e in events.items():
    e.to_csv(RAW/f"{n}.csv.gz",index=False,compression="gzip")

mdf=pd.DataFrame(metrics)
mdf.to_csv(OUT/"hypothesis_metrics.csv",index=False)

desc={}
for col in ["basis_raw_bps","index_basis_raw_bps","fair_basis_raw_bps"]:
    s=m_raw[col].dropna().abs()
    desc[col]={
        "n":int(len(s)),"median_abs_bps":float(s.median()),"p95_abs_bps":float(s.quantile(.95)),
        "p99_abs_bps":float(s.quantile(.99)),"max_abs_bps":float(s.max()),
        "count_ge_20":int((s>=20).sum()),"count_ge_40":int((s>=40).sum())
    }
if fx_hypotheses_enabled:
    s=m["basis_fx_bps"].dropna().abs()
    desc["basis_fx_bps"]={
        "n":int(len(s)),"median_abs_bps":float(s.median()),"p95_abs_bps":float(s.quantile(.95)),
        "p99_abs_bps":float(s.quantile(.99)),"max_abs_bps":float(s.max()),
        "count_ge_20":int((s>=20).sum()),"count_ge_40":int((s>=40).sum())
    }

verdicts={"H1_raw_pair":eval_primary("H1_raw_pair",metrics)}
if fx_hypotheses_enabled:
    verdicts.update({
        "H2_fx_pair":eval_primary("H2_fx_pair",metrics),
        "H3_USDT_leads":eval_primary("H3_USDT_leads",metrics),
        "H4_USD1_leads":eval_primary("H4_USD1_leads",metrics),
    })
else:
    verdicts.update({
        "H2_fx_pair":"BLOCKED_FX_COVERAGE",
        "H3_USDT_leads":"BLOCKED_FX_COVERAGE",
        "H4_USD1_leads":"BLOCKED_FX_COVERAGE",
    })

if any(v=="SURVIVES_CANDLE_EXECUTION_PENDING" for v in verdicts.values()):
    global_verdict="SURVIVES_CANDLE_EXECUTION_PENDING"
elif all(v=="NO_EDGE" for v in verdicts.values()):
    global_verdict="NO_EDGE"
elif verdicts["H1_raw_pair"]=="NO_EDGE" and not fx_hypotheses_enabled:
    global_verdict="PARTIAL_NO_EDGE_H1_NORMALIZED_HYPOTHESES_BLOCKED"
elif any(v.startswith("BLOCKED") for v in verdicts.values()):
    global_verdict="BLOCKED"
else:
    global_verdict="NO_EDGE"

summary={
    "study":"MEXC-NAS100-MULTIRAIL-001",
    "verdict":global_verdict,
    "hypothesis_verdicts":verdicts,
    "coverage":coverage,
    "costs_bps":{
        "one_leg_taker_round_trip":ONELEG_TAKER_RT,
        "pair_taker_round_trip":PAIR_TAKER_RT,
        "one_leg_maker_fee_floor":ONELEG_MAKER_RT,
        "pair_maker_fee_floor":PAIR_MAKER_RT
    },
    "thresholds":{
        "pair_basis_trigger_bps":H1_H2_TRIGGER_BPS,
        "lead_return_bps":H3_H4_LEADER_BPS,
        "lagger_max_fraction_of_leader":H3_H4_RATIO,
        "near_zero_bps":NEAR_ZERO_BPS,
        "fx_max_staleness_sec":300,
        "fx_required_coverage_ratio":0.80
    },
    "basis_descriptives":desc,
    "architecture":arch,
    "important_limit":"1m candles are an optimistic screening layer, not executable L1/L2 fills. SURVIVES requires a new preregistered forward microstructure test."
}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8")
(OUT/"manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")

print("=== NAS100 MULTIRAIL SUMMARY ===")
print(json.dumps(summary,indent=2))
print("\n=== METRICS ===")
print(mdf.to_string(index=False))

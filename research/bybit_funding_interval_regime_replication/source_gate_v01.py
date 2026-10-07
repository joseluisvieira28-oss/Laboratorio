#!/usr/bin/env python3
from __future__ import annotations
import json, math, re, statistics, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import requests

LAB="BYBIT-FUNDING-INTERVAL-REGIME-REPLICATION-001"
START=datetime(2023,1,1,tzinfo=timezone.utc)
END=datetime(2025,12,31,23,59,59,tzinfo=timezone.utc)
START_MS=int(START.timestamp()*1000)
END_MS=int(END.timestamp()*1000)
ANN="https://api.bybit.com/v5/announcements/index"
FUND="https://api.bybit.com/v5/market/funding/history"
OUT=Path("bfirr_v01_source_gate_report.json")
SESSION=requests.Session()
SESSION.headers.update({"User-Agent":"Mozilla/5.0 CryptoLab-BFIRR/0.1","Accept":"application/json"})
CANON=(1,2,4,8,12,24)

def req(url,params,attempts=7):
    last=None
    for i in range(attempts):
        try:
            r=SESSION.get(url,params=params,timeout=40)
            if r.status_code==429:
                wait=min(45,2**(i+1)); print(f"RATE_LIMIT wait={wait}s"); time.sleep(wait); last=RuntimeError("429"); continue
            if r.status_code>=500:
                time.sleep(min(20,2**i)); last=RuntimeError(f"http_{r.status_code}"); continue
            r.raise_for_status()
            j=r.json()
            if int(j.get("retCode",0))!=0:
                raise RuntimeError(f"retCode={j.get('retCode')} retMsg={j.get('retMsg')}")
            return j
        except Exception as e:
            last=e
            if i+1<attempts: time.sleep(min(20,2**i))
    raise RuntimeError(str(last))

def ts_of(a):
    for k in ("publishTime","dateTimestamp","startDateTimestamp","startDataTimestamp"):
        v=a.get(k)
        if isinstance(v,(int,float)) and v>0: return int(v)
        if isinstance(v,str) and v.isdigit(): return int(v)
    return None

def enumerate_announcements():
    allrows=[]; seen=set(); crossed=False; pages=[]
    for page in range(1,401):
        j=req(ANN,{"locale":"en-US","page":page,"limit":20})
        result=j.get("result") or {}
        rows=result.get("list") or []
        if not rows:
            pages.append({"page":page,"count":0})
            break
        pts=[ts_of(x) for x in rows if ts_of(x)]
        pages.append({"page":page,"count":len(rows),"min_ts":min(pts) if pts else None,"max_ts":max(pts) if pts else None})
        for a in rows:
            u=a.get("url") or ""
            key=u or (a.get("title"),ts_of(a))
            if key in seen: continue
            seen.add(key); allrows.append(a)
        if pts and min(pts)<START_MS:
            crossed=True; break
        time.sleep(0.10)
    return allrows,pages,crossed

def candidate(a):
    title=(a.get("title") or "")
    desc=(a.get("description") or "")
    txt=(title+" "+desc).lower()
    return (
        ("funding rate interval" in txt or "funding interval" in txt or "funding rate intervals" in txt)
        and ("adjust" in txt or "change" in txt or "changes" in txt)
        and "new listing" not in txt
        and "launch" not in txt
        and "delist" not in txt
    )

def symbols_from(a):
    txt=((a.get("title") or "")+" "+(a.get("description") or "")).upper()
    return sorted(set(re.findall(r"\b([A-Z0-9]{2,30}USDT)\b",txt)))

def funding_timestamps(symbol,t0):
    span=10*24*60*60*1000
    j=req(FUND,{
        "category":"linear","symbol":symbol,
        "startTime":t0-span,"endTime":t0+span,"limit":200
    })
    rows=(j.get("result") or {}).get("list") or []
    # SCIENTIFIC SAFETY: fundingRate field is intentionally never read, stored, logged or compared.
    ts=sorted({int(x["fundingRateTimestamp"]) for x in rows if str(x.get("fundingRateTimestamp","")).isdigit()})
    return ts

def canon_gap(h):
    best=min(CANON,key=lambda x:abs(x-h))
    return best if abs(best-h)<=0.10 else None

def infer_interval(ts,t0,side):
    if side=="pre":
        z=[x for x in ts if x<t0]
        if len(z)<4: return None,[],False
        gaps=[canon_gap((b-a)/3600000) for a,b in zip(z[-4:-1],z[-3:])]
    else:
        z=[x for x in ts if x>t0]
        if len(z)<4: return None,[],False
        gaps=[canon_gap((b-a)/3600000) for a,b in zip(z[:3],z[1:4])]
    if any(g is None for g in gaps): return None,gaps,False
    c=Counter(gaps)
    mode,n=c.most_common(1)[0]
    return mode,gaps,n>=2

def main():
    rows,pages,crossed=enumerate_announcements()
    inwin=[a for a in rows if ts_of(a) and START_MS<=ts_of(a)<=END_MS]
    cand=[a for a in inwin if candidate(a)]
    print("ANNOUNCEMENTS_IN_WINDOW="+str(len(inwin)))
    print("CANDIDATES="+str(len(cand)))
    print("CROSSED_PRE2023="+str(crossed))

    inspected=[]; eligible=[]
    for i,a in enumerate(sorted(cand,key=ts_of)):
        t0=ts_of(a); syms=symbols_from(a)
        title=a.get("title") or ""; url=a.get("url") or ""
        rec={"title":title,"url":url,"publish_ms":t0,"symbols":syms,"asset_results":[]}
        for s in syms:
            try:
                ts=funding_timestamps(s,t0)
                old,pre_gaps,pre_stable=infer_interval(ts,t0,"pre")
                new,post_gaps,post_stable=infer_interval(ts,t0,"post")
                ok=bool(old in CANON and new in CANON and pre_stable and post_stable and new<old)
                ar={"symbol":s,"pre_gaps_hours":pre_gaps,"post_gaps_hours":post_gaps,
                    "old_interval_hours":old,"new_interval_hours":new,
                    "pre_stable":pre_stable,"post_stable":post_stable,"eligible":ok}
                rec["asset_results"].append(ar)
                if ok:
                    eligible.append({
                        "announcement_url":url,"official_title":title,"publish_ms":t0,
                        "symbol":s,"old_interval_hours":old,"new_interval_hours":new,
                        "funding_timestamp_count":len(ts)
                    })
            except Exception as e:
                rec["asset_results"].append({"symbol":s,"eligible":False,"error":f"{type(e).__name__}:{e}"})
            time.sleep(0.08)
        inspected.append(rec)
        print(f"CANDIDATE_PROGRESS={i+1}/{len(cand)} symbols={len(syms)} eligible={sum(1 for x in rec['asset_results'] if x.get('eligible'))} title={title[:90]}")

    dd={}
    for e in eligible:
        dd[(e["announcement_url"],e["publish_ms"],e["symbol"],e["old_interval_hours"],e["new_interval_hours"])]=e
    eligible=list(dd.values())
    clusters={}
    for e in eligible:
        k=f"{e['announcement_url']}@{e['publish_ms']}"
        clusters.setdefault(k,[]).append(e)
    assets=sorted({e["symbol"] for e in eligible})
    years=sorted({datetime.fromtimestamp(e["publish_ms"]/1000,tz=timezone.utc).year for e in eligible})
    n=len(eligible)
    maxcl=max((len(v) for v in clusters.values()),default=0)
    conc=maxcl/n if n else 1.0
    gates={
        "clusters_ge_12":len(clusters)>=12,
        "asset_events_ge_20":n>=20,
        "unique_contracts_ge_8":len(assets)>=8,
        "years_ge_2":len(years)>=2,
        "max_cluster_le_35pct":conc<=0.35,
    }
    if crossed and all(gates.values()): verdict="EXTERNAL_SOURCE_PASS"
    elif crossed: verdict="EXTERNAL_INSUFFICIENT_SAMPLE"
    else: verdict="EXTERNAL_SOURCE_BLOCKED"

    report={
        "family":LAB,"verdict":verdict,"calendar":"2023-2025","outcome_access":"NONE",
        "announcement_pages":pages,"archive_crossed_pre2023":crossed,
        "announcements_in_window":len(inwin),"candidate_announcements":len(cand),
        "eligible_asset_events":n,"independent_clusters":len(clusters),"unique_contracts":len(assets),
        "years":years,"max_cluster_concentration":conc,"sample_gates":gates,
        "eligible_events":sorted(eligible,key=lambda e:(e["publish_ms"],e["symbol"])),
        "inspected_candidates":inspected,
        "safety":{
            "premium_values_opened":False,
            "funding_rate_values_read_or_used":False,
            "price_returns_opened":False,
            "pnl_opened":False,
            "authenticated_api":False,
            "mutation":False
        }
    }
    OUT.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("BFIRR_SOURCE_RESULT="+verdict)
    print("ELIGIBLE_ASSET_EVENTS="+str(n))
    print("INDEPENDENT_CLUSTERS="+str(len(clusters)))
    print("UNIQUE_CONTRACTS="+str(len(assets)))
    print("YEARS="+json.dumps(years))
    print("MAX_CLUSTER_CONCENTRATION="+str(conc))
    print("SAMPLE_GATES="+json.dumps(gates,sort_keys=True))
    print("SAFETY: no premium values; fundingRate field never read/used")
    return 0

if __name__=="__main__":
    raise SystemExit(main())

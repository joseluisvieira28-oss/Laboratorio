#!/usr/bin/env python3
import csv, json, math, os, time
from collections import deque
from datetime import datetime, timezone
import requests
from scipy.stats import binomtest

BASE="https://contract.mexc.com"
SYMBOL="MUSTOCK_USDT"
CELLS=[
 {"h":10,"th":1.0},
 {"h":10,"th":1.5},
 {"h":10,"th":2.0},
 {"h":30,"th":1.5},
 {"h":30,"th":2.0},
]
P0=1/1.8
Z95=1.959963984540054
STEP=300
ROLL_SEC=24*3600
ROLL_MAX=288
ROLL_MIN=240
HOLD_START=int(datetime(2026,9,1,tzinfo=timezone.utc).timestamp())
HOLD_END=int(datetime(2026,10,1,tzinfo=timezone.utc).timestamp())
FETCH_START=HOLD_START-2*24*3600
FETCH_END_RAW=HOLD_END-2*STEP

def fetch_json(url,params,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,timeout=30)
            r.raise_for_status()
            j=r.json()
            if isinstance(j,dict) and j.get("success") is True: return j
            last=RuntimeError(f"non-success payload: {j}")
        except Exception as e:
            last=e
        time.sleep(0.5*(i+1))
    raise last

def fetch_series(kind):
    route="index_price" if kind=="index" else "fair_price"
    url=f"{BASE}/api/v1/contract/kline/{route}/{SYMBOL}"
    out={}; reqs=0; t=FETCH_START-STEP; chunk=5*24*3600
    while t<=FETCH_END_RAW:
        e=min(t+chunk,FETCH_END_RAW)
        j=fetch_json(url,{"interval":"Min5","start":t,"end":e}); reqs+=1
        d=j.get("data") or {}
        for s,p in zip(d.get("time") or [],d.get("close") or []):
            try: s=int(s); p=float(p)
            except Exception: continue
            if s>=HOLD_END:
                raise RuntimeError("October outcome boundary violation")
            mapped=s+STEP
            if FETCH_START<=mapped<HOLD_END:
                out[mapped]=p
        t=e+STEP
        time.sleep(0.08)
    return out,reqs

def build_z(index,fair):
    premium={}
    for t in sorted(set(index).intersection(fair)):
        ip=index[t]; fp=fair[t]
        if ip and math.isfinite(ip) and math.isfinite(fp):
            premium[t]=(fp-ip)/ip*10000.0
    z={}; q=deque(); s=0.0; ss=0.0
    for t in sorted(premium):
        x=premium[t]; q.append((t,x)); s+=x; ss+=x*x
        cutoff=t-ROLL_SEC+STEP
        while q and q[0][0]<cutoff:
            _,old=q.popleft(); s-=old; ss-=old*old
        while len(q)>ROLL_MAX:
            _,old=q.popleft(); s-=old; ss-=old*old
        n=len(q)
        if n<ROLL_MIN: continue
        mean=s/n
        var=(ss-n*mean*mean)/(n-1) if n>1 else 0.0
        if var<=0 or not math.isfinite(var): continue
        z[t]=(x-mean)/math.sqrt(var)
    return premium,z

def aligned(h):
    sec=h*60
    t=((HOLD_START+sec-1)//sec)*sec
    while t<HOLD_END:
        yield t
        t+=sec

def wilson_lower(w,l):
    n=w+l
    if not n: return None
    p=w/n; z2=Z95*Z95
    return (p+z2/(2*n)-Z95*math.sqrt((p*(1-p)+z2/(4*n))/n))/(1+z2/n)

def score(index,z,h,th):
    w=l=ties=missing=no_signal=0
    for t in aligned(h):
        after=t+h*60
        if after>=HOLD_END: continue
        if t not in index or after not in index or t not in z:
            missing+=1; continue
        zz=z[t]
        if abs(zz)<th or zz==0:
            no_signal+=1; continue
        sig=1 if zz>0 else -1
        fut=index[after]-index[t]
        if fut==0: ties+=1
        elif (fut>0 and sig>0) or (fut<0 and sig<0): w+=1
        else: l+=1
    n=w+l
    acc=w/n if n else None
    p=float(binomtest(w,n,P0,alternative="greater").pvalue) if n else None
    total=w+l+ties
    return {
      "horizon_min":h,"z_threshold":th,"mode":"FOLLOW_PREMIUM",
      "wins":w,"losses":l,"ties":ties,"missing":missing,"no_signal":no_signal,
      "non_ties":n,"accuracy":acc,"wilson95_lower":wilson_lower(w,l),
      "raw_p":p,
      "ev80":((w*0.8-l)/total) if total else None,
      "ev70":((w*0.7-l)/total) if total else None,
      "required_payout_for_ev0":(l/w) if w else None,
    }

def holm(rows):
    indexed=sorted([(r["raw_p"],i) for i,r in enumerate(rows) if r["raw_p"] is not None])
    m=len(indexed); running=0.0
    for rank,(p,i) in enumerate(indexed,1):
        adj=min(1.0,(m-rank+1)*p)
        running=max(running,adj)
        rows[i]["holm_adjusted_p"]=running
        rows[i]["holm_rank"]=rank
    for r in rows:
        if "holm_adjusted_p" not in r:
            r["holm_adjusted_p"]=None; r["holm_rank"]=None
        r["basic_effect_pass"]=bool(
            r["accuracy"] is not None and r["accuracy"]>P0
            and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
            and r["ev80"] is not None and r["ev80"]>0
        )
        r["final_survivor"]=bool(
            r["basic_effect_pass"]
            and r["holm_adjusted_p"] is not None
            and r["holm_adjusted_p"]<=0.05
        )
    return rows

def main():
    outdir="artifacts/mexc_event_futures"; os.makedirs(outdir,exist_ok=True)
    idx,ri=fetch_series("index")
    fair,rf=fetch_series("fair")
    premium,z=build_z(idx,fair)
    rows=holm([score(idx,z,c["h"],c["th"]) for c in CELLS])
    survivors=[r for r in rows if r["final_survivor"]]
    report={
      "lab":"MEXC_EVENT_FUTURES_PREMIUM_BASIS_V1.2_FINAL_HOLDOUT",
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "symbol":SYMBOL,
      "holdout_start_utc":"2026-09-01T00:00:00Z",
      "holdout_end_exclusive_utc":"2026-10-01T00:00:00Z",
      "october_outcomes_accessed":False,
      "index_requests":ri,"fair_requests":rf,
      "index_rows":len(idx),"fair_rows":len(fair),
      "premium_rows":len(premium),"z_rows":len(z),
      "reference_payout":0.80,"reference_break_even_accuracy":P0,
      "multiplicity":"HOLM_BONFERRONI_FWER_ALPHA_0.05",
      "cells":rows,
      "survivors":survivors,
      "survivor_count":len(survivors),
      "verdict":"FINAL_HOLDOUT_SURVIVOR" if survivors else "NO_SURVIVOR_FINAL_HOLDOUT",
      "exact_event_futures_settlement":"NOT_PROVEN",
      "historical_payout_series":"NOT_AVAILABLE",
      "promotion_status":"PROXY_HOLDOUT_CANDIDATE_ONLY" if survivors else "NO_PROMOTION",
    }
    jp=f"{outdir}/premium_basis_v12_holdout.json"
    cp=f"{outdir}/premium_basis_v12_holdout.csv"
    with open(jp,"w",encoding="utf-8") as f: json.dump(report,f,indent=2,sort_keys=True)
    fields=list(rows[0].keys())
    with open(cp,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)
    print(json.dumps({
      "verdict":report["verdict"],
      "survivor_count":len(survivors),
      "cells":rows,
      "october_outcomes_accessed":False,
      "exact_event_futures_settlement":"NOT_PROVEN"
    },indent=2,sort_keys=True))
    print("WROTE",jp); print("WROTE",cp)

if __name__=="__main__":
    main()

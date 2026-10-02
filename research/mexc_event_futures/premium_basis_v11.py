#!/usr/bin/env python3
"""
MEXC Event Futures Lab V1.1 — fair-price / index premium directional study.

Research only. Public MEXC standard-futures sources.
No authentication, no orders, no September-2026 holdout.
"""
import csv, json, math, os, time
from collections import deque
from datetime import datetime, timezone

import requests
from scipy.stats import binomtest

BASE="https://contract.mexc.com"
SYMBOLS={
    "BTCUSDT":"BTC_USDT",
    "ETHUSDT":"ETH_USDT",
    "NVDAUSDT":"NVIDIA_USDT",
    "MUUSDT":"MUSTOCK_USDT",
    "SPCXUSDT":"SPCXSTOCK_USDT",
}
HORIZONS={
    "BTCUSDT":[10,30,60,1440],
    "ETHUSDT":[10,30,60,1440],
    "NVDAUSDT":[10,30,60,240],
    "MUUSDT":[10,30,60,240],
    "SPCXUSDT":[10,30,60,240],
}
THRESHOLDS=[1.0,1.5,2.0]
MODES=["FOLLOW_PREMIUM","FADE_PREMIUM"]
MIN_N={10:120,30:100,60:80,240:40,1440:20}
P0=1/1.8
BH_Q=0.05
Z95=1.959963984540054
STEP=300
ROLL_SEC=24*3600
ROLL_MAX=288
ROLL_MIN=240

DISC_START=int(datetime(2026,4,1,tzinfo=timezone.utc).timestamp())
DISC_END=int(datetime(2026,8,1,tzinfo=timezone.utc).timestamp())
OOS_START=DISC_END
OOS_END=int(datetime(2026,9,1,tzinfo=timezone.utc).timestamp())
FETCH_START=DISC_START-2*24*3600
FETCH_END_RAW=OOS_END-2*STEP

def fetch_json(url,params,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,timeout=30)
            r.raise_for_status()
            j=r.json()
            if isinstance(j,dict) and j.get("success") is True:
                return j
            last=RuntimeError(f"non-success payload: {j}")
        except Exception as e:
            last=e
        time.sleep(0.5*(i+1))
    raise last

def fetch_series(symbol,kind):
    if kind=="index":
        url=f"{BASE}/api/v1/contract/kline/index_price/{symbol}"
    elif kind=="fair":
        url=f"{BASE}/api/v1/contract/kline/fair_price/{symbol}"
    else:
        raise ValueError(kind)
    chunk=5*24*3600
    t=FETCH_START-STEP
    out={}
    reqs=0
    while t<=FETCH_END_RAW:
        e=min(t+chunk,FETCH_END_RAW)
        j=fetch_json(url,{"interval":"Min5","start":t,"end":e})
        reqs+=1
        d=j.get("data") or {}
        for s,p in zip(d.get("time") or [],d.get("close") or []):
            try:
                s=int(s); p=float(p)
            except Exception:
                continue
            if s>=OOS_END:
                raise RuntimeError(f"holdout-boundary violation in {kind}")
            mapped=s+STEP
            if FETCH_START<=mapped<OOS_END:
                out[mapped]=p
        t=e+STEP
        time.sleep(0.08)
    return out,reqs

def coverage(p,start,end):
    a=[t for t in p if start<=t<end]
    return {"rows":len(a),"first":min(a) if a else None,"last":max(a) if a else None}

def build_premium_and_z(index,fair):
    premium={}
    common=sorted(set(index).intersection(fair))
    for t in common:
        ip=index[t]
        fp=fair[t]
        if ip and math.isfinite(ip) and math.isfinite(fp):
            premium[t]=(fp-ip)/ip*10000.0

    z={}
    q=deque()
    s=0.0
    ss=0.0
    for t in sorted(premium):
        x=premium[t]
        q.append((t,x)); s+=x; ss+=x*x
        cutoff=t-ROLL_SEC+STEP
        while q and q[0][0]<cutoff:
            _,old=q.popleft(); s-=old; ss-=old*old
        while len(q)>ROLL_MAX:
            _,old=q.popleft(); s-=old; ss-=old*old
        n=len(q)
        if n<ROLL_MIN:
            continue
        mean=s/n
        var=(ss-n*mean*mean)/(n-1) if n>1 else 0.0
        if var<=0 or not math.isfinite(var):
            continue
        sd=math.sqrt(max(var,0.0))
        z[t]=(x-mean)/sd
    return premium,z

def aligned(start,end,h):
    sec=h*60
    t=((start+sec-1)//sec)*sec
    while t<end:
        yield t
        t+=sec

def wilson_lower(w,l):
    n=w+l
    if not n: return None
    p=w/n; z2=Z95*Z95
    return (p+z2/(2*n)-Z95*math.sqrt((p*(1-p)+z2/(4*n))/n))/(1+z2/n)

def exact_p(w,l):
    n=w+l
    return None if not n else float(binomtest(w,n,P0,alternative="greater").pvalue)

def score(index,z,h,threshold,mode,start,end):
    w=l=ties=missing=no_signal=0
    thirds=[[0,0,0] for _ in range(3)]
    span=end-start
    for t in aligned(start,end,h):
        after=t+h*60
        if after>=end:
            continue
        if t not in index or after not in index or t not in z:
            missing+=1; continue
        zz=z[t]
        if abs(zz)<threshold or zz==0:
            no_signal+=1; continue
        sig=1 if zz>0 else -1
        if mode=="FADE_PREMIUM":
            sig=-sig
        fut=index[after]-index[t]
        third=min(2,max(0,int(3*(t-start)/max(1,span))))
        if fut==0:
            ties+=1; thirds[third][2]+=1
        elif (fut>0 and sig>0) or (fut<0 and sig<0):
            w+=1; thirds[third][0]+=1
        else:
            l+=1; thirds[third][1]+=1

    n=w+l
    acc=w/n if n else None
    thirds_acc=[a/(a+b) if a+b else None for a,b,_ in thirds]
    total=w+l+ties
    ev80=((w*0.80-l)/total) if total else None
    ev70=((w*0.70-l)/total) if total else None
    req=(l/w) if w else None
    return {
        "wins":w,"losses":l,"ties":ties,"missing":missing,"no_signal":no_signal,
        "non_ties":n,"accuracy":acc,"wilson95_lower":wilson_lower(w,l),
        "p_value_vs_be80":exact_p(w,l),"third_accuracies":thirds_acc,
        "ev80":ev80,"ev70":ev70,"required_payout_for_ev0":req,
        "entry_stride_min":h,
    }

def eligible(r,h):
    return (
        r["non_ties"]>=MIN_N[h]
        and r["accuracy"] is not None and r["accuracy"]>P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
        and all(x is not None and x>0.50 for x in r["third_accuracies"])
        and r["p_value_vs_be80"] is not None
    )

def bh_select(cells):
    e=[x for x in cells if x["eligible"]]
    e.sort(key=lambda x:x["discovery"]["p_value_vs_be80"])
    m=len(e); cutoff=None
    for rank,x in enumerate(e,1):
        if x["discovery"]["p_value_vs_be80"] <= rank/m*BH_Q:
            cutoff=x["discovery"]["p_value_vs_be80"]
    return ([] if cutoff is None else [x for x in e if x["discovery"]["p_value_vs_be80"]<=cutoff]),m,cutoff

def oos_pass(r):
    return (
        r["non_ties"]>0
        and r["accuracy"] is not None and r["accuracy"]>P0
        and r["wilson95_lower"] is not None and r["wilson95_lower"]>0.50
        and r["p_value_vs_be80"] is not None and r["p_value_vs_be80"]<0.05
        and r["ev80"] is not None and r["ev80"]>0
    )

def flat(stage,asset,h,th,mode,r,gate):
    return {
        "stage":stage,"asset":asset,"horizon_min":h,"z_threshold":th,"mode":mode,
        "wins":r["wins"],"losses":r["losses"],"ties":r["ties"],
        "missing":r["missing"],"no_signal":r["no_signal"],"non_ties":r["non_ties"],
        "accuracy":r["accuracy"],"wilson95_lower":r["wilson95_lower"],
        "p_value_vs_be80":r["p_value_vs_be80"],
        "third1_accuracy":r["third_accuracies"][0],
        "third2_accuracy":r["third_accuracies"][1],
        "third3_accuracy":r["third_accuracies"][2],
        "ev80":r["ev80"],"ev70":r["ev70"],
        "required_payout_for_ev0":r["required_payout_for_ev0"],"gate":gate,
    }

def main():
    outdir="artifacts/mexc_event_futures"; os.makedirs(outdir,exist_ok=True)
    assets={}
    data={}
    for asset,symbol in SYMBOLS.items():
        a={"proxy_symbol":symbol}
        try:
            idx,ri=fetch_series(symbol,"index")
            fair,rf=fetch_series(symbol,"fair")
            prem,z=build_premium_and_z(idx,fair)
            a.update({
                "index_requests":ri,"fair_requests":rf,
                "index_rows":len(idx),"fair_rows":len(fair),
                "premium_rows":len(prem),"z_rows":len(z),
                "index_discovery_coverage":coverage(idx,DISC_START,DISC_END),
                "fair_discovery_coverage":coverage(fair,DISC_START,DISC_END),
                "index_oos_coverage":coverage(idx,OOS_START,OOS_END),
                "fair_oos_coverage":coverage(fair,OOS_START,OOS_END),
            })
            ok=(a["index_discovery_coverage"]["rows"] and a["fair_discovery_coverage"]["rows"]
                and a["index_oos_coverage"]["rows"] and a["fair_oos_coverage"]["rows"] and len(z)>0)
            a["source_status"]="SOURCE_AVAILABLE" if ok else "SOURCE_BLOCKED"
            if ok:
                data[asset]=(idx,z)
        except Exception as e:
            a["source_status"]="SOURCE_BLOCKED"
            a["error"]=repr(e)
        assets[asset]=a

    cells=[]; rows=[]
    available=[a for a,v in assets.items() if v["source_status"]=="SOURCE_AVAILABLE"]
    for asset in available:
        idx,z=data[asset]
        for h in HORIZONS[asset]:
            for th in THRESHOLDS:
                for mode in MODES:
                    r=score(idx,z,h,th,mode,DISC_START,DISC_END)
                    ok=eligible(r,h)
                    c={"asset":asset,"horizon_min":h,"z_threshold":th,"mode":mode,
                       "eligible":ok,"discovery":r}
                    cells.append(c)
                    rows.append(flat("DISCOVERY",asset,h,th,mode,r,
                                     "DISCOVERY_ELIGIBLE" if ok else "DISCOVERY_FAIL"))

    selected,m,cutoff=bh_select(cells)
    survivors=[]
    for c in selected:
        idx,z=data[c["asset"]]
        r=score(idx,z,c["horizon_min"],c["z_threshold"],c["mode"],OOS_START,OOS_END)
        passed=oos_pass(r)
        rows.append(flat("OOS",c["asset"],c["horizon_min"],c["z_threshold"],c["mode"],r,
                         "OOS_PASS" if passed else "OOS_FAIL"))
        if passed:
            survivors.append({
                "asset":c["asset"],"horizon_min":c["horizon_min"],
                "z_threshold":c["z_threshold"],"mode":c["mode"],
                "discovery":c["discovery"],"oos":r,
            })

    report={
        "lab":"MEXC_EVENT_FUTURES_PREMIUM_BASIS_V1.1",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":"PUBLIC_MEXC_MIN5_INDEX_AND_FAIR_PRICE_PROXY_CLOSE_AT_BUCKET_END",
        "historical_holdout_sep_2026":"LOCKED_NOT_FETCHED",
        "exact_event_futures_settlement":"NOT_PROVEN",
        "current_display_equivalence_candidate":"PASSED_V0.6.4.2",
        "reference_payout":0.80,"reference_break_even_accuracy":P0,
        "current_observed_payout_context":{"BTCUSDT":0.70,"ETHUSDT":0.80,"NVDAUSDT":0.80,"MUUSDT":0.80,"SPCXUSDT":0.80},
        "discovery_multiple_testing":"BENJAMINI_HOCHBERG_FDR_Q_0.05",
        "assets":assets,"source_available_assets":available,
        "source_blocked_assets":[a for a,v in assets.items() if v["source_status"]!="SOURCE_AVAILABLE"],
        "discovery_cells":cells,"bh_eligible_count":m,"bh_cutoff_p":cutoff,
        "bh_selected":[{k:v for k,v in c.items() if k!="eligible"} for c in selected],
        "oos_survivors":survivors,
        "verdict":"PROXY_CANDIDATES_SURVIVE_OOS" if survivors else "NO_PROXY_SURVIVOR_AT_FROZEN_V11_GATE",
        "promotion_status":"NO_EXACT_EVENT_FUTURES_PROMOTION",
    }
    jp=f"{outdir}/premium_basis_v11.json"; cp=f"{outdir}/premium_basis_matrix_v11.csv"
    with open(jp,"w",encoding="utf-8") as f: json.dump(report,f,indent=2,sort_keys=True)
    fields=list(rows[0].keys()) if rows else []
    with open(cp,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    compact={
        "verdict":report["verdict"],"source_available_assets":available,
        "source_blocked_assets":report["source_blocked_assets"],
        "discovery_cells":len(cells),"bh_eligible_count":m,
        "bh_selected_count":len(selected),"bh_cutoff_p":cutoff,
        "oos_survivor_count":len(survivors),
        "oos_survivors":[{
            "asset":x["asset"],"horizon_min":x["horizon_min"],"z_threshold":x["z_threshold"],"mode":x["mode"],
            "disc_n":x["discovery"]["non_ties"],"disc_acc":x["discovery"]["accuracy"],
            "disc_p":x["discovery"]["p_value_vs_be80"],
            "oos_n":x["oos"]["non_ties"],"oos_acc":x["oos"]["accuracy"],
            "oos_p":x["oos"]["p_value_vs_be80"],"oos_ev80":x["oos"]["ev80"],
            "oos_ev70":x["oos"]["ev70"],"required_payout_for_ev0":x["oos"]["required_payout_for_ev0"],
        } for x in survivors],
        "holdout":report["historical_holdout_sep_2026"],
    }
    print(json.dumps(compact,indent=2,sort_keys=True))
    print("WROTE",jp); print("WROTE",cp)

if __name__=="__main__":
    main()

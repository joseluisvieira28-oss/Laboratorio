#!/usr/bin/env python3
"""
MEXC Event Futures Lab V0.10 — frozen peer-breadth proxy study.

Research only. Public MEXC standard-futures index-price Min5 proxy.
No authentication, no orders, no September-2026 holdout.
"""
import csv, json, math, os, time
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
LOOKBACKS=[10,30,60,240]
HORIZONS=[10,30,60,1440]
THRESHOLDS=["THREE_OF_FOUR","FOUR_OF_FOUR"]
MODES=["FOLLOW_BREADTH","FADE_BREADTH"]
MIN_N={10:100,30:80,60:60,1440:20}
P0=1/1.8
PAYOUT=0.80
BH_Q=0.05
Z95=1.959963984540054
STEP=300

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
        time.sleep(0.6*(i+1))
    raise last

def fetch_prices(symbol):
    url=f"{BASE}/api/v1/contract/kline/index_price/{symbol}"
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
                raise RuntimeError("holdout-boundary violation")
            mapped=s+STEP
            if FETCH_START<=mapped<OOS_END:
                out[mapped]=p
        t=e+STEP
        time.sleep(0.10)
    return out,reqs

def aligned(start,end,stride_min):
    step=stride_min*60
    t=((start+step-1)//step)*step
    while t<end:
        yield t
        t+=step

def wilson_lower(w,l):
    n=w+l
    if not n: return None
    p=w/n; z2=Z95*Z95
    return (p+z2/(2*n)-Z95*math.sqrt((p*(1-p)+z2/(4*n))/n))/(1+z2/n)

def exact_p(w,l):
    n=w+l
    return None if not n else float(binomtest(w,n,P0,alternative="greater").pvalue)

def breadth_signal(prices,target,t,lookback,threshold,mode):
    before=t-lookback*60
    ups=downs=0
    for peer,p in prices.items():
        if peer==target:
            continue
        if before not in p or t not in p:
            return None
        d=p[t]-p[before]
        if d>0: ups+=1
        elif d<0: downs+=1

    need=3 if threshold=="THREE_OF_FOUR" else 4
    if ups>=need:
        sig=1
    elif downs>=need:
        sig=-1
    else:
        return None
    return sig if mode=="FOLLOW_BREADTH" else -sig

def score(prices,target,lookback,horizon,threshold,mode,start,end):
    stride=max(lookback,horizon)
    w=l=ties=missing=no_signal=0
    thirds=[[0,0,0] for _ in range(3)]
    span=end-start
    targetp=prices[target]

    for t in aligned(start,end,stride):
        after=t+horizon*60
        if after>=end:
            continue
        if t not in targetp or after not in targetp:
            missing+=1
            continue
        sig=breadth_signal(prices,target,t,lookback,threshold,mode)
        if sig is None:
            no_signal+=1
            continue
        fut=targetp[after]-targetp[t]
        third=min(2,max(0,int(3*(t-start)/max(1,span))))
        if fut==0:
            ties+=1; thirds[third][2]+=1
        elif (fut>0 and sig>0) or (fut<0 and sig<0):
            w+=1; thirds[third][0]+=1
        else:
            l+=1; thirds[third][1]+=1

    n=w+l
    acc=w/n if n else None
    third_acc=[a/(a+b) if a+b else None for a,b,_ in thirds]
    ev=((w*PAYOUT-l)/(w+l+ties)) if w+l+ties else None
    required=(l/w) if w else None
    return {
        "wins":w,"losses":l,"ties":ties,"missing":missing,"no_signal":no_signal,
        "non_ties":n,"accuracy":acc,"wilson95_lower":wilson_lower(w,l),
        "p_value_vs_be80":exact_p(w,l),"third_accuracies":third_acc,
        "ev80":ev,"required_payout_for_ev0":required,"entry_stride_min":stride,
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

def flat(stage,target,lookback,horizon,threshold,mode,r,gate):
    return {
        "stage":stage,"target":target,"lookback_min":lookback,"horizon_min":horizon,
        "breadth_threshold":threshold,"mode":mode,"entry_stride_min":r["entry_stride_min"],
        "wins":r["wins"],"losses":r["losses"],"ties":r["ties"],
        "missing":r["missing"],"no_signal":r["no_signal"],"non_ties":r["non_ties"],
        "accuracy":r["accuracy"],"wilson95_lower":r["wilson95_lower"],
        "p_value_vs_be80":r["p_value_vs_be80"],
        "third1_accuracy":r["third_accuracies"][0],
        "third2_accuracy":r["third_accuracies"][1],
        "third3_accuracy":r["third_accuracies"][2],
        "ev80":r["ev80"],"required_payout_for_ev0":r["required_payout_for_ev0"],
        "gate":gate,
    }

def coverage(p,start,end):
    a=[t for t in p if start<=t<end]
    return {"rows":len(a),"first":min(a) if a else None,"last":max(a) if a else None}

def main():
    outdir="artifacts/mexc_event_futures"; os.makedirs(outdir,exist_ok=True)
    prices={}; assets={}
    for asset,symbol in SYMBOLS.items():
        try:
            p,reqs=fetch_prices(symbol)
            prices[asset]=p
            assets[asset]={
                "proxy_symbol":symbol,"requests":reqs,"total_rows":len(p),
                "discovery_coverage":coverage(p,DISC_START,DISC_END),
                "oos_coverage":coverage(p,OOS_START,OOS_END),
            }
            assets[asset]["source_status"]="SOURCE_AVAILABLE" if assets[asset]["discovery_coverage"]["rows"] and assets[asset]["oos_coverage"]["rows"] else "SOURCE_BLOCKED"
        except Exception as e:
            assets[asset]={"proxy_symbol":symbol,"source_status":"SOURCE_BLOCKED","error":repr(e)}

    available=[a for a,v in assets.items() if v["source_status"]=="SOURCE_AVAILABLE"]
    cells=[]; rows=[]
    if len(available)==5:
        for target in available:
            for lb in LOOKBACKS:
                for h in HORIZONS:
                    for th in THRESHOLDS:
                        for mode in MODES:
                            r=score(prices,target,lb,h,th,mode,DISC_START,DISC_END)
                            ok=eligible(r,h)
                            c={"target":target,"lookback_min":lb,"horizon_min":h,
                               "breadth_threshold":th,"mode":mode,"eligible":ok,"discovery":r}
                            cells.append(c)
                            rows.append(flat("DISCOVERY",target,lb,h,th,mode,r,
                                             "DISCOVERY_ELIGIBLE" if ok else "DISCOVERY_FAIL"))

    selected,m,cutoff=bh_select(cells)
    survivors=[]
    for c in selected:
        r=score(prices,c["target"],c["lookback_min"],c["horizon_min"],
                c["breadth_threshold"],c["mode"],OOS_START,OOS_END)
        passed=oos_pass(r)
        rows.append(flat("OOS",c["target"],c["lookback_min"],c["horizon_min"],
                         c["breadth_threshold"],c["mode"],r,"OOS_PASS" if passed else "OOS_FAIL"))
        if passed:
            survivors.append({
                "target":c["target"],"lookback_min":c["lookback_min"],
                "horizon_min":c["horizon_min"],"breadth_threshold":c["breadth_threshold"],
                "mode":c["mode"],"discovery":c["discovery"],"oos":r,
            })

    report={
        "lab":"MEXC_EVENT_FUTURES_PEER_BREADTH_V0.10",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":"MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_PROXY_CLOSE_AT_BUCKET_END",
        "historical_holdout_sep_2026":"LOCKED_NOT_FETCHED",
        "exact_event_futures":"NOT_PROVEN",
        "reference_payout":PAYOUT,"reference_break_even_accuracy":P0,
        "discovery_multiple_testing":"BENJAMINI_HOCHBERG_FDR_Q_0.05",
        "assets":assets,"source_available_assets":available,
        "source_blocked_assets":[a for a,v in assets.items() if v["source_status"]!="SOURCE_AVAILABLE"],
        "discovery_cells":cells,"bh_eligible_count":m,"bh_cutoff_p":cutoff,
        "bh_selected":[{k:v for k,v in c.items() if k!="eligible"} for c in selected],
        "oos_survivors":survivors,
        "verdict":"PROXY_CANDIDATES_SURVIVE_OOS" if survivors else "NO_PROXY_SURVIVOR_AT_FROZEN_V010_GATE",
        "promotion_status":"NO_EXACT_EVENT_FUTURES_PROMOTION",
    }

    jp=f"{outdir}/peer_breadth_v010.json"; cp=f"{outdir}/peer_breadth_matrix_v010.csv"
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
            "target":x["target"],"lookback_min":x["lookback_min"],
            "horizon_min":x["horizon_min"],"breadth_threshold":x["breadth_threshold"],
            "mode":x["mode"],"disc_n":x["discovery"]["non_ties"],
            "disc_acc":x["discovery"]["accuracy"],"disc_p":x["discovery"]["p_value_vs_be80"],
            "oos_n":x["oos"]["non_ties"],"oos_acc":x["oos"]["accuracy"],
            "oos_p":x["oos"]["p_value_vs_be80"],"oos_ev80":x["oos"]["ev80"],
            "required_payout_for_ev0":x["oos"]["required_payout_for_ev0"],
        } for x in survivors],
        "holdout":report["historical_holdout_sep_2026"],
        "exact_event_futures":report["exact_event_futures"],
    }
    print(json.dumps(compact,indent=2,sort_keys=True))
    print("WROTE",jp); print("WROTE",cp)

if __name__=="__main__":
    main()

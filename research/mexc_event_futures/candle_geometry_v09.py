#!/usr/bin/env python3
"""
MEXC Event Futures Lab V0.9 — frozen candle-geometry proxy study.

Research only. Public MEXC standard-futures index-price OHLC proxy.
No authentication, no orders, no September-2026 holdout.
"""
import csv, json, math, os, time
from collections import defaultdict
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
CHART_TFS=[5,15,60,240]
HORIZONS=[10,30,60,1440]
STRATEGIES=[
    "STRONG_BODY_CONT",
    "STRONG_BODY_REV",
    "UPPER_WICK_REJECT",
    "LOWER_WICK_REJECT",
    "ENGULFING_CONT",
    "ENGULFING_REV",
]
MIN_N={10:80,30:60,60:50,1440:15}
P0=1/1.8
PAYOUT=0.80
BH_Q=0.05
Z95=1.959963984540054
RAW_STEP=300

DISC_START=int(datetime(2026,4,1,tzinfo=timezone.utc).timestamp())
DISC_END=int(datetime(2026,8,1,tzinfo=timezone.utc).timestamp())
OOS_START=DISC_END
OOS_END=int(datetime(2026,9,1,tzinfo=timezone.utc).timestamp())
FETCH_START=DISC_START-2*24*3600
FETCH_END_RAW=OOS_END-2*RAW_STEP

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

def fetch_raw(symbol):
    url=f"{BASE}/api/v1/contract/kline/index_price/{symbol}"
    chunk=5*24*3600
    t=FETCH_START-RAW_STEP
    bars={}
    reqs=0
    while t<=FETCH_END_RAW:
        e=min(t+chunk,FETCH_END_RAW)
        j=fetch_json(url,{"interval":"Min5","start":t,"end":e})
        reqs+=1
        d=j.get("data") or {}
        arrays=[d.get(k) or [] for k in ("time","open","high","low","close")]
        if not all(len(x)==len(arrays[0]) for x in arrays):
            raise RuntimeError("OHLC array length mismatch")
        for s,o,h,l,c in zip(*arrays):
            try:
                s=int(s); o=float(o); h=float(h); l=float(l); c=float(c)
            except Exception:
                continue
            if s>=OOS_END:
                raise RuntimeError("holdout-boundary violation")
            end=s+RAW_STEP
            if FETCH_START<=end<OOS_END:
                bars[end]={"open":o,"high":h,"low":l,"close":c}
        t=e+RAW_STEP
        time.sleep(0.10)
    return bars,reqs

def aggregate_bars(raw,tf_min):
    if tf_min==5:
        return dict(raw)
    tf=tf_min*60
    need=tf//RAW_STEP
    groups=defaultdict(list)
    for end,bar in raw.items():
        group_end=((end+tf-1)//tf)*tf
        groups[group_end].append((end,bar))
    out={}
    for group_end,items in groups.items():
        items.sort()
        if len(items)!=need:
            continue
        expected=[group_end-tf+RAW_STEP+i*RAW_STEP for i in range(need)]
        actual=[x[0] for x in items]
        if actual!=expected:
            continue
        bars=[x[1] for x in items]
        out[group_end]={
            "open":bars[0]["open"],
            "high":max(x["high"] for x in bars),
            "low":min(x["low"] for x in bars),
            "close":bars[-1]["close"],
        }
    return out

def signal(name,bar,prev):
    o,h,l,c=bar["open"],bar["high"],bar["low"],bar["close"]
    rng=h-l
    if rng<=0:
        return None
    body=abs(c-o)
    body_ratio=body/rng
    upper=(h-max(o,c))/rng
    lower=(min(o,c)-l)/rng
    candle_sign=1 if c>o else (-1 if c<o else 0)

    if name=="STRONG_BODY_CONT":
        if body_ratio<0.70 or candle_sign==0: return None
        return candle_sign
    if name=="STRONG_BODY_REV":
        if body_ratio<0.70 or candle_sign==0: return None
        return -candle_sign
    if name=="UPPER_WICK_REJECT":
        return -1 if upper>=0.55 and body_ratio<=0.35 else None
    if name=="LOWER_WICK_REJECT":
        return 1 if lower>=0.55 and body_ratio<=0.35 else None

    if name in ("ENGULFING_CONT","ENGULFING_REV"):
        if prev is None or candle_sign==0 or body_ratio<0.50:
            return None
        plo=min(prev["open"],prev["close"])
        phi=max(prev["open"],prev["close"])
        clo=min(o,c); chi=max(o,c)
        if not (clo<=plo and chi>=phi):
            return None
        return candle_sign if name=="ENGULFING_CONT" else -candle_sign

    raise ValueError(name)

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

def score(raw,charts,tf,horizon,strategy,start,end):
    chart=charts[tf]
    chart_times=sorted(chart)
    prev_map={}
    prev=None
    for t in chart_times:
        prev_map[t]=prev
        prev=chart[t]

    stride=max(tf,horizon)
    w=l=ties=missing=no_signal=0
    thirds=[[0,0,0] for _ in range(3)]
    span=end-start
    for t in aligned(start,end,stride):
        after=t+horizon*60
        if after>=end:
            continue
        if t not in chart or t not in raw or after not in raw:
            missing+=1; continue
        sig=signal(strategy,chart[t],prev_map.get(t))
        if sig is None:
            no_signal+=1; continue
        future=raw[after]["close"]-raw[t]["close"]
        third=min(2,max(0,int(3*(t-start)/max(1,span))))
        if future==0:
            ties+=1; thirds[third][2]+=1
        elif (future>0 and sig>0) or (future<0 and sig<0):
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

def flat(stage,asset,tf,h,strategy,r,gate):
    return {
        "stage":stage,"asset":asset,"chart_tf_min":tf,"horizon_min":h,
        "strategy":strategy,"entry_stride_min":r["entry_stride_min"],
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

def coverage(raw,start,end):
    a=[t for t in raw if start<=t<end]
    return {"rows":len(a),"first":min(a) if a else None,"last":max(a) if a else None}

def main():
    outdir="artifacts/mexc_event_futures"; os.makedirs(outdir,exist_ok=True)
    raws={}; charts_by_asset={}; assets={}
    for asset,symbol in SYMBOLS.items():
        try:
            raw,reqs=fetch_raw(symbol)
            charts={tf:aggregate_bars(raw,tf) for tf in CHART_TFS}
            raws[asset]=raw
            charts_by_asset[asset]=charts
            assets[asset]={
                "proxy_symbol":symbol,"requests":reqs,"raw_rows":len(raw),
                "discovery_coverage":coverage(raw,DISC_START,DISC_END),
                "oos_coverage":coverage(raw,OOS_START,OOS_END),
                "chart_rows":{str(tf):len(charts[tf]) for tf in CHART_TFS},
            }
            assets[asset]["source_status"]="SOURCE_AVAILABLE" if assets[asset]["discovery_coverage"]["rows"] and assets[asset]["oos_coverage"]["rows"] else "SOURCE_BLOCKED"
        except Exception as e:
            assets[asset]={"proxy_symbol":symbol,"source_status":"SOURCE_BLOCKED","error":repr(e)}

    available=[a for a,v in assets.items() if v["source_status"]=="SOURCE_AVAILABLE"]
    cells=[]; rows=[]
    for asset in available:
        for tf in CHART_TFS:
            for h in HORIZONS:
                for strategy in STRATEGIES:
                    r=score(raws[asset],charts_by_asset[asset],tf,h,strategy,DISC_START,DISC_END)
                    ok=eligible(r,h)
                    c={"asset":asset,"chart_tf_min":tf,"horizon_min":h,"strategy":strategy,
                       "eligible":ok,"discovery":r}
                    cells.append(c)
                    rows.append(flat("DISCOVERY",asset,tf,h,strategy,r,
                                     "DISCOVERY_ELIGIBLE" if ok else "DISCOVERY_FAIL"))

    selected,m,cutoff=bh_select(cells)
    survivors=[]
    for c in selected:
        r=score(raws[c["asset"]],charts_by_asset[c["asset"]],c["chart_tf_min"],
                c["horizon_min"],c["strategy"],OOS_START,OOS_END)
        passed=oos_pass(r)
        rows.append(flat("OOS",c["asset"],c["chart_tf_min"],c["horizon_min"],c["strategy"],r,
                         "OOS_PASS" if passed else "OOS_FAIL"))
        if passed:
            survivors.append({
                "asset":c["asset"],"chart_tf_min":c["chart_tf_min"],
                "horizon_min":c["horizon_min"],"strategy":c["strategy"],
                "discovery":c["discovery"],"oos":r,
            })

    report={
        "lab":"MEXC_EVENT_FUTURES_CANDLE_GEOMETRY_V0.9",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "source":"MEXC_STANDARD_FUTURES_INDEX_PRICE_MIN5_OHLC_PROXY_BUCKET_END",
        "historical_holdout_sep_2026":"LOCKED_NOT_FETCHED",
        "exact_event_futures":"NOT_PROVEN",
        "reference_payout":PAYOUT,"reference_break_even_accuracy":P0,
        "discovery_multiple_testing":"BENJAMINI_HOCHBERG_FDR_Q_0.05",
        "assets":assets,"source_available_assets":available,
        "source_blocked_assets":[a for a,v in assets.items() if v["source_status"]!="SOURCE_AVAILABLE"],
        "discovery_cells":cells,"bh_eligible_count":m,"bh_cutoff_p":cutoff,
        "bh_selected":[{k:v for k,v in c.items() if k!="eligible"} for c in selected],
        "oos_survivors":survivors,
        "verdict":"PROXY_CANDIDATES_SURVIVE_OOS" if survivors else "NO_PROXY_SURVIVOR_AT_FROZEN_V09_GATE",
        "promotion_status":"NO_EXACT_EVENT_FUTURES_PROMOTION",
    }

    jp=f"{outdir}/candle_geometry_v09.json"
    cp=f"{outdir}/candle_geometry_matrix_v09.csv"
    with open(jp,"w",encoding="utf-8") as f: json.dump(report,f,indent=2,sort_keys=True)
    fields=list(rows[0].keys()) if rows else []
    with open(cp,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(rows)

    compact={
        "verdict":report["verdict"],
        "source_available_assets":available,
        "source_blocked_assets":report["source_blocked_assets"],
        "discovery_cells":len(cells),"bh_eligible_count":m,
        "bh_selected_count":len(selected),"bh_cutoff_p":cutoff,
        "oos_survivor_count":len(survivors),
        "oos_survivors":[{
            "asset":x["asset"],"chart_tf_min":x["chart_tf_min"],
            "horizon_min":x["horizon_min"],"strategy":x["strategy"],
            "disc_n":x["discovery"]["non_ties"],"disc_acc":x["discovery"]["accuracy"],
            "disc_p":x["discovery"]["p_value_vs_be80"],
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

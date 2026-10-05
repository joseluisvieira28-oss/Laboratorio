#!/usr/bin/env python3
# V2.0 2025 HOLDOUT — ONE SHOT.
# Scientific semantics are frozen in V20_LBANK_2025_CONFIRMATORY_PRE_OUTCOME_FREEZE_2026-10-05.md

import json
import statistics
import time
import urllib.parse
import urllib.request
import urllib.error

FREEZE="7baa29f41260470ed78fb8d9e92bbcdabc8446b4"
ACTIVATION="edad79d8c2d55041da1eeb766891d5f57b0a60a4"

EVENTS=[
    ("AIXBT",1736499327639,"KUCOIN"),
    ("CGPT",1736499327639,"KUCOIN"),
    ("COOKIE",1736499327639,"KUCOIN"),
    ("SYRUP",1746530720814,"LBANK"),
    ("KMNO",1746530720814,"KUCOIN"),
    ("PUMP",1757590673797,"KUCOIN"),
    ("AVNT",1757908021934,"KUCOIN"),
    ("ASTER",1759736929954,"KUCOIN"),
    ("GIGGLE",1761361338417,"KUCOIN"),
    ("F",1761361338417,"KUCOIN"),
    ("BANK",1763028026501,"BITGET"),
    ("MET",1763028026501,"KUCOIN"),
]

UA={"User-Agent":"Mozilla/5.0 CryptoLabV20Holdout/1.0","Accept":"application/json"}

def req_json(url):
    last=None
    for attempt in range(5):
        try:
            r=urllib.request.Request(url,headers=UA)
            with urllib.request.urlopen(r,timeout=30) as x:
                return json.load(x)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            last=e
            if attempt==4:
                raise
            time.sleep(0.5*(attempt+1))
    raise last

# Unified tuple: (ts_ms, open, high, low, close, volume)
def kc(sym,a,b):
    q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
    j=req_json("https://api.kucoin.com/api/v1/market/candles?"+q)
    out=[]
    for x in j.get("data") or []:
        try:
            out.append((int(x[0])*1000,float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])))
        except Exception:
            pass
    return out

def bg(sym,a,b):
    q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
    j=req_json("https://api.bitget.com/api/v3/market/history-candles?"+q)
    out=[]
    for x in j.get("data") or []:
        try:
            out.append((int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
        except Exception:
            pass
    return out

def lb(sym,a,b):
    q=urllib.parse.urlencode({"symbol":sym.lower()+"_usdt","size":2000,"type":"minute1","time":a//1000})
    j=req_json("https://api.lbank.info/v2/kline.do?"+q)
    out=[]
    for x in j.get("data") or []:
        try:
            ts=int(float(x[0]))*1000
            if a<=ts<=b:
                # LBank kline schema: [timestamp, open, high, low, close, volume]
                out.append((ts,float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
        except Exception:
            pass
    return out

def paged_fetch(fn,sym,a,b,window_minutes,overlap_minutes,sleep_s):
    out={}
    cur=a
    while cur<=b:
        end=min(cur+window_minutes*60000,b)
        for x in fn(sym,cur,end):
            out[x[0]]=x
        if end>=b:
            break
        cur=end-overlap_minutes*60000
        time.sleep(sleep_s)
    return [out[k] for k in sorted(out)]

def fetch(venue,sym,a,b):
    if venue=="KUCOIN":
        return paged_fetch(kc,sym,a,b,850,2,0.08)
    if venue=="BITGET":
        return paged_fetch(bg,sym,a,b,80,2,0.20)
    if venue=="LBANK":
        return sorted({x[0]:x for x in lb(sym,a,b)}.values())
    raise ValueError("unknown venue")

def ceilmin(x):
    return ((x+59999)//60000)*60000

def exact(bars,ts):
    for x in bars:
        if x[0]==ts:
            return x
    return None

def median_or_none(xs):
    return statistics.median(xs) if xs else None

def loo_positive(xs):
    if len(xs)<2:
        return False
    return all(statistics.median([v for j,v in enumerate(xs) if j!=i])>0 for i in range(len(xs)))

def concentration_positive(xs):
    pos=[max(0.0,x) for x in xs]
    s=sum(pos)
    return (max(pos)/s) if s>0 else 1.0

def one(ticker,t0,venue):
    floor=(t0//60000)*60000
    ceil=ceilmin(t0)
    entry=ceilmin(t0+60000)
    start=floor-24*3600000-10*60000
    finish=max(floor+70*60000,entry+61*60000)

    bars=fetch(venue,ticker,start,finish)
    by={x[0]:x for x in bars}

    hist=[x for x in bars if t0-24*3600000<=x[0]<t0-3600000]
    hist_gaps=sum(1 for a,b in zip(hist,hist[1:]) if b[0]-a[0]!=60000)
    chunks=[sum(y[5] for y in hist[i:i+5]) for i in range(0,len(hist)-4,5)]
    baseline_med=median_or_none(chunks)

    first5=[x for x in bars if ceil<=x[0]<ceil+5*60000]
    p0bar=exact(bars,floor-60000)

    required=[floor-60000,floor+60000,floor+5*60000,floor+15*60000,floor+60*60000,
              entry,entry+4*60000,entry+14*60000,entry+59*60000]
    if (p0bar is None or len(first5)!=5 or hist_gaps!=0 or not chunks or baseline_med is None or baseline_med<=0
        or not all(ts in by for ts in required)):
        return {"ticker":ticker,"venue":venue,"status":"SOURCE_FAIL_AT_OUTCOME_RUN"}

    btc=fetch(venue,"BTC",entry-2*60000,entry+61*60000)
    bby={x[0]:x for x in btc}
    btc_required=[entry,entry+4*60000,entry+14*60000,entry+59*60000]
    if not all(ts in bby for ts in btc_required):
        return {"ticker":ticker,"venue":venue,"status":"SOURCE_FAIL_AT_OUTCOME_RUN"}

    p0=p0bar[4]
    r={"ticker":ticker,"venue":venue,"status":"VALID","t0_ms":t0,
       "info_p0":p0,"baseline_5m_chunks":len(chunks),"hist_gaps":hist_gaps}

    for n in [1,5,15,60]:
        target=floor+n*60000
        xb=by[target]
        rr=xb[4]/p0-1
        win=[x for x in bars if floor<=x[0]<=target]
        r[f"r{n}"]=rr
        r[f"mfe{n}"]=max((x[2]/p0-1 for x in win),default=None)
        r[f"mae{n}"]=min((x[3]/p0-1 for x in win),default=None)

    r["volume_shock_5m"]=sum(x[5] for x in first5)/baseline_med
    r["exec_entry_ts"]=entry
    ep=by[entry][1]
    r["exec_entry_price"]=ep

    bep=bby[entry][1]
    for n,target_off in [(5,4),(15,14),(60,59)]:
        target=entry+target_off*60000
        xb=by[target]
        bb=bby[target]
        gross=xb[4]/ep-1
        btc_gross=bb[4]/bep-1
        r[f"exec_r{n}"]=gross
        r[f"exec_r{n}_btc"]=btc_gross
        r[f"exec_r{n}_exbtc"]=gross-btc_gross
        r[f"exec_net25_r{n}"]=(xb[4]*(1-0.00125))/(ep*(1+0.00125))-1
        r[f"exec_net50_r{n}"]=(xb[4]*(1-0.0025))/(ep*(1+0.0025))-1
        r[f"exec_net100_r{n}"]=(xb[4]*(1-0.005))/(ep*(1+0.005))-1
        w=[x for x in bars if entry<=x[0]<=target]
        r[f"exec_mfe{n}"]=max((x[2]/ep-1 for x in w),default=None)
        r[f"exec_mae{n}"]=min((x[3]/ep-1 for x in w),default=None)
    return r

rows=[]
for e in EVENTS:
    try:
        rows.append(one(*e))
    except Exception as ex:
        rows.append({"ticker":e[0],"venue":e[2],"status":"SOURCE_FAIL_AT_OUTCOME_RUN","error_type":type(ex).__name__})

valid=[x for x in rows if x.get("status")=="VALID"]

summary={
    "parent_freeze":FREEZE,
    "activation_receipt":ACTIVATION,
    "sample_size_frozen":12,
    "n":len(valid),
}

if len(valid)<12:
    summary.update({
        "information_gate_pass":False,
        "primary_execution_gate_pass":False,
        "verdict":"SOURCE_BLOCKED",
    })
else:
    def vals(k): return [x[k] for x in valid]

    info_r15=vals("r15")
    info_hit=sum(x>0 for x in info_r15)/len(info_r15)
    info_conc=concentration_positive(info_r15)
    info_loo=loo_positive(info_r15)
    info_gate=(
        len(valid)>=12
        and statistics.median(info_r15)>.0075
        and info_hit>=.65
        and statistics.median(vals("r5"))>.005
        and statistics.median(vals("volume_shock_5m"))>=2
        and info_loo
        and info_conc<=.35
    )

    net50=vals("exec_net50_r15")
    exec_hit=sum(x>0 for x in net50)/len(net50)
    exec_loo=loo_positive(net50)
    exec_conc=concentration_positive(net50)
    exec_exbtc_med=statistics.median(vals("exec_r15_exbtc"))
    exec_gate=(
        len(valid)>=12
        and statistics.median(net50)>0
        and exec_hit>=.60
        and exec_loo
        and exec_conc<=.35
        and exec_exbtc_med>0
    )

    summary.update({
        "median_r1":statistics.median(vals("r1")),
        "median_r5":statistics.median(vals("r5")),
        "median_r15":statistics.median(info_r15),
        "median_r60":statistics.median(vals("r60")),
        "hit_r15":info_hit,
        "median_volume_shock_5m":statistics.median(vals("volume_shock_5m")),
        "information_loo_positive":info_loo,
        "information_positive_concentration":info_conc,
        "information_gate_pass":info_gate,

        "median_exec_gross_r5":statistics.median(vals("exec_r5")),
        "median_exec_gross_r15":statistics.median(vals("exec_r15")),
        "median_exec_gross_r60":statistics.median(vals("exec_r60")),
        "median_exec_net25_r15":statistics.median(vals("exec_net25_r15")),
        "median_exec_net50_r15":statistics.median(net50),
        "median_exec_net100_r15":statistics.median(vals("exec_net100_r15")),
        "exec_net50_r15_hit_rate":exec_hit,
        "exec_net50_r15_loo_positive":exec_loo,
        "exec_net50_r15_positive_concentration":exec_conc,
        "median_exec_gross_r15_exbtc":exec_exbtc_med,
        "median_exec_mfe15":statistics.median(vals("exec_mfe15")),
        "median_exec_mae15":statistics.median(vals("exec_mae15")),
        "primary_execution_gate_pass":exec_gate,
        "verdict":"SURVIVES_EXECUTION_HOLDOUT" if exec_gate else "NO_EXECUTABLE_EDGE_HOLDOUT",
    })

print("V20_2025_HOLDOUT_SUMMARY_BEGIN")
print(json.dumps(summary,indent=2,sort_keys=True))
print("V20_2025_HOLDOUT_SUMMARY_END")
print("V20_2025_HOLDOUT_EVENTS_BEGIN")
print(json.dumps(rows,indent=2,sort_keys=True))
print("V20_2025_HOLDOUT_EVENTS_END")

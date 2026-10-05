#!/usr/bin/env python3
# V2.0 all-binding SOURCE-ONLY preflight, technically remediated.
# Emits counts/booleans only. No prices, returns, PnL, MFE or MAE.

import json
import statistics
import time
import urllib.parse
import urllib.request
import urllib.error

EVENTS = [
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

UA={"User-Agent":"Mozilla/5.0 CryptoLabV20PreflightRemediated/1.0","Accept":"application/json"}

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

def kc(sym,a,b):
    q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
    j=req_json("https://api.kucoin.com/api/v1/market/candles?"+q)
    out=[]
    for x in j.get("data") or []:
        try: out.append((int(x[0])*1000,float(x[5])))
        except Exception: pass
    return out

def bg(sym,a,b):
    q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
    j=req_json("https://api.bitget.com/api/v3/market/history-candles?"+q)
    out=[]
    for x in j.get("data") or []:
        try: out.append((int(x[0]),float(x[5])))
        except Exception: pass
    return out

def lb(sym,a,b):
    q=urllib.parse.urlencode({"symbol":sym.lower()+"_usdt","size":2000,"type":"minute1","time":a//1000})
    j=req_json("https://api.lbank.info/v2/kline.do?"+q)
    out=[]
    for x in j.get("data") or []:
        try:
            ts=int(float(x[0]))*1000
            if a<=ts<=b: out.append((ts,float(x[5])))
        except Exception: pass
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

def one(ticker,t0,venue):
    floor=(t0//60000)*60000
    ceil=ceilmin(t0)
    entry=ceilmin(t0+60000)
    start=floor-24*3600000-10*60000
    finish=max(floor+70*60000,entry+59*60000)

    bars=fetch(venue,ticker,start,finish)
    ts={x[0] for x in bars}

    witness=[x for x in bars if x[0]<=t0-24*3600000]
    near=[x for x in bars if t0-10*60000<=x[0]<floor]
    first5=[x for x in bars if ceil<=x[0]<ceil+5*60000]
    hist=[x for x in bars if t0-24*3600000<=x[0]<t0-3600000]
    chunks=[sum(y[1] for y in hist[i:i+5]) for i in range(0,len(hist)-4,5)]
    med=statistics.median(chunks) if chunks else None
    gaps=sum(1 for a,b in zip(hist,hist[1:]) if b[0]-a[0]!=60000)

    btc=fetch(venue,"BTC",entry-2*60000,entry+61*60000)
    bts={x[0] for x in btc}

    required_asset=[
        floor-60000,
        floor+1*60000,
        floor+5*60000,
        floor+15*60000,
        floor+60*60000,
        entry,
        entry+4*60000,
        entry+14*60000,
        entry+59*60000,
    ]
    required_btc=[entry,entry+4*60000,entry+14*60000,entry+59*60000]

    source_ok=bool(
        witness
        and near
        and len(first5)==5
        and chunks
        and med is not None
        and med>0
        and gaps==0
        and all(x in ts for x in required_asset)
        and all(x in bts for x in required_btc)
    )
    return {
        "ticker":ticker,
        "venue":venue,
        "bars":len(bars),
        "witness":len(witness),
        "near":len(near),
        "first5":len(first5),
        "hist_minutes":len(hist),
        "hist_5m_chunks":len(chunks),
        "hist_gaps":gaps,
        "baseline_median_volume_positive":bool(med is not None and med>0),
        "asset_required_bars_present":all(x in ts for x in required_asset),
        "btc_required_bars_present":all(x in bts for x in required_btc),
        "source_ok":source_ok,
    }

rows=[]
for e in EVENTS:
    try:
        rows.append(one(*e))
    except Exception as ex:
        rows.append({"ticker":e[0],"venue":e[2],"source_ok":False,"error_type":type(ex).__name__})

all_ok=len(rows)==12 and all(r.get("source_ok") for r in rows)
print("V20_ALL_BINDINGS_SOURCE_PREFLIGHT_BEGIN")
print(json.dumps({"n":len(rows),"all_ok":all_ok,"rows":rows},indent=2,sort_keys=True))
print("V20_ALL_BINDINGS_SOURCE_PREFLIGHT_END")
if not all_ok:
    raise SystemExit(2)

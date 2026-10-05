#!/usr/bin/env python3
# COINDESK20-REBALANCE-FORCED-FLOW-001 V0.2
# One-shot development outcome runner. Must only run after activation receipt.
import io, json, math, statistics, urllib.request, zipfile
from datetime import datetime, date, timedelta, timezone
from zoneinfo import ZoneInfo

EVENTS=[
 {"quarter":"2024-04","symbol":"NEAR","action":"ADD","pub":"2024-03-19","impl":"2024-04-02"},
 {"quarter":"2024-04","symbol":"XLM","action":"DELETE","pub":"2024-03-19","impl":"2024-04-02"},
 {"quarter":"2024-07","symbol":"HBAR","action":"ADD","pub":"2024-06-18","impl":"2024-07-02"},
 {"quarter":"2024-07","symbol":"RNDR","action":"ADD","pub":"2024-06-18","impl":"2024-07-02"},
 {"quarter":"2024-07","symbol":"DOGE","action":"DELETE","pub":"2024-06-18","impl":"2024-07-02"},
 {"quarter":"2024-07","symbol":"SHIB","action":"DELETE","pub":"2024-06-18","impl":"2024-07-02"},
 {"quarter":"2024-10","symbol":"XLM","action":"ADD","pub":"2024-09-18","impl":"2024-10-02"},
 {"quarter":"2024-10","symbol":"ATOM","action":"DELETE","pub":"2024-09-18","impl":"2024-10-02"},
 {"quarter":"2025-01","symbol":"SUI","action":"ADD","pub":"2025-01-03","impl":"2025-01-31"},
 {"quarter":"2025-01","symbol":"AAVE","action":"ADD","pub":"2025-01-03","impl":"2025-01-31"},
 {"quarter":"2025-01","symbol":"RENDER","action":"DELETE","pub":"2025-01-03","impl":"2025-01-31"},
 {"quarter":"2025-01","symbol":"ETC","action":"DELETE","pub":"2025-01-03","impl":"2025-01-31"},
 {"quarter":"2025-10","symbol":"CRO","action":"ADD","pub":"2025-10-03","impl":"2025-10-31"},
 {"quarter":"2025-10","symbol":"FIL","action":"DELETE","pub":"2025-10-03","impl":"2025-10-31"},
]
BASE="https://data.binance.vision/data/spot"
UA={"User-Agent":"Mozilla/5.0 CryptoLabCD20V02/1.0"}
_cache={}

def norm_ts(v):
    n=int(v)
    return n//1000 if n>10**14 else n

def fetch_zip(url):
    if url in _cache: return _cache[url]
    req=urllib.request.Request(url,headers=UA)
    with urllib.request.urlopen(req,timeout=40) as r: b=r.read()
    z=zipfile.ZipFile(io.BytesIO(b))
    names=z.namelist()
    if not names: raise RuntimeError("empty zip")
    raw=z.read(names[0]).decode("utf-8","replace")
    _cache[url]=raw
    return raw

def daily_1m(pair, ds):
    url=f"{BASE}/daily/klines/{pair}/1m/{pair}-1m-{ds}.zip"
    raw=fetch_zip(url)
    out={}
    for line in raw.splitlines():
        p=line.split(",")
        if len(p)<7: continue
        try:
            ts=norm_ts(p[0])
            out[ts]={"open":float(p[1]),"high":float(p[2]),"low":float(p[3]),"close":float(p[4])}
        except: pass
    return out

def monthly_1h(pair, ym):
    url=f"{BASE}/monthly/klines/{pair}/1h/{pair}-1h-{ym}.zip"
    raw=fetch_zip(url)
    out=[]
    for line in raw.splitlines():
        p=line.split(",")
        if len(p)<7: continue
        try:
            out.append((norm_ts(p[0]),float(p[1]),float(p[2]),float(p[3]),float(p[4])))
        except: pass
    return out

def ms(dt): return int(dt.timestamp()*1000)

def pub_entry(pub, days):
    y,m,d=map(int,pub.split("-"))
    return datetime(y,m,d,tzinfo=timezone.utc)+timedelta(days=days)

def impl_dt(s):
    y,m,d=map(int,s.split("-"))
    return datetime(y,m,d,16,0,tzinfo=ZoneInfo("America/New_York")).astimezone(timezone.utc)

def bar_open_for_close_at_or_before(target):
    # 1m bar opening one minute before target has close <= target.
    return target-timedelta(minutes=1)

def get_open(pair, dt):
    bars=daily_1m(pair,dt.date().isoformat())
    row=bars.get(ms(dt))
    if row is None: raise KeyError(f"{pair} missing open bar {dt.isoformat()}")
    return row["open"]

def get_close(pair, bar_open):
    bars=daily_1m(pair,bar_open.date().isoformat())
    row=bars.get(ms(bar_open))
    if row is None: raise KeyError(f"{pair} missing close bar {bar_open.isoformat()}")
    return row["close"]

def months_between(a,b):
    y,m=a.year,a.month
    out=[]
    while (y,m)<=(b.year,b.month):
        out.append(f"{y:04d}-{m:02d}")
        m+=1
        if m==13: y,m=y+1,1
    return out

def mfe_mae(pair, entry_dt, exit_bar_open, entry_px, direction):
    vals=[]
    for ym in months_between(entry_dt,exit_bar_open):
        try: vals.extend(monthly_1h(pair,ym))
        except Exception: continue
    start=ms(entry_dt); end=ms(exit_bar_open+timedelta(minutes=1))
    sub=[x for x in vals if start<=x[0]<end]
    if not sub: return None,None
    highs=[x[2] for x in sub]; lows=[x[3] for x in sub]
    if direction==1:
        mfe=max(h/entry_px-1 for h in highs)
        mae=min(l/entry_px-1 for l in lows)
    else:
        mfe=max(1-l/entry_px for l in lows)
        mae=min(1-h/entry_px for h in highs)
    return mfe,mae

def med(xs): return statistics.median(xs) if xs else None

rows=[]
for e in EVENTS:
    direction=1 if e["action"]=="ADD" else -1
    pair=e["symbol"]+"USDT"
    ent=pub_entry(e["pub"],2)
    ent24=pub_entry(e["pub"],1)
    impl=impl_dt(e["impl"])
    exit5_open=bar_open_for_close_at_or_before(impl-timedelta(minutes=5))
    exit60_open=bar_open_for_close_at_or_before(impl-timedelta(minutes=60))
    exitp5_open=bar_open_for_close_at_or_before(impl+timedelta(minutes=5))
    try:
        pe=get_open(pair,ent); pb=get_open("BTCUSDT",ent)
        px=get_close(pair,exit5_open); pxb=get_close("BTCUSDT",exit5_open)
        ra=px/pe-1; rb=pxb/pb-1; ex=ra-rb
        row={**e,"pair":pair,"market_valid":True,"direction":direction,
             "entry_utc":ent.isoformat(),"exit_primary_bar_open_utc":exit5_open.isoformat(),
             "r_asset":ra,"r_btc":rb,"r_exbtc":ex,
             "signed_raw":direction*ra,"signed_exbtc":direction*ex}
        # Secondary diagnostics.
        try:
            pe24=get_open(pair,ent24); pb24=get_open("BTCUSDT",ent24)
            row["secondary_entry24_signed_exbtc"]=direction*((px/pe24-1)-(pxb/pb24-1))
        except Exception as z: row["secondary_entry24_error"]=type(z).__name__
        try:
            p60=get_close(pair,exit60_open); b60=get_close("BTCUSDT",exit60_open)
            row["secondary_exit60_signed_exbtc"]=direction*((p60/pe-1)-(b60/pb-1))
        except Exception as z: row["secondary_exit60_error"]=type(z).__name__
        try:
            pp5=get_close(pair,exitp5_open); bp5=get_close("BTCUSDT",exitp5_open)
            row["secondary_exit_plus5_signed_exbtc"]=direction*((pp5/pe-1)-(bp5/pb-1))
        except Exception as z: row["secondary_exit_plus5_error"]=type(z).__name__
        try:
            mfe,mae=mfe_mae(pair,ent,exit5_open,pe,direction)
            row["mfe_raw_signed"]=mfe; row["mae_raw_signed"]=mae
        except Exception as z: row["mfe_mae_error"]=type(z).__name__
    except Exception as exn:
        row={**e,"pair":pair,"market_valid":False,"error":f"{type(exn).__name__}:{exn}"}
    rows.append(row)

valid=[r for r in rows if r.get("market_valid")]
sx=[r["signed_exbtc"] for r in valid]
sr=[r["signed_raw"] for r in valid]
hit=sum(x>0 for x in sx)/len(sx) if sx else 0
loo=[]
for i in range(len(sx)):
    loo.append(med(sx[:i]+sx[i+1:]))
quarters=sorted(set(r["quarter"] for r in valid))
qloo={}
for q in quarters:
    z=[r["signed_exbtc"] for r in valid if r["quarter"]!=q]
    qloo[q]=med(z)
pos=[x for x in sx if x>0]
conc=max(pos)/sum(pos) if pos else None
adds=[r["r_exbtc"] for r in valid if r["action"]=="ADD"]
dels=[-r["r_exbtc"] for r in valid if r["action"]=="DELETE"]
gates={
 "n_ge_12":len(valid)>=12,
 "median_signed_exbtc_gt_1pct":(med(sx) is not None and med(sx)>0.01),
 "hit_ge_65pct":hit>=0.65,
 "median_signed_raw_gt_0":(med(sr) is not None and med(sr)>0),
 "loo_all_positive":bool(loo) and all(x is not None and x>0 for x in loo),
 "quarter_loo_all_positive":bool(qloo) and all(x is not None and x>0 for x in qloo.values()),
 "concentration_le_35pct":(conc is not None and conc<=0.35),
 "median_add_exbtc_gt_0":(med(adds) is not None and med(adds)>0),
 "median_delete_signed_exbtc_gt_0":(med(dels) is not None and med(dels)>0),
}
if len(valid)<12:
    verdict="SOURCE_BLOCKED"
elif all(gates.values()):
    verdict="SURVIVES_FORCED_FLOW_DISCOVERY"
else:
    verdict="NO_EDGE_DISCOVERY"

summary={
 "family":"COINDESK20-REBALANCE-FORCED-FLOW-001",
 "version":"V0.2",
 "n_source":len(EVENTS),"n_market_valid":len(valid),
 "median_signed_exbtc":med(sx),"hit_signed_exbtc":hit,
 "median_signed_raw":med(sr),
 "loo_medians":loo,"quarter_loo_medians":qloo,
 "positive_concentration":conc,
 "median_add_exbtc":med(adds),"median_delete_signed_exbtc":med(dels),
 "gates":gates,"verdict":verdict,
}
print("CD20_V02_OUTCOME_BEGIN")
print(json.dumps({"summary":summary,"events":rows},indent=2,sort_keys=True))
print("CD20_V02_OUTCOME_END")

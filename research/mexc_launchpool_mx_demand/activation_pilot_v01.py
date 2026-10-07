import ccxt, math, random, statistics, json, os, csv
from datetime import datetime, timezone, timedelta

OUT="artifacts/mexc_launchpool_mx_demand_v02_pilot"
os.makedirs(OUT,exist_ok=True)

EVENTS=[
("APT","2025-01-23T10:00:00Z"),
("IP","2025-02-12T10:00:00Z"),
("TERM","2025-03-25T11:00:00Z"),
("K","2025-03-28T10:00:00Z"),
("MNT","2025-03-31T14:00:00Z"),
("EPT","2025-04-21T12:00:00Z"),
("SHM","2025-05-02T11:00:00Z"),
("ICEBERG","2025-05-20T11:00:00Z"),
("BOMB","2025-06-13T10:00:00Z"),
("EURR","2025-07-24T11:00:00Z"),
("USDR","2025-07-28T11:00:00Z"),
("EIN","2025-08-04T10:00:00Z"),
("EMBLEM","2026-04-15T13:00:00Z"),
("NEX","2026-05-20T13:00:00Z"),
]

ex=ccxt.mexc({"enableRateLimit":True})

def ms(dt): return int(dt.timestamp()*1000)

def fetch_exact(symbol, t0):
    since=ms(t0-timedelta(hours=1))
    rows=ex.fetch_ohlcv(symbol,"15m",since=since,limit=120)
    mp={int(r[0]):r for r in rows}
    return mp

def qtile(xs,p):
    ys=sorted(xs)
    if not ys: return None
    pos=(len(ys)-1)*p
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi:return ys[lo]
    return ys[lo]*(hi-pos)+ys[hi]*(pos-lo)

rows=[]
for name,tstr in EVENTS:
    t0=datetime.fromisoformat(tstr.replace("Z","+00:00"))
    entry=t0
    t1=t0+timedelta(hours=1)
    t6=t0+timedelta(hours=6)
    t24=t0+timedelta(hours=24)
    try:
        mx=fetch_exact("MX/USDT",t0)
        btc=fetch_exact("BTC/USDT",t0)
        need=[entry,t1,t6,t24]
        keys=[ms(x) for x in need]
        if not all(k in mx and k in btc for k in keys):
            rows.append({"event":name,"t0":tstr,"status":"MISSING_EXACT_CANDLE",
                         "missing":[datetime.fromtimestamp(k/1000,timezone.utc).isoformat() for k in keys if k not in mx or k not in btc]})
            continue
        def op(m,t): return float(m[ms(t)][1])
        mx0,mx1,mx6,mx24=[op(mx,t) for t in need]
        b0,b1,b6,b24=[op(btc,t) for t in need]
        rel1=math.log(mx1/mx0)-math.log(b1/b0)
        rel6=math.log(mx6/mx0)-math.log(b6/b0)
        rel24=math.log(mx24/mx0)-math.log(b24/b0)
        rows.append({
          "event":name,"t0":tstr,"status":"OK",
          "mx_entry":mx0,"mx_exit_24h":mx24,
          "btc_entry":b0,"btc_exit_24h":b24,
          "mx_raw_24h":mx24/mx0-1,
          "btc_raw_24h":b24/b0-1,
          "rel_log_1h":rel1,
          "rel_log_6h":rel6,
          "rel_log_24h":rel24,
          "year":t0.year
        })
    except Exception as e:
        rows.append({"event":name,"t0":tstr,"status":"ERROR","error":repr(e)})

ok=[r for r in rows if r["status"]=="OK"]
vals=[r["rel_log_24h"] for r in ok]
n=len(vals)
pos=sum(v>0 for v in vals)

if n:
    mean=sum(vals)/n
    med=statistics.median(vals)
    p_sign=sum(math.comb(n,k) for k in range(pos,n+1))/(2**n)
    rng=random.Random(20261007)
    boots=[]
    for _ in range(10000):
        s=[vals[rng.randrange(n)] for __ in range(n)]
        boots.append(sum(s)/n)
    ci90=[qtile(boots,.05),qtile(boots,.95)]
    loo=[]
    for i in range(n):
        vv=vals[:i]+vals[i+1:]
        if vv: loo.append(sum(vv)/len(vv))
    loo_min=min(loo) if loo else None
else:
    mean=med=p_sign=loo_min=None; ci90=[None,None]

by_year={}
for y in sorted(set(r["year"] for r in ok)):
    vv=[r["rel_log_24h"] for r in ok if r["year"]==y]
    by_year[str(y)]={"n":len(vv),"mean":sum(vv)/len(vv),"median":statistics.median(vv)}

present=bool(n>=10 and med>0 and pos/n>0.5 and p_sign<0.10 and loo_min is not None and loo_min>0)
summary={
 "candidate_id":"MEXC-LAUNCHPOOL-MX-DEMAND-001",
 "study":"ACTIVATION_PILOT_V0.1",
 "market_source":"MEXC public spot OHLCV via CCXT",
 "authenticated":False,
 "orders":False,
 "event_count_frozen":len(EVENTS),
 "n_analyzable":n,
 "positive_count":pos,
 "positive_fraction":pos/n if n else None,
 "mean_rel_log_24h":mean,
 "median_rel_log_24h":med,
 "sign_test_one_sided_p":p_sign,
 "bootstrap_mean_ci90":ci90,
 "loo_min_mean":loo_min,
 "by_year":by_year,
 "classification":"PILOT_SIGNAL_PRESENT" if present else "PILOT_NO_SIGNAL",
 "promotion_credit":0
}

with open(f"{OUT}/pilot_rows.json","w") as f: json.dump(rows,f,indent=2)
with open(f"{OUT}/pilot_summary.json","w") as f: json.dump(summary,f,indent=2)
with open(f"{OUT}/pilot_rows.csv","w",newline="") as f:
    keys=sorted({k for r in rows for k in r})
    w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)
print(json.dumps(summary,indent=2))

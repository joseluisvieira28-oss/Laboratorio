import csv, io, json, math, os, random, statistics, requests
from datetime import datetime, timezone, timedelta
import ccxt

OUT="artifacts/mexc_launchpool_mx_demand_v022_full_pilot"
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
IDS={
 "MX":"7fb2a8ab8a5e4eb699ac34ee340489f8",
 "BTC":"2fb942154ef44a4ab2ef98c8afb6a4a7",
}
S=requests.Session()
S.headers.update({"User-Agent":"CryptoLabResearch/1.0"})
EX=ccxt.mexc({"enableRateLimit":True})
cache={}

def month_start(dt):
    return dt.replace(day=1,hour=0,minute=0,second=0,microsecond=0)

def archive_month(asset, dt):
    key=(asset,dt.year,dt.month)
    if key in cache:return cache[key]
    name=f"{asset}_USDT-Min15-{dt.year:04d}-{dt.month:02d}-01.csv"
    url=f"https://d2s4an60yebwep.cloudfront.net/SPOT2/kline/{IDS[asset]}/monthly/Min15/{name}"
    r=S.get(url,timeout=45)
    if r.status_code!=200:
        raise RuntimeError(f"archive_http_{r.status_code}:{url}")
    mp={}
    rd=csv.DictReader(io.StringIO(r.text))
    for row in rd:
        mp[int(row["open_time"])]=float(row["open"])
    cache[key]=(mp,url,len(r.content))
    return cache[key]

def archive_open(asset, t):
    mp,_,_=archive_month(asset,month_start(t))
    k=int(t.timestamp()*1000)
    if k in mp:return mp[k]
    return None

def v3_map(symbol,t0):
    since=int((t0-timedelta(hours=1)).timestamp()*1000)
    rows=EX.fetch_ohlcv(symbol,"15m",since=since,limit=120)
    return {int(r[0]):float(r[1]) for r in rows}

def qtile(xs,p):
    ys=sorted(xs)
    pos=(len(ys)-1)*p
    lo=int(math.floor(pos));hi=int(math.ceil(pos))
    return ys[lo] if lo==hi else ys[lo]*(hi-pos)+ys[hi]*(pos-lo)

rows=[]
for name,tstr in EVENTS:
    t0=datetime.fromisoformat(tstr.replace("Z","+00:00"))
    times=[t0,t0+timedelta(hours=1),t0+timedelta(hours=6),t0+timedelta(hours=24)]
    try:
        if t0.year==2025:
            mx=[archive_open("MX",t) for t in times]
            btc=[archive_open("BTC",t) for t in times]
            source="MEXC_OFFICIAL_MONTHLY_ARCHIVE_MIN15"
        else:
            mm=v3_map("MX/USDT",t0); bm=v3_map("BTC/USDT",t0)
            keys=[int(t.timestamp()*1000) for t in times]
            mx=[mm.get(k) for k in keys]; btc=[bm.get(k) for k in keys]
            source="MEXC_PUBLIC_V3_MIN15_ORIGINAL_ROUTE"
        if any(x is None for x in mx+btc):
            rows.append({"event":name,"t0":tstr,"year":t0.year,"status":"MISSING_EXACT_CANDLE","source":source,
                         "mx_missing":[times[i].isoformat() for i,x in enumerate(mx) if x is None],
                         "btc_missing":[times[i].isoformat() for i,x in enumerate(btc) if x is None]})
            continue
        mx0,mx1,mx6,mx24=mx
        b0,b1,b6,b24=btc
        rel1=math.log(mx1/mx0)-math.log(b1/b0)
        rel6=math.log(mx6/mx0)-math.log(b6/b0)
        rel24=math.log(mx24/mx0)-math.log(b24/b0)
        rows.append({
          "event":name,"t0":tstr,"year":t0.year,"status":"OK","source":source,
          "mx_entry":mx0,"mx_exit_24h":mx24,"btc_entry":b0,"btc_exit_24h":b24,
          "mx_raw_24h":mx24/mx0-1,"btc_raw_24h":b24/b0-1,
          "rel_log_1h":rel1,"rel_log_6h":rel6,"rel_log_24h":rel24
        })
    except Exception as e:
        rows.append({"event":name,"t0":tstr,"year":t0.year,"status":"ERROR","error":repr(e)})

ok=[r for r in rows if r["status"]=="OK"]
vals=[r["rel_log_24h"] for r in ok]
n=len(vals); pos=sum(v>0 for v in vals)
if n:
    mean=sum(vals)/n
    med=statistics.median(vals)
    p_sign=sum(math.comb(n,k) for k in range(pos,n+1))/(2**n)
    rng=random.Random(20261007)
    boots=[sum(vals[rng.randrange(n)] for __ in range(n))/n for _ in range(10000)]
    ci90=[qtile(boots,.05),qtile(boots,.95)]
    loo=[sum(vals[:i]+vals[i+1:])/(n-1) for i in range(n)] if n>1 else []
    loo_min=min(loo) if loo else None
else:
    mean=med=p_sign=loo_min=None;ci90=[None,None]

by_year={}
for y in sorted(set(r["year"] for r in ok)):
    vv=[r["rel_log_24h"] for r in ok if r["year"]==y]
    by_year[str(y)]={"n":len(vv),"mean":sum(vv)/len(vv),"median":statistics.median(vv),
                     "positive_fraction":sum(v>0 for v in vv)/len(vv)}

present=bool(n>=10 and med>0 and pos/n>0.5 and p_sign<0.10 and loo_min is not None and loo_min>0)
classification=("PILOT_SIGNAL_PRESENT" if present else ("PILOT_NO_SIGNAL" if n>=10 else "DATA_COVERAGE_INSUFFICIENT"))
summary={
 "candidate_id":"MEXC-LAUNCHPOOL-MX-DEMAND-001",
 "study":"ACTIVATION_PILOT_V0.1_WITH_V0.2.2_SOURCE_REMEDIATION",
 "event_count_frozen":14,
 "n_analyzable":n,
 "positive_count":pos,
 "positive_fraction":pos/n if n else None,
 "mean_rel_log_24h":mean,
 "median_rel_log_24h":med,
 "sign_test_one_sided_p":p_sign,
 "bootstrap_mean_ci90":ci90,
 "loo_min_mean":loo_min,
 "by_year":by_year,
 "classification":classification,
 "promotion_credit":0,
 "science_changed":False,
 "event_set_changed":False,
 "horizon_changed":False,
 "authenticated":False,
 "orders":False
}
with open(f"{OUT}/pilot_rows.json","w") as f:json.dump(rows,f,indent=2)
with open(f"{OUT}/pilot_summary.json","w") as f:json.dump(summary,f,indent=2)
print(json.dumps(summary,indent=2))
print("ROWS")
for r in rows:
    if r["status"]=="OK":
        print(r["event"],r["t0"],f'{100*r["rel_log_24h"]:.4f}%')
    else:
        print(r["event"],r["status"],r.get("error",""))

import requests,csv,io,math,json,os
from datetime import datetime,timezone,timedelta
import numpy as np

OUT="artifacts/mexc_launchpool_reward_token_sellpressure_v01_discovery"
os.makedirs(OUT,exist_ok=True)
BASE="https://www.mexc.com"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (CryptoLabResearch/1.0)"})

EVENTS=[
("XTER","2025-01-08T10:00:00Z"),
("IP","2025-02-13T09:00:00Z"),
("TERM","2025-03-26T04:00:00Z"),
("K","2025-03-31T15:00:00Z"),
("EPT","2025-04-21T12:00:00Z"),
("SHM","2025-05-08T10:00:00Z"),
("ICEBERG","2025-05-20T11:00:00Z"),
("BOMB","2025-06-17T10:10:00Z"),
("TRN","2025-07-17T17:00:00Z"),
("EMBLEM","2026-04-16T15:00:00Z"),
("NEX","2026-05-20T15:00:00Z"),
]

sym=S.get(BASE+"/api/platform/spot/market-v2/web/symbolsV2",timeout=30); sym.raise_for_status()
usdt=(((sym.json().get("data") or {}).get("symbols") or {}).get("USDT") or [])

def choose(base):
    rows=[x for x in usdt if str(x.get("vn","")).upper()==base.upper()]
    rows=sorted(rows,key=lambda x:(0 if x.get("sts")==1 else 1,x.get("srt",10**9),str(x.get("id",""))))
    if not rows:return None
    return rows[0]

bases=sorted(set(["BTC"]+[x[0] for x in EVENTS]))
bindings={b:choose(b) for b in bases}
missing_bindings=[b for b,v in bindings.items() if v is None]

indexes={}
for base,row in bindings.items():
    if row is None:continue
    fp=f"SPOT2/kline/{row['id']}/daily/Min15/"
    r=S.get(BASE+"/file-svc/history/download",params={"filePath":fp},timeout=30); r.raise_for_status()
    indexes[base]={x["fileName"]:x for x in (r.json().get("data") or [])}

cache={}
def bucket(ts_ms):
    dt=datetime.fromtimestamp(ts_ms/1000,tz=timezone.utc)+timedelta(hours=8)
    return dt.date().isoformat()

def daymap(base,date):
    k=(base,date)
    if k in cache:return cache[k]
    row=bindings.get(base)
    if row is None: cache[k]=None; return None
    fn=f"{base}_USDT-Min15-{date}.csv"
    rec=indexes.get(base,{}).get(fn)
    if not rec:
        # file names sometimes use canonical vn; search suffix by date
        arr=[v for n,v in indexes.get(base,{}).items() if n.endswith(f"-Min15-{date}.csv")]
        rec=arr[0] if len(arr)==1 else None
    if not rec:cache[k]=None;return None
    rr=S.get(rec["maskedUrl"],timeout=30);rr.raise_for_status()
    mp={}
    for z in csv.DictReader(io.StringIO(rr.text)):
        try:mp[int(z["open_time"])]=float(z["open"])
        except:pass
    cache[k]=mp;return mp

def p_at(base,ts):
    mp=daymap(base,bucket(ts))
    return None if mp is None else mp.get(ts)

def ms(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
Q=15*60*1000
def ceil15(t):return ((t+Q-1)//Q)*Q
def rel(a0,a1,b0,b1):return math.log(a1/a0)-math.log(b1/b0)

ledger=[]
for base,t0s in EVENTS:
    t0=ms(t0s); entry=ceil15(t0)
    times={"entry":entry,"1h":entry+3600_000,"6h":entry+6*3600_000,"24h":entry+24*3600_000}
    rec={"symbol":base,"listing_t0":t0s,"entry_15m":datetime.fromtimestamp(entry/1000,tz=timezone.utc).isoformat()}
    vals={}
    for k,t in times.items():
        vals[f"project_{k}"]=p_at(base,t)
        vals[f"btc_{k}"]=p_at("BTC",t)
    rec.update(vals)
    rec["analyzable"]=all(v is not None for v in vals.values())
    if rec["analyzable"]:
        for h in ["1h","6h","24h"]:
            rec[f"rel_{h}"]=rel(vals["project_entry"],vals[f"project_{h}"],vals["btc_entry"],vals[f"btc_{h}"])
        rec["project_raw_24h"]=math.log(vals["project_24h"]/vals["project_entry"])
        rec["btc_raw_24h"]=math.log(vals["btc_24h"]/vals["btc_entry"])
    else:
        rec["missing"]=[k for k,v in vals.items() if v is None]
    ledger.append(rec)

vals=np.array([x["rel_24h"] for x in ledger if x["analyzable"]],dtype=float)
N=len(vals); neg=int((vals<0).sum()) if N else 0
mean=float(vals.mean()) if N else None
median=float(np.median(vals)) if N else None
negfrac=float(neg/N) if N else None
sign_p=sum(math.comb(N,k) for k in range(neg,N+1))/(2**N) if N else None
rng=np.random.default_rng(20261008)
if N:
    boot=np.array([rng.choice(vals,size=N,replace=True).mean() for _ in range(10000)])
    ci90=[float(np.quantile(boot,.05)),float(np.quantile(boot,.95))]
    loo=[float(np.delete(vals,i).mean()) for i in range(N)] if N>1 else [float(vals[0])]
    loo_max=max(loo)
    concentration=float(np.max(np.abs(vals))/np.sum(np.abs(vals))) if np.sum(np.abs(vals)) else None
else:
    ci90=[None,None];loo_max=None;concentration=None

def yr(y):
    a=[x["rel_24h"] for x in ledger if x["analyzable"] and x["listing_t0"].startswith(str(y))]
    return {"n":len(a),"mean":float(np.mean(a)) if a else None,"median":float(np.median(a)) if a else None}

gates={
 "n_ge_10":N>=10,
 "median_lt_0":median is not None and median<0,
 "negative_fraction_gt_0_5":negfrac is not None and negfrac>0.5,
 "sign_p_lt_0_10":sign_p is not None and sign_p<0.10,
 "bootstrap_90_upper_lt_0":ci90[1] is not None and ci90[1]<0,
 "loo_max_mean_lt_0":loo_max is not None and loo_max<0,
 "largest_abs_share_le_0_40":concentration is not None and concentration<=0.40,
}
summary={
 "protocol":"MLRTS-V0.1-DISCOVERY-FROZEN-2026-10-08",
 "authenticated":False,"orders":False,"exchange_mutation":False,
 "market_source":"MEXC official public history CSV files",
 "file_bucket_rule":"date(UTC timestamp + 8h)",
 "planned_events":len(EVENTS),"missing_symbol_bindings":missing_bindings,
 "bindings":{k:(None if v is None else {"id":v.get("id"),"vn":v.get("vn"),"sts":v.get("sts")}) for k,v in bindings.items()},
 "N":N,"negative_count":neg,"mean_rel_24h":mean,"median_rel_24h":median,
 "negative_fraction":negfrac,"sign_test_one_sided_p":sign_p,
 "bootstrap_90_ci_mean":ci90,"leave_one_out_max_mean":loo_max,
 "largest_abs_observation_share":concentration,
 "year_2025":yr(2025),"year_2026":yr(2026),
 "gates":gates,
 "classification":"SELLPRESSURE_DISCOVERY_SURVIVES" if all(gates.values()) else ("MARKET_DATA_INSUFFICIENT" if N<10 else "NO_EDGE_DISCOVERY"),
}
with open(f"{OUT}/ledger.json","w") as f:json.dump(ledger,f,indent=2)
with open(f"{OUT}/summary.json","w") as f:json.dump(summary,f,indent=2)
print(json.dumps(summary,indent=2))

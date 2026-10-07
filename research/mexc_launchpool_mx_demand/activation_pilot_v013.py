import requests,csv,io,math,json,os
from datetime import datetime,timezone,timedelta
import numpy as np

OUT="artifacts/mexc_launchpool_mx_demand_activation_pilot_v013"
os.makedirs(OUT,exist_ok=True)
BASE="https://www.mexc.com"
S=requests.Session(); S.headers.update({"User-Agent":"Mozilla/5.0 (CryptoLab research)"})

EVENTS=[
("APT","2025-01-23T10:00:00Z"),("IP","2025-02-12T10:00:00Z"),
("TERM","2025-03-25T11:00:00Z"),("K","2025-03-28T10:00:00Z"),
("MNT","2025-03-31T14:00:00Z"),("EPT","2025-04-21T12:00:00Z"),
("SHM","2025-05-02T11:00:00Z"),("ICEBERG","2025-05-20T11:00:00Z"),
("BOMB","2025-06-13T10:00:00Z"),("EURR","2025-07-24T11:00:00Z"),
("USDR","2025-07-28T11:00:00Z"),("EIN2","2025-08-04T10:00:00Z"),
("EMBLEM","2026-04-15T13:00:00Z"),("NEX","2026-05-20T13:00:00Z")
]

# Deterministic public symbol binding
sym=S.get(BASE+"/api/platform/spot/market-v2/web/symbolsV2",timeout=30); sym.raise_for_status()
usdt=(((sym.json().get("data") or {}).get("symbols") or {}).get("USDT") or [])
def choose(base):
    rows=[x for x in usdt if str(x.get("vn","")).upper()==base]
    rows=sorted(rows,key=lambda x:(0 if x.get("sts")==1 else 1,x.get("srt",10**9),str(x.get("id",""))))
    if not rows: raise RuntimeError("NO_SYMBOL_"+base)
    return rows[0]

bindings={"MX_USDT":choose("MX"),"BTC_USDT":choose("BTC")}

# Official history file indexes
indexes={}
for market,row in bindings.items():
    file_path=f"SPOT2/kline/{row['id']}/daily/Min15/"
    r=S.get(BASE+"/file-svc/history/download",params={"filePath":file_path},timeout=30); r.raise_for_status()
    data=(r.json().get("data") or [])
    indexes[market]={x["fileName"]:x for x in data}
    print("INDEX",market,"files",len(data),"id",row["id"])

cache={}
def day_map(market,date_s):
    key=(market,date_s)
    if key in cache:return cache[key]
    fn=f"{market}-Min15-{date_s}.csv"
    rec=indexes[market].get(fn)
    if not rec:
        cache[key]=None
        return None
    rr=S.get(rec["maskedUrl"],timeout=30); rr.raise_for_status()
    reader=csv.DictReader(io.StringIO(rr.text))
    out={}
    for row in reader:
        try: out[int(row["open_time"])]=float(row["open"])
        except Exception: pass
    cache[key]=out
    return out

def price_at(market,ts_ms):
    dt=datetime.fromtimestamp(ts_ms/1000,tz=timezone.utc)
    mp=day_map(market,dt.date().isoformat())
    return None if mp is None else mp.get(ts_ms)

def ms(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
def rel(mx0,mx1,b0,b1): return math.log(mx1/mx0)-math.log(b1/b0)

ledger=[]
for name,t0s in EVENTS:
    t0=ms(t0s)
    need={"1h":t0+3600_000,"6h":t0+6*3600_000,"24h":t0+24*3600_000}
    rec={"event":name,"t0":t0s}
    mx0=price_at("MX_USDT",t0); b0=price_at("BTC_USDT",t0)
    vals={"mx_entry":mx0,"btc_entry":b0}
    for k,t in need.items():
        vals[f"mx_{k}"]=price_at("MX_USDT",t)
        vals[f"btc_{k}"]=price_at("BTC_USDT",t)
    rec.update(vals)
    rec["analyzable"]=all(v is not None for v in vals.values())
    if rec["analyzable"]:
        for k in ["1h","6h","24h"]:
            rec[f"rel_{k}"]=rel(mx0,rec[f"mx_{k}"],b0,rec[f"btc_{k}"])
        rec["mx_raw_24h"]=math.log(rec["mx_24h"]/mx0)
        rec["btc_raw_24h"]=math.log(rec["btc_24h"]/b0)
    else:
        rec["missing"]=[k for k,v in vals.items() if v is None]
    ledger.append(rec)

vals=np.array([x["rel_24h"] for x in ledger if x["analyzable"]],dtype=float)
N=len(vals); wins=int((vals>0).sum()) if N else 0
mean=float(vals.mean()) if N else None
median=float(np.median(vals)) if N else None
posfrac=float(wins/N) if N else None
sign_p=sum(math.comb(N,k) for k in range(wins,N+1))/(2**N) if N else None
rng=np.random.default_rng(20261007)
if N:
    boot=np.array([rng.choice(vals,size=N,replace=True).mean() for _ in range(10000)])
    ci90=[float(np.quantile(boot,.05)),float(np.quantile(boot,.95))]
    loo=[float(np.delete(vals,i).mean()) for i in range(N)] if N>1 else [float(vals[0])]
    loo_min=min(loo)
else:
    ci90=[None,None]; loo_min=None

def yr(y):
    a=[x["rel_24h"] for x in ledger if x["analyzable"] and x["t0"].startswith(str(y))]
    return {"n":len(a),"mean":float(np.mean(a)) if a else None,"median":float(np.median(a)) if a else None}

gates={
 "n_ge_10":N>=10,
 "median_gt_0":median is not None and median>0,
 "positive_fraction_gt_0_5":posfrac is not None and posfrac>0.5,
 "sign_p_lt_0_10":sign_p is not None and sign_p<0.10,
 "loo_min_mean_gt_0":loo_min is not None and loo_min>0
}
summary={
 "protocol":"MLMXD-ACTIVATION-PILOT-V0.1.3-OFFICIAL-HISTORY-FILES",
 "authenticated":False,"orders":False,"exchange_mutation":False,
 "market_source":"MEXC official public history CSV files",
 "symbol_bindings":{k:{"id":v["id"],"vn":v.get("vn")} for k,v in bindings.items()},
 "N":N,"wins":wins,"mean_rel_24h":mean,"median_rel_24h":median,
 "positive_fraction":posfrac,"sign_test_one_sided_p":sign_p,
 "bootstrap_90_ci_mean":ci90,"leave_one_out_min_mean":loo_min,
 "year_2025":yr(2025),"year_2026":yr(2026),"gates":gates,
 "classification":"PILOT_SIGNAL_PRESENT" if all(gates.values()) else "PILOT_NO_SIGNAL",
 "promotion_credit":"ZERO",
 "science_changed":False
}
with open(f"{OUT}/ledger.json","w") as f: json.dump(ledger,f,indent=2)
with open(f"{OUT}/summary.json","w") as f: json.dump(summary,f,indent=2)
print(json.dumps(summary,indent=2))

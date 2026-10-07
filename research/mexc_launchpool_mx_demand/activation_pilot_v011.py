import requests, math, json, os
from datetime import datetime
import numpy as np

OUT="artifacts/mexc_launchpool_mx_demand_activation_pilot_v011"
os.makedirs(OUT,exist_ok=True)
BASE="https://api.mexc.com/api/v3/klines"
EVENTS=[
("APT","2025-01-23T10:00:00Z"),("IP","2025-02-12T10:00:00Z"),
("TERM","2025-03-25T11:00:00Z"),("K","2025-03-28T10:00:00Z"),
("MNT","2025-03-31T14:00:00Z"),("EPT","2025-04-21T12:00:00Z"),
("SHM","2025-05-02T11:00:00Z"),("ICEBERG","2025-05-20T11:00:00Z"),
("BOMB","2025-06-13T10:00:00Z"),("EURR","2025-07-24T11:00:00Z"),
("USDR","2025-07-28T11:00:00Z"),("EIN2","2025-08-04T10:00:00Z"),
("EMBLEM","2026-04-15T13:00:00Z"),("NEX","2026-05-20T13:00:00Z")]

def ms(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
def get_map(symbol,t0):
    params={"symbol":symbol,"interval":"15m","startTime":t0,"endTime":t0+24*3600_000+15*60_000,"limit":1000}
    r=requests.get(BASE,params=params,timeout=30); r.raise_for_status()
    rows=r.json()
    return {int(x[0]):float(x[1]) for x in rows}, r.url

def rel(a,b,c,d): return math.log(b/a)-math.log(d/c)

ledger=[]
for name,t0s in EVENTS:
    t0=ms(t0s)
    mx,mxurl=get_map("MXUSDT",t0); bt,bturl=get_map("BTCUSDT",t0)
    need={"1h":t0+3600_000,"6h":t0+6*3600_000,"24h":t0+24*3600_000}
    rec={"event":name,"t0":t0s,"mx_query":mxurl,"btc_query":bturl}
    ok=t0 in mx and t0 in bt and all(t in mx and t in bt for t in need.values())
    rec["analyzable"]=ok
    if ok:
        rec["mx_entry"]=mx[t0]; rec["btc_entry"]=bt[t0]
        for k,t in need.items():
            rec[f"mx_{k}"]=mx[t]; rec[f"btc_{k}"]=bt[t]
            rec[f"rel_{k}"]=rel(mx[t0],mx[t],bt[t0],bt[t])
        rec["mx_raw_24h"]=math.log(mx[need["24h"]]/mx[t0])
        rec["btc_raw_24h"]=math.log(bt[need["24h"]]/bt[t0])
    else:
        rec["missing"]={
          "mx_entry":t0 not in mx,"btc_entry":t0 not in bt,
          **{f"mx_{k}":t not in mx for k,t in need.items()},
          **{f"btc_{k}":t not in bt for k,t in need.items()}}
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

gates={"n_ge_10":N>=10,"median_gt_0":median is not None and median>0,
"positive_fraction_gt_0_5":posfrac is not None and posfrac>0.5,
"sign_p_lt_0_10":sign_p is not None and sign_p<0.10,
"loo_min_mean_gt_0":loo_min is not None and loo_min>0}
summary={"protocol":"MLMXD-ACTIVATION-PILOT-V0.1.1-TRANSPORT-REMEDIATION",
"parent_incomplete_run":37624255115,"authenticated":False,"orders":False,"exchange_mutation":False,
"N":N,"wins":wins,"mean_rel_24h":mean,"median_rel_24h":median,"positive_fraction":posfrac,
"sign_test_one_sided_p":sign_p,"bootstrap_90_ci_mean":ci90,"leave_one_out_min_mean":loo_min,
"year_2025":yr(2025),"year_2026":yr(2026),"gates":gates,
"classification":"PILOT_SIGNAL_PRESENT" if all(gates.values()) else "PILOT_NO_SIGNAL","promotion_credit":"ZERO"}
json.dump(ledger,open(f"{OUT}/ledger.json","w"),indent=2)
json.dump(summary,open(f"{OUT}/summary.json","w"),indent=2)
print(json.dumps(summary,indent=2))

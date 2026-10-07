import ccxt, math, json, os, time
from datetime import datetime, timezone
import numpy as np

OUT="artifacts/mexc_launchpool_mx_demand_activation_pilot_v01"
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
("EIN2","2025-08-04T10:00:00Z"),
("EMBLEM","2026-04-15T13:00:00Z"),
("NEX","2026-05-20T13:00:00Z"),
]

ex=ccxt.mexc({"enableRateLimit":True})
markets=ex.load_markets()
assert "MX/USDT" in markets and "BTC/USDT" in markets

def ms(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)

def fetch_map(symbol,start_ms):
    rows=ex.fetch_ohlcv(symbol,"15m",since=start_ms,limit=120)
    return {int(r[0]):float(r[1]) for r in rows}

def relret(mx0,mx1,bt0,bt1):
    return math.log(mx1/mx0)-math.log(bt1/bt0)

ledger=[]
for name,t0s in EVENTS:
    t0=ms(t0s)
    # T0 values are exact quarter-hour in the frozen event list.
    entry=t0
    mx=fetch_map("MX/USDT",entry)
    bt=fetch_map("BTC/USDT",entry)
    rec={"event":name,"t0":t0s,"entry_ms":entry}
    needed={"1h":entry+3600_000,"6h":entry+6*3600_000,"24h":entry+24*3600_000}
    if entry not in mx or entry not in bt or any(t not in mx or t not in bt for t in needed.values()):
        rec["analyzable"]=False
        rec["missing"]={
          "mx_entry":entry not in mx,"btc_entry":entry not in bt,
          **{f"mx_{k}":t not in mx for k,t in needed.items()},
          **{f"btc_{k}":t not in bt for k,t in needed.items()},
        }
    else:
        rec["analyzable"]=True
        rec["mx_entry"]=mx[entry]; rec["btc_entry"]=bt[entry]
        for k,t in needed.items():
            rec[f"mx_{k}"]=mx[t]; rec[f"btc_{k}"]=bt[t]
            rec[f"rel_{k}"]=relret(mx[entry],mx[t],bt[entry],bt[t])
        rec["mx_raw_24h"]=math.log(mx[needed["24h"]]/mx[entry])
        rec["btc_raw_24h"]=math.log(bt[needed["24h"]]/bt[entry])
    ledger.append(rec)
    time.sleep(0.15)

vals=np.array([x["rel_24h"] for x in ledger if x.get("analyzable")],dtype=float)
N=len(vals)
wins=int((vals>0).sum()) if N else 0
mean=float(vals.mean()) if N else None
median=float(np.median(vals)) if N else None
posfrac=float(wins/N) if N else None

# exact one-sided sign test P(X>=wins), X~Binom(N,0.5)
sign_p=sum(math.comb(N,k) for k in range(wins,N+1))/(2**N) if N else None

rng=np.random.default_rng(20261007)
if N:
    boot=np.array([rng.choice(vals,size=N,replace=True).mean() for _ in range(10000)])
    ci90=[float(np.quantile(boot,0.05)),float(np.quantile(boot,0.95))]
    loo=[float(np.delete(vals,i).mean()) for i in range(N)] if N>1 else [float(vals[0])]
    loo_min=min(loo)
else:
    ci90=[None,None]; loo_min=None

def by_year(year):
    arr=[x["rel_24h"] for x in ledger if x.get("analyzable") and x["t0"].startswith(str(year))]
    return {"n":len(arr),"mean":float(np.mean(arr)) if arr else None,"median":float(np.median(arr)) if arr else None}

gates={
 "n_ge_10":N>=10,
 "median_gt_0":bool(median is not None and median>0),
 "positive_fraction_gt_0_5":bool(posfrac is not None and posfrac>0.5),
 "sign_p_lt_0_10":bool(sign_p is not None and sign_p<0.10),
 "loo_min_mean_gt_0":bool(loo_min is not None and loo_min>0),
}
classification="PILOT_SIGNAL_PRESENT" if all(gates.values()) else "PILOT_NO_SIGNAL"

summary={
 "protocol":"MEXC-LAUNCHPOOL-MX-DEMAND-001-ACTIVATION-PILOT-V0.1",
 "authenticated":False,
 "orders":False,
 "exchange_mutation":False,
 "market_source":"MEXC public spot OHLCV via ccxt",
 "N":N,
 "wins":wins,
 "mean_rel_24h":mean,
 "median_rel_24h":median,
 "positive_fraction":posfrac,
 "sign_test_one_sided_p":sign_p,
 "bootstrap_90_ci_mean":ci90,
 "leave_one_out_min_mean":loo_min,
 "year_2025":by_year(2025),
 "year_2026":by_year(2026),
 "gates":gates,
 "classification":classification,
 "promotion_credit":"ZERO",
}

with open(f"{OUT}/ledger.json","w") as f: json.dump(ledger,f,indent=2)
with open(f"{OUT}/summary.json","w") as f: json.dump(summary,f,indent=2)
print(json.dumps(summary,indent=2))

#!/usr/bin/env python3
import csv, io, json, math, random, statistics, hashlib, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
YEAR=2025
NY=ZoneInfo("America/New_York")
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/usopen_persist_001_2025_oos_receipt.json")

HOLIDAYS={
"2025-01-01","2025-01-09","2025-01-20","2025-02-17","2025-04-18",
"2025-05-26","2025-06-19","2025-07-04","2025-09-01","2025-11-27","2025-12-25"
}

def median(xs): return statistics.median(xs) if xs else float("nan")
def pct(xs,p):
    ys=sorted(xs)
    if not ys: return float("nan")
    k=(len(ys)-1)*p
    f=math.floor(k); c=math.ceil(k)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)

def fetch_month(symbol,month):
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/5m/{symbol}-5m-{YEAR}-{month:02d}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-USOPEN-PERSIST-001/1.0"})
    with urllib.request.urlopen(req,timeout=90) as r:
        raw=r.read()
    sha=hashlib.sha256(raw).hexdigest()
    rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name=z.namelist()[0]
        with io.TextIOWrapper(z.open(name),encoding="utf-8") as txt:
            for row in csv.reader(txt):
                if not row or not row[0].isdigit(): continue
                rows.append({"t":int(row[0]),"c":float(row[4]),"v":float(row[5])})
    return rows,{"url":url,"sha256":sha,"rows":len(rows),"month":month}

def load_symbol(symbol):
    rows=[]; prov=[]
    for m in range(1,13):
        rs,p=fetch_month(symbol,m)
        rows.extend(rs); prov.append(p)
    rows.sort(key=lambda x:x["t"])
    ded=[]; seen=set()
    for r in rows:
        if r["t"] in seen: continue
        seen.add(r["t"]); ded.append(r)
    return ded,prov

def local_dt(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).astimezone(NY)

def eligible_date(d):
    return d.year==YEAR and d.weekday()<5 and d.isoformat() not in HOLIDAYS

def calc(rows):
    bydate=defaultdict(list)
    for r in rows:
        dt=local_dt(r["t"])
        if eligible_date(dt.date()):
            x=dict(r); x["dt"]=dt
            bydate[dt.date()].append(x)

    obs=[]; exc={"zero_rv":0,"gaps":0,"missing_clock_bars":0}
    wanted=[time(8,55),
            time(9,0),time(9,5),time(9,10),time(9,15),time(9,20),time(9,25),
            time(9,30),time(9,35),time(9,40),time(9,45),time(9,50),time(9,55),
            time(10,0),time(10,5),time(10,10),time(10,15),time(10,20),time(10,25),
            time(10,30),time(10,35),time(10,40),time(10,45),time(10,50),time(10,55)]
    pre=[time(9,0),time(9,5),time(9,10),time(9,15),time(9,20),time(9,25)]
    opn=[time(9,30),time(9,35),time(9,40),time(9,45),time(9,50),time(9,55)]
    persist=[time(10,0),time(10,5),time(10,10),time(10,15),time(10,20),time(10,25)]
    decay=[time(10,30),time(10,35),time(10,40),time(10,45),time(10,50),time(10,55)]

    for d,day in sorted(bydate.items()):
        day.sort(key=lambda x:x["t"])
        idx={x["dt"].time().replace(second=0,microsecond=0):i for i,x in enumerate(day)}
        if not all(t in idx for t in wanted):
            exc["missing_clock_bars"]+=1; continue
        seq=[day[idx[t]] for t in wanted]
        if any(seq[i+1]["t"]-seq[i]["t"]!=300000 for i in range(len(seq)-1)):
            exc["gaps"]+=1; continue

        ret={}
        for t in wanted[1:]:
            i=idx[t]
            if i<=0 or day[i]["t"]-day[i-1]["t"]!=300000:
                ret={}; break
            ret[t]=math.log(day[i]["c"]/day[i-1]["c"])
        if not ret:
            exc["gaps"]+=1; continue

        def rv(ts): return sum(ret[t]*ret[t] for t in ts)
        rv_pre,rv_open,rv_persist,rv_decay=rv(pre),rv(opn),rv(persist),rv(decay)
        if min(rv_pre,rv_open,rv_persist)<=0:
            exc["zero_rv"]+=1; continue

        pre_vol=sum(day[idx[t]]["v"] for t in pre)
        persist_vol=sum(day[idx[t]]["v"] for t in persist)

        obs.append({
            "date":d.isoformat(),
            "log_open_pre":math.log(rv_open/rv_pre),
            "log_persist_pre":math.log(rv_persist/rv_pre),
            "log_persist_open":math.log(rv_persist/rv_open),
            "log_decay_pre":math.log(rv_decay/rv_pre) if rv_decay>0 else None,
            "volume_persist_pre":persist_vol/pre_vol if pre_vol>0 else None
        })
    return obs,exc

def cluster_ci(obs,key,seed):
    bydate=defaultdict(list)
    for o in obs: bydate[o["date"]].append(o[key])
    dates=sorted(bydate)
    rng=random.Random(seed); vals=[]
    for _ in range(5000):
        xs=[]
        for __ in dates:
            d=dates[rng.randrange(len(dates))]
            xs.extend(bydate[d])
        vals.append(median(xs))
    return [math.exp(pct(vals,.025)),math.exp(pct(vals,.975))]

def main():
    allobs=[]; prov=[]; symbols={}; exclusions={}
    for s in SYMBOLS:
        rows,p=load_symbol(s)
        obs,exc=calc(rows)
        for o in obs: o["symbol"]=s
        allobs.extend(obs); prov.extend([{"symbol":s,**x} for x in p])
        symbols[s]={"rows":len(rows),"symbol_days":len(obs)}
        exclusions[s]=exc

    def ratio(key):
        return math.exp(median([o[key] for o in allobs]))

    per_symbol={}
    for s in SYMBOLS:
        xs=[o for o in allobs if o["symbol"]==s]
        per_symbol[s]={
            "n":len(xs),
            "median_open_pre_ratio":math.exp(median([x["log_open_pre"] for x in xs])) if xs else None,
            "median_persist_pre_ratio":math.exp(median([x["log_persist_pre"] for x in xs])) if xs else None,
            "median_persist_open_ratio":math.exp(median([x["log_persist_open"] for x in xs])) if xs else None,
            "median_volume_persist_pre_ratio":median([x["volume_persist_pre"] for x in xs if x["volume_persist_pre"] is not None]) if xs else None,
            "median_decay_pre_ratio":math.exp(median([x["log_decay_pre"] for x in xs if x["log_decay_pre"] is not None])) if xs else None
        }

    result={
        "symbol_days":len(allobs),
        "distinct_dates":len(set(o["date"] for o in allobs)),
        "pooled_median_open_pre_ratio":ratio("log_open_pre"),
        "bootstrap95_open_pre_ratio":cluster_ci(allobs,"log_open_pre",20260928),
        "pooled_median_persist_pre_ratio":ratio("log_persist_pre"),
        "bootstrap95_persist_pre_ratio":cluster_ci(allobs,"log_persist_pre",20260929),
        "pooled_median_persist_open_ratio":ratio("log_persist_open"),
        "bootstrap95_persist_open_ratio":cluster_ci(allobs,"log_persist_open",20260930),
        "symbols_persist_pre_median_gt_1_10":sum(1 for v in per_symbol.values() if v["median_persist_pre_ratio"] is not None and v["median_persist_pre_ratio"]>1.10),
        "pooled_median_decay_pre_ratio":math.exp(median([o["log_decay_pre"] for o in allobs if o["log_decay_pre"] is not None])),
        "per_symbol":per_symbol
    }

    enough=result["symbol_days"]>=1400
    passed=bool(
        enough and
        result["pooled_median_open_pre_ratio"]>=1.20 and
        result["bootstrap95_open_pre_ratio"][0]>1.05 and
        result["pooled_median_persist_pre_ratio"]>=1.20 and
        result["bootstrap95_persist_pre_ratio"][0]>1.05 and
        result["symbols_persist_pre_median_gt_1_10"]>=4
    )
    result["pass"]=passed
    result["classification"]="OOS_2025_PERSISTENCE_SURVIVES" if passed else ("INSUFFICIENT_SAMPLE" if not enough else "OOS_2025_PERSISTENCE_FAILS")

    receipt={
        "lab_id":"USOPEN-PERSIST-001",
        "scope":"2025_OOS_ONLY",
        "oos":result,
        "symbols":symbols,
        "exclusions":exclusions,
        "provenance":prov,
        "terminal_state":result["classification"],
        "protected_periods_opened":["2025"],
        "protected_periods_remaining_sealed":["2026"],
        "directional_returns_computed":False,
        "pnl_computed":False,
        "live_execution":False,
        "merge_to_main":False
    }
    receipt["source_bundle_sha256"]=hashlib.sha256("".join(x["sha256"] for x in prov).encode()).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"terminal_state":receipt["terminal_state"],"oos":result,"remaining_sealed":["2026"]},indent=2,allow_nan=False))

if __name__=="__main__":
    main()

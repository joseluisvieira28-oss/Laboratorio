#!/usr/bin/env python3
import csv, io, json, math, random, statistics, hashlib, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, date, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
NY=ZoneInfo("America/New_York")
ROOT=Path("Dream-Account-OS-v2.3-PARTIAL")
PARENT_RECEIPT=ROOT/"runtime/usopen_vol_001_discovery_receipt.json"
OUT=ROOT/"runtime/usopen_vol_002_postetf_2024_receipt.json"

HOLIDAYS={
"2022-01-17","2022-02-21","2022-04-15","2022-05-30","2022-06-20","2022-07-04","2022-09-05","2022-11-24","2022-12-26",
"2023-01-02","2023-01-16","2023-02-20","2023-04-07","2023-05-29","2023-06-19","2023-07-04","2023-09-04","2023-11-23","2023-12-25",
"2024-01-01","2024-01-15","2024-02-19","2024-03-29","2024-05-27","2024-06-19","2024-07-04","2024-09-02","2024-11-28","2024-12-25"
}

BASE_START=date(2022,1,1)
BASE_END=date(2023,12,31)
POST_START=date(2024,1,11)
POST_END=date(2024,12,31)

def median(xs): return statistics.median(xs) if xs else float("nan")
def pct(xs,p):
    ys=sorted(xs)
    if not ys: return float("nan")
    k=(len(ys)-1)*p
    f=math.floor(k); c=math.ceil(k)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)

def fetch_month(symbol,year,month):
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/5m/{symbol}-5m-{year}-{month:02d}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-USOPEN-VOL-002/1.0"})
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
    return rows,{"url":url,"sha256":sha,"rows":len(rows),"year":year,"month":month}

def load_symbol(symbol):
    rows=[]; prov=[]
    for y in (2022,2023,2024):
        for m in range(1,13):
            rs,p=fetch_month(symbol,y,m)
            rows.extend(rs); prov.append(p)
    rows.sort(key=lambda x:x["t"])
    ded=[]; seen=set()
    for r in rows:
        if r["t"] in seen: continue
        seen.add(r["t"]); ded.append(r)
    return ded,prov

def local_dt(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).astimezone(NY)

def eligible_date(d,start,end):
    return start<=d<=end and d.weekday()<5 and d.isoformat() not in HOLIDAYS

def calc(rows,start,end):
    bydate=defaultdict(list)
    for r in rows:
        dt=local_dt(r["t"])
        if eligible_date(dt.date(),start,end):
            x=dict(r); x["dt"]=dt
            bydate[dt.date()].append(x)
    obs=[]; excluded={"zero_rv":0,"gaps":0,"missing_clock_bars":0}
    wanted=[time(8,55),time(9,0),time(9,5),time(9,10),time(9,15),time(9,20),time(9,25),
            time(9,30),time(9,35),time(9,40),time(9,45),time(9,50),time(9,55),
            time(10,0),time(10,5),time(10,10),time(10,15),time(10,20),time(10,25)]
    pre_times=[time(9,0),time(9,5),time(9,10),time(9,15),time(9,20),time(9,25)]
    opn_times=[time(9,30),time(9,35),time(9,40),time(9,45),time(9,50),time(9,55)]
    post_times=[time(10,0),time(10,5),time(10,10),time(10,15),time(10,20),time(10,25)]
    for d,day in sorted(bydate.items()):
        day.sort(key=lambda x:x["t"])
        idx={x["dt"].time().replace(second=0,microsecond=0):i for i,x in enumerate(day)}
        if not all(t in idx for t in wanted):
            excluded["missing_clock_bars"]+=1; continue
        seq=[day[idx[t]] for t in wanted]
        if any(seq[i+1]["t"]-seq[i]["t"]!=300000 for i in range(len(seq)-1)):
            excluded["gaps"]+=1; continue
        ret={}
        for t in wanted[1:]:
            i=idx[t]
            if i<=0 or day[i]["t"]-day[i-1]["t"]!=300000:
                ret={}; break
            ret[t]=math.log(day[i]["c"]/day[i-1]["c"])
        if not ret:
            excluded["gaps"]+=1; continue
        pre=sum(ret[t]*ret[t] for t in pre_times)
        opn=sum(ret[t]*ret[t] for t in opn_times)
        post=sum(ret[t]*ret[t] for t in post_times)
        if pre<=0 or opn<=0 or post<=0:
            excluded["zero_rv"]+=1; continue
        pre_vol=sum(day[idx[t]]["v"] for t in pre_times)
        opn_vol=sum(day[idx[t]]["v"] for t in opn_times)
        obs.append({
            "date":d.isoformat(),
            "rv_pre":pre,"rv_open":opn,"rv_post":post,
            "log_open_pre":math.log(opn/pre),
            "log_open_post":math.log(opn/post),
            "volume_open_pre":opn_vol/pre_vol if pre_vol>0 else None
        })
    return obs,excluded

def cluster_bootstrap_ratio(observations,key,reps,seed):
    bydate=defaultdict(list)
    for o in observations: bydate[o["date"]].append(o[key])
    dates=sorted(bydate)
    rng=random.Random(seed); vals=[]
    for _ in range(reps):
        xs=[]
        for __ in dates:
            d=dates[rng.randrange(len(dates))]
            xs.extend(bydate[d])
        vals.append(median(xs))
    return [math.exp(pct(vals,.025)),math.exp(pct(vals,.975))]

def structural_bootstrap_factor(base,post,reps=5000,seed=20260926):
    b=defaultdict(list); p=defaultdict(list)
    for o in base: b[o["date"]].append(o["log_open_pre"])
    for o in post: p[o["date"]].append(o["log_open_pre"])
    bd=sorted(b); pd=sorted(p)
    rng=random.Random(seed); vals=[]
    for _ in range(reps):
        bx=[]; px=[]
        for __ in bd:
            d=bd[rng.randrange(len(bd))]; bx.extend(b[d])
        for __ in pd:
            d=pd[rng.randrange(len(pd))]; px.extend(p[d])
        vals.append(median(px)-median(bx))
    return [math.exp(pct(vals,.025)),math.exp(pct(vals,.975))]

def summarize(obs,seed1,seed2):
    bysym={}
    for s in SYMBOLS:
        xs=[o for o in obs if o["symbol"]==s]
        bysym[s]={
            "n":len(xs),
            "median_open_pre_ratio":math.exp(median([x["log_open_pre"] for x in xs])) if xs else None,
            "median_open_post_ratio":math.exp(median([x["log_open_post"] for x in xs])) if xs else None,
            "median_volume_open_pre_ratio":median([x["volume_open_pre"] for x in xs if x["volume_open_pre"] is not None]) if xs else None
        }
    return {
        "symbol_days":len(obs),
        "distinct_dates":len(set(o["date"] for o in obs)),
        "pooled_median_open_pre_ratio":math.exp(median([o["log_open_pre"] for o in obs])),
        "pooled_median_open_post_ratio":math.exp(median([o["log_open_post"] for o in obs])),
        "date_cluster_bootstrap95_open_pre_ratio":cluster_bootstrap_ratio(obs,"log_open_pre",5000,seed1),
        "date_cluster_bootstrap95_open_post_ratio":cluster_bootstrap_ratio(obs,"log_open_post",5000,seed2),
        "symbols_open_pre_median_gt_1_10":sum(1 for v in bysym.values() if v["median_open_pre_ratio"] is not None and v["median_open_pre_ratio"]>1.10),
        "per_symbol":bysym
    }

def main():
    parent=json.loads(PARENT_RECEIPT.read_text(encoding="utf-8"))
    receipt={
        "lab_id":"USOPEN-VOL-002",
        "parent_lab_id":"USOPEN-VOL-001",
        "mve_id":"USOV-POSTETF-2024-001",
        "scope":"POSTETF_2024_REPLICATION_ONLY",
        "regime_boundary":{"approval_date":"2024-01-10","first_public_trading_date":"2024-01-11","post_sample_start":"2024-01-11","post_sample_end":"2024-12-31"},
        "symbols":{},"exclusions":{"baseline":{},"postetf_2024":{}},"provenance":{"baseline":[],"postetf_2024":[]}
    }
    base_all=[]; post_all=[]
    for s in SYMBOLS:
        rows,prov=load_symbol(s)
        bobs,bexc=calc(rows,BASE_START,BASE_END)
        pobs,pexc=calc(rows,POST_START,POST_END)
        for o in bobs: o["symbol"]=s
        for o in pobs: o["symbol"]=s
        base_all.extend(bobs); post_all.extend(pobs)
        receipt["symbols"][s]={"rows_2022_2024":len(rows),"baseline_symbol_days":len(bobs),"postetf_2024_symbol_days":len(pobs)}
        receipt["exclusions"]["baseline"][s]=bexc
        receipt["exclusions"]["postetf_2024"][s]=pexc
        for p in prov:
            dst=receipt["provenance"]["baseline"] if p["year"] in (2022,2023) else receipt["provenance"]["postetf_2024"]
            dst.append({"symbol":s,**p})

    base_hash=hashlib.sha256("".join(p["sha256"] for p in receipt["provenance"]["baseline"]).encode()).hexdigest()
    post_hash=hashlib.sha256("".join(p["sha256"] for p in receipt["provenance"]["postetf_2024"]).encode()).hexdigest()
    parent_hash=parent.get("source_bundle_sha256")
    baseline_source_match=(base_hash==parent_hash)

    baseline=summarize(base_all,20260923,20260924)
    post=summarize(post_all,20260925,20260927)

    enough=post["symbol_days"]>=1350
    passed=bool(
        enough and
        post["pooled_median_open_pre_ratio"]>=1.20 and
        post["date_cluster_bootstrap95_open_pre_ratio"][0]>1.05 and
        post["pooled_median_open_post_ratio"]>=1.10 and
        post["date_cluster_bootstrap95_open_post_ratio"][0]>1.00 and
        post["symbols_open_pre_median_gt_1_10"]>=4
    )
    post["pass"]=passed
    post["classification"]="POSTETF_2024_EXACT_REPLICATION_SURVIVES" if passed else ("INSUFFICIENT_SAMPLE" if not enough else "POSTETF_2024_EXACT_REPLICATION_FAILS")

    point_factor=post["pooled_median_open_pre_ratio"]/baseline["pooled_median_open_pre_ratio"]
    if baseline_source_match:
        sci=structural_bootstrap_factor(base_all,post_all)
        structural_class="AMPLIFIED" if sci[0]>1 else ("ATTENUATED" if sci[1]<1 else "NO_DETECTABLE_SHIFT")
    else:
        sci=[None,None]; structural_class="BLOCKED_BASELINE_SOURCE_DRIFT"
    structural={
        "metric":"2024 post-ETF median OPEN/PRE divided by 2022-2023 baseline median OPEN/PRE",
        "point_factor":point_factor,
        "bootstrap95_factor":sci,
        "classification":structural_class,
        "causal_claim":False,
        "baseline_source_bundle_matches_parent":baseline_source_match
    }

    receipt["baseline_recomputed"]=baseline
    receipt["postetf_2024"]=post
    receipt["structural_comparison"]=structural
    receipt["terminal_state"]=post["classification"]
    receipt["baseline_source_bundle_sha256"]=base_hash
    receipt["parent_source_bundle_sha256"]=parent_hash
    receipt["postetf_2024_source_bundle_sha256"]=post_hash
    receipt["protected_periods_opened"]=["2024-01-11/2024-12-31"]
    receipt["protected_periods_remaining_sealed"]=["2025","2026"]
    receipt["directional_returns_computed"]=False
    receipt["pnl_computed"]=False
    receipt["live_execution"]=False
    receipt["merge_to_main"]=False

    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({
        "terminal_state":receipt["terminal_state"],
        "postetf_2024":receipt["postetf_2024"],
        "structural_comparison":receipt["structural_comparison"],
        "remaining_sealed":receipt["protected_periods_remaining_sealed"]
    },indent=2,allow_nan=False))

if __name__=="__main__":
    main()

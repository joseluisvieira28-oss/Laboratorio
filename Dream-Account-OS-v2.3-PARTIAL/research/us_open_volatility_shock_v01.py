#!/usr/bin/env python3
import csv, io, json, math, random, statistics, hashlib, urllib.request, zipfile
from collections import defaultdict
from datetime import datetime, time, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
YEARS=[2022,2023]
MONTHS=range(1,13)
NY=ZoneInfo("America/New_York")
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/usopen_vol_001_discovery_receipt.json")

HOLIDAYS={
"2022-01-17","2022-02-21","2022-04-15","2022-05-30","2022-06-20","2022-07-04","2022-09-05","2022-11-24","2022-12-26",
"2023-01-02","2023-01-16","2023-02-20","2023-04-07","2023-05-29","2023-06-19","2023-07-04","2023-09-04","2023-11-23","2023-12-25"
}

def mean(xs): return sum(xs)/len(xs) if xs else float("nan")
def median(xs): return statistics.median(xs) if xs else float("nan")
def pct(xs,p):
    ys=sorted(xs)
    if not ys: return float("nan")
    k=(len(ys)-1)*p
    f=math.floor(k); c=math.ceil(k)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)

def fetch_month(symbol,year,month):
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/5m/{symbol}-5m-{year}-{month:02d}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-USOPEN-VOL-001/1.0"})
    with urllib.request.urlopen(req,timeout=90) as r:
        raw=r.read()
    sha=hashlib.sha256(raw).hexdigest()
    rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name=z.namelist()[0]
        with io.TextIOWrapper(z.open(name),encoding="utf-8") as txt:
            for row in csv.reader(txt):
                if not row or not row[0].isdigit(): continue
                rows.append({
                    "t":int(row[0]),"o":float(row[1]),"h":float(row[2]),
                    "l":float(row[3]),"c":float(row[4]),"v":float(row[5])
                })
    return rows,{"url":url,"sha256":sha,"rows":len(rows)}

def load_symbol(symbol):
    rows=[]; prov=[]
    for y in YEARS:
        for m in MONTHS:
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

def eligible_date(d):
    return d.weekday()<5 and d.isoformat() not in HOLIDAYS

def calc(rows):
    bydate=defaultdict(list)
    for r in rows:
        dt=local_dt(r["t"])
        if eligible_date(dt.date()):
            x=dict(r); x["dt"]=dt
            bydate[dt.date()].append(x)

    obs=[]; excluded_zero=0; excluded_gap=0; excluded_missing=0
    wanted=[time(8,55),time(9,0),time(9,5),time(9,10),time(9,15),time(9,20),time(9,25),
            time(9,30),time(9,35),time(9,40),time(9,45),time(9,50),time(9,55),
            time(10,0),time(10,5),time(10,10),time(10,15),time(10,20),time(10,25)]
    for d,day in sorted(bydate.items()):
        day.sort(key=lambda x:x["t"])
        idx={x["dt"].time().replace(second=0,microsecond=0):i for i,x in enumerate(day)}
        if not all(t in idx for t in wanted):
            excluded_missing+=1; continue
        seq=[day[idx[t]] for t in wanted]
        if any(seq[i+1]["t"]-seq[i]["t"]!=300000 for i in range(len(seq)-1)):
            excluded_gap+=1; continue

        # returns keyed by bar start; each return uses that bar close vs previous bar close
        ret={}
        for t in wanted[1:]:
            i=idx[t]
            if i<=0 or day[i]["t"]-day[i-1]["t"]!=300000:
                ret={}; break
            ret[t]=math.log(day[i]["c"]/day[i-1]["c"])
        if not ret: excluded_gap+=1; continue

        pre_times=[time(9,0),time(9,5),time(9,10),time(9,15),time(9,20),time(9,25)]
        opn_times=[time(9,30),time(9,35),time(9,40),time(9,45),time(9,50),time(9,55)]
        post_times=[time(10,0),time(10,5),time(10,10),time(10,15),time(10,20),time(10,25)]
        pre=sum(ret[t]*ret[t] for t in pre_times)
        opn=sum(ret[t]*ret[t] for t in opn_times)
        post=sum(ret[t]*ret[t] for t in post_times)
        if pre<=0 or opn<=0 or post<=0:
            excluded_zero+=1; continue

        pre_vol=sum(day[idx[t]]["v"] for t in pre_times)
        opn_vol=sum(day[idx[t]]["v"] for t in opn_times)

        obs.append({
            "date":d.isoformat(),"year":d.year,
            "rv_pre":pre,"rv_open":opn,"rv_post":post,
            "log_open_pre":math.log(opn/pre),
            "log_open_post":math.log(opn/post),
            "volume_open_pre":opn_vol/pre_vol if pre_vol>0 else None
        })
    return obs,{"zero_rv":excluded_zero,"gaps":excluded_gap,"missing_clock_bars":excluded_missing}

def date_cluster_bootstrap(observations,key,reps=5000,seed=20260923):
    bydate=defaultdict(list)
    for o in observations: bydate[o["date"]].append(o[key])
    dates=sorted(bydate)
    rng=random.Random(seed)
    vals=[]
    for _ in range(reps):
        xs=[]
        for __ in dates:
            d=dates[rng.randrange(len(dates))]
            xs.extend(bydate[d])
        vals.append(median(xs))
    return [math.exp(pct(vals,.025)),math.exp(pct(vals,.975))]

def main():
    receipt={
      "lab_id":"USOPEN-VOL-001",
      "mve_id":"USOV-PREETF-001",
      "scope":"DISCOVERY_2022_2023_ONLY",
      "symbols":{},"provenance":[],"exclusions":{}
    }
    allobs=[]
    for s in SYMBOLS:
        rows,prov=load_symbol(s)
        obs,exc=calc(rows)
        for o in obs: o["symbol"]=s
        allobs.extend(obs)
        receipt["symbols"][s]={"rows":len(rows),"symbol_days":len(obs)}
        receipt["exclusions"][s]=exc
        receipt["provenance"].extend([{"symbol":s,**p} for p in prov])

    lop=[o["log_open_pre"] for o in allobs]
    lpost=[o["log_open_post"] for o in allobs]
    med_op=math.exp(median(lop)) if lop else None
    med_post=math.exp(median(lpost)) if lpost else None
    ci_op=date_cluster_bootstrap(allobs,"log_open_pre") if allobs else [None,None]
    ci_post=date_cluster_bootstrap(allobs,"log_open_post",seed=20260924) if allobs else [None,None]

    per_symbol={}
    for s in SYMBOLS:
        xs=[o for o in allobs if o["symbol"]==s]
        per_symbol[s]={
          "n":len(xs),
          "median_open_pre_ratio":math.exp(median([x["log_open_pre"] for x in xs])) if xs else None,
          "median_open_post_ratio":math.exp(median([x["log_open_post"] for x in xs])) if xs else None,
          "median_volume_open_pre_ratio":median([x["volume_open_pre"] for x in xs if x["volume_open_pre"] is not None]) if xs else None
        }

    per_year={}
    for y in YEARS:
        xs=[o for o in allobs if o["year"]==y]
        # date-level median across symbols, then median dates
        byd=defaultdict(list)
        for x in xs: byd[x["date"]].append(x["log_open_pre"])
        dmed=[median(v) for v in byd.values()]
        per_year[str(y)]={
          "symbol_days":len(xs),
          "dates":len(byd),
          "median_open_pre_ratio":math.exp(median(dmed)) if dmed else None
        }

    result={
      "symbol_days":len(allobs),
      "distinct_dates":len(set(o["date"] for o in allobs)),
      "pooled_median_open_pre_ratio":med_op,
      "pooled_median_open_post_ratio":med_post,
      "date_cluster_bootstrap95_open_pre_ratio":ci_op,
      "date_cluster_bootstrap95_open_post_ratio":ci_post,
      "symbols_open_pre_median_gt_1_10":sum(1 for v in per_symbol.values() if v["median_open_pre_ratio"] is not None and v["median_open_pre_ratio"]>1.10),
      "years_open_pre_median_gt_1_05":sum(1 for v in per_year.values() if v["median_open_pre_ratio"] is not None and v["median_open_pre_ratio"]>1.05),
      "per_symbol":per_symbol,
      "per_year":per_year
    }

    enough=len(allobs)>=2700
    passed=bool(
      enough and
      med_op>=1.20 and ci_op[0]>1.05 and
      med_post>=1.10 and ci_post[0]>1.00 and
      result["symbols_open_pre_median_gt_1_10"]>=4 and
      result["years_open_pre_median_gt_1_05"]>=2
    )
    result["pass"]=passed
    result["classification"]="DISCOVERY_MECHANISM_SURVIVES_PREETF_ONLY" if passed else ("INSUFFICIENT_SAMPLE" if not enough else "NO_SIGNAL_PREETF")
    receipt["discovery"]=result
    receipt["terminal_state"]=result["classification"]
    receipt["protected_periods_opened"]=[]
    receipt["directional_returns_computed"]=False
    receipt["pnl_computed"]=False
    receipt["live_execution"]=False
    receipt["merge_to_main"]=False
    bundle="".join(p["sha256"] for p in receipt["provenance"]).encode()
    receipt["source_bundle_sha256"]=hashlib.sha256(bundle).hexdigest()

    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"terminal_state":receipt["terminal_state"],"discovery":receipt["discovery"]},indent=2,allow_nan=False))

if __name__=="__main__":
    main()

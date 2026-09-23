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
COST10=10.0
COST14=14.0
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/usorb001_discovery_receipt.json")

# Full-day U.S. cash-market closures inside the frozen Discovery block.
HOLIDAYS={
"2022-01-17","2022-02-21","2022-04-15","2022-05-30","2022-06-20","2022-07-04","2022-09-05","2022-11-24","2022-12-26",
"2023-01-02","2023-01-16","2023-02-20","2023-04-07","2023-05-29","2023-06-19","2023-07-04","2023-09-04","2023-11-23","2023-12-25"
}

def mean(xs): return sum(xs)/len(xs) if xs else float("nan")

def percentile(xs,p):
    ys=sorted(xs)
    if not ys: return float("nan")
    k=(len(ys)-1)*p
    f=math.floor(k); c=math.ceil(k)
    return ys[f] if f==c else ys[f]*(c-k)+ys[c]*(k-f)

def profit_factor(xs):
    pos=sum(x for x in xs if x>0)
    neg=-sum(x for x in xs if x<0)
    return pos/neg if neg>0 else (float("inf") if pos>0 else 0.0)

def fetch_month(symbol,year,month):
    url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/5m/{symbol}-5m-{year}-{month:02d}.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-USORB-001/1.0"})
    with urllib.request.urlopen(req,timeout=90) as r:
        raw=r.read()
    sha=hashlib.sha256(raw).hexdigest()
    rows=[]
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name=z.namelist()[0]
        with io.TextIOWrapper(z.open(name),encoding="utf-8") as txt:
            for row in csv.reader(txt):
                if not row or not row[0].isdigit(): continue
                rows.append({"t":int(row[0]),"o":float(row[1]),"h":float(row[2]),"l":float(row[3]),"c":float(row[4]),"v":float(row[5])})
    return rows,{"url":url,"sha256":sha,"rows":len(rows)}

def load_symbol(symbol):
    rows=[]; prov=[]
    for y in YEARS:
        for m in MONTHS:
            rs,p=fetch_month(symbol,y,m)
            rows.extend(rs); prov.append(p)
    rows.sort(key=lambda x:x["t"])
    out=[]; seen=set()
    for r in rows:
        if r["t"] in seen: continue
        seen.add(r["t"]); out.append(r)
    return out,prov

def local_dt(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).astimezone(NY)

def eligible_date(d):
    s=d.isoformat()
    return d.weekday()<5 and s not in HOLIDAYS

def compute_trades(rows):
    bydate=defaultdict(list)
    for r in rows:
        dt=local_dt(r["t"])
        if eligible_date(dt.date()):
            x=dict(r); x["dt"]=dt
            bydate[dt.date()].append(x)

    trades=[]
    for d,day in sorted(bydate.items()):
        day.sort(key=lambda x:x["t"])
        idx={x["dt"].time().replace(second=0,microsecond=0):i for i,x in enumerate(day)}
        ortimes=[time(9,30),time(9,35),time(9,40)]
        if not all(t in idx for t in ortimes): continue
        orbars=[day[idx[t]] for t in ortimes]
        orh=max(x["h"] for x in orbars); orl=min(x["l"] for x in orbars)
        sig=None; sigi=None
        cur=time(9,45)
        # scan explicit five-minute starts through 11:25 ET
        for h in range(9,12):
            for minute in range(0,60,5):
                t=time(h,minute)
                if t<time(9,45) or t>=time(11,30): continue
                if t not in idx: continue
                i=idx[t]; x=day[i]
                if x["c"]>orh:
                    sig=1; sigi=i; break
                if x["c"]<orl:
                    sig=-1; sigi=i; break
            if sig is not None: break
        if sig is None: continue
        entry_i=sigi+1; exit_i=sigi+12
        if exit_i>=len(day): continue
        # enforce uninterrupted 5m sequence across signal->exit
        ok=True
        for j in range(sigi,exit_i):
            if day[j+1]["t"]-day[j]["t"]!=300000:
                ok=False; break
        if not ok: continue
        entry=day[entry_i]["o"]; exitp=day[exit_i]["c"]
        gross=sig*((exitp/entry)-1.0)*10000.0
        trades.append({
          "date":d.isoformat(),"year":d.year,"side":sig,
          "signal_time_et":day[sigi]["dt"].strftime("%H:%M"),
          "or_width_bps":(orh/orl-1.0)*10000.0,
          "gross_bps":gross,"net10_bps":gross-COST10,"net14_bps":gross-COST14
        })
    return trades

def cluster_bootstrap(trades,reps=5000,seed=20260923):
    bydate=defaultdict(list)
    for t in trades: bydate[t["date"]].append(t["net10_bps"])
    dates=sorted(bydate)
    rng=random.Random(seed); vals=[]
    for _ in range(reps):
        sample=[]
        for __ in dates:
            d=dates[rng.randrange(len(dates))]
            sample.extend(bydate[d])
        vals.append(mean(sample))
    return [percentile(vals,.025),percentile(vals,.975)]

def positive_pnl_share(per_symbol):
    positives={k:max(v["sum_net10_bps"],0.0) for k,v in per_symbol.items()}
    total=sum(positives.values())
    return max(positives.values())/total if total>0 else 1.0

def main():
    receipt={"lab_id":"USORB-001","scope":"DISCOVERY_2022_2023_ONLY","symbols":{},"provenance":[]}
    alltr=[]
    for s in SYMBOLS:
        rows,prov=load_symbol(s)
        tr=compute_trades(rows)
        for x in tr: x["symbol"]=s
        alltr.extend(tr)
        receipt["symbols"][s]={"rows":len(rows),"trades":len(tr)}
        receipt["provenance"].extend([{"symbol":s,**p} for p in prov])

    nets10=[t["net10_bps"] for t in alltr]
    nets14=[t["net14_bps"] for t in alltr]
    per_symbol={}
    for s in SYMBOLS:
        xs=[t["net10_bps"] for t in alltr if t["symbol"]==s]
        per_symbol[s]={"n":len(xs),"mean_net10_bps":mean(xs) if xs else None,"sum_net10_bps":sum(xs)}
    per_year={}
    for y in YEARS:
        xs=[t["net10_bps"] for t in alltr if t["year"]==y]
        per_year[str(y)]={"n":len(xs),"mean_net10_bps":mean(xs) if xs else None}

    ci=cluster_bootstrap(alltr) if alltr else [None,None]
    pshare=positive_pnl_share(per_symbol)
    result={
      "trades":len(alltr),
      "mean_gross_bps":mean([t["gross_bps"] for t in alltr]) if alltr else None,
      "mean_net10_bps":mean(nets10) if nets10 else None,
      "mean_net14_bps":mean(nets14) if nets14 else None,
      "profit_factor_net10":profit_factor(nets10) if nets10 else None,
      "cluster_bootstrap95_net10":ci,
      "positive_symbols_net10":sum(1 for v in per_symbol.values() if v["mean_net10_bps"] is not None and v["mean_net10_bps"]>0),
      "positive_years_net10":sum(1 for v in per_year.values() if v["mean_net10_bps"] is not None and v["mean_net10_bps"]>0),
      "max_single_symbol_positive_pnl_share":pshare,
      "per_symbol":per_symbol,
      "per_year":per_year,
      "median_or_width_bps":statistics.median([t["or_width_bps"] for t in alltr]) if alltr else None
    }

    enough=len(alltr)>=1500
    passed=bool(enough and result["mean_net10_bps"]>0 and result["mean_net14_bps"]>0 and result["profit_factor_net10"]>1.0 and ci[0]>0 and result["positive_symbols_net10"]>=4 and result["positive_years_net10"]>=2 and pshare<=0.60)
    result["pass"]=passed
    result["classification"]="DISCOVERY_SURVIVES_ONLY" if passed else ("INSUFFICIENT_SAMPLE" if not enough else "NO_EDGE")
    receipt["discovery"]=result
    receipt["terminal_state"]=result["classification"]
    receipt["protected_periods_opened"]=[]
    receipt["live_execution"]=False
    receipt["merge_to_main"]=False
    bundle="".join(p["sha256"] for p in receipt["provenance"]).encode()
    receipt["source_bundle_sha256"]=hashlib.sha256(bundle).hexdigest()
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"terminal_state":receipt["terminal_state"],"discovery":receipt["discovery"]},indent=2,allow_nan=False))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations
import bisect,csv,hashlib,json,math,random,shutil,sys,tempfile,time,urllib.request,zipfile
from collections import Counter
from datetime import datetime,timezone,timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"flow_path_absorption_hist_v02"))
import run_v02 as base

LAB_ID="EXTREME-FLOW-HIGHVOL-REVERSION-2026-001"
BASELINE=2016
COOLDOWN=12
MIN_EVENTS=100
MIN_DATES=60
MIN_COVERAGE=0.99
BOOT_N=10000
BOOT_SEED=20261001
OUT=Path("extreme_flow_highvol_reversion_2026/run_output")
DAILY_BASE="https://data.binance.vision/data/spot/daily/klines/BTCUSDT/1m"

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for ch in iter(lambda:f.read(1024*1024),b""): h.update(ch)
    return h.hexdigest()

def fetch(url,path):
    last=None
    for n in range(5):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-HighVol/0.1"})
            with urllib.request.urlopen(req,timeout=60) as r,open(path,"wb") as w:
                shutil.copyfileobj(r,w,1024*1024)
            return
        except Exception as e:
            last=e;time.sleep(min(2**n,8))
    raise RuntimeError(f"download failed {url}: {last}")

def load_daily(day,tmp,prov):
    name=f"BTCUSDT-1m-{day}.zip";url=f"{DAILY_BASE}/{name}"
    z=tmp/name;c=tmp/(name+".CHECKSUM")
    fetch(url,z);fetch(url+".CHECKSUM",c)
    expected=c.read_text().strip().split()[0].lower();actual=sha256_file(z)
    if actual!=expected:raise RuntimeError(f"checksum mismatch {day}")
    prov.append({"day":day,"url":url,"zip_sha256":actual})
    out=[]
    with zipfile.ZipFile(z) as zz:
        names=zz.namelist()
        if len(names)!=1:raise RuntimeError(f"unexpected archive members {day}")
        with zz.open(names[0],"r") as raw:
            reader=csv.reader((line.decode("utf-8") for line in raw))
            cur=None;bucket=[]
            for row in reader:
                if not row or not str(row[0]).strip().lstrip("-").isdigit():continue
                ot=base.ms(row[0])
                r={"open_ms":ot,"open":float(row[1]),"close":float(row[4]),"volume":float(row[5]),"taker_buy":float(row[9])}
                bo=(ot//base.BAR_MS)*base.BAR_MS
                if cur is None:cur=bo
                if bo!=cur:
                    x=base.finalize5(bucket)
                    if x:out.append(x)
                    bucket=[];cur=bo
                bucket.append(r)
            if bucket:
                x=base.finalize5(bucket)
                if x:out.append(x)
    z.unlink(missing_ok=True);c.unlink(missing_ok=True)
    return out

def load_all():
    rows=[];prov=[]
    with tempfile.TemporaryDirectory() as td:
        tmp=Path(td)
        for m in base.months("2025-12","2026-08"):
            print("monthly",m,flush=True)
            rows.extend(base.load_month(m,tmp,prov))
        d=datetime(2026,9,1,tzinfo=timezone.utc)
        end=datetime(2026,10,1,tzinfo=timezone.utc)
        while d<end:
            s=d.date().isoformat();print("daily",s,flush=True)
            rows.extend(load_daily(s,tmp,prov));d+=timedelta(days=1)
    rows.sort(key=lambda r:r["bar_open_ms"])
    seen=set()
    for r in rows:
        if r["bar_open_ms"] in seen:raise RuntimeError("duplicate 5m bar")
        seen.add(r["bar_open_ms"])
    return rows,prov

def median(v):
    a=sorted(v);n=len(a)
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2

def wilson(k,n,z=1.959963984540054):
    p=k/n;den=1+z*z/n
    cen=p+z*z/(2*n);adj=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)
    return (cen-adj)/den

def bootstrap_mean(v):
    rng=random.Random(BOOT_SEED);n=len(v);means=[]
    for _ in range(BOOT_N):
        means.append(sum(v[rng.randrange(n)] for __ in range(n))/n)
    means.sort()
    return base.quant(means,.025),base.quant(means,.975)

def pf(v):
    pos=sum(x for x in v if x>0);neg=-sum(x for x in v if x<0)
    return pos/neg if neg>0 else math.inf

def classify(rows,start_ms,end_ms):
    ds=sorted(abs(r["agg_delta_pct"]) for r in rows[:BASELINE])
    vs=sorted(r["agg_base_volume"] for r in rows[:BASELINE])
    events=[];counts=Counter();cool=-1
    for i in range(BASELINE,len(rows)):
        r=rows[i];td=base.quant(ds,.95);tv=base.quant(vs,.75)
        if start_ms<=r["bar_open_ms"]<end_ms:
            d=1 if r["agg_delta_pct"]>0 else -1 if r["agg_delta_pct"]<0 else 0
            cand=d!=0 and abs(r["agg_delta_pct"])>=td and r["agg_base_volume"]>=2.0*tv
            if cand:
                if i<=cool:counts["COOLDOWN_SUPPRESSED"]+=1
                else:
                    events.append({**r,"direction":d,"q95_abs_delta_pct":td,"q75_agg_base_volume":tv,"volume_ratio_to_q75":r["agg_base_volume"]/tv})
                    counts["ACCEPTED"]+=1;cool=i+COOLDOWN
            else:counts["NON_EVENT"]+=1
        old=rows[i-BASELINE]
        base.remove_sorted(ds,abs(old["agg_delta_pct"]));bisect.insort(ds,abs(r["agg_delta_pct"]))
        base.remove_sorted(vs,old["agg_base_volume"]);bisect.insort(vs,r["agg_base_volume"])
    return events,counts

def add_outcomes(events,rows):
    idx={r["bar_open_ms"]:i for i,r in enumerate(rows)};out=[]
    for e in events:
        x=dict(e);i=idx[e["bar_open_ms"]];j=i+48
        if j<len(rows) and rows[j]["bar_open_ms"]-e["bar_open_ms"]==240*60000:
            signed=e["direction"]*(rows[j]["close"]/e["close"]-1)*10000.0
            x["F240"]=-signed
        else:x["F240"]=None
        dt=datetime.fromtimestamp(e["bar_close_ms"]/1000,tz=timezone.utc)
        x["utc_date"]=dt.date().isoformat();x["utc_quarter"]=f"{dt.year}-Q{(dt.month-1)//3+1}"
        out.append(x)
    return out

def econ(v,cost):
    net=[x-cost for x in v];lo,hi=bootstrap_mean(net)
    return {"roundtrip_cost_bps":cost,"mean_net_bps":sum(net)/len(net),"median_net_bps":median(net),
            "profit_factor":pf(net),"bootstrap95_mean_net_bps":[lo,hi],
            "economic_survives":(sum(net)/len(net)>0 and pf(net)>1 and lo>0)}

def main():
    rows,prov=load_all()
    start=base.dtms("2026-01-01T00:00:00Z");end=base.dtms("2026-10-01T00:00:00Z")
    expected=(end-start)//base.BAR_MS
    valid=[r for r in rows if start<=r["bar_open_ms"]<end]
    source_cov=len(valid)/expected
    events,counts=classify(rows,start,end)
    ev=add_outcomes(events,rows)
    vals=[x["F240"] for x in ev if isinstance(x.get("F240"),(int,float)) and math.isfinite(x["F240"])]
    cov=len(vals)/len(ev) if ev else 0
    dates={x["utc_date"] for x in ev}
    q={}
    for qq in ("2026-Q1","2026-Q2","2026-Q3"):
        z=[x["F240"] for x in ev if x["utc_quarter"]==qq and isinstance(x.get("F240"),(int,float)) and math.isfinite(x["F240"])]
        q[qq]={"n":len(z),"mean_F240_bps":sum(z)/len(z) if z else None,"median_F240_bps":median(z) if z else None,"hit_rate":sum(x>0 for x in z)/len(z) if z else None}
    base_report={"lab_id":LAB_ID,"source_coverage":source_cov,"valid_5m_bars":len(valid),"expected_5m_bars":expected,
                 "accepted_events":len(ev),"distinct_utc_dates":len(dates),"F240_coverage":cov,"class_counts":dict(sorted(counts.items())),
                 "quarterly":q,"trading_authority":"NONE"}
    if source_cov<MIN_COVERAGE:
        report={**base_report,"classification":"SOURCE_BLOCKED"}
    elif len(ev)<MIN_EVENTS or len(dates)<MIN_DATES or cov<MIN_COVERAGE:
        report={**base_report,"classification":"INSUFFICIENT_SAMPLE"}
    else:
        mean=sum(vals)/len(vals);med=median(vals);lo,hi=bootstrap_mean(vals);hits=sum(x>0 for x in vals);rate=hits/len(vals);wlo=wilson(hits,len(vals))
        posq=sum(1 for z in q.values() if z["median_F240_bps"] is not None and z["median_F240_bps"]>0)
        gross=mean>0 and med>0 and lo>0 and rate>.5 and wlo>.5 and posq>=2
        costs={str(c):econ(vals,c) for c in (12,14,16,18)}
        if not gross:cl="HOLDOUT_FAILED"
        elif costs["12"]["economic_survives"]:cl="HOLDOUT_GROSS_SURVIVES_MAKER_ECONOMIC_SURVIVES"
        else:cl="HOLDOUT_GROSS_SURVIVES_COST_BLOCKED"
        report={**base_report,"classification":cl,"gross_gate_pass":gross,"mean_F240_bps":mean,"median_F240_bps":med,
                "gross_profit_factor":pf(vals),"bootstrap95_mean_F240_bps":[lo,hi],"hit_rate_F240":rate,
                "hit_rate_wilson_lower95":wlo,"positive_median_quarters":posq,"cost_models":costs,
                "mexc_api_taker_economic_survives":costs["16"]["economic_survives"]}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"HOLDOUT_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (OUT/"SOURCE_PROVENANCE.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n")
    fields=["bar_open_ms","bar_close_ms","utc_date","utc_quarter","direction","agg_delta_pct","agg_base_volume","q95_abs_delta_pct","q75_agg_base_volume","volume_ratio_to_q75","F240"]
    with (OUT/"HOLDOUT_EVENTS.csv").open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader()
        for x in ev:w.writerow({k:x.get(k) for k in fields})
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":
    main()

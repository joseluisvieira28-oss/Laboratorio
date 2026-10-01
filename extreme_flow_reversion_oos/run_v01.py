#!/usr/bin/env python3
from __future__ import annotations
import bisect,csv,json,math,random,sys
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"flow_path_absorption_hist_v02"))
import run_v02 as base

LAB_ID="EXTREME-FLOW-REVERSION-OOS-001"
BASELINE=2016
COOLDOWN=12
MIN_EVENTS=200
MIN_DATES=30
MIN_COVERAGE=0.99
BOOT_N=10000
BOOT_SEED=20261001
HORIZONS=(5,15,30,60,240)
OUT=Path("extreme_flow_reversion_oos/run_output")

def median(v):
    a=sorted(v);n=len(a)
    if not n:return math.nan
    return a[n//2] if n%2 else (a[n//2-1]+a[n//2])/2

def wilson(k,n,z=1.959963984540054):
    if n<=0:return math.nan
    p=k/n;den=1+z*z/n
    cen=p+z*z/(2*n);adj=z*math.sqrt((p*(1-p)+z*z/(4*n))/n)
    return (cen-adj)/den

def bootstrap_median(v):
    rng=random.Random(BOOT_SEED);vals=[]
    for _ in range(BOOT_N):
        s=[v[rng.randrange(len(v))] for __ in range(len(v))]
        vals.append(median(s))
    vals.sort()
    return base.quant(vals,.025),base.quant(vals,.975)

def classify(rows,start_ms,end_ms):
    if len(rows)<=BASELINE:return [],Counter()
    ds=sorted(abs(r["agg_delta_pct"]) for r in rows[:BASELINE])
    vs=sorted(r["agg_base_volume"] for r in rows[:BASELINE])
    events=[];counts=Counter();cool=-1
    for i in range(BASELINE,len(rows)):
        r=rows[i]
        td=base.quant(ds,.95);tv=base.quant(vs,.75)
        if start_ms<=r["bar_open_ms"]<end_ms:
            d=1 if r["agg_delta_pct"]>0 else -1 if r["agg_delta_pct"]<0 else 0
            extreme=d!=0 and abs(r["agg_delta_pct"])>=td and r["agg_base_volume"]>=tv
            if extreme:
                if i<=cool:
                    counts["COOLDOWN_SUPPRESSED"]+=1
                else:
                    x={**r,"direction":d,"q95_abs_delta_pct":td,"q75_agg_base_volume":tv}
                    events.append(x);counts["EXTREME_FLOW_EVENT"]+=1;cool=i+COOLDOWN
            else:
                counts["NON_EVENT"]+=1
        old=rows[i-BASELINE]
        base.remove_sorted(ds,abs(old["agg_delta_pct"]));bisect.insort(ds,abs(r["agg_delta_pct"]))
        base.remove_sorted(vs,old["agg_base_volume"]);bisect.insort(vs,r["agg_base_volume"])
    return events,counts

def add_outcomes(events,rows):
    idx={r["bar_open_ms"]:i for i,r in enumerate(rows)}
    out=[]
    for e in events:
        i=idx[e["bar_open_ms"]];x=dict(e)
        for h in HORIZONS:
            j=i+h//5
            if j<len(rows) and rows[j]["bar_open_ms"]-e["bar_open_ms"]==h*60000:
                x[f"R{h}"]=e["direction"]*(rows[j]["close"]/e["close"]-1)*10000.0
            else:x[f"R{h}"]=None
        dt=datetime.fromtimestamp(e["bar_close_ms"]/1000,tz=timezone.utc)
        x["utc_date"]=dt.date().isoformat()
        x["utc_quarter"]=f"{dt.year}-Q{(dt.month-1)//3+1}"
        out.append(x)
    return out

def main():
    rows,prov=base.load_period(base.months("2024-12","2025-12"))
    start=base.dtms("2025-01-01T00:00:00Z");end=base.dtms("2026-01-01T00:00:00Z")
    expected=(end-start)//base.BAR_MS
    valid=[r for r in rows if start<=r["bar_open_ms"]<end]
    source_cov=len(valid)/expected
    events,counts=classify(rows,start,end)
    ev=add_outcomes(events,rows)
    r60=[x["R60"] for x in ev if isinstance(x.get("R60"),(int,float)) and math.isfinite(x["R60"])]
    cov=len(r60)/len(ev) if ev else 0.0
    dates={x["utc_date"] for x in ev}
    qmed={}
    for q in ("2025-Q1","2025-Q2","2025-Q3","2025-Q4"):
        vals=[x["R60"] for x in ev if x["utc_quarter"]==q and isinstance(x.get("R60"),(int,float)) and math.isfinite(x["R60"])]
        qmed[q]={"n":len(vals),"median_R60_bps":median(vals) if vals else None}
    base_report={
      "lab_id":LAB_ID,"phase":"OOS_2025","source_coverage":source_cov,
      "valid_5m_bars":len(valid),"expected_5m_bars":expected,
      "accepted_events":len(ev),"distinct_utc_dates":len(dates),
      "R60_coverage":cov,"class_counts":dict(sorted(counts.items())),
      "quarterly":qmed,"trading_authority":"NONE"
    }
    if source_cov<MIN_COVERAGE:
        report={**base_report,"classification":"SOURCE_BLOCKED"}
    elif len(ev)<MIN_EVENTS or len(dates)<MIN_DATES or cov<MIN_COVERAGE:
        report={**base_report,"classification":"INSUFFICIENT_SAMPLE"}
    else:
        med=median(r60);lo,hi=bootstrap_median(r60)
        rev=sum(x<0 for x in r60);rate=rev/len(r60);wlo=wilson(rev,len(r60))
        negq=sum(1 for q in qmed.values() if q["median_R60_bps"] is not None and q["median_R60_bps"]<0)
        survive=med<0 and hi<0 and rate>.5 and wlo>.5 and negq>=3
        report={**base_report,
          "classification":"OOS_REVERSION_SURVIVES" if survive else "OOS_REVERSION_FAILED",
          "median_R60_bps":med,"bootstrap95_median_R60_bps":[lo,hi],
          "reversal_rate_R60":rate,"reversal_wilson_lower95":wlo,
          "negative_median_quarters":negq}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"OOS_REPORT.json").write_text(json.dumps(report,indent=2,sort_keys=True,allow_nan=False)+"\n")
    (OUT/"SOURCE_PROVENANCE.json").write_text(json.dumps(prov,indent=2,sort_keys=True)+"\n")
    fields=["bar_open_ms","bar_close_ms","utc_date","utc_quarter","direction","agg_delta_pct","agg_base_volume","q95_abs_delta_pct","q75_agg_base_volume"]+[f"R{h}" for h in HORIZONS]
    with (OUT/"OOS_EVENTS.csv").open("w",newline="") as fh:
        w=csv.DictWriter(fh,fieldnames=fields);w.writeheader()
        for x in ev:w.writerow({k:x.get(k) for k in fields})
    print(json.dumps(report,indent=2,sort_keys=True),flush=True)

if __name__=="__main__":
    main()

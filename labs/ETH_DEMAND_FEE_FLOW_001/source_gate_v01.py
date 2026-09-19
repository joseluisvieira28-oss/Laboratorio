#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.parse, urllib.request
from pathlib import Path
import pandas as pd

BASE="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
START="2024-03-01"; END="2025-12-31"
METRICS=["FeeTotNtv","SplyCur","PriceUSD"]

def fetch_all():
    params={
      "assets":"eth",
      "metrics":",".join(METRICS),
      "frequency":"1d",
      "start_time":START,
      "end_time":END,
      "page_size":"10000"
    }
    url=BASE+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-EDFF-SourceGate/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r:
        status=getattr(r,"status",200)
        raw=r.read()
    obj=json.loads(raw)
    data=obj.get("data",[])
    return status,url,data,obj

def main():
    status,url,data,obj=fetch_all()
    df=pd.DataFrame(data)
    missing=[m for m in ["time"]+METRICS if m not in df.columns]
    if missing:
        out={"classification":"EDFF_SOURCE_BLOCKED","http_status":status,"missing_columns":missing,
             "row_count":len(df),"authentication_used":False,"outcomes_opened":False}
        Path("edff_source_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
        print(json.dumps(out,sort_keys=True)); return 2

    df["time"]=pd.to_datetime(df["time"],utc=True,errors="coerce")
    for m in METRICS: df[m]=pd.to_numeric(df[m],errors="coerce")
    df=df.sort_values("time")
    complete=df.dropna(subset=["time"]+METRICS).copy()
    positive=complete[(complete["FeeTotNtv"]>0)&(complete["SplyCur"]>0)&(complete["PriceUSD"]>0)].copy()
    expected=len(pd.date_range(START,END,freq="D",tz="UTC"))
    unique_days=positive["time"].dt.floor("D").nunique()
    coverage=unique_days/expected
    duplicates=int(positive["time"].dt.floor("D").duplicated().sum())
    full=(status==200 and len(positive)>=600 and coverage>=.95 and duplicates==0)
    limited=(status==200 and len(positive)>=450 and coverage>=.80)
    cls="EDFF_SOURCE_FULL" if full else ("EDFF_SOURCE_LIMITED" if limited else "EDFF_SOURCE_BLOCKED")

    reps={}
    for ds in ["2024-03-15","2024-12-15","2025-06-15","2025-12-15"]:
        day=pd.Timestamp(ds,tz="UTC")
        q=positive[positive["time"].dt.floor("D")==day]
        reps[ds]=None if q.empty else {m:float(q.iloc[0][m]) for m in METRICS}

    out={
      "lab_id":"ETH-DEMAND-FEE-FLOW-001",
      "source_gate_id":"EDFF-CM-COMMUNITY-001",
      "classification":cls,
      "http_status":status,
      "endpoint":url,
      "raw_row_count":int(len(df)),
      "complete_positive_rows":int(len(positive)),
      "expected_calendar_days":expected,
      "unique_complete_days":int(unique_days),
      "coverage_ratio":float(coverage),
      "duplicate_daily_rows":duplicates,
      "timestamp_min_utc":positive["time"].min().isoformat() if len(positive) else None,
      "timestamp_max_utc":positive["time"].max().isoformat() if len(positive) else None,
      "representative_values":reps,
      "authentication_used":False,
      "cash_spend_usd":0,
      "outcomes_opened":False,
      "regression_run":False,
      "pnl_opened":False,
      "year_2026_opened":False
    }
    Path("edff_source_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    positive.to_csv("edff_source_daily_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0 if cls!="EDFF_SOURCE_BLOCKED" else 2

if __name__=="__main__":
    raise SystemExit(main())

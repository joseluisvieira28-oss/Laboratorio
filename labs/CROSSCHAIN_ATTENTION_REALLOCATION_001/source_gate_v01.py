#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.parse, urllib.request
from pathlib import Path
import pandas as pd

BASE="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics"
ASSETS=["eth","sol","avax"]

def fetch(asset):
    params={
      "assets":asset,
      "metrics":"TxCnt",
      "frequency":"1d",
      "start_time":"2022-01-01",
      "end_time":"2024-12-31",
      "page_size":"10000"
    }
    url=BASE+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CAR-Source/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r:
        payload=json.loads(r.read().decode("utf-8"))
    return url,payload

def main():
    rec={}; frames=[]; full=0; limited=0
    for a in ASSETS:
        try:
            url,p=fetch(a); rows=p.get("data",[])
            d=pd.DataFrame(rows)
            if not {"time","TxCnt"}.issubset(d.columns):
                rec[a]={"classification":"BLOCKED","url":url,"columns":list(d.columns),"row_count":len(d)}
                continue
            d["time"]=pd.to_datetime(d["time"],utc=True,errors="coerce")
            d["TxCnt"]=pd.to_numeric(d["TxCnt"],errors="coerce")
            n=len(d); valid=d["TxCnt"].notna()
            nn=float(valid.mean()) if n else 0
            pos=float((d["TxCnt"]>0).mean()) if n else 0
            mn=d["time"].min(); mx=d["time"].max()
            checks={
              "rows_gte_1000":n>=1000,
              "nonnull_gte_0_95":nn>=.95,
              "positive_gte_0_95":pos>=.95,
              "min_time_lte_2022_01_03":bool(pd.notna(mn) and mn<=pd.Timestamp("2022-01-03T00:00:00Z")),
              "max_time_gte_2024_12_29":bool(pd.notna(mx) and mx>=pd.Timestamp("2024-12-29T00:00:00Z")),
              "max_time_lte_2024_12_31":bool(pd.notna(mx) and mx<=pd.Timestamp("2024-12-31T23:59:59Z")),
              "no_pagination":not bool(p.get("next_page_token"))
            }
            if all(checks.values()):
                cls="FULL"; full+=1
            elif n>=750 and nn>=.90 and pos>=.90 and pd.notna(mx) and mx<=pd.Timestamp("2024-12-31T23:59:59Z"):
                cls="LIMITED"; limited+=1
            else: cls="BLOCKED"
            rec[a]={"classification":cls,"url":url,"row_count":n,
                    "time_min":mn.isoformat() if pd.notna(mn) else None,
                    "time_max":mx.isoformat() if pd.notna(mx) else None,
                    "nonnull_fraction":nn,"positive_fraction":pos,"checks":checks}
            if cls!="BLOCKED":
                d["asset"]=a; frames.append(d[["asset","time","TxCnt"]])
        except Exception as e:
            rec[a]={"classification":"BLOCKED","error":f"{type(e).__name__}:{str(e)[:300]}"}

    if full==3:
        final="CAR_SOURCE_FULL"
    elif full+limited==3:
        final="CAR_SOURCE_LIMITED"
    else:
        final="CAR_SOURCE_BLOCKED"
    out={"lab_id":"CROSSCHAIN-ATTENTION-REALLOCATION-001","source_gate_id":"CAR-COINMETRICS-ACTIVITY-001",
         "classification":final,"assets":rec,"credentials_used":False,"cash_spend_usd":0,
         "outcomes_opened":False,"returns_computed":False,"protected_2025_2026_requested":False}
    Path("car_source_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    if frames: pd.concat(frames,ignore_index=True).to_csv("car_activity_2022_2024_v01.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0 if final!="CAR_SOURCE_BLOCKED" else 2

if __name__=="__main__": raise SystemExit(main())

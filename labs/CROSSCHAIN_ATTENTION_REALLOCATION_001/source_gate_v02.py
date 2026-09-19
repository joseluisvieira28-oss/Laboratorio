#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.parse, urllib.request
from pathlib import Path
import pandas as pd

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-CAR-ChainNative/0.2","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=90) as r:
        return json.loads(r.read().decode("utf-8"))

def eth():
    p={"assets":"eth","metrics":"TxCnt","frequency":"1d","start_time":"2022-01-01","end_time":"2024-12-31","page_size":"10000"}
    u="https://community-api.coinmetrics.io/v4/timeseries/asset-metrics?"+urllib.parse.urlencode(p)
    js=get_json(u); d=pd.DataFrame(js.get("data",[]))
    return u,d.rename(columns={"time":"date","TxCnt":"activity"})[["date","activity"]]

def sol():
    p={"filter":"nonvote_success","from_date":"20220101","to_date":"20241231"}
    u="https://public-api.solscan.io/analytics/transactions?"+urllib.parse.urlencode(p)
    js=get_json(u)
    data=js.get("data",js)
    if isinstance(data,dict) and "series" in data: data=data["series"]
    if isinstance(data,dict) and "data" in data: data=data["data"]
    d=pd.DataFrame(data)
    # Accept documented shapes: block_date/value or date/value.
    dc=next((c for c in ["block_date","date","time"] if c in d.columns),None)
    vc=next((c for c in ["value","nonvote_success","nonVoteSuccess"] if c in d.columns),None)
    if dc is None or vc is None: raise RuntimeError("unrecognized Solscan schema "+repr(list(d.columns)))
    return u,d.rename(columns={dc:"date",vc:"activity"})[["date","activity"]]

def avax():
    p={"startTimestamp":1640995200,"endTimestamp":1735689599,"timeInterval":"day","pageSize":2160}
    u="https://metrics.avax.network/v2/chains/43114/metrics/txCount?"+urllib.parse.urlencode(p)
    js=get_json(u); d=pd.DataFrame(js.get("results",[]))
    if not {"timestamp","value"}.issubset(d.columns): raise RuntimeError("unrecognized Avalanche schema "+repr(list(d.columns)))
    d["date"]=pd.to_datetime(pd.to_numeric(d["timestamp"],errors="coerce"),unit="s",utc=True,errors="coerce")
    d=d.rename(columns={"value":"activity"})
    return u,d[["date","activity"]]

def assess(name,u,d):
    d=d.copy()
    d["date"]=pd.to_datetime(d["date"],utc=True,errors="coerce").dt.floor("D")
    d["activity"]=pd.to_numeric(d["activity"],errors="coerce")
    d=d[(d["date"]>=pd.Timestamp("2022-01-01",tz="UTC"))&(d["date"]<=pd.Timestamp("2024-12-31",tz="UTC"))]
    d=d.sort_values("date").drop_duplicates("date",keep="last")
    n=len(d); nn=float(d["activity"].notna().mean()) if n else 0; pos=float((d["activity"]>0).mean()) if n else 0
    mn=d["date"].min(); mx=d["date"].max()
    checks={"rows_gte_900":n>=900,"nonnull_gte_0_95":nn>=.95,"positive_gte_0_95":pos>=.95,
            "min_date_lte_2022_01_07":bool(pd.notna(mn) and mn<=pd.Timestamp("2022-01-07",tz="UTC")),
            "max_date_gte_2024_12_20":bool(pd.notna(mx) and mx>=pd.Timestamp("2024-12-20",tz="UTC")),
            "max_date_lte_2024_12_31":bool(pd.notna(mx) and mx<=pd.Timestamp("2024-12-31",tz="UTC"))}
    return d,{"url":u,"row_count":n,"nonnull_fraction":nn,"positive_fraction":pos,
              "date_min":mn.isoformat() if pd.notna(mn) else None,"date_max":mx.isoformat() if pd.notna(mx) else None,
              "checks":checks,"classification":"FULL" if all(checks.values()) else "BLOCKED"}

def main():
    funcs={"ETH":eth,"SOL":sol,"AVAX":avax}; rec={}; frames=[]
    for name,fn in funcs.items():
        try:
            u,d=fn(); d,r=assess(name,u,d); rec[name]=r
            if r["classification"]=="FULL": d["chain"]=name; frames.append(d)
        except Exception as e:
            rec[name]={"classification":"BLOCKED","error":f"{type(e).__name__}:{str(e)[:500]}"}
    final="CAR_SOURCE_FULL_V02" if all(rec.get(c,{}).get("classification")=="FULL" for c in funcs) else "CAR_SOURCE_BLOCKED_V02"
    out={"lab_id":"CROSSCHAIN-ATTENTION-REALLOCATION-001","source_gate_id":"CAR-CHAINNATIVE-ACTIVITY-002",
         "classification":final,"chains":rec,"credentials_used":False,"cash_spend_usd":0,
         "outcomes_opened":False,"returns_computed":False,"protected_2025_2026_requested":False}
    Path("car_v02_source_receipt.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    if frames: pd.concat(frames,ignore_index=True)[["chain","date","activity"]].to_csv("car_v02_activity.csv",index=False)
    print(json.dumps(out,sort_keys=True))
    return 0 if final=="CAR_SOURCE_FULL_V02" else 2

if __name__=="__main__": raise SystemExit(main())

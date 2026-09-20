#!/usr/bin/env python3
from __future__ import annotations
import json, re, urllib.parse, urllib.request
from pathlib import Path
import pandas as pd

BASE="https://community-api.coinmetrics.io/v4"
START="2019-01-01"; END="2025-12-31"

def get_json(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-BMV-SourceGate/0.1"})
    with urllib.request.urlopen(req,timeout=60) as r:
        status=getattr(r,"status",200); raw=r.read()
    return status,json.loads(raw)

def fetch_metric(metric):
    q=urllib.parse.urlencode({
      "assets":"btc","metrics":metric,"frequency":"1d",
      "start_time":START,"end_time":END,"page_size":"10000"
    })
    status,obj=get_json(BASE+"/timeseries/asset-metrics?"+q)
    d=pd.DataFrame(obj.get("data",[]))
    if d.empty or "time" not in d.columns or metric not in d.columns:
        return {"metric":metric,"status":status,"rows":0,"coverage":0.0,"valid":False}
    d["time"]=pd.to_datetime(d["time"],utc=True,errors="coerce")
    d[metric]=pd.to_numeric(d[metric],errors="coerce")
    d=d.dropna(subset=["time",metric]).copy()
    d=d[d[metric]>0].sort_values("time")
    expected=len(pd.date_range(START,END,freq="D",tz="UTC"))
    uniq=d["time"].dt.floor("D").nunique()
    dup=int(d["time"].dt.floor("D").duplicated().sum())
    return {
      "metric":metric,"status":status,"rows":int(len(d)),
      "unique_days":int(uniq),"expected_days":expected,
      "coverage":float(uniq/expected),"duplicates":dup,
      "date_min":d["time"].min().isoformat() if len(d) else None,
      "date_max":d["time"].max().isoformat() if len(d) else None,
      "valid":bool(len(d)>0 and dup==0),
      "sample_values":[float(x) for x in d[metric].iloc[:3].tolist()] if len(d) else []
    }

def main():
    cat_status,cat=get_json(BASE+"/catalog-all/assets?assets=btc")
    # catalog shape varies; collect any strings that look like metric ids from BTC record.
    metric_ids=set()
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k in {"metric","metrics"}:
                    if isinstance(v,str): metric_ids.add(v)
                    elif isinstance(v,list):
                        for z in v:
                            if isinstance(z,str): metric_ids.add(z)
                            elif isinstance(z,dict) and isinstance(z.get("metric"),str): metric_ids.add(z["metric"])
                walk(v)
        elif isinstance(x,list):
            for z in x: walk(z)
    walk(cat)

    meta_status,meta=get_json(BASE+"/reference-data/asset-metrics?page_size=10000")
    candidates=[]
    for r in meta.get("data",[]):
        metric=str(r.get("metric",""))
        txt=" ".join(str(r.get(k,"")) for k in ["metric","full_name","description","category","subcategory"])
        low=txt.lower()
        if ("realized" in low and ("cap" in low or "value" in low)) or "mvrv" in low or ("market value" in low and "realized" in low):
            if not metric_ids or metric in metric_ids:
                candidates.append({
                  "metric":metric,
                  "full_name":r.get("full_name"),
                  "description":r.get("description"),
                  "category":r.get("category"),
                  "subcategory":r.get("subcategory")
                })

    # Add conservative known-name guesses only as probes; metadata must still validate them.
    meta_by={str(r.get("metric","")):r for r in meta.get("data",[])}
    for g in ["CapMVRVCur","CapRealUSD","CapMrktCurUSD","CapMrktEstUSD"]:
        if g in meta_by and all(c["metric"]!=g for c in candidates):
            r=meta_by[g]
            candidates.append({"metric":g,"full_name":r.get("full_name"),"description":r.get("description"),
                               "category":r.get("category"),"subcategory":r.get("subcategory")})

    probes=[]
    for c in candidates:
        try: p=fetch_metric(c["metric"])
        except Exception as e: p={"metric":c["metric"],"error":f"{type(e).__name__}:{str(e)[:240]}","coverage":0.0,"valid":False}
        p["metadata"]=c; probes.append(p)

    # Semantic roles from metadata.
    direct=[]; real=[]; market=[]
    for p in probes:
        md=p.get("metadata",{})
        txt=(" ".join(str(md.get(k,"")) for k in ["metric","full_name","description"])).lower()
        if "mvrv" in txt or ("market" in txt and "realized" in txt and ("ratio" in txt or "value" in txt)):
            direct.append(p)
        if "realized" in txt and ("capital" in txt or "cap" in txt) and "ratio" not in txt:
            real.append(p)
        if ("market cap" in txt or "market capitalization" in txt) and "realized" not in txt:
            market.append(p)

    full_direct=[p for p in direct if p.get("valid") and p.get("coverage",0)>=.95]
    full_real=[p for p in real if p.get("valid") and p.get("coverage",0)>=.95]
    full_market=[p for p in market if p.get("valid") and p.get("coverage",0)>=.95]
    lim_any=[p for p in probes if p.get("valid") and p.get("coverage",0)>=.80]

    if full_direct or (full_real and full_market): cls="BMV_SOURCE_FULL"
    elif lim_any and (direct or real): cls="BMV_SOURCE_LIMITED"
    else: cls="BMV_SOURCE_BLOCKED"

    out={
      "lab_id":"BTC-MVRV-VALUATION-001","source_gate_id":"BMV-CM-COMMUNITY-001",
      "classification":cls,
      "catalog_http_status":cat_status,"metadata_http_status":meta_status,
      "catalog_metric_count_detected":len(metric_ids),
      "candidate_count":len(candidates),
      "direct_candidates":[p["metric"] for p in direct],
      "realized_cap_candidates":[p["metric"] for p in real],
      "market_cap_candidates":[p["metric"] for p in market],
      "probes":probes,
      "authentication_used":False,"cash_spend_usd":0,
      "future_returns_opened":False,"pnl_opened":False,"year_2026_opened":False
    }
    Path("bmv_source_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "classification":cls,
      "candidate_count":len(candidates),
      "direct_candidates":out["direct_candidates"],
      "realized_cap_candidates":out["realized_cap_candidates"],
      "market_cap_candidates":out["market_cap_candidates"],
      "probe_summary":[{"metric":p.get("metric"),"coverage":p.get("coverage"),"valid":p.get("valid"),"error":p.get("error")} for p in probes]
    },sort_keys=True))
    return 0 if cls!="BMV_SOURCE_BLOCKED" else 2

if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""MU opening 1m source forensic: hashes and timestamps ONLY; NO outcome/return reads."""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

DAYS=(dt.date(2026,10,26),dt.date(2026,10,27))
UTC=dt.timezone.utc
NY=ZoneInfo("America/New_York")
OUT=Path("artifacts/event10m_mu_source_forensics_v03")
DAY0=int(dt.datetime(2026,10,26,tzinfo=UTC).timestamp())
DAY2=int(dt.datetime(2026,10,28,tzinfo=UTC).timestamp())
def h(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode()).hexdigest()
def get(url):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-ReadOnly-Research/0.3"})
    with urllib.request.urlopen(req,timeout=30) as response:
        if response.status!=200:raise RuntimeError("NON200_RESPONSE")
        raw=response.read(3_500_001)
    if len(raw)>3_500_000:raise RuntimeError("SOURCE_TOO_LARGE")
    return raw
def stock(host):
    url="https://"+host+"/v8/finance/chart/MU?"+urllib.parse.urlencode(
      {"period1":DAY0,"period2":DAY2,"interval":"1m","includePrePost":"false"})
    b=get(url)
    doc=json.loads(b).get("chart",{})
    if doc.get("error"):raise RuntimeError("CHART_ERROR")
    arr=doc.get("result") or []
    if len(arr)!=1:raise RuntimeError("CHART_RESULT_SCHEMA")
    j=arr[0]
    meta=j.get("meta") or {}
    if meta.get("symbol")!="MU":raise RuntimeError("STOCK_IDENTITY_ERROR")
    quotes=(j.get("indicators") or {}).get("quote") or []
    if len(quotes)!=1:raise RuntimeError("MISSING_QUOTE")
    stamps=j.get("timestamp")
    closes=quotes[0].get("close")
    if not isinstance(stamps,list) or not isinstance(closes,list) or len(stamps)!=len(closes):raise RuntimeError("SOURCE_ARRAY_SCHEMA")
    vals={}
    for stamp,close in zip(stamps,closes):
        if close is None:continue
        t=int(stamp);v=float(close)
        if t%60 or t in vals or not math.isfinite(v) or v<=0:raise RuntimeError("BAD_STOCK_MINUTE")
        vals[t]=v
    return {"provider":host,"raw_sha256":hashlib.sha256(b).hexdigest(),
            "stock_meta":{"symbol":meta.get("symbol"),"exchangeName":meta.get("exchangeName"),
                          "currency":meta.get("currency"),"instrumentType":meta.get("instrumentType")},
            "series":vals,"full_digest":h(sorted(vals.items()))}
def index(day):
    start=int(dt.datetime.combine(day,dt.time.min,UTC).timestamp())
    url="https://contract.mexc.com/api/v1/contract/kline/index_price/MUSTOCK_USDT?"+urllib.parse.urlencode(
       {"interval":"Min1","start":start,"end":start+86400-60})
    b=get(url);j=json.loads(b)
    if j.get("success") is not True or not isinstance(j.get("data"),dict):raise RuntimeError("MEXC_SCHEMA")
    d=j["data"];stamps=d.get("time");opens=d.get("open")
    if not isinstance(stamps,list) or not isinstance(opens,list) or len(stamps)!=len(opens):raise RuntimeError("MEXC_ARRAYS")
    vals={}
    for stamp,price in zip(stamps,opens):
        t=int(stamp);v=float(price)
        if t%60 or t in vals or t<start or t>=start+86400 or not math.isfinite(v) or v<=0:raise RuntimeError("MEXC_BAD_MINUTE")
        vals[t]=v
    return {"provider":"MEXC_INDEX_MIN1","date":str(day),"raw_sha256":hashlib.sha256(b).hexdigest(),
            "series":vals,"full_digest":h(sorted(vals.items()))}
def slot(day,n):
    start=dt.datetime.combine(day,dt.time(9,30),NY)
    return [int((start+dt.timedelta(minutes=i)).timestamp()) for i in range(n)]
def portion(source,day,n):
    ts=slot(day,n);vals=source["series"]
    missing=[t for t in ts if t not in vals]
    canon=[(t,vals[t]) for t in ts if t in vals]
    return {"date":str(day),"expected_minutes":n,"valid_minutes":len(canon),
            "missing_utc":missing,"canonical_sha256":h(canon),
            "per_minute_sha256":{str(t):h([t,vals[t]]) for t in ts if t in vals}}
def envelope(source,day,n):
    return portion(source,day,n)
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    assert slot(DAYS[0],1)[0]==int(dt.datetime(2026,10,26,13,30,tzinfo=UTC).timestamp())
    assert slot(DAYS[1],1)[0]==int(dt.datetime(2026,10,27,13,30,tzinfo=UTC).timestamp())
    report={"lab":"EVENT10M_MU_SOURCE_FORENSICS_V03","gate":"STARTING",
            "parent_gate":"SOURCE_DRIFT_BLOCKED_UNCHANGED","outcomes_opened":0,
            "market_return_calculated":False,"historical_payouts":False,
            "NVIDIA_excluded":True,"SPCX_excluded":True,"MLI_alias_used":False,
            "protected_holdout_unopened":True,"stock_runs":[],"index_runs":[]}
    try:
        yahoo=[stock("query1.finance.yahoo.com"),stock("query1.finance.yahoo.com"),
               stock("query2.finance.yahoo.com")]
        idx=[]
        for day in DAYS:idx.append((index(day),index(day)))
        for s in yahoo:
            report["stock_runs"].append({"provider":s["provider"],"raw_sha256":s["raw_sha256"],
             "full_digest":s["full_digest"],"meta":s["stock_meta"],"rows":len(s["series"]),
             "opening":[envelope(s,d,60) for d in DAYS]})
        for day,items in zip(DAYS,idx):
            for s in items:
                report["index_runs"].append({"date":str(day),"raw_sha256":s["raw_sha256"],
                 "full_digest":s["full_digest"],"rows":len(s["series"]),
                 "opening":envelope(s,day,61)})
        compatible=all(x["opening"][i]["valid_minutes"]==60 for x in report["stock_runs"] for i in (0,1))
        compatible &= all(x["opening"]["valid_minutes"]==61 for x in report["index_runs"])
        stable=all(
            len(set(x["opening"][i]["canonical_sha256"] for x in report["stock_runs"]))==1
            for i in (0,1))
        for day in DAYS:
            candidates=[x for x in report["index_runs"] if x["date"]==str(day)]
            stable &= len(set(x["opening"]["canonical_sha256"] for x in candidates))==1
        report["source_window_stable_within_run"]=stable
        report["coverage_complete"]=compatible
        report["gate"]="SOURCE_WINDOW_STABLE_WITHIN_RUN" if stable and compatible else "SOURCE_WINDOW_DRIFT_OR_GAPS"
    except Exception as exc:
        report["gate"]="SOURCE_BLOCKED"
        report["error"]=type(exc).__name__+":"+str(exc)[:180]
        raise
    finally:
        (OUT/"receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        digest_summary={
            "lab":report["lab"],"gate":report["gate"],"error":report.get("error"),
            "stock": [{"provider":s["provider"],"raw_sha256":s["raw_sha256"],
                       "full_digest":s["full_digest"],
                       "opening": [(x["date"],x["canonical_sha256"],x["valid_minutes"]) for x in s["opening"]]}
                      for s in report["stock_runs"]],
            "index":[{"date":z["date"],"full_digest":z["full_digest"],
                      "opening":z["opening"]["canonical_sha256"],
                      "valid":z["opening"]["valid_minutes"]} for z in report["index_runs"]],
            "outcomes_opened":0}
        print(json.dumps(digest_summary,indent=2,sort_keys=True),flush=True)
    if report["gate"]!="SOURCE_WINDOW_STABLE_WITHIN_RUN":raise SystemExit(2)
if __name__=="__main__":main()

#!/usr/bin/env python3
"""MU stock and MEXC MUSTOCK index one-minute historical SOURCE ONLY."""
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

OUT=Path("artifacts/event10m_mu_source_v01")
UTC=dt.timezone.utc
NY=ZoneInfo("America/New_York")
DAYS=(dt.date(2026,10,26),dt.date(2026,10,27))

def seconds(v):return int(v.timestamp())
def midnight(d):return dt.datetime.combine(d,dt.time(0),UTC)
def expected(day):
    start=dt.datetime.combine(day,dt.time(9,30),NY)
    return {seconds(start+dt.timedelta(minutes=x)) for x in range(40)}
def download(url,maximum=2500000):
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-ReadOnly-SourceProbe/0.1"})
    with urllib.request.urlopen(req,timeout=35) as reply:
        if reply.status!=200:raise ValueError("HTTP_NON200")
        b=reply.read(maximum+1)
    if len(b)>maximum:raise ValueError("BODY_TOO_LARGE")
    return b
def clean(ts,values):
    if not isinstance(ts,list) or not isinstance(values,list) or len(ts)!=len(values) or not ts:
        raise ValueError("MISSING_SOURCE_ARRAYS")
    found=set()
    for stamp,price in zip(ts,values):
        if price is None:continue
        t=int(stamp);p=float(price)
        if t%60 or t in found or not math.isfinite(p) or p<=0:raise ValueError("BAD_TIME_OR_PRICE")
        found.add(t)
    return found
def yahoo():
    a=seconds(midnight(DAYS[0]))
    b=seconds(midnight(DAYS[-1]+dt.timedelta(days=1)))
    url="https://query1.finance.yahoo.com/v8/finance/chart/MU?"+urllib.parse.urlencode(
       {"period1":a,"period2":b,"interval":"1m","includePrePost":"false"})
    z={"provider":"YAHOO_UNOFFICIAL_MU_1M","url":url,"status":"BLOCKED"}
    try:
        raw=download(url,3500000);z["sha256"]=hashlib.sha256(raw).hexdigest()
        chart=json.loads(raw)["chart"]
        if chart.get("error"):raise ValueError("CHART_ERROR")
        result=chart.get("result") or []
        if len(result)!=1:raise ValueError("NO_CHART_RESULT")
        timestamps=result[0].get("timestamp")
        quotes=((result[0].get("indicators") or {}).get("quote") or [])
        if len(quotes)!=1:raise ValueError("NO_CHART_QUOTES")
        z["seen"]=clean(timestamps,quotes[0].get("open"))
        z["status"]="SOURCE_SCHEMA_PASS"
    except Exception as e:
        z["error"]=type(e).__name__+":"+str(e)[:160]
    return z
def mexc(day):
    a=seconds(midnight(day));b=a+86400
    url="https://contract.mexc.com/api/v1/contract/kline/index_price/MUSTOCK_USDT?"+urllib.parse.urlencode(
        {"interval":"Min1","start":a,"end":b-60})
    z={"provider":"MEXC_STANDARD_FUTURES_INDEX_NOT_EVENT_PRICE",
       "day":day.isoformat(),"url":url,"status":"BLOCKED"}
    try:
        raw=download(url);z["sha256"]=hashlib.sha256(raw).hexdigest()
        data=json.loads(raw)
        if data.get("success") is not True or not isinstance(data.get("data"),dict):
            raise ValueError("NOT_SUCCESS")
        bars=data["data"]
        seen=clean(bars.get("time"),bars.get("open"))
        if any(t<a or t>=b for t in seen):raise ValueError("OUT_OF_DAY")
        z["seen"]=seen
        z["status"]="SOURCE_SCHEMA_PASS"
    except Exception as e:
        z["error"]=type(e).__name__+":"+str(e)[:160]
    return z
def main():
    assert min(expected(DAYS[0]))==seconds(dt.datetime(2026,10,26,13,30,tzinfo=UTC))
    assert min(expected(DAYS[1]))==seconds(dt.datetime(2026,10,27,13,30,tzinfo=UTC))
    OUT.mkdir(parents=True,exist_ok=True)
    y=yahoo()
    m={d:mexc(d) for d in DAYS}
    days=[]
    for day in DAYS:
        ex=expected(day);ys=y.get("seen") or set();ms=m[day].get("seen") or set()
        overlap=ex&ys&ms
        days.append({"date":day.isoformat(),"expected":40,"yahoo":len(ex&ys),
                     "mexc":len(ex&ms),"overlap":len(overlap),
                     "missing_shared_utc":sorted(ex-overlap),
                     "passed":min(len(ex&ys),len(ex&ms),len(overlap))>=30})
    def strip(z):return {k:v for k,v in z.items() if k!="seen"}
    passed=all(x["passed"] for x in days)
    report={"lab":"EVENT10M_MU_US_OPEN_SOURCE_V01",
      "gate":"HISTORICAL_SOURCE_FEASIBLE" if passed else "SOURCE_BLOCKED",
      "stocks":[strip(y)],"indices":[strip(m[d]) for d in DAYS],
      "coverage":days,"NVIDIA_excluded":True,"SPCX_excluded":True,
      "MLIUSDT_alias_not_proven":True,"historical_payout_known":False,
      "index_equals_event_order_price_proven":False,
      "collector_asof_proven":False,
      "outcomes_opened":0,"protected_september_opened":False,
      "account_or_trading_actions":0}
    (OUT/"receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    print(json.dumps({**report,"coverage":[{k:v for k,v in day.items() if k!="missing_shared_utc"} for day in days]},indent=2,sort_keys=True),flush=True)
    if not passed:raise SystemExit(2)
if __name__=="__main__":main()

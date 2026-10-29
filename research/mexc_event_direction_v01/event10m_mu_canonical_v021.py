#!/usr/bin/env python3
"""MU 1m source-only canonical digest stability; NO outcomes."""
import datetime as dt
import hashlib,json,math,urllib.parse
from pathlib import Path
import event10m_mu_source_v01 as par

OUT=Path("artifacts/event10m_mu_canonical_v021")
DAYS=par.DAYS
def pairs(ts,prices):
    if len(ts)!=len(prices):raise ValueError("MISALIGNED")
    result={}
    for t,p in zip(ts,prices):
        if p is None:continue
        t=int(t);p=float(p)
        if t%60 or not math.isfinite(p) or p<=0 or t in result:
            raise ValueError("INVALID_OR_DUPLICATE")
        result[t]=p
    return result
def getstock():
    a=par.seconds(par.midnight(DAYS[0]))
    b=par.seconds(par.midnight(DAYS[-1]+dt.timedelta(days=1)))
    url="https://query1.finance.yahoo.com/v8/finance/chart/MU?"+urllib.parse.urlencode(
       {"period1":a,"period2":b,"interval":"1m","includePrePost":"false"})
    raw=par.download(url,3500000)
    j=json.loads(raw)["chart"]
    if j.get("error"):raise ValueError("YAHOO_CHART_ERROR")
    obj=j["result"][0]
    price=obj["indicators"]["quote"][0]["close"]
    return raw,pairs(obj["timestamp"],price)
def getindex(d):
    a=par.seconds(par.midnight(d))
    url="https://contract.mexc.com/api/v1/contract/kline/index_price/MUSTOCK_USDT?"+urllib.parse.urlencode(
        {"interval":"Min1","start":a,"end":a+86400-60})
    raw=par.download(url)
    j=json.loads(raw)
    if j.get("success") is not True:raise ValueError("MEXC_NOT_SUCCESS")
    prices=pairs(j["data"]["time"],j["data"]["open"])
    if any(x<a or x>=a+86400 for x in prices):raise ValueError("INDEX_WRONG_DAY")
    return raw,prices
def canonical(series):
    body=json.dumps(sorted(series.items()),separators=(",",":"),ensure_ascii=True)
    return hashlib.sha256(body.encode()).hexdigest()
def twice(fn,name):
    a,p=fn();b,q=fn()
    digest_a=canonical(p);digest_b=canonical(q)
    if digest_a!=digest_b:raise ValueError(name+"_CANONICAL_DRIFT")
    return p,{"identity":name,"raw_sha256_first":hashlib.sha256(a).hexdigest(),
       "raw_sha256_second":hashlib.sha256(b).hexdigest(),
       "canonical_sha256":digest_a,"rows":len(p),
       "raw_payload_changed":a!=b}
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    report={"lab":"EVENT10M_MU_CANONICAL_SOURCE_V021","gate":"STARTING",
        "outcomes_opened":0,"directions_calculated":0,"prices_disclosed":False,
        "NVIDIA_in_scope":False,"SPCX_in_scope":False,"MLI_alias_used":False,
        "protected_holdout_unopened":True,"sources":[],"coverage":[]}
    try:
        mu,a=twice(getstock,"YAHOO_MU_CLOSE")
        report["sources"].append(a)
        sources={}
        for day in DAYS:
            idx,b=twice(lambda day=day:getindex(day),"MEXC_MUSTOCK_OPEN_"+str(day))
            report["sources"].append(b);sources[day]=idx
        for day in DAYS:
            base=dt.datetime.combine(day,dt.time(9,30),par.NY)
            stamps={int((base+dt.timedelta(minutes=i)).timestamp()) for i in range(60)}
            overlap=len(stamps & mu.keys() & sources[day].keys())
            report["coverage"].append({"day":str(day),"expected":60,
                  "mu":len(stamps&mu.keys()),"mexc":len(stamps&sources[day].keys()),
                  "aligned":overlap})
        if any(x["aligned"]<55 for x in report["coverage"]):raise ValueError("COVERAGE_INSUFFICIENT")
        report["gate"]="CANONICAL_SOURCE_STABLE_PASS"
    except Exception as e:
        report["gate"]="CANONICAL_SOURCE_BLOCKED"
        report["reason"]=type(e).__name__+":"+str(e)[:160]
        raise
    finally:
        (OUT/"receipt.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True),flush=True)
if __name__=="__main__":main()

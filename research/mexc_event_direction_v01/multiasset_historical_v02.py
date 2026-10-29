#!/usr/bin/env python3
"""Event Futures multiasset HISTORICAL PRICE-ONLY proxy, frozen 5x4x2x2 cells.

No MEXC Event Futures executed price or historical payout available.
Same 2026-10-22/23 UTC Min5 public index data as prior source-only check.
"""
import datetime as dt
import hashlib
import json
import math
import pathlib
import urllib.parse
import urllib.request

ROOT=pathlib.Path("artifacts/event_futures_multiasset_v02")
ROOT.mkdir(parents=True,exist_ok=True)
START=int(dt.datetime(2026,10,22,tzinfo=dt.timezone.utc).timestamp())
END=int(dt.datetime(2026,10,24,tzinfo=dt.timezone.utc).timestamp())
CANDLE=300
N_EXPECTED=(END-START)//CANDLE
ASSETS={
 "BTC_USDT":"b9d15f93fa42cfd41fc575b46b69a3727c47492fbe6d310477a100afc7632f11",
 "ETH_USDT":"73cc1abc1212bd5388a2a78a1aad7be4774c7827b86c6a4b4aaf254d4dde5835",
 "NVIDIA_USDT":"7d7dab388ffae69d78d592f938a1ba33c0eb9b236c57efb1c64d8d528e1ae4ca",
 "SPCXSTOCK_USDT":"1ca4a17ec40a3514847226f728858b47ac7c75fc79d5f424a7883fe958896b0c",
 "MUSTOCK_USDT":"fcb039e436cb14c5bc55f62f778a3bcc99d223e3811d47da678cc2797615d81d"
}
RULES=("UP_ALWAYS","DOWN_ALWAYS","ROC3_CONT","ROC3_REV")
HORIZONS=(10,30)
STRATA=("ALL_24H","US_REGULAR_PROXY")
PAYOUTS=(0.4,0.7,0.8,0.85)
def prices(symbol, expected_sha):
    url=("https://contract.mexc.com/api/v1/contract/kline/index_price/"+
        symbol+"?"+urllib.parse.urlencode({"interval":"Min5","start":START,"end":END-CANDLE}))
    req=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"CryptoLab-Multiasset-Immutable-Hist/0.2"})
    with urllib.request.urlopen(req,timeout=40) as response:
        if response.status!=200:raise ValueError("HTTP_FAIL")
        raw=response.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError("SOURCE_TOO_LARGE")
    digest=hashlib.sha256(raw).hexdigest()
    if digest!=expected_sha:raise ValueError("SOURCE_BODY_CHANGED "+symbol+" sha="+digest)
    obj=json.loads(raw)
    if obj.get("success") is not True or not isinstance(obj.get("data"),dict):
        raise ValueError("BAD_SOURCE_SCHEMA")
    d=obj["data"];times=d.get("time");opens=d.get("open")
    if not isinstance(times,list) or not isinstance(opens,list) or len(times)!=len(opens):
        raise ValueError("BAD_KLINE_ARRAYS")
    p={int(t):float(v) for t,v in zip(times,opens)}
    if len(p)!=N_EXPECTED or len(times)!=N_EXPECTED:raise ValueError("SOURCE_COVERAGE_CHANGED")
    for t in range(START,END,CANDLE):
        if t not in p or not(math.isfinite(p[t]) and p[t]>0):
            raise ValueError("MISSING_OR_BAD_OPEN")
    return p,url,digest
def side(rule,p,t):
    if rule=="UP_ALWAYS":return 1
    if rule=="DOWN_ALWAYS":return -1
    a=p.get(t-900);b=p.get(t-300)
    if a is None or b is None:return None
    if b==a:return None
    val=1 if b>a else -1
    return val if rule=="ROC3_CONT" else -val
def regular(t,h):
    d=dt.datetime.fromtimestamp(t,dt.timezone.utc)
    mins=d.hour*60+d.minute
    return (d.weekday()<5 and 13*60+30<=mins and
            mins+h<=20*60)
def score(p,rule,h,stratum):
    # Decisions UTC-midnight-anchored and separated H minutes.
    outcomes=[]
    by_day={}
    skipped=0
    for t in range(START,END-h*60,h*60):
        if stratum=="US_REGULAR_PROXY" and not regular(t,h):
            continue
        if t not in p or t+h*60 not in p:
            skipped+=1;continue
        prediction=side(rule,p,t)
        if prediction is None:
            skipped+=1;continue
        delta=p[t+h*60]-p[t]
        result=0 if delta==0 else (1 if delta*prediction>0 else -1)
        outcomes.append(result)
        day=dt.datetime.fromtimestamp(t,dt.timezone.utc).date().isoformat()
        counts=by_day.setdefault(day,{"wins":0,"losses":0,"ties":0})
        counts["wins" if result==1 else "losses" if result==-1 else "ties"]+=1
    w=outcomes.count(1);loss=outcomes.count(-1);ties=outcomes.count(0)
    n=len(outcomes)
    ev={str(q):round((q*w-loss)/n,8) if n else None for q in PAYOUTS}
    return {"n":n,"wins":w,"losses":loss,"ties":ties,
            "skipped_missing_or_flat_features":skipped,
            "accuracy_ex_ties":w/(w+loss) if w+loss else None,
            "unit_EV_hypothetical_symmetric_payout":ev,
            "by_utc_day":by_day}
def main():
    assert N_EXPECTED==576
    report={"study":"EVENT_FUTURES_NEW_ASSETS_HIST_DISCOVERY_V02",
      "window_start":"2026-10-22T00:00:00Z","window_end_exclusive":"2026-10-24T00:00:00Z",
      "rules":list(RULES),"horizons_minutes":list(HORIZONS),"strata":list(STRATA),
      "payout_scenarios":list(PAYOUTS),"exact_historical_event_payouts":False,
      "exact_event_order_entry_price":False,
      "actual_product_online_those_dates":"UNKNOWN",
      "source_price_type":"MEXC_STANDARD_FUTURES_INDEX_MIN5_OPEN_PROXY_ONLY",
      "screenshot_mli_identity":"UNKNOWN_NOT_TESTED",
      "holds_september_2026_protected":True,
      "no_account_or_orders":True,"economic_verdict":"DISCOVERY_ONLY_NO_CERTIFIED_EDGE",
      "cells":[],"sources":[]}
    try:
        for symbol,sha in ASSETS.items():
            p,url,bodyhash=prices(symbol,sha)
            report["sources"].append({"symbol":symbol,"url":url,"sha256":bodyhash,"bars":len(p)})
            for h in HORIZONS:
                for rule in RULES:
                    for stratum in STRATA:
                        x=score(p,rule,h,stratum)
                        report["cells"].append({"symbol":symbol,"horizon_minutes":h,
                                                "rule":rule,"stratum":stratum,**x})
        if len(report["cells"])!=80:raise ValueError("MISSING_FROZEN_CELLS")
        report["source_status"]="SOURCE_HASH_AND_COVERAGE_PASS"
    except Exception as e:
        report["source_status"]="BLOCKED"
        report["source_error"]=type(e).__name__+":"+str(e)[:300]
        raise
    finally:
        (ROOT/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
        print(json.dumps(report,indent=2,sort_keys=True))
if __name__=="__main__":main()

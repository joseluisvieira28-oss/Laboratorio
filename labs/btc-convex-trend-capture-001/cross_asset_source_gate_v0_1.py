#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE GATE V0.1B

Coverage/provenance only. NO economic outcomes.
Funding transport follows CROSS_ASSET_SOURCE_AMENDMENT_003.
"""
from __future__ import annotations
import json, math, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
SYMBOLS=["ETHUSDT","SOLUSDT","BNBUSDT"]
START_MS=int(datetime(2021,1,1,0,0,tzinfo=timezone.utc).timestamp()*1000)
END_MS=int(datetime(2025,12,31,23,59,59,tzinfo=timezone.utc).timestamp()*1000)
FUNDING_HOST="https://www.binance.com"

def months(y0,m0,y1,m1):
    y,m=y0,m0
    while (y,m)<=(y1,m1):
        yield y,m
        m+=1
        if m==13:y+=1;m=1

def head_ok(url):
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"CryptoLab-SourceGate/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            return True, getattr(r,"status",200), r.headers.get("Content-Length")
    except Exception as e:
        return False, None, str(e)

def funding_history(symbol):
    rows=[]
    cursor=START_MS
    seen={}
    while cursor<=END_MS:
        qs=urllib.parse.urlencode({
            "symbol":symbol,
            "startTime":cursor,
            "endTime":END_MS,
            "limit":1000,
        })
        url=FUNDING_HOST+"/fapi/v1/fundingRate?"+qs
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-SourceGate/1.0"})
        with urllib.request.urlopen(req,timeout=30) as r:
            arr=json.loads(r.read().decode())
        if not isinstance(arr,list):
            raise RuntimeError(f"{symbol}: unexpected funding payload type")
        if not arr:
            break
        for x in arr:
            t=int(x["fundingTime"])
            if not (START_MS<=t<=END_MS):
                continue
            rate=float(x["fundingRate"])
            mark=float(x["markPrice"])
            if not math.isfinite(rate):
                raise RuntimeError(f"{symbol}: nonfinite funding rate at {t}")
            if not math.isfinite(mark) or mark<=0:
                raise RuntimeError(f"{symbol}: invalid markPrice at {t}")
            rec={"t":t,"rate":rate,"mark":mark,"rateType":x.get("rateType")}
            if t in seen and seen[t]!=rec:
                raise RuntimeError(f"{symbol}: conflicting duplicate funding record {t}")
            seen[t]=rec
        nxt=int(arr[-1]["fundingTime"])+1
        if nxt<=cursor:
            raise RuntimeError(f"{symbol}: funding pagination stalled")
        cursor=nxt
        if len(arr)<1000:
            break
    rows=[seen[t] for t in sorted(seen)]
    if not rows:
        raise RuntimeError(f"{symbol}: no funding records")
    return rows

out={"lab":"BTC-CONVEX-TREND-CAPTURE-001","gate":"CROSS_ASSET_SOURCE_GATE_V0.1B",
     "funding_host":FUNDING_HOST,"symbols":{}}
all_pass=True
for s in SYMBOLS:
    price_missing=[]; price_present=0
    for y,m in months(2020,12,2025,12):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/1h/{s}-1h-{ym}.zip"
        ok,status,detail=head_ok(url)
        if ok: price_present+=1
        else: price_missing.append({"month":ym,"url":url,"detail":detail})
    try:
        funds=funding_history(s)
        first=funds[0]["t"]; last=funds[-1]["t"]
        monotonic=all(funds[i]["t"]<funds[i+1]["t"] for i in range(len(funds)-1))
        funding_pass=(first<=START_MS+9*3600*1000 and last>=END_MS-9*3600*1000 and monotonic)
        funding_meta={
            "count":len(funds),
            "first_ms":first,
            "last_ms":last,
            "all_mark_prices_present":all(x["mark"]>0 for x in funds),
            "strictly_chronological":monotonic,
            "rate_types":sorted(set(x.get("rateType") for x in funds if x.get("rateType") is not None)),
        }
    except Exception as e:
        funding_pass=False
        funding_meta={"error":repr(e)}
    price_pass=(len(price_missing)==0)
    passed=price_pass and funding_pass
    all_pass &= passed
    out["symbols"][s]={
        "price_monthly_files_expected":61,
        "price_monthly_files_present":price_present,
        "price_missing_months":price_missing,
        "funding":funding_meta,
        "price_coverage_pass":price_pass,
        "funding_coverage_pass":funding_pass,
        "pass":passed,
    }
out["overall"]="PASS" if all_pass else "FAIL_CLOSED"
path=EVID/"CROSS_ASSET_SOURCE_GATE_V0.1B.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
print("WROTE",path)
if not all_pass:
    raise SystemExit("FAIL_CLOSED: cross-asset source gate V0.1B failed")

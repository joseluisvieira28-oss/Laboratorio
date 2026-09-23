#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE GATE V0.1

Coverage/provenance only. NO economic outcomes.
"""
from __future__ import annotations
import json, urllib.request, urllib.parse
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
SYMBOLS=["ETHUSDT","SOLUSDT","BNBUSDT"]
START_FUND=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)
END_FUND=int(datetime(2025,12,31,23,59,59,tzinfo=timezone.utc).timestamp()*1000)

def months():
    y,m=2020,12
    while (y,m)<=(2025,12):
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

def funding_meta(symbol):
    base="https://fapi.binance.com/fapi/v1/fundingRate"
    cursor=START_FUND
    count=0; first=None; last=None; mark_present=0; rate_types={}
    while cursor<=END_FUND:
        qs=urllib.parse.urlencode({
            "symbol":symbol,
            "startTime":cursor,
            "endTime":END_FUND,
            "limit":1000,
        })
        req=urllib.request.Request(base+"?"+qs,headers={"User-Agent":"CryptoLab-SourceGate/1.0"})
        with urllib.request.urlopen(req,timeout=30) as r:
            arr=json.loads(r.read().decode())
        if not arr: break
        for x in arr:
            t=int(x["fundingTime"])
            if t<START_FUND or t>END_FUND: continue
            count+=1
            first=t if first is None else min(first,t)
            last=t if last is None else max(last,t)
            if x.get("markPrice") not in (None,""): mark_present+=1
            rt=x.get("rateType","UNSPECIFIED")
            rate_types[rt]=rate_types.get(rt,0)+1
        nxt=int(arr[-1]["fundingTime"])+1
        if nxt<=cursor: raise RuntimeError("funding pagination stalled")
        cursor=nxt
        if len(arr)<1000: break
    return {
        "count":count,
        "first_ms":first,
        "last_ms":last,
        "mark_price_present_count":mark_present,
        "rate_types":rate_types,
    }

out={"lab":"BTC-CONVEX-TREND-CAPTURE-001","gate":"CROSS_ASSET_SOURCE_GATE_V0.1","symbols":{}}
all_pass=True
for s in SYMBOLS:
    missing=[]; present=0
    for y,m in months():
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/1h/{s}-1h-{ym}.zip"
        ok,status,detail=head_ok(url)
        if ok: present+=1
        else: missing.append({"month":ym,"url":url,"detail":detail})
    try:
        fm=funding_meta(s)
    except Exception as e:
        fm={"error":repr(e),"count":0,"first_ms":None,"last_ms":None,"mark_price_present_count":0}
    price_pass=(len(missing)==0)
    funding_pass=(fm.get("count",0)>0 and fm.get("first_ms") is not None and fm["first_ms"]<=START_FUND+9*3600*1000 and fm.get("last_ms") is not None and fm["last_ms"]>=END_FUND-9*3600*1000)
    passed=price_pass and funding_pass
    all_pass &= passed
    out["symbols"][s]={
        "monthly_files_expected":61,
        "monthly_files_present":present,
        "missing_months":missing,
        "funding":fm,
        "price_coverage_pass":price_pass,
        "funding_coverage_pass":funding_pass,
        "pass":passed,
    }
out["overall"]="PASS" if all_pass else "FAIL_CLOSED"
path=EVID/"CROSS_ASSET_SOURCE_GATE_V0.1.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
print("WROTE",path)
if not all_pass:
    raise SystemExit("FAIL_CLOSED: cross-asset source gate failed")

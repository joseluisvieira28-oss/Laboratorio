#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE GATE V0.1A

Coverage/provenance only. NO economic outcomes.
Funding transport follows CROSS_ASSET_SOURCE_AMENDMENT_001.
"""
from __future__ import annotations
import csv, io, json, urllib.request, zipfile
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
SYMBOLS=["ETHUSDT","SOLUSDT","BNBUSDT"]

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

def inspect_funding_schema(symbol):
    url=f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{symbol}/{symbol}-fundingRate-2021-01.zip"
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-SourceGate/1.0"})
    with urllib.request.urlopen(req,timeout=30) as r:
        body=r.read()
    with zipfile.ZipFile(io.BytesIO(body)) as zf:
        names=zf.namelist()
        if len(names)!=1:
            raise RuntimeError(f"unexpected funding zip members: {names}")
        text=zf.read(names[0]).decode("utf-8-sig")
    reader=csv.reader(io.StringIO(text))
    header=next(reader)
    count=0
    for _ in reader: count+=1
    return {"sample_url":url,"header":header,"sample_row_count":count}

out={"lab":"BTC-CONVEX-TREND-CAPTURE-001","gate":"CROSS_ASSET_SOURCE_GATE_V0.1A","symbols":{}}
all_pass=True
for s in SYMBOLS:
    price_missing=[]; price_present=0
    for y,m in months(2020,12,2025,12):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/1h/{s}-1h-{ym}.zip"
        ok,status,detail=head_ok(url)
        if ok: price_present+=1
        else: price_missing.append({"month":ym,"url":url,"detail":detail})

    fund_missing=[]; fund_present=0
    for y,m in months(2021,1,2025,12):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{s}/{s}-fundingRate-{ym}.zip"
        ok,status,detail=head_ok(url)
        if ok: fund_present+=1
        else: fund_missing.append({"month":ym,"url":url,"detail":detail})

    try:
        schema=inspect_funding_schema(s)
        schema_ok=any(x.lower() in ("fundingtime","calc_time","funding_time") for x in schema["header"]) and any("rate" in x.lower() for x in schema["header"])
    except Exception as e:
        schema={"error":repr(e)}
        schema_ok=False

    price_pass=(len(price_missing)==0)
    funding_pass=(len(fund_missing)==0 and schema_ok)
    passed=price_pass and funding_pass
    all_pass &= passed
    out["symbols"][s]={
        "price_monthly_files_expected":61,
        "price_monthly_files_present":price_present,
        "price_missing_months":price_missing,
        "funding_monthly_files_expected":60,
        "funding_monthly_files_present":fund_present,
        "funding_missing_months":fund_missing,
        "funding_schema":schema,
        "price_coverage_pass":price_pass,
        "funding_coverage_pass":funding_pass,
        "pass":passed,
    }

out["overall"]="PASS" if all_pass else "FAIL_CLOSED"
path=EVID/"CROSS_ASSET_SOURCE_GATE_V0.1A.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
print("WROTE",path)
if not all_pass:
    raise SystemExit("FAIL_CLOSED: cross-asset source gate V0.1A failed")

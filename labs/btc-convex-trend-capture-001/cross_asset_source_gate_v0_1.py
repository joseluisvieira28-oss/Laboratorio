#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — CROSS-ASSET SOURCE GATE V0.1D

Coverage/provenance only. NO economic outcomes.
Authority:
- CROSS_ASSET_COST_VALIDATION_FREEZE_V0.1
- CROSS_ASSET_SOURCE_AMENDMENT_004
- CROSS_ASSET_SOURCE_AMENDMENT_005
"""
from __future__ import annotations
import csv, io, json, math, hashlib, urllib.request, urllib.parse, zipfile
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
SYMBOLS=["ETHUSDT","SOLUSDT","BNBUSDT"]
START_MS=int(datetime(2021,1,1,0,0,tzinfo=timezone.utc).timestamp()*1000)
END_MS=int(datetime(2025,12,31,23,59,59,tzinfo=timezone.utc).timestamp()*1000)
FUNDING_HOST="https://www.binance.com"
HOUR_MS=3_600_000
MAX_TS_DEVIATION_MS=1_000

def months(y0,m0,y1,m1):
    y,m=y0,m0
    while (y,m)<=(y1,m1):
        yield y,m
        m+=1
        if m==13:
            y+=1; m=1

def get_bytes(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-SourceGate/1.0"})
    with urllib.request.urlopen(req,timeout=45) as r:
        return r.read()

def head_ok(url):
    req=urllib.request.Request(url,method="HEAD",headers={"User-Agent":"CryptoLab-SourceGate/1.0"})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            return True, getattr(r,"status",200), r.headers.get("Content-Length")
    except Exception as e:
        return False, None, str(e)

def normalize_hour(raw_t):
    # Deterministic nearest-hour rounding for positive epoch milliseconds.
    norm=((raw_t + HOUR_MS//2)//HOUR_MS)*HOUR_MS
    dev=abs(raw_t-norm)
    if dev>MAX_TS_DEVIATION_MS:
        raise RuntimeError(f"funding timestamp deviation {dev} ms exceeds {MAX_TS_DEVIATION_MS}: raw={raw_t} norm={norm}")
    return norm,dev

def load_mark_prices(symbol):
    marks={}
    manifest=[]
    missing=[]
    for y,m in months(2021,1,2025,12):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/markPriceKlines/{symbol}/1h/{symbol}-1h-{ym}.zip"
        try:
            body=get_bytes(url)
        except Exception as e:
            missing.append({"month":ym,"url":url,"error":repr(e)})
            continue
        manifest.append({"month":ym,"url":url,"sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body)})
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            names=zf.namelist()
            if len(names)!=1:
                raise RuntimeError(f"{symbol} {ym}: unexpected markPrice zip members {names}")
            text=zf.read(names[0]).decode("utf-8-sig")
        for q in csv.reader(io.StringIO(text)):
            if not q: continue
            try:
                t=int(q[0])
            except ValueError:
                continue
            if t>10**14:
                t//=1000
            p=float(q[1])
            if not math.isfinite(p) or p<=0:
                raise RuntimeError(f"{symbol}: invalid markPrice kline OPEN {t}")
            if t in marks and abs(marks[t]-p)>1e-12:
                raise RuntimeError(f"{symbol}: conflicting markPrice kline {t}")
            marks[t]=p
    return marks,manifest,missing

def funding_history(symbol,mark_map):
    seen={}
    cursor=START_MS
    direct=fallback=dedup=0
    exact_hour=normalized_count=0
    max_dev=0
    pages=[]
    timestamp_audit=[]
    while cursor<=END_MS:
        qs=urllib.parse.urlencode({
            "symbol":symbol,
            "startTime":cursor,
            "endTime":END_MS,
            "limit":1000,
        })
        url=FUNDING_HOST+"/fapi/v1/fundingRate?"+qs
        raw=get_bytes(url)
        pages.append({"url":url,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
        arr=json.loads(raw.decode())
        if not isinstance(arr,list):
            raise RuntimeError(f"{symbol}: unexpected funding payload")
        if not arr:
            break

        for x in arr:
            raw_t=int(x["fundingTime"])
            if raw_t<START_MS-1000 or raw_t>END_MS+1000:
                continue
            norm_t,dev=normalize_hour(raw_t)
            if not (START_MS<=norm_t<=END_MS):
                continue
            max_dev=max(max_dev,dev)
            if dev==0:
                exact_hour+=1
            else:
                normalized_count+=1
            rate=float(x["fundingRate"])
            if not math.isfinite(rate):
                raise RuntimeError(f"{symbol}: nonfinite funding rate {raw_t}")

            raw_mark=x.get("markPrice")
            if raw_mark not in (None,""):
                mark=float(raw_mark)
                source="funding_record"
                direct+=1
            else:
                if norm_t not in mark_map:
                    raise RuntimeError(f"{symbol}: missing funding mark and no exact markPriceKline {norm_t}")
                mark=mark_map[norm_t]
                source="markPriceKline_open"
                fallback+=1
            if not math.isfinite(mark) or mark<=0:
                raise RuntimeError(f"{symbol}: invalid resolved markPrice {raw_t}")

            core={"rate":rate,"mark":mark,"mark_source":source}
            if norm_t in seen:
                prev=seen[norm_t]
                same=(abs(prev["rate"]-rate)<=1e-15 and abs(prev["mark"]-mark)<=1e-10)
                if not same:
                    raise RuntimeError(f"{symbol}: conflicting duplicate after timestamp normalization {norm_t}")
                dedup+=1
            else:
                seen[norm_t]={
                    **core,
                    "rateType":x.get("rateType"),
                    "raw_funding_time_ms":raw_t,
                    "normalized_funding_time_ms":norm_t,
                    "deviation_ms":dev,
                }

            timestamp_audit.append({
                "raw_funding_time_ms":raw_t,
                "normalized_funding_time_ms":norm_t,
                "deviation_ms":dev,
            })

        raw_last=int(arr[-1]["fundingTime"])
        nxt=raw_last+1
        if nxt<=cursor:
            raise RuntimeError(f"{symbol}: funding pagination stalled")
        cursor=nxt
        if len(arr)<1000:
            break

    if not seen:
        raise RuntimeError(f"{symbol}: no funding records")

    ordered={t:seen[t] for t in sorted(seen)}
    return ordered,{
        "direct_mark_count":direct,
        "fallback_mark_count":fallback,
        "exact_hour_record_count":exact_hour,
        "normalized_record_count":normalized_count,
        "max_timestamp_deviation_ms":max_dev,
        "deduplicated_after_normalization":dedup,
        "timestamp_audit":timestamp_audit,
        "pages":pages,
    }

out={
    "lab":"BTC-CONVEX-TREND-CAPTURE-001",
    "gate":"CROSS_ASSET_SOURCE_GATE_V0.1D",
    "authority":[
        "CROSS_ASSET_COST_VALIDATION_FREEZE_V0.1",
        "CROSS_ASSET_SOURCE_AMENDMENT_004",
        "CROSS_ASSET_SOURCE_AMENDMENT_005",
    ],
    "symbols":{}
}
all_pass=True

for s in SYMBOLS:
    price_missing=[]; price_present=0
    for y,m in months(2020,12,2025,12):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/{s}/1h/{s}-1h-{ym}.zip"
        ok,status,detail=head_ok(url)
        if ok:
            price_present+=1
        else:
            price_missing.append({"month":ym,"url":url,"detail":detail})

    try:
        mark_map,mark_manifest,mark_missing=load_mark_prices(s)
        funds,fmeta=funding_history(s,mark_map)
        first=min(funds); last=max(funds)
        funding_pass=(
            not mark_missing
            and first<=START_MS+9*HOUR_MS
            and last>=END_MS-9*HOUR_MS
            and fmeta["max_timestamp_deviation_ms"]<=MAX_TS_DEVIATION_MS
        )
        funding_meta={
            "count":len(funds),
            "first_normalized_ms":first,
            "last_normalized_ms":last,
            "direct_mark_count":fmeta["direct_mark_count"],
            "fallback_mark_count":fmeta["fallback_mark_count"],
            "unresolved_mark_count":0,
            "exact_hour_record_count":fmeta["exact_hour_record_count"],
            "normalized_record_count":fmeta["normalized_record_count"],
            "max_timestamp_deviation_ms":fmeta["max_timestamp_deviation_ms"],
            "deduplicated_after_normalization":fmeta["deduplicated_after_normalization"],
            "timestamp_audit":fmeta["timestamp_audit"],
            "funding_page_count":len(fmeta["pages"]),
            "funding_pages":fmeta["pages"],
            "mark_price_monthly_files_expected":60,
            "mark_price_monthly_files_present":len(mark_manifest),
            "mark_price_missing_months":mark_missing,
            "mark_price_manifest":mark_manifest,
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
path=EVID/"CROSS_ASSET_SOURCE_GATE_V0.1D.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps({
    "gate":out["gate"],
    "authority":out["authority"],
    "overall":out["overall"],
    "symbols":{
        s:{
            "pass":v["pass"],
            "price_files":f'{v["price_monthly_files_present"]}/{v["price_monthly_files_expected"]}',
            "funding_count":v["funding"].get("count"),
            "direct_mark_count":v["funding"].get("direct_mark_count"),
            "fallback_mark_count":v["funding"].get("fallback_mark_count"),
            "normalized_record_count":v["funding"].get("normalized_record_count"),
            "max_timestamp_deviation_ms":v["funding"].get("max_timestamp_deviation_ms"),
            "error":v["funding"].get("error"),
        } for s,v in out["symbols"].items()
    }
},indent=2))
print("WROTE",path)
if not all_pass:
    raise SystemExit("FAIL_CLOSED: cross-asset source gate V0.1D failed")

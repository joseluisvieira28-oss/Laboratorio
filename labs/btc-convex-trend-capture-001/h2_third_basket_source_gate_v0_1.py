#!/usr/bin/env python3
"""
BTC-CONVEX-TREND-CAPTURE-001 — H2 THIRD-BASKET SOURCE GATE V0.1

Coverage/provenance only. NO economic outcomes.
Authority:
- CROSS_ASSET_COST_VALIDATION_FREEZE_V0.1
- CROSS_ASSET_SOURCE_AMENDMENT_004
- CROSS_ASSET_SOURCE_AMENDMENT_005
- CROSS_ASSET_SOURCE_AMENDMENT_006
- CROSS_ASSET_SOURCE_AMENDMENT_007
"""
from __future__ import annotations
import csv, io, json, math, hashlib, urllib.request, urllib.parse, zipfile
from datetime import datetime, timezone
from pathlib import Path

LAB=Path(__file__).resolve().parent
EVID=LAB/"evidence"; EVID.mkdir(exist_ok=True)
SYMBOLS=["LTCUSDT","BCHUSDT","TRXUSDT","DOTUSDT","UNIUSDT"]
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


def load_market_coverage(symbol):
    """
    Reconstruct the frozen 2021-2025 1h market timeline from official
    Binance Vision monthly files. Any exact hourly gap is completed only
    from the official daily 1h archive at the same timestamp.
    No interpolation or nearest-neighbor substitution.
    """
    market={}
    manifest=[]
    monthly_errors=[]

    for y,m in months(2020,12,2025,12):
        ym=f"{y:04d}-{m:02d}"
        url=f"https://data.binance.vision/data/futures/um/monthly/klines/{symbol}/1h/{symbol}-1h-{ym}.zip"
        try:
            body=get_bytes(url)
        except Exception as e:
            monthly_errors.append({"month":ym,"url":url,"error":repr(e)})
            continue
        manifest.append({
            "kind":"monthly_market_kline","month":ym,"url":url,
            "sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body)
        })
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            names=zf.namelist()
            if len(names)!=1:
                raise RuntimeError(f"{symbol} {ym}: unexpected market zip members {names}")
            text=zf.read(names[0]).decode("utf-8-sig")
        for q in csv.reader(io.StringIO(text)):
            if not q: continue
            try: t=int(q[0])
            except ValueError: continue
            if t>10**14: t//=1000
            rec=(float(q[1]),float(q[2]),float(q[3]),float(q[4]),float(q[5]))
            if t in market and market[t]!=rec:
                raise RuntimeError(f"{symbol}: conflicting monthly market bar {t}")
            market[t]=rec

    end_bar=int(datetime(2025,12,31,23,0,tzinfo=timezone.utc).timestamp()*1000)
    missing=[t for t in range(START_MS,end_bar+1,HOUR_MS) if t not in market]
    dates=sorted(set(datetime.fromtimestamp(t/1000,tz=timezone.utc).strftime("%Y-%m-%d") for t in missing))
    gapfill_added=0
    daily_errors=[]

    for ds in dates:
        url=f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1h/{symbol}-1h-{ds}.zip"
        try:
            body=get_bytes(url)
        except Exception as e:
            daily_errors.append({"date":ds,"url":url,"error":repr(e)})
            continue
        manifest.append({
            "kind":"daily_market_gapfill","date":ds,"url":url,
            "sha256":hashlib.sha256(body).hexdigest(),"bytes":len(body)
        })
        with zipfile.ZipFile(io.BytesIO(body)) as zf:
            names=zf.namelist()
            if len(names)!=1:
                raise RuntimeError(f"{symbol} {ds}: unexpected daily market zip members {names}")
            text=zf.read(names[0]).decode("utf-8-sig")
        for q in csv.reader(io.StringIO(text)):
            if not q: continue
            try: t=int(q[0])
            except ValueError: continue
            if t>10**14: t//=1000
            rec=(float(q[1]),float(q[2]),float(q[3]),float(q[4]),float(q[5]))
            if t in market:
                if market[t]!=rec:
                    raise RuntimeError(f"{symbol}: daily/monthly market conflict {t}")
            else:
                market[t]=rec
                gapfill_added+=1

    expected=((end_bar-START_MS)//HOUR_MS)+1
    remaining=[t for t in range(START_MS,end_bar+1,HOUR_MS) if t not in market]
    present=sum(1 for t in market if START_MS<=t<=end_bar)
    # Dec-2020 warmup archive must exist and provide enough pre-boundary history.
    warmup_start=int(datetime(2020,12,1,0,0,tzinfo=timezone.utc).timestamp()*1000)
    warmup_hours=sum(1 for t in market if warmup_start<=t<START_MS)
    passed=(
        present==expected
        and not remaining
        and START_MS in market
        and end_bar in market
        and warmup_hours>=200
    )
    return {
        "pass":passed,
        "expected_hours":expected,
        "present_hours":present,
        "missing_hours":len(remaining),
        "first_missing_ms":remaining[0] if remaining else None,
        "last_missing_ms":remaining[-1] if remaining else None,
        "gapfill_dates":dates,
        "gapfill_hours_added":gapfill_added,
        "monthly_errors":monthly_errors,
        "daily_gapfill_errors":daily_errors,
        "warmup_hours_before_boundary":warmup_hours,
        "manifest_count":len(manifest),
        "manifest_sha256":hashlib.sha256(
            json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()
        ).hexdigest(),
        "manifest":manifest,
    }

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
    direct=monthly_fallback=daily_fallback=dedup=0
    exact_hour=normalized_count=0
    max_dev=0
    pages=[]
    timestamp_audit=[]
    daily_cache={}
    daily_manifest=[]
    daily_fallback_audit=[]

    def resolve_daily_exact(norm_t):
        date_str=datetime.fromtimestamp(norm_t/1000,tz=timezone.utc).strftime("%Y-%m-%d")
        if date_str not in daily_cache:
            url=f"https://data.binance.vision/data/futures/um/daily/markPriceKlines/{symbol}/1h/{symbol}-1h-{date_str}.zip"
            body=get_bytes(url)
            sha=hashlib.sha256(body).hexdigest()
            daily_manifest.append({"date":date_str,"url":url,"sha256":sha,"bytes":len(body)})
            with zipfile.ZipFile(io.BytesIO(body)) as zf:
                names=zf.namelist()
                if len(names)!=1:
                    raise RuntimeError(f"{symbol} {date_str}: unexpected daily markPrice zip members {names}")
                text=zf.read(names[0]).decode("utf-8-sig")
            rows={}
            for q in csv.reader(io.StringIO(text)):
                if not q: continue
                try: t=int(q[0])
                except ValueError: continue
                if t>10**14: t//=1000
                p=float(q[1])
                if not math.isfinite(p) or p<=0:
                    raise RuntimeError(f"{symbol}: invalid daily markPrice OPEN {t}")
                rows[t]=p
            daily_cache[date_str]={"rows":rows,"url":url,"sha256":sha}
        item=daily_cache[date_str]
        if norm_t not in item["rows"]:
            raise RuntimeError(f"{symbol}: missing funding mark and no exact daily markPriceKline {norm_t}")
        mark=item["rows"][norm_t]
        daily_fallback_audit.append({
            "normalized_funding_time_ms":norm_t,
            "date":date_str,
            "url":item["url"],
            "sha256":item["sha256"],
            "open":mark,
        })
        return mark

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
            if dev==0: exact_hour+=1
            else: normalized_count+=1

            rate=float(x["fundingRate"])
            if not math.isfinite(rate):
                raise RuntimeError(f"{symbol}: nonfinite funding rate {raw_t}")

            raw_mark=x.get("markPrice")
            if raw_mark not in (None,""):
                mark=float(raw_mark)
                source="funding_record"
                direct+=1
            elif norm_t in mark_map:
                mark=mark_map[norm_t]
                source="monthly_markPriceKline_open"
                monthly_fallback+=1
            else:
                mark=resolve_daily_exact(norm_t)
                source="daily_markPriceKline_open"
                daily_fallback+=1

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
        "monthly_fallback_mark_count":monthly_fallback,
        "daily_fallback_mark_count":daily_fallback,
        "daily_fallback_audit":daily_fallback_audit,
        "daily_mark_manifest":daily_manifest,
        "exact_hour_record_count":exact_hour,
        "normalized_record_count":normalized_count,
        "max_timestamp_deviation_ms":max_dev,
        "deduplicated_after_normalization":dedup,
        "timestamp_audit":timestamp_audit,
        "pages":pages,
    }

out={
    "lab":"BTC-CONVEX-TREND-CAPTURE-001",
    "gate":"H2_THIRD_BASKET_SOURCE_GATE_V0.1",
    "authority":[
        "CHILD_H2_RISING_REGIME_FREEZE",
        "CROSS_ASSET_SOURCE_AMENDMENT_004",
        "CROSS_ASSET_SOURCE_AMENDMENT_005",
        "CROSS_ASSET_SOURCE_AMENDMENT_006",
        "CROSS_ASSET_SOURCE_AMENDMENT_007",
    ],
    "symbols":{}
}
valid_count=0

for s in SYMBOLS:
    try:
        market_meta=load_market_coverage(s)
        price_pass=bool(market_meta["pass"])
    except Exception as e:
        price_pass=False
        market_meta={"error":repr(e)}

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
            "monthly_fallback_mark_count":fmeta["monthly_fallback_mark_count"],
            "daily_fallback_mark_count":fmeta["daily_fallback_mark_count"],
            "daily_fallback_audit":fmeta["daily_fallback_audit"],
            "daily_mark_manifest":fmeta["daily_mark_manifest"],
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

    passed=price_pass and funding_pass
    valid_count += int(passed)
    out["symbols"][s]={
        "market_coverage":market_meta,
        "funding":funding_meta,
        "price_coverage_pass":price_pass,
        "funding_coverage_pass":funding_pass,
        "pass":passed,
    }

out["valid_asset_count"]=valid_count
out["blocked_asset_count"]=len(SYMBOLS)-valid_count
out["overall"]="PASS" if valid_count>=4 else "FAIL_CLOSED"
path=EVID/"H2_THIRD_BASKET_SOURCE_GATE_V0.1.json"
path.write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps({
    "gate":out["gate"],
    "authority":out["authority"],
    "overall":out["overall"],
    "symbols":{
        s:{
            "pass":v["pass"],
            "market_hours":(
                f'{v["market_coverage"].get("present_hours")}/{v["market_coverage"].get("expected_hours")}'
                if isinstance(v.get("market_coverage"),dict) else None
            ),
            "market_gapfill_hours_added":v.get("market_coverage",{}).get("gapfill_hours_added"),
            "funding_count":v["funding"].get("count"),
            "direct_mark_count":v["funding"].get("direct_mark_count"),
            "monthly_fallback_mark_count":v["funding"].get("monthly_fallback_mark_count"),
            "daily_fallback_mark_count":v["funding"].get("daily_fallback_mark_count"),
            "normalized_record_count":v["funding"].get("normalized_record_count"),
            "max_timestamp_deviation_ms":v["funding"].get("max_timestamp_deviation_ms"),
            "error":v["funding"].get("error"),
        } for s,v in out["symbols"].items()
    }
},indent=2))
print("WROTE",path)
if valid_count<4:
    raise SystemExit("FAIL_CLOSED: H2 third-basket source gate V0.1 failed")

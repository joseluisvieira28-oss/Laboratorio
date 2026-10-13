#!/usr/bin/env python3
"""Read-only, FAIL-CLOSED BTCUSDT USD-M *future* shadow intake.

The first permitted market open is 2026-10-14T00:00Z. Daily Binance
Vision archives become available after the day ends; no pre-boundary bars
or private/authenticated endpoints are ever queried. This is NOT a trader.
The paired forward_boundary_gate.py decides if the 200h warm-up passed.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,urllib.parse,urllib.request,zipfile
from datetime import datetime,timedelta,timezone
from pathlib import Path

UTC=timezone.utc
FIRST_DAY=datetime(2026,10,14,tzinfo=UTC)
H=3_600_000
DAY=24*H
MAX_DAYS=45
BASE="https://data.binance.vision/data/futures/um/daily"
FUND_URL="https://fapi.binance.com/fapi/v1/fundingRate"
SYMBOL="BTCUSDT"
USER_AGENT="CryptoLab-Payoff-Research-PublicOnly/0.1"

class SourceBlocked(RuntimeError):pass

def window(now:datetime)->list[datetime]:
    if now.tzinfo is None:raise SourceBlocked("NAIVE_TIME_FORBIDDEN")
    today=now.astimezone(UTC).replace(hour=0,minute=0,second=0,microsecond=0)
    previous=today-timedelta(days=1)
    if previous < FIRST_DAY+timedelta(days=8):
        raise SourceBlocked("POST_BOUNDARY_WARMUP_OR_DAILY_ARCHIVE_PENDING")
    days=(previous-FIRST_DAY).days+1
    if days>MAX_DAYS:raise SourceBlocked("SOURCE_HORIZON_LIMIT_REQUIRES_NEW_FROZEN_ROLLOVER")
    return [FIRST_DAY+timedelta(days=i) for i in range(days)]

def get(url,max_size=3_000_000)->bytes:
    if not (url.startswith(BASE+"/") or url.startswith(FUND_URL+"?")):
        raise SourceBlocked("UNAPPROVED_NETWORK_OR_ENDPOINT")
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/json,*/*"})
    with urllib.request.urlopen(req,timeout=35) as response:
        if response.status!=200:raise SourceBlocked("HTTP_NOT_200")
        data=response.read(max_size+1)
    if len(data)>max_size:raise SourceBlocked("UNEXPECTED_SOURCE_SIZE")
    return data

def parse_day_archive(day:datetime,kind:str,read=get):
    if kind not in ("klines","markPriceKlines"):raise SourceBlocked("KIND_NOT_ALLOWED")
    ds=day.strftime("%Y-%m-%d")
    stem=f"{SYMBOL}-1h-{ds}.zip"
    url=f"{BASE}/{kind}/{SYMBOL}/1h/{stem}"
    raw=read(url)
    checksum=read(url+".CHECKSUM",4096).decode("ascii").strip().split()[0].lower()
    digest=hashlib.sha256(raw).hexdigest()
    if len(checksum)!=64 or digest!=checksum:raise SourceBlocked("ZIP_CHECKSUM_MISMATCH:"+ds+":"+kind)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members=[n for n in z.namelist() if n.endswith(".csv") and not n.startswith("__")]
        if len(members)!=1:raise SourceBlocked("INVALID_ARCHIVE_MEMBERS")
        info=z.getinfo(members[0])
        if info.file_size>1_000_000:raise SourceBlocked("ZIP_UNCOMPRESSED_TOO_LARGE")
        rows=list(csv.reader(io.StringIO(z.read(members[0]).decode("utf-8-sig"))))
    base=int(day.timestamp()*1000)
    output={}
    for row in rows:
        if not row:continue
        if not row[0].isdigit():raise SourceBlocked("INVALID_ROW_TIMESTAMP")
        t=int(row[0])
        if t>10**14:t//=1000
        if not (base<=t<base+DAY and t%H==0) or t in output:
            raise SourceBlocked("TIMESTAMP_INVALID_DUPLICATE_OR_OUTSIDE_DAY")
        if len(row)<5:raise SourceBlocked("INVALID_KLINE_COLUMN_COUNT")
        o,hi,lo,c=map(float,row[1:5])
        if not all(math.isfinite(n) for n in (o,hi,lo,c)) or not(0<lo<=min(o,c)<=max(o,c)<=hi):
            raise SourceBlocked("INVALID_KLINE_OHLC")
        rec={"t":t,"open":o,"high":hi,"low":lo,"close":c}
        if kind=="klines":
            if len(row)<6:raise SourceBlocked("MARKET_VOLUME_MISSING")
            rec["volume"]=float(row[5])
            if not math.isfinite(rec["volume"]) or rec["volume"]<0:
                raise SourceBlocked("INVALID_MARKET_VOLUME")
        output[t]=rec
    if set(output)!={base+i*H for i in range(24)}:
        raise SourceBlocked("DAILY_BAR_COVERAGE_INCOMPLETE:"+ds+":"+kind)
    return output,{"kind":kind,"utc_day":ds,"url":url,
                   "official_zip_sha256":digest,"official_checksum_sha256":checksum,
                   "hourly_bars":len(output)}

def read_funding(start:int,exclusive_end:int,read=get):
    seen={};receipts=[];cursor=start
    while cursor<exclusive_end:
        qs=urllib.parse.urlencode({"symbol":SYMBOL,"startTime":cursor,
                                   "endTime":exclusive_end-1,"limit":1000})
        url=FUND_URL+"?"+qs
        raw=read(url,1_000_000)
        receipts.append({"url":url,"sha256":hashlib.sha256(raw).hexdigest()})
        payload=json.loads(raw)
        if not isinstance(payload,list):raise SourceBlocked("FUNDING_RESPONSE_NOT_LIST")
        if not payload:break
        previous=None
        for item in payload:
            if item.get("symbol")!=SYMBOL:raise SourceBlocked("FUNDING_SYMBOL_MISMATCH")
            t0=int(item["fundingTime"])
            t=round(t0/H)*H
            if abs(t-t0)>1000 or t<start or t>=exclusive_end:
                raise SourceBlocked("FUNDING_TIMESTAMP_OUT_OF_SCOPE")
            if previous is not None and t0<=previous:
                raise SourceBlocked("FUNDING_API_OUT_OF_ORDER")
            previous=t0
            rate=float(item["fundingRate"])
            if not math.isfinite(rate) or abs(rate)>1:
                raise SourceBlocked("INVALID_FUNDING_RATE")
            if t in seen and seen[t]!=rate:raise SourceBlocked("CONFLICTING_FUNDING_EVENT")
            seen[t]=rate
        nxt=int(payload[-1]["fundingTime"])+1
        if nxt<=cursor:raise SourceBlocked("FUNDING_CURSOR_STALLED")
        cursor=nxt
        if len(payload)<1000:break
    if not seen:raise SourceBlocked("NO_FUNDING_EVENTS")
    ts=sorted(seen)
    # Conservative completeness checks. BTC funding normally settles several
    # times daily; missing public periods are a blocking SOURCE condition.
    if ts[0]>start+DAY or ts[-1]<exclusive_end-DAY:
        raise SourceBlocked("FUNDING_EDGE_COVERAGE_UNVERIFIED")
    if any(b-a>DAY for a,b in zip(ts,ts[1:])):
        raise SourceBlocked("FUNDING_INTERVAL_GAP_OVER_24H")
    return {str(k):seen[k] for k in ts},receipts

def collect(now=None,read=get):
    current=now or datetime.now(UTC)
    dates=window(current) # no network before full 200h warmup possible
    market={};marks={};manifest=[]
    for day in dates:
        m,receipt=parse_day_archive(day,"klines",read)
        mk,mark_receipt=parse_day_archive(day,"markPriceKlines",read)
        if set(market)&set(m) or set(marks)&set(mk):
            raise SourceBlocked("OVERLAPPING_DAYS")
        market.update(m);marks.update(mk)
        manifest.extend((receipt,mark_receipt))
    start=int(FIRST_DAY.timestamp()*1000)
    end=int((dates[-1]+timedelta(days=1)).timestamp()*1000)
    funding, funding_manifest=read_funding(start,end,read)
    if set(market)!=set(marks) or len(market)!=len(dates)*24:
        raise SourceBlocked("PRICE_MARK_ALIGNMENT_FAILURE")
    return {"status":"SOURCE_OK","authority":"PUBLIC_READ_ONLY_SHADOW",
      "forward_boundary_utc":"2026-10-14T00:00:00Z",
      "verified_complete_through_ms":end,"funding_verified_through_ms":end,
      "source_mode":"CHECKSUM_VERIFIED_DAILY_ARCHIVE_PLUS_PUBLIC_FUNDING_ENDPOINT",
      "bars":[market[t] for t in sorted(market)],
      "marks":{str(t):marks[t] for t in sorted(marks)},
      "funding":funding,"manifests":manifest,"funding_manifests":funding_manifest,
      "observed_utc_days":[day.strftime("%Y-%m-%d") for day in dates],
      "trading_authority":"NONE"}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--source-output",type=Path,required=True)
    p.add_argument("--shadow-output",type=Path,required=True)
    a=p.parse_args()
    o={"status":"SOURCE_BLOCKED"}
    try:
        o=collect()
        import forward_boundary_gate
        result=forward_boundary_gate.run(o)
    except Exception as exc:
        o={"status":"SOURCE_BLOCKED","reason":repr(exc),
           "authority":"PUBLIC_READ_ONLY_SHADOW","trading_authority":"NONE"}
        result=None
    a.source_output.parent.mkdir(parents=True,exist_ok=True)
    a.source_output.write_text(json.dumps(o,sort_keys=True)+"\n")
    if result is not None:
        a.shadow_output.parent.mkdir(parents=True,exist_ok=True)
        a.shadow_output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print(json.dumps({"source_status":o["status"],"reason":o.get("reason"),
                      "trading_authority":"NONE",
                      "forward_science":result.get("science") if result else None},sort_keys=True))
    if result is None:raise SystemExit(2)

if __name__=="__main__":main()

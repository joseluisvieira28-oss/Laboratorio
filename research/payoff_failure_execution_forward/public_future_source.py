#!/usr/bin/env python3
"""Public-only BTCUSDT USD-M 1h forward collector. Absolutely no trading.
Can only collect 2026-10-14 UTC and later data. Refuses any pre-boundary warmup.
Manual workflow_dispatch only; no live scheduling or default-branch change.
"""
from __future__ import annotations
import argparse,datetime as dt,hashlib,json,math,urllib.parse,urllib.request
from pathlib import Path
import forward_boundary_gate as guard

BASE="https://fapi.binance.com"
BOUNDARY=guard.BOUNDARY
H=guard.H
MAX_BYTES=2_000_000
SYMBOL="BTCUSDT"
TIMEOUT=25

def fetch_json(path,params,manifest):
    if path not in ("/fapi/v1/klines","/fapi/v1/markPriceKlines",
                    "/fapi/v1/fundingRate"):
        raise ValueError("FORBIDDEN_ENDPOINT")
    url=BASE+path+"?"+urllib.parse.urlencode(params)
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Public-ReadOnly-Shadow/0.1"})
    with urllib.request.urlopen(req,timeout=TIMEOUT) as response:
        b=response.read(MAX_BYTES+1)
        if response.status!=200 or len(b)>MAX_BYTES:
            raise ValueError("PUBLIC_SOURCE_HTTP_OR_SIZE_BLOCKED")
    obj=json.loads(b.decode("utf-8"))
    if not isinstance(obj,list):raise ValueError("UNEXPECTED_API_SHAPE")
    manifest.append({"endpoint":path,"params":params,"sha256":hashlib.sha256(b).hexdigest(),
                     "bytes":len(b),"observed_records":len(obj)})
    return obj

def paginated_klines(path,end,manifest):
    output={};start=BOUNDARY
    while start<=end:
        rows=fetch_json(path,{"symbol":SYMBOL,"interval":"1h",
                             "startTime":start,"endTime":end+H-1,"limit":1000},manifest)
        if not rows:raise ValueError("PUBLIC_KLINE_PAGINATION_GAP")
        last=None
        for row in rows:
            if not isinstance(row,list) or len(row)<7:raise ValueError("KLINE_SCHEMA")
            t=int(row[0])
            if t<BOUNDARY or t>end or t%H:raise ValueError("OUT_OF_BOUNDARY_KLINE")
            if int(row[6])<t+H-1:raise ValueError("UNCONFIRMED_KLINE")
            o,hi,lo,c=(float(row[i]) for i in (1,2,3,4))
            if not (0<lo<=min(o,c)<=max(o,c)<=hi and all(math.isfinite(x) for x in (o,hi,lo,c))):
                raise ValueError("INVALID_OHLC")
            rec={"t":t,"open":o,"high":hi,"low":lo,"close":c}
            if path.endswith("/klines"):
                vol=float(row[5])
                if not math.isfinite(vol) or vol<0:raise ValueError("INVALID_VOLUME")
                rec["volume"]=vol
            if t in output and rec!=output[t]:raise ValueError("CONFLICTING_PUBLIC_BAR")
            output[t]=rec;last=t
        if last is None or last<start:raise ValueError("PAGINATION_STALLED")
        start=last+H
    expected=(end-BOUNDARY)//H+1
    if len(output)!=expected or min(output)!=BOUNDARY or max(output)!=end:
        raise ValueError("SOURCE_HOURLY_COVERAGE_INCOMPLETE")
    return [output[t] for t in sorted(output)]

def paginated_funding(end,manifest):
    output={};start=BOUNDARY
    while start<=end+H-1:
        rows=fetch_json("/fapi/v1/fundingRate",
                        {"symbol":SYMBOL,"startTime":start,"endTime":end+H-1,"limit":1000},manifest)
        if not rows:break
        newest=start-1
        for r in rows:
            raw=int(r["fundingTime"]);ts=((raw+H//2)//H)*H
            if abs(raw-ts)>1000 or ts<BOUNDARY or ts>end+H:
                raise ValueError("FUNDING_TIMESTAMP_OUT_OF_SCOPE")
            rate=float(r["fundingRate"])
            if not math.isfinite(rate):raise ValueError("BAD_FUNDING_RATE")
            if ts in output and output[ts]!=rate:
                raise ValueError("CONFLICTING_FUNDING_RATE")
            output[ts]=rate
            newest=max(raw,newest)
        if newest<start:raise ValueError("FUNDING_PAGINATION_STALLED")
        start=newest+1
        if len(rows)<1000:break
    return output

def collect(clock=None):
    now=clock if clock is not None else dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:raise ValueError("UTC_AWARE_CLOCK_REQUIRED")
    now=now.astimezone(dt.timezone.utc)
    now_ms=int(now.timestamp()*1000)
    last_open=(now_ms//H-1)*H
    # Safety: this check happens BEFORE ANY external network interaction.
    if last_open<BOUNDARY+201*H:
        raise ValueError("FORWARD_NOT_READY_AT_LEAST_202_POST_BOUNDARY_BARS")
    manifest=[]
    price=paginated_klines("/fapi/v1/klines",last_open,manifest)
    mark=paginated_klines("/fapi/v1/markPriceKlines",last_open,manifest)
    fund=paginated_funding(last_open,manifest)
    src={"status":"SOURCE_OK","authority":"PUBLIC_READ_ONLY_SHADOW",
         "forward_boundary_utc":"2026-10-14T00:00:00Z",
         "verified_complete_through_ms":last_open+H,
         "funding_verified_through_ms":last_open+H,
         "funding_attestation":"Public fundingRate API queried to end of requested closed-bar range; publication latency not independently validated",
         "symbol":SYMBOL,"venue":"BINANCE_USDM_PROXY_NOT_MEXC",
         "queried_at_utc":now.isoformat(),
         "bars":price,
         "marks":{str(b["t"]):{k:v for k,v in b.items() if k!="t"} for b in mark},
         "funding":{str(k):v for k,v in fund.items()},
         "request_manifests":manifest}
    guard.validate(src)
    return src

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result=collect();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True)+"\n")
    print(json.dumps({"status":result["status"],"no_account_or_order":True,
                      "public_bars":len(result["bars"]),"funding":len(result["funding"]),
                      "requested_pages":len(result["request_manifests"])},sort_keys=True))
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Research-only official Binance USD-M BTCUSDT archive collector.

Only public source, 2020-02 to 2025-12. Never open private API,
accounts, positions, wallets or order endpoints. Checksum verified.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,urllib.request,zipfile
from datetime import datetime,timezone
from pathlib import Path

BASE="https://data.binance.vision/data/futures/um/"
SYMBOL="BTCUSDT"
HOUR=3_600_000
MAX_BYTES=4_000_000

def months():
    y,m=2020,2
    while (y,m)<=(2025,12):
        yield f"{y:04d}-{m:02d}"
        m+=1
        if m==13:y,m=y+1,1

def archive(kind,month,scope="monthly"):
    if scope not in ("monthly","daily") or (scope=="daily" and kind!="markPriceKlines"):
        raise ValueError("FORBIDDEN_ARCHIVE_SCOPE")
    if kind in ("klines","markPriceKlines"):
        name=f"{kind}/{SYMBOL}/1h/{SYMBOL}-1h-{month}.zip"
    elif kind=="fundingRate":
        name=f"{kind}/{SYMBOL}/{SYMBOL}-fundingRate-{month}.zip"
    else:raise ValueError("UNAUTHORIZED_SOURCE")
    url=BASE+scope+"/"+name
    def request(url,limit):
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PAYOFF-ResearchOnly/0.1"})
        with urllib.request.urlopen(req,timeout=45) as r:data=r.read(limit+1)
        if len(data)>limit:raise ValueError("SOURCE_TOO_LARGE")
        return data
    data=request(url,MAX_BYTES)
    sha=hashlib.sha256(data).hexdigest()
    claimed=request(url+".CHECKSUM",500).decode("utf-8-sig").strip().split()[0].lower()
    if len(claimed)!=64 or sha!=claimed:raise ValueError("CHECKSUM_MISMATCH "+url)
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        members=[p for p in z.namelist() if p.endswith(".csv")]
        if len(members)!=1:raise ValueError("ZIP_MEMBER_INVARIANT "+url)
        contents=z.read(members[0]).decode("utf-8-sig")
    return contents,dict(kind=kind,month=month,scope=scope,sha256=sha,bytes=len(data),url=url)

def timestamp(v):
    ts=int(v)
    if ts>10**14:ts//=1000
    return ts

def parse_ohlc(raw,volume):
    out={}
    for r in csv.reader(io.StringIO(raw)):
        if not r or not r[0].strip().isdigit():continue
        if len(r)<(6 if volume else 5):raise ValueError("OHLC_SCHEMA")
        t=timestamp(r[0]);op,hi,lo,cl=map(float,r[1:5])
        vol=float(r[5]) if volume else 0.
        if not all(math.isfinite(a) for a in (op,hi,lo,cl,vol)):raise ValueError("NONFINITE")
        if not (0<lo<=min(op,cl)<=max(op,cl)<=hi and vol>=0 and t%HOUR==0):
            raise ValueError("INVALID_KLINE")
        p=dict(t=t,open=op,high=hi,low=lo,close=cl)
        if volume:p["volume"]=vol
        if t in out:raise ValueError("DUPLICATE_KLINE")
        out[t]=p
    if not out:raise ValueError("EMPTY_KLINE_ARCHIVE")
    return out

def parse_funding(raw):
    rows=list(csv.reader(io.StringIO(raw)))
    if not rows:raise ValueError("EMPTY_FUNDING")
    cols=[c.strip().lower() for c in rows[0]]
    ti=next((cols.index(c) for c in ("calc_time","fundingtime") if c in cols),None)
    ri=next((cols.index(c) for c in ("last_funding_rate","fundingrate","rate") if c in cols),None)
    if ti is None or ri is None:raise ValueError("UNKNOWN_FUNDING_HEADER "+repr(rows[0]))
    out={}
    for r in rows[1:]:
        if not r:continue
        if len(r)<=max(ti,ri):raise ValueError("FUNDING_SCHEMA")
        t=timestamp(r[ti]);rate=float(r[ri])
        if not math.isfinite(rate) or t<=0 or t in out:raise ValueError("INVALID_FUNDING")
        out[t]=rate
    if not out:raise ValueError("NO_FUNDING_RECORDS")
    return out

def collect():
    market={};marks={};funding={};manifest=[]
    for kind in ("klines","markPriceKlines","fundingRate"):
        for ym in months():
            raw,identity=archive(kind,ym);manifest.append(identity)
            part=parse_funding(raw) if kind=="fundingRate" else parse_ohlc(raw,kind=="klines")
            dest={"klines":market,"markPriceKlines":marks,"fundingRate":funding}[kind]
            for t,v in part.items():
                if t in dest:raise ValueError("DUPLICATE_SOURCE_RECORD "+str(t))
                dest[t]=v
    start=int(datetime(2020,2,1,tzinfo=timezone.utc).timestamp()*1000)
    end=int(datetime(2025,12,31,23,tzinfo=timezone.utc).timestamp()*1000)
    # PRE-OUTCOME SOURCE AMENDMENT 001: fill exact missing mark-price hours
    # using only checksum-matched official daily markPriceKlines. The policy is
    # source-availability-based, never conditioned on strategy PnL.
    missing_mark_hours=[t for t in range(start,end+HOUR,HOUR) if t not in marks]
    missing_dates=sorted(set(datetime.fromtimestamp(t/1000,tz=timezone.utc).strftime("%Y-%m-%d")
                             for t in missing_mark_hours))
    if len(missing_dates)>120:
        raise ValueError("MARK_GAPFILL_SCOPE_TOO_LARGE:"+str(len(missing_dates)))
    gapfill_hours=0
    for day in missing_dates:
        raw,receipt=archive("markPriceKlines",day,scope="daily")
        part=parse_ohlc(raw,False)
        for t,point in part.items():
            if not (start<=t<=end):continue
            if t in marks:
                if marks[t]!=point:
                    raise ValueError("MONTHLY_DAILY_MARK_CONFLICT:"+str(t))
            else:
                marks[t]=point
                gapfill_hours+=1
        manifest.append(receipt)
    span=(end-start)//HOUR+1
    for kind,src in (("market",market),("mark",marks)):
        gaps=[t for t in range(start,end+HOUR,HOUR) if t not in src]
        if gaps:raise ValueError("HOURLY_SOURCE_GAPS_"+kind+":"+str(gaps[:5]))
        if len([t for t in src if start<=t<=end])!=span:
            raise ValueError("COVERAGE_COUNT_MISMATCH")
    if not funding:raise ValueError("NO_FUNDING")
    offgrid=[t for t in funding if t%HOUR!=0]
    if offgrid:raise ValueError("OFFGRID_FUNDING_TIMESTAMP:"+str(offgrid[:4]))
    unmapped=[t for t in funding if start<=t<=end and t not in marks]
    if unmapped:raise ValueError("FUNDING_MARK_MISSING:"+str(unmapped[:4]))
    return {"status":"SOURCE_OK","venue":"Binance USD-M proxy, not historical MEXC fills",
            "manifests":manifest,
            "bars":[market[t] for t in sorted(market) if start<=t<=end],
            "marks":{str(t):marks[t] for t in marks if start<=t<=end},
            "funding":{str(t):v for t,v in funding.items() if start<=t<=end},
            "counts":{"market":span,"mark":span,"funding":len(funding),"daily_mark_gapfill_dates":len(missing_dates),"daily_mark_gapfill_hours":gapfill_hours}}

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    o={"status":"SOURCE_BLOCKED"}
    try:o=collect()
    except Exception as exc:o["reason"]=repr(exc)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(o,sort_keys=True))
    print(json.dumps({"status":o["status"],"reason":o.get("reason"),"counts":o.get("counts"),"file_count":len(o.get("manifests",[]))}))
    if o["status"]!="SOURCE_OK":raise SystemExit(2)

if __name__=="__main__":main()

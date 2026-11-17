#!/usr/bin/env python3
"""CARRY-001: historical funding observations from official Binance Vision and Hyperliquid.
Read-only, no account, wallet, orders, API keys, transfers, background tasks.
Frozen coverage: 2024-09-01 UTC inclusive to 2026-11-01 exclusive.
"""
import csv,datetime as dt,gzip,hashlib,io,json,os,pathlib,time,urllib.request,urllib.error,zipfile
from collections import defaultdict
OUT=pathlib.Path("carry001-evidence");OUT.mkdir(exist_ok=True)
RAW=OUT/"raw";RAW.mkdir(exist_ok=True)
UTC=dt.timezone.utc
START=dt.datetime(2024,9,1,tzinfo=UTC)
END=dt.datetime(2026,11,1,tzinfo=UTC)
START_MS=int(START.timestamp()*1000); END_MS=int(END.timestamp()*1000)
COINS=("BTC","ETH","SOL")
USER_AGENT="CryptoLab-CARRY001/0.1 research read-only"
RETRY=(0,2,5,12,25,50)
def raw_request(url,body=None):
    data=json.dumps(body,separators=(",",":")).encode() if body else None
    req=urllib.request.Request(url,data=data,headers={"User-Agent":USER_AGENT,
        "Accept":"application/json","Content-Type":"application/json" if body else "application/octet-stream"})
    err=None
    for delay in RETRY:
        if delay:time.sleep(delay)
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                return r.read(4_000_000)
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError) as e:
            err=repr(e)
            if isinstance(e,urllib.error.HTTPError) and e.code in (403,404,451):break
    raise RuntimeError(f"read-only fetch failed {url}: {err}")
def month_iter():
    cur=START
    while cur<END:
        yield cur.strftime("%Y-%m")
        cur=dt.datetime(cur.year+1,1,1,tzinfo=UTC) if cur.month==12 else dt.datetime(cur.year,cur.month+1,1,tzinfo=UTC)
def parse_float(text):
    try:
        x=float(text)
        if not (-.25<=x<=.25):raise ValueError("unrealistic funding rate")
        return x
    except Exception as e:
        raise ValueError("invalid funding rate "+repr(text)) from e
def process_binance(coin):
    all_rows={};provenance=[];failed=[]
    symbol=coin+"USDT"
    for month in month_iter():
        filename=f"{symbol}-fundingRate-{month}.zip"
        url=f"https://data.binance.vision/data/futures/um/monthly/fundingRate/{symbol}/{filename}"
        try:
            raw=raw_request(url)
            digest=hashlib.sha256(raw).hexdigest()
            path=RAW/filename;path.write_bytes(raw)
            with zipfile.ZipFile(io.BytesIO(raw)) as z:
                if len(z.namelist())!=1 or not z.namelist()[0].endswith(".csv"):
                    raise ValueError("invalid archive")
                rows=list(csv.DictReader(io.StringIO(z.read(z.namelist()[0]).decode("utf8-sig"))))
            good=0
            for r in rows:
                timestamp=int(r["calc_time"])
                if timestamp<START_MS or timestamp>=END_MS:continue
                rate=parse_float(r["last_funding_rate"])
                interval=int(r["funding_interval_hours"])
                if interval not in [1,2,4,8,12,24]:raise ValueError(f"Invalid interval {interval}")
                # We use each exact payment, not a synthetic per-hour rate.
                if timestamp in all_rows and all_rows[timestamp]!=(rate,interval):
                    raise ValueError("conflicting duplicated payments")
                all_rows[timestamp]=(rate,interval)
                good+=1
            provenance.append({"month":month,"filename":filename,"sha256":digest,
              "archive_rows":len(rows),"retained":good,"bytes":len(raw)})
        except Exception as e:
            failed.append({"month":month,"error":str(e)[:250]})
        print("BINANCE",coin,month,"ok" if not any(v["month"]==month for v in failed) else "BLOCKED",flush=True)
    rows=[{"venue":"Binance","coin":coin,"timestamp_ms":k,"rate":v[0],
        "interval_hours":v[1]} for k,v in sorted(all_rows.items())]
    return rows,{"sources":provenance,"missing_months":failed,"rows":len(rows)}
def process_hl(coin):
    cursor=START_MS;rows={};provenance=[];n=0
    while cursor<END_MS and n<130:
        body={"type":"fundingHistory","coin":coin,"startTime":cursor,"endTime":END_MS-1}
        raw=raw_request("https://api.hyperliquid.xyz/info",body)
        digest=hashlib.sha256(raw).hexdigest()
        payload=json.loads(raw)
        if not isinstance(payload,list):raise ValueError("HL response non-array")
        for record in payload:
            t=int(record["time"])
            if not (START_MS<=t<END_MS):continue
            rate=parse_float(record["fundingRate"])
            if t in rows and rows[t]!=rate:raise ValueError("conflicting duplicate HL settlement")
            rows[t]=rate
        (RAW/f"HL_{coin}_page_{n:03}.json.gz").write_bytes(gzip.compress(raw,mtime=0))
        provenance.append({"page":n,"start":cursor,"count":len(payload),
          "sha256":digest,"first":int(payload[0]["time"]) if payload else None,
          "last":int(payload[-1]["time"]) if payload else None})
        if not payload:break
        last=int(payload[-1]["time"])
        if last<cursor:raise ValueError("Nonmonotonic HL page")
        cursor=last+1
        n+=1
        if n%10==0:print("HL_PROGRESS",coin,n,len(rows),dt.datetime.fromtimestamp(last/1000,tz=UTC).strftime("%Y-%m-%d"),flush=True)
        if len(payload)<500:break
        time.sleep(0.65)
    if n>=130:raise RuntimeError("HL pagination cap hit")
    out=[{"venue":"Hyperliquid","coin":coin,"timestamp_ms":t,"rate":v,
        "interval_hours":1} for t,v in sorted(rows.items())]
    return out,{"pages":provenance,"rows":len(out),"last_cursor":cursor}
def main():
    manifesto={"created_utc":dt.datetime.now(tz=UTC).isoformat(),"start":START.isoformat(),"end_exclusive":END.isoformat(),
        "source_code":"CARRY-001 pinned research workflow","coins":COINS,"providers":{},"not_trades":True}
    all_rates=[]
    for coin in COINS:
        b,bmeta=process_binance(coin)
        h,hmeta=process_hl(coin)
        all_rates.extend(b+h)
        manifesto["providers"][coin]={"binance":bmeta,"hyperliquid":hmeta}
        print("COIN_COMPLETE",coin,json.dumps({"binance_rows":len(b),
            "hyperliquid_rows":len(h),"missing_binance_months":bmeta["missing_months"]})[:2300],flush=True)
    path=OUT/"funding_events.csv"
    with path.open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["venue","coin","timestamp_ms","rate","interval_hours"])
        w.writeheader();w.writerows(sorted(all_rates,key=lambda z:(z["coin"],z["timestamp_ms"],z["venue"])))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    manifesto["csv_sha256"]=digest
    (OUT/"source_manifest.json").write_text(json.dumps(manifesto,indent=2,ensure_ascii=False))
    print("CARRY_SOURCE_COMPLETE",json.dumps({"rates":len(all_rates),"sha256":digest,
      "per_coin":{c:{k:len([r for r in all_rates if r["coin"]==c and r["venue"]==v])
         for k,v in (("binance","Binance"),("hyperliquid","Hyperliquid"))}
         for c in COINS}},ensure_ascii=False),flush=True)
    missing=sum(len(manifesto["providers"][coin]["binance"]["missing_months"]) for coin in COINS)
    if missing:
        raise RuntimeError(f"BLOCKED_SOURCE {missing} missing Binance monthly archives: no economic GO")
if __name__=="__main__":main()

#!/usr/bin/env python3
"""BINANCE006 public 90d official ZIP+CHECKSUM validation then frozen historical proxy.

One non-retrying run. No account, orders, paid data, exchange private endpoints,
new parameter search, or archive substitution. FAIL CLOSED with original receipts.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import urllib.request
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

from flow_study import (SYMBOLS,START,VALID_START,TEST_START,END,T0,T_END,US,
                        FlowStudy,parse_agg_row,summarize,write_events_csv)

HOST="https://data.binance.vision"
MONTHS=("2026-08","2026-09","2026-10")
MAX_TOTAL_COMPRESSED=900_000_000
MAX_ONE_COMPRESSED=250_000_000
MAX_ONE_UNCOMPRESSED=2_000_000_000
MAX_TOTAL_UNCOMPRESSED=12_000_000_000
MAX_ROWS=100_000_000
OUT=Path("binance006-evidence")
HEAD_TIMEOUT=18
GET_TIMEOUT=70

def requests_for():
    out=[]
    for symbol in SYMBOLS:
        for month in MONTHS:
            for kind in ("aggTrades","klines"):
                if kind=="aggTrades":
                    filename=f"{symbol}-aggTrades-{month}.zip"
                    path=f"/data/spot/monthly/aggTrades/{symbol}/{filename}"
                else:
                    filename=f"{symbol}-1m-{month}.zip"
                    path=f"/data/spot/monthly/klines/{symbol}/1m/{filename}"
                out.append({"symbol":symbol,"month":month,"kind":kind,
                            "filename":filename,"url":HOST+path})
    return out

def checked_url(url):
    if not url.startswith(HOST+"/data/spot/monthly/"):
        raise ValueError("NOT_WHITELISTED_SPOT_ARCHIVE")
    return url

def anonymous(url,method="GET",headers=None):
    checked_url(url)
    request=urllib.request.Request(url,method=method,headers={
        "User-Agent":"Crypto-Lab-Binance006-HistoricalReadOnly/1.0",
        "Accept":"application/octet-stream",
        **(headers or {})
    })
    return urllib.request.urlopen(request,timeout=HEAD_TIMEOUT if method=="HEAD" else GET_TIMEOUT)

def remote_check(entry):
    with anonymous(entry["url"],"HEAD") as response:
        if response.status!=200:raise ValueError("ZIP_HEAD_HTTP_"+str(response.status))
        length=response.headers.get("Content-Length")
        if not length or not length.isdigit():raise ValueError("MISSING_ARCHIVE_SIZE")
        size=int(length)
    if size<=0 or size>MAX_ONE_COMPRESSED:raise ValueError("ZIP_SIZE_CAP_"+entry["filename"]+"_"+str(size))
    with anonymous(entry["url"]+".CHECKSUM") as response:
        if response.status!=200:raise ValueError("CHECKSUM_HTTP_"+str(response.status))
        raw=response.read(1025)
    if len(raw)>1024:raise ValueError("CHECKSUM_TOO_LARGE")
    text=raw.decode("ascii","strict").strip()
    matches=re.findall(r"(?<![a-f0-9])([a-fA-F0-9]{64})\s+\*?([^\s]+)",text)
    if len(matches)!=1 or matches[0][1]!=entry["filename"]:
        raise ValueError("CHECKSUM_UNEXPECTED_FORMAT_OR_FILENAME_"+entry["filename"])
    entry["expected_sha256"]=matches[0][0].lower()
    entry["head_zip_bytes"]=size
    entry["official_checksum_text"]=text
    return entry

def download_checked(entry,folder):
    dest=Path(folder)/entry["filename"]
    sha=hashlib.sha256()
    n=0
    with anonymous(entry["url"]) as response, dest.open("wb") as f:
        if response.status!=200:raise ValueError("ARCHIVE_HTTP_"+str(response.status))
        while True:
            block=response.read(1024*1024)
            if not block:break
            n+=len(block)
            if n>entry["head_zip_bytes"] or n>MAX_ONE_COMPRESSED:
                raise ValueError("ZIP_RECEIPT_TOO_BIG_OR_HEAD_DISAGREES")
            sha.update(block)
            f.write(block)
    if n!=entry["head_zip_bytes"]:
        raise ValueError("TRUNCATED_ZIP_"+entry["filename"])
    digest=sha.hexdigest()
    if digest!=entry["expected_sha256"]:
        raise ValueError("OFFICIAL_SHA256_MISMATCH_"+entry["filename"])
    entry["observed_zip_bytes"]=n
    entry["observed_zip_sha256"]=digest
    return dest

def zip_records(path):
    with zipfile.ZipFile(path) as z:
        files=[f for f in z.infolist() if not f.is_dir()]
        if len(files)!=1 or files[0].filename!=path.stem+".csv":
            raise ValueError("BAD_CSV_MEMBER_"+path.name)
        if files[0].file_size>MAX_ONE_UNCOMPRESSED:
            raise ValueError("ZIP_UNCOMPRESSED_SIZE_CAP")
        with z.open(files[0],"r") as body:
            with io.TextIOWrapper(body,encoding="utf-8",newline="") as txt:
                for row in csv.reader(txt):
                    yield row,files[0].file_size

def read_agg(path,entry,model,ledger):
    count=0
    first=None
    last=None
    previous_id=model.previous_id
    previous_ts=model.previous_ts
    uncompressed=None
    for row,size in zip_records(path):
        uncompressed=size
        if count==0 and row and row[0].lower() in ("agg_trade_id","aggregate tradeid","aggtradeid"):
            continue
        t=parse_agg_row(row,previous_id,previous_ts)
        previous_id=t.agg_id;previous_ts=t.ts_us
        # Reject extraneous data outside claimed month; October 30/31 is
        # allowed but discarded because outside 90-day preregistered scope.
        month_utc=dt.datetime.fromtimestamp(t.ts_us/US,dt.timezone.utc).strftime("%Y-%m")
        if month_utc!=entry["month"]:raise ValueError("MONTH_FILE_CONTAINS_WRONG_UTC_MONTH")
        if t.ts_us>=T_END:break
        if t.ts_us<T0:raise ValueError("PRE_EXPERIMENT_TIMESTAMP")
        model.ingest(t)
        count+=1
        if first is None:first=t.ts_us
        last=t.ts_us
        if sum(ledger.values())+count>MAX_ROWS:
            raise ValueError("OVERALL_AGGTRADE_ROW_CAP")
    if count==0:raise ValueError("EMPTY_AGG_ARCHIVE")
    ledger[entry["symbol"]]+=count
    entry.update({"observed_rows_in_90d":count,"first_trade_us":first,
                  "last_trade_us":last,"uncompressed_csv_bytes":uncompressed})
    return count

def read_klines(path,entry,minute_count,last_seen):
    n=0
    first=None
    last=None
    uncompressed=None
    for row,size in zip_records(path):
        uncompressed=size
        if row and row[0].lower() in ("open time","open_time","opentime"):continue
        if len(row)!=12:raise ValueError("WRONG_KLINE_CSV_COLUMNS")
        ts=int(row[0])
        if not 1_700_000_000_000_000<=ts<1_900_000_000_000_000:
            raise ValueError("2026_KLINE_EXPECTS_MICROSECONDS")
        if ts%(60*US)!=0:raise ValueError("KLINE_UNALIGNED_UTC_MINUTE")
        if dt.datetime.fromtimestamp(ts/US,dt.timezone.utc).strftime("%Y-%m")!=entry["month"]:
            raise ValueError("KLINE_WRONG_UTC_MONTH")
        if ts>=T_END:break
        prev=last_seen.get(entry["symbol"])
        if prev is not None and ts!=prev+60*US:
            raise ValueError("MISSING_OR_DUPLICATE_1MIN_KLINE")
        last_seen[entry["symbol"]]=ts
        day=dt.datetime.fromtimestamp(ts/US,dt.timezone.utc).strftime("%Y-%m-%d")
        minute_count[(entry["symbol"],day)]+=1
        n+=1
        if first is None:first=ts
        last=ts
    if not n:raise ValueError("EMPTY_KLINE_ARCHIVE")
    entry.update({"observed_rows_in_90d":n,"first_kline_us":first,
                  "last_kline_us":last,"uncompressed_csv_bytes":uncompressed})

def date_list():
    return [(START+dt.timedelta(days=k)).strftime("%Y-%m-%d") for k in range(90)]

def verify_coverage(models,minute_count):
    for s,m in models.items():
        for day in date_list():
            if minute_count[(s,day)]!=1440:
                raise ValueError("KLINE_MINUTE_COVERAGE_"+s+"_"+day+"_"+str(minute_count[(s,day)]))
            count=m.trade_count_by_day[day]
            if count<1:raise ValueError("NO_AGGTRADES_IN_UTC_DAY_"+s+"_"+day)
            midnight=int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp()*US)
            # Binance active BTC/ETH/SOL markets should trade near day edges.
            if m.source_first_by_day[day]>midnight+60*US or m.source_last_by_day[day]<(midnight+86400*US-60*US):
                raise ValueError("AGGTRADES_UNVERIFIED_DAY_EDGE_"+s+"_"+day)
    return {"assets":list(SYMBOLS),"complete_utc_days_each":90,
            "expected_1m_bars_per_symbol":129600,
            "strict_daily_trade_edge_max_gap_seconds":60}

def sha_file(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""):h.update(block)
    return h.hexdigest()

def persist(manifest):
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/"source_manifest.json"
    p.write_text(json.dumps(manifest,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")
    (OUT/"source_manifest.sha256").write_text(sha_file(p)+"  source_manifest.json\n")
    return p

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={"study":"BINANCE006_SPOT_AGGTRADE_FLOWONLY_90D_V01",
              "created_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
              "status":"SOURCE_BLOCKED",
              "source":"official Binance data.binance.vision monthly spot",
              "scope":"BTCUSDT ETHUSDT SOLUSDT, 2026-08-01 through 2026-10-29 UTC",
              "source_price_kind":"historical aggregate trade PRINT, NOT order book bid/ask",
              "data_free_and_public":True,
              "source_zip_bytes_cap":MAX_TOTAL_COMPRESSED,
              "per_zip_bytes_cap":MAX_ONE_COMPRESSED,
              "checksums_official_required":True,
              "archive_files":[],"real_orders":0,"actual_executable_fills":0,
              "no_keys":True,"no_paid_api":True,"no_trades":True}
    files=requests_for()
    try:
        total=0
        for entry in files:
            remote_check(entry)
            total+=entry["head_zip_bytes"]
            manifest["archive_files"].append(entry)
            persist(manifest)
        manifest["preflight_total_compressed_bytes"]=total
        if total>MAX_TOTAL_COMPRESSED:
            raise ValueError("PRE_DATA_DOWNLOAD_ARCHIVE_SIZE_CAP_"+str(total))
        manifest["status"]="SOURCE_HEAD_AND_OFFICIAL_CHECKSUM_PREFLIGHT_PASS"
        persist(manifest)
        models={s:FlowStudy(s) for s in SYMBOLS}
        minute_count=Counter()
        last_kline={}
        rows_by_symbol=defaultdict(int)
        with tempfile.TemporaryDirectory(prefix="binance006-official-archives-") as tmp:
            for entry in files:
                p=download_checked(entry,tmp)
                try:
                    if entry["kind"]=="aggTrades":
                        read_agg(p,entry,models,rows_by_symbol)
                    else:
                        read_klines(p,entry,minute_count,last_kline)
                finally:
                    p.unlink(missing_ok=True)
                entry["validated"]=True
                persist(manifest)
        coverage=verify_coverage(models,minute_count)
        all_events=[]
        for s in SYMBOLS:
            all_events.extend(models[s].finish())
        result=summarize(all_events)
        # The original-source stage is separate from the scientific inference.
        result["source_verified_externally"]=True
        result["source_days_utc_per_symbol"]=90
        result["source_total_aggr_trades_per_symbol"]=dict(rows_by_symbol)
        result["source_coverage"]=coverage
        ledger=OUT/"event_ledger.csv"
        write_events_csv(all_events,ledger)
        result["event_ledger_sha256"]=sha_file(ledger)
        result["event_ledger_rows"]=len(all_events)
        result["archive_receipts_sha256"]={
            f["filename"]:f["observed_zip_sha256"] for f in manifest["archive_files"]
        }
        result["L2_absorption_reconstructed"]=False
        result["live_trading_go"]=False
        verdict=OUT/"economic_verdict.json"
        verdict.write_text(json.dumps(result,indent=2,sort_keys=True,ensure_ascii=False)+"\n")
        (OUT/"economic_verdict.sha256").write_text(sha_file(verdict)+"  economic_verdict.json\n")
        manifest["status"]="OFFICIAL_90D_DATA_VERIFIED_AND_FLOW_ONLY_RESEARCH_COMPLETE"
        manifest["source_coverage"]=coverage
        manifest["total_agg_rows_by_symbol"]=dict(rows_by_symbol)
        manifest["event_ledger_sha256"]=result["event_ledger_sha256"]
        manifest["economic_verdict_sha256"]=sha_file(verdict)
        persist(manifest)
        # Report only fully verified conclusions. A technical PASS cannot
        # promote positive print-level outcomes to executable profits.
        print(json.dumps({"source_status":manifest["status"],
              "source_total_bytes":total,"source_agg_rows_by_symbol":dict(rows_by_symbol),
              "event_ledger_sha256":result["event_ledger_sha256"],
              "economic_summary":result},indent=2,sort_keys=True))
        return 0
    except Exception as exc:
        manifest["status"]="SOURCE_BLOCKED"
        manifest["blocker_type"]=type(exc).__name__
        manifest["blocker"]=str(exc)[:280]
        persist(manifest)
        print(json.dumps({"study":manifest["study"],
                          "status":"SOURCE_BLOCKED",
                          "blocker":manifest["blocker"],
                          "collected_receipt_count":len(manifest["archive_files"]),
                          "no_trades":True},indent=2))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

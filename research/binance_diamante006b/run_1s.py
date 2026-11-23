#!/usr/bin/env python3
"""BINANCE006B -- anonymous official Spot 1s archive source gate + 90d OOS shadow.
One run; no exchange login/API/trades/subscriptions/keys or source retries.
"""
from __future__ import annotations
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import re
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from engine import S,US,T0,TE,DAY,KlineFlow,parse_1s,summarize,day_of

HOST="https://data.binance.vision"
MONTHS=("2026-08","2026-09","2026-10")
MAX_TOTAL_ZIP=900_000_000
MAX_ONE_ZIP=250_000_000
MAX_ONE_UNZIPPED=2_000_000_000
OUT=Path("binance006b-evidence")

def entries():
    result=[]
    for sym in S:
        for month in MONTHS:
            filename=f"{sym}-1s-{month}.zip"
            url=f"{HOST}/data/spot/monthly/klines/{sym}/1s/{filename}"
            result.append({"symbol":sym,"month":month,"filename":filename,"url":url})
    return result

def fetch(url,method="GET"):
    if not url.startswith(HOST+"/data/spot/monthly/klines/"):
        raise ValueError("OUTSIDE_PINNED_PUBLIC_SOURCE_HOST")
    return urllib.request.urlopen(urllib.request.Request(
        url,method=method,headers={"User-Agent":"CryptoLab-006B-Official-Archive-NO-TRADING/1.0"}),
        timeout=18 if method=="HEAD" else 90)

def preflight(e):
    with fetch(e["url"],"HEAD") as res:
        if res.status!=200:raise ValueError("ZIP_NOT_AVAILABLE_HTTP_"+str(res.status))
        amount=res.headers.get("Content-Length")
        if not amount or not amount.isdigit():raise ValueError("SOURCE_UNKNOWN_CONTENT_LENGTH")
        size=int(amount)
    e["reported_zip_bytes"]=size
    with fetch(e["url"]+".CHECKSUM") as res:
        raw=res.read(2049)
    if len(raw)>2048:raise ValueError("CHECKSUM_FILE_NOT_SMALL")
    txt=raw.decode("ascii","strict").strip()
    pieces=re.findall(r"([a-fA-F0-9]{64})\s+\*?([^\s]+)",txt)
    if len(pieces)!=1 or pieces[0][1]!=e["filename"]:
        raise ValueError("UNEXPECTED_OFFICIAL_SHA256_FORMAT")
    e["official_sha256"]=pieces[0][0].lower()
    e["official_checksum_text"]=txt
    return size

def transfer(e,folder):
    n=0;h=hashlib.sha256()
    file=Path(folder)/e["filename"]
    with fetch(e["url"]) as resp,file.open("wb") as f:
        if resp.status!=200:raise ValueError("ZIP_DOWNLOAD_BAD_HTTP_STATUS")
        while True:
            chunk=resp.read(1024*1024)
            if not chunk:break
            n+=len(chunk)
            if n>e["reported_zip_bytes"] or n>MAX_ONE_ZIP:
                raise ValueError("ZIP_DOWNLOAD_SIZE_EXCEEDS_PREFLIGHT")
            f.write(chunk);h.update(chunk)
    if n!=e["reported_zip_bytes"] or h.hexdigest()!=e["official_sha256"]:
        raise ValueError("OFFICIAL_ZIP_SHA_OR_SIZE_MISMATCH")
    e["validated_sha256"]=h.hexdigest()
    e["validated_zip_bytes"]=n
    return file

def digest(path):
    sha=hashlib.sha256()
    with Path(path).open("rb") as f:
        for part in iter(lambda:f.read(1024*1024),b""):sha.update(part)
    return sha.hexdigest()

def persist_report(report,path):
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/path
    p.write_text(json.dumps(report,sort_keys=True,indent=2,ensure_ascii=False)+"\n")
    (OUT/(path+".sha256")).write_text(digest(p)+"  "+path+"\n")
    return p

def consume_zip(e,path,model):
    rows=0
    first=None
    last=None
    with zipfile.ZipFile(path) as z:
        names=[v for v in z.infolist() if not v.is_dir()]
        if len(names)!=1 or names[0].filename!=path.stem+".csv":
            raise ValueError("ZIP_MEMBER_INCORRECT")
        if names[0].file_size>MAX_ONE_UNZIPPED:
            raise ValueError("UNCOMPRESSED_ZIP_BUDGET")
        e["uncompressed_bytes"]=names[0].file_size
        with z.open(names[0]) as body,io.TextIOWrapper(body,encoding="utf-8",newline="") as txt:
            for raw in csv.reader(txt):
                if raw and raw[0].lower() in ("open time","open_time","opentime"):continue
                bar=parse_1s(raw)
                current=bar[0]
                if dt.datetime.fromtimestamp(current/US,dt.timezone.utc).strftime("%Y-%m")!=e["month"]:
                    raise ValueError("ARCHIVE_HAS_WRONG_UTC_MONTH")
                if current>=TE:break
                if current<T0:raise ValueError("ARCHIVE_BEFORE_FROZEN_PERIOD")
                model.ingest(bar)
                if first is None:first=current
                last=current;rows+=1
    if not rows:raise ValueError("EMPTY_SOURCE_ZIP")
    e["processed_1s_bars"]=rows
    e["first_open_us"]=first
    e["last_open_us"]=last

def validate_coverage(models):
    for symbol,m in models.items():
        if m.source_1s_rows!=90*86400:raise ValueError("WRONG_TOTAL_SECOND_BARS_"+symbol+"_"+str(m.source_1s_rows))
        for n in range(90):
            day=day_of(T0+n*DAY)
            if m.days[day]!=86400:
                raise ValueError("MISSING_OR_DUPLICATE_UTC_SECONDS_"+symbol+"_"+day)
    return {"source_assets":list(S),"utc_days_per_symbol":90,
            "validated_seconds_per_symbol":7776000,
            "total_seconds_over_all_assets":23328000}

def write_ledger(events):
    path=OUT/"shadow_events.csv.gz"
    fields=("symbol","kind","cohort","decision_us","date","status","entry_us",
            "entry_close","exit_us","exit_close","gross_bps","base_net_bps","stress_net_bps")
    with gzip.open(path,"wt",encoding="utf-8",newline="",compresslevel=6) as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for e in events:writer.writerow({k:e.get(k) for k in fields})
    return path

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest={"study":"BINANCE006B_SPOT_1S_SELLFLOW_60S_OOS_V01",
              "status":"SOURCE_BLOCKED",
              "original_scientific_freeze_commit":"7cef5245d77148097ab445a62db3c65c26c23f99",
              "official_source_host":HOST,"archive_files":[],
              "source_sample":"2026-08-01 through 2026-10-29, BTCUSDT ETHUSDT SOLUSDT 1-second klines",
              "source_kind":"completed 1-second OHLCV plus taker buy quote asset volume, NOT aggTrades and NOT L2",
              "source_zip_total_cap":MAX_TOTAL_ZIP,"one_zip_cap":MAX_ONE_ZIP,
              "private_api":False,"paid_api":False,"payments":False,"trading":False,
              "actual_fills":0}
    try:
        total=0
        for e in entries():
            total+=preflight(e)
            manifest["archive_files"].append(e)
            persist_report(manifest,"source_manifest.json")
        manifest["expected_compressed_bytes"]=total
        if any(x["reported_zip_bytes"]<=0 or x["reported_zip_bytes"]>MAX_ONE_ZIP
               for x in manifest["archive_files"]):
            raise ValueError("ONE_SECOND_MONTHLY_ZIP_OVER_SINGLE_FILE_CAP")
        if total>MAX_TOTAL_ZIP:
            raise ValueError("ONE_SECOND_MONTHLY_ZIPS_OVER_TOTAL_TRANSFER_CAP_"+str(total))
        manifest["status"]="OFFICIAL_NINE_CHECKSUM_PREFLIGHT_PASS"
        persist_report(manifest,"source_manifest.json")
        models={s:KlineFlow(s) for s in S}
        with tempfile.TemporaryDirectory(prefix="binance006b-official-source-") as folder:
            for e in manifest["archive_files"]:
                path=transfer(e,folder)
                try:consume_zip(e,path,models[e["symbol"]])
                finally:path.unlink(missing_ok=True)
                e["status"]="ZIP_SHA_AND_1S_CHRONOLOGY_PASS"
                persist_report(manifest,"source_manifest.json")
        coverage=validate_coverage(models)
        events=[]
        for s in S:events.extend(models[s].finish())
        economic=summarize(events)
        economic["source_coverage"]=coverage
        economic["original_binance_official_sha256"]={x["filename"]:x["validated_sha256"]
             for x in manifest["archive_files"]}
        economic["baseline_overlap_not_independent"]=True
        ledger=write_ledger(events)
        economic["event_ledger_archive_sha256"]=digest(ledger)
        economic["event_count_including_censored"]=len(events)
        economic["1s_close_is_hypothetical_not_filled"]=True
        economic["real_pnl"]=None
        verdict=persist_report(economic,"economic_verdict.json")
        manifest["status"]="OFFICIAL_90D_1S_KLINES_VERIFIED_AND_FLOW_PROXY_STUDY_COMPLETE"
        manifest["coverage"]=coverage
        manifest["ledger_archive_sha256"]=digest(ledger)
        manifest["economic_verdict_sha256"]=digest(verdict)
        persist_report(manifest,"source_manifest.json")
        print(json.dumps({"source_status":manifest["status"],
            "total_official_compressed_bytes":total,
            "original_1s_bars":coverage["total_seconds_over_all_assets"],
            "ledger_sha256":economic["event_ledger_archive_sha256"],
            "scientific_economic_shadow":economic},sort_keys=True,indent=2))
        return 0
    except Exception as exc:
        manifest["status"]="SOURCE_BLOCKED"
        manifest["blocked_reason"]=str(exc)[:280]
        manifest["blocked_type"]=type(exc).__name__
        persist_report(manifest,"source_manifest.json")
        print(json.dumps({"study":manifest["study"],"status":"SOURCE_BLOCKED",
            "reason":manifest["blocked_reason"],"checked_files":len(manifest["archive_files"]),
            "no_economic_inference":True,"no_trades":True},indent=2))
        return 2
if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
# FIRST-SECONDS CASCADE V0.1 — canonical Gate SPOT deals source-window census.
# SOURCE ONLY: reads timestamps only. It does NOT parse, emit, store, or inspect prices/returns.

import csv
import gzip
import io
import json
import urllib.request
import urllib.error
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone

EVENTS=[
  ("AIXBT","AIXBT_USDT",1736499327639),
  ("CGPT","CGPT_USDT",1736499327639),
  ("COOKIE","COOKIE_USDT",1736499327639),
  ("1000CHEEMS","CHEEMS_USDT",1739085031264),
  ("SYRUP","SYRUP_USDT",1746530720814),
  ("KMNO","KMNO_USDT",1746530720814),
  ("PUMP","PUMP_USDT",1757590673797),
  ("AVNT","AVNT_USDT",1757908021934),
  ("GIGGLE","GIGGLE_USDT",1761361338417),
  ("F","F_USDT",1761361338417),
  ("BANK","BANK_USDT",1763028026501),
  ("MET","MET_USDT",1763028026501),
]

def month(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).strftime("%Y%m")

def ts_us(raw):
    try:
        d=Decimal(raw.strip())
        return int(d*Decimal(1_000_000))
    except (InvalidOperation, ValueError):
        return None

def scan(asset,market,t0_ms):
    ym=month(t0_ms)
    url=f"https://download.gatedata.org/spot/deals/{ym}/{market}-{ym}.csv.gz"
    t0=t0_ms*1000
    pre24_lo=t0-24*3600*1_000_000
    pre1h_hi=t0-3600*1_000_000
    near_lo=t0-10*1_000_000
    post_hi=t0+60*1_000_000

    counts={"baseline_24h_to_1h":0,"near_pre_10s":0,"post_60s":0}
    fractional_ts_seen=False
    rows_scanned=0
    min_ts=None
    max_ts=None
    http=None
    err=None

    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabFirstSecondsV01/1.0","Accept":"application/gzip,*/*"})
    try:
        with urllib.request.urlopen(req,timeout=60) as resp:
            http=resp.status
            with gzip.GzipFile(fileobj=resp) as gz:
                txt=io.TextIOWrapper(gz,encoding="utf-8",errors="replace",newline="")
                for row in csv.reader(txt):
                    if not row:
                        continue
                    raw=row[0].strip()
                    u=ts_us(raw)
                    if u is None:
                        continue
                    rows_scanned+=1
                    if "." in raw and raw.split(".",1)[1].rstrip("0"):
                        fractional_ts_seen=True
                    min_ts=u if min_ts is None else min(min_ts,u)
                    max_ts=u if max_ts is None else max(max_ts,u)
                    if pre24_lo <= u < pre1h_hi:
                        counts["baseline_24h_to_1h"]+=1
                    if near_lo <= u < t0:
                        counts["near_pre_10s"]+=1
                    if t0 <= u <= post_hi:
                        counts["post_60s"]+=1
    except urllib.error.HTTPError as e:
        http=e.code
        err="HTTPError"
    except Exception as e:
        err=type(e).__name__

    source_ok=bool(
        http==200
        and counts["baseline_24h_to_1h"]>0
        and counts["near_pre_10s"]>0
        and counts["post_60s"]>0
        and fractional_ts_seen
    )
    return {
        "asset":asset,
        "market":market,
        "ym":ym,
        "http":http,
        "error_type":err,
        "rows_scanned":rows_scanned,
        "baseline_present":counts["baseline_24h_to_1h"]>0,
        "near_pre_10s_count":counts["near_pre_10s"],
        "post_60s_count":counts["post_60s"],
        "subsecond_timestamp_seen":fractional_ts_seen,
        "source_ok":source_ok,
    }

rows=[]
for e in EVENTS:
    rows.append(scan(*e))

n=sum(1 for r in rows if r["source_ok"])
res={
    "parent_freeze":"5110f7ebda90809de56155b4605b9621bd8fb781",
    "identity_resolution":"9744ce8e12b99e644a0f9bee55b1d89689a9b0dd",
    "n_resolved_candidates":len(rows),
    "n_source_valid":n,
    "source_gate_minimum":8,
    "source_gate_pass":n>=8,
    "rows":rows,
}
print("FIRST_SECONDS_V01_CANONICAL_SOURCE_CENSUS_BEGIN")
print(json.dumps(res,indent=2,sort_keys=True))
print("FIRST_SECONDS_V01_CANONICAL_SOURCE_CENSUS_END")
if n<8:
    raise SystemExit(2)

#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, re, sys, zipfile
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
import requests

LAB_ID="LL-0017-POSITIONING-RATIO-001"
MVE_ID="LL17-BTCUSDT-METRICS-SCHEMA-001A"
BASE="https://data.binance.vision/data/futures/um/daily/metrics/BTCUSDT"
DATES=["2021-01-15","2022-06-15","2023-06-15","2024-12-15"]
SYMBOL="BTCUSDT"
EXPECTED_FIELDS={
 "top_trader_account_ratio":"count_toptrader_long_short_ratio",
 "top_trader_position_ratio":"sum_toptrader_long_short_ratio",
 "global_account_ratio":"count_long_short_ratio",
}
def shab(b): return hashlib.sha256(b).hexdigest()
def csum(t):
 m=re.search(r"\b([0-9a-fA-F]{64})\b",t)
 if not m: raise ValueError("checksum SHA256 not found")
 return m.group(1).lower()
def get(url):
 if "2025" in url or "2026" in url: raise RuntimeError("protected period URL")
 return requests.get(url,timeout=(15,120),headers={"User-Agent":f"{LAB_ID}/schema-v0.1A"})
def pts(s):
 s=s.strip()
 if re.fullmatch(r"\d+",s):
  n=int(s)
  if n>10**17:return n//10**9
  if n>10**14:return n//10**6
  if n>10**11:return n//1000
  return n
 dt=datetime.fromisoformat(s.replace("Z","+00:00"))
 if dt.tzinfo is None: dt=dt.replace(tzinfo=timezone.utc)
 return int(dt.timestamp())
def dayof(ts): return datetime.fromtimestamp(ts,tz=timezone.utc).strftime("%Y-%m-%d")

def main():
 out=Path("ll0017_source_v01a_output"); out.mkdir(parents=True,exist_ok=True)
 dst=out/"LL0017_POSITIONING_RATIO_SOURCE_SCHEMA_RECEIPT_V0_1A.json"
 rows_out=[]; common=None; failure=None; failure_class=None
 try:
  for day in DATES:
   zn=f"{SYMBOL}-metrics-{day}.zip"; zu=f"{BASE}/{zn}"; cu=zu+".CHECKSUM"
   zr,cr=get(zu),get(cu)
   if zr.status_code!=200 or cr.status_code!=200:
    failure_class="SOURCE_ACCESS_BLOCKED"; raise RuntimeError(f"{day}: zip={zr.status_code} checksum={cr.status_code}")
   actual=shab(zr.content); expected=csum(cr.text)
   if actual!=expected:
    failure_class="SOURCE_CHECKSUM_FAILURE"; raise RuntimeError(f"{day}: checksum mismatch")
   with zipfile.ZipFile(io.BytesIO(zr.content)) as zf:
    ms=[x for x in zf.namelist() if not x.endswith("/")]
    if len(ms)!=1 or not ms[0].lower().endswith(".csv"):
     failure_class="SOURCE_SCHEMA_INADEQUATE"; raise RuntimeError(f"{day}: members={ms}")
    text=zf.read(ms[0]).decode("utf-8-sig")
   lines=text.splitlines()
   if not lines:
    failure_class="SOURCE_SCHEMA_INADEQUATE"; raise RuntimeError(f"{day}: empty csv")
   header=[x.strip() for x in next(csv.reader([lines[0]]))]
   lower=[x.lower() for x in header]
   if common is None: common=header
   elif header!=common:
    failure_class="PROVENANCE_FAILURE"; raise RuntimeError(f"{day}: header mismatch")
   sem={k:(v in lower) for k,v in EXPECTED_FIELDS.items()}
   if not all(sem.values()):
    failure_class="SOURCE_SCHEMA_INADEQUATE"; raise RuntimeError(f"{day}: required ratio fields missing")
   tc=[x for x in ("create_time","timestamp","time") if x in lower]
   if len(tc)!=1:
    failure_class="SOURCE_SCHEMA_INADEQUATE"; raise RuntimeError(f"{day}: timestamp field ambiguity")
   ti=lower.index(tc[0])
   groups={}
   raw_rows=0
   for line in lines[1:]:
    if not line.strip(): continue
    row=next(csv.reader([line]))
    if len(row)!=len(header):
     failure_class="PROVENANCE_FAILURE"; raise RuntimeError(f"{day}: row width mismatch")
    ts=pts(row[ti]); h=shab(line.encode("utf-8")); raw_rows+=1
    groups.setdefault(ts,set()).add(h)
   divergent={ts:hs for ts,hs in groups.items() if len(hs)>1}
   if divergent:
    failure_class="PROVENANCE_FAILURE"; raise RuntimeError(f"{day}: non-identical duplicate timestamp groups={len(divergent)}")
   unique=sorted(groups)
   duplicate_rows=raw_rows-len(unique)
   if len(unique)<200:
    failure_class="SOURCE_TEMPORAL_COVERAGE_INADEQUATE"; raise RuntimeError(f"{day}: unique timestamps={len(unique)}")
   if any(dayof(x)!=day for x in unique):
    failure_class="PROVENANCE_FAILURE"; raise RuntimeError(f"{day}: timestamp outside requested UTC day")
   diffs=[b-a for a,b in zip(unique,unique[1:])]
   med=median(diffs) if diffs else None
   p95=sorted(diffs)[max(0,min(len(diffs)-1,int(.95*(len(diffs)-1))))] if diffs else None
   if med is None or med>600:
    failure_class="SOURCE_TEMPORAL_COVERAGE_INADEQUATE"; raise RuntimeError(f"{day}: median interval={med}")
   rows_out.append({
    "date":day,"provider_sha256":expected,"archive_sha256":actual,"archive_bytes":len(zr.content),
    "csv_member":ms[0],"csv_header":header,"positioning_field_presence":sem,
    "timestamp_field":tc[0],"raw_row_count":raw_rows,"normalized_unique_timestamp_count":len(unique),
    "exact_duplicate_rows_removed":duplicate_rows,"nonidentical_duplicate_groups":0,
    "median_interval_seconds":med,"p95_interval_seconds":p95,
    "first_timestamp_utc":datetime.fromtimestamp(unique[0],tz=timezone.utc).isoformat(),
    "last_timestamp_utc":datetime.fromtimestamp(unique[-1],tz=timezone.utc).isoformat()
   })
  classification="SOURCE_SCHEMA_PASS"
 except requests.RequestException as exc:
  classification=failure_class or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"; failure=f"{type(exc).__name__}: {str(exc)[:1000]}"
 except Exception as exc:
  classification=failure_class or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"; failure=f"{type(exc).__name__}: {str(exc)[:1500]}"
 receipt={
  "lab_id":LAB_ID,"mve_id":MVE_ID,"phase":"SOURCE_SCHEMA_V0_1A_EXACT_DUP_NORMALIZATION_OUTCOME_BLIND",
  "classification":classification,"failure":failure,"frozen_probe_dates":DATES,"source":BASE,
  "normalization_rule":"collapse only timestamp duplicates whose complete raw CSV line SHA256 is identical",
  "probe_results":rows_out,"common_header":common,
  "safety":{"ratio_numeric_values_parsed":False,"metric_values_exposed":False,"prices_opened":False,"returns_opened":False,"pnl_opened":False,"2025_accessed":False,"2026_accessed":False,"live_trading":False,"exchange_mutation":False}
 }
 dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"classification":classification,"failure":failure,"probe_count":len(rows_out),"results":rows_out,"ratio_values_parsed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
 return 0 if classification=="SOURCE_SCHEMA_PASS" else 2
if __name__=="__main__": sys.exit(main())

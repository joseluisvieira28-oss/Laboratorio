#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, io, json, re, sys, zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://data.binance.vision/data/futures/um/monthly/metrics/BTCUSDT"
EXPECTED_HEADER=[
 "create_time","symbol","sum_open_interest","sum_open_interest_value",
 "count_toptrader_long_short_ratio","sum_toptrader_long_short_ratio",
 "count_long_short_ratio","sum_taker_long_short_vol_ratio"
]
TARGETS={
 "2021-01-20":271,
 "2021-02-05":279,
 "2021-02-11":276,
 "2021-02-19":218,
 "2021-02-20":272,
 "2021-04-27":258,
 "2021-06-22":126,
 "2021-06-23":275,
 "2021-06-24":279,
 "2021-11-26":276,
 "2024-02-16":163,
}
MONTHS=["2021-01","2021-02","2021-04","2021-06","2021-11","2024-02"]

def sha(b): return hashlib.sha256(b).hexdigest()
def csum(t):
 m=re.search(r"\b([0-9a-fA-F]{64})\b",t)
 if not m: raise ValueError("provider checksum not found")
 return m.group(1).lower()
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
 out=Path("ll0017_monthly_probe_output"); out.mkdir(parents=True,exist_ok=True)
 dst=out/"LL0017_MONTHLY_ARCHIVE_SOURCE_FEASIBILITY_RECEIPT_V0_3.json"
 results={}
 monthly_meta=[]
 classification=None; failure=None
 try:
  for month in MONTHS:
   if month.startswith(("2025","2026")): raise RuntimeError("protected period")
   zn=f"BTCUSDT-metrics-{month}.zip"; zu=f"{BASE}/{zn}"; cu=zu+".CHECKSUM"
   zr=requests.get(zu,timeout=(15,120),headers={"User-Agent":"LL0017/monthly-source-v0.3"})
   cr=requests.get(cu,timeout=(15,120),headers={"User-Agent":"LL0017/monthly-source-v0.3"})
   if zr.status_code!=200 or cr.status_code!=200:
    classification="SOURCE_ACCESS_BLOCKED"; raise RuntimeError(f"{month}: zip={zr.status_code} checksum={cr.status_code}")
   expected=csum(cr.text); actual=sha(zr.content)
   if expected!=actual:
    classification="SOURCE_CHECKSUM_FAILURE"; raise RuntimeError(f"{month}: checksum mismatch")
   with zipfile.ZipFile(io.BytesIO(zr.content)) as zf:
    members=[x for x in zf.namelist() if not x.endswith("/")]
    if len(members)!=1 or not members[0].lower().endswith(".csv"):
     classification="SOURCE_SCHEMA_INADEQUATE"; raise RuntimeError(f"{month}: members={members}")
    text=zf.read(members[0]).decode("utf-8-sig")
   lines=text.splitlines()
   if not lines:
    classification="SOURCE_SCHEMA_INADEQUATE"; raise RuntimeError(f"{month}: empty csv")
   header=[x.strip() for x in next(csv.reader([lines[0]]))]
   if header!=EXPECTED_HEADER:
    classification="SOURCE_SCHEMA_INADEQUATE"; raise RuntimeError(f"{month}: header mismatch {header}")
   ti=0
   groups=defaultdict(lambda:defaultdict(set))
   raw_counts=defaultdict(int)
   for line in lines[1:]:
    if not line.strip(): continue
    row=next(csv.reader([line]))
    if len(row)!=len(header):
     classification="PROVENANCE_FAILURE"; raise RuntimeError(f"{month}: row width mismatch")
    ts=pts(row[ti]); d=dayof(ts)
    if not d.startswith(month+"-"):
     classification="PROVENANCE_FAILURE"; raise RuntimeError(f"{month}: row timestamp outside month {d}")
    groups[d][ts].add(sha(line.encode("utf-8"))); raw_counts[d]+=1

   target_days=[d for d in TARGETS if d.startswith(month+"-")]
   for d in target_days:
    tgroups=groups.get(d,{})
    divergent=sum(1 for hs in tgroups.values() if len(hs)>1)
    if divergent:
     classification="PROVENANCE_FAILURE"; raise RuntimeError(f"{d}: nonidentical duplicate timestamp groups={divergent}")
    unique=len(tgroups); daily=TARGETS[d]
    results[d]={
      "daily_source_unique_timestamps":daily,
      "monthly_source_unique_timestamps":unique,
      "incremental_timestamps":unique-daily,
      "monthly_raw_rows":raw_counts.get(d,0),
      "exact_duplicate_rows_removed":raw_counts.get(d,0)-unique,
      "reaches_original_280_minimum":unique>=280,
      "is_full_288_day":unique==288,
    }
   monthly_meta.append({
    "month":month,"archive_sha256":actual,"archive_bytes":len(zr.content),
    "csv_member":members[0],"header":header,
    "target_day_count":len(target_days)
   })

  if len(results)!=len(TARGETS):
   classification="PROVENANCE_FAILURE"; raise RuntimeError(f"target result count {len(results)} != {len(TARGETS)}")
  if any(v["incremental_timestamps"]>0 for v in results.values()):
   classification="MONTHLY_SOURCE_ROUTE_RECOVERY_PLAUSIBLE"
  else:
   classification="MONTHLY_SOURCE_ROUTE_NO_INCREMENTAL_COVERAGE"
 except requests.RequestException as exc:
  classification=classification or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
  failure=f"{type(exc).__name__}: {str(exc)[:1000]}"
 except Exception as exc:
  classification=classification or "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
  failure=f"{type(exc).__name__}: {str(exc)[:1500]}"

 receipt={
  "classification":classification,"failure":failure,
  "source":BASE,"months":MONTHS,"target_results":results,"monthly_meta":monthly_meta,
  "summary":{
    "targets":len(results),
    "targets_with_incremental_coverage":sum(1 for v in results.values() if v["incremental_timestamps"]>0),
    "targets_reaching_280":sum(1 for v in results.values() if v["reaches_original_280_minimum"]),
    "targets_full_288":sum(1 for v in results.values() if v["is_full_288_day"]),
  },
  "safety":{"ratio_numeric_values_parsed":False,"metric_values_exposed":False,"prices_opened":False,"returns_opened":False,"pnl_opened":False,"2025_accessed":False,"2026_accessed":False,"live_trading":False,"exchange_mutation":False}
 }
 dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"classification":classification,"failure":failure,"summary":receipt["summary"],"target_results":results,"ratio_values_parsed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
 return 0 if classification in ("MONTHLY_SOURCE_ROUTE_RECOVERY_PLAUSIBLE","MONTHLY_SOURCE_ROUTE_NO_INCREMENTAL_COVERAGE") else 2
if __name__=="__main__": raise SystemExit(main())

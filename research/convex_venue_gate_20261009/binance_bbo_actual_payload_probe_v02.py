#!/usr/bin/env python3
"""V0.2 actual official raw 2023/2024 six-archive SOURCE feasibility.
Uses only previously downloaded V0.1 HEAD metadata; no original outcome access.
"""
import json, hashlib, os, sys, runpy, traceback
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed

HERE=Path(__file__).resolve().parent
ORIG=HERE/"VENUE_SOURCE_GATE_RESULT_2026_10_09.json"
OUT=HERE/"BINANCE_RAW_2023_2024_BBO_SAMPLE_V02_RESULT.json"
SYMS=("ETHUSDT","SOLUSDT","BNBUSDT")
DATES=("2023-05-24","2024-01-15")
MAX_SINGLE=80_000_000;MAX_TOTAL=280_000_000
VALID_STATUSES=("HEAD_OK","RANGE_GET_OK")

def main():
 try:
  orig=json.loads(ORIG.read_text())
  if orig.get("status")!="SOURCE_GATE_EXECUTED__NO_HISTORICAL_MEXC_EXECUTION_APPROVAL":
   raise ValueError("V01_RECEIPT_IDENTITY_WRONG")
  orig_hash=hashlib.sha256(ORIG.read_bytes()).hexdigest()
  archived={(d["symbol"],d["date"]):d for d in orig.get("archive_presence_matrix",[])}
  source=runpy.run_path(str(HERE/"venue_historical_public_source_probe.py"),run_name="as_library_source_probe")
  sample_fn=source["sample_bbo"]
  candidates=[];missing=[];total_proposed=0
  for sym in SYMS:
   for date in DATES:
    m=archived.get((sym,date))
    if not m:
     missing.append({"symbol":sym,"date":date,"status":"NOT_IN_V01_MATRIX"})
     continue
    if m.get("status") not in VALID_STATUSES:
     missing.append({"symbol":sym,"date":date,"status":"SOURCE_NOT_PROVEN","prior":m.get("status")})
     continue
    n=int(m.get("content_length") or "0")
    if n<=0 or n>MAX_SINGLE:
     missing.append({"symbol":sym,"date":date,"status":"ZIP_SIZE_INVALID_OR_TOO_LARGE","bytes":n})
     continue
    if total_proposed+n>MAX_TOTAL:
     missing.append({"symbol":sym,"date":date,"status":"AGGREGATE_FREEZE_BYTE_CAP","bytes":n})
     continue
    candidates.append((sym,date,m))
    total_proposed+=n
  results=[]
  with ThreadPoolExecutor(max_workers=2) as pool:
   futs={pool.submit(sample_fn,sym,date,m):(sym,date) for sym,date,m in candidates}
   for fut in as_completed(futs):
    sym,date=futs[fut]
    try:result=fut.result()
    except Exception as e:result={"status":"EXCEPTION_FAIL_CLOSED","reason":repr(e)}
    result["symbol"]=sym;result["date"]=date
    results.append(result)
    print("RAW_BBO_ARCHIVE",sym,date,
          json.dumps({k:v for k,v in result.items() if k not in ("field_header",)},sort_keys=True),
          flush=True)
  results.sort(key=lambda x:(x["symbol"],x["date"]))
  good=[x for x in results if x["status"]=="SAMPLED_OFFICIAL_BINANCE_BBO_PAYLOAD_PARSE_PASS"]
  status="SAMPLED_BINANCE_BBO_RAW_BYTES_PASS_2023_2024" if len(good)==6 else (
     "PARTIAL_ARCHIVED_BINANCE_BBO_SOURCE_PASS" if good else "BINANCE_BBO_PAYLOAD_SOURCE_BLOCKED")
  artifact={
   "status":status,
   "confirmed_payload_zip_samples":len(good),
   "required_source_matrix_denominator":6,
   "missing_or_too_large":missing,
   "attempted_payload_zip_samples":len(results),
   "sampled_payload_receipts":results,
   "planned_total_download_bytes":total_proposed,
   "v01_source_gate_sha256":orig_hash,
   "mexc_historical_bbo_2021_2025":"SOURCE_NOT_ESTABLISHED",
   "mexc_2021_2025_funding":"SOURCE_TOO_SHORT_EARLIEST_V01_2025_04_17",
   "venue":"BINANCE_FUTURES_USDM_BOOKTICKER_NOT_MEXC",
   "sampled_only_first_1000_rows_per_file":True,
   "exact_trade_fill_proven":False,
   "economic_performance_upgrade":False,
   "independent_OOS":False,
   "live_go":False,
   "notes":["Frozen six archives chosen from previously observed source-availability matrix, no after-the-fact asset substitution.",
       "Sampled spread p05/median/p95 apply only to the first 1000 records in each file, not trade-time spread or full-day distribution.",
       "No bid/ask matched to original 2021-2025 ETH/SOL/BNB individual trade entry/stop timestamps.",
       "Actual stop fill requires exchange-side quote sequence, queue/depth, orders, volume at timestamp, independent fee/funding evidence; nothing traded."]
  }
  OUT.write_text(json.dumps(artifact,sort_keys=True,indent=2)+"\n")
  print("BINANCE_BBO_RAW_SOURCE_GATE_FINAL",json.dumps({
      "status":status,"source_pass":len(good),"required":6,
      "missing":missing,"attempted":len(results)},sort_keys=True),flush=True)
  # partial is a legitimate source gate failure of full coverage, report with exit 0.
 except Exception as e:
  OUT.write_text(json.dumps({"status":"TECHNICAL_FAIL_CLOSED","reason":repr(e),
      "live_go":False,"economic_credit":"ZERO"},sort_keys=True,indent=2)+"\n")
  traceback.print_exc()
  sys.exit(2)

if __name__=="__main__":main()

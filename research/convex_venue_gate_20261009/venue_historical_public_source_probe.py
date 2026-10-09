#!/usr/bin/env python3
"""Crypto Lab historical venue execution SOURCE-ONLY study.
No authentication, trades, private API, protected holdout opening, or market orders.
"""
import csv, hashlib, io, json, math, os, sys, time, traceback, urllib.error, urllib.parse, urllib.request, zipfile
from datetime import datetime,timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed

HERE=Path(__file__).resolve().parent
START=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2025,12,31,23,tzinfo=timezone.utc).timestamp()*1000)
B="https://data.binance.vision/data/futures/um/daily/bookTicker"
M="https://contract.mexc.com/api/v1"
PAIRS=[("ETHUSDT","ETH_USDT"),("SOLUSDT","SOL_USDT"),("BNBUSDT","BNB_USDT")]
DATES=("2021-01-02","2023-05-24","2024-01-15","2025-06-17","2025-12-01")
LIMIT=80_000_000
TIMEOUT=25
HEADERS={"User-Agent":"CryptoLab-Source-Gate-Research-v01/1.0","Accept":"application/json,application/zip,*/*"}

def iso(ms):
 return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def fetch_meta(url):
 # HEAD is a presence probe, never source data for scientific economics.
 req=urllib.request.Request(url,headers=HEADERS,method="HEAD")
 try:
  with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
   d={"status":"HEAD_OK","http_code":r.status,"content_length":r.headers.get("Content-Length"),
       "last_modified":r.headers.get("Last-Modified"),
       "content_type":r.headers.get("Content-Type")}
   return d
 except urllib.error.HTTPError as e:
  if e.code not in (403,405):
   return {"status":"HEAD_HTTP_ERROR","http_code":e.code,"reason":str(e)[:150]}
 except Exception as e:
  return {"status":"HEAD_NETWORK_BLOCKED","reason":repr(e)[:250]}
 # Range GET only to distinguish unavailable HEAD from actual missing archive.
 req=urllib.request.Request(url,headers={**HEADERS,"Range":"bytes=0-255"},method="GET")
 try:
  with urllib.request.urlopen(req,timeout=TIMEOUT) as r:
   r.read(256)
   return {"status":"RANGE_GET_OK","http_code":r.status,"content_length":r.headers.get("Content-Length"),
     "content_range":r.headers.get("Content-Range"),"last_modified":r.headers.get("Last-Modified")}
 except urllib.error.HTTPError as e:
  return {"status":"HEAD_AND_RANGE_HTTP_ERROR","http_code":e.code,"reason":str(e)[:150]}
 except Exception as e:
  return {"status":"HEAD_AND_RANGE_NETWORK_BLOCKED","reason":repr(e)[:200]}

def public_json(url):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers=HEADERS,method="GET"),timeout=TIMEOUT) as r:
   raw=r.read(4_000_001)
   if len(raw)>4_000_000:raise ValueError("JSON_RESPONSE_TOO_LARGE")
   obj=json.loads(raw)
   return obj,{"status":"HTTP_OK","http_code":r.status,"sha256":hashlib.sha256(raw).hexdigest(),
        "bytes":len(raw)}
 except urllib.error.HTTPError as e:
  return None,{"status":"HTTP_BLOCKED","code":e.code,"message":str(e)[:250]}
 except Exception as e:
  return None,{"status":"NETWORK_OR_PARSE_BLOCKED","message":repr(e)[:250]}

def standard_ok(obj):
 return isinstance(obj,dict) and obj.get("success") is True and obj.get("code") in (0,"0")

def contract_and_depth(symbol):
 suffix=urllib.parse.quote(symbol)
 out={"symbol":symbol,"public_only":True}
 obj,receipt=public_json(M+"/contract/depth/"+suffix+"?limit=20")
 out["depth_http"]=receipt
 if standard_ok(obj) and isinstance(obj.get("data"),dict):
  d=obj["data"]
  bids=d.get("bids",[]);asks=d.get("asks",[])
  try:
   bid=max(float(x[0]) for x in bids)
   ask=min(float(x[0]) for x in asks)
   if bid<=0 or ask<bid:raise ValueError("INVALID_CROSSED_DEPTH")
   t=int(d["timestamp"])
   out["depth_now"]={
      "status":"LIVE_SNAPSHOT_ONLY_NOT_2021_25_HISTORY",
      "timestamp":t,"timestamp_iso":iso(t),
      "best_bid":bid,"best_ask":ask,
      "spread_bps":round((ask-bid)/((bid+ask)/2)*10000,6),
      "visible_bid_top_level_raw":next((x for x in bids if float(x[0])==bid),None),
      "visible_ask_top_level_raw":next((x for x in asks if float(x[0])==ask),None),
      "levels_ask":len(asks),"levels_bid":len(bids),
   }
  except Exception as e:out["depth_now"]={"status":"MALFORMED_LIVE_DEPTH","error":repr(e)}
 else:out["depth_now"]={"status":"NO_VALID_LIVE_DEPTH","api_code":obj.get("code") if isinstance(obj,dict) else None}
 obj,receipt=public_json(M+"/contract/detail/country?symbol="+suffix)
 out["contract_http"]=receipt
 if standard_ok(obj):
  body=obj.get("data")
  arr=body if isinstance(body,list) else ([body] if isinstance(body,dict) else [])
  item=next((i for i in arr if isinstance(i,dict) and i.get("symbol")==symbol),None)
  if item is None and len(arr)==1:item=arr[0]
  if item:
   fields=("symbol","contractSize","minVol","volUnit","maxVol","marketOrderMaxVol",
       "marketOrderMaxLevel","priceScale","minLeverage","maxLeverage","apiAllowed","takerFeeRate","makerFeeRate",
       "feeRateMode","state","openingTime","createTime","contractId","riskLimitType","marketOrderPriceLimitRate1")
   out["contract_now"]={"status":"CURRENT_METADATA_ONLY",
        **{k:item.get(k) for k in fields if k in item}}
  else:out["contract_now"]={"status":"CONTRACT_NOT_FOUND_IN_PUBLIC_RESPONSE","items":len(arr)}
 else:out["contract_now"]={"status":"CONTRACT_API_BLOCKED"}
 obj,receipt=public_json(M+"/contract/funding_rate/history?"+urllib.parse.urlencode({
   "symbol":symbol,"page_num":1,"page_size":1000}))
 out["funding_http"]=receipt
 if standard_ok(obj) and isinstance(obj.get("data"),dict):
  d=obj["data"]
  rows=d.get("resultList",[])
  tvals=[int(x["settleTime"]) for x in rows if "settleTime" in x]
  total=int(d.get("totalPage",0) or 0)
  out["funding_history"]={
    "status":"FIRST_PAGE_ONLY_PARTIAL" if total>1 else "SINGLE_PAGE_NEEDS_COVERAGE_CHECK",
    "first_page_count":len(rows),"total_count":d.get("totalCount"),
    "total_pages":total,"most_recent_ms":max(tvals) if tvals else None,
    "oldest_first_page_ms":min(tvals) if tvals else None,
  }
  if 2<=total<=1000:
   obj2,re2=public_json(M+"/contract/funding_rate/history?"+urllib.parse.urlencode({
     "symbol":symbol,"page_num":total,"page_size":1000}))
   out["funding_last_page_http"]=re2
   if standard_ok(obj2) and isinstance(obj2.get("data"),dict):
    rows2=obj2["data"].get("resultList",[])
    t2=[int(x["settleTime"]) for x in rows2 if "settleTime" in x]
    if t2:
     earliest=min(t2)
     out["funding_history"]["earliest_last_page_ms"]=earliest
     out["funding_history"]["earliest_last_page_iso"]=iso(earliest)
     out["funding_history"]["required_2021_start_ms"]=START
     out["funding_history"]["status"]="EARLIEST_AT_OR_BEFORE_2021_BOUNDARY" if earliest<=START else "OLDER_THAN_AVAILABLE_HISTORY_NOT_PROVEN"
     if earliest>START:out["funding_history"]["status"]="HISTORY_TOO_SHORT_FOR_FULL_2021_2025"
   else:out["funding_history"]["status"]="LAST_PAGE_EMPTY_OR_INVALID"
  elif total>1000:
   out["funding_history"]["status"]="UNBOUNDED_PAGINATION_SOURCE_BLOCKED"
  else:
   if tvals and min(tvals)<=START and max(tvals)>=END:
    out["funding_history"]["status"]="TIMESTAMP_BOUNDARY_ONLY__INTERIOR_NOT_VERIFIED"
   else:out["funding_history"]["status"]="BOUNDARY_COVERAGE_NOT_PROVEN"
 else:out["funding_history"]={"status":"HISTORICAL_FUNDING_API_BLOCKED"}
 return out

def archive_one(symbol,date):
 url=f"{B}/{symbol}/{symbol}-bookTicker-{date}.zip"
 d=fetch_meta(url);d.update({"symbol":symbol,"date":date,"url":url})
 return d

def download_zip(url,maxbytes):
 req=urllib.request.Request(url,headers=HEADERS,method="GET")
 with urllib.request.urlopen(req,timeout=80) as r:
  chunks=[];n=0
  while True:
   x=r.read(1_048_576)
   if not x:break
   n+=len(x)
   if n>maxbytes:raise ValueError("DOWNLOAD_SIZE_CAP_EXCEEDED")
   chunks.append(x)
  return b"".join(chunks)

def sample_bbo(symbol,date,meta):
 if meta["status"] not in ("HEAD_OK","RANGE_GET_OK"):
  return {"status":"NOT_ATTEMPTED_SOURCE_MISSING","symbol":symbol,"date":date}
 try:
  n=int(meta.get("content_length") or "0")
  if n<=0:
   return {"status":"NOT_ATTEMPTED_UNBOUNDED_SIZE","content_length":n}
  if n>LIMIT:
   return {"status":"NOT_ATTEMPTED_TOO_LARGE","content_length":n}
  url=meta["url"];blob=download_zip(url,LIMIT)
  sha=hashlib.sha256(blob).hexdigest()
  check_url=url+".CHECKSUM"
  try:
   with urllib.request.urlopen(urllib.request.Request(check_url,headers=HEADERS,method="GET"),timeout=TIMEOUT) as r:
    contents=r.read(2048).decode(errors="replace").split()
    check=("PASS" if contents and contents[0].lower()==sha else "MISMATCH_OR_UNPARSEABLE")
  except Exception:
   check="UNAVAILABLE"
  if check=="MISMATCH_OR_UNPARSEABLE":raise ValueError("OFFICIAL_BINANCE_CHECKSUM_MISMATCH")
  with zipfile.ZipFile(io.BytesIO(blob)) as z:
   files=[f for f in z.namelist() if not f.endswith("/")]
   if len(files)!=1:raise ValueError("MULTIPLE_BOOKTICKER_ZIP_MEMBERS")
   with z.open(files[0]) as f:
    reader=csv.reader(io.TextIOWrapper(f,encoding="utf-8-sig"))
    fields=next(reader,None)
    if not fields:raise ValueError("BOOKTICKER_EMPTY")
    expected=("update_id","best_bid_price","best_bid_qty","best_ask_price","best_ask_qty","transaction_time","event_time")
    if len(fields)!=7:raise ValueError("BOOKTICKER_HEADER_UNKNOWN")
    # Binance legacy may omit a header; handle that as row0 but report.
    has_header=fields[0].strip().lower()=="update_id"
    sample=[]
    if not has_header:sample.append(fields)
    for row in reader:
     if not row:continue
     sample.append(row)
     if len(sample)>=1000:break
  valid=[];times=[];price_issue=0
  for row in sample:
   if len(row)!=7:
    price_issue+=1;continue
   try:
    update=int(row[0]);bid=float(row[1]);bqty=float(row[2]);ask=float(row[3]);aqty=float(row[4])
    tx=int(row[5]);event=int(row[6])
    if max(tx,event)>10**14:tx//=1000;event//=1000
    if not (math.isfinite(bid) and math.isfinite(ask) and math.isfinite(bqty) and math.isfinite(aqty) and bid>0 and ask>=bid and bqty>0 and aqty>0):
     raise ValueError("CROSSED_OR_BAD_QUOTES")
    if not (date<=datetime.fromtimestamp(event/1000,timezone.utc).strftime("%Y-%m-%d")<=date):
     raise ValueError("WRONG_FILE_DAY")
    spread=(ask-bid)/((ask+bid)/2)*10000
    valid.append((update,bid,ask,bqty,aqty,tx,event,spread));times.append(event)
   except Exception:price_issue+=1
  if not valid:raise ValueError("NO_VALID_QUOTE_ROWS")
  sorted_spreads=sorted(v[-1] for v in valid)
  q=lambda frac:round(sorted_spreads[int((len(sorted_spreads)-1)*frac)],6)
  time_inversions=sum(times[i]<times[i-1] for i in range(1,len(times)))
  return {"status":"SAMPLED_OFFICIAL_BINANCE_BBO_PAYLOAD_PARSE_PASS",
    "source_sha256":sha,"checksum":check,"zip_bytes":len(blob),
    "field_header":fields if has_header else "NO_HEADER","sample_rows":len(sample),
    "valid_rows":len(valid),"bad_rows":price_issue,
    "observed_date":date,"observed_event_start_ms":min(times),"observed_event_end_ms":max(times),
    "event_time_inversions_first_sample":time_inversions,
    "sample_spread_bps_p05":q(.05),"sample_spread_bps_median":q(.5),
    "sample_spread_bps_p95":q(.95),
    "sample_only":True,
    "not_mexc":True,
    "not_trade_timestamp_fill":True}
 except Exception as e:
  return {"status":"BBO_PAYLOAD_SOURCE_BLOCKED","reason":repr(e)[:300]}

def main():
 out=HERE/"VENUE_SOURCE_GATE_RESULT_2026_10_09.json"
 try:
  with ThreadPoolExecutor(max_workers=5) as pool:
   jobs={}
   for sym,msym in PAIRS:jobs[pool.submit(contract_and_depth,msym)]=("mexc",msym)
   for sym,_ in PAIRS:
    for date in DATES:
     jobs[pool.submit(archive_one,sym,date)]=("archive",sym,date)
   data=[];mexc=[]
   for fut in as_completed(jobs):
    desc=jobs[fut]
    try:item=fut.result()
    except Exception as e:
     item={"status":"PROBE_FAILED","reason":repr(e),"identity":desc}
    if desc[0]=="mexc":mexc.append(item)
    else:data.append(item)
  data.sort(key=lambda d:(d.get("symbol",""),d.get("date","")))
  mexc.sort(key=lambda d:d.get("symbol",""))
  first=next((x for x in data if x.get("symbol")=="ETHUSDT" and x.get("date")=="2025-12-01"),None)
  samples={}
  if first:
   samples["ETHUSDT_2025_12_01"]=sample_bbo("ETHUSDT","2025-12-01",first)
  if first and first.get("status") in ("HEAD_OK","RANGE_GET_OK") and (int(first.get("content_length") or 0) <=20_000_000):
   second=next((x for x in data if x.get("symbol")=="ETHUSDT" and x.get("date")=="2024-01-15"),None)
   if second:samples["ETHUSDT_2024_01_15"]=sample_bbo("ETHUSDT","2024-01-15",second)
  old_summary={}
  for sym,_ in PAIRS:
   present=[x for x in data if x.get("symbol")==sym and x.get("status") in ("HEAD_OK","RANGE_GET_OK")]
   old_summary[sym]={"present":len(present),"asked":len(DATES),
     "dates":[x.get("date") for x in present],
     "2021_coverage_proven":any(x.get("date")=="2021-01-02" for x in present)}
  mexc_depth_state="MEXC_SNAPSHOTS_PRESENT_CURRENT_ONLY" if any(x.get("depth_now",{}).get("status")=="LIVE_SNAPSHOT_ONLY_NOT_2021_25_HISTORY" for x in mexc) else "NO_LIVE_PUBLIC_DEPTH_PROVEN"
  earliest=[]
  for x in mexc:
   a=x.get("funding_history",{})
   if a.get("earliest_last_page_ms"):earliest.append(a["earliest_last_page_ms"])
  payload_pass=any(x.get("status")=="SAMPLED_OFFICIAL_BINANCE_BBO_PAYLOAD_PARSE_PASS" for x in samples.values())
  result={
   "status":"SOURCE_GATE_EXECUTED__NO_HISTORICAL_MEXC_EXECUTION_APPROVAL",
   "MEXC_historical_BBO_2021_2025":"SOURCE_NOT_ESTABLISHED",
   "MEXC_contract_and_current_depth":mexc_depth_state,
   "MEXC_funding_history":"PARTIAL_OR_BLOCKED_UNLESS_PER_SYMBOL_HISTORICAL_COMPLETENESS_PROVED",
   "BINANCE_bookTicker_presence_matrix":old_summary,
   "BINANCE_BBO_payload_source_status":"SAMPLED_BBO_PAYLOAD_PROVEN" if payload_pass else "SAMPLED_BBO_PAYLOAD_NOT_PROVEN",
   "BINANCE_quote_probe_scope":"ONLY_ARCHIVE_DATES_NOT_EXACT_ORIGINAL_TRADE_TIMESTAMPS",
   "MEXC_API_taker_fee_each_side_bps_official_2026":8,
   "MEXC_API_roundtrip_fee_only_bps":16,
   "original_Binance_BASE_roundtrip_fees_and_fixed_slip_bps":24,
   "current_fee_does_not_prove_history":True,
   "archived_2026_holdout_opened":False,
   "research_only":True,"live_go":False,
   "source_documents":[
     "https://www.mexc.io/api-docs/futures/market-endpoints/get-contract-order-book-depth",
     "https://www.mexc.io/api-docs/futures/market-endpoints/get-funding-rate-history",
     "https://www.mexc.io/api-docs/futures/market-endpoints/get-contract-info",
     "https://www.mexc.com/en-GB/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742",
     "https://github.com/binance/binance-public-data/issues/305"
   ],
   "archive_presence_matrix":data,
   "mexc_public_api_observations":mexc,
   "archive_actual_payload_samples":samples,
  }
  out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
  print("VENUE_SOURCE_GATE_RESULT",json.dumps({
    "gate":result["status"],"mexc_bbo":result["MEXC_historical_BBO_2021_2025"],
    "mexc_live_depth":mexc_depth_state,"binance_dates":old_summary,"sample":samples,
    "mexc_funding":[{"symbol":x.get("symbol"),"funding":x.get("funding_history"),"contract":x.get("contract_now"),
      "depth_status":x.get("depth_now",{}).get("status")} for x in mexc]
  },sort_keys=True),flush=True)
 except Exception as e:
  out.write_text(json.dumps({"status":"SOURCE_GATE_TECHNICAL_FAIL_CLOSED","reason":repr(e),
    "science_credit":"ZERO","live_go":False},indent=2)+"\n")
  traceback.print_exc();sys.exit(2)

if __name__=="__main__":main()

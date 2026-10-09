#!/usr/bin/env python3
"""Unauthenticated fixed three-year MEXC historical 1H market price SOURCE probe.
No 2026 outcome data, private endpoints, trading, orders, accounts, or wallet.
"""
import concurrent.futures, datetime, hashlib, json, math, sys, urllib.request, urllib.error, urllib.parse, traceback
from pathlib import Path

OUT=Path(__file__).resolve().parent/"MEXC_HISTORICAL_1H_SAMPLE_GATE_V01.json"
PAIRS=("ETH_USDT","SOL_USDT","BNB_USDT")
DAYS=("2021-06-15","2023-06-15","2025-06-15")
BASE="https://contract.mexc.com/api/v1/contract/kline/"
def call(sym,day):
 try:
  start=datetime.datetime.fromisoformat(day).replace(tzinfo=datetime.timezone.utc)
  st=int(start.timestamp());end=st+86400-1
  url=BASE+urllib.parse.quote(sym)+"?"+urllib.parse.urlencode({
      "interval":"Min60","start":st,"end":end})
  request=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-PublicKlineSourceProbe-v01","Accept":"application/json"},method="GET")
  with urllib.request.urlopen(request,timeout=25) as r:
   raw=r.read(2_000_001)
   if len(raw)>2_000_000:raise ValueError("RESPONSE_TOO_LARGE")
   j=json.loads(raw)
   h={"HTTP_status":r.status,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)}
  if not isinstance(j,dict) or j.get("success") is not True or j.get("code") not in (0,"0"):
   return {"symbol":sym,"date":day,"status":"API_INVALID_RESPONSE",**h,"api_code":j.get("code") if isinstance(j,dict) else None}
  d=j.get("data",{})
  ts=d.get("time",[])
  names=("open","high","low","close","vol")
  if not isinstance(ts,list) or not all(isinstance(d.get(f),list) for f in names):
   return {"symbol":sym,"date":day,"status":"OHLCV_STRUCTURE_INVALID",**h}
  n=len(ts)
  if not all(len(d[f])==n for f in names):
   return {"symbol":sym,"date":day,"status":"OHLCV_COLUMN_LENGTH_MISMATCH",**h}
  stamps=[int(x)*1000 if int(x)<10**11 else int(x) for x in ts]
  within=sum(st*1000 <= x <= (st+86399)*1000 for x in stamps)
  unique=len(set(stamps))
  strictly_hourly=len(stamps)==24 and set(stamps)==set((st+k*3600)*1000 for k in range(24))
  invalid=0
  for i in range(n):
   try:
    o,hi,lo,c,v=(float(d[k][i]) for k in names)
    if not all(map(math.isfinite,(o,hi,lo,c,v))) or not (lo<=min(o,c)<=max(o,c)<=hi and o>0 and v>=0):
     invalid+=1
   except Exception:invalid+=1
  return {"symbol":sym,"date":day,
    "status":"FIXED_DAY_1H_24_OF_24_SOURCE_PASS" if strictly_hourly and invalid==0 else "SOURCE_INVALID_FOR_REQUESTED_DAY",
    **h,"returned":n,"within_requested_day":within,"unique_timestamp_count":unique,
    "has_exact_24_hour_set":strictly_hourly,"invalid_price_rows":invalid,
    "min_timestamp_ms":min(stamps) if stamps else None,
    "max_timestamp_ms":max(stamps) if stamps else None,
    "market_price_only_not_orderbook":True}
 except urllib.error.HTTPError as e:
  return {"symbol":sym,"date":day,"status":"PUBLIC_API_HTTP_BLOCKED","http_code":e.code,"reason":str(e)}
 except Exception as e:
  return {"symbol":sym,"date":day,"status":"PUBLIC_API_NETWORK_OR_PARSE_BLOCKED","reason":repr(e)[:300]}
def main():
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
   futs=[pool.submit(call,s,d) for s in PAIRS for d in DAYS]
   data=[f.result() for f in futs]
  data.sort(key=lambda a:(a["symbol"],a["date"]))
  good=sum(x["status"]=="FIXED_DAY_1H_24_OF_24_SOURCE_PASS" for x in data)
  a={"status":"ALL_NINE_FIXED_DAYS_1H_SOURCE_PROBE_PASS" if good==9 else (
        "PARTIAL_MEXC_1H_HISTORICAL_DAY_SOURCE" if good else "MEXC_HISTORICAL_1H_SOURCE_BLOCKED"),
     "requested_nine_pairs_days":9,"proven_exact_day_count":good,
     "symbol_date_probes":data,"full_2021_2025_continuity_proven":False,
     "full_historical_mexc_funding_proven":False,"bid_ask_2021_2025_proven":False,
     "real_executable_net_edge":"UNVERIFIED","independent_oos":False,"live_go":False}
  OUT.write_text(json.dumps(a,indent=2,sort_keys=True)+"\n")
  print("MEXC_HIST_1H_SOURCE_PROBE",json.dumps({"status":a["status"],"pass":good,"details":data},sort_keys=True),flush=True)
 except Exception as e:
  traceback.print_exc()
  OUT.write_text(json.dumps({"status":"TECHNICAL_FAIL_CLOSED","reason":repr(e),"live_go":False},indent=2)+"\n")
  sys.exit(2)
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Pre-frozen Kraken Derivatives public GET source feasibility. NO accounts or trading."""
import concurrent.futures, datetime, hashlib, json, sys, time, traceback, urllib.error,urllib.parse,urllib.request
from pathlib import Path
HERE=Path(__file__).resolve().parent
OUT=HERE/"KRAKEN_PUBLIC_VENUE_SOURCE_GATE_RECEIPT_V01.json"
ROOT="https://futures.kraken.com"
SYMS=("PF_ETHUSD","PF_SOLUSD","PF_BNBUSD")
DATES=("2021-06-15","2023-06-15","2025-06-15")
ORDER_DAY="2023-05-24"
AGENT={"User-Agent":"CryptoLab-BTCConvex-ReadOnly-VenueSourceV01","Accept":"application/json"}
def utc_ms(date):
 return int(datetime.datetime.fromisoformat(date).replace(tzinfo=datetime.timezone.utc).timestamp()*1000)
def get(url):
 req=urllib.request.Request(url,headers=AGENT,method="GET")
 try:
  with urllib.request.urlopen(req,timeout=23) as resp:
   b=resp.read(1500001)
   if len(b)>1500000:raise ValueError("PUBLIC_JSON_TOO_LARGE")
   return json.loads(b),{"http":resp.status,"bytes":len(b),"sha256":hashlib.sha256(b).hexdigest(),"status":"PUBLIC_HTTP_OK"}
 except urllib.error.HTTPError as e:
  return None,{"http":e.code,"status":"HTTP_NOT_ACCESSIBLE","error":str(e)[:160]}
 except Exception as e:
  return None,{"status":"NETWORK_OR_JSON_BLOCKED","error":repr(e)[:240]}
def instruments():
 u=ROOT+"/derivatives/api/v3/instruments"
 obj,meta=get(u)
 r={"source_url":u,"http_receipt":meta}
 if isinstance(obj,dict):
  arr=obj.get("instruments",[])
  if isinstance(arr,list):
   matches=[x for x in arr if isinstance(x,dict) and x.get("symbol") in SYMS]
   r["status"]="PUBLIC_INSTRUMENTS_SCHEMA_READ"
   r["count_total"]=len(arr)
   r["requested_symbols_found"]=[x.get("symbol") for x in matches]
   r["specific_instrument_public_fields"]=[{
    k:v for k,v in x.items() if k in
    ("symbol","type","tradeable","openingDate","firstTradeTime","tickSize","contractSize",
      "contractValueTradePrecision","maxPositionSize","marginLevels","pair","underlying","fundingRate")
   } for x in matches]
  else:r["status"]="UNKNOWN_INSTRUMENT_STRUCTURE"
 else:r["status"]="INSTRUMENTS_NOT_ACCESSIBLE"
 return r
def candle(sym,date):
 beginning=utc_ms(date)//1000
 end=beginning+86400
 q=urllib.parse.urlencode({"from":beginning,"to":end,"count":48})
 u=f"{ROOT}/api/charts/v1/trade/{sym}/1h?{q}"
 j,receipt=get(u)
 r={"symbol":sym,"date":date,"url":u,"http_receipt":receipt}
 if isinstance(j,dict):
  candidates=j.get("candles",j.get("elements",None))
  if not isinstance(candidates,list):
   r["status"]="UNKNOWN_CANDLE_BODY_SHAPE"
   r["response_keys"]=sorted(list(j))[:18]
   return r
  valid=0;timestamps=[];schema_set=set()
  for x in candidates:
   if not isinstance(x,dict):continue
   schema_set.update(x.keys())
   k=x.get("time",x.get("timestamp"))
   try:
    t=int(k)
    if t<10**11:t*=1000
    if beginning*1000<=t<end*1000:valid+=1
    timestamps.append(t)
   except Exception:continue
  target={beginning*1000+i*3600000 for i in range(24)}
  r.update({"body_elements":len(candidates),"in_requested_day":valid,
    "timestamps_unique":len(set(timestamps)),"column_keys":sorted(schema_set)[:25],
    "matches_exact_24_UTC_hours":set(timestamps)==target})
  r["status"]="EXACT_DAY_CANDLES_PASS" if set(timestamps)==target else "DAY_BARS_PARTIAL_OR_INVALID"
 elif isinstance(j,list):
  r["status"]="UNEXPECTED_LIST_BODY";r["len"]=len(j)
 else:r["status"]="CANDLE_SOURCE_NOT_ACCESSIBLE"
 return r
def orders(sym):
 start=utc_ms(ORDER_DAY);end=start+86400000
 u=f"{ROOT}/api/history/v3/market/{sym}/orders?"+urllib.parse.urlencode({
   "since":start,"before":end,"sort":"asc","count":2
  })
 j,m=get(u)
 r={"symbol":sym,"day":ORDER_DAY,"url":u,"http_receipt":m}
 if isinstance(j,dict):
  r["keys"]=sorted(j.keys())[:18]
  for k in ("elements","orders","events"):
   x=j.get(k)
   if isinstance(x,list):
    r["returned_event_count"]=len(x)
    r["event_value_keys"]=sorted(x[0].keys())[:25] if x and isinstance(x[0],dict) else []
  r["status"]="ORDER_EVENT_ENDPOINT_REACHABLE_NOT_BOOK_SNAPSHOT"
 else:r["status"]="ORDER_EVENT_ENDPOINT_UNAVAILABLE"
 return r
def main():
 try:
  with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:
   a=p.submit(instruments)
   b=[p.submit(candle,s,d) for s in SYMS for d in DATES]
   c=[p.submit(orders,s) for s in SYMS]
   ins=a.result()
   candles=[x.result() for x in b]
   order=[x.result() for x in c]
  candles.sort(key=lambda x:(x["symbol"],x["date"]))
  order.sort(key=lambda x:x["symbol"])
  passed=[x for x in candles if x["status"]=="EXACT_DAY_CANDLES_PASS"]
  found=ins.get("requested_symbols_found",[])
  result={
   "status":"KRAKEN_PUBLIC_SOURCE_SCAN_COMPLETE_NOT_EXECUTION_CERTIFIED",
   "frozen_target_derivatives_symbols":SYMS,
   "instrument_source":ins,
   "exact_three_date_hourly_probe":candles,
   "hourly_source_days_passed":len(passed),
   "hourly_source_day_total":9,
   "public_historical_order_events_probe":order,
   "order_events_not_orderbook_bbo":True,
   "2021_2025_full_quote_depth_archive_verified":False,
   "2021_2025_full_derivatives_funding_verified":False,
   "2021_2025_exact_fee_parity_verified":False,
   "current_base_taker_fee_per_side_bps_from_official_2026_10_07":5,
   "current_base_maker_fee_per_side_bps_from_official_2026_10_07":2,
   "swiss_geographic_list_not_explicitly_excluded_but_account_eligibility_not_proven":True,
   "source_links":{
     "fees":"https://support.kraken.com/articles/360048917612-fee-schedule",
     "eligibility":"https://support.kraken.com/articles/360023786632-kraken-derivatives-eligibility",
     "charts":"https://docs.kraken.com/api/docs/futures-api/charts/candles",
     "events":"https://docs.kraken.com/api/docs/futures-api/history/get-public-order-events",
   },
   "no_account_data":True,"no_paid_source":True,"no_orders":True,
   "no_new_independent_oos":True,"live_go":False
  }
  OUT.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
  print("KRAKEN_VENUE_SOURCE_GATE",json.dumps({
    "status":result["status"],"instruments":found,"hourly_days_passed":len(passed),
    "hourly_samples":[{"symbol":x["symbol"],"date":x["date"],"status":x["status"],
       "http":x["http_receipt"].get("http"),"body":x.get("body_elements")} for x in candles],
    "order_event_endpoint_status":[{"symbol":x["symbol"],"status":x["status"],
        "http":x["http_receipt"].get("http"),"events":x.get("returned_event_count")} for x in order],
    "historical_book_confirmed":False
  },sort_keys=True),flush=True)
 except Exception as e:
  OUT.write_text(json.dumps({"status":"KRAKEN_SOURCE_TECHNICAL_FAIL_CLOSED","reason":repr(e),
   "live_go":False},indent=2)+"\n")
  traceback.print_exc();sys.exit(2)
if __name__=="__main__":main()

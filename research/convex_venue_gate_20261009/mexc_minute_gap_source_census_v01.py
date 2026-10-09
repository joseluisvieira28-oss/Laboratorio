#!/usr/bin/env python3
"""MEXC full monthly official 1h source census, independent 1m exact-gap source probe.
Source/coverage ONLY, no strategy, trading, accounts or 2026 outcomes.
"""
import hashlib, json, math, time, urllib.request, urllib.error, urllib.parse, traceback, sys
from datetime import datetime,timezone
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import defaultdict

HERE=Path(__file__).resolve().parent
OUTPUT=HERE/"MEXC_HOURLY_MINUTE_SOURCE_CENSUS_V01.json"
SYMBOLS=("ETH_USDT","SOL_USDT","BNB_USDT")
MONTHS=[(y,m) for y in range(2020,2026) for m in range(1,13) if y!=2020 or m>=12]
HOUR=3600000
MIN=60000
HOST="https://contract.mexc.com/api/v1/contract/kline/"
assert len(MONTHS)==61

def timestamp(y,m):return int(datetime(y,m,1,tzinfo=timezone.utc).timestamp()*1000)
def get_public(sym,interval,tstart,tend):
 url=HOST+urllib.parse.quote(sym)+"?"+urllib.parse.urlencode({"interval":interval,
      "start":int(tstart//1000),"end":int(tend//1000)})
 last=None
 for attempt in range(4):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-MEXC-Official-1h-1m-Source-Census-v01","Accept":"application/json"},method="GET")
   with urllib.request.urlopen(req,timeout=35) as r:
    body=r.read(2_000_001)
   if len(body)>2_000_000:raise ValueError("PUBLIC_SOURCE_BYTES_LIMIT_EXCEEDED")
   j=json.loads(body)
   if not (isinstance(j,dict) and j.get("success") is True and j.get("code") in (0,"0") and isinstance(j.get("data"),dict)):
    raise ValueError("MEXC_SOURCE_PAYLOAD_FAIL")
   return j["data"],{"sha256":hashlib.sha256(body).hexdigest(),"url":url,"bytes":len(body)}
  except Exception as e:
   last=repr(e)
   if attempt<3:time.sleep(.5*(attempt+1))
  finally:time.sleep(.3)
 raise ValueError("SOURCE_FETCH_FAILED:"+sym+":"+interval+":"+str(last))

def parse(source):
 ts=source.get("time",[])
 fields=("open","high","low","close","vol")
 if not isinstance(ts,list) or any(not isinstance(source.get(z),list) or len(source[z])!=len(ts) for z in fields):
  raise ValueError("BAD_KLINE_COLUMNS")
 seen={}
 dup=0;bad=0
 for k,item in enumerate(ts):
  try:
   t=int(item)
   if t<10**11:t*=1000
   o,h,l,c,v=(float(source[f][k]) for f in fields)
   if (not all(math.isfinite(z) for z in (o,h,l,c,v)) or o<=0 or l<=0 or v<0 or l>min(o,c) or max(o,c)>h):
    raise ValueError("OHLC_INVALID")
   if t in seen:dup+=1
   else:seen[t]=(o,h,l,c,v)
  except Exception:bad+=1
 return seen,dup,bad

def month(sym,y,m):
 start=timestamp(y,m)
 end=timestamp(y+1,1) if m==12 else timestamp(y,m+1)
 src,receipt=get_public(sym,"Min60",start,end-1000)
 rows,duplicates,bad=parse(src)
 expected=set(range(start,end,HOUR));actual=set(rows)
 missing=sorted(expected-actual);unexpected=sorted(actual-expected)
 return {
  "sym":sym,"month":f"{y:04}-{m:02}",
  "start_ms":start,"end_ms":end,"expected_count":len(expected),
  "actual_unique_count":len(rows),"duplicate_count":duplicates,"invalid_record_count":bad,
  "missing_hours_ms":missing,"unexpected_hours_ms":unexpected,
  "source_sha256":receipt["sha256"],"source_url":receipt["url"],"source_bytes":receipt["bytes"],
  "_bars":rows,
 }

def valid_minute(sym,hour):
 d,info=get_public(sym,"Min1",hour,hour+HOUR-1000)
 rows,dups,bad=parse(d)
 want=list(range(hour,hour+HOUR,MIN))
 result={"symbol":sym,"hour_ms":hour,"url":info["url"],
         "sha256":info["sha256"],"returned_unique_minute_bars":len(rows),
         "duplicate_count":dups,"invalid_count":bad}
 if dups or bad or set(rows)!=set(want):
  result["status"]="EXACT_MINUTE_COVERAGE_BLOCKED"
  result["missing_minutes"]=len(set(want)-set(rows))
  return None,result
 first,last=rows[want[0]],rows[want[-1]]
 out={"t":hour,"open":first[0],"high":max(rows[t][1] for t in want),
       "low":min(rows[t][2] for t in want),"close":last[3],"volume":sum(rows[t][4] for t in want)}
 result["status"]="EXACT_60_MINUTES_VALID"
 result["minute_composite_OHLCV"]=out
 return out,result

def main():
 try:
  allmonths=[];errors=[]
  with ThreadPoolExecutor(max_workers=3) as ex:
   futures={ex.submit(month,s,y,m):(s,y,m) for s in SYMBOLS for y,m in MONTHS}
   for fut in as_completed(futures):
    sym,y,m=futures[fut]
    try:
     allmonths.append(fut.result())
    except Exception as e:
     errors.append({"symbol":sym,"month":f"{y:04}-{m:02}","reason":repr(e)})
  allmonths.sort(key=lambda d:(d["sym"],d["month"]))
  gaps=[]
  records={}
  for row in allmonths:
   k=(row["sym"],row["month"])
   records[k]=row
   for hour in row["missing_hours_ms"]:gaps.append((row["sym"],row["month"],hour))
  controls={};minute_gap_receipts=[];hour_gap_recovered=0;first_unrecovered=[]
  if len(gaps)<=100 and not errors:
   handled=set()
   for sym,ym,hour in gaps:
    try:
     minute,meta=valid_minute(sym,hour)
     minute_gap_receipts.append({**meta,"type":"MISSING_1H"})
     if minute is None:
      first_unrecovered.append({"symbol":sym,"hour_ms":hour,"reason":meta["status"]})
     else:hour_gap_recovered+=1
     if (sym,ym) not in handled:
      handled.add((sym,ym))
      src=records[(sym,ym)]
      control_t=hour-HOUR
      while control_t>=src["start_ms"] and control_t not in src["_bars"]:
       control_t-=HOUR
      if control_t<src["start_ms"]:
       controls[f"{sym}:{ym}"]={"status":"NO_PRECEDING_CONTROL_HOUR"}
       first_unrecovered.append({"symbol":sym,"hour_ms":hour,"reason":"NO_PRECEDING_CONTROL"})
      else:
       check,control_meta=valid_minute(sym,control_t)
       original=src["_bars"][control_t]
       verdict="MATCH"
       if not check:
        verdict="CONTROL_MINUTE_COVERAGE_BLOCKED"
       else:
        def same(a,b,abs_tol,rel_tol):
         return math.isclose(float(a),float(b),abs_tol=abs_tol,rel_tol=rel_tol)
        for attr,orig,n in zip(("open","high","low","close","volume"),original,range(5)):
         if not same(check[attr],orig,1e-5 if attr=="volume" else 1e-8,1e-7 if attr=="volume" else 1e-8):
          verdict=f"CONTROL_MISMATCH:{attr}"
          break
       controls[f"{sym}:{ym}"]={
         "status":verdict,"hour_ms":control_t,"source_sha256":control_meta["sha256"],
         "original_official_1h":list(original),
         "aggregated_official_1m":check,
       }
       if verdict!="MATCH":first_unrecovered.append({"symbol":sym,"hour_ms":control_t,"reason":verdict})
    except Exception as e:
     first_unrecovered.append({"symbol":sym,"hour_ms":hour,"reason":repr(e)})
  unacceptable=sum(r["duplicate_count"]>0 or r["invalid_record_count"]>0 or bool(r["unexpected_hours_ms"]) for r in allmonths)
  complete_1h=len(gaps)==0 and len(errors)==0 and unacceptable==0
  alternate_ok=(bool(gaps) and len(gaps)<=100 and len(errors)==0 and unacceptable==0
     and len(first_unrecovered)==0 and hour_gap_recovered==len(gaps) and all(x["status"]=="MATCH" for x in controls.values()))
  status=("SOURCE_1H_FULL_PASS" if complete_1h else
       "OFFICIAL_MIN1_EXACT_RECOVERY_AVAILABLE_SOURCE_ONLY" if alternate_ok else
       "SOURCE_COVERAGE_BLOCKED")
  summary={
   "status":status,"science_mode":"SOURCE_PROVENANCE_ONLY_NO_SIGNAL_OUTCOMES_OPENED",
   "symbols":SYMBOLS,"months_attempted":183,"monthly_ok":len(allmonths),
   "monthly_fetch_failures":errors,"missing_1h_total":len(gaps),
   "missing_1h_hours": [{"symbol":s,"month":m,"hour_ms":h} for s,m,h in gaps][:130],
   "unexpected_time_buckets":sum(len(z["unexpected_hours_ms"]) for z in allmonths),
   "bad_or_duplicate_months":unacceptable,
   "attempted_official_minute_gap_recovery":len(gaps)<=100 and not errors,
   "exact_minutes_gap_recovered":hour_gap_recovered,
   "exact_minutes_gap_control_receipts":controls,
   "exact_minutes_missing_hour_receipts":minute_gap_receipts,
   "unresolved_gap_control":first_unrecovered[:130],
   "monthly_receipts":[{k:v for k,v in m.items() if k!="_bars"} for m in allmonths],
   "no_price_only_pnl_computed":True,
   "2021_2025_mexc_funding_complete":False,
   "2021_2025_mexc_bbo_history_complete":False,
   "live_go":False,
  }
  OUTPUT.write_text(json.dumps(summary,sort_keys=True,indent=2)+"\n")
  print("MEXC_OFFICIAL_MIN1_CENSUS_FINAL",json.dumps({
    "status":status,"months_ok":len(allmonths),"missing_hours_total":len(gaps),
    "missing_hours":summary["missing_1h_hours"][:30],"minute_recovered":hour_gap_recovered,
    "unresolved":first_unrecovered[:30],"control_summary":{k:v["status"] for k,v in controls.items()},
    "fetch_errors":errors[:8]},sort_keys=True),flush=True)
 except Exception as e:
  OUTPUT.write_text(json.dumps({"status":"TECHNICAL_FAIL_CLOSED","reason":repr(e),
    "economic_credit":"ZERO","live_go":False},indent=2)+"\n")
  traceback.print_exc();sys.exit(2)
if __name__=="__main__":main()

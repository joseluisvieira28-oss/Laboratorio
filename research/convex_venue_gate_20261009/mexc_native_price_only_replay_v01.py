#!/usr/bin/env python3
"""MEXC 2020-12 through 2025-12 native public 1h retrospective PRICE-ONLY transfer.
Original frozen signal/fee/slip costs; NO actual 2021-25 MEXC funding or BBO.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, os, runpy, subprocess, sys, time, traceback, urllib.error, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE_SHA="49e2bafd2e487352db24f2a812e936372a2cb1ff"
START=1609459200000
LAST=1767222000000 # 2025-12-31 23:00 UTC
FIRST_WARMUP=1606780800000
SYMS=("ETHUSDT","SOLUSDT","BNBUSDT")
BASEURL="https://contract.mexc.com/api/v1/contract/kline/"
MONTHS=[]
for y in range(2020,2026):
 for m in range(1,13):
  if y==2020 and m<12:continue
  MONTHS.append((y,m))
assert len(MONTHS)==61

def first(y,m):
 return datetime(y,m,1,tzinfo=timezone.utc)
def t_millis(d):return int(d.timestamp()*1000)
def get_month(symbol,year,month):
 nextday=first(year+1,1) if month==12 else first(year,month+1)
 start=first(year,month);start_sec=int(start.timestamp());end_sec=int(nextday.timestamp())-1
 ms=t_millis(start);maxms=t_millis(nextday)
 url=BASEURL+symbol.replace("USDT","_USDT")+"?"+urllib.parse.urlencode({
  "interval":"Min60","start":start_sec,"end":end_sec})
 raw=None;err=None
 for try_id in range(4):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-MEXC-NativePriceOnly-v01/1.0","Accept":"application/json"},method="GET")
   with urllib.request.urlopen(req,timeout=35) as f:
    raw=f.read(2_000_001)
    if len(raw)>2_000_000:raise ValueError("MEXC_PUBLIC_HOURLY_PAYLOAD_TOO_LARGE")
   obj=json.loads(raw)
   if not (isinstance(obj,dict) and obj.get("success") is True and obj.get("code") in (0,"0")):
    raise ValueError("MEXC_KLINE_JSON_NOT_OK")
   break
  except Exception as e:
   err=repr(e)
   if try_id==3:raise ValueError(f"MEXC_SOURCE_REQUEST_FAIL:{symbol}:{year}-{month:02}:{err}")
   time.sleep(.6*(try_id+1))
  finally:
   time.sleep(.38)
 d=obj.get("data")
 if not isinstance(d,dict):raise ValueError("MEXC_KLINE_DATA_NOT_MAP")
 cols=("time","open","high","low","close","vol")
 if any(not isinstance(d.get(x),list) for x in cols):raise ValueError("MEXC_KLINE_SCHEMA_INVALID")
 count=len(d["time"])
 if any(len(d[k])!=count for k in cols):raise ValueError("KLINE_COLUMN_COUNT_CONFLICT")
 expect=int((maxms-ms)//3600000)
 if count!=expect:raise ValueError(f"MONTHLY_MEXC_SOURCE_HOLES:{symbol}:{year}-{month:02}:{count}:{expect}")
 rows=[]
 for i in range(count):
  t=int(d["time"][i]);t=t*1000 if t<10**11 else t
  o,h,l,c,v=(float(d[k][i]) for k in cols[1:])
  if not all(math.isfinite(x) for x in (o,h,l,c,v)) or not (o>0 and l>0 and l<=min(o,c)<=max(o,c)<=h and v>=0):
   raise ValueError(f"INVALID_NATIVE_MEXC_HOURLY_BAR:{symbol}:{t}")
  rows.append({"t":t,"open":o,"high":h,"low":l,"close":c,"volume":v})
 rows.sort(key=lambda x:x["t"])
 if [r["t"] for r in rows]!=list(range(ms,maxms,3600000)):
  raise ValueError(f"NATIVE_MEXC_BAR_GAP_OR_TIMESTAMP:{symbol}:{year}-{month:02}")
 meta={"symbol":symbol.replace("USDT","_USDT"),"month":f"{year:04}-{month:02}",
       "url":url,"raw_response_sha256":hashlib.sha256(raw).hexdigest(),
       "bytes":len(raw),"bar_count":len(rows),"earliest_bar_ms":rows[0]["t"],
       "latest_bar_ms":rows[-1]["t"]}
 return rows,meta

def original_definitions(path):
 blob=subprocess.run(["git","hash-object",str(path)],text=True,check=True,capture_output=True).stdout.strip()
 if blob!=SOURCE_SHA:raise ValueError("ORIGINAL_SIMULATOR_HASH_MISMATCH")
 s=Path(path).read_text()
 if s.count("\nout={\n")!=1:raise ValueError("ORIGINAL_SCRIPT_STRUCTURE_CHANGED")
 env={"__file__":str(Path(path).resolve()),"__name__":"original_frozen_definitions","__builtins__":__builtins__}
 exec(compile(s.split("\nout={\n")[0],str(path),"exec"),env)
 if env["START_MS"]!=START or env["END_MS"]!=LAST:raise ValueError("ORIGINAL_STRATEGY_BOUNDARY_MODIFIED")
 if env["FEE"]!=.001 or env["STOP"]!=.04 or env["TRAIL"]!=.12 or env["ACT"]!=.05:raise ValueError("ORIGINAL_PARAMETERS_MODIFIED")
 return env

def load_one(symbol):
 bars=[];receipts=[]
 for year,month in MONTHS:
  b,meta=get_month(symbol,year,month)
  bars.extend(b);receipts.append(meta)
  if month in (3,6,9,12):
   print("MEXC_NATIVE_SOURCE_PROGRESS",symbol,f"{year:04}-{month:02}","hourly",len(bars),flush=True)
 if not bars or bars[0]["t"]!=FIRST_WARMUP or bars[-1]["t"]!=LAST:raise ValueError("NATIVE_SOURCE_BOUNDARY_MISSING:"+symbol)
 if len(bars)!=len(set(x["t"] for x in bars)):raise ValueError("NATIVE_SOURCE_DUPLICATE:"+symbol)
 count=sum(START<=b["t"]<=LAST for b in bars)
 if count!=43824:raise ValueError(f"NATIVE_ECONOMIC_BARS_NOT_43824:{symbol}:{count}")
 if len(bars)!=43824+744:raise ValueError("NATIVE_2020_DEC_WARMUP_NOT_744:"+symbol)
 return symbol,bars,receipts

def main():
 import argparse
 p=argparse.ArgumentParser()
 p.add_argument("--pinned-original",required=True)
 args=p.parse_args()
 out=HERE/"MEXC_NATIVE_5Y_PRICE_ONLY_TRANSFER_RESULT_2026_10_09.json"
 try:
  env=original_definitions(args.pinned_original)
  all_data={}
  with ThreadPoolExecutor(max_workers=3) as ex:
   futures=[ex.submit(load_one,sym) for sym in SYMS]
   for f in as_completed(futures):
    sym,bars,receipts=f.result()
    all_data[sym]={"bars":bars,"receipts":receipts}
  results={};ledgers={"BASE":{},"STRESS":{}};summ={}
  for sym in SYMS:
   data=all_data[sym]
   symresults={}
   for layer,slip in (("BASE",.0002),("STRESS",.0005)):
    r=env["simulate"](sym,data["bars"],{},"PARENT",slip)
    ledgers[layer][sym]=r["trades"]
    symresults[layer]={
      "completed_trades":r["closed_trades"],
      "price_only_return_pct":round(r["net_return"]*100,6),
      "original_fee_bps_side_inherited_model":10,
      "adverse_slippage_bps_side_inherited_model":slip*10000,
      "excluded_all_historical_mexc_funding":True,
      "price_only_profit_factor":r["profit_factor"],
      "price_only_bar_mtm_dd_pct":round(r["max_mark_to_market_drawdown"]*100,6),
      "price_only_wins":r["wins"],"price_only_losses":r["losses"],
      "zero_funding_cashflow":r["funding_cashflow"],
      "price_only_net_without_top1_usdt":round(r["net_without_top1"],6),
    }
   results[sym]=symresults
   summ[sym]={
    "hourly_economic_bars":43824,
    "warmup_hourly_bars":744,
    "market_source_months":len(data["receipts"]),
    "month_source_receipts":data["receipts"],
   }
  # fixed original risk-engine replay of MEXC-native price-only trades
  prior=runpy.run_path(str(HERE.parent/"convex_risk_v01"/"convex_risk_replay_v01.py"),run_name="import_source_only_replay")
  events_for=prior["events_for"];replay=prior["replay"]
  output={}
  for layer in ("BASE","STRESS"):
   output[layer]={}
   for risk in (.0025,.005):
    events=events_for(SYMS,ledgers["BASE"],ledgers[layer],0,False)
    t=replay(events,risk)
    output[layer][str(risk)]={
     "price_only_shared_portfolio_return_pct":t["net_return_pct"],
     "closed_only_dd_pct":t["realized_only_dd_pct"],
     "n_trades":t["trades"],"skipped":t["skipped_concurrent_or_budget"],
     "year_realized_price_only_pnl":t["year_net_usdt"],
     "funding_excluded":True,"MEXC_actual_2021_2025_execution_spread_excluded":True}
  result={
    "status":"MEXC_NATIVE_FULL_1H_2021_2025_SOURCE_PASS__PRICE_TRANSFER_DIAGNOSTIC_ONLY",
    "evidence_type":"RETROSPECTIVE_PRICE_ONLY_WITH_FEE_SLIP_PROXY_EXCLUDING_MEXC_FUNDING",
    "scientific_credit":"NO_NEW_OOS__NOT_FULL_ECONOMIC_NET",
    "symbols":SYMS,"month_count_per_symbol":61,
    "original_pinned_source_sha":SOURCE_SHA,
    "source_manifests":summ,
    "independent_symbol_PRICE_ONLY":results,
    "shared_capital_PRICE_ONLY":output,
    "MEXC_historic_funding_2021_2025_complete":False,
    "MEXC_historic_bidask_execution_complete":False,
    "taker_fee_model_proven_historic_account":False,
    "live_go":False,"main_unmodified":True,
    "warnings":[
      "Zero MEXC funding data were modeled for 2021-25; positive or negative price-only results are not economic after all true costs.",
      "Original strategy signals and trade outcomes previously observed on Binance; this is retrospective source transfer not independently untouched OOS.",
      "Retains original 10bps fee per side and 2/5bps fixed slippage per side as research assumptions, NOT exact historic MEXC account fee or quote fill proof.",
      "MEXC 1h OHLCV data prove candle coverage, not earliest exact bid/ask or depth at each stop or open; true quote-level execution may be worse.",
    ]
  }
  out.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
  print("MEXC_NATIVE_PRICE_TRANSFER_FINAL",json.dumps({
   "status":result["status"],"price_only_per_symbol":results,"price_only_shared":output,
   "warning":"ALL FUNDING EXCLUDED NOT TRUE ECONOMIC NET"
  },sort_keys=True),flush=True)
 except Exception as e:
  out.write_text(json.dumps({"status":"MEXC_NATIVE_PRICE_TRANSFER_SOURCE_OR_TECHNICAL_BLOCKED",
    "reason":repr(e),"economic_credit":"ZERO","live_go":False},indent=2)+"\n")
  traceback.print_exc();sys.exit(2)
if __name__=="__main__":main()

#!/usr/bin/env python3
"""Replay frozen Parent V5 historical 2021-2025 trade ledgers at low risk,
and independently re-mark still-open trades with SHA-matched original Binance 1h OHLCV.
NOT actual MTM including pathwise funding; NOT a new OOS or actual exchange fills.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,math,os,sys,zipfile,urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path

from research.convex_risk_v01.convex_risk_replay_v01 import (
  verify_load,get_raw_trades,events_for,replay,PLANNED_STOP_DRAG,
  MAX_CONCURRENT,MAX_TOTAL_PLANNED_RISK,INITIAL_CAPITAL,RISK_LEVELS
)

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"RAWBAR_MTM_RISK_RECEIPT_V01.json"
SYMS=("ETHUSDT","SOLUSDT","BNBUSDT")
START=int(datetime(2021,1,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2026,1,1,tzinfo=timezone.utc).timestamp()*1000)
HOUR=3600000
EXPECTED=(END-START)//HOUR
USER_AGENT="CryptoLab-RAWBAR-MTM-FROZEN/0.1"

def get_bytes(url, sha):
 if not url.startswith("https://data.binance.vision/data/futures/um/"):
  raise ValueError("INVALID_OR_UNAUTHORIZED_KLINE_URL")
 last=None
 for i in range(2):
  try:
   req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT})
   with urllib.request.urlopen(req,timeout=50) as u:
    data=u.read()
   h=hashlib.sha256(data).hexdigest()
   if h!=sha:raise ValueError("ARCHIVE_SHA256_MISMATCH:"+url+":"+h)
   return data
  except Exception as e:
   last=e
   if isinstance(e,ValueError):break
 raise ValueError("SOURCE_UNAVAILABLE:"+url+":"+str(last))

def from_zip(data,symbol):
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  files=[x for x in z.namelist() if x.lower().endswith(".csv")]
  if len(files)!=1:raise ValueError("ZIP_MEMBER_INVALID:"+symbol)
  data=z.read(files[0]).decode("utf-8-sig")
 result={}
 for row in csv.reader(io.StringIO(data)):
  if not row:continue
  try:t=int(row[0])
  except ValueError:continue
  if t>10**14:t//=1000
  if not START<=t<END:continue
  if len(row)<6:raise ValueError("KLINE_SCHEMA_SHORT")
  vals=(float(row[1]),float(row[2]),float(row[3]),float(row[4]))
  if not all(math.isfinite(x) and x>0 for x in vals):raise ValueError("KLINE_NONFINITE")
  op,hi,lo,cl=vals
  if lo>min(op,cl)+1e-8 or hi<max(op,cl)-1e-8:raise ValueError("OHLC_SHAPE")
  if t in result and result[t]!=vals:raise ValueError("CONFLICTING_ARCHIVE_BAR")
  result[t]=vals
 return result

def recover_bars(first):
 tasks=[];pairs=set()
 for s in SYMS:
  prov=first["symbols"][s]["provenance"]
  if int(prov["bar_count_economic"])!=EXPECTED:raise ValueError("ORIGINAL_BAR_COUNT_MISMATCH:"+s)
  for m in prov["manifest_entries"]:
   kind=m.get("kind")
   if kind=="kline" and "2021-01"<=m.get("month","")<="2025-12":
    pass
   elif kind=="kline_daily_gapfill":
    pass
   else:continue
   url=m["url"];sha=m["sha256"]
   key=(s,url)
   if key in pairs:raise ValueError("DUPLICATE_KLINE_ARCHIVE_REFERENCE")
   pairs.add(key);tasks.append((s,url,sha,kind))
 monthly={s:0 for s in SYMS};daily={s:0 for s in SYMS}
 for s,url,_,kind in tasks:
  if kind=="kline":monthly[s]+=1
  else:daily[s]+=1
 for s in SYMS:
  if monthly[s]!=60:raise ValueError(f"INCOMPLETE_MONTHLY_KLINE_MANIFEST:{s}:{monthly[s]}")
 # Compare raw archive hashes to immutable original manifest before loading prices.
 values={s:{} for s in SYMS}
 total_archives=0;total_bytes=0
 with ThreadPoolExecutor(max_workers=6) as pool:
  futures={pool.submit(get_bytes,url,sha):(s,url,kind) for s,url,sha,kind in tasks}
  for f in as_completed(futures):
   s,url,kind=futures[f];blob=f.result();parsed=from_zip(blob,s)
   total_archives+=1;total_bytes+=len(blob)
   for t,row in parsed.items():
    if t in values[s] and values[s][t]!=row:
     raise ValueError("CONFLICTING_MONTHLY_DAILY_PRICE:"+s+":"+str(t))
    values[s][t]=row
 for s,rows in values.items():
  if len(rows)!=EXPECTED:raise ValueError(f"KLINE_CONTIGUITY_FAIL:{s}:{len(rows)}/{EXPECTED}")
  for idx,t in enumerate(sorted(rows)):
   if t!=START+idx*HOUR:raise ValueError(f"HOURLY_GAP:{s}:{t}")
 return values,{"archives_sha_checked":total_archives,"compressed_bytes_sha_checked":total_bytes,
                "original_monthly_archive_count":monthly,"daily_gapfill_archive_count":daily,
                "observed_hours":{s:len(rows) for s,rows in values.items()}}

def check_raw_fills(bars,base,stress):
 audit={}
 for symbol in SYMS:
  audit[symbol]={}
  for layer,trades in (("BASE",base[symbol]),("STRESS",stress[symbol])):
   slip=.0002 if layer=="BASE" else .0005
   count={"STOP":0,"FORCED_END":0}
   max_entry_error_bps=0.0
   max_exit_candle_error_bps=0.0
   for t in trades:
    entry=int(t["entry_t"]);end=int(t["exit_t"])
    if entry not in bars[symbol] or end not in bars[symbol]:
     raise ValueError("ENTRY_OR_EXIT_SOURCE_BAR_MISSING:"+symbol)
    start_ohlc=bars[symbol][entry];exit_ohlc=bars[symbol][end]
    actual_entry=float(t["entry"])
    theoretical_entry=start_ohlc[0]*(1+slip)
    d=abs(actual_entry/theoretical_entry-1)*10000
    max_entry_error_bps=max(max_entry_error_bps,d)
    if d>0.00001:raise ValueError("ORIGINAL_ENTRY_OPEN_PRICE_MISMATCH:"+symbol)
    reason=t.get("reason")
    if reason not in count:raise ValueError("UNKNOWN_EXIT_REASON:"+str(reason))
    count[reason]+=1
    exec_exit=float(t["exit"])
    raw_exit=exec_exit/(1-slip)
    lo,hi=exit_ohlc[2],exit_ohlc[1]
    if reason=="FORCED_END":
     d=abs(raw_exit/exit_ohlc[3]-1)*10000
     max_exit_candle_error_bps=max(max_exit_candle_error_bps,d)
     if d>0.00001:raise ValueError("FORCED_EXIT_ORIGINAL_CLOSE_MISMATCH")
    else:
     # Existing original trailing/stop fill, after reversing frozen slippage,
     # must be within same verified hourly candle high-low envelope.
     d=max(0.0,lo-raw_exit,raw_exit-hi)/max(1.0,abs(raw_exit))*10000
     max_exit_candle_error_bps=max(max_exit_candle_error_bps,d)
     if d>0.00001:raise ValueError("ORIGINAL_STOP_OUTSIDE_HOURLY_CANDLE:"+symbol)
   audit[symbol][layer]={
    "trades_matched":len(trades),
    "stop_count":count["STOP"],
    "forced_close_count":count["FORCED_END"],
    "max_entry_price_error_bps":round(max_entry_error_bps,10),
    "max_exit_hilo_or_close_violation_bps":round(max_exit_candle_error_bps,10),
    "verdict":"BAR_CANDLE_COHERENCE_PASS_NOT_EXCHANGE_EXECUTION"
   }
 return audit

def audit_loss_overshoot(base,stress):
 d={}
 for s in SYMS:
  d[s]={}
  for label,rows in (("BASE",base[s]),("STRESS",stress[s])):
   bad=[r for r in rows if float(r["return_pct"])/100 < -PLANNED_STOP_DRAG]
   worst=min(float(r["return_pct"])/100 for r in rows)
   same=sum(int(r["entry_t"])==int(r["exit_t"]) for r in rows)
   d[s][label]={
    "trades":len(rows),"net_losses_beyond_planned_4p24pct_notional":len(bad),
    "fraction_beyond_planned_pct":round(100*len(bad)/len(rows),4),
    "worst_net_trade_notional_pct":round(100*worst,6),
    "worst_loss_over_planned_R":round(abs(min(worst,0))/PLANNED_STOP_DRAG,6),
    "same_one_hour_bar_entry_exit":same
   }
 return d

def replay_marks(values,base,stress,risk,label):
 trades=base if label=="BASE" else stress
 slip_exit=.0002 if label=="BASE" else .0005
 events=events_for(SYMS,base,trades,0,False)
 expected=replay(events,risk)
 eventmap=defaultdict(list)
 for row in events:
  eventmap[int(row[0])].append(row)
 equity=INITIAL_CAPITAL
 openpos={};reserved=0.0;skips=0;take=0
 observed_peak=INITIAL_CAPITAL;min_marked_dd=0.0
 worst_hourly_low_dd=0.0
 min_hourly_close=None;peak_observed_close=INITIAL_CAPITAL
 sampled=0;low_optimism_gap=0.0
 max_daily_open=0;count_open_hours=0
 worst_unrealized_individual=0.0
 year_min_close_dd={str(i):0.0 for i in range(2021,2026)}
 year_min_low_dd={str(i):0.0 for i in range(2021,2026)}
 for h in range(EXPECTED):
  t=START+h*HOUR
  for row in eventmap.get(t,()):
   _,etype,s,ident,runit=row
   if etype!=1:
    if ident not in openpos:continue
    p=openpos.pop(ident)
    reserved-=p["reserved"]
    equity+=p["notional"]*runit
    if equity<=0:raise ValueError("NONPOSITIVE_EQUITY")
    take+=1
   else:
    notional=min(equity*risk/PLANNED_STOP_DRAG,equity*.95)
    planned=notional*PLANNED_STOP_DRAG
    if len(openpos)>=MAX_CONCURRENT or reserved+planned>equity*MAX_TOTAL_PLANNED_RISK+1e-8:
     skips+=1;continue
    source=trades[s][ident[3]]
    if int(source["entry_t"])!=ident[1] or int(source["exit_t"])!=ident[2]:
     raise ValueError("TRADE_RECORD_MISMATCH")
    openpos[ident]={"notional":notional,"reserved":planned,"entry":float(source["entry"]),"symbol":s}
    reserved+=planned
  marked=equity;low_marked=equity
  for p in openpos.values():
   symbol=p["symbol"];entry=p["entry"]
   price=values[symbol][t];close=price[3];lo=price[2]
   # Original trade's executed entry already incorporates the input slippage.
   # Estimate liquidation price as close/low with original entry commission and
   # projected taker exit commission/slip; interim historical funding not reconstructed.
   estimated_cost=.001+.001+slip_exit
   marked+=p["notional"]*((close/entry-1)-estimated_cost)
   low_marked+=p["notional"]*((lo/entry-1)-estimated_cost)
   worst_unrealized_individual=min(worst_unrealized_individual,
                                   (lo/entry-1)-estimated_cost)
  if not math.isfinite(marked) or not math.isfinite(low_marked):
   raise ValueError("NONFINITE_EQUITY_MTM")
  if marked<=0 or low_marked<=0:
   raise ValueError("MODELED_MTM_EQUITY_DEPLETED")
  observed_peak=max(observed_peak,marked)
  min_marked_dd=min(min_marked_dd,marked/observed_peak-1)
  worst_hourly_low_dd=min(worst_hourly_low_dd,low_marked/observed_peak-1)
  yy=str(datetime.fromtimestamp(t/1000,timezone.utc).year)
  year_min_close_dd[yy]=min(year_min_close_dd[yy],marked/observed_peak-1)
  year_min_low_dd[yy]=min(year_min_low_dd[yy],low_marked/observed_peak-1)
  low_optimism_gap=max(low_optimism_gap,(marked-low_marked)/observed_peak)
  if openpos:count_open_hours+=1
  max_daily_open=max(max_daily_open,len(openpos))
  sampled+=1
 if openpos:raise ValueError("OPEN_AT_FINAL_BAR")
 if (take!=expected["trades"] or skips!=expected["skipped_concurrent_or_budget"]
     or not math.isclose(equity,expected["end_capital_usdt"],rel_tol=0,abs_tol=.000002)):
  raise ValueError("REPLAY_NOT_IDENTICAL_TO_FROZEN_RISK_V01")
 return {
    "trades_reproduced":take,"blocked_entries_reproduced":skips,
    "net_return_pct_reproduced":expected["net_return_pct"],
    "realized_only_dd_pct_from_prior":expected["realized_only_dd_pct"],
    "indicative_hourly_close_mtm_dd_pct":round(100*min_marked_dd,6),
    "same_hour_low_envelope_pessimistic_pct":round(100*worst_hourly_low_dd,6),
    "max_low_close_gap_as_pct_historical_peak":round(100*low_optimism_gap,6),
    "worst_open_trade_low_mark_net_pct_of_notional":round(100*worst_unrealized_individual,6),
    "hourly_observations":sampled,"hours_with_open_position":count_open_hours,
    "max_concurrent_open":max_daily_open,
    "indicative_mtm_understates_funding_and_intrabar_fill_risks":True,
    "year_min_dd_close_pct_of_global_running_peak":{k:round(100*v,6) for k,v in year_min_close_dd.items()},
    "year_min_low_envelope_pct":{k:round(100*v,6) for k,v in year_min_low_dd.items()}
 }

def self_test():
 import math
 assert EXPECTED==43824
 assert math.isclose(PLANNED_STOP_DRAG,.0424,abs_tol=1e-12)
 assert 1+0.01 < 1+0.02
 sample="""1640995200000,100,103,99,101,2\n1640998800000,101,105,100,104,3\n"""
 zipped=io.BytesIO()
 with zipfile.ZipFile(zipped,"w") as z:z.writestr("sample.csv",sample)
 assert len(from_zip(zipped.getvalue(),"TEST"))==2
 print("SELFTEST_PASS")

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--archive-root")
 p.add_argument("--self-test",action="store_true")
 a=p.parse_args()
 if a.self_test:
  # Synthetic 2022 bar parse and fixed 2021..25 bounds.
  assert EXPECTED==43824
  assert math.isclose(PLANNED_STOP_DRAG,.0424,abs_tol=1e-12)
  sample="""1640995200000,100,103,99,101,2\n1640998800000,101,105,100,104,3\n"""
  z=io.BytesIO()
  with zipfile.ZipFile(z,"w") as f:f.writestr("example.csv",sample)
  assert len(from_zip(z.getvalue(),"TEST"))==2
  assert 1640995200000 in from_zip(z.getvalue(),"TEST")
  print("RAWBAR_MTM_SYNTHETIC_PASS: 3")
  return
 if not a.archive_root:raise SystemExit("ARCHIVE_ROOT_REQUIRED")
 try:
  original,source_hash=verify_load(a.archive_root)
  base,stress,provenance=get_raw_trades(original)
  candles,source_check=recover_bars(original["FIRST"])
  data={"status":"RAW_1H_PROVENANCE_PASS__MARKED_RISK_ESTIMATE_ONLY",
    "canonical_historical_sources_sha256":source_hash,
    "risk_v01_original_artifact":11600701586,
    "raw_archive_check":source_check,
    "losses_beyond_planned_stop_risk":audit_loss_overshoot(base,stress),
    "raw_entry_exit_candle_integrity":check_raw_fills(candles,base,stress),
    "no_new_historical_oos":True,"execution_market_quote_or_order_proven":False,
    "run_commit":os.environ.get("GITHUB_SHA","LOCAL"),"scenarios":{}}
  for level in RISK_LEVELS:
   k=f"{100*level:.2f}pct";data["scenarios"][k]={}
   for label in ("BASE","STRESS"):
    data["scenarios"][k][label]=replay_marks(candles,base,stress,level,label)
  OUT.write_text(json.dumps(data,sort_keys=True,indent=2)+"\n")
  print("RAWBAR_SHA256_PROVENANCE_VERIFIED",json.dumps(source_check))
  for k,v in data["scenarios"].items():
   for label,m in v.items():
    print("RISK_MTM_RESULT",json.dumps({"risk":k,"layer":label,**m},sort_keys=True))
  print("STOP_OVERSHOOT",json.dumps(data["losses_beyond_planned_stop_risk"],sort_keys=True))
  print("RAWBAR_ENTRY_EXIT_INTEGRITY",json.dumps(data["raw_entry_exit_candle_integrity"],sort_keys=True))
  print("RAWBAR_MTM_FINAL_STATUS",data["status"])
 except Exception as e:
  OUT.write_text(json.dumps({"status":"SOURCE_OR_MTM_BLOCKED",
     "error":str(e),"scientific_credit":"NONE","no_live_trading_authority":True},indent=2))
  print("RAWBAR_MTM_FAIL_CLOSED",repr(e),file=sys.stderr)
  raise

if __name__=="__main__":main()

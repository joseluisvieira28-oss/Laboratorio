#!/usr/bin/env python3
"""Binance official 1m stop first-touch source and gap diagnostic.
Runs ONLY against original previously-opened canonical Parent V5 histories.
Quotes, spread, true execution and MEXC transfer are NOT established by this study.
"""
from __future__ import annotations
import argparse, csv, hashlib, io, json, math, sys, traceback, urllib.request, urllib.error, zipfile, time, copy, runpy
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
from pathlib import Path

HERE=Path(__file__).resolve().parent
SYMBOLS=("ETHUSDT","SOLUSDT","BNBUSDT")
LAYERS={"BASE":.0002,"STRESS":.0005}
EXPECTED={"BASE":{"0.0025":34.59609,"0.005":20.080257},
          "STRESS":{"0.0025":33.684714,"0.005":16.949956}}
HOUR=3600000;MIN=60000
EXIT_END=int(datetime(2025,12,31,23,tzinfo=timezone.utc).timestamp()*1000)
WINDOW=["2021-01-01T00:00:00Z","2025-12-31T23:00:00Z"]
SOURCE_BASE="https://data.binance.vision/data/futures/um"
RISK_SCRIPT=HERE.parent/"convex_risk_v01"/"convex_risk_replay_v01.py"

def finite(v):
    n=float(v)
    if not math.isfinite(n) or n<=0:raise ValueError("INVALID_MARKET_PRICE")
    return n

def one_archive(root):
    f=list(Path(root).rglob("CROSS_ASSET_COST_VALIDATION_V0.1.json"))
    if len(f)!=1:raise ValueError("ORIGINAL_CANONICAL_ARTIFACT_MISSING_OR_DUPLICATE")
    blob=f[0].read_bytes();doc=json.loads(blob)
    if doc.get("period")!=WINDOW or set(doc.get("symbols",{}))!=set(SYMBOLS):
        raise ValueError("ORIGINAL_ARCHIVE_BOUNDARY_OR_UNIVERSE_WRONG")
    return doc,hashlib.sha256(blob).hexdigest()

def dataset_work(doc):
    want=defaultdict(set); originals={};covered={"BASE":0,"STRESS":0}
    for layer in LAYERS:
      originals[layer]={}
      for symbol in SYMBOLS:
        tr=doc["symbols"][symbol]["results"]["PARENT"][layer]["trades"]
        originals[layer][symbol]=tr
        for trade in tr:
          if trade["reason"] not in ("STOP","FORCED_END"):
             raise ValueError("UNKNOWN_ORIGINAL_EXIT_TYPE")
          end=int(trade["exit_t"])
          dt=datetime.fromtimestamp(end/1000,timezone.utc)
          want[(symbol,dt.strftime("%Y-%m"))].add(end)
          covered[layer]+=1
    return want,originals,covered

def fetch(url,optional=False):
    for retry in range(4):
      try:
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-1MinuteStopSourceGate/1.0"})
        with urllib.request.urlopen(req,timeout=70) as h:
          return h.read()
      except urllib.error.HTTPError as e:
        if e.code==404:return None
        if optional and e.code in (403,404):return None
        if retry==3:raise
      except (TimeoutError,ConnectionError,OSError):
        if retry==3:raise
      time.sleep((retry+1)*1.5)
    return None

def parse_1m_zip(data,wanted_hours,src):
    rows=defaultdict(dict)
    if not data:return rows
    with zipfile.ZipFile(io.BytesIO(data)) as z:
      if len(z.namelist())!=1:raise ValueError("NON_UNIQUE_ZIP_MEMBER:"+src)
      rd=csv.reader(io.StringIO(z.read(z.namelist()[0]).decode("utf-8-sig")))
      for q in rd:
        if not q:continue
        try:t=int(q[0])
        except (ValueError,IndexError):continue
        if t>10**14:t//=1000
        ht=(t//HOUR)*HOUR
        if ht not in wanted_hours:continue
        if t % MIN !=0:raise ValueError(f"NON_MINUTE_TIMESTAMPS:{src}:{t}")
        o,h,l,c=tuple(finite(q[i]) for i in range(1,5))
        if not (l<=min(o,c)<=max(o,c)<=h):raise ValueError("INVALID_1M_CANDLE_OHLC")
        if t in rows[ht] and rows[ht][t]!=(o,h,l,c):
          raise ValueError("1M_DUPLICATE_CONFLICT:"+src)
        rows[ht][t]=(o,h,l,c)
    return rows

def add_missing(rows,wanted_hours,symbol,notes):
    # Pre-frozen exact daily 1m source fallback ONLY for hours with missing minutes.
    missing={h for h in wanted_hours if len(rows.get(h,{}))<60}
    by_day=defaultdict(set)
    for h in missing:
        by_day[datetime.fromtimestamp(h/1000,timezone.utc).strftime("%Y-%m-%d")].add(h)
    for day,hours in by_day.items():
        url=f"{SOURCE_BASE}/daily/klines/{symbol}/1m/{symbol}-1m-{day}.zip"
        body=fetch(url)
        if body is None:
          notes.append({"daily":day,"status":"SOURCE_MISSING","url":url})
          continue
        notes.append({"daily":day,"status":"SOURCE_OK","url":url,"sha256":hashlib.sha256(body).hexdigest()})
        found=parse_1m_zip(body,hours,url)
        for h,v in found.items():
            for t,c in v.items():
                if t in rows[h] and rows[h][t]!=c:
                    raise ValueError(f"MONTHLY_DAILY_CANDLE_CONFLICT:{symbol}:{t}")
                rows[h][t]=c

def download_month(k,hours):
    sym,ym=k
    url=f"{SOURCE_BASE}/monthly/klines/{sym}/1m/{sym}-1m-{ym}.zip"
    info={"symbol":sym,"month":ym,"monthly_url":url,"request_hours":len(hours),"daily_fallbacks":[]}
    try:
      body=fetch(url)
      if body is None:
          info["monthly_status"]="NOT_FOUND"
          rows=defaultdict(dict)
      else:
          info["monthly_status"]="OK"
          info["monthly_sha256"]=hashlib.sha256(body).hexdigest()
          # Official companion SHA when supplied; optional source integrity strengthening.
          chk=fetch(url+".CHECKSUM",optional=True)
          if chk:
            tokens=chk.decode(errors="replace").strip().split()
            if tokens and len(tokens[0])==64:
                if tokens[0].lower()!=info["monthly_sha256"].lower():
                    raise ValueError(f"OFFICIAL_COMPANION_SHA_MISMATCH:{sym}:{ym}")
                info["companion_checksum"]="PASS"
            else:info["companion_checksum"]="UNRECOGNIZED"
          else:info["companion_checksum"]="UNAVAILABLE"
          rows=parse_1m_zip(body,hours,url)
      add_missing(rows,hours,sym,info["daily_fallbacks"])
      info["covered_hours"]=sum(len(rows.get(h,{}))==60 for h in hours)
      info["missing_hours"]=sum(len(rows.get(h,{}))!=60 for h in hours)
      print("OFFICIAL_1M_MONTH",sym,ym,"complete_hours",info["covered_hours"],"asked",len(hours),flush=True)
      return k,rows,info,None
    except Exception as e:
      info["status"]="SOURCE_BLOCKED"
      info["reason"]=repr(e)
      return k,{},info,str(e)

def first_touch(layer,trade,rows):
    exit_t=int(trade["exit_t"])
    if len(rows)!=60:return {"status":"BLOCKED_1M_COVERAGE","extra_gap_bps":None}
    sequence=[]
    for k in range(60):
      t=exit_t+k*MIN
      if t not in rows:
        return {"status":"BLOCKED_1M_SEQUENCE","extra_gap_bps":None,"missing_t":t}
      sequence.append((t,rows[t]))
    slip=LAYERS[layer]
    target=finite(trade["exit"])/(1-slip)
    entry=finite(trade["entry"])
    if trade["reason"]=="FORCED_END":
      close1m=sequence[-1][1][3]
      gap=abs(target-close1m)
      if gap>max(1e-8,1e-7*target):
        return {"status":"BLOCKED_END_CLOSE_MISMATCH","extra_gap_bps":None,
                "delta":gap}
      return {"status":"FORCED_END_CLOSE_CONFIRMED","extra_gap_bps":0.}
    for minute_t,(o,h,l,c) in sequence:
      if o<=target*(1+1e-10) or l<=target*(1+1e-10):
        extra=max(0.,target-o)/entry*10000.
        return {"status":"STOP_MINUTE_TOUCH_CONFIRMED","extra_gap_bps":extra,
          "minute_t":minute_t,"entry_ref":entry,"stop_ref":target,
          "first_cross_minute_open":o,
          "first_touch_minute_from_hour":(minute_t-exit_t)//MIN}
    return {"status":"BLOCKED_NO_1M_STOP_CROSSING","extra_gap_bps":None,
        "exit_ref":target,"hour_min":min(v[1][2] for v in sequence)}

def cost_scenario(original,by_trade):
    # Reuse exact fixed previous risk engine; adjust ONLY existing original STOP return%.
    ns=runpy.run_path(str(RISK_SCRIPT),run_name="minute_gap_reference")
    events_for=ns["events_for"];replay=ns["replay"]
    results={}
    for layer in LAYERS:
      cloned=copy.deepcopy(original[layer])
      for sym,tr in enumerate(SYMBOLS):
        for i,trade in enumerate(cloned[tr]):
          rec=by_trade[(layer,tr,i)]
          if not rec["status"] in ("STOP_MINUTE_TOUCH_CONFIRMED","FORCED_END_CLOSE_CONFIRMED"):
            raise ValueError("INCOMPLETE_GAP_IMPUTATION_FORBIDDEN")
          trade["return_pct"]-=rec["extra_gap_bps"]/100.
      results[layer]={}
      for risk in (.0025,.005):
        orig_events=events_for(SYMBOLS,original["BASE"],original[layer],0,False)
        edited_events=events_for(SYMBOLS,original["BASE"],cloned,0,False)
        baseline=replay(orig_events,risk)
        amended=replay(edited_events,risk)
        key=str(risk)
        if abs(baseline["net_return_pct"]-EXPECTED[layer][key])>.005:
          raise ValueError("BASELINE_COUNTERFACTUAL_DRIFT:"+layer+":"+key)
        results[layer][key]={
          "baseline_return_pct":baseline["net_return_pct"],
          "after_minute_open_gap_stress_return_pct":amended["net_return_pct"],
          "change_percentage_points":round(amended["net_return_pct"]-baseline["net_return_pct"],6),
          "closed_trades":amended["trades"],
          "skipped_original_signals":amended["skipped_concurrent_or_budget"],
          "note":"Assumes minute observed OPEN as adverse if below original stop; not actual quote order fill"
        }
    return results

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original-archive",required=True)
    args=p.parse_args()
    output=HERE/"ONE_MINUTE_STOP_GAP_RESULT_2026_10_09.json"
    try:
      doc,sha=one_archive(args.original_archive)
      wanted,original,expected=dataset_work(doc)
      keyed={}
      with ThreadPoolExecutor(max_workers=5) as pool:
        futures={pool.submit(download_month,k,h):k for k,h in wanted.items()}
        for fu in as_completed(futures):
          k,rows,info,error=fu.result()
          keyed[k]=(rows,info,error)
      notes=[keyed[k][1] for k in sorted(keyed)]
      by_trade={}
      counts=defaultdict(int);problems=[];penalties=defaultdict(list)
      for layer in LAYERS:
       for sym in SYMBOLS:
        for i,tr in enumerate(original[layer][sym]):
          m=datetime.fromtimestamp(int(tr["exit_t"])/1000,timezone.utc).strftime("%Y-%m")
          month_hour_rows=keyed[(sym,m)][0].get(int(tr["exit_t"]),{})
          rec=first_touch(layer,tr,month_hour_rows)
          by_trade[(layer,sym,i)]=rec
          counts[layer+":"+rec["status"]]+=1
          if rec["status"].startswith("BLOCKED"):
            problems.append({"symbol":sym,"layer":layer,"trade_index":i,
                    "exit_t":tr["exit_t"],"failure":rec})
          else:penalties[layer].append(rec["extra_gap_bps"])
      all_ok=len(problems)==0
      result={
         "status":"FULL_1M_STOP_SOURCE_GATE_PASS" if all_ok else "PARTIAL_1M_STOP_SOURCE_GATE__FAIL_CLOSED_ECONOMIC",
         "scientific_credit":"DIAGNOSTIC_ONLY_PREVIOUSLY_OPENED_OOS",
         "orig_canonical_artifact_id":10775714534,
         "original_json_sha256":sha,
         "original_2021_2025_only":True,
         "frozen_months_requested":len(wanted),
         "original_trade_counts":expected,
         "source_month_receipts":notes,
         "stop_verification_counts":dict(counts),
         "blocked_event_count":len(problems),"blocked_event_details":problems[:120],
         "minute_open_gap_summary":{
          l:{"max_extra_gap_bps":round(max(penalties[l]),6) if penalties[l] else None,
             "positive_extra_gap_events":sum(x>0 for x in penalties[l]),
             "sum_extra_gap_bps_across_events":round(sum(penalties[l]),6)}
          for l in LAYERS},
         "live_go":False,
         "not_proven":"Point-in-time MEXC bid-ask/size, order fill, tick ordering within minute and stop execution latency"
      }
      if all_ok:
        result["frozen_shared_risk_1m_gap_sensitivity"]=cost_scenario(original,by_trade)
      else:
        result["frozen_shared_risk_1m_gap_sensitivity"]="NOT_COMPUTED_BROKEN_MINUTE_COVERAGE"
      output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
      print("ONE_MINUTE_STOP_GATE_FINAL",json.dumps({
       "status":result["status"],"counts":result["stop_verification_counts"],
       "gap":result["minute_open_gap_summary"],
       "risk":result["frozen_shared_risk_1m_gap_sensitivity"]},sort_keys=True),flush=True)
      if not all_ok:sys.exit(2)
    except Exception as e:
      traceback.print_exc()
      fail={"status":"SOURCE_OR_TECHNICAL_BLOCKED","reason":repr(e),"live_go":False}
      output.write_text(json.dumps(fail,indent=2)+"\n")
      print("ONE_MINUTE_STOP_GATE_FINAL",fail["status"],str(e),flush=True)
      sys.exit(2)

if __name__=="__main__":main()

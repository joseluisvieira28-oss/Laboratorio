#!/usr/bin/env python3
"""Nasdaq earnings calendar fallback source gate. No strategy outcomes."""
from __future__ import annotations
import csv, io, json, time, zipfile, hashlib
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
BASE_BIND=json.loads((HERE/"MEXC_GLOBALASSET_CASHOPEN_SOURCE_BINDING_V0.7.json").read_text())
OUT=Path("artifacts/mexc_global_assets/earnings_shock_v201_source")
START=date(2026,7,1); END=date(2026,8,31)
HEADERS={
 "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139 Safari/537.36",
 "Accept":"application/json, text/plain, */*",
 "Accept-Language":"en-US,en;q=0.9",
 "Referer":"https://www.nasdaq.com/market-activity/earnings"
}

def H(b):return hashlib.sha256(b).hexdigest()
def sec(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def next_weekday(d):
 d=d+timedelta(days=1)
 while d.weekday()>=5:d+=timedelta(days=1)
 return d
def get(url,params=None,timeout=60,retries=4):
 last=None
 for i in range(retries):
  try:
   r=requests.get(url,params=params,headers=HEADERS,timeout=timeout)
   if r.status_code!=200:raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
   return r
  except Exception as e:last=e;time.sleep(.7*(i+1))
 raise last

def market_transport(target,ext,d):
 ds=d.isoformat();a=sec(ds+"T12:20:00Z");b=sec(ds+"T13:40:00Z")
 mr=get(f"https://api.mexc.com/api/v1/contract/kline/{target}",{"interval":"Min1","start":str(a),"end":str(b)})
 try:mc=len((mr.json().get("data") or {}).get("time") or [])
 except:mc=0
 br=get(f"https://data.binance.vision/data/futures/um/daily/klines/{ext}/1m/{ext}-1m-{ds}.zip",timeout=90)
 bc=0
 try:
  z=zipfile.ZipFile(io.BytesIO(br.content));names=z.namelist()
  if len(names)==1:
   for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
    try:t=int(row[0])//1000;float(row[4])
    except:continue
    if a<=t<=b:bc+=1
 except:pass
 gr=get("https://api.bitget.com/api/v2/mix/market/history-candles",{
  "symbol":ext,"productType":"USDT-FUTURES","granularity":"1m",
  "startTime":str(a*1000),"endTime":str(b*1000),"limit":"100"})
 try:gc=len(gr.json().get("data") or [])
 except:gc=0
 return {"mexc_rows":mc,"binance_rows":bc,"bitget_rows":gc,
  "mexc_sha256":H(mr.content),"binance_sha256":H(br.content),"bitget_sha256":H(gr.content),
  "source_pass":mc>=75 and bc>=75 and gc>=75}

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 mapping={}
 for c in BASE_BIND["candidates"]:
  ext=c["external_binance"];root=ext[:-4] if ext.endswith("USDT") else ext
  mapping[root.upper()]={"target":c["target"],"external":ext}
 raw_days=[];events=[]
 d=START
 while d<=END:
  if d.weekday()<5:
   try:
    r=get("https://api.nasdaq.com/api/calendar/earnings",{"date":d.isoformat()})
    j=r.json();rows=((j.get("data") or {}).get("rows") or [])
    raw_days.append({"date":d.isoformat(),"http":r.status_code,"rows":len(rows),"sha256":H(r.content)})
    for row in rows:
     sym=str(row.get("symbol") or "").upper().strip()
     if sym not in mapping:continue
     timing=str(row.get("time") or row.get("timeOfDay") or "").lower()
     if "after" in timing:
      session=next_weekday(d);timing_class="AFTER_HOURS"
     elif "pre" in timing:
      session=d;timing_class="PRE_MARKET"
     else:
      continue
     if session<START or session>END or session.weekday()>=5:continue
     events.append({"calendar_date":d.isoformat(),"event_session":session.isoformat(),
      "timing_raw":row.get("time") or row.get("timeOfDay"),"timing_class":timing_class,
      "ticker":sym,"target":mapping[sym]["target"],"external":mapping[sym]["external"],
      "fiscal_quarter_ending":row.get("fiscalQuarterEnding"),"eps_forecast":row.get("epsForecast")})
   except Exception as e:
    raw_days.append({"date":d.isoformat(),"error":repr(e)})
   time.sleep(.08)
  d+=timedelta(days=1)

 seen=set();uniq=[]
 for e in sorted(events,key=lambda x:(x["event_session"],x["ticker"],x["calendar_date"])):
  k=(e["ticker"],e["event_session"])
  if k in seen:continue
  seen.add(k);uniq.append(e)
 events=uniq
 for e in events:
  try:e["market_source"]=market_transport(e["target"],e["external"],date.fromisoformat(e["event_session"]))
  except Exception as ex:e["market_source"]={"source_pass":False,"error":repr(ex)}
  print(e["event_session"],e["ticker"],e["timing_class"],e["market_source"].get("source_pass"))
  time.sleep(.04)
 passed=[e for e in events if e["market_source"].get("source_pass")]
 rep={"gate_id":"MEXC_EARNINGS_SHOCK_SOURCE_V2_0_1","source_only":True,
  "event_authority":"Nasdaq Earnings Calendar public endpoint; explicit pre-market/after-hours timing only",
  "event_window":["2026-07-01","2026-08-31"],"calendar_day_receipts":raw_days,
  "eligible_event_count":len(events),"full_transport_event_count":len(passed),"events":events,
  "verdict":"EARNINGS_SHOCK_SOURCE_PASS" if len(passed)>=8 else ("EARNINGS_SHOCK_SOURCE_UNDERPOWERED" if passed else "EARNINGS_SHOCK_SOURCE_BLOCKED"),
  "outcomes_opened":0,"private_endpoints_used":False,"account_reads":False,"orders":False,"wallets":False,"live_trading":False}
 (OUT/"MEXC_EARNINGS_SHOCK_SOURCE_V201.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
 print(json.dumps({"verdict":rep["verdict"],"eligible_event_count":len(events),"full_transport_event_count":len(passed),
 "passed":[{"session":e["event_session"],"ticker":e["ticker"],"timing":e["timing_class"]} for e in passed]},indent=2))
if __name__=="__main__":main()

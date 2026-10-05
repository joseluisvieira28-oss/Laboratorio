#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,time,zipfile,hashlib
from datetime import datetime
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
B=json.loads((HERE/"MEXC_GLOBALASSET_TRANSFER_SOURCE_BINDING_V0.5.json").read_text())
OUT=Path("artifacts/mexc_global_assets/cashopen_v06_source")
DAY="2026-09-30"; UA="CryptoLab-CashOpen-Source/0.6"
def H(b):return hashlib.sha256(b).hexdigest()
def ts(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def req(url,params=None,timeout=60):
 for i in range(4):
  try:return requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
  except Exception:
   time.sleep(.5*(i+1))
 raise RuntimeError(url)
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 start=ts(DAY+"T13:20:00Z"); end=ts(DAY+"T14:05:00Z")
 rows=[]
 for c in B["candidates"]:
  target=c["target"]; ext=c["external_binance"]
  rec={"target":target,"external":ext,"outcomes_opened":0}
  mr=req(f"https://api.mexc.com/api/v1/contract/kline/{target}",{"interval":"Min1","start":str(start),"end":str(end)})
  mc=0
  if mr.status_code==200:
   try:
    j=mr.json();d=j.get("data") or {};mc=len(d.get("time") or [])
   except:pass
  rec["mexc"]={"http":mr.status_code,"rows":mc,"ok":mc>=40,"sha256":H(mr.content)}
  br=req(f"https://data.binance.vision/data/futures/um/daily/klines/{ext}/1m/{ext}-1m-{DAY}.zip",timeout=90)
  bc=0
  if br.status_code==200:
   try:
    z=zipfile.ZipFile(io.BytesIO(br.content)); names=z.namelist()
    if len(names)==1:
     for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
      try:t=int(row[0])//1000; float(row[4])
      except:continue
      if start<=t<=end:bc+=1
   except:pass
  rec["binance"]={"http":br.status_code,"rows":bc,"ok":bc>=40,"sha256":H(br.content) if br.status_code==200 else None}
  gr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":ext,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(start*1000),"endTime":str(end*1000),"limit":"100"})
  gc=0
  if gr.status_code==200:
   try:gc=len((gr.json().get("data") or []))
   except:pass
  rec["bitget"]={"http":gr.status_code,"rows":gc,"ok":gc>=40,"sha256":H(gr.content)}
  rec["source_pass"]=rec["mexc"]["ok"] and rec["binance"]["ok"] and rec["bitget"]["ok"]
  rows.append(rec);print(target,rec["source_pass"],mc,bc,gc);time.sleep(.02)
 passed=[{"target":x["target"],"external":x["external"]} for x in rows if x["source_pass"]]
 rep={"gate_id":"MEXC_GLOBALASSET_CASHOPEN_SOURCE_V0_6","source_only":True,"verification_date":DAY,
 "window_utc":["13:20","14:05"],"results":rows,"source_pass":passed,"source_pass_count":len(passed),
 "verdict":"CASHOPEN_SOURCE_PASS_CANDIDATES_FOUND" if passed else "CASHOPEN_SOURCE_BLOCKED",
 "private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading_authorized":False}
 (OUT/"MEXC_GLOBALASSET_CASHOPEN_SOURCE_V06.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
 print(json.dumps({"verdict":rep["verdict"],"source_pass_count":len(passed),"source_pass":passed},indent=2))
if __name__=="__main__":main()

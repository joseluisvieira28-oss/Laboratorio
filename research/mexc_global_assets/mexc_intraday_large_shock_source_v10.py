#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,time,zipfile,hashlib
from datetime import datetime
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
B=json.loads((HERE/"MEXC_GLOBALASSET_TRANSFER_SOURCE_BINDING_V0.5.json").read_text())
OUT=Path("artifacts/mexc_global_assets/intraday_large_shock_v10_source")
DAY="2026-09-30"; UA="CryptoLab-IntradayLargeShock-Source/1.0"
def H(b):return hashlib.sha256(b).hexdigest()
def ts(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def req(url,params=None,timeout=90):
 for i in range(4):
  try:
   r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
   return r
  except Exception:time.sleep(.5*(i+1))
 raise RuntimeError(url)
def main():
 OUT.mkdir(parents=True,exist_ok=True); start=ts(DAY+"T14:20:00Z");end=ts(DAY+"T19:05:00Z");rows=[]
 for c in B["candidates"]:
  t=c["target"];e=c["external_binance"];rec={"target":t,"external":e}
  mr=req(f"https://api.mexc.com/api/v1/contract/kline/{t}",{"interval":"Min1","start":str(start),"end":str(end)})
  try:mc=len((mr.json().get("data") or {}).get("time") or []) if mr.status_code==200 else 0
  except:mc=0
  br=req(f"https://data.binance.vision/data/futures/um/daily/klines/{e}/1m/{e}-1m-{DAY}.zip")
  bc=0
  if br.status_code==200:
   try:
    z=zipfile.ZipFile(io.BytesIO(br.content))
    for row in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding="utf-8")):
     try:x=int(row[0])//1000
     except:continue
     if start<=x<=end:bc+=1
   except:pass
  gr=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":e,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(start*1000),"endTime":str(end*1000),"limit":"1000"})
  try:gc=len(gr.json().get("data") or []) if gr.status_code==200 else 0
  except:gc=0
  rec.update({"mexc_rows":mc,"binance_rows":bc,"bitget_rows":gc,"source_pass":mc>=270 and bc>=270 and gc>=260,
   "mexc_sha256":H(mr.content),"binance_sha256":H(br.content) if br.status_code==200 else None,"bitget_sha256":H(gr.content)})
  rows.append(rec);print(t,rec["source_pass"],mc,bc,gc);time.sleep(.02)
 rep={"gate_id":"MEXC_INTRADAY_LARGE_SHOCK_SOURCE_V1_0","source_only":True,"verification_date":DAY,"window":["14:20","19:05"],
  "source_pass_count":sum(x["source_pass"] for x in rows),"results":rows,"outcomes_opened":0,
  "verdict":"SOURCE_PASS" if all(x["source_pass"] for x in rows) else "SOURCE_PARTIAL_OR_BLOCKED",
  "private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading":False}
 (OUT/"MEXC_INTRADAY_LARGE_SHOCK_SOURCE_V10.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
 print(json.dumps({"verdict":rep["verdict"],"source_pass_count":rep["source_pass_count"]},indent=2))
if __name__=="__main__":main()

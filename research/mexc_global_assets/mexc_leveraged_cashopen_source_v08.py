#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,zipfile,requests
from datetime import datetime
from pathlib import Path
OUT=Path("artifacts/mexc_global_assets/leveraged_cashopen_v08_source")
DAY="2026-09-30"
PAIRS=[("MUU_USDT","MUUUSDT"),("MVLL_USDT","MVLLUSDT")]
def ts(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 a=ts(DAY+"T13:20:00Z");b=ts(DAY+"T14:05:00Z");rows=[]
 for target,ext in PAIRS:
  mr=requests.get(f"https://api.mexc.com/api/v1/contract/kline/{target}",params={"interval":"Min1","start":a,"end":b},timeout=30)
  mj=mr.json() if mr.status_code==200 else {};md=mj.get("data") or {};mc=len(md.get("time") or [])
  br=requests.get(f"https://data.binance.vision/data/futures/um/daily/klines/{ext}/1m/{ext}-1m-{DAY}.zip",timeout=60)
  bc=0
  if br.status_code==200:
   z=zipfile.ZipFile(io.BytesIO(br.content))
   for row in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding="utf-8")):
    try:t=int(row[0])//1000
    except:continue
    if a<=t<=b:bc+=1
  gr=requests.get("https://api.bitget.com/api/v2/mix/market/history-candles",params={"symbol":ext,"productType":"USDT-FUTURES","granularity":"1m","startTime":a*1000,"endTime":b*1000,"limit":"100"},timeout=30)
  gj=gr.json() if gr.status_code==200 else {};gc=len(gj.get("data") or [])
  ok=mc>=40 and bc>=40 and gc>=40
  rows.append({"target":target,"external":ext,"mexc_rows":mc,"binance_rows":bc,"bitget_rows":gc,"source_pass":ok})
  print(target,ok,mc,bc,gc)
 rep={"gate_id":"MEXC_LEVERAGED_CASHOPEN_SOURCE_V0_8","source_only":True,"verification_date":DAY,"results":rows,
      "source_pass_count":sum(x["source_pass"] for x in rows),"verdict":"PASS" if all(x["source_pass"] for x in rows) else "BLOCKED",
      "outcomes_opened":0,"orders":False,"live_trading":False}
 (OUT/"MEXC_LEVERAGED_CASHOPEN_SOURCE_V08.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
 print(json.dumps(rep,indent=2))
if __name__=="__main__":main()

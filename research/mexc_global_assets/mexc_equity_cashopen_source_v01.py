#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,zipfile,hashlib
from pathlib import Path
from datetime import datetime,timezone
import requests

OUT=Path("artifacts/mexc_global_assets/equity_cashopen_source_v01"); OUT.mkdir(parents=True,exist_ok=True)
UA="CryptoLab-MEXC-Equity-CashOpen-Source/0.1"
DAY="2026-09-30"
ASSETS={
 "TSLA":{"mexc":"TESLA_USDT","external":"TSLAUSDT"},
 "AAPL":{"mexc":"AAPLSTOCK_USDT","external":"AAPLUSDT"},
 "PLTR":{"mexc":"PLTRSTOCK_USDT","external":"PLTRUSDT"},
 "META":{"mexc":"METASTOCK_USDT","external":"METAUSDT"},
 "AMZN":{"mexc":"AMZNSTOCK_USDT","external":"AMZNUSDT"},
 "MSFT":{"mexc":"MSFTSTOCK_USDT","external":"MSFTUSDT"},
}
def sha(b): return hashlib.sha256(b).hexdigest()
def req(u,p=None,t=60): return requests.get(u,params=p,headers={"User-Agent":UA},timeout=t)
def save(n,r):
 (OUT/n).write_bytes(r.content)
 (OUT/(n+".meta.json")).write_text(json.dumps({"url":r.url,"status":r.status_code,"sha256":sha(r.content),"captured_at_utc":datetime.now(timezone.utc).isoformat()},indent=2))
def main():
 start=int(datetime.fromisoformat(DAY+"T13:20:00+00:00").timestamp())
 end=int(datetime.fromisoformat(DAY+"T14:01:00+00:00").timestamp())
 rep={"lab":"MEXC_MULTI_EQUITY_CASHOPEN_SOURCE_V0_1","source_only":True,"verification_date":DAY,"window_utc":"13:20-14:01","historical_outcomes_opened":0,"signal_tested":False,"assets":{}}
 for t,cfg in ASSETS.items():
  x={"mexc_symbol":cfg["mexc"],"external_symbol":cfg["external"]}
  r=req(f"https://api.mexc.com/api/v1/contract/kline/{cfg['mexc']}",{"interval":"Min1","start":str(start),"end":str(end)}); save(f"mexc_{t}.json",r)
  mj=r.json() if r.status_code==200 else {}; md=mj.get("data") or {}
  x["mexc_rows"]=len(md.get("time") or []); x["mexc_ok"]=r.status_code==200 and mj.get("success") is True and x["mexc_rows"]>=38
  r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{cfg['external']}/1m/{cfg['external']}-1m-{DAY}.zip",t=90); save(f"binance_{t}.zip",r)
  core=0
  if r.status_code==200:
   try:
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)==1:
     for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
      try: ts=int(row[0])//1000
      except: continue
      if start<=ts<=end: core+=1
   except: pass
  x["binance_rows"]=core; x["binance_ok"]=core>=38
  r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":cfg["external"],"productType":"USDT-FUTURES","granularity":"1m","startTime":str(start*1000),"endTime":str(end*1000),"limit":"100"}); save(f"bitget_{t}.json",r)
  bj=r.json() if r.status_code==200 else {}; rows=bj.get("data") or []
  x["bitget_rows"]=len(rows); x["bitget_ok"]=r.status_code==200 and bj.get("code")=="00000" and len(rows)>=38
  x["source_pass"]=x["mexc_ok"] and x["binance_ok"] and x["bitget_ok"]
  rep["assets"][t]=x
 rep["pass_assets"]=[t for t,x in rep["assets"].items() if x["source_pass"]]
 rep["verdict"]="MULTI_EQUITY_CASHOPEN_SOURCE_PASS" if len(rep["pass_assets"])==len(ASSETS) else "PARTIAL_MULTI_EQUITY_CASHOPEN_SOURCE"
 rep.update({"private_endpoints_used":False,"account_reads":False,"orders":False,"exchange_mutation":False,"live_trading_authorized":False})
 (OUT/"MEXC_EQUITY_CASHOPEN_SOURCE_RECEIPT_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
 print(json.dumps({"verdict":rep["verdict"],"pass_assets":rep["pass_assets"],"assets":rep["assets"]},indent=2,sort_keys=True))
if __name__=="__main__": main()

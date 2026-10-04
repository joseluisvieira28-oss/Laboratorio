#!/usr/bin/env python3
import requests,json,hashlib
from datetime import datetime
from pathlib import Path
OUT=Path("artifacts/aster_nvda/v01_source");BASE="https://fapi.asterdex.com/fapi/v3"
def h(b):return hashlib.sha256(b).hexdigest()
def ts(x):return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)
def main():
 OUT.mkdir(parents=True,exist_ok=True)
 e=requests.get(BASE+"/exchangeInfo",timeout=40);j=e.json();hits=[x for x in j.get("symbols",[]) if "NVDA" in x.get("symbol","").upper()]
 probes=[]
 for x in hits:
  sym=x["symbol"];k=requests.get(BASE+"/klines",params={"symbol":sym,"interval":"1m","startTime":ts("2026-09-30T14:25:00Z"),"endTime":ts("2026-09-30T19:05:00Z"),"limit":500},timeout=30)
  d=requests.get(BASE+"/depth",params={"symbol":sym,"limit":5},timeout=30)
  try:bars=k.json()
  except:bars=[]
  try:book=d.json()
  except:book={}
  best=None
  try:
   bid=float(book["bids"][0][0]);ask=float(book["asks"][0][0]);mid=(bid+ask)/2;best={"bid":bid,"ask":ask,"spread_bps":10000*(ask-bid)/mid}
  except:pass
  probes.append({"symbol":sym,"metadata":x,"kline_http":k.status_code,"bars":len(bars) if isinstance(bars,list) else None,"kline_sha":h(k.content),"depth_http":d.status_code,"current_best":best})
 rep={"gate_id":"ASTER_NVDA_SOURCE_GATE_V0_1","source_only":True,"outcomes_opened":0,"exchange_info_http":e.status_code,"exchange_info_sha":h(e.content),"nvda_hits":hits,"probes":probes,
 "private_endpoints_used":False,"account_reads":False,"wallets":False,"orders":False,"live_trading_authorized":False}
 rep["verdict"]="ASTER_NVDA_PUBLIC_SOURCE_PASS" if any((x["bars"] or 0)>=250 for x in probes) else "ASTER_NVDA_SOURCE_BLOCKED"
 (OUT/"ASTER_NVDA_SOURCE_GATE_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
 print(json.dumps({"verdict":rep["verdict"],"nvda_symbols":[x["symbol"] for x in hits],"probes":[{"symbol":x["symbol"],"bars":x["bars"],"current_best":x["current_best"]} for x in probes]},indent=2))
if __name__=="__main__":main()

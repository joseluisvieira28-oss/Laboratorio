#!/usr/bin/env python3
"""Hyperliquid xyz:NVDA public source/fee-state probe. No outcomes."""
from __future__ import annotations
import json,hashlib,requests
from datetime import datetime
from pathlib import Path
OUT=Path("artifacts/hyperliquid_xyz_nvda/v01_source")
URL="https://api.hyperliquid.xyz/info"
def h(b):return hashlib.sha256(b).hexdigest()
def post(body):
 r=requests.post(URL,json=body,timeout=30);return r
def ts(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp()*1000)
def main():
 OUT.mkdir(parents=True,exist_ok=True);probes=[]
 bodies=[
  {"type":"perpDexs"},
  {"type":"metaAndAssetCtxs","dex":"xyz"},
  {"type":"candleSnapshot","req":{"coin":"xyz:NVDA","interval":"1m","startTime":ts("2026-09-30T14:25:00Z"),"endTime":ts("2026-09-30T19:05:00Z")}},
  {"type":"l2Book","coin":"xyz:NVDA","nSigFigs":5}
 ]
 parsed=[]
 for b in bodies:
  r=post(b);rec={"request":b,"http":r.status_code,"sha256":h(r.content)}
  try:rec["json"]=r.json()
  except:rec["text"]=r.text[:5000]
  parsed.append(rec);print(json.dumps({"request":b,"http":r.status_code,"sha256":rec["sha256"]}))
 meta=next((x["json"] for x in parsed if x["request"].get("type")=="metaAndAssetCtxs" and x["http"]==200),None)
 nvda=None
 if isinstance(meta,list) and len(meta)>=2 and isinstance(meta[0],dict):
  universe=meta[0].get("universe") or [];ctx=meta[1] if isinstance(meta[1],list) else []
  for i,u in enumerate(universe):
   if str(u.get("name","")).upper() in {"NVDA","XYZ:NVDA"}:
    nvda={"index":i,"meta":u,"ctx":ctx[i] if i<len(ctx) else None};break
 candles=next((x.get("json") for x in parsed if x["request"].get("type")=="candleSnapshot"),None)
 book=next((x.get("json") for x in parsed if x["request"].get("type")=="l2Book"),None)
 # best bid/ask source-only current snapshot
 best=None
 if isinstance(book,dict):
  lv=book.get("levels") or []
  try:
   bid=max(float(x["px"]) for x in lv[0]);ask=min(float(x["px"]) for x in lv[1]);mid=(bid+ask)/2
   best={"bid":bid,"ask":ask,"mid":mid,"spread_bps":10000*(ask-bid)/mid}
  except:pass
 rep={"gate_id":"HYPERLIQUID_XYZ_NVDA_SOURCE_GATE_V0_1","source_only":True,"outcomes_opened":0,
  "nvda_market":nvda,"history_probe_bars":len(candles) if isinstance(candles,list) else None,
  "current_l2_best":best,"raw_probes":parsed,
  "growth_mode_status_proven":(nvda or {}).get("meta",{}).get("growthMode") if nvda else None,
  "private_endpoints_used":False,"account_reads":False,"wallets":False,"orders":False,"live_trading_authorized":False}
 rep["verdict"]="HL_XYZ_NVDA_PUBLIC_SOURCE_PASS" if nvda and isinstance(candles,list) and len(candles)>=250 else "HL_XYZ_NVDA_SOURCE_BLOCKED"
 (OUT/"HYPERLIQUID_XYZ_NVDA_SOURCE_GATE_V01.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
 print(json.dumps({"verdict":rep["verdict"],"nvda_market":nvda,"history_probe_bars":rep["history_probe_bars"],"current_l2_best":best,"growth_mode_status_proven":rep["growth_mode_status_proven"]},indent=2))
if __name__=="__main__":main()

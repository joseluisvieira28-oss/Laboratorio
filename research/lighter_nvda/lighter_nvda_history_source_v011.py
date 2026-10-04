#!/usr/bin/env python3
"""Lighter NVDA V0.1.1 public historical candle coverage probe. Source only."""
from __future__ import annotations
import json,hashlib,requests
from datetime import datetime,timezone
from pathlib import Path
OUT=Path("artifacts/lighter_nvda/v011_history")
BASE="https://mainnet.zklighter.elliot.ai"
MID=110
DATES=["2026-09-09","2026-09-30","2026-10-02"]
RES=["1m","5m","1h"]
def ts(s):return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
def h(b):return hashlib.sha256(b).hexdigest()
def main():
 OUT.mkdir(parents=True,exist_ok=True);rows=[]
 for d in DATES:
  for res in RES:
   a=ts(d+"T14:25:00Z");b=ts(d+"T19:05:00Z")
   r=requests.get(BASE+"/api/v1/candles",params={"market_id":MID,"resolution":res,"start_timestamp":a,"end_timestamp":b,"count_back":500},timeout=30)
   rec={"date":d,"resolution":res,"http":r.status_code,"sha256":h(r.content),"bars":None,"first_t":None,"last_t":None}
   try:
    j=r.json();c=j.get("c") or [];rec["bars"]=len(c)
    if c:rec["first_t"]=c[0].get("t");rec["last_t"]=c[-1].get("t")
    rec["code"]=j.get("code");rec["echo_resolution"]=j.get("r")
   except Exception as e:rec["parse_error"]=repr(e)
   rows.append(rec);print(rec)
 rep={"gate_id":"LIGHTER_NVDA_HISTORY_SOURCE_GATE_V0_1_1","source_only":True,"market_id":MID,
      "dates":DATES,"results":rows,"outcomes_opened":0,
      "one_minute_history_pass":all(x["http"]==200 and (x["bars"] or 0)>=250 for x in rows if x["resolution"]=="1m"),
      "private_endpoints_used":False,"account_reads":False,"orders":False,"wallets":False}
 rep["verdict"]="LIGHTER_NVDA_1M_HISTORY_SOURCE_PASS" if rep["one_minute_history_pass"] else "LIGHTER_NVDA_1M_HISTORY_SOURCE_BLOCKED"
 (OUT/"LIGHTER_NVDA_HISTORY_SOURCE_V011.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
 print(json.dumps({"verdict":rep["verdict"],"results":rows},indent=2))
if __name__=="__main__":main()

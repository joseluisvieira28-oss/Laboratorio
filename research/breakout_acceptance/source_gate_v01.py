#!/usr/bin/env python3
import json, urllib.request, urllib.parse, time, sys
SYMS=["BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT"]
BASE="https://api.binance.com"
STEP=14400000
def main():
 out={"lab_id":"BREAKOUT-ACCEPTANCE-001","phase":"SOURCE_ONLY","classification":"SOURCE_FAIL","market_outcomes_computed":False,"symbols":{}}
 try:
  now=int(time.time()*1000)
  for s in SYMS:
   q=urllib.parse.urlencode({"symbol":s,"interval":"4h","limit":250})
   req=urllib.request.Request(BASE+"/api/v3/klines?"+q,headers={"User-Agent":"ARQ018-source-v0.1"})
   with urllib.request.urlopen(req,timeout=30) as r: rows=json.loads(r.read().decode())
   closed=[x for x in rows if int(x[6])<now][-200:]
   ots=[int(x[0]) for x in closed]
   if len(closed)!=200 or any(b-a!=STEP for a,b in zip(ots,ots[1:])): raise RuntimeError(s+":coverage")
   out["symbols"][s]={"closed_bars":200,"first_open_ms":ots[0],"last_open_ms":ots[-1],"contiguous":True}
  out["classification"]="SOURCE_PASS"
 except Exception as e: out["failure"]=f"{type(e).__name__}:{e}"
 open("ARQ018_SOURCE_GATE_V0_1.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
 print(json.dumps({"classification":out["classification"],"symbols":len(out["symbols"]),"market_outcomes_computed":False,"failure":out.get("failure")},sort_keys=True))
 return 0 if out["classification"]=="SOURCE_PASS" else 2
if __name__=="__main__":sys.exit(main())

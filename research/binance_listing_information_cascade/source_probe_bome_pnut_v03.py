#!/usr/bin/env python3
# SOURCE-ONLY forensic probe. Never computes/prints post-T0 prices or returns.
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone
E=[("BOME",1710581406588),("PNUT",1731303569462)]
def req(u):
 r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLabSourceOnly/3.0","Accept":"application/json"})
 try:
  with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
 except Exception as e:return None,None,repr(e)
def iso(ms):return datetime.fromtimestamp(ms/1000,timezone.utc).isoformat()
def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 st,j,e=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 xs=(j or {}).get("data") or [];ts=sorted(int(x[0]) for x in xs)
 return {"http":st,"error":e,"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}
def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 st,j,e=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 xs=(j or {}).get("data") or [];ts=sorted(int(x[0])*1000 for x in xs)
 return {"http":st,"error":e,"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}
rows=[]
for t,t0 in E:
 m=(t0//60000)*60000
 windows={
 "pre25_23":(m-25*3600000,m-23*3600000),
 "pre24_1_start":(m-24*3600000,m-22*3600000),
 "p0_only":(m-10*60000,m-60000),
 "event_presence_only":(m,m+65*60000)}
 row={"ticker":t,"t0":iso(t0),"venues":{}}
 for name,fn in [("BITGET",bitget),("KUCOIN",kucoin)]:
  row["venues"][name]={}
  for w,(a,b) in windows.items():
   z=fn(t,a,b);time.sleep(.05)
   # event window is presence metadata only; never prices/outcomes
   row["venues"][name][w]=z
 row["source_pass"]=any(v["pre25_23"]["n"]>0 and v["p0_only"]["n"]>0 and v["event_presence_only"]["n"]>0 for v in row["venues"].values())
 rows.append(row)
print(json.dumps(rows,indent=2))

#!/usr/bin/env python3
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone
E=[
("RPL",1674014406526),("GNS",1676619260939),("SYN",1677047419653),("LQTY",1677568518334),
("ARB",1679306561345),("RDNT",1680146454557),("FLOKI",1683285604106),("PEPE",1683285604106),
("PENDLE",1688365335567),("WLD",1690182131620),("NTRN",1696923917379),("TIA",1698671932206),
("ORDI",1699339453500),("BLUR",1700806187186),("JTO",1701950138787),("1000SATS",1702361370579),
("BONK",1702612713180)
]
ALIASES={"1000SATS":["1000SATS","SATS"]}

def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV07Source/1.0","Accept":"application/json"})
 try:
  with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
 except urllib.error.HTTPError as e:return e.code,None,e.read().decode("utf-8","replace")[:400]
 except Exception as e:return None,None,repr(e)

def iso(ms):return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()
def tslist(j,kind):
 out=[]
 try:
  if kind=="BITGET":
   for x in (j or {}).get("data") or []:out.append(int(x[0]))
  elif kind=="KUCOIN":
   for x in (j or {}).get("data") or []:out.append(int(x[0])*1000)
  elif kind in ("MEXC","GATE"):
   for x in j or []:out.append(int(x[0])*(1000 if kind=="GATE" else 1))
  elif kind=="OKX":
   for x in (j or {}).get("data") or []:out.append(int(x[0]))
 except:pass
 return sorted(out)
def pack(st,j,err,kind):
 ts=tslist(j,kind);return {"http":st,"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None,"error":err}
def call(kind,sym,a,b):
 if kind=="BITGET":
  q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
  st,j,e=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 elif kind=="KUCOIN":
  q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
  st,j,e=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 elif kind=="MEXC":
  q=urllib.parse.urlencode({"symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":1000})
  st,j,e=req("https://api.mexc.com/api/v3/klines?"+q)
 elif kind=="GATE":
  q=urllib.parse.urlencode({"currency_pair":sym+"_USDT","interval":"1m","from":a//1000,"to":b//1000})
  st,j,e=req("https://api.gateio.ws/api/v4/spot/candlesticks?"+q)
 else:
  q=urllib.parse.urlencode({"instId":sym+"-USDT","bar":"1m","after":str(b+60000),"before":str(a-60000),"limit":"300"})
  st,j,e=req("https://www.okx.com/api/v5/market/history-candles?"+q)
 return pack(st,j,e,kind)

rows=[]
for ticker,t0 in E:
 best=None
 for alias in ALIASES.get(ticker,[ticker]):
  a=t0-25*3600000;b=t0-23*3600000;c=t0-10*60000;d=t0+65*60000
  probes={}
  for kind in ["BITGET","KUCOIN","MEXC","GATE","OKX"]:
   p=call(kind,alias,a,b);time.sleep(.02);e=call(kind,alias,c,d);time.sleep(.02)
   probes[kind]={"pre":p,"event":e,"pass":p["n"]>0 and e["n"]>0}
  venue=next((k for k in ["BITGET","KUCOIN","MEXC","GATE","OKX"] if probes[k]["pass"]),None)
  row={"ticker":ticker,"alias":alias,"t0":iso(t0),"selected_venue":venue,
       "status":"SOURCE_COVERAGE_PASS" if venue else "NO_PRIMARY_SOURCE_COVERAGE","probes":probes}
  if venue:best=row;break
  if best is None:best=row
 rows.append(best)
valid=[r for r in rows if r["status"]=="SOURCE_COVERAGE_PASS"]
print("V07_SOURCE_GATE_BEGIN")
print(json.dumps({"candidate_assets":len(E),"n_valid":len(valid),
 "valid":[{"ticker":r["ticker"],"alias":r["alias"],"selected_venue":r["selected_venue"],"t0":r["t0"]} for r in valid],
 "invalid":[r["ticker"] for r in rows if r["status"]!="SOURCE_COVERAGE_PASS"],"rows":rows},indent=2))
print("V07_SOURCE_GATE_END")

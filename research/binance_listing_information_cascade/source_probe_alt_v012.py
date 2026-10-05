#!/usr/bin/env python3
import json,time,urllib.parse,urllib.request
from datetime import datetime

EVENTS=[
("WIF","2024-03-05T10:01:00Z"),("AXL","2024-03-01T07:18:00Z"),
("TAO","2024-04-11T06:43:00Z"),("NEIRO","2024-09-16T05:45:00Z"),
("TURBO","2024-09-16T05:45:00Z"),("1MBABYDOGE","2024-09-16T05:45:00Z"),
("COW","2024-11-06T05:10:00Z"),("CETUS","2024-11-06T05:10:00Z"),
("ACT","2024-11-11T05:39:00Z"),("PNUT","2024-11-11T05:39:00Z"),
("ACX","2024-12-06T08:34:00Z"),("ORCA","2024-12-06T08:34:00Z"),
("VELODROME","2024-12-13T08:07:00Z")]
ALIASES={
"1MBABYDOGE":["BABYDOGE","1MBABYDOGE"],
"NEIRO":["NEIRO","NEIROETH"],
"VELODROME":["VELODROME","VELO"],
}

def req(url):
    r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabSourceProbe/1.0","Accept":"application/json"})
    try:
      with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
    except urllib.error.HTTPError as e:
      body=e.read().decode("utf-8","replace")[:500]
      return e.code,None,body
    except Exception as e:return None,None,repr(e)

def iso(ms): return datetime.utcfromtimestamp(ms/1000).isoformat()+"Z"

def kucoin(sym,a,b):
    u="https://api.kucoin.com/api/v1/market/candles?"+urllib.parse.urlencode(
      {"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
    st,j,err=req(u)
    if not j:return {"http":st,"error":err}
    xs=j.get("data",[]); ts=sorted(int(x[0])*1000 for x in xs)
    return {"http":st,"code":j.get("code"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}

def mexc(sym,a,b):
    u="https://api.mexc.com/api/v3/klines?"+urllib.parse.urlencode(
      {"symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":1000})
    st,j,err=req(u)
    if not isinstance(j,list):return {"http":st,"error":err or j}
    ts=sorted(int(x[0]) for x in j)
    return {"http":st,"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}

for ticker,t in EVENTS:
  t0=int(datetime.fromisoformat(t.replace("Z","+00:00")).timestamp()*1000)
  for alias in ALIASES.get(ticker,[ticker]):
    for w,(a,b) in {
      "pre24h":(t0-25*3600000,t0-23*3600000),
      "event":(t0-10*60000,t0+65*60000)
    }.items():
      print(json.dumps({"ticker":ticker,"alias":alias,"window":w,
        "kucoin":kucoin(alias,a,b),"mexc":mexc(alias,a,b)},sort_keys=True))
      time.sleep(.12)

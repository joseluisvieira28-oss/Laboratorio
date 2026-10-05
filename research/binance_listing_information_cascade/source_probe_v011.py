#!/usr/bin/env python3
import json, time, urllib.parse, urllib.request
from datetime import datetime

EVENTS=[
("WIF","2024-03-05T10:01:00Z"),("AXL","2024-03-01T07:18:00Z"),
("TAO","2024-04-11T06:43:00Z"),("TURBO","2024-09-16T05:45:00Z"),
("COW","2024-11-06T05:10:00Z"),("CETUS","2024-11-06T05:10:00Z"),
("ACT","2024-11-11T05:39:00Z"),("PNUT","2024-11-11T05:39:00Z"),
("ACX","2024-12-06T08:34:00Z"),("ORCA","2024-12-06T08:34:00Z"),
("VELODROME","2024-12-13T08:07:00Z")
]
ALIASES={"VELODROME":["VELODROME","VELO"],"WIF":["WIF"],"ORCA":["ORCA"],"CETUS":["CETUS"],"TURBO":["TURBO"]}

def req(url):
    r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabSourceProbe/1.0","Accept":"application/json"})
    with urllib.request.urlopen(r,timeout=20) as x:
        return x.status, json.load(x)

def iso(ms):
    return datetime.utcfromtimestamp(ms/1000).isoformat()+"Z"

def bybit(sym,a,b):
    u="https://api.bybit.com/v5/market/kline?"+urllib.parse.urlencode(
      {"category":"spot","symbol":sym+"USDT","interval":"1","start":a,"end":b,"limit":1000})
    try:
      st,j=req(u); xs=j.get("result",{}).get("list",[])
      ts=sorted(int(x[0]) for x in xs)
      return {"http":st,"retCode":j.get("retCode"),"retMsg":j.get("retMsg"),"n":len(ts),
              "first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}
    except Exception as e:return {"error":repr(e)}

def okx(sym,a,b):
    u="https://www.okx.com/api/v5/market/history-candles?"+urllib.parse.urlencode(
      {"instId":sym+"-USDT","bar":"1m","after":a-1,"before":b+1,"limit":300})
    try:
      st,j=req(u); xs=j.get("data",[])
      ts=sorted(int(x[0]) for x in xs)
      return {"http":st,"code":j.get("code"),"msg":j.get("msg"),"n":len(ts),
              "first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}
    except Exception as e:return {"error":repr(e)}

def gate(sym,a,b):
    u="https://api.gateio.ws/api/v4/spot/candlesticks?"+urllib.parse.urlencode(
      {"currency_pair":sym+"_USDT","interval":"1m","from":a//1000,"to":b//1000})
    try:
      st,j=req(u)
      if isinstance(j,dict): return {"http":st,"dict":j}
      ts=sorted(int(x[0])*1000 for x in j)
      return {"http":st,"n":len(ts),"first":iso(ts[0]) if ts else None,
              "last":iso(ts[-1]) if ts else None}
    except Exception as e:return {"error":repr(e)}

for ticker,t in EVENTS:
    t0=int(datetime.fromisoformat(t.replace("Z","+00:00")).timestamp()*1000)
    # source-only witnesses: one window around T-24h, one around T0. No OHLC values printed.
    windows={"pre24h":(t0-25*3600000,t0-23*3600000),"event":(t0-10*60000,t0+65*60000)}
    for alias in ALIASES.get(ticker,[ticker]):
      for w,(a,b) in windows.items():
        print(json.dumps({"ticker":ticker,"alias":alias,"window":w,
          "bybit":bybit(alias,a,b),"okx":okx(alias,a,b),"gate":gate(alias,a,b)},sort_keys=True))
        time.sleep(.2)

# trigger after workflow registration

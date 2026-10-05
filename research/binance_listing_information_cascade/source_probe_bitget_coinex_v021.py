#!/usr/bin/env python3
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone

EVENTS=[
("JUP",1706684813622),("PYTH",1706860207072),("RONIN",1707124296210),("DYM",1707211617933),
("STRK",1708395922135),("AXL",1709277537028),("WIF",1709632897364),("METIS",1710143970976),
("BOME",1710581406588),("W",1712054366812),("TNSR",1712576657942),("TAO",1712817838489),
("ZK",1718589610865),("ZRO",1718864370953),("TON",1723095568744),("NEIRO",1726465502167),
("TURBO",1726465502167),("1MBABYDOGE",1726465502167),("EIGEN",1727684397115),
("COW",1730869807602),("CETUS",1730869807602),("ACT",1731303569462),("PNUT",1731303569462),
("ACX",1733474058953),("ORCA",1733474058953),("ME",1733815340546),("VELODROME",1734077277826)]
ALIASES={"1MBABYDOGE":["BABYDOGE","1MBABYDOGE"],"NEIRO":["NEIRO","NEIROETH"]}

def req(url):
  r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabSourceProbe/2.1","Accept":"application/json"})
  try:
    with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
  except urllib.error.HTTPError as e:return e.code,None,e.read().decode("utf-8","replace")[:500]
  except Exception as e:return None,None,repr(e)

def iso(ms): return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def bitget(sym,a,b):
  q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
  st,j,err=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
  if not isinstance(j,dict):return {"http":st,"error":err or j}
  xs=j.get("data") or []
  ts=[]
  for x in xs:
    try: ts.append(int(x[0]))
    except: pass
  ts.sort()
  return {"http":st,"code":j.get("code"),"msg":j.get("msg"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}

def coinex(sym,a,b):
  q=urllib.parse.urlencode({"market":sym+"USDT","period":"1min","start_time":a,"end_time":b,"limit":1000})
  st,j,err=req("https://api.coinex.com/v2/spot/kline?"+q)
  if not isinstance(j,dict):return {"http":st,"error":err or j}
  xs=j.get("data") or []
  ts=[]
  for x in xs:
    try:
      v=x.get("created_at") if isinstance(x,dict) else x[0]
      v=int(v)
      # current docs use milliseconds; tolerate accidental microseconds
      if v>10**14:v//=1000
      ts.append(v)
    except: pass
  ts.sort()
  return {"http":st,"code":j.get("code"),"msg":j.get("message"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}

rows=[]
for ticker,t0 in EVENTS:
  best=None
  for alias in ALIASES.get(ticker,[ticker]):
    a=t0-25*3600000;b=t0-23*3600000;c=t0-10*60000;d=t0+65*60000
    bp=bitget(alias,a,b); time.sleep(.08); be=bitget(alias,c,d); time.sleep(.08)
    cp=coinex(alias,a,b); time.sleep(.08); ce=coinex(alias,c,d); time.sleep(.08)
    bo=bp.get("n",0)>0 and be.get("n",0)>0
    co=cp.get("n",0)>0 and ce.get("n",0)>0
    row={"ticker":ticker,"alias":alias,"t0":iso(t0),"bitget_pre":bp,"bitget_event":be,"coinex_pre":cp,"coinex_event":ce,
         "bitget_pass":bo,"coinex_pass":co}
    if bo or co: best=row;break
    if best is None:best=row
  rows.append(best)
print("ALT2_SOURCE_JSON_BEGIN")
print(json.dumps({"bitget_valid":[r["ticker"] for r in rows if r["bitget_pass"]],
                  "coinex_valid":[r["ticker"] for r in rows if r["coinex_pass"]],
                  "rows":rows},indent=2))
print("ALT2_SOURCE_JSON_END")

# trigger after workflow registration

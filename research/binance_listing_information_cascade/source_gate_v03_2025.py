#!/usr/bin/env python3
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone

# Parsed directly from official 2025 Binance "Binance Will List ..." census.
# Stablecoin-like listings excluded by the frozen V0.3 rules:
# XUSD, USD1, BFUSD, USDE, KGST.
E=[
("AIXBT",1736499327639),("CGPT",1736499327639),("COOKIE",1736499327639),
("TRUMP",1737259542151),
("1000CHEEMS",1739085031264),("TST",1739085031264),
("SYRUP",1746530720814),("KMNO",1746530720814),
("WLFI",1756691345082),("PUMP",1757590673797),("AVNT",1757908021934),
("ASTER",1759736929954),("GIGGLE",1761361338417),("F",1761361338417),
("BANK",1763028026501),("MET",1763028026501)
]
ALIASES={"1000CHEEMS":["1000CHEEMS","CHEEMS"]}

def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV03Source/1.0","Accept":"application/json"})
 try:
  with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
 except urllib.error.HTTPError as e:return e.code,None,e.read().decode("utf-8","replace")[:400]
 except Exception as e:return None,None,repr(e)

def iso(ms):return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 st,j,err=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 if not isinstance(j,dict):return {"http":st,"error":err}
 xs=j.get("data") or [];ts=[]
 for x in xs:
  try:ts.append(int(x[0]))
  except:pass
 ts.sort()
 return {"http":st,"code":j.get("code"),"msg":j.get("msg"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}

def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 st,j,err=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 if not isinstance(j,dict):return {"http":st,"error":err}
 xs=j.get("data") or [];ts=[]
 for x in xs:
  try:ts.append(int(x[0])*1000)
  except:pass
 ts.sort()
 return {"http":st,"code":j.get("code"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None}

rows=[]
for ticker,t0 in E:
 best=None
 for alias in ALIASES.get(ticker,[ticker]):
  a=t0-25*3600000;b=t0-23*3600000;c=t0-10*60000;d=t0+65*60000
  bp=bitget(alias,a,b);time.sleep(.05);be=bitget(alias,c,d);time.sleep(.05)
  kp=kucoin(alias,a,b);time.sleep(.05);ke=kucoin(alias,c,d);time.sleep(.05)
  bo=bp.get("n",0)>0 and be.get("n",0)>0
  ko=kp.get("n",0)>0 and ke.get("n",0)>0
  venue="BITGET" if bo else ("KUCOIN" if ko else None)
  row={"ticker":ticker,"alias":alias,"t0":iso(t0),
       "bitget_pre":bp,"bitget_event":be,"kucoin_pre":kp,"kucoin_event":ke,
       "bitget_pass":bo,"kucoin_pass":ko,"selected_venue":venue,
       "status":"SOURCE_COVERAGE_PASS" if venue else "NO_PRIMARY_SOURCE_COVERAGE"}
  if venue:best=row;break
  if best is None:best=row
 rows.append(best)

valid=[r for r in rows if r["status"]=="SOURCE_COVERAGE_PASS"]
print("V03_SOURCE_GATE_BEGIN")
print(json.dumps({"candidate_assets":len(E),"n_valid":len(valid),
                  "valid":[{"ticker":r["ticker"],"alias":r["alias"],"selected_venue":r["selected_venue"],"t0":r["t0"]} for r in valid],
                  "invalid":[r["ticker"] for r in rows if r["status"]!="SOURCE_COVERAGE_PASS"],
                  "rows":rows},indent=2))
print("V03_SOURCE_GATE_END")

#!/usr/bin/env python3
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone

E=[
("币安人生",1767782346580),("ZKP",1767782346580),
("FOGO",1768222253294),("SENT",1769059554238),("ZAMA",1770006523224),
("ESP",1770881303176),("ROBO",1772629994452),("KAT",1773366336337),
("CFG",1773656559260),("XAUT",1774521928143),("CHIP",1776772832132),
("MEGA",1777540049704),("AIGENSYN",1778752803676),
("GENIUS",1779434315961),("OPG",1779434315961),("RE",1781776041424),
("AERO",1784273401964),("MARSCOIN",1788516901870),("牛来",1788953419513),
("HYPE",1790235038608)
]

def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV06Source/1.0","Accept":"application/json"})
 try:
  with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
 except urllib.error.HTTPError as e:return e.code,None,e.read().decode("utf-8","replace")[:400]
 except Exception as e:return None,None,repr(e)

def iso(ms):return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()
def summarize(st,j,err,scale=1):
 ts=[]
 if isinstance(j,list):
  for x in j:
   try:ts.append(int(x[0])*scale)
   except:pass
 elif isinstance(j,dict):
  for x in (j.get("data") or []):
   try:ts.append(int(x[0])*scale)
   except:pass
 ts.sort()
 return {"http":st,"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None,"error":err}

def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 st,j,err=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 xs=(j or {}).get("data") or [];ts=[]
 for x in xs:
  try:ts.append(int(x[0]))
  except:pass
 ts.sort()
 return {"http":st,"code":(j or {}).get("code"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None,"error":err}

def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 st,j,err=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 xs=(j or {}).get("data") or [];ts=[]
 for x in xs:
  try:ts.append(int(x[0])*1000)
  except:pass
 ts.sort()
 return {"http":st,"code":(j or {}).get("code"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None,"error":err}

def mexc(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":1000})
 st,j,err=req("https://api.mexc.com/api/v3/klines?"+q)
 return summarize(st,j,err,1)

def gate(sym,a,b):
 q=urllib.parse.urlencode({"currency_pair":sym+"_USDT","interval":"1m","from":a//1000,"to":b//1000})
 st,j,err=req("https://api.gateio.ws/api/v4/spot/candlesticks?"+q)
 return summarize(st,j,err,1000)

def okx(sym,a,b):
 q=urllib.parse.urlencode({"instId":sym+"-USDT","bar":"1m","after":str(b+60000),"before":str(a-60000),"limit":"300"})
 st,j,err=req("https://www.okx.com/api/v5/market/history-candles?"+q)
 return summarize(st,j,err,1)

rows=[]
for ticker,t0 in E:
 a=t0-25*3600000;b=t0-23*3600000;c=t0-10*60000;d=t0+65*60000
 probes={}
 for name,fn in [("BITGET",bitget),("KUCOIN",kucoin),("MEXC",mexc),("GATE",gate),("OKX",okx)]:
  p=fn(ticker,a,b);time.sleep(.025);e=fn(ticker,c,d);time.sleep(.025)
  probes[name]={"pre":p,"event":e,"pass":p.get("n",0)>0 and e.get("n",0)>0}
 venue=next((name for name in ["BITGET","KUCOIN","MEXC","GATE","OKX"] if probes[name]["pass"]),None)
 rows.append({"ticker":ticker,"t0":iso(t0),"selected_venue":venue,
              "status":"SOURCE_COVERAGE_PASS" if venue else "NO_PRIMARY_SOURCE_COVERAGE","probes":probes})
valid=[r for r in rows if r["status"]=="SOURCE_COVERAGE_PASS"]
print("V06_SOURCE_GATE_BEGIN")
print(json.dumps({"candidate_assets":len(E),"n_valid":len(valid),
 "valid":[{"ticker":r["ticker"],"selected_venue":r["selected_venue"],"t0":r["t0"]} for r in valid],
 "invalid":[r["ticker"] for r in rows if r["status"]!="SOURCE_COVERAGE_PASS"],"rows":rows},ensure_ascii=False,indent=2))
print("V06_SOURCE_GATE_END")

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
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV04Source/1.0","Accept":"application/json"})
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
 a=t0-25*3600000;b=t0-23*3600000;c=t0-10*60000;d=t0+65*60000
 bp=bitget(ticker,a,b);time.sleep(.04);be=bitget(ticker,c,d);time.sleep(.04)
 kp=kucoin(ticker,a,b);time.sleep(.04);ke=kucoin(ticker,c,d);time.sleep(.04)
 bo=bp.get("n",0)>0 and be.get("n",0)>0
 ko=kp.get("n",0)>0 and ke.get("n",0)>0
 venue="BITGET" if bo else ("KUCOIN" if ko else None)
 rows.append({"ticker":ticker,"t0":iso(t0),"bitget_pre":bp,"bitget_event":be,"kucoin_pre":kp,"kucoin_event":ke,
              "bitget_pass":bo,"kucoin_pass":ko,"selected_venue":venue,
              "status":"SOURCE_COVERAGE_PASS" if venue else "NO_PRIMARY_SOURCE_COVERAGE"})
valid=[r for r in rows if r["status"]=="SOURCE_COVERAGE_PASS"]
print("V04_SOURCE_GATE_BEGIN")
print(json.dumps({"candidate_assets":len(E),"n_valid":len(valid),
 "valid":[{"ticker":r["ticker"],"selected_venue":r["selected_venue"],"t0":r["t0"]} for r in valid],
 "invalid":[r["ticker"] for r in rows if r["status"]!="SOURCE_COVERAGE_PASS"],
 "rows":rows},ensure_ascii=False,indent=2))
print("V04_SOURCE_GATE_END")

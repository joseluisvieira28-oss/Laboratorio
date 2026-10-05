#!/usr/bin/env python3
import json,time,urllib.parse,urllib.request
from datetime import datetime,timezone

E=[
("AIXBT",1736499327639),("CGPT",1736499327639),("COOKIE",1736499327639),
("TRUMP",1737259542151),("1000CHEEMS",1739085031264),("TST",1739085031264),
("SYRUP",1746530720814),("KMNO",1746530720814),("WLFI",1756691345082),
("PUMP",1757590673797),("AVNT",1757908021934),("ASTER",1759736929954),
("GIGGLE",1761361338417),("F",1761361338417),("BANK",1763028026501),("MET",1763028026501),
]
# 2025 stable/fiat-like announcements were excluded mechanically before source scan. F remains identity-ambiguous and is not admissible by ticker alone.
def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV04Source/1.0","Accept":"application/json"})
 try:
  with urllib.request.urlopen(r,timeout=20) as x:return x.status,json.load(x),None
 except urllib.error.HTTPError as e:return e.code,None,e.read().decode("utf-8","replace")[:250]
 except Exception as e:return None,None,repr(e)
def iso(ms):return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()
def kc(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 st,j,err=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 if not isinstance(j,dict):return {"http":st,"error":err,"ts":[]}
 xs=j.get("data") or [];ts=sorted(int(x[0])*1000 for x in xs)
 return {"http":st,"code":j.get("code"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None,"ts":ts}
def bg(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 st,j,err=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 if not isinstance(j,dict):return {"http":st,"error":err,"ts":[]}
 xs=j.get("data") or [];ts=sorted(int(x[0]) for x in xs)
 return {"http":st,"code":j.get("code"),"msg":j.get("msg"),"n":len(ts),"first":iso(ts[0]) if ts else None,"last":iso(ts[-1]) if ts else None,"ts":ts}
def compact(x):
 return {k:v for k,v in x.items() if k!="ts"}
rows=[]
for sym,t0 in E:
 a,b=t0-25*3600000,t0-23*3600000
 c,d=t0-10*60000,t0+10*60000
 kp=kc(sym,a,b);time.sleep(.06);ke=kc(sym,c,d);time.sleep(.06)
 bp=bg(sym,a,b);time.sleep(.06);be=bg(sym,c,d);time.sleep(.06)
 def ok(p,e):
  ts=p.get("ts",[]); es=e.get("ts",[])
  return any(x<=t0-24*3600000 for x in ts) and any(t0-10*60000<=x<t0 for x in es) and any(t0<=x<=t0+5*60000 for x in es)
 ko,bo=ok(kp,ke),ok(bp,be)
 rows.append({"ticker":sym,"t0":iso(t0),"kucoin_pass":ko,"bitget_pass":bo,
              "kucoin_pre":compact(kp),"kucoin_event":compact(ke),
              "bitget_pre":compact(bp),"bitget_event":compact(be)})
print("V04_2025_SOURCE_BEGIN")
print(json.dumps({"n_assets":len(E),
 "kucoin_valid":[r["ticker"] for r in rows if r["kucoin_pass"]],
 "bitget_valid":[r["ticker"] for r in rows if r["bitget_pass"]],
 "union_valid":[r["ticker"] for r in rows if r["kucoin_pass"] or r["bitget_pass"]],
 "rows":rows},indent=2))
print("V04_2025_SOURCE_END")

# trigger after workflow registration

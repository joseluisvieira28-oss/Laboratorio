#!/usr/bin/env python3
import json,statistics,time,urllib.parse,urllib.request
from pathlib import Path

OBS=[
{"ticker":"FLOKI","venue":"BITGET","symbol":"FLOKI","t0":1683285604106},
{"ticker":"PEPE","venue":"BITGET","symbol":"PEPE","t0":1683285604106},
{"ticker":"PENDLE","venue":"BITGET","symbol":"PENDLE","t0":1688365335567},
{"ticker":"ORDI","venue":"BITGET","symbol":"ORDI","t0":1699339453500},
{"ticker":"BLUR","venue":"KUCOIN","symbol":"BLUR","t0":1700806187186},
{"ticker":"1000SATS","venue":"KUCOIN","symbol":"SATS","t0":1702361370579},
{"ticker":"BONK","venue":"BITGET","symbol":"BONK","t0":1702612713180},
{"ticker":"ZKP","venue":"KUCOIN","symbol":"ZKP","t0":1767782346580},
{"ticker":"ROBO","venue":"BITGET","symbol":"ROBO","t0":1772629994452},
{"ticker":"CFG","venue":"KUCOIN","symbol":"CFG","t0":1773656559260},
{"ticker":"XAUT","venue":"BITGET","symbol":"XAUT","t0":1774521928143},
{"ticker":"GENIUS","venue":"BITGET","symbol":"GENIUS","t0":1779434315961},
{"ticker":"AERO","venue":"BITGET","symbol":"AERO","t0":1784273401964},
{"ticker":"牛来","venue":"MEXC","symbol":"牛来","t0":1788953419513},
{"ticker":"HYPE","venue":"BITGET","symbol":"HYPE","t0":1790235038608},
]

def req(u):
 r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLabV09OOS/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)

def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 j=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 return [(int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])) for x in (j.get("data") or [])]

def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 j=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 return [(int(x[0])*1000,float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])) for x in (j.get("data") or [])]

def mexc(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":1000})
 j=req("https://api.mexc.com/api/v3/klines?"+q)
 if not isinstance(j,list):return []
 return [(int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])) for x in j]

FNS={"BITGET":bitget,"KUCOIN":kucoin,"MEXC":mexc}
SPANS={"BITGET":85,"KUCOIN":900,"MEXC":900}

def fetch_range(fn,sym,a,b,span):
 out={};cur=a
 while cur<=b:
  end=min(cur+span*60000,b)
  for x in fn(sym,cur,end):out[x[0]]=x
  if end>=b:break
  nxt=end-2*60000
  cur=nxt if nxt>cur else end+60000
  time.sleep(.025)
 return out

rows=[]
for o in OBS:
 t0=o["t0"];m=(t0//60000)*60000;fn=FNS[o["venue"]]
 try:
  event=fetch_range(fn,o["symbol"],m,m+61*60000,60)
  ent=event.get(m+60000);e5=event.get(m+5*60000);e15=event.get(m+15*60000);e60=event.get(m+60*60000)
  if not ent or not e5:
   rows.append({**o,"status":"EVENT_SOURCE_FAIL","event_n":len(event),"has_entry":bool(ent),"has_h5":bool(e5)});continue
  base_start=m-24*3600000;base_end=m-3600000-60000
  hist=fetch_range(fn,o["symbol"],base_start,base_end,SPANS[o["venue"]])
  ep=ent[1]
  r={**o,"status":"VALID","entry_price":ep,"entry_ts":m+60000,"h5":e5[4]/ep-1}
  w5=[x for ts,x in event.items() if m+60000<=ts<=m+5*60000]
  r["mfe5"]=max((x[2]/ep-1 for x in w5),default=None);r["mae5"]=min((x[3]/ep-1 for x in w5),default=None)
  r["h15"]=e15[4]/ep-1 if e15 else None;r["h60"]=e60[4]/ep-1 if e60 else None
  first=sum(event.get(m+i*60000,(0,0,0,0,0,0))[5] for i in range(5))
  buckets=[]
  for bs in range(m-24*3600000,m-3600000,5*60000):
   buckets.append(sum(hist.get(bs+i*60000,(0,0,0,0,0,0))[5] for i in range(5)))
  medv=statistics.median(buckets) if buckets else 0
  r["baseline_minutes_present"]=sum(1 for ts in hist if m-24*3600000<=ts<m-3600000)
  r["volume_shock_5m"]=first/medv if medv>0 else None
  rows.append(r)
 except Exception as e:rows.append({**o,"status":"TECHNICAL_ERROR","error":repr(e)})

v=[r for r in rows if r["status"]=="VALID" and r.get("volume_shock_5m") is not None]
def med(k):return statistics.median([r[k] for r in v if r.get(k) is not None]) if v else None
n=len(v);hit=sum(r["h5"]>0 for r in v)/n if n else 0
loo=n>1 and all(statistics.median([x["h5"] for j,x in enumerate(v) if j!=i])>0 for i in range(n))
pos=[max(0,r["h5"]) for r in v];conc=max(pos)/sum(pos) if sum(pos)>0 else 1
s={"oos_pool":"2023+2026","n":n,"median_h5":med("h5"),"hit_h5":hit,"median_volume_shock_5m":med("volume_shock_5m"),"loo_positive":loo,"positive_concentration":conc,"median_h15_descriptive":med("h15"),"median_h60_descriptive":med("h60")}
s["gate_components"]={"n":n>=12,"h5":s["median_h5"] is not None and s["median_h5"]>.005,"hit":hit>=.65,"volume":s["median_volume_shock_5m"] is not None and s["median_volume_shock_5m"]>=2,"loo":loo,"concentration":conc<=.35}
s["verdict"]="SURVIVES_SHORT_HORIZON_OOS" if all(s["gate_components"].values()) else ("SOURCE_BLOCKED_SHORT_HORIZON_OOS" if n<12 else "NO_EDGE_SHORT_HORIZON_OOS")
p=Path("research/binance_listing_information_cascade/results_v09_short_horizon_oos");p.mkdir(exist_ok=True)
(p/"events.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2));(p/"summary.json").write_text(json.dumps(s,indent=2))
print("V09_RESULT",json.dumps(s,indent=2));print("EVENTS",json.dumps(rows,ensure_ascii=False,indent=2))

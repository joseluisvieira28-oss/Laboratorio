#!/usr/bin/env python3
import json,statistics,time,urllib.parse,urllib.request
from pathlib import Path

OBS=[
{"ticker":"AIXBT","venue":"KUCOIN","symbol":"AIXBT","t0":1736499327639},
{"ticker":"CGPT","venue":"BITGET","symbol":"CGPT","t0":1736499327639},
{"ticker":"COOKIE","venue":"BITGET","symbol":"COOKIE","t0":1736499327639},
{"ticker":"1000CHEEMS","venue":"BITGET","symbol":"CHEEMS","t0":1739085031264},
{"ticker":"SYRUP","venue":"KUCOIN","symbol":"SYRUP","t0":1746530720814},
{"ticker":"KMNO","venue":"BITGET","symbol":"KMNO","t0":1746530720814},
{"ticker":"PUMP","venue":"BITGET","symbol":"PUMP","t0":1757590673797},
{"ticker":"AVNT","venue":"BITGET","symbol":"AVNT","t0":1757908021934},
{"ticker":"ASTER","venue":"KUCOIN","symbol":"ASTER","t0":1759736929954},
{"ticker":"GIGGLE","venue":"KUCOIN","symbol":"GIGGLE","t0":1761361338417},
{"ticker":"F","venue":"BITGET","symbol":"F","t0":1761361338417},
{"ticker":"BANK","venue":"BITGET","symbol":"BANK","t0":1763028026501},
{"ticker":"MET","venue":"BITGET","symbol":"MET","t0":1763028026501},
]

def req(u):
 r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLabV03Holdout/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)

def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 j=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 if j.get("code")!="00000": return []
 return [(int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])) for x in (j.get("data") or [])]

def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 j=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 if j.get("code")!="200000": return []
 return [(int(x[0])*1000,float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])) for x in (j.get("data") or [])]

def fetch_range(fn,sym,a,b,span_min=85):
 out={};cur=a
 while cur<=b:
  end=min(cur+span_min*60000,b)
  for x in fn(sym,cur,end): out[x[0]]=x
  if end>=b: break
  cur=end-2*60000
  time.sleep(.03)
 return out

def run_one(o):
 t0=o["t0"];m=(t0//60000)*60000;fn=bitget if o["venue"]=="BITGET" else kucoin
 try:
  event=fetch_range(fn,o["symbol"],m-10*60000,m+61*60000,70)
  p0=event.get(m-60000);targets={n:event.get(m+n*60000) for n in [1,5,15,60]}
  if not p0 or not all(targets.values()):
   return {**o,"status":"EVENT_TARGET_SOURCE_FAIL","event_n":len(event),"has_p0":bool(p0),"targets":{str(k):bool(v) for k,v in targets.items()}}
  base_start=m-24*3600000;base_end=m-3600000-60000
  hist=fetch_range(fn,o["symbol"],base_start,base_end,85)
  witness=[ts for ts in hist if ts<=m-24*3600000+10*60000]
  if not witness:return {**o,"status":"BASELINE_SOURCE_FAIL","baseline_n":len(hist)}
  price0=p0[4];r={**o,"status":"VALID","p0":price0,"p0_ts":m-60000}
  for n,b in targets.items():
   r[f"r{n}"]=b[4]/price0-1
   w=[x for ts,x in event.items() if m<=ts<=m+n*60000]
   r[f"mfe{n}"]=max(x[2]/price0-1 for x in w);r[f"mae{n}"]=min(x[3]/price0-1 for x in w)
  first=sum(event.get(m+i*60000,(0,0,0,0,0,0))[5] for i in range(5))
  buckets=[]
  for bs in range(m-24*3600000,m-3600000,5*60000):
   buckets.append(sum(hist.get(bs+i*60000,(0,0,0,0,0,0))[5] for i in range(5)))
  medv=statistics.median(buckets) if buckets else 0
  r["baseline_minutes_present"]=sum(1 for ts in hist if m-24*3600000<=ts<m-3600000)
  r["volume_shock_5m"]=first/medv if medv>0 else None
  return r
 except Exception as e:return {**o,"status":"TECHNICAL_ERROR","error":repr(e)}

rows=[run_one(o) for o in OBS]
v=[r for r in rows if r["status"]=="VALID" and r.get("volume_shock_5m") is not None]
def med(k):return statistics.median([r[k] for r in v]) if v else None
n=len(v);hit=sum(r["r15"]>0 for r in v)/n if n else 0
loo=n>1 and all(statistics.median([x["r15"] for j,x in enumerate(v) if j!=i])>0 for i in range(n))
pos=[max(0,r["r15"]) for r in v];conc=max(pos)/sum(pos) if sum(pos)>0 else 1
s={"holdout":"2025","n":n,"median_r1":med("r1"),"median_r5":med("r5"),"median_r15":med("r15"),"median_r60":med("r60"),"hit_r15":hit,"median_volume_shock_5m":med("volume_shock_5m"),"loo_positive":loo,"positive_concentration":conc}
s["gate_components"]={"n":n>=12,"median_r15":s["median_r15"] is not None and s["median_r15"]>.0075,"hit_r15":hit>=.65,"median_r5":s["median_r5"] is not None and s["median_r5"]>.005,"volume":s["median_volume_shock_5m"] is not None and s["median_volume_shock_5m"]>=2,"loo":loo,"concentration":conc<=.35}
s["verdict"]="SURVIVES_HOLDOUT" if all(s["gate_components"].values()) else ("SOURCE_BLOCKED_HOLDOUT" if n<12 else "NO_EDGE_HOLDOUT")
p=Path("research/binance_listing_information_cascade/results_v03_2025_holdout");p.mkdir(exist_ok=True)
(p/"events.json").write_text(json.dumps(rows,indent=2));(p/"summary.json").write_text(json.dumps(s,indent=2))
print("V03_HOLDOUT_RESULT",json.dumps(s,indent=2));print("V03_HOLDOUT_EVENTS",json.dumps(rows,indent=2))

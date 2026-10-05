#!/usr/bin/env python3
import json,statistics,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path("research/binance_listing_information_cascade")
src=json.loads((ROOT/"results_v03_2025_holdout/events.json").read_text())
OBS=[r for r in src if r.get("status")=="VALID" and r.get("volume_shock_5m") is not None]
def req(u):
 r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLabV08DelayedAudit/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)
def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 j=req("https://api.bitget.com/api/v3/market/history-candles?"+q)
 return {int(x[0]):(float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])) for x in (j.get("data") or [])}
def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 j=req("https://api.kucoin.com/api/v1/market/candles?"+q)
 return {int(x[0])*1000:(float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])) for x in (j.get("data") or [])}
rows=[]
for o in OBS:
 t0=o["t0"];m=(t0//60000)*60000;fn=bitget if o["venue"]=="BITGET" else kucoin
 try:
  d=fn(o["symbol"],m,m+61*60000)
  ent=d.get(m+60000);targets={5:d.get(m+5*60000),15:d.get(m+15*60000),60:d.get(m+60*60000)}
  if not ent or not all(targets.values()):
   rows.append({"ticker":o["ticker"],"status":"SOURCE_FAIL","venue":o["venue"]});continue
  ep=ent[0];r={"ticker":o["ticker"],"venue":o["venue"],"symbol":o["symbol"],"status":"VALID","entry":ep,"volume_shock_5m":o["volume_shock_5m"]}
  for n,b in targets.items():
   r[f"h{n}"]=b[3]/ep-1
   win=[x for ts,x in d.items() if m+60000<=ts<=m+n*60000]
   r[f"mfe{n}"]=max(x[1]/ep-1 for x in win)
   r[f"mae{n}"]=min(x[2]/ep-1 for x in win)
  rows.append(r)
 except Exception as e:rows.append({"ticker":o["ticker"],"status":"TECHNICAL_ERROR","error":repr(e)})
v=[r for r in rows if r["status"]=="VALID"]
def med(k):return statistics.median([r[k] for r in v]) if v else None
n=len(v);hit=sum(r["h15"]>0 for r in v)/n if n else 0
loo=n>1 and all(statistics.median([x["h15"] for j,x in enumerate(v) if j!=i])>0 for i in range(n))
pos=[max(0,r["h15"]) for r in v];conc=max(pos)/sum(pos) if sum(pos)>0 else 1
s={"retrospective":True,"promotion_eligible":False,"n":n,"median_h5":med("h5"),"median_h15":med("h15"),"median_h60":med("h60"),"hit_h15":hit,
"median_volume_shock_5m":med("volume_shock_5m"),"loo_positive":loo,"positive_concentration":conc}
s["gate_components"]={"n":n>=12,"h15":s["median_h15"] is not None and s["median_h15"]>.0075,"hit":hit>=.65,"h5":s["median_h5"] is not None and s["median_h5"]>.005,"volume":s["median_volume_shock_5m"] is not None and s["median_volume_shock_5m"]>=2,"loo":loo,"concentration":conc<=.35}
s["diagnostic_verdict"]="MECHANISM_SURVIVES_RETROSPECTIVE" if all(s["gate_components"].values()) else "MECHANISM_FAILS_RETROSPECTIVE"
p=ROOT/"audits";p.mkdir(exist_ok=True)
(p/"V08_2025_DELAYED_ENTRY_RETROSPECTIVE.json").write_text(json.dumps({"summary":s,"events":rows},indent=2))
print("V08_DELAYED_AUDIT",json.dumps(s,indent=2));print("EVENTS",json.dumps(rows,indent=2))

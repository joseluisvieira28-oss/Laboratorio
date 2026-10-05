#!/usr/bin/env python3
# Post-outcome TECHNICAL/SOURCE diagnostic only.
# Does not compute/print prices, returns, PnL, thresholds, or change V0.3 science.
import json,statistics,time,urllib.parse,urllib.request
EVENTS=[
("AIXBT",1736499327639),("CGPT",1736499327639),("COOKIE",1736499327639),
("SYRUP",1746530720814),("KMNO",1746530720814),("PUMP",1757590673797),
("AVNT",1757908021934),("ASTER",1759736929954),("GIGGLE",1761361338417),
("F",1761361338417),("BANK",1763028026501),("MET",1763028026501)]
BIND={"AIXBT":"KUCOIN","CGPT":"KUCOIN","COOKIE":"KUCOIN","SYRUP":"KUCOIN","KMNO":"KUCOIN",
"PUMP":"KUCOIN","AVNT":"KUCOIN","ASTER":"KUCOIN","GIGGLE":"KUCOIN","F":"KUCOIN","BANK":"BITGET","MET":"KUCOIN"}
def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV04Diag/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=25) as x:return json.load(x)
def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 j=req("https://api.kucoin.com/api/v1/market/candles?"+q);o=[]
 for x in j.get("data") or []:o.append((int(x[0])*1000,float(x[5])))
 return sorted(o)
def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 j=req("https://api.bitget.com/api/v3/market/history-candles?"+q);o=[]
 for x in j.get("data") or []:o.append((int(x[0]),float(x[5])))
 return sorted(o)
def fetch(venue,sym,a,b):
 fn=kucoin if venue=="KUCOIN" else bitget; step=(699 if venue=="KUCOIN" else 89)*60000
 out={};cur=a
 while cur<=b:
  z=min(cur+step,b)
  for x in fn(sym,cur,z):out[x[0]]=x
  cur=z+60000;time.sleep(.04)
 return sorted(out.values())
def ceilmin(x):return ((x+59999)//60000)*60000
rows=[]
for ticker,t0 in EVENTS:
 venue=BIND[ticker]
 try:
  bars=fetch(venue,ticker,t0-24*3600000-10*60000,t0+70*60000)
  floor=(t0//60000)*60000;ceil=ceilmin(t0)
  witness=[x for x in bars if x[0]<=t0-24*3600000]
  near=[x for x in bars if t0-10*60000<=x[0]<floor]
  first5=[x for x in bars if ceil<=x[0]<ceil+5*60000]
  hist=[x for x in bars if t0-24*3600000<=x[0]<t0-3600000]
  chunks=[sum(y[1] for y in hist[i:i+5]) for i in range(0,len(hist)-4,5)]
  medvol=statistics.median(chunks) if chunks else None
  gaps=0
  for a,b in zip(hist,hist[1:]):
   if b[0]-a[0]!=60000:gaps+=1
  rows.append({"ticker":ticker,"venue":venue,"bars":len(bars),"witness":len(witness),"near":len(near),
    "first5":len(first5),"hist_minutes":len(hist),"hist_5m_chunks":len(chunks),"hist_gaps":gaps,
    "baseline_median_volume_positive":bool(medvol and medvol>0),
    "strict_source_ok":bool(witness and near and len(first5)==5),
    "volume_metric_possible":bool(len(first5)==5 and chunks and medvol and medvol>0)})
 except Exception as e:
  rows.append({"ticker":ticker,"venue":venue,"error":type(e).__name__+":"+str(e)[:200]})
print("V04_SOURCE_DIAG_BEGIN")
print(json.dumps(rows,indent=2))
print("V04_SOURCE_DIAG_END")

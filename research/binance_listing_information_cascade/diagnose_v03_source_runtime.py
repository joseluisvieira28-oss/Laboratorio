#!/usr/bin/env python3
# Post-outcome TECHNICAL/SOURCE diagnostic only.
# Does not compute/print prices, returns, PnL, thresholds, or change V0.3 science.
import json,statistics,time,urllib.parse,urllib.request
EVENTS=[
("IMX",1641794176091),("API3",1642746484252),("WOO",1644286833903),("ASTR",1646033043037),
("LDO",1652079437647),("STG",1660889501192),("FLOKI",1683285604106),("PEPE",1683285604106),
("PENDLE",1688365335567),("ORDI",1699339453500),("BLUR",1700806187186),("BONK",1702612713180)]
BIND={"IMX":"KUCOIN","API3":"KUCOIN","WOO":"KUCOIN","ASTR":"KUCOIN","LDO":"BITGET","STG":"KUCOIN",
"FLOKI":"KUCOIN","PEPE":"BITGET","PENDLE":"BITGET","ORDI":"KUCOIN","BLUR":"KUCOIN","BONK":"KUCOIN"}
def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV03Diag/1.0","Accept":"application/json"})
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
 fn=kucoin if venue=="KUCOIN" else bitget; step=(700 if venue=="KUCOIN" else 90)*60000
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
print("V03_SOURCE_DIAG_BEGIN")
print(json.dumps(rows,indent=2))
print("V03_SOURCE_DIAG_END")

#!/usr/bin/env python3
# V0.4.1 source-only Gate probe for SYRUP. Emits no price, return or PnL.
import json,statistics,time,urllib.parse,urllib.request
T0=1746530720814
def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV041Gate/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=25) as x:return json.load(x)
def gate(a,b):
 q=urllib.parse.urlencode({"currency_pair":"SYRUP_USDT","interval":"1m","from":a//1000,"to":b//1000,"limit":1000})
 j=req("https://api.gateio.ws/api/v4/spot/candlesticks?"+q);o=[]
 for x in j or []:
  try:o.append((int(float(x[0]))*1000,float(x[6])))
  except Exception:pass
 return sorted(o)
def fetch(a,b):
 out={};cur=a
 while cur<=b:
  end=min(cur+599*60000,b)
  for x in gate(cur,end):out[x[0]]=x
  cur=end+60000;time.sleep(.06)
 return [out[k] for k in sorted(out)]
floor=(T0//60000)*60000;ceil=((T0+59999)//60000)*60000
bars=fetch(floor-24*3600000-10*60000,floor+10*60000)
witness=[x for x in bars if x[0]<=T0-24*3600000]
near=[x for x in bars if T0-10*60000<=x[0]<floor]
first5=[x for x in bars if ceil<=x[0]<ceil+5*60000]
hist=[x for x in bars if T0-24*3600000<=x[0]<T0-3600000]
chunks=[sum(y[1] for y in hist[i:i+5]) for i in range(0,len(hist)-4,5)]
med=statistics.median(chunks) if chunks else None
gaps=sum(1 for a,b in zip(hist,hist[1:]) if b[0]-a[0]!=60000)
res={"ticker":"SYRUP","venue":"GATE","bars":len(bars),"witness":len(witness),"near":len(near),
"first5":len(first5),"hist_minutes":len(hist),"hist_5m_chunks":len(chunks),"hist_gaps":gaps,
"baseline_median_volume_positive":bool(med and med>0),
"strict_source_ok":bool(witness and near and len(first5)==5),
"volume_metric_possible":bool(len(first5)==5 and chunks and med and med>0)}
print("V041_GATE_SOURCE_BEGIN")
print(json.dumps(res,indent=2))
print("V041_GATE_SOURCE_END")

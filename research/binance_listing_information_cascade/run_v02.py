#!/usr/bin/env python3
import json,statistics,time,urllib.parse,urllib.request
from datetime import datetime,timezone
from pathlib import Path
E=[("PYTH",1706860207072),("RONIN",1707124296210),("AXL",1709277537028),("WIF",1709632897364),("METIS",1710143970976),("BOME",1710581406588),("TAO",1712817838489),("1MBABYDOGE",1726465502167),("CETUS",1730869807602),("ACT",1731303569462),("PNUT",1731303569462),("ORCA",1733474058953)]
A={"1MBABYDOGE":["BABYDOGE","1MBABYDOGE"]}
def req(u):
 r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLab/2.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)
def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 j=req("https://api.bitget.com/api/v3/market/history-candles?"+q);o=[]
 for x in j.get("data") or []:
  o.append((int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
 return sorted(o)
def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 j=req("https://api.kucoin.com/api/v1/market/candles?"+q);o=[]
 for x in j.get("data") or []:
  # time,open,close,high,low,volume,turnover
  o.append((int(x[0])*1000,float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])))
 return sorted(o)
def allbars(fn,sym,t0):
 # <=90m chunks works for Bitget 100 cap and KuCoin
 out={}
 a=t0-24*3600000;b=t0+65*60000
 while a<b:
  z=min(a+90*60000,b)
  for x in fn(sym,a,z):out[x[0]]=x
  a=z+60000;time.sleep(.04)
 return sorted(out.values())
def one(ticker,t0):
 for venue,fn in [("BITGET",bitget),("KUCOIN",kucoin)]:
  for sym in A.get(ticker,[ticker]):
   try:
    bars=allbars(fn,sym,t0)
    minute=(t0//60000)*60000
    pre=[x for x in bars if x[0]<minute]
    witness=[x for x in bars if x[0]<=t0-23*3600000]
    evt=[x for x in bars if minute<=x[0]<=minute+60*60000]
    if not(pre and witness and evt):continue
    p0=pre[-1][4];r={"ticker":ticker,"venue":venue,"symbol":sym,"t0":t0,"p0":p0}
    for n in [1,5,15,60]:
     w=[x for x in evt if x[0]<=minute+n*60000]
     r["r"+str(n)]=w[-1][4]/p0-1 if w else None
     r["mfe"+str(n)]=max((x[2]/p0-1 for x in w),default=None)
     r["mae"+str(n)]=min((x[3]/p0-1 for x in w),default=None)
    first=[x for x in bars if minute<=x[0]<minute+5*60000]
    hist=[x for x in bars if t0-24*3600000<=x[0]<t0-3600000]
    chunks=[sum(x[5] for x in hist[i:i+5]) for i in range(0,len(hist)-4,5)]
    r["volume_shock_5m"]=sum(x[5] for x in first)/statistics.median(chunks) if chunks and statistics.median(chunks)>0 else None
    return r
   except Exception as e: print("ERR",ticker,venue,sym,repr(e))
 return {"ticker":ticker,"status":"SOURCE_FAIL"}
rows=[one(*x) for x in E];v=[x for x in rows if "r15" in x]
med=lambda k:statistics.median([x[k] for x in v])
n=len(v);hit=sum(x["r15"]>0 for x in v)/n if n else 0
loo=n>1 and all(statistics.median([x["r15"] for j,x in enumerate(v) if j!=i])>0 for i in range(n))
pos=[max(0,x["r15"]) for x in v];conc=max(pos)/sum(pos) if sum(pos)>0 else 1
summ={"n":n,"median_r1":med("r1") if n else None,"median_r5":med("r5") if n else None,"median_r15":med("r15") if n else None,"median_r60":med("r60") if n else None,"hit_r15":hit,"median_volume_shock_5m":med("volume_shock_5m") if n else None,"loo_positive":loo,"positive_concentration":conc}
summ["verdict"]="SURVIVES_DISCOVERY" if n>=12 and summ["median_r15"]>.0075 and hit>=.65 and summ["median_r5"]>.005 and summ["median_volume_shock_5m"]>=2 and loo and conc<=.35 else ("SOURCE_BLOCKED" if n<12 else "NO_EDGE_DISCOVERY")
p=Path("research/binance_listing_information_cascade/results_v02");p.mkdir(exist_ok=True)
(p/"summary.json").write_text(json.dumps(summ,indent=2));(p/"events.json").write_text(json.dumps(rows,indent=2))
print("V02_RESULT",json.dumps(summ,indent=2));print("EVENTS",json.dumps(rows,indent=2))

#!/usr/bin/env python3
import json,statistics,time,urllib.parse,urllib.request
from pathlib import Path
E=[("PYTH",1706860207072),("RONIN",1707124296210),("AXL",1709277537028),("WIF",1709632897364),("METIS",1710143970976),("BOME",1710581406588),("TAO",1712817838489),("1MBABYDOGE",1726465502167),("CETUS",1730869807602),("ACT",1731303569462),("PNUT",1731303569462),("ORCA",1733474058953)]
A={"1MBABYDOGE":["BABYDOGE","1MBABYDOGE"]}

def req(u):
 r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLabRemediation/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=20) as x:return json.load(x)

def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 j=req("https://api.bitget.com/api/v3/market/history-candles?"+q);o=[]
 for x in j.get("data") or []:o.append((int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
 return o

def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 j=req("https://api.kucoin.com/api/v1/market/candles?"+q);o=[]
 for x in j.get("data") or []:o.append((int(x[0])*1000,float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])))
 return o

def allbars(fn,sym,t0):
 minute=(t0//60000)*60000
 start=minute-24*3600000
 finish=minute+60*60000
 out={}
 a=start
 while a<=finish:
  b=min(a+89*60000,finish)
  for x in fn(sym,a,b):out[x[0]]=x
  a=b+60000
  time.sleep(.03)
 return [out[k] for k in sorted(out)]

def one(ticker,t0):
 minute=(t0//60000)*60000
 for venue,fn in [("BITGET",bitget),("KUCOIN",kucoin)]:
  for sym in A.get(ticker,[ticker]):
   try:
    bars=allbars(fn,sym,t0);d={x[0]:x for x in bars}
    p0bar=d.get(minute-60000)
    targets={n:d.get(minute+n*60000) for n in [1,5,15,60]}
    witness=d.get(minute-24*3600000)
    if not(p0bar and witness and all(targets.values())):continue
    p0=p0bar[4];r={"ticker":ticker,"venue":venue,"symbol":sym,"t0":t0,"p0":p0}
    for n,b in targets.items():
      r[f"r{n}"]=b[4]/p0-1
      win=[x for x in bars if minute<=x[0]<=minute+n*60000]
      r[f"mfe{n}"]=max(x[2]/p0-1 for x in win)
      r[f"mae{n}"]=min(x[3]/p0-1 for x in win)
    first=[d.get(minute+i*60000) for i in range(5)]
    if not all(first):continue
    hist=[d.get(minute-24*3600000+i*60000) for i in range(23*60)]
    if not all(hist):continue
    chunks=[sum(x[5] for x in hist[i:i+5]) for i in range(0,len(hist),5)]
    base=statistics.median(chunks)
    r["volume_shock_5m"]=sum(x[5] for x in first)/base if base>0 else None
    return r
   except Exception as e: print("ERR",ticker,venue,sym,repr(e))
 return {"ticker":ticker,"status":"SOURCE_FAIL"}

rows=[one(*e) for e in E]
v=[x for x in rows if "r15" in x]
def med(k): return statistics.median([x[k] for x in v]) if v else None
n=len(v);hit=sum(x["r15"]>0 for x in v)/n if n else 0
loo=n>1 and all(statistics.median([x["r15"] for j,x in enumerate(v) if j!=i])>0 for i in range(n))
pos=[max(0,x["r15"]) for x in v];conc=max(pos)/sum(pos) if sum(pos)>0 else 1
s={"technical_remediation":True,"n":n,"median_r1":med("r1"),"median_r5":med("r5"),"median_r15":med("r15"),"median_r60":med("r60"),"hit_r15":hit,"median_volume_shock_5m":med("volume_shock_5m"),"loo_positive":loo,"positive_concentration":conc}
s["verdict"]="SURVIVES_DISCOVERY" if n>=12 and s["median_r15"]>.0075 and hit>=.65 and s["median_r5"]>.005 and s["median_volume_shock_5m"]>=2 and loo and conc<=.35 else ("SOURCE_BLOCKED" if n<12 else "NO_EDGE_DISCOVERY")
p=Path("research/binance_listing_information_cascade/results_v02_remediated");p.mkdir(exist_ok=True)
(p/"events.json").write_text(json.dumps(rows,indent=2));(p/"summary.json").write_text(json.dumps(s,indent=2))
print("REMEDIATED_RESULT",json.dumps(s,indent=2));print("EVENTS",json.dumps(rows,indent=2))

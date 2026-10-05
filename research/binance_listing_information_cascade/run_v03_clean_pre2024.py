#!/usr/bin/env python3
import json,statistics,time,urllib.parse,urllib.request,math
from pathlib import Path

FREEZE_COMMIT="08b83cb2bbf10d3806425c833f648032fcaaee23"
EVENTS=[
("IMX",1641794176091),("API3",1642746484252),("WOO",1644286833903),("ASTR",1646033043037),
("LDO",1652079437647),("STG",1660889501192),("FLOKI",1683285604106),("PEPE",1683285604106),
("PENDLE",1688365335567),("ORDI",1699339453500),("BLUR",1700806187186),("BONK",1702612713180),
]
BIND={
"IMX":"KUCOIN","API3":"KUCOIN","WOO":"KUCOIN","ASTR":"KUCOIN","LDO":"BITGET","STG":"KUCOIN",
"FLOKI":"KUCOIN","PEPE":"BITGET","PENDLE":"BITGET","ORDI":"KUCOIN","BLUR":"KUCOIN","BONK":"KUCOIN"
}
def req(url):
 r=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabV03Frozen/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=25) as x:return json.load(x)

# normalized tuple: ts, open, high, low, close, base_volume
def kucoin(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 j=req("https://api.kucoin.com/api/v1/market/candles?"+q);o=[]
 for x in j.get("data") or []:
  o.append((int(x[0])*1000,float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])))
 return sorted(o)
def bitget(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 j=req("https://api.bitget.com/api/v3/market/history-candles?"+q);o=[]
 for x in j.get("data") or []:
  o.append((int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
 return sorted(o)
def fetch_all(venue,sym,a,b):
 fn=kucoin if venue=="KUCOIN" else bitget
 step=(700 if venue=="KUCOIN" else 90)*60000
 out={};cur=a
 while cur<=b:
  end=min(cur+step,b)
  for x in fn(sym,cur,end): out[x[0]]=x
  cur=end+60000
  time.sleep(.05)
 return sorted(out.values())
def ceil_min(ms): return ((ms+59999)//60000)*60000
def latest_at(bars,ts):
 xs=[x for x in bars if x[0]<=ts]
 return xs[-1] if xs else None
def exact(bars,ts):
 for x in bars:
  if x[0]==ts:return x
 return None
def one(ticker,t0):
 venue=BIND[ticker]
 try:
  bars=fetch_all(venue,ticker,t0-24*3600000-10*60000,t0+70*60000)
  floor=(t0//60000)*60000; ceil=ceil_min(t0)
  pre=[x for x in bars if x[0]<floor]
  witness=[x for x in bars if x[0]<=t0-24*3600000]
  near=[x for x in bars if t0-10*60000<=x[0]<floor]
  if not(pre and witness and near):
   return {"ticker":ticker,"venue":venue,"status":"SOURCE_FAIL_STRICT"}
  p0=pre[-1][4]
  r={"ticker":ticker,"venue":venue,"status":"VALID","t0_ms":t0,"p0":p0}
  for n in [1,5,15,60]:
   end=latest_at(bars,floor+n*60000)
   win=[x for x in bars if floor<=x[0]<=floor+n*60000]
   r[f"r{n}"]=end[4]/p0-1 if end else None
   r[f"mfe{n}"]=max((x[2]/p0-1 for x in win),default=None)
   r[f"mae{n}"]=min((x[3]/p0-1 for x in win),default=None)
  first5=[x for x in bars if ceil<=x[0]<ceil+5*60000]
  hist=[x for x in bars if t0-24*3600000<=x[0]<t0-3600000]
  chunks=[sum(y[5] for y in hist[i:i+5]) for i in range(0,len(hist)-4,5)]
  r["baseline_5m_chunks"]=len(chunks)
  r["volume_shock_5m"]=sum(x[5] for x in first5)/statistics.median(chunks) if len(first5)==5 and chunks and statistics.median(chunks)>0 else None

  # Layer B: at least 60 seconds reaction/latency before entry.
  ent=ceil_min(t0+60000)
  eb=exact(bars,ent)
  r["exec_entry_ts"]=ent
  if eb:
   ep=eb[1];r["exec_entry_price"]=ep
   btc=fetch_all(venue,"BTC",ent-2*60000,ent+65*60000)
   be=exact(btc,ent)
   for n in [5,15,60]:
    target=ent+(n-1)*60000
    xb=exact(bars,target)
    bb=exact(btc,target)
    er=xb[4]/ep-1 if xb else None
    br=bb[4]/be[1]-1 if (bb and be) else None
    r[f"exec_r{n}"]=er
    r[f"exec_r{n}_exbtc"]=er-br if er is not None and br is not None else None
    w=[x for x in bars if ent<=x[0]<=target]
    r[f"exec_mfe{n}"]=max((x[2]/ep-1 for x in w),default=None)
    r[f"exec_mae{n}"]=min((x[3]/ep-1 for x in w),default=None)
  return r
 except Exception as e:
  return {"ticker":ticker,"venue":venue,"status":"SOURCE_RUNTIME_FAIL","error":type(e).__name__+":"+str(e)[:180]}

rows=[one(*x) for x in EVENTS]
v=[x for x in rows if x.get("status")=="VALID" and x.get("r15") is not None and x.get("volume_shock_5m") is not None]
def vals(k):return [x[k] for x in v if x.get(k) is not None]
def med(k):return statistics.median(vals(k)) if vals(k) else None
n=len(v);hit=sum(x["r15"]>0 for x in v)/n if n else 0
loo=n>1 and all(statistics.median([x["r15"] for j,x in enumerate(v) if j!=i])>0 for i in range(n))
pos=[max(0,x["r15"]) for x in v];conc=max(pos)/sum(pos) if sum(pos)>0 else 1
info=(n>=12 and med("r15")>.0075 and hit>=.65 and med("r5")>.005 and
      med("volume_shock_5m")>=2 and loo and conc<=.35)
verdict="SURVIVES_INFORMATION_DISCOVERY" if info else ("SOURCE_BLOCKED" if n<12 else "NO_EDGE_DISCOVERY")
summary={"freeze_commit":FREEZE_COMMIT,"verdict":verdict,"n":n,
 "median_r1":med("r1"),"median_r5":med("r5"),"median_r15":med("r15"),"median_r60":med("r60"),
 "hit_r15":hit,"median_volume_shock_5m":med("volume_shock_5m"),"loo_positive":loo,
 "positive_concentration":conc}
for k in ["exec_r5","exec_r15","exec_r60","exec_r5_exbtc","exec_r15_exbtc","exec_r60_exbtc","exec_mfe15","exec_mae15"]:
 x=vals(k);summary["median_"+k]=statistics.median(x) if x else None
for k in ["exec_r5","exec_r15","exec_r60"]:
 x=vals(k);summary["hit_"+k]=sum(y>0 for y in x)/len(x) if x else None
out=Path("research/binance_listing_information_cascade/results_v03_clean_pre2024");out.mkdir(parents=True,exist_ok=True)
(out/"summary.json").write_text(json.dumps(summary,indent=2))
(out/"events.json").write_text(json.dumps(rows,indent=2))
print("V03_CLEAN_RESULT_BEGIN")
print(json.dumps(summary,indent=2))
print("V03_CLEAN_RESULT_END")

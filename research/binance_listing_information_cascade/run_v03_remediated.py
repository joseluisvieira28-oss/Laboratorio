#!/usr/bin/env python3
import json,statistics,time,urllib.parse,urllib.request
from pathlib import Path
FREEZE="08b83cb2bbf10d3806425c833f648032fcaaee23"
EVENTS=[("IMX",1641794176091),("API3",1642746484252),("WOO",1644286833903),("ASTR",1646033043037),("LDO",1652079437647),("STG",1660889501192),("FLOKI",1683285604106),("PEPE",1683285604106),("PENDLE",1688365335567),("ORDI",1699339453500),("BLUR",1700806187186),("BONK",1702612713180)]
# Pre-outcome source gate pass matrix.
KC_PASS={"IMX","API3","WOO","ASTR","STG","FLOKI","ORDI","BLUR","BONK"}
BG_PASS={"IMX","LDO","LUNA","STG","FLOKI","PEPE","PENDLE","ORDI","BONK"}

def req(u):
 r=urllib.request.Request(u,headers={"User-Agent":"Mozilla/5.0 CryptoLabV03Remediation/1.0","Accept":"application/json"})
 with urllib.request.urlopen(r,timeout=25) as x:return json.load(x)

def kc(sym,a,b):
 q=urllib.parse.urlencode({"symbol":sym+"-USDT","type":"1min","startAt":a//1000,"endAt":b//1000})
 j=req("https://api.kucoin.com/api/v1/market/candles?"+q);o=[]
 for x in j.get("data") or []:o.append((int(x[0])*1000,float(x[1]),float(x[3]),float(x[4]),float(x[2]),float(x[5])))
 return o

def bg(sym,a,b):
 q=urllib.parse.urlencode({"category":"SPOT","symbol":sym+"USDT","interval":"1m","startTime":a,"endTime":b,"limit":100})
 j=req("https://api.bitget.com/api/v3/market/history-candles?"+q);o=[]
 for x in j.get("data") or []:o.append((int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
 return o

def fetch(venue,sym,t0):
 floor=(t0//60000)*60000
 start=floor-24*3600000-10*60000
 finish=floor+70*60000
 out={}
 cur=start
 span=(699 if venue=="KUCOIN" else 89)*60000
 fn=kc if venue=="KUCOIN" else bg
 while cur<=finish:
  end=min(cur+span,finish)
  for x in fn(sym,cur,end):out[x[0]]=x
  cur=end+60000
  time.sleep(.04)
 return [out[k] for k in sorted(out)]

def ceilmin(x):return ((x+59999)//60000)*60000
def exact(bars,ts):
 for x in bars:
  if x[0]==ts:return x
 return None
def latest(bars,ts):
 xs=[x for x in bars if x[0]<=ts]
 return xs[-1] if xs else None

def source_metrics_ok(bars,t0):
 floor=(t0//60000)*60000;ceil=ceilmin(t0)
 witness=[x for x in bars if x[0]<=t0-24*3600000]
 near=[x for x in bars if t0-10*60000<=x[0]<floor]
 first5=[x for x in bars if ceil<=x[0]<ceil+5*60000]
 hist=[x for x in bars if t0-24*3600000<=x[0]<t0-3600000]
 chunks=[sum(y[5] for y in hist[i:i+5]) for i in range(0,len(hist)-4,5)]
 med=statistics.median(chunks) if chunks else None
 return bool(witness and near and len(first5)==5 and chunks and med and med>0),first5,hist,chunks,med

def one(ticker,t0):
 candidates=[]
 if ticker in KC_PASS:candidates.append("KUCOIN")
 if ticker in BG_PASS:candidates.append("BITGET")
 for venue in candidates:
  try:
   bars=fetch(venue,ticker,t0)
   ok,first5,hist,chunks,medv=source_metrics_ok(bars,t0)
   if not ok:continue
   floor=(t0//60000)*60000
   pre=[x for x in bars if x[0]<floor]
   if not pre:continue
   p0=pre[-1][4]
   r={"ticker":ticker,"venue":venue,"status":"VALID","t0_ms":t0,"p0":p0,"baseline_5m_chunks":len(chunks)}
   for n in [1,5,15,60]:
    end=latest(bars,floor+n*60000)
    win=[x for x in bars if floor<=x[0]<=floor+n*60000]
    r[f"r{n}"]=end[4]/p0-1 if end else None
    r[f"mfe{n}"]=max((x[2]/p0-1 for x in win),default=None)
    r[f"mae{n}"]=min((x[3]/p0-1 for x in win),default=None)
   r["volume_shock_5m"]=sum(x[5] for x in first5)/medv
   ent=ceilmin(t0+60000); eb=exact(bars,ent);r["exec_entry_ts"]=ent
   if eb:
    ep=eb[1];r["exec_entry_price"]=ep
    btc=fetch(venue,"BTC",ent)
    be=exact(btc,ent)
    for n in [5,15,60]:
     target=ent+(n-1)*60000;xb=exact(bars,target);bb=exact(btc,target)
     er=xb[4]/ep-1 if xb else None;br=bb[4]/be[1]-1 if (bb and be) else None
     r[f"exec_r{n}"]=er;r[f"exec_r{n}_exbtc"]=er-br if er is not None and br is not None else None
     w=[x for x in bars if ent<=x[0]<=target]
     r[f"exec_mfe{n}"]=max((x[2]/ep-1 for x in w),default=None)
     r[f"exec_mae{n}"]=min((x[3]/ep-1 for x in w),default=None)
   return r
  except Exception as e:
   print("SOURCE_ERR",ticker,venue,type(e).__name__,str(e)[:120])
 return {"ticker":ticker,"status":"SOURCE_FAIL_AFTER_FROZEN_HIERARCHY"}

rows=[one(*x) for x in EVENTS]
v=[x for x in rows if x.get("status")=="VALID" and x.get("r15") is not None and x.get("volume_shock_5m") is not None]
def vals(k):return [x[k] for x in v if x.get(k) is not None]
def med(k):return statistics.median(vals(k)) if vals(k) else None
n=len(v);hit=sum(x["r15"]>0 for x in v)/n if n else 0
loo=n>1 and all(statistics.median([x["r15"] for j,x in enumerate(v) if j!=i])>0 for i in range(n))
pos=[max(0,x["r15"]) for x in v];conc=max(pos)/sum(pos) if sum(pos)>0 else 1
info=n>=12 and med("r15")>.0075 and hit>=.65 and med("r5")>.005 and med("volume_shock_5m")>=2 and loo and conc<=.35
summary={"parent_freeze":FREEZE,"technical_remediation":True,"n":n,"median_r1":med("r1"),"median_r5":med("r5"),"median_r15":med("r15"),"median_r60":med("r60"),"hit_r15":hit,"median_volume_shock_5m":med("volume_shock_5m"),"loo_positive":loo,"positive_concentration":conc,"verdict":"SURVIVES_INFORMATION_DISCOVERY" if info else ("SOURCE_BLOCKED" if n<12 else "NO_EDGE_DISCOVERY")}
for k in ["exec_r5","exec_r15","exec_r60","exec_r5_exbtc","exec_r15_exbtc","exec_r60_exbtc","exec_mfe15","exec_mae15"]:
 x=vals(k);summary["median_"+k]=statistics.median(x) if x else None
for k in ["exec_r5","exec_r15","exec_r60"]:
 x=vals(k);summary["hit_"+k]=sum(y>0 for y in x)/len(x) if x else None
out=Path("research/binance_listing_information_cascade/results_v03_clean_pre2024_remediated");out.mkdir(parents=True,exist_ok=True)
(out/"summary.json").write_text(json.dumps(summary,indent=2));(out/"events.json").write_text(json.dumps(rows,indent=2))
print("V03_REMEDIATED_RESULT_BEGIN");print(json.dumps(summary,indent=2));print("V03_REMEDIATED_RESULT_END")
print("V03_REMEDIATED_EVENTS_BEGIN");print(json.dumps(rows,indent=2));print("V03_REMEDIATED_EVENTS_END")

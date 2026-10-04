#!/usr/bin/env python3
from __future__ import annotations
import requests,json,csv,io,zipfile,math,statistics,time
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
R=json.loads((Path(__file__).resolve().parent/"ASTER_NVDA_PORTABILITY_RULE_V0.2.json").read_text());OUT=Path("artifacts/aster_nvda/v02")
def sec(d,h,m):return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def mean(x):return sum(x)/len(x) if x else None
def sgn(x):return 1 if x>0 else(-1 if x<0 else 0)
def req(url,params=None):
 for i in range(4):
  try:
   r=requests.get(url,params=params,timeout=60)
   if r.status_code==200:return r
  except:pass
  time.sleep(.4*(i+1))
 raise RuntimeError(url)
def sess():
 a=date.fromisoformat(R["start"]);b=date.fromisoformat(R["end"]);ex={date.fromisoformat(x) for x in R["excluded"]};o=[];d=a
 while d<=b:
  if d.weekday()<5 and d not in ex:o.append(d)
  d+=timedelta(days=1)
 return o
def aster(d):
 r=req("https://fapi.asterdex.com/fapi/v3/klines",{"symbol":"NVDAUSDT","interval":"1m","startTime":sec(d,14,20)*1000,"endTime":sec(d,19,10)*1000,"limit":500});o={}
 for x in r.json():
  try:o[int(x[0])//1000+60]=float(x[4])
  except:pass
 return o
def binance(d):
 s="NVDAUSDT";r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{s}/1m/{s}-1m-{d.isoformat()}.zip");z=zipfile.ZipFile(io.BytesIO(r.content));o={}
 for row in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding="utf-8")):
  try:t=int(row[0])//1000;p=float(row[4])
  except:continue
  if sec(d,14,20)<=t<=sec(d,19,10):o[t+60]=p
 return o
def bitget(d):
 o={}
 for a,b in [(sec(d,14,20),sec(d,16,45)),(sec(d,16,46),sec(d,19,10))]:
  j=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":"NVDAUSDT","productType":"USDT-FUTURES","granularity":"1m","startTime":a*1000,"endTime":b*1000,"limit":200}).json()
  for x in j.get("data") or []:
   try:o[int(x[0])//1000+60]=float(x[4])
   except:pass
 return o
def main():
 D={};cov={}
 for d in sess():
  a=aster(d);b=binance(d);g=bitget(d);ds=d.isoformat();c=len(set(a)&set(b)&set(g));cov[ds]=[len(a),len(b),len(g),c]
  if len(a)>=250 and len(b)>=250 and len(g)>=240 and c>=240:D[ds]=(a,b,g)
 vals=[];days=[]
 for ds,(a,b,g) in D.items():
  d=date.fromisoformat(ds);na=sec(d,14,31)
  for t in sorted(set(a)&set(b)&set(g)):
   if t<sec(d,14,31) or t>sec(d,18,44) or t<na:continue
   p=t-60;e=t+60
   if any(z not in q for q in [a,b,g] for z in [p,t]) or e not in a:continue
   ext=(10000*(b[t]/b[p]-1)+10000*(g[t]/g[p]-1))/2;ar=10000*(a[t]/a[p]-1);gap=ext-ar
   if abs(ext)<5 or sgn(gap)!=sgn(ext) or abs(gap)<3:continue
   vals.append(sgn(ext)*10000*(a[e]/a[t]-1));days.append(ds);na=t+60
 n=len(vals);w=sum(x>0 for x in vals);half=n//2;p=sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None;m=mean(vals)
 res={"complete_sessions":len(D),"n":n,"wins":w,"win_rate":w/n if n else None,"signal_sessions":len(set(days)),"mean_gross_bps":m,"median_bps":statistics.median(vals) if vals else None,"halves":[mean(vals[:half]),mean(vals[half:])],"p":p,"net":{str(c):m-c for c in R["costs"]} if vals else {}}
 res["pass"]=bool(len(D)==len(sess()) and n>=30 and res["signal_sessions"]>=12 and m>0 and res["median_bps"]>0 and res["win_rate"]>.5 and all(x>0 for x in res["halves"]) and p<.05)
 res["verdict"]="ASTER_NVDA_PORTABILITY_PASS__EXECUTION_VALIDATION_REQUIRED" if res["pass"] else "ASTER_NVDA_PORTABILITY_FAIL_AT_FROZEN_V02_GATE"
 OUT.mkdir(parents=True,exist_ok=True);(OUT/"ASTER_NVDA_PORTABILITY_CLOSEOUT_V02.json").write_text(json.dumps({"result":res,"coverage":cov,"orders":False,"live_trading":False},indent=2))
 print(json.dumps(res,indent=2))
if __name__=="__main__":main()

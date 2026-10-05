#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_INTRADAY_LARGE_SHOCK_RULE_V1.1.json").read_text())
OUT=Path("artifacts/mexc_global_assets/intraday_large_shock_v11/assets")
UA="CryptoLab-IntradayLargeShock/1.1"
def sec(d,h,m):return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sgn(x):return 1 if x>0 else(-1 if x<0 else 0)
def req(url,params=None,timeout=90):
 for i in range(4):
  try:
   r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
   if r.status_code==200:return r
  except:pass
  time.sleep(.4*(i+1))
 raise RuntimeError(url)
def sessions():
 a=date.fromisoformat(R["sample_start"]);b=date.fromisoformat(R["sample_end_inclusive"]);ex={date.fromisoformat(x) for x in R["excluded_dates"]};o=[];d=a
 while d<=b:
  if d.weekday()<5 and d not in ex:o.append(d)
  d+=timedelta(days=1)
 return o
def mexc(sym,d):
 r=req(f"https://api.mexc.com/api/v1/contract/kline/{sym}",{"interval":"Min1","start":str(sec(d,14,20)),"end":str(sec(d,18,50))});j=r.json();z=j.get("data") or {};o={}
 for t,p in zip(z.get("time") or [],z.get("close") or []):
  try:o[int(t)+60]=float(p)
  except:pass
 return o
def binance(sym,d):
 r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{sym}/1m/{sym}-1m-{d.isoformat()}.zip");z=zipfile.ZipFile(io.BytesIO(r.content));o={}
 for row in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding="utf-8")):
  try:t=int(row[0])//1000;p=float(row[4])
  except:continue
  if sec(d,14,20)<=t<=sec(d,18,50):o[t+60]=p
 return o
def bitget(sym,d):
 o={}
 for a,b in [(sec(d,14,20),sec(d,16,40)),(sec(d,16,41),sec(d,18,50))]:
  j=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":sym,"productType":"USDT-FUTURES","granularity":"1m","startTime":a*1000,"endTime":b*1000,"limit":"200"}).json()
  for x in j.get("data") or []:
   try:o[int(x[0])//1000+60]=float(x[4])
   except:pass
 return o
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--target",required=True);ap.add_argument("--external",required=True);a=ap.parse_args();tr=[];cov={}
 for d in sessions():
  ds=d.isoformat()
  try:m=mexc(a.target,d);b=binance(a.external,d);g=bitget(a.external,d)
  except Exception as e:cov[ds]={"error":str(e)};continue
  cov[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g)};nexta=sec(d,14,31)
  for t in range(sec(d,14,31),sec(d,18,39)+1,60):
   if t<nexta:continue
   p=t-60;e=t+5*60
   if any(z not in q for q in [m,b,g] for z in [p,t]) or e not in m:continue
   er=(10000*(b[t]/b[p]-1)+10000*(g[t]/g[p]-1))/2;mr=10000*(m[t]/m[p]-1);gap=er-mr
   if abs(er)<25 or sgn(gap)!=sgn(er) or abs(gap)<15:continue
   gross=sgn(er)*10000*(m[e]/m[t]-1)
   tr.append({"date":ds,"t":t,"gross_bps":gross,"external_shock_bps":er,"gap_bps":gap});nexta=t+5*60
 OUT.mkdir(parents=True,exist_ok=True);rec={"target":a.target,"external":a.external,"trades":tr,"coverage":cov}
 (OUT/(a.target+".json")).write_text(json.dumps(rec,indent=2,sort_keys=True));print(json.dumps({"target":a.target,"trades":len(tr)},indent=2))
if __name__=="__main__":main()

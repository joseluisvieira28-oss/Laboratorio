#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,math,statistics,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_GLOBALASSET_CASHOPEN_RULE_V0.7.json").read_text())
OUT=Path("artifacts/mexc_global_assets/cashopen_v07/assets")
UA="CryptoLab-CashOpen-V07"
def mean(x):return sum(x)/len(x) if x else None
def med(x):return statistics.median(x) if x else None
def sgn(x):return 1 if x>0 else(-1 if x<0 else 0)
def sec(d,h,m):return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def req(url,params=None,timeout=60,retries=4):
 last=None
 for i in range(retries):
  try:
   r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
   if r.status_code!=200:raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
   return r
  except Exception as e:last=e;time.sleep(.5*(i+1))
 raise last
def sessions():
 a=date.fromisoformat(R["discovery_start_date"]);b=date.fromisoformat(R["discovery_end_date_inclusive"]);ex={date.fromisoformat(x) for x in R["excluded_dates"]};o=[];d=a
 while d<=b:
  if d.weekday()<5 and d not in ex:o.append(d)
  d+=timedelta(days=1)
 return o
def mexc(symbol,d):
 r=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",{"interval":"Min1","start":str(sec(d,13,20)),"end":str(sec(d,14,1))})
 j=r.json();z=j.get("data") or {};o={}
 if j.get("success") is not True:return {}
 for t,p in zip(z.get("time") or [],z.get("close") or []):
  try:o[int(t)+60]=float(p)
  except:pass
 return o
def binance(symbol,d):
 r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{d.isoformat()}.zip",timeout=90)
 z=zipfile.ZipFile(io.BytesIO(r.content));o={}
 for row in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding="utf-8")):
  try:t=int(row[0])//1000;p=float(row[4])
  except:continue
  if sec(d,13,20)<=t<=sec(d,14,1):o[t+60]=p
 return o
def bitget(symbol,d):
 r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(sec(d,13,20)*1000),"endTime":str(sec(d,14,1)*1000),"limit":"100"})
 j=r.json();o={}
 for row in j.get("data") or []:
  try:o[int(row[0])//1000+60]=float(row[4])
  except:pass
 return o
def binom(w,n):return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def halves(v):
 n=len(v);k=n//2
 return [mean(v[:k]),mean(v[k:])] if n>=2 else [None,None]
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--target",required=True);ap.add_argument("--external",required=True);a=ap.parse_args()
 vals=[];basis_abs=[];days=[];cov={}
 for d in sessions():
  ds=d.isoformat()
  try:m=mexc(a.target,d);b=binance(a.external,d);g=bitget(a.external,d)
  except Exception as e:cov[ds]={"error":str(e)};continue
  t29=sec(d,13,29);t59=sec(d,13,59)
  cov[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g),"has_signal":t29 in m and t29 in b and t29 in g and t59 in m}
  if not cov[ds]["has_signal"]:continue
  ext=(b[t29]+g[t29])/2;m29=m[t29];basis=10000*(m29/ext-1);side=-sgn(basis)
  if side==0:continue
  raw=10000*(m[t59]/m29-1);vals.append(side*raw);basis_abs.append(abs(basis));days.append(ds)
 n=len(vals);w=sum(x>0 for x in vals);h=halves(vals);mg=mean(vals)
 res={"target":a.target,"external":a.external,"n":n,"wins":w,"win_rate":w/n if n else None,"mean_gross_bps":mg,"median_gross_bps":med(vals),
 "half_means_bps":h,"p":binom(w,n),"mean_abs_basis_bps":mean(basis_abs),"net":{str(c):(mg-c if mg is not None else None) for c in R["cost_scenarios_roundtrip_bps"]},
 "complete_signal_sessions":len(days),"coverage":cov}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/(a.target+".json")).write_text(json.dumps(res,indent=2,sort_keys=True));print(json.dumps(res,indent=2))
if __name__=="__main__":main()

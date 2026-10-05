#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_CASHOPEN_EXTMOM_RULE_V1.2.json").read_text())
OUT=Path("artifacts/mexc_global_assets/cashopen_extmom_v12/assets")
UA="CryptoLab-CashOpen-ExtMom/1.2"
def sec(d,h,m):return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sgn(x):return 1 if x>0 else(-1 if x<0 else 0)
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
 a=date.fromisoformat(R["sample_start"]);b=date.fromisoformat(R["sample_end_inclusive"]);ex={date.fromisoformat(x) for x in R["excluded_dates"]};o=[];d=a
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
 z=zipfile.ZipFile(io.BytesIO(r.content));names=z.namelist()
 if len(names)!=1:raise RuntimeError("BINANCE_ZIP_IDENTITY")
 o={}
 for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
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
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--target",required=True);ap.add_argument("--external",required=True);a=ap.parse_args()
 obs=[];cov={}
 for d in sessions():
  ds=d.isoformat()
  try:m=mexc(a.target,d);b=binance(a.external,d);g=bitget(a.external,d)
  except Exception as e:cov[ds]={"error":str(e)};continue
  t24=sec(d,13,24);t29=sec(d,13,29);t59=sec(d,13,59)
  ok=all(t in m for t in [t29,t59]) and all(t in b for t in [t24,t29]) and all(t in g for t in [t24,t29])
  cov[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g),"ok":ok}
  if not ok:continue
  ext24=(b[t24]+g[t24])/2;ext29=(b[t29]+g[t29])/2
  mom=10000*(ext29/ext24-1);side=sgn(mom)
  if side==0:continue
  raw=10000*(m[t59]/m[t29]-1);signed=side*raw
  obs.append({"date":ds,"external_momentum_5m_bps":mom,"side":side,"mexc_raw_30m_bps":raw,"signed_gross_bps":signed})
 rec={"target":a.target,"external":a.external,"observations":obs,"coverage":cov,"outcomes_opened_post_freeze":True,
      "private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading_authorized":False}
 OUT.mkdir(parents=True,exist_ok=True);(OUT/(a.target+".json")).write_text(json.dumps(rec,indent=2,sort_keys=True))
 print(json.dumps({"target":a.target,"observation_count":len(obs)},indent=2))
if __name__=="__main__":main()

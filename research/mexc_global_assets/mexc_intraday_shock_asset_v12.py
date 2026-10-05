#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_INTRADAY_SHOCK_RULE_V1.2.json").read_text())
OUT=Path("artifacts/mexc_global_assets/intraday_shock_v12/assets")
UA="CryptoLab-IntradayShock/1.2"
def sec(d,h,m):return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sgn(x):return 1 if x>0 else(-1 if x<0 else 0)
def req(url,params=None,timeout=70,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
            return r
        except Exception as e:last=e;time.sleep(.5*(i+1))
    raise last
def sessions():
    a=date.fromisoformat(R["sample_start"]);b=date.fromisoformat(R["sample_end_inclusive"]);ex={date.fromisoformat(x) for x in R["excluded_dates"]};o=[];d=a
    while d<=b:
        if d.weekday()<5 and d not in ex:o.append(d)
        d+=timedelta(days=1)
    return o
def mexc(sym,d):
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{sym}",{"interval":"Min1","start":str(sec(d,14,29)),"end":str(sec(d,18,50))})
    j=r.json();z=j.get("data") or {};o={}
    if j.get("success") is not True:return o
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try:o[int(t)+60]=float(p)
        except:pass
    return o
def binance(sym,d):
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{sym}/1m/{sym}-1m-{d.isoformat()}.zip",timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content));o={}
    for row in csv.reader(io.TextIOWrapper(z.open(z.namelist()[0]),encoding="utf-8")):
        try:t=int(row[0])//1000;p=float(row[4])
        except:continue
        if sec(d,14,29)<=t<=sec(d,18,50):o[t+60]=p
    return o
def bitget(sym,d):
    o={}
    for a,b in [(sec(d,14,29),sec(d,16,44)),(sec(d,16,45),sec(d,18,50))]:
        j=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":sym,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"}).json()
        for row in j.get("data") or []:
            try:o[int(row[0])//1000+60]=float(row[4])
            except:pass
    return o
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--target",required=True);ap.add_argument("--external",required=True);a=ap.parse_args()
    events=[];coverage={}
    for d in sessions():
        ds=d.isoformat()
        try:m=mexc(a.target,d);b=binance(a.external,d);g=bitget(a.external,d)
        except Exception as e:coverage[ds]={"error":str(e)};continue
        common=set(m)&set(b)&set(g);coverage[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g),"common":len(common)}
        start=sec(d,14,35);stop=sec(d,18,39);next_allowed=start
        for t in sorted(common):
            if t<start or t>stop or t<next_allowed:continue
            p=t-300;e=t+300
            if p not in m or p not in b or p not in g or e not in m:continue
            er=(10000*(b[t]/b[p]-1)+10000*(g[t]/g[p]-1))/2
            mr=10000*(m[t]/m[p]-1);gap=er-mr
            if abs(er)<30 or sgn(gap)!=sgn(er) or abs(gap)<20:continue
            gross=sgn(er)*10000*(m[e]/m[t]-1)
            events.append({"date":ds,"t":t,"gross_bps":gross,"external_5m_bps":er,"mexc_5m_bps":mr,"gap_bps":gap})
            next_allowed=t+300
    OUT.mkdir(parents=True,exist_ok=True)
    rec={"target":a.target,"external":a.external,"events":events,"event_count":len(events),"coverage":coverage,"orders":False,"live_trading":False}
    (OUT/(a.target+".json")).write_text(json.dumps(rec,indent=2,sort_keys=True))
    print(json.dumps({"target":a.target,"event_count":len(events)},indent=2))
if __name__=="__main__":main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_SESSION_SHOCK_NEWASSETS_RULE_V1.5.json").read_text())
OUT=Path("artifacts/mexc_global_assets/session_shock_newassets_v15/assets")
UA="CryptoLab-SessionShock-NewAssets/1.5"
def sec(d,h,m):return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sgn(x):return 1 if x>0 else(-1 if x<0 else 0)
def req(url,params=None,timeout=70,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200:raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
            return r
        except Exception as e:last=e;time.sleep(.5*(i+1))
    raise last
def sessions():
    a=date.fromisoformat(R["sample_start"]);b=date.fromisoformat(R["sample_end_inclusive"]);ex={date.fromisoformat(x) for x in R["excluded_dates"]}
    o=[];d=a
    while d<=b:
        if d.weekday()<5 and d not in ex:o.append(d)
        d+=timedelta(days=1)
    return o
def mexc(sym,d):
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{sym}",{"interval":"Min1","start":str(sec(d,14,25)),"end":str(sec(d,18,45))})
    j=r.json();z=j.get("data") or {};o={}
    if j.get("success") is not True:return {}
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
        if sec(d,14,25)<=t<=sec(d,18,45):o[t+60]=p
    return o
def bitget(sym,d):
    o={}
    for a,b in [(sec(d,14,25),sec(d,16,35)),(sec(d,16,36),sec(d,18,45))]:
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
        coverage[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g)}
        for t in sorted(set(m)&set(b)&set(g)):
            if t<sec(d,14,35) or t>sec(d,18,39):continue
            p=t-300;e=t+300
            if p not in m or p not in b or p not in g or e not in m:continue
            eb=10000*(b[t]/b[p]-1);eg=10000*(g[t]/g[p]-1);ext=(eb+eg)/2
            mr=10000*(m[t]/m[p]-1);gap=ext-mr
            if abs(ext)<50 or sgn(gap)!=sgn(ext) or abs(gap)<25:continue
            gross=sgn(ext)*10000*(m[e]/m[t]-1)
            events.append({"timestamp":t,"date":ds,"target":a.target,"external":a.external,"external_5m_bps":ext,"mexc_5m_bps":mr,"lag_gap_bps":gap,"gross_bps":gross})
        time.sleep(.02)
    OUT.mkdir(parents=True,exist_ok=True)
    rec={"target":a.target,"external":a.external,"events":events,"event_count":len(events),"coverage":coverage,"orders":False,"live_trading":False}
    (OUT/(a.target+".json")).write_text(json.dumps(rec,indent=2,sort_keys=True))
    print(json.dumps({"target":a.target,"event_count":len(events)},indent=2))
if __name__=="__main__":main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_PREOPEN_SHOCK_RULE_V1.1.json").read_text())
OUT=Path("artifacts/mexc_global_assets/preopen_shock_v11/assets")
UA="CryptoLab-PreopenShock-V1.1"

def sec(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sgn(x): return 1 if x>0 else(-1 if x<0 else 0)

def req(url,params=None,timeout=70,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
            return r
        except Exception as e:
            last=e; time.sleep(.6*(i+1))
    raise last

def sessions():
    a=date.fromisoformat(R["sample_start"]); b=date.fromisoformat(R["sample_end_inclusive"])
    ex={date.fromisoformat(x) for x in R["excluded_dates"]}; out=[]; d=a
    while d<=b:
        if d.weekday()<5 and d not in ex: out.append(d)
        d+=timedelta(days=1)
    return out

def fetch_mexc(symbol,d):
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",{
      "interval":"Min1","start":str(sec(d,12,20)),"end":str(sec(d,13,40))})
    j=r.json(); z=j.get("data") or {}; out={}
    if j.get("success") is not True:return out
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try:out[int(t)+60]=float(p)
        except:pass
    return out

def fetch_binance(symbol,d):
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{d.isoformat()}.zip",timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1:raise RuntimeError("BINANCE_ZIP_IDENTITY")
    out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:t=int(row[0])//1000;p=float(row[4])
        except:continue
        if sec(d,12,20)<=t<=sec(d,13,40):out[t+60]=p
    return out

def fetch_bitget(symbol,d):
    r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
      "symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m",
      "startTime":str(sec(d,12,20)*1000),"endTime":str(sec(d,13,40)*1000),"limit":"100"})
    j=r.json(); out={}
    if j.get("code")!="00000":return out
    for row in j.get("data") or []:
        try:out[int(row[0])//1000+60]=float(row[4])
        except:pass
    return out

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--target",required=True);ap.add_argument("--external",required=True);a=ap.parse_args()
    events=[]; coverage={}
    for d in sessions():
        ds=d.isoformat()
        try:m=fetch_mexc(a.target,d);b=fetch_binance(a.external,d);g=fetch_bitget(a.external,d)
        except Exception as e:
            coverage[ds]={"error":str(e)};continue
        t0=sec(d,12,29);t1=sec(d,13,29);te=sec(d,13,34)
        needed=all(t in m for t in [t0,t1,te]) and all(t in b for t in [t0,t1]) and all(t in g for t in [t0,t1])
        coverage[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g),"exact_points_ok":needed}
        if not needed:continue
        rb=10000*(b[t1]/b[t0]-1); rg=10000*(g[t1]/g[t0]-1); ext=(rb+rg)/2
        rm=10000*(m[t1]/m[t0]-1); gap=ext-rm
        trig=(abs(ext)>=R["trigger"]["abs_external_60m_return_gte_bps"] and
              sgn(gap)==sgn(ext) and abs(gap)>=R["trigger"]["abs_lag_gap_gte_bps"])
        rec={"date":ds,"external_60m_bps":ext,"mexc_60m_bps":rm,"lag_gap_bps":gap,"triggered":trig}
        if trig:
            side=sgn(ext)
            gross=side*10000*(m[te]/m[t1]-1)
            rec.update({"side":side,"gross_signed_bps":gross,
                        "net_bps":{str(c):gross-float(c) for c in R["cost_scenarios_roundtrip_bps"]}})
        events.append(rec)
    receipt={"target":a.target,"external":a.external,"events":events,"coverage":coverage,
             "trigger_count":sum(1 for x in events if x["triggered"]),
             "orders":False,"account_reads":False,"private_endpoints_used":False,"live_trading":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(a.target+".json")).write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print(json.dumps({"target":a.target,"trigger_count":receipt["trigger_count"],
      "trigger_dates":[x["date"] for x in events if x["triggered"]]},indent=2))
if __name__=="__main__":main()

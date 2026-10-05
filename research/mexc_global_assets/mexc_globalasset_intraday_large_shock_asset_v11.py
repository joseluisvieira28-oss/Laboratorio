#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_GLOBALASSET_INTRADAY_LARGE_SHOCK_RULE_V1.1.json").read_text())
OUT=Path("artifacts/mexc_global_assets/intraday_large_shock_v11/assets")
UA="CryptoLab-IntradayLargeShock-V1.1"

def sec(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sgn(x): return 1 if x>0 else(-1 if x<0 else 0)

def req(url,params=None,timeout=80,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
            return r
        except Exception as e:
            last=e; time.sleep(.5*(i+1))
    raise last

def sessions():
    a=date.fromisoformat(R["sample_start"]); b=date.fromisoformat(R["sample_end_inclusive"])
    ex={date.fromisoformat(x) for x in R["excluded_dates"]}; out=[]; d=a
    while d<=b:
        if d.weekday()<5 and d not in ex: out.append(d)
        d+=timedelta(days=1)
    return out

def fetch_mexc(symbol,d):
    out={}
    start=sec(d,13,25); finish=sec(d,20,5); cur=start
    while cur<finish:
        end=min(cur+170*60,finish)
        r=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",
              {"interval":"Min1","start":str(cur),"end":str(end)})
        j=r.json(); z=j.get("data") or {}
        if j.get("success") is not True: raise RuntimeError("MEXC_SUCCESS_FALSE")
        for t,p in zip(z.get("time") or [],z.get("close") or []):
            try:out[int(t)+60]=float(p)
            except:pass
        cur=end
    return out

def fetch_binance(symbol,d):
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{d.isoformat()}.zip",timeout=100)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1:raise RuntimeError("BINANCE_ZIP_IDENTITY")
    out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:t=int(row[0])//1000;p=float(row[4])
        except:continue
        out[t+60]=p
    return out

def fetch_bitget(symbol,d):
    out={}; cur=sec(d,13,25); finish=sec(d,20,5)
    while cur<finish:
        end=min(cur+90*60,finish)
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(cur*1000),"endTime":str(end*1000),"limit":"100"})
        j=r.json()
        if j.get("code")!="00000":raise RuntimeError("BITGET_CODE_"+str(j.get("code")))
        for row in j.get("data") or []:
            try:out[int(row[0])//1000+60]=float(row[4])
            except:pass
        cur=end; time.sleep(.02)
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--target",required=True)
    ap.add_argument("--external-binance",required=True)
    ap.add_argument("--external-bitget",required=True)
    a=ap.parse_args()
    raw=[]; coverage={}
    for d in sessions():
        ds=d.isoformat()
        try:m=fetch_mexc(a.target,d);b=fetch_binance(a.external_binance,d);g=fetch_bitget(a.external_bitget,d)
        except Exception as e:
            coverage[ds]={"error":str(e)};continue
        coverage[ds]={"mexc":sum(sec(d,13,30)<=t<=sec(d,20,0) for t in m),
                      "binance":sum(sec(d,13,30)<=t<=sec(d,20,0) for t in b),
                      "bitget":sum(sec(d,13,30)<=t<=sec(d,20,0) for t in g)}
        t=sec(d,13,45); end=sec(d,19,55)
        while t<=end:
            t0=t-15*60; te=t+5*60
            need=all(x in m for x in (t0,t,te)) and all(x in b for x in (t0,t)) and all(x in g for x in (t0,t))
            if need:
                rb=10000*(b[t]/b[t0]-1); rg=10000*(g[t]/g[t0]-1); ext=(rb+rg)/2
                rm=10000*(m[t]/m[t0]-1); gap=ext-rm
                trig=(sgn(rb)==sgn(rg) and sgn(rb)!=0 and
                      abs(rb)>=R["trigger"]["abs_each_leader_15m_return_gte_bps"] and
                      abs(rg)>=R["trigger"]["abs_each_leader_15m_return_gte_bps"] and
                      abs(ext)>=R["trigger"]["abs_external_mean_15m_return_gte_bps"] and
                      sgn(gap)==sgn(ext) and abs(gap)>=R["trigger"]["abs_lag_gap_gte_bps"])
                if trig:
                    side=sgn(ext)
                    gross=side*10000*(m[te]/m[t]-1)
                    raw.append({"date":ds,"timestamp":t,"signal_utc":datetime.fromtimestamp(t,timezone.utc).isoformat(),
                                "binance_15m_bps":rb,"bitget_15m_bps":rg,"external_15m_bps":ext,
                                "mexc_15m_bps":rm,"lag_gap_bps":gap,"side":side,"gross_signed_bps":gross})
            t+=60
    rec={"target":a.target,"external_binance":a.external_binance,"external_bitget":a.external_bitget,
         "raw_triggers":raw,"raw_trigger_count":len(raw),"coverage":coverage,
         "orders":False,"account_reads":False,"private_endpoints_used":False,"live_trading":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(a.target+".json")).write_text(json.dumps(rec,indent=2,sort_keys=True))
    print(json.dumps({"target":a.target,"raw_trigger_count":len(raw)},sort_keys=True))

if __name__=="__main__":main()

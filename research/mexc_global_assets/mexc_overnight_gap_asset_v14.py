#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,io,json,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_OVERNIGHT_GAP_RULE_V1.4.json").read_text())
OUT=Path("artifacts/mexc_global_assets/overnight_gap_v14/assets")
UA="CryptoLab-OvernightGap/1.4"

def sec(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
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

def current_sessions():
    a=date.fromisoformat(R["sample_start"]); b=date.fromisoformat(R["sample_end_inclusive"])
    ex={date.fromisoformat(x) for x in R["excluded_current_dates"]}
    out=[]; d=a
    while d<=b:
        if d.weekday()<5 and d not in ex: out.append(d)
        d+=timedelta(days=1)
    return out

def prev_weekday(d):
    p=d-timedelta(days=1)
    while p.weekday()>=5: p-=timedelta(days=1)
    return p

def mexc_window(symbol,d,h0,m0,h1,m1):
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",
          {"interval":"Min1","start":str(sec(d,h0,m0)),"end":str(sec(d,h1,m1))})
    j=r.json(); z=j.get("data") or {}; out={}
    if j.get("success") is not True: return {}
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try: out[int(t)+60]=float(p)
        except: pass
    return out

def binance_window(symbol,d,h0,m0,h1,m1):
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{d.isoformat()}.zip",timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1: raise RuntimeError("BINANCE_ZIP_IDENTITY")
    lo=sec(d,h0,m0); hi=sec(d,h1,m1); out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try: t=int(row[0])//1000; px=float(row[4])
        except: continue
        if lo<=t<=hi: out[t+60]=px
    return out

def bitget_window(symbol,d,h0,m0,h1,m1):
    r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
      "symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m",
      "startTime":str(sec(d,h0,m0)*1000),"endTime":str(sec(d,h1,m1)*1000),"limit":"100"})
    j=r.json(); out={}
    if j.get("code")!="00000": return out
    for row in j.get("data") or []:
        try: out[int(row[0])//1000+60]=float(row[4])
        except: pass
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--target",required=True); ap.add_argument("--external",required=True)
    a=ap.parse_args()
    obs=[]; coverage={}
    for cur in current_sessions():
        prev=prev_weekday(cur); ds=cur.isoformat()
        try:
            mp=mexc_window(a.target,prev,19,50,20,5)
            mc=mexc_window(a.target,cur,13,20,14,5)
            bp=binance_window(a.external,prev,19,50,20,5)
            bc=binance_window(a.external,cur,13,20,14,5)
            gp=bitget_window(a.external,prev,19,50,20,5)
            gc=bitget_window(a.external,cur,13,20,14,5)
        except Exception as e:
            coverage[ds]={"prev":prev.isoformat(),"error":str(e)}
            continue
        tprev=sec(prev,20,0); tsig=sec(cur,13,29); texit=sec(cur,13,59)
        ok=(tprev in mp and tprev in bp and tprev in gp and tsig in mc and tsig in bc and tsig in gc and texit in mc)
        coverage[ds]={"prev":prev.isoformat(),"mexc_prev":len(mp),"mexc_cur":len(mc),
                      "bin_prev":len(bp),"bin_cur":len(bc),"bit_prev":len(gp),"bit_cur":len(gc),"ok":ok}
        if not ok: continue
        ext_prev=(bp[tprev]+gp[tprev])/2
        ext_cur=(bc[tsig]+gc[tsig])/2
        er=10000*(ext_cur/ext_prev-1)
        mr=10000*(mc[tsig]/mp[tprev]-1)
        gap=er-mr
        T=R["trigger"]
        if abs(er)<T["abs_external_overnight_return_gte_bps"]: continue
        if sgn(gap)!=sgn(er): continue
        if abs(gap)<T["abs_lag_gap_gte_bps"]: continue
        side=sgn(er)
        gross=side*10000*(mc[texit]/mc[tsig]-1)
        obs.append({"date":ds,"previous_session":prev.isoformat(),
                    "external_overnight_return_bps":er,"mexc_overnight_return_bps":mr,
                    "lag_gap_bps":gap,"side":side,"signed_gross_30m_bps":gross})
        time.sleep(.02)
    rec={"target":a.target,"external":a.external,"triggered_observations":obs,"coverage":coverage,
         "private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading_authorized":False}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(a.target+".json")).write_text(json.dumps(rec,indent=2,sort_keys=True))
    print(json.dumps({"target":a.target,"triggered":len(obs),"trigger_days":[x["date"] for x in obs]},indent=2))

if __name__=="__main__": main()

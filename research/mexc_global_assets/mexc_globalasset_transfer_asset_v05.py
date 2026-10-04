#!/usr/bin/env python3
"""Evaluate one frozen V0.5 MEXC global-asset transfer candidate."""
from __future__ import annotations
import argparse,csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE=json.loads((HERE/"MEXC_GLOBALASSET_TRANSFER_RULE_V0.5.json").read_text())
OUT=Path("artifacts/mexc_global_assets/globalasset_transfer_v05/assets")
UA="CryptoLab-GlobalAsset-Transfer/0.5"

def h(b):return hashlib.sha256(b).hexdigest()
def mean(x):return sum(x)/len(x) if x else None
def med(x):return statistics.median(x) if x else None
def sgn(x):return 1 if x>0 else (-1 if x<0 else 0)
def sec(d,hh,mm):return int(datetime(d.year,d.month,d.day,hh,mm,tzinfo=timezone.utc).timestamp())
def sessions():
    a=date.fromisoformat(RULE["discovery_start_date"]);b=date.fromisoformat(RULE["discovery_end_date_inclusive"])
    ex={date.fromisoformat(x) for x in RULE["excluded_dates"]};out=[];d=a
    while d<=b:
        if d.weekday()<5 and d not in ex:out.append(d)
        d+=timedelta(days=1)
    return out
def req(url,params=None,timeout=70,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200:raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
            return r
        except Exception as e:
            last=e;time.sleep(.7*(i+1))
    raise last
def mexc(symbol,d):
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",{"interval":"Min1","start":str(sec(d,14,29)),"end":str(sec(d,18,59))})
    j=r.json();z=j.get("data") or {};out={}
    if j.get("success") is not True:return {},h(r.content)
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try:out[int(t)+60]=float(p)
        except:pass
    return out,h(r.content)
def binance(symbol,d):
    day=d.isoformat()
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{day}.zip",timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content));names=z.namelist()
    if len(names)!=1:raise RuntimeError("BINANCE_ZIP_IDENTITY")
    lo=sec(d,14,29);hi=sec(d,18,59);out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:t=int(row[0])//1000;p=float(row[4])
        except:continue
        if lo<=t<=hi:out[t+60]=p
    return out,h(r.content)
def bitget(symbol,d):
    out={};hs=[]
    for a,b in [(sec(d,14,29),sec(d,16,44)),(sec(d,16,45),sec(d,18,59))]:
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
        hs.append(h(r.content));j=r.json()
        if j.get("code")!="00000":continue
        for row in j.get("data") or []:
            try:out[int(row[0])//1000+60]=float(row[4])
            except:pass
    return out,hs
def binom(w,n):
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def thirds(v):
    n=len(v)
    if not n:return [None,None,None]
    c=[0,n//3,(2*n)//3,n]
    return [mean(v[c[i]:c[i+1]]) for i in range(3)]
def score(D):
    R=RULE["rule"];vals=[];days=[];exts=[];gaps=[]
    for ds,X in D.items():
        d=date.fromisoformat(ds);start=sec(d,14,31);stop=sec(d,18,44);next_allowed=start
        for t in sorted(set(X["mexc"])&set(X["binance"])&set(X["bitget"])):
            if t<start or t>stop or t<next_allowed:continue
            prev=t-60;ex=t+R["horizon_min"]*60
            if prev not in X["mexc"] or prev not in X["binance"] or prev not in X["bitget"] or ex not in X["mexc"]:continue
            rb=10000*(X["binance"][t]/X["binance"][prev]-1)
            rg=10000*(X["bitget"][t]/X["bitget"][prev]-1)
            er=(rb+rg)/2
            mr=10000*(X["mexc"][t]/X["mexc"][prev]-1)
            gap=er-mr
            if abs(er)<R["shock_threshold_bps"] or sgn(gap)!=sgn(er) or abs(gap)<R["lag_gap_threshold_bps"]:continue
            gross=sgn(er)*10000*(X["mexc"][ex]/X["mexc"][t]-1)
            vals.append(gross);days.append(ds);exts.append(er);gaps.append(gap)
            next_allowed=t+R["cooldown_min"]*60
    n=len(vals);wins=sum(x>0 for x in vals)
    m=mean(vals)
    return {"n":n,"wins":wins,"losses_or_zero":n-wins,"win_rate":wins/n if n else None,
      "distinct_signal_sessions":len(set(days)),"mean_gross_signed_bps":m,
      "median_gross_signed_bps":med(vals),"chronological_third_means_bps":thirds(vals),
      "p_value_one_sided_binomial_vs_50":binom(wins,n),
      "mean_abs_external_shock_bps":mean([abs(x) for x in exts]) if exts else None,
      "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]) if gaps else None,
      "mean_net_bps":{str(c):(m-c if m is not None else None) for c in RULE["cost_scenarios_roundtrip_bps"]}}
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--target",required=True);ap.add_argument("--external",required=True);a=ap.parse_args()
    ss=sessions()
    if len(ss)!=17:raise SystemExit("FAIL_CLOSED_SESSION_COUNT")
    D={};coverage={};hashes={}
    for d in ss:
        ds=d.isoformat()
        try:
            m,mh=mexc(a.target,d);b,bh=binance(a.external,d);g,gh=bitget(a.external,d)
        except Exception as e:
            coverage[ds]={"error":str(e)};continue
        common=len(set(m)&set(b)&set(g))
        coverage[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g),"common":common}
        hashes[ds]={"mexc":mh,"binance":bh,"bitget":gh}
        if len(m)>=260 and len(b)>=260 and len(g)>=240 and common>=250:D[ds]={"mexc":m,"binance":b,"bitget":g}
        time.sleep(.02)
    result=score(D) if len(D)==17 else None
    receipt={"target":a.target,"external":a.external,"complete_sessions":len(D),"source_complete":len(D)==17,
             "result":result,"coverage":coverage,"source_hashes":hashes,"post_outcome_tuning":False,
             "private_endpoints_used":False,"account_reads":False,"orders":False,"live_trading_authorized":False}
    OUT.mkdir(parents=True,exist_ok=True)
    p=OUT/(a.target+".json");p.write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print(json.dumps({"target":a.target,"external":a.external,"complete_sessions":len(D),
      "n":result["n"] if result else None,"mean":result["mean_gross_signed_bps"] if result else None,
      "p":result["p_value_one_sided_binomial_vs_50"] if result else None},indent=2))
if __name__=="__main__":main()

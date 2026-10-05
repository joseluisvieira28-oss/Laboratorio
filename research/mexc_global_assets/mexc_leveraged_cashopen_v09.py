#!/usr/bin/env python3
from __future__ import annotations
import csv,io,json,math,statistics,time,zipfile
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests
HERE=Path(__file__).resolve().parent
R=json.loads((HERE/"MEXC_LEVERAGED_CASHOPEN_RULE_V0.9.json").read_text())
OUT=Path("artifacts/mexc_global_assets/leveraged_cashopen_v09")
UA="CryptoLab-Leveraged-CashOpen/0.9"

def mean(x): return sum(x)/len(x) if x else None
def med(x): return statistics.median(x) if x else None
def sgn(x): return 1 if x>0 else(-1 if x<0 else 0)
def sec(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())
def req(url,params=None,timeout=60,retries=4):
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
    a=date.fromisoformat(R["start"]); b=date.fromisoformat(R["end"]); ex={date.fromisoformat(x) for x in R["excluded"]}
    out=[]; d=a
    while d<=b:
        if d.weekday()<5 and d not in ex: out.append(d)
        d+=timedelta(days=1)
    return out

def mexc(symbol,d):
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",{"interval":"Min1","start":str(sec(d,13,20)),"end":str(sec(d,14,1))})
    j=r.json(); z=j.get("data") or {}; out={}
    if j.get("success") is not True: return {}
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try: out[int(t)+60]=float(p)
        except: pass
    return out

def binance(symbol,d):
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{d.isoformat()}.zip",timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1: raise RuntimeError("BINANCE_ZIP_IDENTITY")
    out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:t=int(row[0])//1000;p=float(row[4])
        except:continue
        if sec(d,13,20)<=t<=sec(d,14,1):out[t+60]=p
    return out

def bitget(symbol,d):
    r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{"symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m","startTime":str(sec(d,13,20)*1000),"endTime":str(sec(d,14,1)*1000),"limit":"100"})
    j=r.json(); out={}
    for row in j.get("data") or []:
        try: out[int(row[0])//1000+60]=float(row[4])
        except: pass
    return out

def binom(w,n): return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None
def halves(v):
    n=len(v);k=n//2
    return [mean(v[:k]),mean(v[k:])] if n>=2 else [None,None]

def evaluate(target,ext):
    vals=[]; bas=[]; cov={}
    for d in sessions():
        ds=d.isoformat()
        try:m=mexc(target,d);b=binance(ext,d);g=bitget(ext,d)
        except Exception as e:
            cov[ds]={"error":str(e)};continue
        t29=sec(d,13,29);t59=sec(d,13,59)
        ok=t29 in m and t29 in b and t29 in g and t59 in m
        cov[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g),"ok":ok}
        if not ok: continue
        external=(b[t29]+g[t29])/2; basis=10000*(m[t29]/external-1); side=-sgn(basis)
        if side==0: continue
        ret=10000*(m[t59]/m[t29]-1)
        vals.append(side*ret);bas.append(abs(basis))
    n=len(vals);w=sum(x>0 for x in vals);h=halves(vals);mg=mean(vals)
    return {"target":target,"external":ext,"n":n,"wins":w,"win_rate":w/n if n else None,"mean_gross_bps":mg,
      "median_gross_bps":med(vals),"half_means_bps":h,"p":binom(w,n),"mean_abs_basis_bps":mean(bas),
      "net":{str(c):(mg-c if mg is not None else None) for c in R["costs"]},"coverage":cov}

def eligible(x):
    g=R["scientific_gate"]
    return x["n"]>=g["min_n"] and x["mean_gross_bps"]>0 and x["median_gross_bps"]>0 and x["win_rate"]>g["win_rate_gt"] and all(v is not None and v>0 for v in x["half_means_bps"])

def main():
    results=[evaluate(c["target"],c["external"]) for c in R["candidates"]]
    for x in results:x["pre_holm_eligible"]=eligible(x)
    ordered=sorted(results,key=lambda x:x["p"] if x["p"] is not None else 1.0);still=True;m=len(ordered)
    for rank,x in enumerate(ordered,1):
        cutoff=R["scientific_gate"]["alpha"]/(m-rank+1)
        x["holm_rank"]=rank;x["holm_cutoff"]=cutoff;x["holm_reject"]=bool(still and x["p"] is not None and x["p"]<=cutoff)
        if not x["holm_reject"]: still=False
    for x in results:
        x["scientific_pass"]=bool(x["pre_holm_eligible"] and x["holm_reject"])
        x["net12_survivor"]=bool(x["scientific_pass"] and x["net"]["12"]>0)
        x["net16_survivor"]=bool(x["scientific_pass"] and x["net"]["16"]>0)
        x["verdict"]="ROBUST_API_FEE_SURVIVOR" if x["net16_survivor"] else ("MAKER_MAKER_FEE_SURVIVOR_ONLY" if x["net12_survivor"] else ("SCIENTIFIC_PASS_FEE_BLOCKED" if x["scientific_pass"] else "NO_SCIENTIFIC_PASS"))
    robust=[x for x in results if x["net16_survivor"]]
    overall="ROBUST_API_FEE_SURVIVOR_FOUND__EXECUTION_VALIDATION_REQUIRED" if robust else ("NO_LEVERAGED_CASHOPEN_SURVIVOR_AT_FROZEN_V09_GATE")
    rep={"overall_verdict":overall,"results":results,"scientific_pass_count":sum(x["scientific_pass"] for x in results),"net16_survivor_count":len(robust),"orders":False,"live_trading":False}
    OUT.mkdir(parents=True,exist_ok=True);(OUT/"MEXC_LEVERAGED_CASHOPEN_CLOSEOUT_V09.json").write_text(json.dumps(rep,indent=2,sort_keys=True))
    print(json.dumps(rep,indent=2))
if __name__=="__main__":main()

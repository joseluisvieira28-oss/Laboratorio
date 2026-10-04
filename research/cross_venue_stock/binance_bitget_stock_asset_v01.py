#!/usr/bin/env python3
"""Frozen Binance<->Bitget stock lead-lag V0.1 per-asset evaluator."""
from __future__ import annotations
import argparse,csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE=json.loads((HERE/"BINANCE_BITGET_STOCK_RULE_V0.1.json").read_text())
OUT=Path("artifacts/cross_venue_stock/binance_bitget_v01/assets")
UA="CryptoLab-Binance-Bitget-StockLeadLag/0.1"

def h(b): return hashlib.sha256(b).hexdigest()
def mean(xs): return sum(xs)/len(xs) if xs else None
def med(xs): return statistics.median(xs) if xs else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
def sec(d,hh,mm): return int(datetime(d.year,d.month,d.day,hh,mm,tzinfo=timezone.utc).timestamp())

def sessions():
    a=date.fromisoformat(RULE["discovery_start_date"]); b=date.fromisoformat(RULE["discovery_end_date_inclusive"])
    out=[]; d=a
    while d<=b:
        if d.weekday()<5: out.append(d)
        d+=timedelta(days=1)
    return out

def req(url,params=None,timeout=80,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}")
            return r
        except Exception as e:
            last=e; time.sleep(.6*(i+1))
    raise last

def fetch_binance(symbol,d):
    day=d.isoformat()
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{day}.zip",timeout=100)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1: raise RuntimeError("BINANCE_ZIP_IDENTITY")
    lo=sec(d,14,29); hi=sec(d,18,59); out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:
            t=int(row[0])//1000; p=float(row[4])
        except: continue
        if lo<=t<=hi: out[t+60]=p
    return out,h(r.content)

def fetch_bitget(symbol,d):
    out={}; hs=[]
    for a,b in [(sec(d,14,29),sec(d,16,44)),(sec(d,16,45),sec(d,18,59))]:
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
        hs.append(h(r.content)); j=r.json()
        if j.get("code")!="00000": raise RuntimeError(f"BITGET_CODE_{j.get('code')}")
        for row in j.get("data") or []:
            try: out[int(row[0])//1000+60]=float(row[4])
            except: pass
    return out,hs

def binom_tail(w,n):
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None

def thirds(vals):
    n=len(vals)
    if not n:return [None,None,None]
    c=[0,n//3,(2*n)//3,n]
    return [mean(vals[c[i]:c[i+1]]) for i in range(3)]

def score(D,leader_key,target_key):
    R=RULE["frozen_rule"]
    vals=[];days=[];shocks=[];gaps=[];times=[]
    for ds,X in D.items():
        d=date.fromisoformat(ds);start=sec(d,14,31);stop=sec(d,18,44);next_allowed=start
        common=sorted(set(X["binance"])&set(X["bitget"]))
        for t in common:
            if t<start or t>stop or t<next_allowed:continue
            prev=t-60; ex=t+R["horizon_min"]*60
            if prev not in X[leader_key] or prev not in X[target_key] or ex not in X[target_key]:continue
            lr=10000*(X[leader_key][t]/X[leader_key][prev]-1)
            tr=10000*(X[target_key][t]/X[target_key][prev]-1)
            gap=lr-tr
            if abs(lr)<R["leader_shock_threshold_bps"]:continue
            if R["require_same_sign_gap_and_leader"] and sgn(gap)!=sgn(lr):continue
            if abs(gap)<R["lag_gap_threshold_bps"]:continue
            gross=sgn(lr)*10000*(X[target_key][ex]/X[target_key][t]-1)
            vals.append(gross);days.append(ds);shocks.append(lr);gaps.append(gap)
            times.append(f"{ds}T{datetime.fromtimestamp(t,tz=timezone.utc).strftime('%H:%M:%S')}Z")
            next_allowed=t+R["cooldown_min"]*60
    n=len(vals);wins=sum(v>0 for v in vals)
    return {
      "n":n,"wins":wins,"losses_or_zero":n-wins,"win_rate":wins/n if n else None,
      "distinct_signal_sessions":len(set(days)),
      "mean_gross_signed_bps":mean(vals),"median_gross_signed_bps":med(vals),
      "chronological_third_means_bps":thirds(vals),
      "p_value_one_sided_binomial_vs_50":binom_tail(wins,n),
      "mean_abs_leader_shock_bps":mean([abs(x) for x in shocks]) if shocks else None,
      "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]) if gaps else None,
      "signal_times":times
    }

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--symbol",required=True);a=ap.parse_args()
    ss=sessions()
    if len(ss)!=RULE["expected_weekday_sessions"]:
        raise SystemExit(f"FAIL_CLOSED_SESSION_COUNT_{len(ss)}")
    D={};coverage={};hashes={}
    for d in ss:
        ds=d.isoformat()
        try:
            bn,bh=fetch_binance(a.symbol,d); bg,gh=fetch_bitget(a.symbol,d)
        except Exception as e:
            coverage[ds]={"error":str(e)};continue
        common=len(set(bn)&set(bg))
        coverage[ds]={"binance":len(bn),"bitget":len(bg),"common":common}
        hashes[ds]={"binance":bh,"bitget":gh}
        if len(bn)>=260 and len(bg)>=240 and common>=250:
            D[ds]={"binance":bn,"bitget":bg}
        time.sleep(.02)
    complete=len(D)
    routes={}
    if complete==RULE["expected_weekday_sessions"]:
        routes["BITGET_LEADER__BINANCE_TARGET"]=score(D,"bitget","binance")
        routes["BINANCE_LEADER__BITGET_TARGET"]=score(D,"binance","bitget")
    receipt={
      "symbol":a.symbol,"complete_sessions":complete,
      "source_complete":complete==RULE["expected_weekday_sessions"],
      "routes":routes,"coverage":coverage,"source_hashes":hashes,
      "post_outcome_tuning":False,"private_endpoints_used":False,"account_reads":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/(a.symbol+".json")).write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print(json.dumps({"symbol":a.symbol,"complete_sessions":complete,
      "routes":{k:{"n":v["n"],"mean":v["mean_gross_signed_bps"],"p":v["p_value_one_sided_binomial_vs_50"]} for k,v in routes.items()}},indent=2))

if __name__=="__main__":main()

#!/usr/bin/env python3
"""COINBASE V0.3 prospective forward evaluator. Exact frozen 20/10/5m cell."""
from __future__ import annotations
import csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_COINBASE_REGSESSION_FORWARD_RULE_V0.3.json"
BIND_PATH=HERE/"MEXC_COINBASE_REGSESSION_FORWARD_BINDING_V0.3.json"
RULE=json.loads(RULE_PATH.read_text())
BIND=json.loads(BIND_PATH.read_text())
OUT=Path("artifacts/mexc_global_assets/coinbase_regsession_forward_v03")
UA="CryptoLab-MEXC-COINBASE-Forward/0.3"

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def mean(xs): return sum(xs)/len(xs) if xs else None
def med(xs): return statistics.median(xs) if xs else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
def utcsec(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())

def sessions():
    a=date.fromisoformat(RULE["forward_start_date"]); b=date.fromisoformat(RULE["forward_end_date_inclusive"])
    out=[]; d=a
    while d<=b:
        if d.weekday()<5: out.append(d)
        d+=timedelta(days=1)
    return out

def req(url,params=None,timeout=60,retries=4):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200: raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{r.content[:200]!r}")
            return r
        except Exception as e:
            last=e; time.sleep(.7*(i+1))
    raise last

def fetch_mexc(d):
    a=utcsec(d,14,29); b=utcsec(d,18,51)
    r=req("https://api.mexc.com/api/v1/contract/kline/COINBASE_USDT",{"interval":"Min1","start":str(a),"end":str(b)})
    j=r.json()
    if j.get("success") is not True: raise RuntimeError(f"MEXC:{d}:{j}")
    out={}; z=j.get("data") or {}
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try: out[int(t)+60]=float(p)
        except Exception: pass
    return out,sha_bytes(r.content)

def fetch_bitget(d):
    out={}; hs=[]
    for a,b in [(utcsec(d,14,29),utcsec(d,16,44)),(utcsec(d,16,45),utcsec(d,18,51))]:
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":"COINUSDT","productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
        hs.append(sha_bytes(r.content)); j=r.json()
        if j.get("code")!="00000": raise RuntimeError(f"BITGET:{d}:{j}")
        for row in j.get("data") or []:
            try: out[int(row[0])//1000+60]=float(row[4])
            except Exception: pass
    return out,hs

def fetch_binance(d):
    day=d.isoformat()
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/COINUSDT/1m/COINUSDT-1m-{day}.zip",timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1: raise RuntimeError(f"BINANCE_ID:{day}:{names}")
    out={}; lo=utcsec(d,14,29); hi=utcsec(d,18,51)
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try: t=int(row[0])//1000; p=float(row[4])
        except Exception: continue
        if lo<=t<=hi: out[t+60]=p
    return out,sha_bytes(r.content)

def binom(w,n):
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None

def main():
    now=datetime.now(timezone.utc)
    if now < datetime(2026,10,31,0,0,tzinfo=timezone.utc):
        raise SystemExit("FAIL_CLOSED_FORWARD_WINDOW_NOT_COMPLETE")
    if RULE["future_outcomes_opened_at_freeze"]!=0 or BIND["future_outcomes_opened_at_binding"]!=0:
        raise SystemExit("FAIL_CLOSED_NOT_PRE_OUTCOME")
    cell=RULE["frozen_cell"]
    if [cell["shock_threshold_bps"],cell["lag_gap_threshold_bps"],cell["horizon_min"]] != [20,10,5]:
        raise SystemExit("FAIL_CLOSED_CELL_CHANGED")
    if cell["direction"]!="FOLLOW_EXTERNAL_CONSENSUS":
        raise SystemExit("FAIL_CLOSED_DIRECTION_CHANGED")

    sess=sessions()
    if len(sess)!=RULE["expected_weekday_sessions"]:
        raise SystemExit(f"FAIL_CLOSED_SESSION_COUNT:{len(sess)}")

    vals=[]; events=[]; hashes={}
    for d in sess:
        m,mh=fetch_mexc(d); b,bh=fetch_binance(d); g,gh=fetch_bitget(d); ds=d.isoformat()
        hashes[ds]={"mexc":mh,"binance":bh,"bitget":gh}
        start=utcsec(d,14,31); stop=utcsec(d,18,44); next_allowed=start
        for t in sorted(set(m)&set(b)&set(g)):
            if t<start or t>stop or t<next_allowed: continue
            p=t-60; x=t+300
            if p not in m or p not in b or p not in g or x not in m: continue
            ext=(10000*(b[t]/b[p]-1)+10000*(g[t]/g[p]-1))/2
            mr=10000*(m[t]/m[p]-1); gap=ext-mr
            if abs(ext)<20 or sgn(gap)!=sgn(ext) or abs(gap)<10: continue
            gross=sgn(ext)*10000*(m[x]/m[t]-1)
            vals.append(gross)
            events.append({"date":ds,"t_utc":datetime.fromtimestamp(t,tz=timezone.utc).isoformat(),
                           "external_return_bps":ext,"lag_gap_bps":gap,"gross_signed_bps":gross})
            next_allowed=t+300
        time.sleep(.03)

    n=len(vals); wins=sum(x>0 for x in vals); days=len(set(e["date"] for e in events))
    half=n//2; halves=[mean(vals[:half]),mean(vals[half:])] if n>=2 else [None,None]
    p=binom(wins,n)
    g=RULE["scientific_validation_gate"]
    enough=n>=g["min_n"] and days>=g["min_distinct_signal_sessions"]
    scientific=bool(enough and mean(vals)>0 and med(vals)>0 and wins/n>0.5 and
                    all(x is not None and x>0 for x in halves) and p<g["exact_one_sided_binomial_p_lt"])
    econ=RULE["execution_screen_descriptive_only"]
    fee16=bool(vals and mean(vals)>econ["fee_only_survival_requires_mean_gross_bps_gt"])
    reserve18=bool(vals and mean(vals)>econ["conservative_fee_plus_2bps_reserve_requires_mean_gross_bps_gt"])
    verdict=("FORWARD_VALIDATED_SIGNAL" if scientific else ("FORWARD_UNDERPOWERED" if not enough else "FORWARD_VALIDATION_FAIL"))

    report={
      "study_id":RULE["study_id"],"generated_at_utc":now.isoformat(),
      "rule_sha256":sha_file(RULE_PATH),"binding_sha256":sha_file(BIND_PATH),
      "sessions_frozen":len(sess),"n":n,"distinct_signal_sessions":days,
      "wins":wins,"win_rate":wins/n if n else None,
      "mean_gross_bps":mean(vals),"median_gross_bps":med(vals),
      "chronological_half_means_bps":halves,"p_value_one_sided_binomial_vs_50":p,
      "scientific_validation_pass":scientific,
      "fee_only_16bps_mean_survival":fee16,
      "fee_plus_2bps_reserve_18bps_mean_survival":reserve18,
      "cost_scenarios_mean_net_bps":{str(c):(mean(vals)-c if vals else None) for c in RULE["cost_scenarios_roundtrip_bps"]},
      "verdict":verdict,"events":events,"source_hashes":hashes,
      "orders":False,"account_reads":False,"private_endpoints_used":False,
      "exchange_mutation":False,"live_trading_authorized":False
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_COINBASE_REGSESSION_FORWARD_CLOSEOUT_V03.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({k:report[k] for k in ["verdict","n","distinct_signal_sessions","wins","win_rate","mean_gross_bps","median_gross_bps","chronological_half_means_bps","p_value_one_sided_binomial_vs_50","scientific_validation_pass","fee_only_16bps_mean_survival","fee_plus_2bps_reserve_18bps_mean_survival"]},indent=2))

if __name__=="__main__": main()

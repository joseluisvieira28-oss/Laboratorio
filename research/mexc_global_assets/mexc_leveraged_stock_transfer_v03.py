#!/usr/bin/env python3
"""Frozen V0.3 transfer test on MUU and MVLL. No tuning."""
from __future__ import annotations
import csv,io,json,math,statistics,time,zipfile,hashlib
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE=json.loads((HERE/"MEXC_LEVERAGED_STOCK_TRANSFER_RULE_V0.3.json").read_text())
BIND=json.loads((HERE/"MEXC_LEVERAGED_STOCK_TRANSFER_SOURCE_BINDING_V0.3.json").read_text())
OUT=Path("artifacts/mexc_global_assets/leveraged_stock_transfer_v03")
UA="CryptoLab-LeveragedStock-Transfer/0.3"

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def mean(xs): return sum(xs)/len(xs) if xs else None
def med(xs): return statistics.median(xs) if xs else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
def utcsec(d,h,m): return int(datetime(d.year,d.month,d.day,h,m,tzinfo=timezone.utc).timestamp())

def sessions():
    a=date.fromisoformat(RULE["discovery_start_date"]); b=date.fromisoformat(RULE["discovery_end_date_inclusive"])
    ex={date.fromisoformat(x) for x in RULE["excluded_dates"]}; out=[]; d=a
    while d<=b:
        if d.weekday()<5 and d not in ex: out.append(d)
        d+=timedelta(days=1)
    return out

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

def fetch_mexc(symbol,d):
    a=utcsec(d,14,29); b=utcsec(d,18,59)
    r=req(f"https://api.mexc.com/api/v1/contract/kline/{symbol}",{"interval":"Min1","start":str(a),"end":str(b)})
    j=r.json(); z=j.get("data") or {}; out={}
    if j.get("success") is not True: return {},sha_bytes(r.content)
    for t,p in zip(z.get("time") or [],z.get("close") or []):
        try: out[int(t)+60]=float(p)
        except: pass
    return out,sha_bytes(r.content)

def fetch_binance(symbol,d):
    day=d.isoformat()
    r=req(f"https://data.binance.vision/data/futures/um/daily/klines/{symbol}/1m/{symbol}-1m-{day}.zip",timeout=90)
    z=zipfile.ZipFile(io.BytesIO(r.content)); names=z.namelist()
    if len(names)!=1: raise RuntimeError("BINANCE_ZIP_IDENTITY")
    lo=utcsec(d,14,29); hi=utcsec(d,18,59); out={}
    for row in csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8")):
        try:t=int(row[0])//1000;p=float(row[4])
        except:continue
        if lo<=t<=hi:out[t+60]=p
    return out,sha_bytes(r.content)

def fetch_bitget(symbol,d):
    out={}; hs=[]
    for a,b in [(utcsec(d,14,29),utcsec(d,16,44)),(utcsec(d,16,45),utcsec(d,18,59))]:
        r=req("https://api.bitget.com/api/v2/mix/market/history-candles",{
          "symbol":symbol,"productType":"USDT-FUTURES","granularity":"1m",
          "startTime":str(a*1000),"endTime":str(b*1000),"limit":"200"})
        hs.append(sha_bytes(r.content)); j=r.json()
        if j.get("code")!="00000": continue
        for row in j.get("data") or []:
            try: out[int(row[0])//1000+60]=float(row[4])
            except:pass
    return out,hs

def binom_tail(w,n):
    return sum(math.comb(n,k) for k in range(w,n+1))/(2**n) if n else None

def thirds(vals):
    n=len(vals)
    if not n:return [None,None,None]
    c=[0,n//3,(2*n)//3,n]
    return [mean(vals[c[i]:c[i+1]]) for i in range(3)]

def score(D):
    R=RULE["exact_transfer_rule"]; shock=R["shock_threshold_bps"]; gap=R["lag_gap_threshold_bps"]; h=R["horizon_min"]
    vals=[]; exts=[]; gaps=[]; sigdays=[]; times=[]
    for ds,X in D.items():
        d=date.fromisoformat(ds); start=utcsec(d,14,31); stop=utcsec(d,18,44); next_allowed=start
        common=sorted(set(X["mexc"])&set(X["binance"])&set(X["bitget"]))
        for t in common:
            if t<start or t>stop or t<next_allowed: continue
            prev=t-60; ex=t+h*60
            if prev not in X["mexc"] or prev not in X["binance"] or prev not in X["bitget"] or ex not in X["mexc"]:continue
            rb=10000*(X["binance"][t]/X["binance"][prev]-1); rg=10000*(X["bitget"][t]/X["bitget"][prev]-1)
            ext=(rb+rg)/2; mr=10000*(X["mexc"][t]/X["mexc"][prev]-1); lg=ext-mr
            if abs(ext)<shock or sgn(lg)!=sgn(ext) or abs(lg)<gap:continue
            gross=sgn(ext)*10000*(X["mexc"][ex]/X["mexc"][t]-1)
            vals.append(gross); exts.append(ext); gaps.append(lg); sigdays.append(ds)
            times.append(f"{ds}T{datetime.fromtimestamp(t,tz=timezone.utc).strftime('%H:%M:%S')}Z")
            next_allowed=t+h*60
    n=len(vals); wins=sum(v>0 for v in vals)
    return {
      "n":n,"wins":wins,"losses_or_zero":n-wins,"win_rate":wins/n if n else None,
      "distinct_signal_sessions":len(set(sigdays)),
      "mean_gross_signed_bps":mean(vals),"median_gross_signed_bps":med(vals),
      "chronological_third_means_bps":thirds(vals),
      "p_value_one_sided_binomial_vs_50":binom_tail(wins,n),
      "mean_abs_external_shock_bps":mean([abs(x) for x in exts]) if exts else None,
      "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]) if gaps else None,
      "mean_net_bps":{str(c):(mean(vals)-c if vals else None) for c in RULE["execution_fee_scenarios_roundtrip_bps"]},
      "signal_times":times
    }

def prereq(r):
    g=RULE["scientific_gate"]
    return (r["n"]>=g["min_n"] and r["distinct_signal_sessions"]>=g["min_distinct_signal_sessions"] and
            r["mean_gross_signed_bps"] is not None and r["mean_gross_signed_bps"]>0 and
            r["median_gross_signed_bps"] is not None and r["median_gross_signed_bps"]>0 and
            r["win_rate"] is not None and r["win_rate"]>g["win_rate_gt"] and
            all(x is not None and x>0 for x in r["chronological_third_means_bps"]))

def main():
    if RULE["outcomes_opened_at_freeze"]!=0 or BIND["historical_outcomes_opened_at_binding"]!=0:
        raise SystemExit("FAIL_CLOSED_NOT_PRE_OUTCOME")
    sess=sessions()
    if len(sess)!=17:raise SystemExit(f"FAIL_CLOSED_SESSION_COUNT_{len(sess)}")
    results=[]; coverage={}
    for c in BIND["candidates"]:
        target=c["target"]; bs=c["external_binance"]; gs=c["external_bitget"]
        D={}; cov={}; hashes={}
        for d in sess:
            m,mh=fetch_mexc(target,d); b,bh=fetch_binance(bs,d); g,gh=fetch_bitget(gs,d)
            ds=d.isoformat(); common=len(set(m)&set(b)&set(g))
            cov[ds]={"mexc":len(m),"binance":len(b),"bitget":len(g),"common":common}
            hashes[ds]={"mexc":mh,"binance":bh,"bitget":gh}
            if len(m)>=260 and len(b)>=260 and len(g)>=240 and common>=250:
                D[ds]={"mexc":m,"binance":b,"bitget":g}
            time.sleep(.02)
        complete=len(D)
        coverage[target]=cov
        if complete!=17:
            results.append({"target":target,"coverage_complete_sessions":complete,"source_complete":False,
                            "scientific_pre_holm_eligible":False,"result":None,"source_hashes":hashes})
            continue
        r=score(D)
        results.append({"target":target,"coverage_complete_sessions":complete,"source_complete":True,
                        "scientific_pre_holm_eligible":prereq(r),"result":r,"source_hashes":hashes})
    # Holm over exactly 2 frozen assets. Source-incomplete asset p=1.
    ordered=sorted(results,key=lambda x:(x["result"]["p_value_one_sided_binomial_vs_50"] if x["result"] else 1.0))
    still=True; m=len(results)
    for rank,x in enumerate(ordered,1):
        cutoff=RULE["scientific_gate"]["family_wise_alpha"]/(m-rank+1)
        p=x["result"]["p_value_one_sided_binomial_vs_50"] if x["result"] else 1.0
        reject=bool(still and p<=cutoff)
        x["holm_rank"]=rank;x["holm_cutoff"]=cutoff;x["holm_reject"]=reject
        if not reject:still=False
    for x in results:
        sci=bool(x.get("source_complete") and x["scientific_pre_holm_eligible"] and x.get("holm_reject"))
        x["scientific_pass"]=sci
        if sci:
            x["fee_floor_survivor_12bps"]=x["result"]["mean_net_bps"]["12"]>0
            x["robust_fee_survivor_16bps"]=x["result"]["mean_net_bps"]["16"]>0
            x["net_20bps_positive"]=x["result"]["mean_net_bps"]["20"]>0
        else:
            x["fee_floor_survivor_12bps"]=False;x["robust_fee_survivor_16bps"]=False;x["net_20bps_positive"]=False
        if not x["source_complete"]: x["verdict"]="SOURCE_BLOCKED_HISTORICAL_COVERAGE"
        elif not sci: x["verdict"]="NO_SCIENTIFIC_TRANSFER_SURVIVOR"
        elif x["robust_fee_survivor_16bps"]: x["verdict"]="SCIENTIFIC_AND_ROBUST_API_FEE_SURVIVOR"
        elif x["fee_floor_survivor_12bps"]: x["verdict"]="SCIENTIFIC_AND_MAKER_MAKER_FEE_SURVIVOR_ONLY"
        else:x["verdict"]="SCIENTIFIC_SURVIVOR__STANDARD_MEXC_API_FEE_BLOCKED"
    if any(x["robust_fee_survivor_16bps"] for x in results):
        overall="ROBUST_API_FEE_SURVIVOR_FOUND__EXECUTION_MICROSTRUCTURE_REQUIRED"
    elif any(x["fee_floor_survivor_12bps"] for x in results):
        overall="MAKER_MAKER_FEE_SURVIVOR_FOUND__FILL_RISK_UNPROVEN"
    elif any(x["scientific_pass"] for x in results):
        overall="SCIENTIFIC_TRANSFER_SURVIVORS_FOUND__STANDARD_API_FEE_BLOCKED"
    elif any(not x["source_complete"] for x in results):
        overall="NO_OPERATIONAL_CANDIDATE__SOURCE_OR_SCIENCE_BLOCKED"
    else: overall="NO_OPERATIONAL_CANDIDATE_AT_FROZEN_V03_GATE"
    report={
      "family_id":RULE["family_id"],"generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(HERE/"MEXC_LEVERAGED_STOCK_TRANSFER_RULE_V0.3.json"),
      "binding_sha256":sha_file(HERE/"MEXC_LEVERAGED_STOCK_TRANSFER_SOURCE_BINDING_V0.3.json"),
      "results":results,"coverage":coverage,"overall_verdict":overall,
      "retrospective_oos_opened":False,"post_outcome_tuning_authorized":False,
      "private_endpoints_used":False,"account_reads":False,"orders":False,
      "exchange_mutation":False,"live_trading_authorized":False
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_LEVERAGED_STOCK_TRANSFER_CLOSEOUT_V03.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    print(json.dumps({
      "overall_verdict":overall,
      "assets":[{
        "target":x["target"],"source_complete":x["source_complete"],"complete_sessions":x["coverage_complete_sessions"],
        "scientific_pass":x["scientific_pass"],"holm_cutoff":x.get("holm_cutoff"),
        "n":x["result"]["n"] if x["result"] else None,"wins":x["result"]["wins"] if x["result"] else None,
        "win_rate":x["result"]["win_rate"] if x["result"] else None,
        "mean_gross_bps":x["result"]["mean_gross_signed_bps"] if x["result"] else None,
        "median_gross_bps":x["result"]["median_gross_signed_bps"] if x["result"] else None,
        "thirds":x["result"]["chronological_third_means_bps"] if x["result"] else None,
        "p":x["result"]["p_value_one_sided_binomial_vs_50"] if x["result"] else None,
        "net12":x["result"]["mean_net_bps"]["12"] if x["result"] else None,
        "net16":x["result"]["mean_net_bps"]["16"] if x["result"] else None,
        "verdict":x["verdict"]
      } for x in results],
      "live_trading_authorized":False
    },indent=2))

if __name__=="__main__":main()

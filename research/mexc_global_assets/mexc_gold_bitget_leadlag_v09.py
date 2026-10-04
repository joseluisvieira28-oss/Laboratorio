#!/usr/bin/env python3
from __future__ import annotations
import csv,hashlib,json,math,os,time
from datetime import datetime,timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_GOLD_BITGET_LEADLAG_RULE_V0.9.json"
RULE=json.loads(RULE_PATH.read_text())
OUT=Path("artifacts/mexc_global_assets/gold_bitget_leadlag_v09")
MEXC="https://api.mexc.com"; BITGET="https://api.bitget.com"
UA="CryptoLab-GOLD-Bitget-LeadLag/0.9"; STEP=60

def ts(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
START=ts(RULE["discovery_start"]); END=ts(RULE["discovery_end_exclusive"])
def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def get(url,params=None,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
            if r.status_code!=200: raise RuntimeError(f"HTTP {r.status_code} {r.url}: {r.content[:200]!r}")
            return r.json()
        except Exception as e:
            last=e; time.sleep(0.5*(i+1))
    raise last

def fetch_mexc():
    out={}; cur=START-2*STEP; last_raw=END-2*STEP; span=900*STEP
    while cur<=last_raw:
        e=min(cur+span,last_raw)
        j=get(MEXC+f"/api/v1/contract/kline/{RULE['mexc_symbol']}",
              {"interval":"Min1","start":cur,"end":e})
        if not isinstance(j,dict) or j.get("success") is not True: raise RuntimeError(f"MEXC_NON_SUCCESS:{j}")
        d=j.get("data") or {}
        for s,p in zip(d.get("time") or [],d.get("close") or []):
            try: raw=int(s)
            except Exception: continue
            if raw<cur or raw>e: raise RuntimeError("MEXC_TIMESTAMP_OUTSIDE_REQUEST")
            obs=raw+STEP
            if obs>=END: raise RuntimeError("MEXC_PROTECTED_TIMESTAMP")
            try: px=float(p)
            except Exception: continue
            if px>0: out[obs]=px
        cur=e+STEP; time.sleep(0.04)
    return out

def fetch_bitget():
    out={}; cur=START-2*STEP; last_raw=END-2*STEP; span=900*STEP
    while cur<=last_raw:
        e=min(cur+span,last_raw)
        j=get(BITGET+"/api/v3/market/candles",{
          "category":"USDT-FUTURES","symbol":RULE["leader_symbol"],"interval":"1m",
          "startTime":str(cur*1000),"endTime":str(e*1000),"limit":"1000"
        })
        if str(j.get("code"))!="00000": raise RuntimeError(f"BITGET_NON_SUCCESS:{j}")
        for row in j.get("data") or []:
            try: raw=int(row[0])//1000
            except Exception: continue
            if raw<cur or raw>e: raise RuntimeError("BITGET_TIMESTAMP_OUTSIDE_REQUEST")
            obs=raw+STEP
            if obs>=END: raise RuntimeError("BITGET_PROTECTED_TIMESTAMP")
            try: px=float(row[4])
            except Exception: continue
            if px>0: out[obs]=px
        cur=e+STEP; time.sleep(0.04)
    return out

def mean(xs): return sum(xs)/len(xs) if xs else None
def median(xs):
    if not xs:return None
    y=sorted(xs); n=len(y); return y[n//2] if n%2 else (y[n//2-1]+y[n//2])/2
def thirds(xs):
    n=len(xs)
    if not n:return [None,None,None]
    c=[0,n//3,(2*n)//3,n]
    return [mean(xs[c[i]:c[i+1]]) for i in range(3)]
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)
def binom_tail(w,n):
    if n<=0:return None
    return min(1.0,sum(math.comb(n,k)*(0.5**n) for k in range(w,n+1)))

def score(mexc,lead,shock,gap,hmin):
    h=hmin*60; vals=[]; gaps=[]; shocks=[]; next_allowed=START
    for t in sorted(set(mexc)&set(lead)):
        if t<START or t>=END or t<next_allowed: continue
        if t-STEP not in mexc or t-STEP not in lead: continue
        exit_t=t+h
        if exit_t>=END or exit_t not in mexc: continue
        lr=10000*(lead[t]/lead[t-STEP]-1)
        mr=10000*(mexc[t]/mexc[t-STEP]-1)
        lg=lr-mr
        if abs(lr)<shock or sgn(lg)!=sgn(lr) or abs(lg)<gap: continue
        gross=sgn(lr)*10000*(mexc[exit_t]/mexc[t]-1)
        vals.append(gross); gaps.append(lg); shocks.append(lr); next_allowed=t+h
    n=len(vals); wins=sum(v>0 for v in vals); mg=mean(vals)
    return {
      "n":n,"wins":wins,"losses":n-wins,"win_rate":wins/n if n else None,
      "mean_gross_bps":mg,"median_gross_bps":median(vals),
      "p_value_vs_50":binom_tail(wins,n) if n else None,
      "third_means_gross_bps":thirds(vals),
      "mean_abs_leader_shock_bps":mean([abs(x) for x in shocks]),
      "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]),
      "cost_scenarios_mean_net_bps":{
        str(c):(mg-float(c) if mg is not None else None)
        for c in RULE["cost_scenarios_roundtrip_bps"]
      }
    }

def eligible(r):
    g=RULE["discovery_gate"]
    return (r["n"]>=g["min_n"] and r["mean_gross_bps"] is not None and r["mean_gross_bps"]>0
      and r["win_rate"] is not None and r["win_rate"]>0.5
      and r["p_value_vs_50"] is not None
      and all(x is not None and x>0 for x in r["third_means_gross_bps"]))

def holm(cells):
    es=[x for x in cells if x["eligible"]]
    es.sort(key=lambda x:x["result"]["p_value_vs_50"])
    m=len(es); sel=[]
    for rank,x in enumerate(es,1):
        cutoff=RULE["discovery_gate"]["family_wise_alpha"]/(m-rank+1)
        x["holm_cutoff"]=cutoff
        if x["result"]["p_value_vs_50"]<=cutoff: sel.append(x)
        else: break
    return sel,m

def main():
    if any(k.upper() in {"MEXC_API_KEY","MEXC_SECRET_KEY","API_KEY","SECRET_KEY","PRIVATE_KEY"} for k in os.environ):
        raise SystemExit("FAIL_CLOSED:CREDENTIAL_ENV_DETECTED")
    print("RULE_SHA256=",sha_file(RULE_PATH))
    mexc=fetch_mexc(); lead=fetch_bitget()
    overlap=[t for t in sorted(set(mexc)&set(lead)) if START<=t<END]
    expected=(END-START)//60; coverage=len(overlap)/expected
    if coverage<0.95: raise RuntimeError(f"CLOCK_COVERAGE_FAIL:{coverage}")

    cells=[]
    for shock in RULE["signal"]["leader_shock_thresholds_bps"]:
      for gap in RULE["signal"]["lag_gap_thresholds_bps"]:
       for h in RULE["signal"]["horizons_min"]:
        r=score(mexc,lead,float(shock),float(gap),int(h))
        cells.append({"shock_bps":shock,"gap_bps":gap,"horizon_min":h,"eligible":eligible(r),"result":r})
    selected,neligible=holm(cells)

    report={
      "family_id":RULE["family_id"],"version":RULE["version"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),
      "coverage_ratio":coverage,"exact_overlap_minutes":len(overlap),
      "cells":cells,"pre_holm_eligible_count":neligible,"holm_selected_count":len(selected),
      "holm_selected":[
        {"shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
         "n":x["result"]["n"],"win_rate":x["result"]["win_rate"],
         "mean_gross_bps":x["result"]["mean_gross_bps"],
         "p":x["result"]["p_value_vs_50"],"holm_cutoff":x.get("holm_cutoff")}
        for x in selected],
      "verdict":"GOLD_CROSSVENUE_DISCOVERY_CANDIDATES_FOUND" if selected else "NO_GOLD_CROSSVENUE_DISCOVERY_CANDIDATE_AT_FROZEN_V09_GATE",
      "retrospective_oos_opened":False,"parameter_rescue_authorized":False,
      "private_endpoints_used":False,"account_reads":False,"wallets_used":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_GOLD_BITGET_LEADLAG_CLOSEOUT_V09.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    with (OUT/"MEXC_GOLD_BITGET_LEADLAG_MATRIX_V09.csv").open("w",newline="") as f:
        fields=["shock_bps","gap_bps","horizon_min","n","win_rate","mean_gross_bps","median_gross_bps","p_value_vs_50","eligible"]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader()
        for x in cells:
            r=x["result"]
            w.writerow({"shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
                        "n":r["n"],"win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
                        "median_gross_bps":r["median_gross_bps"],"p_value_vs_50":r["p_value_vs_50"],
                        "eligible":x["eligible"]})
    print(json.dumps({
      "verdict":report["verdict"],"coverage_ratio":coverage,
      "pre_holm_eligible_count":neligible,"holm_selected_count":len(selected),
      "selected":report["holm_selected"],"retrospective_oos_opened":False,
      "live_trading_authorized":False
    },indent=2))

if __name__=="__main__":
    main()

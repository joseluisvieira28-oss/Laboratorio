#!/usr/bin/env python3
"""MEXC-GOLD-CONSENSUS-LEADLAG-001 V0.8 frozen discovery."""
from __future__ import annotations
import csv, gzip, hashlib, io, json, math, statistics, time, zipfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_GOLD_CONSENSUS_LEADLAG_RULE_V0.8.json"
BIND_PATH=HERE/"MEXC_GOLD_MULTIVENUE_SOURCE_BINDING_V0.7.4.json"
OUT=Path("artifacts/mexc_global_assets/gold_consensus_leadlag_v08")
RULE=json.loads(RULE_PATH.read_text())
BIND=json.loads(BIND_PATH.read_text())
UA="CryptoLab-GoldConsensus/0.8"
STEP=60

def ts(s): return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())
START=ts(RULE["discovery_start"]); END=ts(RULE["discovery_end_exclusive"])

def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def mean(xs): return sum(xs)/len(xs) if xs else None
def sgn(x): return 1 if x>0 else (-1 if x<0 else 0)

def median(xs):
    return statistics.median(xs) if xs else None

def get(url,params=None,retries=5,timeout=60):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=timeout)
            if r.status_code!=200:
                raise RuntimeError(f"HTTP {r.status_code}:{r.url}:{r.content[:200]!r}")
            return r.content,r.json() if "json" in r.headers.get("content-type","").lower() else None
        except Exception as e:
            last=e; time.sleep(0.8*(i+1))
    raise last

def archive_get(url,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,headers={"User-Agent":UA},timeout=90)
            if r.status_code!=200:
                raise RuntimeError(f"HTTP {r.status_code}:{url}:{r.content[:200]!r}")
            return r.content
        except Exception as e:
            last=e; time.sleep(0.8*(i+1))
    raise last

def observable(raw_s): return raw_s+STEP

def fetch_binance():
    out={}; hashes={}
    for day in ("2026-10-01","2026-10-02","2026-10-03"):
        url=f"https://data.binance.vision/data/futures/um/daily/klines/XAUUSDT/1m/XAUUSDT-1m-{day}.zip"
        raw=archive_get(url); hashes[day]=sha_bytes(raw)
        z=zipfile.ZipFile(io.BytesIO(raw)); names=z.namelist()
        if len(names)!=1: raise RuntimeError(f"BINANCE_ZIP_IDENTITY:{day}:{names}")
        rows=csv.reader(io.TextIOWrapper(z.open(names[0]),encoding="utf-8"))
        header=next(rows,None)
        for row in rows:
            try: raw_s=int(row[0])//1000; px=float(row[4])
            except Exception: continue
            t=observable(raw_s)
            if START<=t<END and px>0: out[t]=px
    return out,hashes

def fetch_bybit():
    out={}; hashes={}
    for day in ("2026-10-01","2026-10-02","2026-10-03"):
        compact=day.replace("-","")
        url=f"https://public.bybit.com/trading/XAUUSDT/XAUUSDT{day}.csv.gz"
        raw=archive_get(url); hashes[day]=sha_bytes(raw)
        text=gzip.decompress(raw).decode("utf-8")
        rd=csv.DictReader(io.StringIO(text))
        last_by_min={}
        for row in rd:
            try: sec=float(row["timestamp"]); px=float(row["price"])
            except Exception: continue
            raw_s=int(sec//60)*60
            prev=last_by_min.get(raw_s)
            if prev is None or sec>=prev[0]: last_by_min[raw_s]=(sec,px)
        for raw_s,(_,px) in last_by_min.items():
            t=observable(raw_s)
            if START<=t<END and px>0: out[t]=px
    return out,hashes

def fetch_bitget():
    out={}; hashes=[]; cur=START-60; span=850*60
    while cur<END-60:
        e=min(cur+span,END-60)
        raw,j=get("https://api.bitget.com/api/v2/mix/market/candles",{
            "symbol":"XAUUSDT","productType":"USDT-FUTURES","granularity":"1m",
            "startTime":str(cur*1000),"endTime":str(e*1000),"limit":"1000"
        })
        hashes.append(sha_bytes(raw))
        if not isinstance(j,dict) or j.get("code")!="00000":
            raise RuntimeError(f"BITGET_NON_SUCCESS:{j}")
        for row in j.get("data") or []:
            try: raw_s=int(row[0])//1000; px=float(row[4])
            except Exception: continue
            if raw_s<cur or raw_s>e: continue
            t=observable(raw_s)
            if START<=t<END and px>0: out[t]=px
        cur=e+60; time.sleep(0.08)
    return out,hashes

def fetch_mexc():
    out={}; hashes=[]; cur=START-60; span=1200*60
    while cur<END-60:
        e=min(cur+span,END-60)
        raw,j=get("https://api.mexc.com/api/v1/contract/kline/XAU_USDT",{
            "interval":"Min1","start":str(cur),"end":str(e)
        })
        hashes.append(sha_bytes(raw))
        if not isinstance(j,dict) or j.get("success") is not True:
            raise RuntimeError(f"MEXC_NON_SUCCESS:{j}")
        d=j.get("data") or {}
        for s,p in zip(d.get("time") or [],d.get("close") or []):
            try: raw_s=int(s); px=float(p)
            except Exception: continue
            if raw_s<cur or raw_s>e: continue
            t=observable(raw_s)
            if START<=t<END and px>0: out[t]=px
        cur=e+60; time.sleep(0.08)
    return out,hashes

def logsumexp(xs):
    m=max(xs); return m+math.log(sum(math.exp(x-m) for x in xs))
def binom_tail_half(w,n):
    if n<=0:return None
    ln2=math.log(2.0)
    logs=[math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*ln2 for k in range(w,n+1)]
    return min(1.0,math.exp(logsumexp(logs)))
def thirds(xs):
    n=len(xs)
    if n==0:return [None,None,None]
    cuts=[0,n//3,(2*n)//3,n]
    return [mean(xs[cuts[i]:cuts[i+1]]) for i in range(3)]

def score(mexc,binance,bitget,bybit,shock,gap,hmin):
    h=hmin*60; next_allowed=START; vals=[]; cons=[]; gaps=[]
    common=sorted(set(mexc)&set(binance)&set(bitget)&set(bybit))
    for t in common:
        if t<=START or t>=END or t<next_allowed: continue
        if any((t-60) not in d for d in (mexc,binance,bitget,bybit)): continue
        exit_t=t+h
        if exit_t>=END or exit_t not in mexc: continue
        ext=[
            10000*(binance[t]/binance[t-60]-1),
            10000*(bitget[t]/bitget[t-60]-1),
            10000*(bybit[t]/bybit[t-60]-1),
        ]
        consensus=median(ext)
        mr=10000*(mexc[t]/mexc[t-60]-1)
        lag=consensus-mr
        if abs(consensus)<shock: continue
        if sgn(lag)!=sgn(consensus): continue
        if abs(lag)<gap: continue
        side=sgn(consensus)
        gross=side*10000*(mexc[exit_t]/mexc[t]-1)
        vals.append(gross); cons.append(consensus); gaps.append(lag)
        next_allowed=t+h
    n=len(vals); wins=sum(x>0 for x in vals)
    return {
        "n":n,"wins":wins,"losses":n-wins,
        "win_rate":wins/n if n else None,
        "mean_gross_bps":mean(vals),
        "p_value_vs_50":binom_tail_half(wins,n) if n else None,
        "third_means_gross_bps":thirds(vals),
        "mean_abs_consensus_shock_bps":mean([abs(x) for x in cons]),
        "mean_abs_lag_gap_bps":mean([abs(x) for x in gaps]),
        "cost_scenarios_mean_net_bps":{
            str(c):(mean(vals)-float(c) if n else None)
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
    m=len(es); selected=[]
    for rank,x in enumerate(es,1):
        cutoff=RULE["discovery_gate"]["family_wise_alpha"]/(m-rank+1)
        x["holm_cutoff"]=cutoff
        if x["result"]["p_value_vs_50"]<=cutoff: selected.append(x)
        else: break
    return selected,m

def main():
    if BIND.get("source_gate_verdict")!="MEXC_GOLD_MULTIVENUE_SOURCE_PASS":
        raise SystemExit("FAIL_CLOSED: source binding not PASS")
    if RULE.get("outcomes_opened_at_freeze")!=0:
        raise SystemExit("FAIL_CLOSED: freeze not pre-outcome")
    print("RULE_SHA256=",sha_file(RULE_PATH))
    print("BINDING_SHA256=",sha_file(BIND_PATH))
    print("DISCOVERY_WINDOW=",RULE["discovery_start"],RULE["discovery_end_exclusive"])

    binance,bh=fetch_binance()
    bybit,yh=fetch_bybit()
    bitget,gh=fetch_bitget()
    mexc,mh=fetch_mexc()
    common=sorted(set(mexc)&set(binance)&set(bitget)&set(bybit))
    if len(common)<1000: raise RuntimeError(f"INSUFFICIENT_EXACT_COMMON_MINUTES:{len(common)}")

    cells=[]
    for shock in RULE["signal"]["shock_thresholds_bps"]:
        for gap in RULE["signal"]["lag_gap_thresholds_bps"]:
            for h in RULE["signal"]["horizons_min"]:
                r=score(mexc,binance,bitget,bybit,float(shock),float(gap),int(h))
                cells.append({"shock_bps":shock,"gap_bps":gap,"horizon_min":h,
                              "eligible":eligible(r),"result":r})
    selected,pre=holm(cells)
    selected_summary=[
        {"shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
         "n":x["result"]["n"],"win_rate":x["result"]["win_rate"],
         "mean_gross_bps":x["result"]["mean_gross_bps"],
         "p":x["result"]["p_value_vs_50"],"holm_cutoff":x.get("holm_cutoff"),
         "mean_net_12bps":x["result"]["cost_scenarios_mean_net_bps"]["12"]}
        for x in selected
    ]
    report={
        "family_id":RULE["family_id"],"version":RULE["version"],
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "rule_sha256":sha_file(RULE_PATH),"binding_sha256":sha_file(BIND_PATH),
        "window":{"start":RULE["discovery_start"],"end_exclusive":RULE["discovery_end_exclusive"]},
        "coverage":{"mexc_rows":len(mexc),"binance_rows":len(binance),"bitget_rows":len(bitget),
                    "bybit_rows":len(bybit),"exact_common_minutes":len(common),
                    "first_common_utc":datetime.fromtimestamp(common[0],tz=timezone.utc).isoformat(),
                    "last_common_utc":datetime.fromtimestamp(common[-1],tz=timezone.utc).isoformat()},
        "source_hashes":{"binance":bh,"bybit":yh,"bitget":gh,"mexc":mh},
        "cells":cells,"pre_holm_eligible_count":pre,
        "holm_selected_count":len(selected),"holm_selected":selected_summary,
        "verdict":"GOLD_CROSSVENUE_DISCOVERY_CANDIDATES_FOUND" if selected else "NO_GOLD_CROSSVENUE_DISCOVERY_CANDIDATE_AT_FROZEN_V08_GATE",
        "retrospective_oos_opened":False,"parameter_rescue_authorized":False,
        "live_trading_authorized":False
    }
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"MEXC_GOLD_CONSENSUS_LEADLAG_CLOSEOUT_V08.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    with (OUT/"MEXC_GOLD_CONSENSUS_LEADLAG_MATRIX_V08.csv").open("w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["shock_bps","gap_bps","horizon_min","n","win_rate","mean_gross_bps","p_value_vs_50","eligible","holm_selected","mean_net_12bps"])
        w.writeheader()
        ids={(x["shock_bps"],x["gap_bps"],x["horizon_min"]) for x in selected}
        for x in cells:
            r=x["result"]
            w.writerow({"shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
                        "n":r["n"],"win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
                        "p_value_vs_50":r["p_value_vs_50"],"eligible":x["eligible"],
                        "holm_selected":(x["shock_bps"],x["gap_bps"],x["horizon_min"]) in ids,
                        "mean_net_12bps":r["cost_scenarios_mean_net_bps"]["12"]})
    print(json.dumps({"verdict":report["verdict"],"exact_common_minutes":len(common),
                      "pre_holm_eligible_count":pre,"holm_selected_count":len(selected),
                      "selected":selected_summary,"retrospective_oos_opened":False,
                      "live_trading_authorized":False},indent=2,sort_keys=True))

if __name__=="__main__": main()

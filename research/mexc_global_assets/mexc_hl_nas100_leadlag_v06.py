#!/usr/bin/env python3
"""MEXC-HL-NAS100-LEADLAG-001 V0.6 frozen discovery runner.

Public/no-auth market data only.
No accounts, wallets, private endpoints, orders, mutation or live trading.
"""
from __future__ import annotations
import csv, hashlib, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
import requests

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_HL_NAS100_LEADLAG_RULE_V0.6.json"
BIND_PATH=HERE/"MEXC_HL_NAS100_SOURCE_BINDING_V0.5.1.json"
OUT=Path("artifacts/mexc_global_assets/mexc_hl_nas100_leadlag_v06")
MEXC="https://api.mexc.com"
HL="https://api.hyperliquid.xyz/info"
UA="CryptoLab-MEXC-HL-NAS100-LeadLag/0.6"
STEP=60
RULE=json.loads(RULE_PATH.read_text(encoding="utf-8"))
BIND=json.loads(BIND_PATH.read_text(encoding="utf-8"))

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

START=ts(RULE["discovery_start"])
END=ts(RULE["discovery_end_exclusive"])

def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def get_mexc(path, params, retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(MEXC+path,params=params,headers={"User-Agent":UA},timeout=30)
            if r.status_code!=200:
                raise RuntimeError(f"MEXC HTTP {r.status_code}: {r.content[:300]!r}")
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"MEXC non-success: {j}")
            return r.content,j
        except Exception as e:
            last=e; time.sleep(0.7*(i+1))
    raise last

def post_hl(payload,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.post(HL,json=payload,headers={"User-Agent":UA,"Content-Type":"application/json"},timeout=30)
            if r.status_code!=200:
                raise RuntimeError(f"HL HTTP {r.status_code}: {r.content[:300]!r}")
            return r.content,r.json()
        except Exception as e:
            last=e; time.sleep(0.7*(i+1))
    raise last

def fetch_mexc():
    out={}
    raw_hashes=[]
    raw_start=START-2*STEP
    last_raw=END-2*STEP
    cur=raw_start
    request_count=0
    # comfortably below documented 2000-row maximum
    span=1500*STEP
    while cur<=last_raw:
        e=min(cur+span,last_raw)
        raw,j=get_mexc(f"/api/v1/contract/kline/{RULE['mexc_symbol']}",
                       {"interval":"Min1","start":cur,"end":e})
        raw_hashes.append(sha_bytes(raw)); request_count+=1
        d=j.get("data") or {}
        for s,p in zip(d.get("time") or [],d.get("close") or []):
            try: raw_s=int(s)
            except Exception: continue
            if raw_s<cur or raw_s>e:
                raise RuntimeError("MEXC_TIMESTAMP_OUTSIDE_REQUEST")
            observable=raw_s+STEP
            if observable>=END:
                raise RuntimeError("MEXC_PROTECTED_OBSERVABLE_TIMESTAMP")
            try: px=float(p)
            except Exception: continue
            if px>0: out[observable]=px
        cur=e+STEP
        time.sleep(0.05)
    return out,{"requests":request_count,"raw_sha256":raw_hashes}

def fetch_hl():
    raw_start_ms=(START-2*STEP)*1000
    last_raw_ms=(END-2*STEP)*1000
    payload={"type":"candleSnapshot","req":{
        "coin":RULE["hyperliquid_coin"],"interval":"1m",
        "startTime":raw_start_ms,"endTime":last_raw_ms
    }}
    raw,j=post_hl(payload)
    if not isinstance(j,list):
        raise RuntimeError("HL_CANDLE_PAYLOAD_NOT_LIST")
    out={}
    for row in j:
        try:
            raw_t=int(row["t"])
            if raw_t<raw_start_ms or raw_t>last_raw_ms:
                raise RuntimeError("HL_TIMESTAMP_OUTSIDE_REQUEST")
            observable=raw_t//1000+STEP
            if observable>=END:
                raise RuntimeError("HL_PROTECTED_OBSERVABLE_TIMESTAMP")
            px=float(row["c"])
        except RuntimeError:
            raise
        except Exception:
            continue
        if px>0: out[observable]=px
    return out,{"requests":1,"raw_sha256":sha_bytes(raw),"rows_raw":len(j)}

def logsumexp(xs):
    m=max(xs); return m+math.log(sum(math.exp(x-m) for x in xs))

def binom_tail_half(w,n):
    if n<=0:return None
    ln2=math.log(2.0)
    logs=[math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*ln2 for k in range(w,n+1)]
    return min(1.0,math.exp(logsumexp(logs)))

def mean(xs):
    return sum(xs)/len(xs) if xs else None

def median(xs):
    if not xs:return None
    y=sorted(xs); n=len(y)
    return y[n//2] if n%2 else (y[n//2-1]+y[n//2])/2

def thirds(xs):
    n=len(xs)
    if not n:return [None,None,None]
    cuts=[0,n//3,(2*n)//3,n]
    return [mean(xs[cuts[i]:cuts[i+1]]) for i in range(3)]

def sgn(x):
    return 1 if x>0 else (-1 if x<0 else 0)

def score(mexc,hl,shock,gap,hmin):
    h=hmin*60
    times=sorted(set(mexc)&set(hl))
    next_allowed=START
    vals=[]; hlsh=[]; gaps=[]
    for t in times:
        if t<START or t>=END or t<next_allowed: continue
        if t-STEP not in mexc or t-STEP not in hl: continue
        exit_t=t+h
        if exit_t>=END or exit_t not in mexc: continue
        hr=10000*(hl[t]/hl[t-STEP]-1)
        mr=10000*(mexc[t]/mexc[t-STEP]-1)
        lg=hr-mr
        if abs(hr)<shock: continue
        if sgn(lg)!=sgn(hr): continue
        if abs(lg)<gap: continue
        side=sgn(hr)
        gross=side*10000*(mexc[exit_t]/mexc[t]-1)
        vals.append(gross); hlsh.append(hr); gaps.append(lg)
        next_allowed=t+h
    n=len(vals); wins=sum(x>0 for x in vals)
    return {
        "n":n,"wins":wins,"losses":n-wins,
        "win_rate":wins/n if n else None,
        "mean_gross_bps":mean(vals),
        "median_gross_bps":median(vals),
        "p_value_vs_50":binom_tail_half(wins,n) if n else None,
        "third_means_gross_bps":thirds(vals),
        "mean_abs_hl_shock_bps":mean([abs(x) for x in hlsh]),
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
        if x["result"]["p_value_vs_50"]<=cutoff:
            selected.append(x)
        else:
            break
    return selected,m

def main():
    forbidden={"MEXC_API_KEY","MEXC_SECRET_KEY","API_KEY","SECRET_KEY","PRIVATE_KEY"}
    if any(k.upper() in forbidden for k in os.environ):
        raise SystemExit("FAIL_CLOSED: credential-like environment variable detected")
    if BIND.get("verdict")!="HYPERLIQUID_NAS100_SOURCE_PASS__XYZ_XYZ100":
        raise SystemExit("FAIL_CLOSED: source binding not PASS")
    if RULE.get("outcomes_opened_at_freeze")!=0 or RULE.get("live_trading_authorized") is not False:
        raise SystemExit("FAIL_CLOSED: rule governance invalid")

    print("RULE_SHA256=",sha_file(RULE_PATH))
    print("BINDING_SHA256=",sha_file(BIND_PATH))
    print("DISCOVERY_WINDOW=",RULE["discovery_start"],RULE["discovery_end_exclusive"])

    mexc,mm=fetch_mexc()
    hl,hm=fetch_hl()
    overlap=sorted(set(mexc)&set(hl))
    disc_overlap=[t for t in overlap if START<=t<END]
    if not disc_overlap:
        raise RuntimeError("ZERO_EXACT_CLOCK_OVERLAP")
    # Require dense 1m coverage. A tiny number of market pauses/gaps may exist.
    expected=(END-START)//60
    coverage=len(disc_overlap)/expected
    if coverage<0.95:
        raise RuntimeError(f"CLOCK_COVERAGE_FAIL:{coverage}")

    cells=[]
    for shock in RULE["signal"]["hl_shock_thresholds_bps"]:
        for gap in RULE["signal"]["lag_gap_thresholds_bps"]:
            for h in RULE["signal"]["horizons_min"]:
                r=score(mexc,hl,float(shock),float(gap),int(h))
                cells.append({"shock_bps":shock,"gap_bps":gap,"horizon_min":h,
                              "eligible":eligible(r),"result":r})
    selected,eligible_count=holm(cells)

    OUT.mkdir(parents=True,exist_ok=True)
    report={
      "family_id":RULE["family_id"],"version":RULE["version"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),"binding_sha256":sha_file(BIND_PATH),
      "source_binding_verdict":BIND["verdict"],
      "window":{"start":RULE["discovery_start"],"end_exclusive":RULE["discovery_end_exclusive"]},
      "coverage":{
        "expected_minutes":expected,"exact_overlap_minutes":len(disc_overlap),
        "coverage_ratio":coverage,
        "first_overlap_utc":datetime.fromtimestamp(disc_overlap[0],tz=timezone.utc).isoformat(),
        "last_overlap_utc":datetime.fromtimestamp(disc_overlap[-1],tz=timezone.utc).isoformat(),
        "mexc_rows":len(mexc),"hl_rows":len(hl),"mexc_source":mm,"hl_source":hm
      },
      "cells":cells,
      "pre_holm_eligible_count":eligible_count,
      "holm_selected_count":len(selected),
      "holm_selected":[
        {"shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
         "p":x["result"]["p_value_vs_50"],"holm_cutoff":x.get("holm_cutoff"),
         "n":x["result"]["n"],"mean_gross_bps":x["result"]["mean_gross_bps"],
         "win_rate":x["result"]["win_rate"]}
        for x in selected
      ],
      "verdict":"CROSSVENUE_DISCOVERY_CANDIDATES_FOUND" if selected else "NO_CROSSVENUE_DISCOVERY_CANDIDATE_AT_FROZEN_V04_GATE",
      "promotion_ceiling":RULE["promotion_ceiling"],
      "retrospective_oos_opened":False,
      "parameter_rescue_authorized":False,
      "private_endpoints_used":False,"account_reads":False,"wallets_used":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False
    }
    (OUT/"MEXC_HL_NAS100_LEADLAG_CLOSEOUT_V06.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    with (OUT/"MEXC_HL_NAS100_LEADLAG_MATRIX_V06.csv").open("w",newline="",encoding="utf-8") as f:
        field=["shock_bps","gap_bps","horizon_min","n","win_rate","mean_gross_bps","median_gross_bps","p_value_vs_50","eligible","holm_selected"]
        w=csv.DictWriter(f,fieldnames=field); w.writeheader()
        ids={(x["shock_bps"],x["gap_bps"],x["horizon_min"]) for x in selected}
        for x in cells:
            r=x["result"]; key=(x["shock_bps"],x["gap_bps"],x["horizon_min"])
            w.writerow({"shock_bps":x["shock_bps"],"gap_bps":x["gap_bps"],"horizon_min":x["horizon_min"],
                        "n":r["n"],"win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
                        "median_gross_bps":r["median_gross_bps"],"p_value_vs_50":r["p_value_vs_50"],
                        "eligible":x["eligible"],"holm_selected":key in ids})
    print(json.dumps({
      "verdict":report["verdict"],"coverage_ratio":coverage,
      "pre_holm_eligible_count":eligible_count,"holm_selected_count":len(selected),
      "selected":report["holm_selected"],"retrospective_oos_opened":False,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()

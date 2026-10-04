#!/usr/bin/env python3
"""
GLOBAL-ASSET-SP500-BASIS-001 V0.2 — frozen September holdout.

Single preselected cell only:
SPX500_USDT / FADE_BASIS / 5 bps / 15 min.

Research only. Public/no-auth MEXC market endpoints only.
"""
from __future__ import annotations
import hashlib, json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
import requests

BASE="https://api.mexc.com"
HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"GLOBAL_ASSET_SP500_HOLDOUT_RULE_V0.2.json"
DEFAULT_RECEIPT=Path("artifacts/mexc_global_assets/source_gate_v02/GLOBAL_ASSET_SOURCE_GATE_RECEIPT_V01.json")
OUT=Path("artifacts/mexc_global_assets/sp500_holdout_v02")
STEP=300

RULE=json.loads(RULE_PATH.read_text(encoding="utf-8"))
SYMBOL=RULE["symbol"]
TH=float(RULE["threshold_bps"])
H=int(RULE["horizon_min"])*60

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

START=ts(RULE["holdout_start"])
END=ts(RULE["holdout_end_exclusive"])

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def fetch_json(path, params, retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(BASE+path, params=params, timeout=30, headers={"User-Agent":"CryptoLab-SP500-Holdout/0.2"})
            r.raise_for_status()
            j=r.json()
            if not isinstance(j,dict) or j.get("success") is not True:
                raise RuntimeError(f"non-success payload: {j}")
            return j
        except Exception as e:
            last=e
            time.sleep(0.7*(i+1))
    raise last

def fetch_leg(path):
    out={}
    chunk=5*86400
    cur=START-STEP
    last_raw_start=END-2*STEP
    request_count=0
    while cur<=last_raw_start:
        e=min(cur+chunk,last_raw_start)
        j=fetch_json(path,{"interval":"Min5","start":cur,"end":e})
        request_count+=1
        d=j.get("data") or {}
        times=d.get("time") or []
        closes=d.get("close") or []
        for s,p in zip(times,closes):
            try:
                raw_s=int(s)
            except Exception:
                continue
            if raw_s<cur or raw_s>e:
                raise RuntimeError("SOURCE_RETURNED_TIMESTAMP_OUTSIDE_REQUEST")
            mapped=raw_s+STEP
            if mapped>=END:
                raise RuntimeError("SOURCE_RETURNED_PROTECTED_OBSERVABLE_TIMESTAMP")
            if mapped<START:
                continue
            try:
                px=float(p)
            except Exception:
                continue
            if px<=0:
                continue
            out[mapped]=px
        cur=e+STEP
        time.sleep(0.08)
    return out,request_count

def logsumexp(xs):
    m=max(xs)
    return m+math.log(sum(math.exp(x-m) for x in xs))

def binom_tail_half(w,n):
    if n<=0: return None
    ln2=math.log(2.0)
    logs=[
        math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*ln2
        for k in range(w,n+1)
    ]
    return min(1.0,math.exp(logsumexp(logs)))

def mean(xs):
    return sum(xs)/len(xs) if xs else None

def median(xs):
    if not xs: return None
    y=sorted(xs); n=len(y)
    return y[n//2] if n%2 else (y[n//2-1]+y[n//2])/2

def main():
    if any(k for k in os.environ if k.upper() in {"MEXC_API_KEY","MEXC_SECRET_KEY","API_KEY","SECRET_KEY"}):
        raise SystemExit("FAIL_CLOSED: credential-like environment variable detected")

    receipt_path=Path(os.environ.get("GLOBAL_ASSET_SOURCE_RECEIPT",str(DEFAULT_RECEIPT)))
    if not receipt_path.exists():
        raise SystemExit("FAIL_CLOSED: source receipt missing")
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("verdict")!="MEXC_MARKET_SOURCE_PASS":
        raise SystemExit("FAIL_CLOSED: source receipt not PASS")
    if any(receipt.get(k) for k in ["auth_used","private_endpoints_used","account_reads","orders","exchange_mutation"]):
        raise SystemExit("FAIL_CLOSED: governance violation in source receipt")

    rule_sha=sha(RULE_PATH)
    receipt_sha=sha(receipt_path)
    print("RULE_SHA256=",rule_sha)
    print("SOURCE_RECEIPT_SHA256=",receipt_sha)
    print("HOLDOUT=",RULE["holdout_start"],RULE["holdout_end_exclusive"])
    print("CELL=SP500/5bps/15m/FADE_BASIS_ONLY")

    contract,cr=fetch_leg(f"/api/v1/contract/kline/{SYMBOL}")
    index,ir=fetch_leg(f"/api/v1/contract/kline/index_price/{SYMBOL}")
    overlap=sorted(set(contract)&set(index))
    if not overlap:
        raise RuntimeError("ZERO_CONTRACT_INDEX_OVERLAP")
    if min(overlap)<START or max(overlap)>=END:
        raise RuntimeError("HOLDOUT_TIME_BOUNDARY_VIOLATION")

    rets=[]; entries=[]; exit_bases=[]; times=[]; converged=0
    next_allowed=START
    for t in overlap:
        if t<START or t>=END or t<next_allowed:
            continue
        exit_t=t+H
        if exit_t>=END or exit_t not in contract or exit_t not in index:
            continue
        c0,i0=contract[t],index[t]
        c1,i1=contract[exit_t],index[exit_t]
        basis=10000.0*(c0/i0-1.0)
        if abs(basis)<TH:
            continue
        side=-1.0 if basis>0 else 1.0
        gross=side*10000.0*(c1/c0-1.0)
        exit_basis=10000.0*(c1/i1-1.0)
        rets.append(gross); entries.append(basis); exit_bases.append(exit_basis); times.append(t)
        if abs(exit_basis)<abs(basis):
            converged+=1
        next_allowed=t+H

    n=len(rets); wins=sum(x>0 for x in rets); losses=n-wins
    half=n//2
    half_means=[mean(rets[:half]),mean(rets[half:])] if half else [None,mean(rets)]
    wr=wins/n if n else None
    p=binom_tail_half(wins,n) if n else None
    mg=mean(rets)
    gates={
        "min_n":n>=int(RULE["gates"]["min_n"]),
        "mean_gross_gt_0":mg is not None and mg>0,
        "win_rate_gt_50":wr is not None and wr>0.5,
        "p_lt_0_05":p is not None and p<float(RULE["gates"]["exact_one_sided_binomial_p_lt"]),
        "both_halves_nonnegative":all(x is not None and x>=0 for x in half_means),
    }
    passed=all(gates.values())

    OUT.mkdir(parents=True,exist_ok=True)
    report={
        "family_id":RULE["family_id"],
        "version":RULE["version"],
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "rule_sha256":rule_sha,
        "source_receipt_sha256":receipt_sha,
        "source_gate_verdict":receipt["verdict"],
        "symbol":SYMBOL,
        "signal_mode":RULE["signal_mode"],
        "threshold_bps":TH,
        "horizon_min":RULE["horizon_min"],
        "holdout":{"start":RULE["holdout_start"],"end_exclusive":RULE["holdout_end_exclusive"]},
        "coverage":{
            "contract_rows":len(contract),
            "index_rows":len(index),
            "overlap_rows":len(overlap),
            "first_overlap_utc":datetime.fromtimestamp(overlap[0],tz=timezone.utc).isoformat(),
            "last_overlap_utc":datetime.fromtimestamp(overlap[-1],tz=timezone.utc).isoformat(),
            "contract_requests":cr,
            "index_requests":ir,
        },
        "result":{
            "n":n,"wins":wins,"losses":losses,"win_rate":wr,
            "mean_gross_bps":mg,
            "median_gross_bps":median(rets),
            "p_value_vs_50":p,
            "half_means_gross_bps":half_means,
            "convergence_rate":converged/n if n else None,
            "median_entry_basis_abs_bps":median([abs(x) for x in entries]),
            "cost_scenarios_mean_net_bps":{
                str(c):(mg-float(c) if mg is not None else None)
                for c in RULE["cost_scenarios_roundtrip_bps"]
            }
        },
        "gates":gates,
        "verdict":RULE["promotion_if_pass"] if passed else RULE["failure_if_fail"],
        "pass":passed,
        "parameter_rescue_allowed":False,
        "live_trading_authorized":False,
        "private_endpoints_used":False,
        "account_reads":False,
        "orders":False,
        "exchange_mutation":False,
    }
    (OUT/"GLOBAL_ASSET_SP500_HOLDOUT_CLOSEOUT_V02.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({
        "verdict":report["verdict"],
        "n":n,"wins":wins,"win_rate":wr,"mean_gross_bps":mg,"p_value_vs_50":p,
        "half_means_gross_bps":half_means,"gates":gates,
        "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()

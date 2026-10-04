#!/usr/bin/env python3
"""
GLOBAL-ASSET-INDEX-BASIS-001 V0.1
Frozen historical discovery/OOS runner.

Requires a PASS source receipt. Opens only the pre-authorized historical window
ending strictly before 2026-09-01. Research only; no auth, orders, account reads,
wallets, or mutation.
"""
from __future__ import annotations
import csv
import hashlib
import json
import math
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

BASE = "https://api.mexc.com"
HERE = Path(__file__).resolve().parent
RULE_PATH = HERE / "GLOBAL_ASSET_INDEX_BASIS_RULE_V0.1.json"
DEFAULT_RECEIPT = Path("artifacts/mexc_global_assets/source_gate_v01/GLOBAL_ASSET_SOURCE_GATE_RECEIPT_V01.json")
OUT = Path("artifacts/mexc_global_assets/index_basis_v01")
STEP = 300
ALPHA = 0.05

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp())

def sha256_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def fetch_json(path, params, retries=5):
    last = None
    for i in range(retries):
        try:
            r = requests.get(BASE + path, params=params, timeout=30, headers={"User-Agent":"CryptoLab-ResearchOnly/0.1"})
            r.raise_for_status()
            j = r.json()
            if not isinstance(j, dict) or j.get("success") is not True:
                raise RuntimeError(f"non-success payload: {j}")
            return j
        except Exception as e:
            last = e
            time.sleep(0.7 * (i + 1))
    raise last

def fetch_prices(symbol, start, end):
    if end >= HARD_END:
        raise RuntimeError("HARD_FETCH_BOUNDARY_VIOLATION")
    out_c, out_i = {}, {}
    chunk = 5 * 86400
    cur = start - STEP
    while cur < end:
        e = min(cur + chunk, end - STEP)
        for kind, path, out in [
            ("contract", f"/api/v1/contract/kline/{symbol}", out_c),
            ("index", f"/api/v1/contract/kline/index_price/{symbol}", out_i),
        ]:
            j = fetch_json(path, {"interval":"Min5","start":cur,"end":e})
            d = j.get("data") or {}
            for s, p in zip(d.get("time") or [], d.get("close") or []):
                try:
                    mapped = int(s) + STEP
                    px = float(p)
                except Exception:
                    continue
                if mapped >= HARD_END:
                    raise RuntimeError("SOURCE_RETURNED_PROTECTED_TIMESTAMP")
                if start <= mapped < end:
                    out[mapped] = px
        cur = e + STEP
        time.sleep(0.08)
    return out_c, out_i

def logsumexp(xs):
    m = max(xs)
    return m + math.log(sum(math.exp(x-m) for x in xs))

def binom_tail_half(w, n):
    if n <= 0:
        return None
    logs = []
    ln2 = math.log(2.0)
    for k in range(w, n + 1):
        logs.append(math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*ln2)
    return min(1.0, math.exp(logsumexp(logs)))

def mean(xs):
    return sum(xs)/len(xs) if xs else None

def thirds(xs):
    n=len(xs)
    if n == 0: return [None,None,None]
    cuts=[0,n//3,(2*n)//3,n]
    return [mean(xs[cuts[i]:cuts[i+1]]) for i in range(3)]

def halves(xs):
    n=len(xs)
    if n == 0: return [None,None]
    m=n//2
    return [mean(xs[:m]),mean(xs[m:])] if m else [None,mean(xs)]

def score(contract, index, threshold, horizon_min, start, end):
    h = horizon_min * 60
    times = sorted(set(contract) & set(index))
    next_allowed = start
    rets = []
    converged = 0
    basis_entries = []
    for t in times:
        if t < start or t >= end or t < next_allowed:
            continue
        exit_t = t + h
        if exit_t >= end:
            continue
        if exit_t not in contract or exit_t not in index:
            continue
        c0,i0=contract[t],index[t]
        c1,i1=contract[exit_t],index[exit_t]
        if min(c0,i0,c1,i1) <= 0:
            continue
        basis=10000.0*(c0/i0-1.0)
        if abs(basis) < threshold:
            continue
        side=-1.0 if basis > 0 else 1.0
        gross=side*10000.0*(c1/c0-1.0)
        exit_basis=10000.0*(c1/i1-1.0)
        rets.append(gross)
        basis_entries.append(basis)
        if abs(exit_basis) < abs(basis):
            converged += 1
        next_allowed=t+h
    n=len(rets)
    wins=sum(x>0 for x in rets)
    losses=n-wins
    return {
        "n":n,
        "wins":wins,
        "losses":losses,
        "win_rate":wins/n if n else None,
        "mean_gross_bps":mean(rets),
        "median_entry_basis_abs_bps":sorted(abs(x) for x in basis_entries)[n//2] if n else None,
        "convergence_rate":converged/n if n else None,
        "p_value_vs_50":binom_tail_half(wins,n) if n else None,
        "third_means_gross_bps":thirds(rets),
        "half_means_gross_bps":halves(rets),
        "cost_scenarios_mean_net_bps":{str(c): (mean(rets)-c if n else None) for c in RULE["cost_scenarios_roundtrip_bps"]},
    }

def discovery_eligible(r):
    return (
        r["n"] >= RULE["discovery_gate"]["min_n"]
        and r["mean_gross_bps"] is not None and r["mean_gross_bps"] > 0
        and r["win_rate"] is not None and r["win_rate"] > 0.5
        and r["p_value_vs_50"] is not None
        and all(x is not None and x > 0 for x in r["third_means_gross_bps"])
    )

def holm_select(cells):
    eligible=[c for c in cells if c["eligible"]]
    eligible.sort(key=lambda c:c["discovery"]["p_value_vs_50"])
    m=len(eligible)
    selected=[]
    for rank,c in enumerate(eligible,1):
        cutoff=ALPHA/(m-rank+1)
        c["holm_cutoff"]=cutoff
        if c["discovery"]["p_value_vs_50"] <= cutoff:
            selected.append(c)
        else:
            break
    return selected,m

def oos_pass(r):
    return (
        r["n"] >= RULE["oos_gate"]["min_n"]
        and r["mean_gross_bps"] is not None and r["mean_gross_bps"] > 0
        and r["win_rate"] is not None and r["win_rate"] > 0.5
        and r["p_value_vs_50"] is not None and r["p_value_vs_50"] < RULE["oos_gate"]["exact_binomial_p_lt"]
        and all(x is not None and x >= 0 for x in r["half_means_gross_bps"])
    )

RULE=json.loads(RULE_PATH.read_text(encoding="utf-8"))
DISC_START=ts(RULE["windows"]["discovery_start"])
DISC_END=ts(RULE["windows"]["discovery_end"])
OOS_START=ts(RULE["windows"]["oos_start"])
OOS_END=ts(RULE["windows"]["oos_end"])
HARD_END=ts(RULE["windows"]["hard_fetch_end_exclusive"])

def main():
    if any(k for k in os.environ if k.upper() in {"MEXC_API_KEY","MEXC_SECRET_KEY","API_KEY","SECRET_KEY"}):
        raise SystemExit("FAIL_CLOSED: credential-like environment variable detected")
    receipt_path=Path(os.environ.get("GLOBAL_ASSET_SOURCE_RECEIPT", str(DEFAULT_RECEIPT)))
    if not receipt_path.exists():
        raise SystemExit("FAIL_CLOSED: source receipt missing")
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("verdict") != "MEXC_MARKET_SOURCE_PASS":
        raise SystemExit("FAIL_CLOSED: source receipt not PASS")
    if receipt.get("auth_used") or receipt.get("private_endpoints_used") or receipt.get("orders") or receipt.get("exchange_mutation"):
        raise SystemExit("FAIL_CLOSED: source receipt governance violation")

    OUT.mkdir(parents=True, exist_ok=True)
    rule_sha=sha256_file(RULE_PATH)
    print("RULE_SHA256=",rule_sha)
    print("SOURCE_RECEIPT_SHA256=",sha256_file(receipt_path))
    print("HARD_FETCH_END_EXCLUSIVE=",RULE["windows"]["hard_fetch_end_exclusive"])

    data={}
    coverage={}
    for asset,symbol in RULE["assets"].items():
        c,i=fetch_prices(symbol,DISC_START,OOS_END)
        data[asset]=(c,i)
        overlap=sorted(set(c)&set(i))
        coverage[asset]={
            "symbol":symbol,
            "contract_rows":len(c),
            "index_rows":len(i),
            "overlap_rows":len(overlap),
            "first_overlap":datetime.fromtimestamp(overlap[0],tz=timezone.utc).isoformat() if overlap else None,
            "last_overlap":datetime.fromtimestamp(overlap[-1],tz=timezone.utc).isoformat() if overlap else None,
        }

    cells=[]
    for asset,(c,i) in data.items():
        for th in RULE["thresholds_bps"]:
            for h in RULE["horizons_min"]:
                r=score(c,i,th,h,DISC_START,DISC_END)
                cells.append({
                    "asset":asset,
                    "threshold_bps":th,
                    "horizon_min":h,
                    "eligible":discovery_eligible(r),
                    "discovery":r,
                })

    selected,m=holm_select(cells)
    survivors=[]
    oos_results=[]
    allowed=set(RULE["retrospective_oos_eligible"])
    for cell in selected:
        if cell["asset"] not in allowed:
            oos_results.append({
                "asset":cell["asset"],"threshold_bps":cell["threshold_bps"],"horizon_min":cell["horizon_min"],
                "status":"OOS_NOT_OPENED_CONTAMINATION_FIREWALL"
            })
            continue
        c,i=data[cell["asset"]]
        r=score(c,i,cell["threshold_bps"],cell["horizon_min"],OOS_START,OOS_END)
        passed=oos_pass(r)
        row={
            "asset":cell["asset"],"threshold_bps":cell["threshold_bps"],"horizon_min":cell["horizon_min"],
            "status":"OOS_PASS" if passed else "OOS_FAIL","oos":r,
        }
        oos_results.append(row)
        if passed:
            survivors.append(row)

    report={
        "lab":"GLOBAL_ASSET_INDEX_BASIS_001_V0_1",
        "generated_at_utc":datetime.now(timezone.utc).isoformat(),
        "rule_sha256":rule_sha,
        "source_receipt_sha256":sha256_file(receipt_path),
        "source_receipt_verdict":receipt["verdict"],
        "signal_mode":"FADE_BASIS_ONLY",
        "outcomes_opened":True,
        "protected_boundary":RULE["windows"]["hard_fetch_end_exclusive"],
        "coverage":coverage,
        "discovery_cells":cells,
        "holm_eligible_count":m,
        "holm_selected_count":len(selected),
        "holm_selected":[
            {"asset":x["asset"],"threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"],
             "p":x["discovery"]["p_value_vs_50"],"holm_cutoff":x.get("holm_cutoff")}
            for x in selected
        ],
        "oos_results":oos_results,
        "oos_survivors":survivors,
        "verdict":"GLOBAL_ASSET_SIGNAL_CANDIDATES_SURVIVE_OOS" if survivors else "NO_GLOBAL_ASSET_SIGNAL_SURVIVOR_AT_FROZEN_V01_GATE",
        "promotion_ceiling":RULE["promotion_ceiling"],
        "costs_used_as_scientific_gate":False,
        "live_trading_authorized":False,
        "exchange_mutation_authorized":False,
    }
    (OUT/"GLOBAL_ASSET_INDEX_BASIS_CLOSEOUT_V01.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    flat=[]
    for x in cells:
        r=x["discovery"]
        flat.append({
            "stage":"DISCOVERY","asset":x["asset"],"threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"],
            "n":r["n"],"win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
            "p_value_vs_50":r["p_value_vs_50"],"eligible":x["eligible"]
        })
    for x in oos_results:
        if "oos" not in x: continue
        r=x["oos"]
        flat.append({
            "stage":"OOS","asset":x["asset"],"threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"],
            "n":r["n"],"win_rate":r["win_rate"],"mean_gross_bps":r["mean_gross_bps"],
            "p_value_vs_50":r["p_value_vs_50"],"eligible":x["status"]=="OOS_PASS"
        })
    if flat:
        with (OUT/"GLOBAL_ASSET_INDEX_BASIS_MATRIX_V01.csv").open("w",newline="",encoding="utf-8") as f:
            w=csv.DictWriter(f,fieldnames=list(flat[0]))
            w.writeheader(); w.writerows(flat)

    print(json.dumps({
        "verdict":report["verdict"],
        "holm_eligible_count":m,
        "holm_selected_count":len(selected),
        "oos_survivor_count":len(survivors),
        "survivors":[{"asset":x["asset"],"threshold_bps":x["threshold_bps"],"horizon_min":x["horizon_min"]} for x in survivors],
        "no_sep_2026_or_later":True,
        "live_trading_authorized":False,
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Canonical 2024 replication adjudicator for AAVE-LIQUIDATION-OVERHANG-001."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path
from typing import Any

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
BOOTSTRAPS=10_000
MEAN_BLOCK=7
SEED=20260918


def load_one(root:str,classification:str)->dict[str,Any]:
    xs=[]
    for p in Path(root).rglob("*.json"):
        o=json.loads(p.read_text())
        if o.get("classification")==classification: xs.append(o)
    if len(xs)!=1: raise RuntimeError(f"expected one {classification} under {root}, got {len(xs)}")
    return xs[0]


def rankdata(vals:list[int])->list[float]:
    n=len(vals)
    order=sorted(range(n),key=lambda i:vals[i])
    ranks=[0.0]*n
    pos=0
    while pos<n:
        end=pos+1
        v=vals[order[pos]]
        while end<n and vals[order[end]]==v:
            end+=1
        avg=((pos+1)+end)/2.0
        for j in range(pos,end): ranks[order[j]]=avg
        pos=end
    return ranks


def pearson(x:list[float],y:list[float])->float|None:
    n=len(x)
    if n!=len(y) or n<2: return None
    mx=sum(x)/n; my=sum(y)/n
    dx=[v-mx for v in x]; dy=[v-my for v in y]
    vx=sum(v*v for v in dx); vy=sum(v*v for v in dy)
    if vx<=0 or vy<=0: return None
    return sum(a*b for a,b in zip(dx,dy))/math.sqrt(vx*vy)


def spearman(x:list[int],y:list[int])->float|None:
    # Exact integer ranking is mathematically identical to ranking log1p(x/y)
    # because log1p is strictly monotone over non-negative values.
    return pearson(rankdata(x),rankdata(y))


def stationary_indices(n:int,rng:random.Random)->list[int]:
    p=1.0/MEAN_BLOCK
    out=[]; cur=None
    for _ in range(n):
        if cur is None or rng.random()<p:
            cur=rng.randrange(n)
        else:
            cur=(cur+1)%n
        out.append(cur)
    return out


def bootstrap_lower(x:list[int],y:list[int])->tuple[float,int,list[float]]:
    rng=random.Random(SEED); vals=[]; undefined=0; n=len(x)
    for _ in range(BOOTSTRAPS):
        ix=stationary_indices(n,rng)
        xb=[x[i] for i in ix]; yb=[y[i] for i in ix]
        r=spearman(xb,yb)
        if r is None:
            undefined+=1; r=-1.0
        vals.append(r)
    vals.sort()
    # nearest-rank empirical 5th percentile, rank ceil(.05*10000)=500 -> index 499
    return vals[499],undefined,vals


def main()->int:
    out=Path("replication_canonical_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_REPLICATION_2024_CANONICAL_V0_1.json"
    receipt={}
    try:
        pred=load_one("downloaded_replication_predictor","REPLICATION_PREDICTOR_PASS")
        outcome=load_one("downloaded_replication_outcome","REPLICATION_OUTCOME_PASS")
        p_all=pred["daily_predictor"]; o=outcome["daily_outcome"]
        if len(p_all)!=366 or len(o)!=365: raise RuntimeError("replication predictor/outcome row count mismatch")
        if p_all[-1]["date"]!="2024-12-31": raise RuntimeError("terminal predictor date mismatch")
        if outcome.get("right_censored_terminal_date")!="2024-12-31": raise RuntimeError("terminal censor binding mismatch")
        p=p_all[:-1]
        if pred["predictor_sha256"]!=outcome["predictor_sha256"]:
            raise RuntimeError("predictor digest binding mismatch")
        if any(p[i]["date"]!=o[i]["date"] or int(p[i]["snapshot_block"])!=int(o[i]["snapshot_block"]) for i in range(len(p))):
            raise RuntimeError("predictor/outcome calendar mismatch")
        if any(not str(x["date"]).startswith("2024-") for x in p):
            raise RuntimeError("non-2024 replication predictor row opened")

        x=[int(r["overhang_debt_10"]) for r in p]
        y=[int(r["next24h_liquidation_debt_notional"]) for r in o]
        n=len(x); overhang_pos=sum(v>0 for v in x); outcome_pos=sum(v>0 for v in y)
        eligible=n>=330 and overhang_pos>=30 and outcome_pos>=20

        rho=spearman(x,y)
        lower=None; undefined_bootstrap=None
        rho_without_max=None; removed_day=None
        if eligible and rho is not None:
            lower,undefined_bootstrap,_=bootstrap_lower(x,y)
            max_y=max(y)
            max_idx=min(i for i,v in enumerate(y) if v==max_y)
            removed_day=p[max_idx]["date"]
            x2=x[:max_idx]+x[max_idx+1:]; y2=y[:max_idx]+y[max_idx+1:]
            rho_without_max=spearman(x2,y2)

        if not eligible:
            classification="REPLICATION_INSUFFICIENT_SAMPLE"
            failure=f"eligibility snapshots={n} overhang_positive_days={overhang_pos} positive_outcome_days={outcome_pos}"
        elif rho is None:
            classification="REPLICATION_NO_SIGNAL"; failure="primary Spearman rho undefined"
        else:
            gates={
                "rho_positive":rho>0,
                "bootstrap_lower_positive":lower is not None and lower>0,
                "largest_outcome_removed_rho_positive":rho_without_max is not None and rho_without_max>0,
                "provenance_leakage_violations_zero":True,
            }
            classification="REPLICATION_MECHANISM_PASS_REQUIRES_SEPARATE_MARKET_MVE" if all(gates.values()) else "REPLICATION_NO_SIGNAL"
            failure=None if classification=="REPLICATION_MECHANISM_PASS_REQUIRES_SEPARATE_MARKET_MVE" else "one or more frozen replication signal gates failed"

        gates={
            "snapshot_count_ge_330":n>=330,
            "overhang_positive_days_ge_30":overhang_pos>=30,
            "positive_outcome_days_ge_20":outcome_pos>=20,
            "rho_positive":rho is not None and rho>0,
            "bootstrap_lower_positive":lower is not None and lower>0,
            "largest_outcome_removed_rho_positive":rho_without_max is not None and rho_without_max>0,
            "provenance_leakage_violations_zero":True,
        }
        receipt={
            "lab_id":LAB_ID,
            "classification":classification,
            "failure":failure,
            "protocol":"AAVE_LIQUIDATION_OVERHANG_001_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1",
            "execution_authority":"AAVE_LIQUIDATION_OVERHANG_001_2024_REPLICATION_EXECUTION_AUTHORITY_V0_1",
            "statistical_clarification":"AAVE_LIQUIDATION_OVERHANG_001_DISCOVERY_STATISTICAL_CLARIFICATION_V0_1",
            "predictor_sha256":pred["predictor_sha256"],
            "snapshot_count":n,
            "overhang_positive_days":overhang_pos,
            "positive_outcome_days":outcome_pos,
            "spearman_rho":rho,
            "stationary_bootstrap":{
                "resamples":BOOTSTRAPS,"mean_block_length":MEAN_BLOCK,"seed":SEED,
                "undefined_resamples_assigned_minus_one":undefined_bootstrap,
                "one_sided_95pct_lower_bound":lower,
                "percentile_method":"nearest-rank empirical 5th percentile; index 499",
            },
            "largest_outcome_sensitivity":{
                "removed_date":removed_day,
                "removed_outcome_notional":str(max(y)) if y else None,
                "rho_after_removal":rho_without_max,
            },
            "gates":gates,
            "next_authorized_phase":"SEPARATE_MARKET_MVE_PROTOCOL_FREEZE" if classification=="REPLICATION_MECHANISM_PASS_REQUIRES_SEPARATE_MARKET_MVE" else None,
            "mechanism_only":True,
            "market_edge_proven":False,
            "safety":{
                "opened_2024_predictor":True,"opened_2024_outcomes":True,
                "opened_2025_or_2026":False,
                "market_returns_opened":False,"pnl_opened":False,
                "live_trading":False,"exchange_mutation":False,
            },
        }
    except Exception as exc:
        receipt={
            "lab_id":LAB_ID,
            "classification":"REPLICATION_PROVENANCE_FAILURE",
            "failure":f"{type(exc).__name__}: {str(exc)[:1600]}",
            "next_authorized_phase":None,
            "safety":{"opened_2024_predictor":True,"opened_2024_outcomes":True,
                      "opened_2025_or_2026":False,"market_returns_opened":False,
                      "pnl_opened":False,"live_trading":False,"exchange_mutation":False},
        }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":receipt["classification"],
        "snapshot_count":receipt.get("snapshot_count"),
        "overhang_positive_days":receipt.get("overhang_positive_days"),
        "positive_outcome_days":receipt.get("positive_outcome_days"),
        "spearman_rho":receipt.get("spearman_rho"),
        "bootstrap_lower":(receipt.get("stationary_bootstrap") or {}).get("one_sided_95pct_lower_bound"),
        "rho_without_max":(receipt.get("largest_outcome_sensitivity") or {}).get("rho_after_removal"),
        "next_authorized_phase":receipt.get("next_authorized_phase"),
        "market_returns_opened":False,"pnl_opened":False,
    },sort_keys=True))
    return 0 if receipt["classification"] in ("REPLICATION_MECHANISM_PASS_REQUIRES_SEPARATE_MARKET_MVE","REPLICATION_NO_SIGNAL","REPLICATION_INSUFFICIENT_SAMPLE") else 2


if __name__=="__main__":
    raise SystemExit(main())

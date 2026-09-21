#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

SIX_H=6*3600
PHASES={
    "discovery":(1640995200,1704067200),
    "replication":(1704067200,1735689600),
}

def read_jsonl_gz(path:Path):
    with gzip.open(path,"rt",encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                yield json.loads(line)

def load_freeze(path:Path)->dict[str,Any]:
    f=json.loads(path.read_text(encoding="utf-8"))
    assert f["lab_id"]=="DEX-LIQUIDITY-PROVISION-001"
    assert f["observation"]["cadence"]=="6H_UTC_NONOVERLAPPING"
    assert f["observation"]["future_volatility"]["minimum_adjacent_minute_returns"]==330
    assert f["inference"]["bootstrap"]["resamples"]==10000
    assert f["inference"]["bootstrap"]["seed"]==20260921
    return f

def combine_source(root:Path,phase:str,shard_count:int=8):
    receipts=[]
    lp=defaultdict(lambda:[0,0,0,0])
    minutes={}
    all_receipts=list(root.glob("**/shard_receipt.json"))
    for sid in range(shard_count):
        matches=[]
        for rp in all_receipts:
            candidate=json.loads(rp.read_text())
            if candidate.get("phase")==phase and int(candidate.get("shard_id",-1))==sid:
                matches.append((rp,candidate))
        if len(matches)!=1:
            raise RuntimeError(f"artifact receipt identity cardinality failure shard={sid} matches={len(matches)}")
        rp,r=matches[0]
        ps=list(rp.parent.glob("minute_prices.jsonl.gz"))
        ls=list(rp.parent.glob("lp_buckets.jsonl.gz"))
        if len(ps)!=1 or len(ls)!=1:
            raise RuntimeError(f"artifact payload cardinality failure shard={sid} prices={len(ps)} lp={len(ls)}")
        if r.get("classification")!="ECONOMIC_SOURCE_SHARD_PASS":
            raise RuntimeError(f"shard {sid} not PASS")
        if int(r.get("shard_count",-1))!=shard_count:
            raise RuntimeError("shard identity mismatch")
        receipts.append(r)
        for row in read_jsonl_gz(ls[0]):
            b=int(row["bucket_start_ts"])
            lp[b][0]+=int(row["mint_liquidity"])
            lp[b][1]+=int(row["burn_liquidity"])
            lp[b][2]+=int(row["mint_count"])
            lp[b][3]+=int(row["burn_count"])
        for row in read_jsonl_gz(ps[0]):
            m=int(row["minute_ts"])
            cand=(int(row["block_number"]),int(row["log_index"]),int(row["sqrtPriceX96"]))
            prev=minutes.get(m)
            if prev is None or cand[:2]>prev[:2]:
                minutes[m]=cand

    receipts.sort(key=lambda x:int(x["shard_id"]))
    if receipts[0]["from_block"]!=receipts[0]["resolved_phase_from_block"]:
        raise RuntimeError("first shard does not begin at resolved phase start")
    if receipts[-1]["to_block"]!=receipts[-1]["resolved_phase_to_block"]:
        raise RuntimeError("last shard does not end at resolved phase end")
    for a,b in zip(receipts,receipts[1:]):
        if int(a["to_block"])+1!=int(b["from_block"]):
            raise RuntimeError("non-contiguous shard block ranges")

    integrity=sum(int(r.get("source_integrity_failures",0)) for r in receipts)
    counts=defaultdict(int)
    for r in receipts:
        for k,v in (r.get("event_counts") or {}).items():
            counts[k]+=int(v)
    return receipts,lp,minutes,integrity,dict(counts)

def build_observations(lp,minutes,phase:str,min_adj:int)->pd.DataFrame:
    start_ts,end_ts=PHASES[phase]
    mts=np.array(sorted(minutes),dtype=np.int64)
    logp=np.empty(len(mts),dtype=float)
    for i,m in enumerate(mts):
        sqrtp=minutes[int(m)][2]
        logp[i]=2.0*(math.log(float(sqrtp))-96.0*math.log(2.0))

    rows=[]
    for bucket in sorted(lp):
        t=int(bucket)+SIX_H
        if int(bucket)<start_ts or t+SIX_H>end_ts:
            continue
        mint,burn,mc,bc=lp[bucket]
        gross=mint+burn
        if gross<=0:
            continue
        withdrawal=(burn-mint)/gross
        lo=int(np.searchsorted(mts,t,side="left"))
        hi=int(np.searchsorted(mts,t+SIX_H,side="left"))
        if hi-lo<2:
            continue
        ts=mts[lo:hi]
        px=logp[lo:hi]
        dt=np.diff(ts)
        rr=np.diff(px)
        adj=rr[dt==60]
        if len(adj)<min_adj:
            continue
        rv=float(np.sqrt(np.sum(adj*adj))*10000.0)
        rows.append({
            "observation_ts":t,
            "feature_bucket_start_ts":int(bucket),
            "mint_liquidity":int(mint),
            "burn_liquidity":int(burn),
            "gross_liquidity_flow":int(gross),
            "withdrawal_score":float(withdrawal),
            "future_rv6h_bps":rv,
            "adjacent_minute_returns":int(len(adj)),
            "mint_count":int(mc),"burn_count":int(bc)
        })
    return pd.DataFrame(rows).sort_values("observation_ts").reset_index(drop=True) if rows else pd.DataFrame()

def point_stats(df:pd.DataFrame)->dict[str,Any]:
    x=df["withdrawal_score"].to_numpy(float)
    y=df["future_rv6h_bps"].to_numpy(float)
    rho=float(spearmanr(x,y).statistic) if len(df)>=3 else float("nan")
    q20=float(np.quantile(x,0.20))
    q80=float(np.quantile(x,0.80))
    low=y[x<=q20]; high=y[x>=q80]
    low_med=float(np.median(low)) if len(low) else float("nan")
    high_med=float(np.median(high)) if len(high) else float("nan")
    ratio=float(high_med/low_med) if low_med>0 and math.isfinite(low_med) else float("nan")
    return {
        "n":int(len(df)),"spearman_rho":rho,
        "q20_withdrawal_score":q20,"q80_withdrawal_score":q80,
        "q1_n":int(len(low)),"q5_n":int(len(high)),
        "q1_median_rv6h_bps":low_med,"q5_median_rv6h_bps":high_med,
        "q5_q1_median_rv_ratio":ratio,
        "median_future_rv6h_bps":float(np.median(y)) if len(y) else float("nan")
    }

def bootstrap(df:pd.DataFrame,resamples:int,seed:int)->dict[str,Any]:
    day=(df["observation_ts"].to_numpy(np.int64)//86400).astype(np.int64)
    unique=np.unique(day)
    groups={int(d):np.flatnonzero(day==d) for d in unique}
    rng=np.random.default_rng(seed)
    rhos=np.empty(resamples,float); ratios=np.empty(resamples,float)
    xall=df["withdrawal_score"].to_numpy(float); yall=df["future_rv6h_bps"].to_numpy(float)
    for i in range(resamples):
        sampled=rng.choice(unique,size=len(unique),replace=True)
        idx=np.concatenate([groups[int(d)] for d in sampled])
        x=xall[idx]; y=yall[idx]
        rhos[i]=float(spearmanr(x,y).statistic)
        q20=float(np.quantile(x,0.20)); q80=float(np.quantile(x,0.80))
        low=y[x<=q20]; high=y[x>=q80]
        lm=float(np.median(low)); hm=float(np.median(high))
        ratios[i]=hm/lm if lm>0 else np.nan
    goodr=rhos[np.isfinite(rhos)]; goodq=ratios[np.isfinite(ratios)]
    if len(goodr)<resamples*0.99 or len(goodq)<resamples*0.99:
        raise RuntimeError("bootstrap nonfinite rate too high")
    return {
        "unit":"UTC_CALENDAR_DAY_BLOCK","resamples":resamples,"seed":seed,
        "spearman_rho_ci95":[float(np.quantile(goodr,0.025)),float(np.quantile(goodr,0.975))],
        "q5_q1_median_rv_ratio_ci95":[float(np.quantile(goodq,0.025)),float(np.quantile(goodq,0.975))]
    }

def quarter_stats(df:pd.DataFrame)->list[dict[str,Any]]:
    out=[]
    tmp=df.copy()
    dt=pd.to_datetime(tmp["observation_ts"],unit="s",utc=True)
    tmp["quarter"]=dt.dt.to_period("Q").astype(str)
    for q,g in tmp.groupby("quarter",sort=True):
        rho=float(spearmanr(g["withdrawal_score"],g["future_rv6h_bps"]).statistic) if len(g)>=3 else float("nan")
        out.append({"quarter":q,"n":int(len(g)),"spearman_rho":rho})
    return out

def adjudicate(phase:str,df:pd.DataFrame,integrity:int,freeze:dict,stats:dict,boot:dict,quarters:list[dict])->tuple[str,dict]:
    gate=freeze["gates"]["discovery_all_required" if phase=="discovery" else "replication_all_required"]
    floor=int(gate["eligible_observations_gte"])
    if integrity!=0:
        return ("DISCOVERY_DATA_FAILURE" if phase=="discovery" else "REPLICATION_DATA_FAILURE"),{}
    if len(df)<floor:
        return ("DISCOVERY_INSUFFICIENT_SAMPLE" if phase=="discovery" else "REPLICATION_INSUFFICIENT_SAMPLE"),{
            "eligible_observations_gte":False
        }
    qrhos=[float(q["spearman_rho"]) for q in quarters if math.isfinite(float(q["spearman_rho"]))]
    checks={
        "eligible_observations_gte":len(df)>=floor,
        "spearman_rho_gte":stats["spearman_rho"]>=float(gate["spearman_rho_gte"]),
        "bootstrap_95_lower_spearman_rho_gt":boot["spearman_rho_ci95"][0]>float(gate["bootstrap_95_lower_spearman_rho_gt"]),
        "q5_q1_median_rv_ratio_gte":stats["q5_q1_median_rv_ratio"]>=float(gate["q5_q1_median_rv_ratio_gte"]),
        "bootstrap_95_lower_q5_q1_ratio_gt":boot["q5_q1_median_rv_ratio_ci95"][0]>float(gate["bootstrap_95_lower_q5_q1_ratio_gt"]),
        "positive_quarter_rho_count_gte":sum(r>0 for r in qrhos)>=int(gate["positive_quarter_rho_count_gte"]),
        "total_quarters_eq":len(quarters)==int(gate["total_quarters_eq"]),
        "minimum_quarter_rho_gt":len(qrhos)==len(quarters) and min(qrhos)>float(gate["minimum_quarter_rho_gt"]),
        "source_integrity_failures_eq":integrity==int(gate["source_integrity_failures_eq"])
    }
    if all(checks.values()):
        return ("DISCOVERY_SURVIVES" if phase=="discovery" else "REPLICATION_SURVIVES"),checks
    return ("DISCOVERY_NO_EDGE" if phase=="discovery" else "REPLICATION_FAIL"),checks

def safe(v):
    if isinstance(v,float) and (math.isnan(v) or math.isinf(v)): return None
    if isinstance(v,dict): return {k:safe(x) for k,x in v.items()}
    if isinstance(v,list): return [safe(x) for x in v]
    return v

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--phase",choices=sorted(PHASES),required=True)
    ap.add_argument("--root",type=Path,required=True)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    freeze=load_freeze(args.freeze)
    args.out.mkdir(parents=True,exist_ok=True)
    result_path=args.out/f"DEX_LIQUIDITY_PROVISION_001_{args.phase.upper()}_RESULT_V0_1.json"
    obs_path=args.out/f"DEX_LIQUIDITY_PROVISION_001_{args.phase.upper()}_OBSERVATIONS_V0_1.csv.gz"

    try:
        receipts,lp,minutes,integrity,event_counts=combine_source(args.root,args.phase,8)
        df=build_observations(lp,minutes,args.phase,
            int(freeze["observation"]["future_volatility"]["minimum_adjacent_minute_returns"]))
        if len(df):
            df.to_csv(obs_path,index=False,compression="gzip")
        stats=point_stats(df) if len(df) else {"n":0}
        if len(df):
            boot=bootstrap(df,int(freeze["inference"]["bootstrap"]["resamples"]),
                           int(freeze["inference"]["bootstrap"]["seed"]))
            quarters=quarter_stats(df)
        else:
            boot={"unit":"UTC_CALENDAR_DAY_BLOCK","resamples":0,"seed":int(freeze["inference"]["bootstrap"]["seed"]),
                  "spearman_rho_ci95":[None,None],"q5_q1_median_rv_ratio_ci95":[None,None]}
            quarters=[]
        classification,checks=adjudicate(args.phase,df,integrity,freeze,stats,boot,quarters)
        result=safe({
            "lab_id":"DEX-LIQUIDITY-PROVISION-001","phase":args.phase,
            "classification":classification,
            "source_gate_binding":{"run_id":35530732777,"artifact_id":10612116802,
              "artifact_digest":"sha256:918112067a536cee820e62fec1f91dba89b65861b3bb119688aae544ce3d2021"},
            "economic_source":{"event_counts":event_counts,"lp_bucket_count":len(lp),"minute_price_count":len(minutes),
                               "source_integrity_failures":integrity},
            "statistics":stats,"bootstrap":boot,"quarters":quarters,"gate_checks":checks,
            "safety":{"opened_2025":False,"opened_2026":False,"pnl_opened":False,"strategy_claim":False,
                      "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
                      "post_outcome_tuning":False},
            "next_action":(
                "Open frozen 2024 replication exactly once." if classification=="DISCOVERY_SURVIVES" else
                "Close exact frozen mechanism; no rescue." if classification in ("DISCOVERY_NO_EDGE","DISCOVERY_INSUFFICIENT_SAMPLE") else
                "If replication survives, only a separately frozen execution/shadow protocol is authorized." if classification=="REPLICATION_SURVIVES" else
                "Close exact frozen mechanism at replication; no rescue." if classification=="REPLICATION_FAIL" else
                "Resolve data/integrity blocker without changing scientific rules."
            )
        })
        result_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"classification":classification,"n":stats.get("n"),"spearman_rho":stats.get("spearman_rho"),
                          "q5_q1_ratio":stats.get("q5_q1_median_rv_ratio"),"gate_checks":checks},sort_keys=True))
        return 0
    except Exception as exc:
        classification="DISCOVERY_DATA_FAILURE" if args.phase=="discovery" else "REPLICATION_DATA_FAILURE"
        result={
            "lab_id":"DEX-LIQUIDITY-PROVISION-001","phase":args.phase,"classification":classification,
            "failure":f"{type(exc).__name__}: {str(exc)[:2000]}",
            "safety":{"opened_2025":False,"opened_2026":False,"pnl_opened":False,"live_trading":False,
                      "orders":False,"wallets":False,"exchange_mutation":False}
        }
        result_path.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(result,sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""PMD-001 V0.12 exploratory chain-exact feature adjudication.

Joins source-only V0.12 features to the already-opened frozen V0.8 5-minute
outcomes. This stage is explicitly exploratory and has no promotion authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

BASES = [
    "decoded_trade_events","buy_count","sell_count","unique_buyers","unique_sellers","unique_participants",
    "buy_volume_sol","sell_volume_sol","net_flow_sol","volume_balance","count_balance","buy_fraction",
    "wallet_breadth","avg_trade_sol","median_trade_sol","largest_buy_sol","largest_sell_sol",
]
FEATURES = [f"{b}_w{w}" for w in (30,60,300) for b in BASES]
for b in ["net_flow_sol","buy_volume_sol","sell_volume_sol","decoded_trade_events","unique_participants"]:
    FEATURES.append(f"{b}_accel_per_min_w60_vs_w300")
    FEATURES.append(f"{b}_accel_per_sec_w30_vs_w60")


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def trimmed_mean(v: np.ndarray) -> float:
    s=np.sort(np.asarray(v,dtype=float))
    if len(s)>=5:
        s=s[1:-1]
    return float(np.mean(s)) if len(s) else float("nan")


def group_stats(v: np.ndarray) -> dict[str,Any]:
    a=np.asarray(v,dtype=float)
    if len(a)==0:
        return {"n":0}
    j=int(np.argmax(a))
    loo=np.delete(a,j) if len(a)>1 else np.asarray([],dtype=float)
    return {
        "n":int(len(a)),
        "positive_rate":float(np.mean(a>0)),
        "mean_net":float(np.mean(a)),
        "median_net":float(np.median(a)),
        "trimmed_mean_net":trimmed_mean(a),
        "pnl_1sol_each":float(np.sum(a)),
        "max_net":float(np.max(a)),
        "min_net":float(np.min(a)),
        "leave_largest_winner_out_n":int(len(loo)),
        "leave_largest_winner_out_mean_net":float(np.mean(loo)) if len(loo) else None,
        "leave_largest_winner_out_pnl_1sol_each":float(np.sum(loo)) if len(loo) else None,
    }


def eligibility_mask(df:pd.DataFrame, feature:str)->pd.Series:
    if "accel_per_min_w60_vs_w300" in feature:
        return df["decoder_complete_w60"].fillna(False).astype(bool) & df["decoder_complete_w300"].fillna(False).astype(bool)
    if "accel_per_sec_w30_vs_w60" in feature:
        return df["decoder_complete_w30"].fillna(False).astype(bool) & df["decoder_complete_w60"].fillna(False).astype(bool)
    for w in (30,60,300):
        if feature.endswith(f"_w{w}"):
            return df[f"decoder_complete_w{w}"].fillna(False).astype(bool)
    return pd.Series(False,index=df.index)


def quintile_stats(z:pd.DataFrame)->dict[str,Any] | None:
    if len(z)<20 or z.x.nunique()<5:
        return None
    try:
        q=pd.qcut(z.x,5,labels=False,duplicates="drop")
    except Exception:
        return None
    if q.nunique()<5:
        return None
    z=z.copy();z["q"]=q.astype(int)
    qs=[]
    for qi,g in z.groupby("q"):
        rec={"q":int(qi),**group_stats(g.y.to_numpy(float))}
        qs.append(rec)
    qs=sorted(qs,key=lambda r:r["q"])
    return {
        "quintiles":qs,
        "low":qs[0],
        "high":qs[-1],
        "high_minus_low_median_net":float(qs[-1]["median_net"]-qs[0]["median_net"]),
        "high_minus_low_positive_rate":float(qs[-1]["positive_rate"]-qs[0]["positive_rate"]),
        "high_minus_low_trimmed_mean_net":float(qs[-1]["trimmed_mean_net"]-qs[0]["trimmed_mean_net"]),
    }


def eval_feature(df:pd.DataFrame,feature:str)->dict[str,Any] | None:
    if feature not in df.columns:
        return None
    mask=eligibility_mask(df,feature)
    z=pd.DataFrame({
        "x":pd.to_numeric(df.loc[mask,feature],errors="coerce"),
        "y":pd.to_numeric(df.loc[mask,"net_return_5m"],errors="coerce"),
        "t":pd.to_datetime(df.loc[mask,"t0"],utc=True,errors="coerce"),
    }).replace([np.inf,-np.inf],np.nan).dropna()
    z=z.sort_values("t").reset_index(drop=True)
    if len(z)<20 or z.x.nunique()<5:
        return {"feature":feature,"n":int(len(z)),"testable":False}
    rho,p=spearmanr(z.x.to_numpy(float),z.y.to_numpy(float))
    if not np.isfinite(rho) or not np.isfinite(p):
        return {"feature":feature,"n":int(len(z)),"testable":False}
    qstats=quintile_stats(z)
    thirds={}
    splits=np.array_split(np.arange(len(z)),3)
    third_rhos=[];third_deltas=[]
    for name,idx in zip(("early","middle","late"),splits):
        g=z.iloc[idx]
        rr,pp=spearmanr(g.x.to_numpy(float),g.y.to_numpy(float)) if len(g)>=20 and g.x.nunique()>=5 else (np.nan,np.nan)
        qq=quintile_stats(g)
        delta=qq["high_minus_low_median_net"] if qq else None
        thirds[name]={
            "n":int(len(g)),
            "spearman_rho":float(rr) if np.isfinite(rr) else None,
            "spearman_p":float(pp) if np.isfinite(pp) else None,
            "high_minus_low_median_net":delta,
        }
        third_rhos.append(float(rr) if np.isfinite(rr) else None)
        third_deltas.append(delta)
    baseline=float(np.mean(z.y.to_numpy(float)>0))
    return {
        "feature":feature,"n":int(len(z)),"testable":True,
        "spearman_rho":float(rho),"spearman_p":float(p),
        "baseline_positive_rate":baseline,"quintiles":qstats,"thirds":thirds,
        "third_rhos":third_rhos,"third_median_deltas":third_deltas,
    }


def bh_adjust(records:list[dict[str,Any]])->None:
    valid=[r for r in records if r.get("testable") and isinstance(r.get("spearman_p"),(int,float)) and math.isfinite(float(r["spearman_p"]))]
    ordered=sorted(enumerate(valid),key=lambda t:float(t[1]["spearman_p"]))
    m=len(ordered); running=1.0
    for rank in range(m,0,-1):
        _idx,r=ordered[rank-1]
        q=min(running,float(r["spearman_p"])*m/rank,1.0)
        running=q;r["bh_q"]=float(q)


def apply_gate(r:dict[str,Any])->None:
    r["replication_candidate"]=False
    if not r.get("testable") or r.get("n",0)<500 or r.get("bh_q",1)>0.05:
        return
    rho=float(r["spearman_rho"])
    if rho==0:
        return
    sign=1 if rho>0 else -1
    third_rhos=r.get("third_rhos") or []
    deltas=r.get("third_median_deltas") or []
    if len(third_rhos)!=3 or any(x is None or x*sign<=0 for x in third_rhos):
        return
    if len(deltas)!=3 or any(x is None or x*sign<=0 for x in deltas):
        return
    qstats=r.get("quintiles")
    if not qstats:
        return
    fav=qstats["high"] if sign>0 else qstats["low"]
    baseline=float(r["baseline_positive_rate"])
    checks=[
        fav.get("n",0)>=100,
        fav.get("median_net") is not None and fav["median_net"]>0,
        fav.get("trimmed_mean_net") is not None and fav["trimmed_mean_net"]>0,
        fav.get("positive_rate") is not None and fav["positive_rate"]>baseline,
        fav.get("leave_largest_winner_out_mean_net") is not None and fav["leave_largest_winner_out_mean_net"]>0,
    ]
    if all(checks):
        r["replication_candidate"]=True
        r["favorable_extreme"]="high" if sign>0 else "low"
        r["favorable_extreme_stats"]=fav


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--features",required=True)
    ap.add_argument("--outcomes",required=True)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    fp=Path(args.features);op=Path(args.outcomes)
    feats=pd.DataFrame([json.loads(x) for x in fp.read_text(encoding="utf-8").splitlines() if x.strip()])
    if not len(feats):raise RuntimeError("empty V0.12 feature table")
    if not (feats["economic_outcomes_opened"]==False).all():raise RuntimeError("feature provenance outcome-wall violation")
    outs=pd.read_csv(op)
    if len(outs)!=1012 or outs.mint.nunique()!=1012:raise RuntimeError("frozen V0.8 baseline must contain 1,012 unique mints")
    d=feats.merge(outs[["mint","net_return_5m","execution_available","corpus_t0"]],on="mint",how="inner",validate="one_to_one")
    if len(d)!=len(feats):raise RuntimeError("feature/outcome mint reconciliation failure")
    d["t0"]=d["t0"].fillna(d["corpus_t0"])
    records=[]
    for f in FEATURES:
        rec=eval_feature(d,f)
        if rec is not None:records.append(rec)
    bh_adjust(records)
    for r in records:apply_gate(r)
    candidates=[r["feature"] for r in records if r.get("replication_candidate")]
    max_n=max((int(r.get("n",0)) for r in records),default=0)
    if candidates:
        verdict="V012_REPLICATION_CANDIDATE"
    elif max_n<500:
        verdict="V012_DECODER_OR_SAMPLE_INSUFFICIENT"
    else:
        verdict="V012_NO_ROBUST_FEATURE_SIGNAL"
    ranking=sorted(records,key=lambda r:(not bool(r.get("replication_candidate")),float(r.get("bh_q",1.0)), -abs(float(r.get("spearman_rho",0.0) or 0.0))))
    out={
        "lab":"PMD-001","stage":"CHAIN_EXACT_FEATURE_EVALUATION_V012",
        "exploratory_only":True,"promotion_authority":False,
        "features_sha256":sha256_file(fp),"outcomes_sha256":sha256_file(op),
        "feature_rows":int(len(feats)),"joined_rows":int(len(d)),
        "fixed_features_expected":len(FEATURES),"features_evaluated":len(records),
        "multiple_testing":"Benjamini-Hochberg FDR across fixed testable V0.12 family",
        "replication_candidates":candidates,"verdict":verdict,
        "ranking":ranking,
    }
    Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True,default=str)+"\n",encoding="utf-8")
    print(json.dumps({
        "verdict":verdict,"replication_candidates":candidates,"max_feature_n":max_n,
        "top_diagnostics":[{k:r.get(k) for k in ("feature","n","spearman_rho","spearman_p","bh_q","replication_candidate")} for r in ranking[:15]],
    },indent=2,sort_keys=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())

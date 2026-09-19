#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
import pandas as pd

REPS=10000
BLOCK=45
SEED=230923

def slope(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float)
    vx=np.var(x)
    if not np.isfinite(vx) or vx<=0: return np.nan
    return float(np.cov(x,y,bias=True)[0,1]/vx)

def main():
    p=Path("edff_primary_2024_observations_v01.csv")
    d=pd.read_csv(p)
    d["date"]=pd.to_datetime(d["date"],utc=True,errors="coerce")
    d=d.dropna(subset=["date","FD","future_log_return"]).sort_values("date").reset_index(drop=True)
    n=len(d)
    if n!=248:
        raise SystemExit(f"frozen parent sample mismatch: expected 248 got {n}")
    x=d["FD"].to_numpy(float); y=d["future_log_return"].to_numpy(float)
    obs=slope(x,y)

    rng=np.random.default_rng(SEED)
    nb=math.ceil(n/BLOCK)
    bs=np.empty(REPS)
    for i in range(REPS):
        idx=[]
        for s in rng.integers(0,n,size=nb):
            idx.extend(((s+np.arange(BLOCK))%n).tolist())
        idx=np.asarray(idx[:n],int)
        bs[i]=slope(x[idx],y[idx])
    ci=[float(np.nanquantile(bs,.025)),float(np.nanquantile(bs,.975))]
    boot_pos=float(np.nanmean(bs>0))

    shifts=list(range(BLOCK,n-BLOCK+1))
    null=np.asarray([slope(np.roll(x,k),y) for k in shifts],float)
    null=null[np.isfinite(null)]
    pshift=float((1+np.sum(np.abs(null)>=abs(obs)))/(1+len(null))) if len(null) else None

    q=d.copy()
    q["quarter"]=q["date"].dt.to_period("Q").astype(str)
    qs={}
    for name,g in q.groupby("quarter"):
        qs[name]={"N":int(len(g)),"beta":slope(g["FD"],g["future_log_return"])}

    cond_boot=ci[0]>0
    cond_shift=pshift is not None and pshift<.05
    if obs<=0:
        cls="ROBUSTNESS_CONTRADICTS_PARENT"
    elif cond_boot and cond_shift:
        cls="ROBUSTNESS_SUPPORTIVE_NOT_PROMOTIONAL"
    elif cond_boot ^ cond_shift:
        cls="ROBUSTNESS_PARTIAL_NOT_PROMOTIONAL"
    else:
        cls="ROBUSTNESS_WEAK_NOT_PROMOTIONAL"

    out={
      "lab_id":"ETH-DEMAND-FEE-FLOW-001",
      "audit_id":"EDFF-FD45-INFERENCE-ROBUSTNESS-001",
      "classification":cls,
      "N":n,
      "observed_beta":obs,
      "moving_block_bootstrap":{"reps":REPS,"block_length":BLOCK,"seed":SEED,
                                "beta_ci95":ci,"fraction_beta_positive":boot_pos},
      "circular_shift_null":{"min_shift":BLOCK,"shift_count":int(len(null)),
                             "two_sided_p":pshift,
                             "null_beta_q025":float(np.quantile(null,.025)) if len(null) else None,
                             "null_beta_q975":float(np.quantile(null,.975)) if len(null) else None},
      "quarterly_descriptive":qs,
      "parent_verdict_rewritten":False,
      "promotion_authorized":False,
      "protected_2025_2026_opened":False,
      "pnl_computed":False
    }
    Path("edff_robustness_receipt_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))

if __name__=="__main__": main()

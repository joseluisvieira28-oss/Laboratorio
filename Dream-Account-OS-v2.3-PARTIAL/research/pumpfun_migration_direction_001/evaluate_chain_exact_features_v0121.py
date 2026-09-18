#!/usr/bin/env python3
"""PMD-001 V0.12.1 evaluator plumbing for quote-aware decoder completeness.

Feature family, BH-FDR, quintiles, thirds and replication gate are unchanged.
Only per-feature eligibility distinguishes structural decode completeness from
SOL-volume completeness.
"""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd
import evaluate_chain_exact_features_v012 as base

SOL_BASES={
 "buy_volume_sol","sell_volume_sol","net_flow_sol","volume_balance",
 "avg_trade_sol","median_trade_sol","largest_buy_sol","largest_sell_sol"
}

def eligibility_mask_v0121(df:pd.DataFrame,feature:str)->pd.Series:
    if "accel_per_min_w60_vs_w300" in feature:
        sol=feature.startswith(("net_flow_sol_","buy_volume_sol_","sell_volume_sol_"))
        prefix="sol_volume_complete" if sol else "decoder_complete"
        return df[f"{prefix}_w60"].fillna(False).astype(bool) & df[f"{prefix}_w300"].fillna(False).astype(bool)
    if "accel_per_sec_w30_vs_w60" in feature:
        sol=feature.startswith(("net_flow_sol_","buy_volume_sol_","sell_volume_sol_"))
        prefix="sol_volume_complete" if sol else "decoder_complete"
        return df[f"{prefix}_w30"].fillna(False).astype(bool) & df[f"{prefix}_w60"].fillna(False).astype(bool)
    for w in (30,60,300):
        suffix=f"_w{w}"
        if feature.endswith(suffix):
            b=feature[:-len(suffix)]
            prefix="sol_volume_complete" if b in SOL_BASES else "decoder_complete"
            return df[f"{prefix}_w{w}"].fillna(False).astype(bool)
    return pd.Series(False,index=df.index)

base.eligibility_mask=eligibility_mask_v0121

def cli_value(flag:str):
    try:
        i=sys.argv.index(flag);return sys.argv[i+1]
    except Exception:return None

if __name__=="__main__":
    rc=base.main()
    outp=cli_value("--out")
    if outp and Path(outp).exists():
        p=Path(outp);r=json.loads(p.read_text(encoding="utf-8"))
        r["stage"]="CHAIN_EXACT_FEATURE_EVALUATION_V0121_DECODER_REMEDIATION"
        r["decoder_remediation_only"]=True
        r["feature_family_changed"]=False
        r["promotion_authority"]=False
        p.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    raise SystemExit(rc)

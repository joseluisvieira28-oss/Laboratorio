#!/usr/bin/env python3
from __future__ import annotations
import json,sys
from pathlib import Path

ALLOWED_REASON="collateral_flag_true_with_zero_scaled_atoken_at_tx_end"
AUTHORITY="AAVE_LIQUIDATION_OVERHANG_001_R1_COLLATERAL_FLAG_SEMANTICS_AMENDMENT_V0_1"
PROBE_RUN_ID=35384176433
PROBE_ARTIFACT_ID=10563825131
PROBE_DIGEST="sha256:14714b00d328f7f9b946b564b5836a2b2c31b9de7a054aed9ce34393bc0b3429"

def main()->int:
    src=Path("downloaded_r1_shards")
    out=Path("reconciled_r1_shards"); out.mkdir(parents=True,exist_ok=True)
    files=sorted(src.rglob("*.json"))
    if len(files)!=8:
        raise RuntimeError(f"expected exactly 8 shard receipts, got {len(files)}")
    seen=set(); terminal=[]
    for p in files:
        x=json.loads(p.read_text())
        sid=int(x["shard_id"])
        if sid in seen: raise RuntimeError(f"duplicate shard {sid}")
        seen.add(sid)
        original=x.get("classification")
        flags=x.get("collateral_flag_violations") or []
        negatives=x.get("negative_states") or []
        decreases=x.get("index_decreases") or []
        debt_transfers=int((x.get("event_counts") or {}).get("VARIABLE_DEBT_BALANCE_TRANSFER",0))
        eligible=(
          original=="RECONSTRUCTION_RECONCILIATION_FAILURE"
          and len(flags)>0
          and all(r.get("reason")==ALLOWED_REASON for r in flags)
          and len(negatives)==0
          and len(decreases)==0
          and debt_transfers==0
        )
        if eligible:
            x["semantic_reconciliation"]={
              "authority":AUTHORITY,
              "probe_run_id":PROBE_RUN_ID,
              "probe_artifact_id":PROBE_ARTIFACT_ID,
              "probe_artifact_digest":PROBE_DIGEST,
              "original_classification":original,
              "original_failure":x.get("failure"),
              "diagnostic_count_preserved":len(flags),
              "scientific_rule_changed":False,
            }
            x["classification"]="R1_RESERVE_SHARD_PASS"
            x["failure"]=None
        elif original!="R1_RESERVE_SHARD_PASS":
            terminal.append({"shard_id":sid,"classification":original,"failure":x.get("failure")})
        x["phase"]="R1_FULL_RESERVE_SHARD_V0_3_RECONCILED_OUTCOME_BLIND"
        (out/f"r1_reserve_shard_reconciled_{sid:02d}.json").write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    if seen!=set(range(8)): raise RuntimeError(f"shard ids mismatch {sorted(seen)}")
    summary={
      "classification":"R1_RESERVE_SHARDS_RECONCILED_PASS" if not terminal else "R1_RESERVE_SHARDS_RECONCILED_FAIL",
      "terminal_components":terminal,
      "shard_count":8,
      "probe_run_id":PROBE_RUN_ID,
      "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcomes_opened":False,"market_returns_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    }
    Path("reconciled_r1_shards/RECONCILIATION_SUMMARY.json").write_text(json.dumps(summary,indent=2,sort_keys=True)+"\n")
    print(json.dumps(summary,sort_keys=True))
    return 0 if not terminal else 2

if __name__=="__main__":
    try: sys.exit(main())
    except Exception as e:
        print(json.dumps({"classification":"R1_RESERVE_SHARDS_RECONCILIATION_TECHNICAL_FAILURE","failure":f"{type(e).__name__}: {str(e)[:1200]}"}))
        sys.exit(2)

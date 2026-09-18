#!/usr/bin/env python3
from __future__ import annotations
import json,os,sys
from pathlib import Path
import r1_reserve_shard_v02 as v2

ALLOWED_REASON="collateral_flag_true_with_zero_scaled_atoken_at_tx_end"
AUTHORITY="AAVE_LIQUIDATION_OVERHANG_001_R1_COLLATERAL_FLAG_SEMANTICS_AMENDMENT_V0_1"
PROBE_RUN_ID=35384176433
PROBE_ARTIFACT_ID=10563825131
PROBE_DIGEST="sha256:14714b00d328f7f9b946b564b5836a2b2c31b9de7a054aed9ce34393bc0b3429"

def main()->int:
    shard_id=int(os.environ.get("R1_SHARD_ID","0"))
    v2.main()
    p=Path("r1_reserve_shards")/f"r1_reserve_shard_v02_{shard_id:02d}.json"
    if not p.exists():
        raise SystemExit("V0.2 shard receipt missing")
    x=json.loads(p.read_text())
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
        x["v02_original_classification"]=original
        x["v02_original_failure"]=x.get("failure")
        x["classification"]="R1_RESERVE_SHARD_PASS"
        x["failure"]=None
        x["collateral_flag_semantics_amendment"]={
          "authority":AUTHORITY,
          "probe_run_id":PROBE_RUN_ID,
          "probe_artifact_id":PROBE_ARTIFACT_ID,
          "probe_artifact_digest":PROBE_DIGEST,
          "semantic_rule":"stale collateral bit with zero scaled aToken is canonical-possible and diagnostic-only",
          "diagnostic_count_preserved":len(flags),
        }
    x["phase"]="R1_FULL_RESERVE_SHARD_V0_3_OUTCOME_BLIND"
    out=Path("r1_reserve_shards")/f"r1_reserve_shard_v03_{shard_id:02d}.json"
    out.write_text(json.dumps(x,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "shard":shard_id,
      "classification":x.get("classification"),
      "v02_original_classification":original,
      "collateral_flag_diagnostic_count":len(flags),
      "negative_count":len(negatives),
      "index_decrease_count":len(decreases),
      "returns_opened":False,
      "pnl_opened":False
    },sort_keys=True))
    return 0 if x.get("classification")=="R1_RESERVE_SHARD_PASS" else 2

if __name__=="__main__": sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from collections import Counter, defaultdict
from pathlib import Path
import r1_scaled_ledger_audit_v01 as v

LAB_ID=v.LAB_ID
GLOBAL_FROM=16_490_000
GLOBAL_TO=21_525_890
EXPECTED_RANGES=[
 (16490000,17119486),(17119487,17748973),(17748974,18378460),(18378461,19007946),
 (19007947,19637432),(19637433,20266918),(20266919,20896404),(20896405,21525890),
]

def exactly_one(root:str,classification:str|None=None):
    xs=[]
    for p in Path(root).rglob("*.json"):
        o=json.loads(p.read_text(encoding="utf-8"))
        if classification is None or o.get("classification")==classification: xs.append(o)
    if len(xs)!=1: raise RuntimeError(f"expected exactly one receipt under {root}, got {len(xs)}")
    return xs[0]

def main()->int:
    out=Path("r1_scaled_ledger_audit_v02_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2.json"
    transport=Counter()
    receipt={
      "lab_id":LAB_ID,
      "phase":"R1_SCALED_LEDGER_AUDIT_V0_2_SHARDED_OUTCOME_BLIND",
      "protocol":"AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2",
      "remediation":"AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_SHARDING_REMEDIATION_V0_2",
      "frozen_from_block":GLOBAL_FROM,
      "frozen_to_block":GLOBAL_TO,
      "audit_blocks":v.AUDIT_BLOCKS,
      "classification":None,
      "failure":None,
      "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False},
    }
    try:
        sample=exactly_one("downloaded_r1_sample","R1_AUDIT_SAMPLE_PASS")
        sample_users=[str(x).lower() for x in sample["sample_borrowers"]]
        sample_sha=str(sample["sample_sha256"])
        if len(sample_users)!=16: raise RuntimeError("sample size mismatch")
        bootstrap=v.load_bootstrap()
        if int(bootstrap.get("frozen_from_block"))!=GLOBAL_FROM or int(bootstrap.get("frozen_to_block"))!=GLOBAL_TO:
            raise RuntimeError("canonical R0 bootstrap envelope mismatch")
        token_meta,_,_=v.build_token_maps(bootstrap)

        shards=[]
        for p in Path("downloaded_r1_shards").rglob("*.json"):
            shards.append(json.loads(p.read_text(encoding="utf-8")))
        if len(shards)!=8: raise RuntimeError(f"expected 8 audit shards, got {len(shards)}")
        shards.sort(key=lambda x:int(x["from_block"]))
        got=[(int(x["from_block"]),int(x["to_block"])) for x in shards]
        if got!=EXPECTED_RANGES: raise RuntimeError(f"audit shard ranges mismatch {got}")
        ids=[int(x["shard_id"]) for x in shards]
        if ids!=list(range(8)): raise RuntimeError(f"audit shard ids mismatch {ids}")

        block_deltas=defaultdict(lambda:defaultdict(int))
        event_counts=Counter()
        debt_transfer_count=0
        total_serial_rows=0
        for s in shards:
            if s.get("classification")!="R1_AUDIT_SHARD_PASS":
                raise RuntimeError(f"non-pass audit shard {s.get('shard_id')}: {s.get('classification')}")
            if s.get("sample_sha256")!=sample_sha: raise RuntimeError("sample SHA mismatch across audit shards")
            safety=s.get("safety") or {}
            forbidden=["health_factor_computed","overhang_computed","future_liquidation_outcome_computed","market_prices_opened","returns_opened","pnl_opened","accessed_2025_or_2026","live_trading","exchange_mutation"]
            if any(bool(safety.get(k)) for k in forbidden): raise RuntimeError("audit shard safety violation")
            event_counts.update({k:int(val) for k,val in (s.get("scaled_event_counts") or {}).items()})
            debt_transfer_count+=int(s.get("variable_debt_balance_transfer_count",0))
            for k,val in (s.get("transport_stats") or {}).items(): transport[k]+=int(val)
            for row in s.get("block_deltas") or []:
                user=str(row["user"]).lower(); token=str(row["token"]).lower()
                if user not in sample_users: raise RuntimeError("shard delta user escaped frozen sample")
                if token not in token_meta: raise RuntimeError("shard delta token outside canonical reserve map")
                total_serial_rows+=1
                for b,d in row.get("blocks") or []:
                    bn=int(b); delta=int(d)
                    if not (int(s["from_block"])<=bn<=int(s["to_block"])): raise RuntimeError("delta block escaped shard range")
                    block_deltas[(user,token)][bn]+=delta

        targets,negatives=v.replay_targets(block_deltas,token_meta)
        receipt.update({
          "unique_borrower_count":int(sample["unique_borrower_count"]),
          "sample_borrowers":sample_users,
          "sample_sha256":sample_sha,
          "scaled_event_counts":dict(sorted(event_counts.items())),
          "audit_shard_ranges":EXPECTED_RANGES,
          "audit_shard_count":len(shards),
          "serialized_pair_rows":total_serial_rows,
          "touched_user_token_pairs":len(block_deltas),
          "validation_target_count":len(targets),
          "negative_replay_states":negatives[:100],
          "variable_debt_balance_transfer_count":debt_transfer_count,
        })
        if debt_transfer_count!=0:
            receipt["classification"]="RECONSTRUCTION_PROVENANCE_FAILURE"
            receipt["failure"]="variable-debt BalanceTransfer observed despite non-transferability"
        elif negatives:
            receipt["classification"]="RECONSTRUCTION_RECONCILIATION_FAILURE"
            receipt["failure"]=f"negative scaled replay state(s): {len(negatives)}"
        elif not targets:
            receipt["classification"]="RECONSTRUCTION_INSUFFICIENT_COVERAGE"
            receipt["failure"]="no deterministic historical validation targets"
        else:
            classification,failures,endpoint_stats=v.validate_targets(targets)
            receipt["classification"]=classification
            receipt["validation_failures"]=failures[:250]
            receipt["validation_failure_count"]=len(failures)
            receipt["archive_rpc_stats"]=endpoint_stats
            receipt["validated_target_count"]=len(targets)-len(failures)
            receipt["target_digest_sha256"]=hashlib.sha256("\n".join(f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}" for t in targets).encode()).hexdigest()
            receipt["validation_targets"]=targets
    except Exception as exc:
        receipt["classification"]="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1500]}"
    receipt["transport_stats"]=dict(transport)
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"sample_size":len(receipt.get("sample_borrowers",[])),"pairs":receipt.get("touched_user_token_pairs"),"targets":receipt.get("validation_target_count"),"failures":receipt.get("validation_failure_count"),"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if receipt["classification"]=="R1_AUDIT_PASS" else 2

if __name__=="__main__": sys.exit(main())

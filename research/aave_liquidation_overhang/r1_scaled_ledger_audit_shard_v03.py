#!/usr/bin/env python3
"""Four-way borrower-sharded R1 scaled-ledger audit wrapper for V0.3."""
from __future__ import annotations
import hashlib, json, os, sys
from collections import Counter
from pathlib import Path

import r1_scaled_ledger_audit_v01 as base

LAB_ID=base.LAB_ID
SHARD_COUNT=4
GROUP_SIZE=4

def load_one(root:str,classification:str):
    files=list(Path(root).rglob("*.json"))
    matches=[]
    for p in files:
        try:
            obj=json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if obj.get("classification")==classification:
            matches.append((p,obj))
    if len(matches)!=1:
        raise RuntimeError(f"expected exactly one {classification} receipt under {root}, got {len(matches)}")
    return matches[0][1]

def main()->int:
    shard_id=int(os.environ["AUDIT_SHARD_ID"])
    if shard_id not in range(SHARD_COUNT):
        raise SystemExit("invalid AUDIT_SHARD_ID")
    out=Path("r1_audit_shards")
    out.mkdir(parents=True,exist_ok=True)
    dst=out/f"AAVE_LIQUIDATION_OVERHANG_001_R1_AUDIT_SHARD_V0_3_{shard_id:02d}.json"
    stats=Counter()
    receipt={
        "lab_id":LAB_ID,
        "phase":"R1_SCALED_LEDGER_AUDIT_SHARD_V0_3_OUTCOME_BLIND",
        "shard_id":shard_id,
        "shard_count":SHARD_COUNT,
        "classification":None,
        "frozen_from_block":base.FROM_BLOCK,
        "frozen_to_block":base.TO_BLOCK,
        "audit_blocks":base.AUDIT_BLOCKS,
        "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    }
    try:
        sample_receipt=load_one("downloaded_r1_sample","R1_AUDIT_SAMPLE_PASS")
        full_sample=[str(x).lower() for x in sample_receipt["sample_borrowers"]]
        if len(full_sample)!=16:
            raise RuntimeError("frozen sample size is not 16")
        if hashlib.sha256("\n".join(full_sample).encode()).hexdigest()!=sample_receipt["sample_sha256"]:
            raise RuntimeError("sample SHA mismatch")
        lo=shard_id*GROUP_SIZE
        hi=lo+GROUP_SIZE
        sample=full_sample[lo:hi]
        if len(sample)!=GROUP_SIZE:
            raise RuntimeError("invalid 4-borrower partition")

        bootstrap=base.load_bootstrap()
        if int(bootstrap.get("frozen_from_block"))!=base.FROM_BLOCK or int(bootstrap.get("frozen_to_block"))!=base.TO_BLOCK:
            raise RuntimeError("canonical R0 bootstrap envelope mismatch")
        token_meta,atokens,debts=base.build_token_maps(bootstrap)
        block_deltas,event_counts,debt_transfer_count=base.acquire_sample_token_deltas(sample,token_meta,atokens,debts,stats)
        targets,negatives=base.replay_targets(block_deltas,token_meta)

        receipt.update({
            "full_sample_sha256":sample_receipt["sample_sha256"],
            "unique_borrower_count":int(sample_receipt["unique_borrower_count"]),
            "sample_positions":[lo,hi-1],
            "sample_borrowers":sample,
            "sample_shard_sha256":hashlib.sha256("\n".join(sample).encode()).hexdigest(),
            "scaled_event_counts":dict(sorted(event_counts.items())),
            "touched_user_token_pairs":len(block_deltas),
            "validation_target_count":len(targets),
            "negative_replay_states":negatives[:100],
            "variable_debt_balance_transfer_count":debt_transfer_count
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
            classification,failures,endpoint_stats=base.validate_targets(targets)
            receipt["classification"]="R1_AUDIT_SHARD_PASS" if classification=="R1_AUDIT_PASS" else classification
            receipt["validation_failures"]=failures[:250]
            receipt["validation_failure_count"]=len(failures)
            receipt["archive_rpc_stats"]=endpoint_stats
            receipt["validated_target_count"]=len(targets)-len(failures)
            ordered=sorted(targets,key=lambda t:(t["user"],t["token"],int(t["block"])))
            receipt["validation_targets"]=ordered
            receipt["target_digest_sha256"]=hashlib.sha256(
                "\n".join(f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}" for t in ordered).encode()
            ).hexdigest()
    except Exception as exc:
        receipt["classification"]="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1200]}"

    receipt["transport_stats"]=dict(stats)
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "shard":shard_id,
        "classification":receipt["classification"],
        "borrowers":len(receipt.get("sample_borrowers",[])),
        "touched_pairs":receipt.get("touched_user_token_pairs"),
        "validation_targets":receipt.get("validation_target_count"),
        "validation_failures":receipt.get("validation_failure_count"),
        "health_factor_computed":False,
        "overhang_computed":False,
        "returns_opened":False,
        "pnl_opened":False
    },sort_keys=True))
    return 0 if receipt["classification"]=="R1_AUDIT_SHARD_PASS" else 2

if __name__=="__main__":
    sys.exit(main())

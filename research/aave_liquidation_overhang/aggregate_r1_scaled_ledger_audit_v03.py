#!/usr/bin/env python3
"""Canonical V0.3 aggregate for four borrower-sharded AAVE R1 audit receipts."""
from __future__ import annotations
import hashlib, json, sys
from collections import Counter
from pathlib import Path

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
EXPECTED_SHARDS=set(range(4))
FAIL_PRECEDENCE=[
    "RECONSTRUCTION_PROVENANCE_FAILURE",
    "RECONSTRUCTION_RECONCILIATION_FAILURE",
    "RECONSTRUCTION_INSUFFICIENT_COVERAGE",
    "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE",
]

def read_jsons(root:str):
    return [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(root).rglob("*.json"))]

def exactly_one(root:str,classification:str):
    xs=[x for x in read_jsons(root) if x.get("classification")==classification]
    if len(xs)!=1:
        raise RuntimeError(f"expected exactly one {classification} under {root}, got {len(xs)}")
    return xs[0]

def terminal_class(classes):
    for c in FAIL_PRECEDENCE:
        if c in classes:
            return c
    return "RECONSTRUCTION_RECONCILIATION_FAILURE"

def merge_nested_counts(dst:dict,src:dict):
    for ep,vals in (src or {}).items():
        d=dst.setdefault(ep,Counter())
        d.update({k:int(v) for k,v in (vals or {}).items()})

def main()->int:
    out=Path("r1_audit_canonical_output")
    out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_3.json"
    receipt={"lab_id":LAB_ID,"phase":"R1_SCALED_LEDGER_AUDIT_V0_3_CANONICAL_OUTCOME_BLIND","classification":None}
    try:
        sample=exactly_one("downloaded_r1_sample","R1_AUDIT_SAMPLE_PASS")
        shards=read_jsons("downloaded_r1_audit_shards")
        if len(shards)!=4:
            raise RuntimeError(f"expected exactly 4 audit shard receipts, got {len(shards)}")
        ids={int(s["shard_id"]) for s in shards}
        if ids!=EXPECTED_SHARDS:
            raise RuntimeError(f"audit shard ids mismatch: {sorted(ids)}")
        shards=sorted(shards,key=lambda s:int(s["shard_id"]))
        full_sample=[str(x).lower() for x in sample["sample_borrowers"]]
        if len(full_sample)!=16:
            raise RuntimeError("sample size is not 16")
        if hashlib.sha256("\n".join(full_sample).encode()).hexdigest()!=sample["sample_sha256"]:
            raise RuntimeError("sample hash mismatch")

        union=[]
        classes=[]
        for i,s in enumerate(shards):
            classes.append(s.get("classification"))
            expected=full_sample[i*4:(i+1)*4]
            got=[str(x).lower() for x in s.get("sample_borrowers") or []]
            if got!=expected:
                raise RuntimeError(f"shard {i} borrower partition mismatch")
            if s.get("full_sample_sha256")!=sample["sample_sha256"]:
                raise RuntimeError(f"shard {i} full sample hash mismatch")
            union.extend(got)
            safety=s.get("safety") or {}
            forbidden=["health_factor_computed","overhang_computed","future_liquidation_outcome_computed","market_prices_opened","returns_opened","pnl_opened","accessed_2025_or_2026","live_trading","exchange_mutation"]
            if any(bool(safety.get(k)) for k in forbidden):
                raise RuntimeError(f"safety violation in shard {i}")
        if union!=full_sample or len(set(union))!=16:
            raise RuntimeError("shard union does not equal exact frozen sample")

        if any(c!="R1_AUDIT_SHARD_PASS" for c in classes):
            receipt.update({
                "classification":terminal_class(classes),
                "failure":"one or more mandatory V0.3 audit shards did not pass",
                "component_status":{str(s["shard_id"]):s.get("classification") for s in shards},
                "sample_borrowers":full_sample,
                "sample_sha256":sample["sample_sha256"],
                "unique_borrower_count":sample["unique_borrower_count"]
            })
        else:
            event_counts=Counter()
            transport=Counter()
            archive_stats={}
            targets=[]
            failures=[]
            negatives=[]
            touched=0
            validated=0
            debt_transfers=0
            for s in shards:
                event_counts.update({k:int(v) for k,v in (s.get("scaled_event_counts") or {}).items()})
                transport.update({k:int(v) for k,v in (s.get("transport_stats") or {}).items()})
                merge_nested_counts(archive_stats,s.get("archive_rpc_stats") or {})
                targets.extend(s.get("validation_targets") or [])
                failures.extend(s.get("validation_failures") or [])
                negatives.extend(s.get("negative_replay_states") or [])
                touched+=int(s.get("touched_user_token_pairs") or 0)
                validated+=int(s.get("validated_target_count") or 0)
                debt_transfers+=int(s.get("variable_debt_balance_transfer_count") or 0)

            ordered=sorted(targets,key=lambda t:(t["user"],t["token"],int(t["block"])))
            if failures or negatives or debt_transfers:
                raise RuntimeError("pass shard aggregate contains forbidden failures/negative states/debt transfers")
            if len(ordered)==0:
                raise RuntimeError("canonical audit has zero validation targets")
            target_digest=hashlib.sha256(
                "\n".join(f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}" for t in ordered).encode()
            ).hexdigest()
            receipt.update({
                "classification":"R1_AUDIT_PASS",
                "protocol":"AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2 + SHARDING_REMEDIATION_V0_3",
                "frozen_from_block":16_490_000,
                "frozen_to_block":21_525_890,
                "audit_blocks":[17_748_972,19_007_945,20_266_917,21_525_890],
                "unique_borrower_count":int(sample["unique_borrower_count"]),
                "sample_borrowers":full_sample,
                "sample_sha256":sample["sample_sha256"],
                "audit_shard_count":4,
                "component_status":{str(s["shard_id"]):s.get("classification") for s in shards},
                "scaled_event_counts":dict(sorted(event_counts.items())),
                "touched_user_token_pairs":touched,
                "validation_target_count":len(ordered),
                "validated_target_count":validated,
                "validation_failure_count":0,
                "validation_failures":[],
                "negative_replay_states":[],
                "variable_debt_balance_transfer_count":0,
                "archive_rpc_stats":{ep:dict(c) for ep,c in archive_stats.items()},
                "transport_stats":dict(transport),
                "target_digest_sha256":target_digest,
                "validation_targets":ordered,
                "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
            })
    except Exception as exc:
        receipt.update({
            "classification":"RECONSTRUCTION_RECONCILIATION_FAILURE",
            "failure":f"{type(exc).__name__}: {str(exc)[:1500]}",
            "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        })

    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({
        "classification":receipt["classification"],
        "sample_size":len(receipt.get("sample_borrowers",[])),
        "validation_targets":receipt.get("validation_target_count"),
        "validated_targets":receipt.get("validated_target_count"),
        "health_factor_computed":False,
        "overhang_computed":False,
        "returns_opened":False,
        "pnl_opened":False
    },sort_keys=True))
    return 0 if receipt["classification"]=="R1_AUDIT_PASS" else 2

if __name__=="__main__":
    sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from collections import Counter, defaultdict
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("base_audit", HERE/"r1_scaled_ledger_audit_v01.py")
base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

RANGES=[
("0",16490000,17119486),("1",17119487,17748973),("2",17748974,18378460),("3",18378461,19007946),
("4",19007947,19637432),("5",19637433,20266918),("6",20266919,20896404),("7",20896405,21525890)
]

def load_one(root,name):
    fs=list(Path(root).rglob(name))
    if len(fs)!=1: raise RuntimeError(f"expected one {name}, found {len(fs)}")
    return json.loads(fs[0].read_text())

def main():
    out=Path("r1_sharded_audit_output"); out.mkdir(parents=True,exist_ok=True)
    receipt_path=out/"AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2A.json"
    receipt={
      "lab_id":base.LAB_ID,
      "phase":"R1_SCALED_LEDGER_AUDIT_SHARDED_V0_2A_OUTCOME_BLIND",
      "protocol":"AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2",
      "remediation_freeze":"AAVE_LIQUIDATION_OVERHANG_001_R1_SHARDED_AUDIT_REMEDIATION_FREEZE_V0_2A",
      "frozen_from_block":16490000,"frozen_to_block":21525890,
      "audit_blocks":base.AUDIT_BLOCKS,
      "classification":None,"failure":None,
      "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    }
    try:
        sample=load_one("downloaded_r1_sample","AAVE_LIQUIDATION_OVERHANG_001_R1_BORROW_SAMPLE_V0_2A.json")
        if sample.get("classification")!="R1_BORROW_SAMPLE_PASS": raise RuntimeError("sample receipt not PASS")
        borrowers=[str(x).lower() for x in sample["sample_borrowers"]]
        sample_sha=hashlib.sha256("\n".join(borrowers).encode()).hexdigest()
        if sample_sha!=sample.get("sample_sha256"): raise RuntimeError("sample SHA mismatch")
        if int(sample.get("borrow_log_count",0))!=204952: raise RuntimeError("Borrow count mismatch")

        bootstrap=base.load_bootstrap()
        if int(bootstrap.get("frozen_from_block"))!=16490000 or int(bootstrap.get("frozen_to_block"))!=21525890:
            raise RuntimeError("R0 bootstrap envelope mismatch")
        token_meta,_,_=base.build_token_maps(bootstrap)

        fs=sorted(Path("downloaded_delta_shards").rglob("delta_shard_*.json"))
        if len(fs)!=8: raise RuntimeError(f"expected 8 delta shard receipts, found {len(fs)}")
        shards=[json.loads(p.read_text()) for p in fs]; shards.sort(key=lambda x:int(x["shard_id"]))
        got=[(str(x["shard_id"]),int(x["block_start"]),int(x["block_end"])) for x in shards]
        if got!=RANGES: raise RuntimeError(f"delta shard range mismatch {got}")

        merged=defaultdict(lambda:defaultdict(int))
        event_counts=Counter(); transport=Counter(); debt_transfer_count=0
        shard_digests={}
        for s in shards:
            if s.get("classification")!="DELTA_SHARD_PASS":
                raise RuntimeError(f"non-pass delta shard {s.get('shard_id')}: {s.get('classification')}")
            if s.get("sample_sha256")!=sample_sha: raise RuntimeError("delta shard sample SHA mismatch")
            sid=str(s["shard_id"]); a=int(s["block_start"]); b=int(s["block_end"])
            shard_digests[sid]=s.get("delta_ledger_digest_sha256")
            for row in s.get("ledger") or []:
                user=str(row["user"]).lower(); token=str(row["token"]).lower()
                if user not in borrowers: raise RuntimeError("delta ledger user escaped frozen sample")
                if token not in token_meta: raise RuntimeError("delta ledger token escaped R0 universe")
                for bn_s,delta_s in row.get("by_block") or []:
                    bn=int(bn_s); delta=int(delta_s)
                    if not a<=bn<=b: raise RuntimeError("delta block outside shard range")
                    merged[(user,token)][bn]+=delta
            for k,v in (s.get("scaled_event_counts") or {}).items(): event_counts[k]+=int(v)
            for k,v in (s.get("transport_stats") or {}).items(): transport[k]+=int(v)
            debt_transfer_count+=int(s.get("variable_debt_balance_transfer_count",0))

        full_delta_digest=hashlib.sha256(
          "\n".join(
            f"{u}|{t}|{bn}|{delta}"
            for (u,t),by in sorted(merged.items())
            for bn,delta in sorted(by.items())
          ).encode()
        ).hexdigest()

        targets,negatives=base.replay_targets(merged,token_meta)
        receipt.update({
          "unique_borrower_count":int(sample["unique_borrower_count"]),
          "borrow_log_count":int(sample["borrow_log_count"]),
          "sample_borrowers":borrowers,
          "sample_sha256":sample_sha,
          "shard_delta_digests":shard_digests,
          "full_delta_digest_sha256":full_delta_digest,
          "scaled_event_counts":dict(sorted(event_counts.items())),
          "touched_user_token_pairs":len(merged),
          "validation_target_count":len(targets),
          "negative_replay_states":negatives[:100],
          "variable_debt_balance_transfer_count":debt_transfer_count,
          "transport_stats":dict(transport),
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
            receipt["classification"]=classification
            receipt["validation_failures"]=failures[:250]
            receipt["validation_failure_count"]=len(failures)
            receipt["archive_rpc_stats"]=endpoint_stats
            receipt["validated_target_count"]=len(targets)-len(failures)
            receipt["target_digest_sha256"]=hashlib.sha256(
              "\n".join(f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}" for t in targets).encode()
            ).hexdigest()
            receipt["validation_targets"]=targets

    except Exception as exc:
        receipt["classification"]="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1500]}"

    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "classification":receipt["classification"],
      "failure":receipt.get("failure"),
      "borrow_log_count":receipt.get("borrow_log_count"),
      "sample_size":len(receipt.get("sample_borrowers",[])),
      "touched_pairs":receipt.get("touched_user_token_pairs"),
      "validation_targets":receipt.get("validation_target_count"),
      "validation_failures":receipt.get("validation_failure_count"),
      "health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False
    },sort_keys=True))
    return 0 if receipt["classification"]=="R1_AUDIT_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())

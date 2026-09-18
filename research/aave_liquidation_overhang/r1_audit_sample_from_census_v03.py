#!/usr/bin/env python3
"""Derive the frozen 16-borrower R1 audit sample from canonical Source Census shard receipts."""
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from eth_hash.auto import keccak

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
EXPECTED_SHARDS={f"{i:02d}" for i in range(1,9)}
EXPECTED_UNIQUE_BORROWERS=30_691
SAMPLE_SIZE=16

def main()->int:
    out=Path("r1_audit_sample_output")
    out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_R1_AUDIT_SAMPLE_V0_3.json"
    receipt={"lab_id":LAB_ID,"phase":"R1_AUDIT_SAMPLE_FROM_CANONICAL_CENSUS_V0_3","classification":None}
    try:
        files=sorted(Path("downloaded_census_shards").rglob("shard_*.json"))
        if len(files)!=8:
            raise RuntimeError(f"expected 8 canonical census shard receipts, got {len(files)}")
        ids=set()
        borrowers=set()
        ranges=[]
        for p in files:
            obj=json.loads(p.read_text(encoding="utf-8"))
            if obj.get("lab_id")!=LAB_ID or obj.get("classification")!="SHARD_PASS":
                raise RuntimeError(f"noncanonical census shard {p.name}: {obj.get('classification')}")
            sid=str(obj.get("shard_id"))
            ids.add(sid)
            ranges.append([int(obj["from_block"]),int(obj["to_block"])])
            vals=((obj.get("participants_by_event") or {}).get("Borrow") or [])
            borrowers.update(str(x).lower() for x in vals)
            safety=obj.get("safety") or {}
            forbidden=["economic_values_decoded","health_factor_computed","overhang_computed","future_liquidation_outcome_computed","market_prices_opened","returns_opened","pnl_opened","accessed_2025_or_2026","live_trading","exchange_mutation"]
            if any(bool(safety.get(k)) for k in forbidden) or bool(safety.get("log_data_requested")):
                raise RuntimeError(f"safety violation in canonical census shard {sid}")
        if ids!=EXPECTED_SHARDS:
            raise RuntimeError(f"census shard ids mismatch: {sorted(ids)}")
        if len(borrowers)!=EXPECTED_UNIQUE_BORROWERS:
            raise RuntimeError(f"unique borrower count mismatch: {len(borrowers)} != {EXPECTED_UNIQUE_BORROWERS}")
        ranked=sorted(borrowers,key=lambda a:(keccak(bytes.fromhex(a[2:])),a))
        sample=ranked[:SAMPLE_SIZE]
        sample_sha=hashlib.sha256("\n".join(sample).encode()).hexdigest()
        receipt.update({
            "classification":"R1_AUDIT_SAMPLE_PASS",
            "source_census_run_id":35214027573,
            "source_census_shard_count":8,
            "source_census_ranges":sorted(ranges),
            "unique_borrower_count":len(borrowers),
            "sample_size":len(sample),
            "sample_borrowers":sample,
            "sample_sha256":sample_sha,
            "partition_rule":"4 contiguous shards x 4 borrowers in frozen ranked sample order",
            "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        })
    except Exception as exc:
        receipt.update({"classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE","failure":f"{type(exc).__name__}: {str(exc)[:1200]}"})
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"unique_borrowers":receipt.get("unique_borrower_count"),"sample_size":receipt.get("sample_size"),"sample_sha256":receipt.get("sample_sha256")},sort_keys=True))
    return 0 if receipt["classification"]=="R1_AUDIT_SAMPLE_PASS" else 2

if __name__=="__main__":
    sys.exit(main())

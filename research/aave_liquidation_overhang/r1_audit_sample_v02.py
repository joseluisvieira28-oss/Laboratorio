#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
from eth_hash.auto import keccak

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
EXPECTED_RANGES=[
 (16490000,17119486),(17119487,17748973),(17748974,18378460),(18378461,19007946),
 (19007947,19637432),(19637433,20266918),(20266919,20896404),(20896405,21525890),
]
EXPECTED_BORROW_EVENTS=204952
EXPECTED_UNIQUE_BORROWERS=30691
SAMPLE_SIZE=16

def main()->int:
    out=Path("r1_audit_sample_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_R1_AUDIT_SAMPLE_V0_2.json"
    try:
        files=sorted(Path("downloaded_census_shards").rglob("shard_*.json"))
        if len(files)!=8: raise RuntimeError(f"expected 8 census shard receipts, found {len(files)}")
        rows=[]
        for p in files:
            o=json.loads(p.read_text(encoding="utf-8")); rows.append(o)
        rows.sort(key=lambda x:int(x["from_block"]))
        got=[(int(x["from_block"]),int(x["to_block"])) for x in rows]
        if got!=EXPECTED_RANGES: raise RuntimeError(f"census shard ranges mismatch: {got}")
        borrowers=set(); borrow_events=0
        for x in rows:
            if x.get("classification")!="SHARD_PASS": raise RuntimeError(f"non-pass census shard {x.get('shard_id')}")
            safety=x.get("safety") or {}
            forbidden=["economic_values_decoded","health_factor_computed","overhang_computed","future_liquidation_outcome_computed","market_prices_opened","returns_opened","pnl_opened","accessed_2025_or_2026","live_trading","exchange_mutation"]
            if any(bool(safety.get(k)) for k in forbidden): raise RuntimeError("census safety violation")
            borrow_events+=int((x.get("event_counts") or {}).get("Borrow",0))
            borrowers.update((x.get("participants_by_event") or {}).get("Borrow") or [])
        if borrow_events!=EXPECTED_BORROW_EVENTS: raise RuntimeError(f"Borrow event count mismatch {borrow_events}")
        if len(borrowers)!=EXPECTED_UNIQUE_BORROWERS: raise RuntimeError(f"unique borrower count mismatch {len(borrowers)}")
        ranked=sorted((str(a).lower() for a in borrowers), key=lambda a:(keccak(bytes.fromhex(a[2:])),a))
        sample=ranked[:SAMPLE_SIZE]
        sample_sha=hashlib.sha256("\n".join(sample).encode()).hexdigest()
        receipt={
          "lab_id":LAB_ID,
          "phase":"R1_AUDIT_SAMPLE_DERIVATION_V0_2_OUTCOME_BLIND",
          "classification":"R1_AUDIT_SAMPLE_PASS",
          "canonical_source_census_run_id":35214027573,
          "borrow_event_count":borrow_events,
          "unique_borrower_count":len(borrowers),
          "sample_size":len(sample),
          "sample_borrowers":sample,
          "sample_sha256":sample_sha,
          "expected_ranges":EXPECTED_RANGES,
          "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        }
    except Exception as exc:
        receipt={"lab_id":LAB_ID,"phase":"R1_AUDIT_SAMPLE_DERIVATION_V0_2_OUTCOME_BLIND","classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE","failure":f"{type(exc).__name__}: {str(exc)[:1200]}"}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"unique_borrowers":receipt.get("unique_borrower_count"),"sample_size":receipt.get("sample_size"),"sample_sha256":receipt.get("sample_sha256")},sort_keys=True))
    return 0 if receipt["classification"]=="R1_AUDIT_SAMPLE_PASS" else 2

if __name__=="__main__": sys.exit(main())

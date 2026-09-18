#!/usr/bin/env python3
"""Derive the frozen 16-borrower R1 audit sample from canonical Source Census shards."""
from __future__ import annotations
import hashlib,json,sys
from pathlib import Path
from eth_hash.auto import keccak

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
EXPECTED=[
 (16490000,17119486),(17119487,17748973),(17748974,18378460),(18378461,19007946),
 (19007947,19637432),(19637433,20266918),(20266919,20896404),(20896405,21525890),
]
EXPECTED_BORROW_LOGS=204_952
EXPECTED_UNIQUE_BORROWERS=30_691
SAMPLE_SIZE=16

def main()->int:
 out=Path("r1_audit_sample_output"); out.mkdir(parents=True,exist_ok=True)
 dst=out/"AAVE_LIQUIDATION_OVERHANG_001_R1_AUDIT_SAMPLE_V0_3_2.json"
 receipt={"lab_id":LAB_ID,"phase":"R1_AUDIT_SAMPLE_DERIVATION_V0_3_2_OUTCOME_BLIND","classification":None}
 try:
  files=sorted(Path("downloaded_census_shards").rglob("shard_*.json"))
  if len(files)!=8: raise RuntimeError(f"expected 8 canonical census shard receipts, found {len(files)}")
  rows=[json.loads(p.read_text(encoding="utf-8")) for p in files]
  rows.sort(key=lambda x:int(x["from_block"]))
  ranges=[(int(x["from_block"]),int(x["to_block"])) for x in rows]
  if ranges!=EXPECTED: raise RuntimeError(f"canonical census ranges mismatch: {ranges}")
  if any(x.get("classification")!="SHARD_PASS" for x in rows): raise RuntimeError("non-pass canonical census shard")
  borrow_logs=sum(int((x.get("event_counts") or {}).get("Borrow",0)) for x in rows)
  if borrow_logs!=EXPECTED_BORROW_LOGS: raise RuntimeError(f"Borrow log count mismatch {borrow_logs} != {EXPECTED_BORROW_LOGS}")
  borrowers=set()
  for x in rows:
   borrowers.update(str(a).lower() for a in ((x.get("participants_by_event") or {}).get("Borrow") or []))
  if len(borrowers)!=EXPECTED_UNIQUE_BORROWERS:
   raise RuntimeError(f"unique borrower count mismatch {len(borrowers)} != {EXPECTED_UNIQUE_BORROWERS}")
  for a in borrowers:
   if not a.startswith("0x") or len(a)!=42: raise RuntimeError(f"invalid borrower address {a}")
  ranked=sorted(borrowers,key=lambda a:(keccak(bytes.fromhex(a[2:])),a))
  sample=ranked[:SAMPLE_SIZE]
  sample_sha=hashlib.sha256("\n".join(sample).encode()).hexdigest()
  receipt.update({
   "classification":"R1_AUDIT_SAMPLE_PASS",
   "canonical_source_census_run_id":35214027573,
   "canonical_ranges":EXPECTED,
   "borrow_log_count":borrow_logs,
   "unique_borrower_count":len(borrowers),
   "sample_size":len(sample),
   "sample_borrowers":sample,
   "sample_sha256":sample_sha,
   "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,
             "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
             "live_trading":False,"exchange_mutation":False},
  })
 except Exception as exc:
  receipt.update({"classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE","failure":f"{type(exc).__name__}: {str(exc)[:1200]}"})
 dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"classification":receipt["classification"],"unique_borrowers":receipt.get("unique_borrower_count"),
                   "sample_size":receipt.get("sample_size"),"sample_sha256":receipt.get("sample_sha256")},sort_keys=True))
 return 0 if receipt["classification"]=="R1_AUDIT_SAMPLE_PASS" else 2

if __name__=="__main__": sys.exit(main())

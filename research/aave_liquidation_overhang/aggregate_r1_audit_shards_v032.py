#!/usr/bin/env python3
"""Canonical aggregation and adjudication for sharded R1 audit V0.3.2."""
from __future__ import annotations
import hashlib,json,sys
from collections import Counter,defaultdict
from pathlib import Path

import r1_scaled_ledger_audit_v01 as v

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
FROM_BLOCK=16_490_000
TO_BLOCK=21_525_890
AUDIT_BLOCKS=[17_748_972,19_007_945,20_266_917,21_525_890]
EXPECTED=[
 (16490000,17119486),(17119487,17748973),(17748974,18378460),(18378461,19007946),
 (19007947,19637432),(19637433,20266918),(20266919,20896404),(20896405,21525890),
]

def load_exactly_one(root:str,classification:str):
 xs=[]
 for p in Path(root).rglob("*.json"):
  o=json.loads(p.read_text(encoding="utf-8"))
  if o.get("classification")==classification: xs.append(o)
 if len(xs)!=1: raise RuntimeError(f"expected exactly one {classification} under {root}, found {len(xs)}")
 return xs[0]

def main()->int:
 out=Path("r1_scaled_ledger_audit_output"); out.mkdir(parents=True,exist_ok=True)
 dst=out/"AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_3_2.json"
 receipt={"lab_id":LAB_ID,"phase":"R1_SCALED_LEDGER_AUDIT_V0_3_2_SHARDED_OUTCOME_BLIND",
          "protocol":"AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2",
          "frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,"audit_blocks":AUDIT_BLOCKS,
          "classification":None}
 try:
  sample=load_exactly_one("downloaded_r1_sample","R1_AUDIT_SAMPLE_PASS")
  sample_borrowers=[str(x).lower() for x in sample["sample_borrowers"]]
  sample_sha=hashlib.sha256("\n".join(sample_borrowers).encode()).hexdigest()
  if sample_sha!=sample["sample_sha256"]: raise RuntimeError("sample receipt hash mismatch")
  if int(sample["unique_borrower_count"])!=30_691: raise RuntimeError("unique borrower count mismatch")

  bootstrap=load_exactly_one("downloaded_r0_bootstrap","RECONSTRUCTION_R0_BOOTSTRAP_PASS")
  if int(bootstrap.get("frozen_from_block"))!=FROM_BLOCK or int(bootstrap.get("frozen_to_block"))!=TO_BLOCK:
   raise RuntimeError("R0 bootstrap envelope mismatch")
  token_meta,_,_=v.build_token_maps(bootstrap)

  shard_files=sorted(Path("downloaded_r1_token_shards").rglob("*.json"))
  if len(shard_files)!=8: raise RuntimeError(f"expected 8 token shard receipts, found {len(shard_files)}")
  shards=[json.loads(p.read_text(encoding="utf-8")) for p in shard_files]
  shards.sort(key=lambda x:int(x["from_block"]))
  ranges=[(int(x["from_block"]),int(x["to_block"])) for x in shards]
  if ranges!=EXPECTED: raise RuntimeError(f"token shard ranges mismatch: {ranges}")
  if any(x.get("classification")!="R1_AUDIT_TOKEN_SHARD_PASS" for x in shards):
   raise RuntimeError("one or more token shards did not pass acquisition")
  if any(x.get("sample_sha256")!=sample_sha for x in shards):
   raise RuntimeError("sample hash differs across token shards")

  block_deltas=defaultdict(lambda:defaultdict(int))
  event_counts=Counter()
  debt_transfer_count=0
  transport=Counter()
  shard_digests=[]
  for s in shards:
   event_counts.update({k:int(vv) for k,vv in (s.get("scaled_event_counts") or {}).items()})
   debt_transfer_count+=int(s.get("variable_debt_balance_transfer_count",0))
   transport.update({k:int(vv) for k,vv in (s.get("transport_stats") or {}).items()})
   shard_digests.append(str(s.get("block_delta_digest_sha256")))
   for r in s.get("block_deltas") or []:
    user=str(r["user"]).lower(); token=str(r["token"]).lower(); block=int(r["block"]); delta=int(r["delta"])
    if user not in sample_borrowers: raise RuntimeError("delta user escaped frozen sample")
    if token not in token_meta: raise RuntimeError("delta token escaped canonical token map")
    if not (int(s["from_block"])<=block<=int(s["to_block"])): raise RuntimeError("delta block escaped shard range")
    block_deltas[(user,token)][block]+=delta

  targets,negatives=v.replay_targets(block_deltas,token_meta)
  receipt.update({
   "unique_borrower_count":int(sample["unique_borrower_count"]),
   "sample_borrowers":sample_borrowers,
   "sample_sha256":sample_sha,
   "scaled_event_counts":dict(sorted(event_counts.items())),
   "touched_user_token_pairs":len(block_deltas),
   "validation_target_count":len(targets),
   "negative_replay_states":negatives[:100],
   "variable_debt_balance_transfer_count":debt_transfer_count,
   "token_shard_ranges":EXPECTED,
   "token_shard_digests":shard_digests,
   "transport_stats":dict(sorted(transport.items())),
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
   receipt["target_digest_sha256"]=hashlib.sha256(
    "\n".join(f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}" for t in targets).encode()
   ).hexdigest()
   receipt["validation_targets"]=targets

 except Exception as exc:
  receipt["classification"]="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
  receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1500]}"

 receipt["safety"]={"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,
                    "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
                    "live_trading":False,"exchange_mutation":False}
 dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"classification":receipt["classification"],"sample_size":len(receipt.get("sample_borrowers",[])),
                   "touched_pairs":receipt.get("touched_user_token_pairs"),"validation_targets":receipt.get("validation_target_count"),
                   "validation_failures":receipt.get("validation_failure_count"),"health_factor_computed":False,
                   "overhang_computed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
 return 0 if receipt["classification"]=="R1_AUDIT_PASS" else 2

if __name__=="__main__": sys.exit(main())

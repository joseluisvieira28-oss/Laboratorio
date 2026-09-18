#!/usr/bin/env python3
"""Acquire one exact block shard of frozen sample token-native events for R1 audit V0.3.2."""
from __future__ import annotations
import hashlib,json,os,sys
from collections import Counter
from pathlib import Path

import r1_scaled_ledger_audit_v01 as v

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
GLOBAL_FROM=16_490_000
GLOBAL_TO=21_525_890

def load_one(root:str,classification:str):
 files=list(Path(root).rglob("*.json"))
 matches=[]
 for p in files:
  o=json.loads(p.read_text(encoding="utf-8"))
  if o.get("classification")==classification: matches.append(o)
 if len(matches)!=1: raise RuntimeError(f"expected exactly one {classification} under {root}, found {len(matches)}")
 return matches[0]

def main()->int:
 shard_id=int(os.environ["R1_AUDIT_SHARD_ID"])
 start=int(os.environ["R1_AUDIT_FROM_BLOCK"])
 end=int(os.environ["R1_AUDIT_TO_BLOCK"])
 out=Path("r1_audit_token_shards"); out.mkdir(parents=True,exist_ok=True)
 dst=out/f"r1_audit_token_shard_{shard_id:02d}.json"
 receipt={"lab_id":LAB_ID,"phase":"R1_AUDIT_TOKEN_EVENT_SHARD_V0_3_2_OUTCOME_BLIND","shard_id":shard_id,
          "from_block":start,"to_block":end,"classification":None}
 stats=Counter()
 try:
  if not (GLOBAL_FROM<=start<=end<=GLOBAL_TO): raise RuntimeError("shard outside frozen envelope")
  sample_receipt=load_one("downloaded_r1_sample","R1_AUDIT_SAMPLE_PASS")
  sample=[str(x).lower() for x in sample_receipt["sample_borrowers"]]
  if len(sample)!=16 or len(set(sample))!=16: raise RuntimeError("frozen sample must contain exactly 16 unique borrowers")
  sample_sha=hashlib.sha256("\n".join(sample).encode()).hexdigest()
  if sample_sha!=sample_receipt["sample_sha256"]: raise RuntimeError("sample hash mismatch")

  bootstrap=load_one("downloaded_r0_bootstrap","RECONSTRUCTION_R0_BOOTSTRAP_PASS")
  if int(bootstrap.get("frozen_from_block"))!=GLOBAL_FROM or int(bootstrap.get("frozen_to_block"))!=GLOBAL_TO:
   raise RuntimeError("canonical R0 bootstrap envelope mismatch")
  token_meta,atokens,debts=v.build_token_maps(bootstrap)

  # Operational sharding only: reuse the canonical audit implementation on this exact block slice.
  old_from,old_to=v.FROM_BLOCK,v.TO_BLOCK
  v.FROM_BLOCK,v.TO_BLOCK=start,end
  try:
   block_deltas,event_counts,debt_transfer_count=v.acquire_sample_token_deltas(
    sample,token_meta,atokens,debts,stats
   )
  finally:
   v.FROM_BLOCK,v.TO_BLOCK=old_from,old_to

  rows=[]
  for (user,token),by_block in sorted(block_deltas.items()):
   for block,delta in sorted(by_block.items()):
    rows.append({"user":user,"token":token,"block":int(block),"delta":str(int(delta))})
  digest=hashlib.sha256(
   "\n".join(f"{r['block']}|{r['user']}|{r['token']}|{r['delta']}" for r in rows).encode()
  ).hexdigest()
  receipt.update({
   "classification":"R1_AUDIT_TOKEN_SHARD_PASS",
   "sample_sha256":sample_sha,
   "sample_borrowers":sample,
   "scaled_event_counts":dict(sorted(event_counts.items())),
   "variable_debt_balance_transfer_count":int(debt_transfer_count),
   "touched_user_token_pairs":len(block_deltas),
   "block_delta_row_count":len(rows),
   "block_delta_digest_sha256":digest,
   "block_deltas":rows,
   "transport_stats":dict(stats),
   "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,
             "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,
             "live_trading":False,"exchange_mutation":False},
  })
 except Exception as exc:
  receipt.update({"classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE",
                  "failure":f"{type(exc).__name__}: {str(exc)[:1200]}","transport_stats":dict(stats)})
 dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
 print(json.dumps({"shard":shard_id,"classification":receipt["classification"],
                   "delta_rows":receipt.get("block_delta_row_count"),"touched_pairs":receipt.get("touched_user_token_pairs"),
                   "health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
 return 0 if receipt["classification"]=="R1_AUDIT_TOKEN_SHARD_PASS" else 2

if __name__=="__main__": sys.exit(main())

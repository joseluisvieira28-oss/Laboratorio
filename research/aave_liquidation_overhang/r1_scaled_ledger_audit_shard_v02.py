#!/usr/bin/env python3
from __future__ import annotations
import json, os, sys
from collections import Counter
from pathlib import Path
import r1_scaled_ledger_audit_v01 as v

LAB_ID=v.LAB_ID
GLOBAL_FROM=16_490_000
GLOBAL_TO=21_525_890

def load_one(root:str,classification:str):
    xs=[]
    for p in Path(root).rglob("*.json"):
        o=json.loads(p.read_text(encoding="utf-8"))
        if o.get("classification")==classification: xs.append(o)
    if len(xs)!=1: raise RuntimeError(f"expected exactly one {classification} under {root}, got {len(xs)}")
    return xs[0]

def main()->int:
    sid=int(os.environ["R1_AUDIT_SHARD_ID"])
    start=int(os.environ["R1_AUDIT_FROM_BLOCK"])
    end=int(os.environ["R1_AUDIT_TO_BLOCK"])
    if not (GLOBAL_FROM<=start<=end<=GLOBAL_TO): raise SystemExit("invalid shard range")
    out=Path("r1_audit_shards"); out.mkdir(parents=True,exist_ok=True)
    dst=out/f"r1_audit_shard_{sid:02d}.json"
    stats=Counter()
    try:
        sample_receipt=load_one("downloaded_r1_sample","R1_AUDIT_SAMPLE_PASS")
        sample=[str(x).lower() for x in sample_receipt["sample_borrowers"]]
        sample_sha=str(sample_receipt["sample_sha256"])
        if len(sample)!=16: raise RuntimeError("sample size is not 16")
        bootstrap=v.load_bootstrap()
        if int(bootstrap.get("frozen_from_block"))!=GLOBAL_FROM or int(bootstrap.get("frozen_to_block"))!=GLOBAL_TO:
            raise RuntimeError("R0 bootstrap envelope mismatch")
        token_meta,atokens,debts=v.build_token_maps(bootstrap)
        old_from,old_to=v.FROM_BLOCK,v.TO_BLOCK
        try:
            v.FROM_BLOCK=start; v.TO_BLOCK=end
            block_deltas,event_counts,debt_transfer_count=v.acquire_sample_token_deltas(sample,token_meta,atokens,debts,stats)
        finally:
            v.FROM_BLOCK=old_from; v.TO_BLOCK=old_to
        serial=[]
        for (user,token),by_block in sorted(block_deltas.items()):
            serial.append({"user":user,"token":token,"blocks":[[int(b),str(d)] for b,d in sorted(by_block.items())]})
        receipt={
          "lab_id":LAB_ID,
          "phase":"R1_SCALED_LEDGER_AUDIT_SHARD_V0_2_OUTCOME_BLIND",
          "classification":"R1_AUDIT_SHARD_PASS",
          "shard_id":sid,
          "from_block":start,
          "to_block":end,
          "sample_sha256":sample_sha,
          "sample_size":len(sample),
          "scaled_event_counts":dict(sorted(event_counts.items())),
          "variable_debt_balance_transfer_count":debt_transfer_count,
          "block_deltas":serial,
          "touched_user_token_pairs":len(block_deltas),
          "transport_stats":dict(stats),
          "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        }
    except Exception as exc:
        receipt={"lab_id":LAB_ID,"phase":"R1_SCALED_LEDGER_AUDIT_SHARD_V0_2_OUTCOME_BLIND","classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE","shard_id":sid,"from_block":start,"to_block":end,"failure":f"{type(exc).__name__}: {str(exc)[:1200]}","transport_stats":dict(stats)}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"shard_id":sid,"classification":receipt["classification"],"range":[start,end],"pairs":receipt.get("touched_user_token_pairs"),"events":receipt.get("scaled_event_counts"),"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if receipt["classification"]=="R1_AUDIT_SHARD_PASS" else 2

if __name__=="__main__": sys.exit(main())

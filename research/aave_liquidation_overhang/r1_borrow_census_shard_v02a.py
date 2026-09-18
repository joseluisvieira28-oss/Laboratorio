#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, os
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("base_audit", HERE/"r1_scaled_ledger_audit_v01.py")
base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

def main():
    sid=os.environ["R1_SHARD_ID"]
    start=int(os.environ["R1_BLOCK_START"]); end=int(os.environ["R1_BLOCK_END"])
    base.FROM_BLOCK=start; base.TO_BLOCK=end
    stats=Counter(); borrowers=set(); seen=set()
    filters=[{"address":[base.POOL],"topic0":[base.BORROW_TOPIC]}]
    for obj in base.stream_portal(filters,False,stats):
        header=obj.get("header") or obj.get("block") or {}
        bn=int(header["number"])
        if not start<=bn<=end: raise RuntimeError("Borrow row outside shard")
        for log in obj.get("logs") or []:
            topics=log.get("topics") or []
            if len(topics)<3 or str(topics[0]).lower()!=base.BORROW_TOPIC:
                raise RuntimeError("malformed Borrow log")
            txh=str(log.get("transactionHash","")).lower()
            li=base.as_int(log.get("logIndex"))
            ident=f"{txh}|{li}"
            if ident in seen: raise RuntimeError("duplicate Borrow canonical identity inside shard")
            seen.add(ident); borrowers.add(base.topic_address(topics[2]))
    receipt={
      "classification":"BORROW_CENSUS_SHARD_PASS",
      "shard_id":sid,"block_start":start,"block_end":end,
      "borrow_log_count":len(seen),
      "canonical_id_hashes":sorted(hashlib.sha256(x.encode()).hexdigest() for x in seen),
      "unique_borrowers":sorted(borrowers),
      "transport_stats":dict(stats),
      "safety":{"health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False}
    }
    out=Path("r1_borrow_shards"); out.mkdir(parents=True,exist_ok=True)
    p=out/f"borrow_shard_{sid}.json"; p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"shard":sid,"borrow_logs":len(seen),"unique_borrowers":len(borrowers)},sort_keys=True))
if __name__=="__main__": main()

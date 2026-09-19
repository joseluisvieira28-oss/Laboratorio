#!/usr/bin/env python3
"""MSEL-002 V0.4 deterministic transaction-fetch shard. Source/prevalence only."""
from __future__ import annotations
import hashlib,json,os,shutil
from pathlib import Path
import collect_onchain_identity_prevalence_v01 as v1
import collect_onchain_identity_prevalence_v02 as v2  # applies resilient item-level batch retry patch

PROVIDER="https://api.uniblock.dev/uni/v1/json-rpc?chainId=solana"
COUNT=8

def digest(rows):
    h=hashlib.sha256()
    for r in sorted(rows,key=lambda x:(int(x["slot"]),str(x["signature"]))):
        h.update((str(r["slot"])+"|"+str(r["block_time"])+"|"+str(r["signature"])+"\n").encode())
    return h.hexdigest()

def load_upstream(root:Path):
    q=json.loads((root/"qualification_receipt.json").read_text())
    if q.get("classification")!="UNIBLOCK_TRANSPORT_QUALIFICATION_PASS":
        raise RuntimeError(f"qualification not pass: {q.get('classification')}")
    rows=[json.loads(x) for x in (root/"uniblock"/"signatures.jsonl").read_text().splitlines() if x.strip()]
    rows=sorted(rows,key=lambda x:(int(x["slot"]),str(x["signature"])))
    if len(rows)!=9564: raise RuntimeError(f"qualified signature count drift {len(rows)}")
    p=next((x for x in q.get("providers",[]) if x.get("provider")=="uniblock"),None)
    if not p or digest(rows)!=p.get("signature_set_sha256"):
        raise RuntimeError("qualified signature digest mismatch")
    return q,rows

def main():
    sid=int(os.environ["MSEL002_SHARD_ID"])
    if not 0<=sid<COUNT: raise RuntimeError("invalid shard id")
    root=Path(os.environ.get("MSEL002_QUALIFICATION_DIR","downloaded_qualification"))
    q,rows=load_upstream(root)
    selected=[r for i,r in enumerate(rows) if i%COUNT==sid]
    out=Path(f"v04_shard_{sid:02d}")
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    v1.OUT_DIR=out
    v1.RAW_DIR=out/"raw_rpc"
    rpc=v1.Rpc(PROVIDER)
    creates,missing=v1.fetch_transactions(rpc,selected)
    if missing: raise RuntimeError(f"missing transaction results {missing}")
    sdig=digest(selected)
    (out/"selected_signatures.jsonl").write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in selected))
    (out/"decoded_creates.jsonl").write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in sorted(creates,key=lambda r:(r["slot"],r["signature"],r["instruction_scope"],r["instruction_index"]))))
    (out/"rpc_receipts.json").write_text(json.dumps(rpc.receipts,indent=2,sort_keys=True)+"\n")
    receipt={
        "lab_id":"MSEL-002","phase":"V0.4_SHARDED_SOURCE_PREVALENCE_TRANSACTION_ACQUISITION",
        "classification":"V04_SHARD_PASS","shard_id":sid,"shard_count":COUNT,
        "upstream_qualification_run_id":35438540272,
        "upstream_signature_set_sha256":next(x for x in q["providers"] if x["provider"]=="uniblock")["signature_set_sha256"],
        "selected_signature_count":len(selected),"selected_signature_sha256":sdig,
        "decoded_create_count":len(creates),"missing_transaction_results":missing,
        "raw_rpc_file_count":len(list((out/"raw_rpc").glob("*.json"))),
        "safety":{"prevalence_adjudicated":False,"economic_outcomes_opened":False,
                  "graduation_or_migration_opened":False,"returns_opened":False,
                  "live_trading":False,"chain_mutation":False}
    }
    (out/"shard_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"shard":sid,"selected":len(selected),"creates":len(creates),"missing":missing},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())

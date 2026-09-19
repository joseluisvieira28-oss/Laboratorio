#!/usr/bin/env python3
"""MSEL-002 V0.4 canonical sharded source/prevalence aggregate."""
from __future__ import annotations
import hashlib,json,shutil
from pathlib import Path
import collect_onchain_identity_prevalence_v01 as v1

COUNT=8
QUAL_RUN=35438540272

def digest_sig(rows):
    h=hashlib.sha256()
    for r in sorted(rows,key=lambda x:(int(x["slot"]),str(x["signature"]))):
        h.update((str(r["slot"])+"|"+str(r["block_time"])+"|"+str(r["signature"])+"\n").encode())
    return h.hexdigest()

def dump(path,obj):
    blob=(json.dumps(obj,indent=2,sort_keys=True)+"\n").encode()
    path.write_bytes(blob); return hashlib.sha256(blob).hexdigest()

def dump_jsonl(path,rows):
    h=hashlib.sha256()
    with path.open("wb") as f:
        for r in rows:
            b=json.dumps(r,sort_keys=True,separators=(",",":")).encode()+b"\n"; f.write(b); h.update(b)
    return h.hexdigest()

def main():
    qroot=Path("downloaded_qualification")
    q=json.loads((qroot/"qualification_receipt.json").read_text())
    if q.get("classification")!="UNIBLOCK_TRANSPORT_QUALIFICATION_PASS": raise RuntimeError("qualification not pass")
    sigs=[json.loads(x) for x in (qroot/"uniblock"/"signatures.jsonl").read_text().splitlines() if x.strip()]
    sigs=sorted(sigs,key=lambda x:(int(x["slot"]),str(x["signature"])))
    if len(sigs)!=9564: raise RuntimeError("qualified signature count drift")
    expected_up=next(x for x in q["providers"] if x["provider"]=="uniblock")["signature_set_sha256"]
    if digest_sig(sigs)!=expected_up: raise RuntimeError("qualification signature digest mismatch")

    sroot=Path("downloaded_shards")
    receipts=list(sroot.rglob("shard_receipt.json"))
    if len(receipts)!=COUNT: raise RuntimeError(f"expected {COUNT} shard receipts got {len(receipts)}")
    seen_ids=set(); creates=[]
    for p in receipts:
        r=json.loads(p.read_text()); sid=int(r["shard_id"])
        if sid in seen_ids: raise RuntimeError("duplicate shard id")
        seen_ids.add(sid)
        if r.get("classification")!="V04_SHARD_PASS" or int(r.get("shard_count",-1))!=COUNT: raise RuntimeError(f"shard {sid} not pass")
        expected=[x for i,x in enumerate(sigs) if i%COUNT==sid]
        if int(r["selected_signature_count"])!=len(expected) or r["selected_signature_sha256"]!=digest_sig(expected):
            raise RuntimeError(f"shard {sid} deterministic partition mismatch")
        if int(r.get("missing_transaction_results",-1))!=0: raise RuntimeError(f"shard {sid} missing tx")
        cp=p.parent/"decoded_creates.jsonl"
        creates.extend(json.loads(x) for x in cp.read_text().splitlines() if x.strip())
    if seen_ids!=set(range(COUNT)): raise RuntimeError("shard id set mismatch")

    keys=[(r["signature"],r["instruction_scope"],int(r["instruction_index"]),r["mint"]) for r in creates]
    unique_ok=len(keys)==len(set(keys)) and len({r["mint"] for r in creates})==len(creates)
    if not unique_ok: raise RuntimeError("CREATE_UNIQUENESS_FAILURE")
    w=v1.frozen_window()
    candidates,summary=v1.build_features(creates,int(w["candidate_start"]),int(w["source_end"]))
    gates=v1.source_gates(summary,0,True,True)

    out=Path("v04_canonical_output")
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    create_sha=dump_jsonl(out/"decoded_creates_v04.jsonl",sorted(creates,key=lambda r:(r["slot"],r["signature"],r["instruction_scope"],r["instruction_index"])))
    candidate_sha=dump_jsonl(out/"candidate_identity_features_v04.jsonl",candidates)
    summary_sha=dump(out/"source_prevalence_summary_v04.json",summary)
    gates_sha=dump(out/"source_prevalence_gates_v04.json",gates)
    classification=gates["classification"]
    manifest={
        "artifact":"MSEL_002_ONCHAIN_IMMUTABLE_IDENTITY_SOURCE_PREVALENCE_V04_SHARDED",
        "classification":classification,
        "upstream_qualification_run_id":QUAL_RUN,
        "upstream_signature_count":len(sigs),"upstream_signature_set_sha256":expected_up,
        "shard_count":COUNT,"decoded_create_count":len(creates),"missing_transaction_results":0,
        "summary":summary,"gates":gates,"window":w,
        "hashes":{"decoded_creates_v04.jsonl":create_sha,"candidate_identity_features_v04.jsonl":candidate_sha,
                  "source_prevalence_summary_v04.json":summary_sha,"source_prevalence_gates_v04.json":gates_sha},
        "safety":{"economic_outcomes_opened":False,"future_candidate_paths_opened":False,
                  "graduation_or_migration_opened":False,"returns_opened":False,
                  "live_trading":False,"chain_mutation":False}
    }
    man_sha=dump(out/"source_prevalence_manifest_v04.json",manifest)
    print(json.dumps({"classification":classification,**summary,"manifest_sha256":man_sha,"economic_outcomes_opened":False},sort_keys=True))
    return 0
if __name__=="__main__": raise SystemExit(main())

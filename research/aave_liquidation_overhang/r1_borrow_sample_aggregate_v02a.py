#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("base_audit", HERE/"r1_scaled_ledger_audit_v01.py")
base=importlib.util.module_from_spec(spec); spec.loader.exec_module(base)

RANGES=[
("0",16490000,17119486),("1",17119487,17748973),("2",17748974,18378460),("3",18378461,19007946),
("4",19007947,19637432),("5",19637433,20266918),("6",20266919,20896404),("7",20896405,21525890)
]

def main():
    files=sorted(Path("downloaded_borrow_shards").rglob("borrow_shard_*.json"))
    if len(files)!=8: raise SystemExit(f"expected 8 borrower shards, found {len(files)}")
    recs=[json.loads(p.read_text()) for p in files]; recs.sort(key=lambda x:int(x["shard_id"]))
    got=[(str(r["shard_id"]),int(r["block_start"]),int(r["block_end"])) for r in recs]
    if got!=RANGES: raise SystemExit(f"range mismatch {got}")
    all_ids=set(); borrowers=set(); total_logs=0
    for r in recs:
        if r.get("classification")!="BORROW_CENSUS_SHARD_PASS": raise SystemExit("non-pass borrower shard")
        ids=r.get("canonical_id_hashes") or []
        if len(ids)!=len(set(ids)): raise SystemExit("duplicate canonical id hash inside shard receipt")
        overlap=all_ids.intersection(ids)
        if overlap: raise SystemExit(f"cross-shard canonical Borrow duplicate count={len(overlap)}")
        all_ids.update(ids)
        total_logs+=int(r["borrow_log_count"])
        borrowers.update(str(x).lower() for x in r.get("unique_borrowers") or [])
    if total_logs!=204952 or len(all_ids)!=204952:
        raise SystemExit(f"Borrow canonical count mismatch total={total_logs} unique_ids={len(all_ids)}")
    ranked=sorted(borrowers,key=lambda a:(base.keccak(bytes.fromhex(a[2:])),a))
    if len(ranked)<base.SAMPLE_SIZE: raise SystemExit("insufficient unique borrowers")
    sample=ranked[:base.SAMPLE_SIZE]
    sample_sha=hashlib.sha256("\n".join(sample).encode()).hexdigest()
    receipt={
      "classification":"R1_BORROW_SAMPLE_PASS",
      "borrow_log_count":total_logs,
      "unique_borrower_count":len(borrowers),
      "sample_borrowers":sample,
      "sample_size":len(sample),
      "sample_sha256":sample_sha,
      "ranking_rule":"(keccak256(raw20),address)",
      "safety":{"health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False}
    }
    out=Path("r1_borrow_sample"); out.mkdir(parents=True,exist_ok=True)
    p=out/"AAVE_LIQUIDATION_OVERHANG_001_R1_BORROW_SAMPLE_V0_2A.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"borrow_logs":total_logs,"unique_borrowers":len(borrowers),"sample_size":len(sample),"sample_sha256":sample_sha},sort_keys=True))
if __name__=="__main__": main()

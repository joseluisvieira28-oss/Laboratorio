#!/usr/bin/env python3
import argparse
import hashlib
import json
import pathlib

def sha256_file(path: pathlib.Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""):
            h.update(chunk)
    return h.hexdigest()

def tree_manifest(root: pathlib.Path):
    rows=[]
    if not root.exists():
        return rows
    for p in sorted(x for x in root.rglob("*") if x.is_file()):
        rel=p.relative_to(root).as_posix()
        rows.append({"path":rel,"bytes":p.stat().st_size,"sha256":sha256_file(p)})
    return rows

def aggregate(rows):
    h=hashlib.sha256()
    for r in rows:
        h.update(r["path"].encode()); h.update(b"\0")
        h.update(str(r["bytes"]).encode()); h.update(b"\0")
        h.update(r["sha256"].encode()); h.update(b"\n")
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--db-dir",required=True)
    ap.add_argument("--home-dir",required=True)
    ap.add_argument("--chunk-receipt",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--source-commit",required=True)
    ap.add_argument("--genesis-sha256",required=True)
    ap.add_argument("--parent-checkpoint")
    a=ap.parse_args()

    chunk_raw=pathlib.Path(a.chunk_receipt).read_bytes()
    chunk=json.loads(chunk_raw)
    db_rows=tree_manifest(pathlib.Path(a.db_dir))
    home_rows=tree_manifest(pathlib.Path(a.home_dir))
    parent=None
    if a.parent_checkpoint:
        parent_raw=pathlib.Path(a.parent_checkpoint).read_bytes()
        parent={"sha256":hashlib.sha256(parent_raw).hexdigest(),"path":a.parent_checkpoint}
    out={
        "schema":"coreum-v08-local-checkpoint-v1",
        "chain_id":"coreum-mainnet-1",
        "source_commit":a.source_commit,
        "genesis_sha256":a.genesis_sha256,
        "start_height":chunk["start_height"],
        "end_height":chunk["end_height"],
        "final_app_hash":chunk["final_app_hash"],
        "chunk_receipt_sha256":hashlib.sha256(chunk_raw).hexdigest(),
        "block_results_consumed_from_rpc":False,
        "census_executed":False,
        "market_outcomes_opened":False,
        "parent_checkpoint":parent,
        "application_and_state_db":{"files":db_rows,"aggregate_sha256":aggregate(db_rows),"bytes":sum(r["bytes"] for r in db_rows)},
        "home":{"files":home_rows,"aggregate_sha256":aggregate(home_rows),"bytes":sum(r["bytes"] for r in home_rows)},
    }
    raw=json.dumps(out,indent=2,sort_keys=True).encode()+b"\n"
    pathlib.Path(a.out).write_bytes(raw)
    print(json.dumps({
        "end_height":out["end_height"],
        "final_app_hash":out["final_app_hash"],
        "db_bytes":out["application_and_state_db"]["bytes"],
        "db_aggregate_sha256":out["application_and_state_db"]["aggregate_sha256"],
        "home_aggregate_sha256":out["home"]["aggregate_sha256"],
        "checkpoint_sha256":hashlib.sha256(raw).hexdigest(),
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED_ROWS=1012
EXPECTED_INDICES=set(range(EXPECTED_ROWS))
MIN_VIABLE=1000
DETAIL_STAGE="CHAIN_EXACT_CEILING_V073_BLOCKFIRST_SHARD"
TRANSPORT="V073_FINALIZED_BLOCK_FIRST"
PARSER="V07_MIGRATE_AND_MIGRATE_V2"

def read_jsonl(p:Path):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-root",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()
    root=Path(a.input_root)
    df=sorted(root.rglob("chain_exact_ceiling_details.jsonl"))
    rf=sorted(root.rglob("chain_exact_ceiling_shard_receipt.json"))
    rows=[]; receipts=[]; malformed=0
    for p in df:
        try: rows.extend(read_jsonl(p))
        except Exception: malformed+=1
    for p in rf:
        try: receipts.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception: malformed+=1
    indices=[r.get("frozen_manifest_index") for r in rows]
    vi=[int(x) for x in indices if isinstance(x,int)]
    mints=[r.get("mint") for r in rows]
    outcome_wall=all(r.get("outcomes_opened") is False and r.get("economic_outcomes_opened") is False for r in rows)
    detail_contract=all(
        r.get("stage")==DETAIL_STAGE and r.get("transport_version")==TRANSPORT
        and r.get("boundary_parser_version")==PARSER and r.get("scientific_verdict_authority") is False
        for r in rows
    )
    receipt_contract=all(
        r.get("stage")==DETAIL_STAGE and r.get("transport_version")==TRANSPORT
        and r.get("boundary_parser_version")==PARSER and r.get("economic_outcomes_opened") is False
        and r.get("scientific_verdict_authority") is False for r in receipts
    )
    reconciliation_ok=(
        len(rows)==EXPECTED_ROWS and len(vi)==EXPECTED_ROWS
        and set(vi)==EXPECTED_INDICES and len(set(vi))==EXPECTED_ROWS
        and len(mints)==EXPECTED_ROWS and len(set(mints))==EXPECTED_ROWS and None not in mints
        and malformed==0 and outcome_wall and detail_contract and receipt_contract
        and len(receipts)==len(df)
    )
    resolved=sum(bool(r.get("source_resolved")) for r in rows)
    success=sum(bool(r.get("ceiling_has_successful_preboundary_signature")) for r in rows)
    unresolved_indices=sorted(int(r["frozen_manifest_index"]) for r in rows if not r.get("source_resolved"))
    verdict=("CHAIN_EXACT_CEILING_V074_VIABLE" if reconciliation_ok and success>=MIN_VIABLE
             else "CHAIN_EXACT_CEILING_V074_INSUFFICIENT" if reconciliation_ok
             else "CHAIN_EXACT_CEILING_V074_UNRESOLVED")
    canon="".join(json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n"
                  for r in sorted(rows,key=lambda r:int(r.get("frozen_manifest_index",-1))))
    out=Path(a.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"chain_exact_ceiling_v074_rows.jsonl").write_text(canon,encoding="utf-8")
    receipt={
      "lab":"PMD-001","stage":"CHAIN_EXACT_CEILING_V074_ADJUDICATION",
      "authority_basis":"PREEXISTING_GE1000_CEILING_AND_SOURCE_GATE",
      "economic_outcomes_opened":False,"expected_rows":EXPECTED_ROWS,"rows":len(rows),
      "details_files":len(df),"shard_receipts":len(receipts),"malformed_inputs":malformed,
      "unique_indices":len(set(vi)),"unique_mints":len(set(mints)),
      "full_index_set_reconciled":set(vi)==EXPECTED_INDICES,
      "outcome_wall_intact":outcome_wall,"detail_contract_ok":detail_contract,
      "receipt_contract_ok":receipt_contract,"source_resolved_rows":resolved,
      "unresolved_indices":unresolved_indices,
      "rows_with_successful_preboundary_signature":success,
      "minimum_viable":MIN_VIABLE,"rows_sha256":hashlib.sha256(canon.encode()).hexdigest(),
      "verdict":verdict
    }
    (out/"chain_exact_ceiling_v074_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if verdict=="CHAIN_EXACT_CEILING_V074_VIABLE" else 2
if __name__=="__main__": raise SystemExit(main())

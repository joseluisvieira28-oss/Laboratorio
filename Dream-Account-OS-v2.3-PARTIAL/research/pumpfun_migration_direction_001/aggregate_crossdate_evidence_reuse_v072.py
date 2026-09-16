#!/usr/bin/env python3
"""Aggregate all 20 mandatory PMD-001 V0.7.2 reuse row receipts."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_ROWS = 20
EXPECTED_INDICES = set(range(EXPECTED_ROWS))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    files = sorted(Path(args.input_root).rglob("v072_row_receipt.json"))
    rows=[]; malformed=0
    for p in files:
        try:
            rows.append(json.loads(p.read_text(encoding="utf-8")))
        except Exception:
            malformed += 1

    indices=[r.get("crossdate_manifest_index") for r in rows]
    valid_indices=[int(x) for x in indices if isinstance(x,int)]
    mints=[r.get("mint") for r in rows]
    dates={str(r.get("t0"))[:10] for r in rows if r.get("t0")}
    outcomes_closed=all(r.get("outcomes_opened") is False for r in rows)
    stage_ok=all(r.get("stage")=="CHAIN_EXACT_CROSSDATE_V072_REUSE_ROW" for r in rows)
    no_row_authority=all(r.get("scientific_verdict_authority") is False for r in rows)
    boundaries=sum(int(r.get("qualifying_boundaries") or 0)==1 for r in rows)
    complete=sum(bool(r.get("source_complete")) for r in rows)
    eligible=sum(bool(r.get("feature_source_eligible")) for r in rows)

    reconciliation=(
        len(files)==EXPECTED_ROWS and len(rows)==EXPECTED_ROWS and malformed==0
        and len(valid_indices)==EXPECTED_ROWS and set(valid_indices)==EXPECTED_INDICES and len(set(valid_indices))==EXPECTED_ROWS
        and None not in mints and len(set(mints))==EXPECTED_ROWS and len(dates)==EXPECTED_ROWS
        and outcomes_closed and stage_ok and no_row_authority
    )
    if reconciliation and boundaries==EXPECTED_ROWS and complete==EXPECTED_ROWS and eligible==EXPECTED_ROWS:
        verdict="CHAIN_EXACT_CROSSDATE_V072_REUSE_PASS"
    elif reconciliation:
        verdict="CHAIN_EXACT_CROSSDATE_V072_REUSE_FAIL"
    else:
        verdict="CHAIN_EXACT_CROSSDATE_V072_REUSE_TECHNICAL_INCOMPLETE"

    sorted_rows=sorted(rows,key=lambda r:int(r.get("crossdate_manifest_index",-1)))
    canon="".join(json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n" for r in sorted_rows)
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    (out/"chain_exact_crossdate_v072_reuse_rows.jsonl").write_text(canon,encoding="utf-8")
    receipt={
        "lab":"PMD-001","stage":"CHAIN_EXACT_CROSSDATE_V072_REUSE","economic_outcomes_opened":False,
        "row_receipts":len(files),"rows":len(rows),"malformed_receipts":malformed,
        "unique_indices":len(set(valid_indices)),"full_index_set_reconciled":set(valid_indices)==EXPECTED_INDICES,
        "unique_mints":len(set(mints)),"distinct_dates":len(dates),"unique_chain_boundaries":boundaries,
        "source_complete_mints":complete,"feature_source_eligible_mints":eligible,
        "total_gap_slots_required":sum(int(r.get("gap_slots_required") or 0) for r in rows),
        "outcome_wall_intact":outcomes_closed,"rows_sha256":hashlib.sha256(canon.encode()).hexdigest(),
        "verdict":verdict,
    }
    (out/"chain_exact_crossdate_v072_reuse_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if verdict=="CHAIN_EXACT_CROSSDATE_V072_REUSE_PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())

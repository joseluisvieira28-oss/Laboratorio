#!/usr/bin/env python3
"""PMD-001 V0.7.4 distributed full-source gate.

SOURCE-ONLY. Reconciles every returned summary row against the frozen 1,012-row
manifest, then applies the pre-existing >=1000 eligible / >=20 dates gate.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED_ROWS=1012
MIN_ELIGIBLE=1000
MIN_ELIGIBLE_DATES=20

def read_jsonl(p:Path):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-root",required=True)
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    manifest=read_jsonl(Path(a.manifest))
    expected={str(r["mint"]):r for r in manifest}
    files=sorted(Path(a.input_root).rglob("source_rebuild_summary.jsonl"))
    rows=[]; malformed=0
    for p in files:
        try: rows.extend(read_jsonl(p))
        except Exception: malformed+=1

    mints=[str(r.get("mint")) for r in rows if r.get("mint")]
    by_mint={}
    duplicates=[]
    for r in rows:
        m=r.get("mint")
        if not m: continue
        m=str(m)
        if m in by_mint: duplicates.append(m)
        else: by_mint[m]=r

    unexpected=sorted(set(by_mint)-set(expected))
    missing=sorted(set(expected)-set(by_mint))
    field_mismatches=[]
    for m,r in by_mint.items():
        e=expected.get(m)
        if not e: continue
        if str(r.get("t0"))!=str(e.get("t0")) or str(r.get("pool_address"))!=str(e.get("pool_address")):
            field_mismatches.append(m)

    outcomes_closed=all(r.get("outcomes_opened") is False for r in rows)
    stage_ok=all(r.get("stage")=="CHAIN_EXACT_SOURCE_REBUILD_V07" for r in rows)
    parser_ok=all(r.get("boundary_parser_version")=="V07_MIGRATE_AND_MIGRATE_V2" for r in rows)

    eligible=[r for r in rows if bool(r.get("feature_source_eligible"))]
    eligible_dates={str(r.get("t0"))[:10] for r in eligible if r.get("t0")}
    source_complete=sum(bool(r.get("source_complete")) for r in rows)

    reconciliation_ok=(
        len(manifest)==EXPECTED_ROWS and len(expected)==EXPECTED_ROWS
        and len(rows)==EXPECTED_ROWS and len(by_mint)==EXPECTED_ROWS
        and not duplicates and not unexpected and not missing and not field_mismatches
        and malformed==0 and outcomes_closed and stage_ok and parser_ok
    )
    if not reconciliation_ok:
        verdict="CHAIN_EXACT_SOURCE_GATE_V074_TECHNICAL_INCOMPLETE"
    elif len(eligible)>=MIN_ELIGIBLE and len(eligible_dates)>=MIN_ELIGIBLE_DATES:
        verdict="CHAIN_EXACT_SOURCE_GATE_V074_PASS"
    else:
        verdict="CHAIN_EXACT_SOURCE_GATE_V074_INSUFFICIENT_SAMPLE"

    canon="".join(json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n"
                  for r in sorted(rows,key=lambda x:(str(x.get("t0")),str(x.get("mint")))))
    out=Path(a.out_dir);out.mkdir(parents=True,exist_ok=True)
    (out/"chain_exact_source_gate_v074_rows.jsonl").write_text(canon,encoding="utf-8")
    receipt={
      "lab":"PMD-001","stage":"CHAIN_EXACT_SOURCE_GATE_V074_DISTRIBUTED",
      "authority_basis":"FROZEN_GE1000_ELIGIBLE_AND_20_DATES",
      "economic_outcomes_opened":False,
      "expected_rows":EXPECTED_ROWS,"manifest_rows":len(manifest),"summary_files":len(files),
      "rows":len(rows),"unique_mints":len(by_mint),"duplicate_mints":duplicates,
      "unexpected_mints":unexpected,"missing_mints":missing,"field_mismatches":field_mismatches,
      "malformed_inputs":malformed,"outcome_wall_intact":outcomes_closed,
      "stage_ok":stage_ok,"parser_version_ok":parser_ok,
      "source_complete_rows":source_complete,
      "feature_source_eligible_rows":len(eligible),"minimum_eligible_rows":MIN_ELIGIBLE,
      "eligible_distinct_dates":len(eligible_dates),"minimum_eligible_dates":MIN_ELIGIBLE_DATES,
      "rows_sha256":hashlib.sha256(canon.encode()).hexdigest(),"verdict":verdict
    }
    (out/"chain_exact_source_gate_v074_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if verdict=="CHAIN_EXACT_SOURCE_GATE_V074_PASS" else 2
if __name__=="__main__": raise SystemExit(main())

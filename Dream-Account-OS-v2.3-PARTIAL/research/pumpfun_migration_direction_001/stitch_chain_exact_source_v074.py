#!/usr/bin/env python3
"""PMD-001 V0.7.4 source-evidence stitcher.

Combines distributed full-source artifacts with independently recovered heavy-row
artifacts. It never fabricates or overwrites scientific fields. Duplicate mints
must agree on frozen identity/boundary fields or the stitch fails closed.
"""
from __future__ import annotations
import argparse, json, shutil
from pathlib import Path

IDENTITY_FIELDS=("mint","t0","pool_address","bonding_curve_pda")
BOUNDARY_FIELDS=("chain_boundary_block_time","chain_boundary_slot","chain_boundary_transaction_index")

def read_jsonl(p:Path):
    return [json.loads(x) for x in p.read_text(encoding="utf-8").splitlines() if x.strip()]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--primary-root",required=True)
    ap.add_argument("--rescue-root",required=True)
    ap.add_argument("--out-dir",required=True)
    a=ap.parse_args()

    manifest=read_jsonl(Path(a.manifest))
    expected=[str(r["mint"]) for r in manifest]
    expected_set=set(expected)
    candidates={}
    provenance={}
    conflicts=[]

    for label,root in (("primary",Path(a.primary_root)),("rescue",Path(a.rescue_root))):
        for p in sorted(root.rglob("source_rebuild_summary.jsonl")):
            for r in read_jsonl(p):
                if r.get("outcomes_opened") is not False:
                    raise RuntimeError(f"outcome wall violation in {p}")
                m=str(r.get("mint") or "")
                if not m: continue
                candidates.setdefault(m,[]).append(r)
                provenance.setdefault(m,[]).append({"label":label,"summary_file":str(p)})

    selected={}
    duplicate_mints=[]
    for m,rows in candidates.items():
        if len(rows)>1:
            duplicate_mints.append(m)
            ref=rows[0]
            for other in rows[1:]:
                for f in IDENTITY_FIELDS+BOUNDARY_FIELDS:
                    if ref.get(f)!=other.get(f):
                        conflicts.append({"mint":m,"field":f,"a":ref.get(f),"b":other.get(f)})
        # Prefer source-complete + feature-eligible evidence; otherwise first deterministic row.
        rows_sorted=sorted(rows,key=lambda r:(not bool(r.get("source_complete")),not bool(r.get("feature_source_eligible"))))
        selected[m]=rows_sorted[0]

    unexpected=sorted(set(selected)-expected_set)
    missing=[m for m in expected if m not in selected]
    if conflicts or unexpected:
        raise RuntimeError(json.dumps({"conflicts":conflicts,"unexpected":unexpected},sort_keys=True))

    out=Path(a.out_dir); raw_out=out/"raw"; raw_out.mkdir(parents=True,exist_ok=True)
    ordered=[]
    raw_missing=[]
    raw_source={}
    roots=[Path(a.primary_root),Path(a.rescue_root)]
    for m in expected:
        if m not in selected: continue
        ordered.append(selected[m])
        hits=[]
        for root in roots:
            hits.extend(root.rglob(f"raw/{m}.jsonl"))
        if not hits:
            raw_missing.append(m);continue
        # All candidate raw files must be outcome-blind.
        good=[]
        for p in hits:
            rows=read_jsonl(p)
            if all(r.get("outcomes_opened") is False for r in rows):
                good.append(p)
        if not good:
            raw_missing.append(m);continue
        src=sorted(good,key=lambda p:str(p))[0]
        shutil.copyfile(src,raw_out/f"{m}.jsonl")
        raw_source[m]=str(src)

    (out/"source_rebuild_summary.jsonl").write_text(
        "".join(json.dumps(r,sort_keys=True,separators=(",",":"),ensure_ascii=False)+"\n" for r in ordered),
        encoding="utf-8"
    )
    receipt={
      "lab":"PMD-001","stage":"CHAIN_EXACT_SOURCE_STITCH_V074",
      "economic_outcomes_opened":False,
      "manifest_rows":len(manifest),"stitched_rows":len(ordered),
      "unique_mints":len({r.get("mint") for r in ordered}),
      "duplicate_mints":sorted(duplicate_mints),
      "conflicts":conflicts,"unexpected_mints":unexpected,"missing_mints":missing,
      "raw_files_copied":len(raw_source),"raw_missing_mints":raw_missing,
      "full_summary_reconciled":len(ordered)==len(manifest) and not missing,
      "full_raw_reconciled":len(raw_source)==len(manifest) and not raw_missing,
      "source_complete_rows":sum(bool(r.get("source_complete")) for r in ordered),
      "feature_source_eligible_rows":sum(bool(r.get("feature_source_eligible")) for r in ordered),
      "provenance":provenance,
    }
    (out/"source_stitch_v074_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({k:receipt[k] for k in [
      "stitched_rows","unique_mints","missing_mints","raw_files_copied","raw_missing_mints",
      "source_complete_rows","feature_source_eligible_rows","full_summary_reconciled","full_raw_reconciled"
    ]},indent=2,sort_keys=True))
    return 0 if receipt["full_summary_reconciled"] and receipt["full_raw_reconciled"] else 2

if __name__=="__main__": raise SystemExit(main())

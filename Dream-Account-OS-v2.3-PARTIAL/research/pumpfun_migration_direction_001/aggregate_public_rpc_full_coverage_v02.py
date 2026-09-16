#!/usr/bin/env python3
"""Aggregate PMD-001 V0.2 public-RPC coverage shards. PRE-OUTCOME only."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

EXPECTED_POPULATION=1012
MIN_TOTAL=1000
MIN_VAL=200
MIN_HOLDOUT=200
MIN_DATES=20


def sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()


def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument('--root',default='downloaded_shards'); ap.add_argument('--out-dir',default='artifacts/pmd001_public_rpc_full_coverage_v02_aggregate'); args=ap.parse_args()
    root=Path(args.root); out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    files=sorted(root.rglob('coverage_audit.jsonl'))
    if not files:
        raise SystemExit('no coverage audits found')
    rows=[]; input_hashes={}
    for p in files:
        input_hashes[str(p)]=sha256(p)
        for line in p.read_text(encoding='utf-8').splitlines():
            if line.strip(): rows.append(json.loads(line))
    rows.sort(key=lambda r:int(r['manifest_index']))
    idx=[int(r['manifest_index']) for r in rows]
    unique=len(set(idx))
    complete=(len(rows)==EXPECTED_POPULATION and unique==EXPECTED_POPULATION and idx==list(range(EXPECTED_POPULATION)))
    resolved=[r for r in rows if r.get('classification')=='RESOLVED']
    unresolved=[r for r in rows if r.get('classification')!='RESOLVED']
    n300=sum((r.get('n300') or 0)>0 for r in resolved)
    n60=sum((r.get('n60') or 0)>0 for r in resolved)
    n30=sum((r.get('n30') or 0)>0 for r in resolved)
    dates300=sorted({r.get('migration_date') for r in resolved if (r.get('n300') or 0)>0 and r.get('migration_date')})
    # The frozen first MVE requires final-curve activity, and 300s is the broadest allowed raw window.
    source_gate=(complete and not unresolved and n300>=MIN_TOTAL and int(n300*0.20)>=MIN_VAL and n300-int(n300*0.60)-int(n300*0.20)>=MIN_HOLDOUT and len(dates300)>=MIN_DATES)
    classification='PUBLIC_RPC_SOURCE_COVERAGE_GATE_PASS_READY_FOR_FULL_TX_RECONSTRUCTION' if source_gate else 'PUBLIC_RPC_SOURCE_COVERAGE_GATE_FAIL_OR_INCOMPLETE'
    merged=out/'coverage_audit_1012.jsonl'
    merged.write_text(''.join(json.dumps(r,sort_keys=True,default=str)+'\n' for r in rows),encoding='utf-8')
    receipt={
      'lab':'PMD-001','stage':'PUBLIC_RPC_FULL_COVERAGE_AGGREGATE_V02','expected_population':EXPECTED_POPULATION,
      'rows_received':len(rows),'unique_manifest_indices':unique,'manifest_complete':complete,
      'resolved_rows':len(resolved),'unresolved_rows':len(unresolved),'rows_with_any_300':n300,'rows_with_any_60':n60,'rows_with_any_30':n30,
      'distinct_migration_dates_with_300s_activity':len(dates300),'frozen_min_total':MIN_TOTAL,'frozen_min_validation':MIN_VAL,'frozen_min_holdout':MIN_HOLDOUT,'frozen_min_dates':MIN_DATES,
      'projected_count_split_if_300s_source_valid':{'discovery':int(n300*0.60),'validation':int(n300*0.20),'holdout':n300-int(n300*0.60)-int(n300*0.20)},
      'input_audit_sha256':input_hashes,'merged_audit_sha256':sha256(merged),'classification':classification,
      'outcomes_opened':False,'forbidden_outcome_file_acquired':False,
      'note':'PASS here authorizes full pre-T0 transaction reconstruction only; it does not authorize returns or Discovery outcomes.'
    }
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())

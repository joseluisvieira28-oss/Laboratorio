#!/usr/bin/env python3
"""Aggregate the mandatory 20 PMD-001 chain-exact V0.7 cross-date rows."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_ROWS=20
EXPECTED_INDICES=set(range(EXPECTED_ROWS))
ARTIFACT_RE=re.compile(r'PMD-001-chain-exact-v07-row-(\d+)$')


def artifact_index(path:Path):
    for p in path.parents:
        m=ARTIFACT_RE.match(p.name)
        if m:return int(m.group(1))
    return None


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--input-root',required=True)
    ap.add_argument('--out-dir',required=True)
    args=ap.parse_args()

    files=sorted(Path(args.input_root).rglob('source_rebuild_summary.jsonl'))
    rows=[]; indices=[]; malformed=0
    for p in files:
        idx=artifact_index(p)
        parts=[json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
        if idx is None or len(parts)!=1: malformed+=1
        for r in parts:
            r=dict(r); r['crossdate_manifest_index']=idx
            rows.append(r)
            if idx is not None: indices.append(idx)

    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    mints=[r.get('mint') for r in rows]
    dates={str(r.get('t0'))[:10] for r in rows if r.get('t0')}
    duplicate_mints=len(mints)-len(set(mints))
    duplicate_indices=len(indices)-len(set(indices))
    index_ok=set(indices)==EXPECTED_INDICES
    outcomes_closed=all(r.get('outcomes_opened') is False for r in rows)
    stage_ok=all(r.get('stage')=='CHAIN_EXACT_SOURCE_REBUILD_V07' for r in rows)
    parser_ok=all(r.get('boundary_parser_version')=='V07_MIGRATE_AND_MIGRATE_V2' for r in rows)
    complete=sum(bool(r.get('source_complete')) for r in rows)
    eligible=sum(bool(r.get('feature_source_eligible')) for r in rows)
    unique_boundaries=sum(int(r.get('qualifying_pool_creation_boundaries') or 0)==1 for r in rows)

    reconciliation_ok=(
        len(files)==EXPECTED_ROWS and len(rows)==EXPECTED_ROWS and len(set(mints))==EXPECTED_ROWS
        and duplicate_mints==0 and len(dates)==EXPECTED_ROWS and duplicate_indices==0 and index_ok
        and malformed==0 and outcomes_closed and stage_ok and parser_ok
    )
    if not reconciliation_ok:
        verdict='CHAIN_EXACT_CROSSDATE_V07_TECHNICAL_INCOMPLETE'
    elif complete==EXPECTED_ROWS and eligible==EXPECTED_ROWS and unique_boundaries==EXPECTED_ROWS:
        verdict='CHAIN_EXACT_CROSSDATE_V07_PASS'
    else:
        verdict='CHAIN_EXACT_CROSSDATE_V07_FAIL'

    canon=''.join(json.dumps(r,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n'
                  for r in sorted(rows,key=lambda x:int(x.get('crossdate_manifest_index') if x.get('crossdate_manifest_index') is not None else -1)))
    rows_sha=hashlib.sha256(canon.encode()).hexdigest()
    (out/'chain_exact_crossdate_v07_rows.jsonl').write_text(canon,encoding='utf-8')
    receipt={
        'lab':'PMD-001','stage':'CHAIN_EXACT_CROSSDATE_V07','economic_outcomes_opened':False,
        'probe_rows':len(rows),'artifact_files_found':len(files),'unique_mints':len(set(mints)),
        'duplicate_mints':duplicate_mints,'distinct_dates':len(dates),
        'unique_manifest_indices':len(set(indices)),'duplicate_manifest_indices':duplicate_indices,
        'full_index_set_reconciled':index_ok,'malformed_artifacts':malformed,
        'parser_semantics':'migrate+migrate_v2','parser_version_ok':parser_ok,
        'unique_chain_boundaries':unique_boundaries,'source_complete_mints':complete,
        'feature_source_eligible_mints':eligible,'outcome_wall_intact':outcomes_closed,
        'rows_sha256':rows_sha,'verdict':verdict,
    }
    (out/'chain_exact_crossdate_v07_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if verdict=='CHAIN_EXACT_CROSSDATE_V07_PASS' else 2

if __name__=='__main__': raise SystemExit(main())

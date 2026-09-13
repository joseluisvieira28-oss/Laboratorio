#!/usr/bin/env python3
"""Merge complete outcome-blind OPTIONS-SPOTPERP-001 yearly raw shards.

The merger makes no scientific source PASS/FAIL decision. It only verifies that
four non-overlapping frozen-window shards are complete, protected-period flags
are false, raw-page hashes are intact, and then constructs one global manifest
for the latest required-field + canonical calendar-day Source/Data Gate.

NO skew, signal, return, regression or PnL is computed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

YEARS = (2021, 2022, 2023, 2024)
EXPECTED_PERIODS = {
    2021: ("2021-04-01T00:00:00+00:00", "2022-01-01T00:00:00+00:00"),
    2022: ("2022-01-01T00:00:00+00:00", "2023-01-01T00:00:00+00:00"),
    2023: ("2023-01-01T00:00:00+00:00", "2024-01-01T00:00:00+00:00"),
    2024: ("2024-01-01T00:00:00+00:00", "2025-01-01T00:00:00+00:00"),
}
PROTOCOL_SHA = "138cee737d75d27b43d9f377fc9a77e823e8fb2015f360b300cdc4a16cf67cfa"


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()


def load_shard(root: Path, year: int) -> tuple[dict[str,Any],dict[str,Any]]:
    m=json.loads((root/'source_manifest.json').read_text())
    r=json.loads((root/'source_audit_report.json').read_text())
    if m.get('probe_mode') is not False or m.get('source_fetch_complete') is not True:
        raise RuntimeError(f'{year}: incomplete/non-full shard')
    if m.get('holdout_accessed') is not False or m.get('locked_2026_accessed') is not False:
        raise RuntimeError(f'{year}: protected-period flag')
    if r.get('outcome_metrics_computed') is not False:
        raise RuntimeError(f'{year}: outcome metric flag')
    a=r.get('audit',{})
    for k in ('skew_values_computed','forward_returns_computed','pnl_computed'):
        if a.get(k) is not False:
            raise RuntimeError(f'{year}: outcome audit flag {k}')
    p=m.get('requested_period',{})
    exp_start,exp_end=EXPECTED_PERIODS[year]
    if p.get('start')!=exp_start or p.get('end_exclusive')!=exp_end:
        raise RuntimeError(f'{year}: shard period {p} != {(exp_start,exp_end)}')
    if m.get('protocol_sha256') != PROTOCOL_SHA:
        raise RuntimeError(f'{year}: protocol hash mismatch')
    return m,r


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--shards-root',default='year_shards')
    ap.add_argument('--output',default='source_audit_data')
    args=ap.parse_args()
    sroot=Path(args.shards_root).resolve()
    out=Path(args.output).resolve()
    raw_out=out/'raw'
    if out.exists(): shutil.rmtree(out)
    raw_out.mkdir(parents=True)

    merged_pages=[]
    total_trades=0
    requested_windows=completed_windows=0
    shard_summary={}
    for year in YEARS:
        root=sroot/str(year)
        m,r=load_shard(root,year)
        total_trades += int(r.get('audit',{}).get('total_trades',0) or 0)
        requested_windows += int(m.get('requested_top_level_windows',0) or 0)
        completed_windows += int(m.get('completed_top_level_windows',0) or 0)
        copied=0
        for i,e in enumerate(m.get('raw_pages',[]),start=1):
            src=root/'raw'/str(e['page'])
            if not src.exists() or sha256_file(src)!=e.get('sha256'):
                raise RuntimeError(f'{year}: raw hash failure {src.name}')
            new_name=f'y{year}_{i:06d}_{src.name}'
            dst=raw_out/new_name
            shutil.copyfile(src,dst)
            if sha256_file(dst)!=e.get('sha256'):
                raise RuntimeError(f'{year}: copied raw hash failure {new_name}')
            ne=dict(e); ne['page']=new_name; ne['source_shard_year']=year
            merged_pages.append(ne); copied += 1
        shard_summary[str(year)]={
            'raw_pages':copied,
            'total_trades_reported':int(r.get('audit',{}).get('total_trades',0) or 0),
            'manifest_sha256':sha256_file(root/'source_manifest.json'),
            'report_sha256':sha256_file(root/'source_audit_report.json'),
        }

    manifest={
        'lab_id':'OPTIONS-SPOTPERP-001','version':'V0.1','protocol_sha256':PROTOCOL_SHA,
        'stage':'SOURCE_AUDIT_ONLY_YEAR_SHARD_MERGE','status':'SHARD_MERGE_NO_DECISION',
        'probe_mode':False,
        'requested_period':{'start':'2021-04-01T00:00:00+00:00','end_exclusive':'2025-01-01T00:00:00+00:00'},
        'requested_top_level_windows':requested_windows,
        'completed_top_level_windows':completed_windows,
        'source_fetch_complete':True,'holdout_accessed':False,'locked_2026_accessed':False,
        'raw_pages':merged_pages,'shards':shard_summary,
    }
    report={
        'lab_id':'OPTIONS-SPOTPERP-001','version':'V0.1','stage':'SOURCE_AUDIT_ONLY_YEAR_SHARD_MERGE',
        'status':'SHARD_MERGE_NO_DECISION','checks':{'source_fetch_complete':True,'not_probe_mode':True,'protocol_hash_bound':True,'no_holdout_access':True,'no_2026_access':True},
        'audit':{
            'total_trades':total_trades,
            'valid_signal_coverage_days':None,'min_required_valid_days':500,
            'skew_values_computed':False,'forward_returns_computed':False,'pnl_computed':False,
        },
        'detail':'No source verdict at merge stage; global integrity/coverage is recomputed from immutable raw pages by latest canonical gate.',
        'outcome_metrics_computed':False,'holdout_accessed':False,'locked_2026_accessed':False,
    }
    (out/'source_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True))
    (out/'source_audit_report.json').write_text(json.dumps(report,indent=2,sort_keys=True))
    receipt={
        'stage':'YEAR_SHARD_MERGE_ONLY','status':'MERGE_READY_FOR_GLOBAL_SOURCE_GATE',
        'raw_pages':len(merged_pages),'total_trades_reported_across_shards':total_trades,
        'source_manifest_sha256':sha256_file(out/'source_manifest.json'),
        'source_audit_report_sha256':sha256_file(out/'source_audit_report.json'),
        'skew_values_computed':False,'signals_computed':False,'forward_returns_computed':False,'pnl_computed':False,
        'holdout_2025_accessed':False,'year_2026_accessed':False,
    }
    (out/'source_year_shard_merge_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True))
    print('YEAR_SHARD_MERGE_READY_FOR_GLOBAL_SOURCE_GATE')
    print(json.dumps(receipt,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())

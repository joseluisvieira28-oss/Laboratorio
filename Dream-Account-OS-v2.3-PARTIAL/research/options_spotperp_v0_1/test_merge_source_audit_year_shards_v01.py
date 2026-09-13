#!/usr/bin/env python3
from __future__ import annotations

import gzip
import hashlib
import json
import tempfile
from pathlib import Path

import merge_source_audit_year_shards_v01 as m


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def build_shard(root: Path, year: int) -> None:
    root.mkdir(parents=True)
    raw = root / 'raw'; raw.mkdir()
    p = raw / 'response_000001.json.gz'
    # Synthetic source row only; merger does not interpret market values.
    payload = {'result': {'trades': [{'trade_id': f't{year}', 'timestamp': 1}]}}
    with gzip.open(p,'wb') as f:
        f.write(json.dumps(payload).encode())
    start,end=m.EXPECTED_PERIODS[year]
    manifest={
        'lab_id':'OPTIONS-SPOTPERP-001','version':'V0.1','protocol_sha256':m.PROTOCOL_SHA,
        'stage':'SOURCE_AUDIT_ONLY','status':'SOURCE_AUDIT_BLOCKED','probe_mode':False,
        'requested_period':{'start':start,'end_exclusive':end},
        'requested_top_level_windows':1,'completed_top_level_windows':1,
        'source_fetch_complete':True,'holdout_accessed':False,'locked_2026_accessed':False,
        'raw_pages':[{'page':p.name,'sha256':sha(p),'start_ms':year,'end_ms':year,'url':'synthetic','count':1,'bytes_gzip':p.stat().st_size}],
    }
    report={
        'lab_id':'OPTIONS-SPOTPERP-001','version':'V0.1','stage':'SOURCE_AUDIT_ONLY',
        'status':'SOURCE_AUDIT_BLOCKED','checks':{},
        'audit':{'total_trades':1,'valid_signal_coverage_days':0,'min_required_valid_days':500,
                 'skew_values_computed':False,'forward_returns_computed':False,'pnl_computed':False},
        'outcome_metrics_computed':False,'holdout_accessed':False,'locked_2026_accessed':False,
    }
    (root/'source_manifest.json').write_text(json.dumps(manifest))
    (root/'source_audit_report.json').write_text(json.dumps(report))


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        t=Path(td); shards=t/'shards'; out=t/'merged'
        for y in m.YEARS: build_shard(shards/str(y),y)
        import sys
        old=sys.argv
        try:
            sys.argv=['merge_source_audit_year_shards_v01.py','--shards-root',str(shards),'--output',str(out)]
            assert m.main()==0
        finally:
            sys.argv=old
        x=json.loads((out/'source_manifest.json').read_text())
        r=json.loads((out/'source_audit_report.json').read_text())
        q=json.loads((out/'source_year_shard_merge_receipt.json').read_text())
        assert x['source_fetch_complete'] is True and x['probe_mode'] is False
        assert x['holdout_accessed'] is False and x['locked_2026_accessed'] is False
        assert x['requested_period']=={'start':'2021-04-01T00:00:00+00:00','end_exclusive':'2025-01-01T00:00:00+00:00'}
        assert len(x['raw_pages'])==4
        assert {e['source_shard_year'] for e in x['raw_pages']}=={2021,2022,2023,2024}
        assert len({e['page'] for e in x['raw_pages']})==4
        for e in x['raw_pages']:
            p=out/'raw'/e['page']; assert p.exists() and sha(p)==e['sha256']
        assert r['outcome_metrics_computed'] is False
        assert q['status']=='MERGE_READY_FOR_GLOBAL_SOURCE_GATE'
        assert q['holdout_2025_accessed'] is False and q['year_2026_accessed'] is False
        print('YEAR_SHARD_MERGE_SYNTHETIC_TEST_PASS')
        print('4 NON-OVERLAPPING SHARDS / HASHES PRESERVED / NO OUTCOMES / NO 2025 / NO 2026')

if __name__=='__main__':
    main()

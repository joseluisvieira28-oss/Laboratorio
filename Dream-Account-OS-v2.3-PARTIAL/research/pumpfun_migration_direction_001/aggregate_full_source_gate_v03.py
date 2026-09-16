#!/usr/bin/env python3
"""Aggregate PMD-001 full block-first shards into the frozen Source Gate verdict.

Pre-outcome only. Implements FULL_SOURCE_REBUILD_EXECUTION_FREEZE_V02 plus
transport/storage amendments V0.2/V0.3 without adding new promotion criteria.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_ROWS = 1012
MIN_ELIGIBLE = 1000
MIN_DATES = 20


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-root', required=True)
    ap.add_argument('--out-dir', required=True)
    args = ap.parse_args()

    files = sorted(Path(args.input_root).rglob('source_rebuild_summary.jsonl'))
    rows: list[dict] = []
    for p in files:
        rows.extend(json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip())

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    mints = [r.get('mint') for r in rows]
    duplicate_mints = len(mints) - len(set(mints))
    outcomes_closed = all(r.get('outcomes_opened') is False for r in rows)
    timestamp_ok = all(r.get('timestamp_precision_amendment_applied') is True for r in rows)
    retrieval_ts_ok = all(r.get('retrieval_timestamp_evidence_complete') is True for r in rows if r.get('source_complete'))
    transport_ok = all(
        r.get('block_transport') == 'json_rpc_batch_getBlock_json_with_individual_remediation'
        for r in rows
    )

    eligible_rows = [r for r in rows if bool(r.get('feature_source_eligible'))]
    source_complete = sum(bool(r.get('source_complete')) for r in rows)
    eligible = len(eligible_rows)
    eligible_dates = len({str(r.get('t0'))[:10] for r in eligible_rows if r.get('t0')})
    collector_errors = sum(bool(r.get('collector_error')) for r in rows)

    reconciliation_ok = (
        len(files) == 4
        and len(rows) == EXPECTED_ROWS
        and len(set(mints)) == EXPECTED_ROWS
        and duplicate_mints == 0
        and outcomes_closed
        and timestamp_ok
        and transport_ok
    )

    if not reconciliation_ok:
        verdict = 'SOURCE_REBUILD_TECHNICAL_INCOMPLETE'
    elif eligible >= MIN_ELIGIBLE and eligible_dates >= MIN_DATES:
        verdict = 'SOURCE_REBUILD_GATE_PASS'
    else:
        verdict = 'SOURCE_REBUILD_INSUFFICIENT_SAMPLE'

    canon = ''.join(
        json.dumps(r, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'
        for r in sorted(rows, key=lambda x: (str(x.get('t0')), str(x.get('mint'))))
    )
    rows_sha = hashlib.sha256(canon.encode('utf-8')).hexdigest()
    (out / 'pmd_full_source_gate_rows_v03.jsonl').write_text(canon, encoding='utf-8')

    receipt = {
        'lab': 'PMD-001',
        'stage': 'FULL_SOURCE_REBUILD_GATE_V03_BATCH_JSON',
        'economic_outcomes_opened': False,
        'population_expected': EXPECTED_ROWS,
        'population_rows': len(rows),
        'shard_summary_files_found': len(files),
        'unique_mints': len(set(mints)),
        'duplicate_mints': duplicate_mints,
        'source_complete_mints': source_complete,
        'feature_source_eligible_mints': eligible,
        'minimum_viable_mints': MIN_ELIGIBLE,
        'distinct_dates_feature_source_eligible': eligible_dates,
        'minimum_distinct_dates': MIN_DATES,
        'collector_error_rows': collector_errors,
        'timestamp_precision_amendment_applied': timestamp_ok,
        'retrieval_timestamp_evidence_complete_for_source_complete_rows': retrieval_ts_ok,
        'transport_v03_applied': transport_ok,
        'outcome_wall_intact': outcomes_closed,
        'rows_sha256': rows_sha,
        'verdict': verdict,
    }
    (out / 'pmd_full_source_gate_receipt_v03.json').write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if verdict in ('SOURCE_REBUILD_GATE_PASS', 'SOURCE_REBUILD_INSUFFICIENT_SAMPLE') else 2


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
"""Aggregate PMD-001 deterministic signature-ceiling shards.

Pre-outcome only. Emits the sole scientific ceiling verdict after reconciling
all 1,012 frozen rows. Individual shards have no scientific verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_ROWS = 1012
MIN_VIABLE = 1000
EXPECTED_INDICES = set(range(EXPECTED_ROWS))
EXPECTED_MANIFEST_SHA = '56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b'


def canonical_sha(rows: list[dict]) -> tuple[str, str]:
    canon = ''.join(json.dumps(r, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'
                    for r in sorted(rows, key=lambda x: int(x.get('frozen_manifest_index', -1))))
    return canon, hashlib.sha256(canon.encode('utf-8')).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-root', required=True)
    ap.add_argument('--out-dir', required=True)
    args = ap.parse_args()

    root = Path(args.input_root)
    files = sorted(root.rglob('signature_ceiling_details.jsonl'))
    rows: list[dict] = []
    for p in files:
        rows.extend(json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip())

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    indices = [r.get('frozen_manifest_index') for r in rows]
    mints = [r.get('mint') for r in rows]
    valid_indices = [i for i in indices if isinstance(i, int)]
    duplicate_indices = len(valid_indices) - len(set(valid_indices))
    duplicate_mints = len(mints) - len(set(mints))
    index_set_ok = set(valid_indices) == EXPECTED_INDICES
    outcomes_closed = all(r.get('outcomes_opened') is False for r in rows)
    timestamp_ok = all(r.get('timestamp_precision_amendment_applied') is True for r in rows)
    source_complete = sum(bool(r.get('source_complete')) for r in rows)
    incomplete = len(rows) - source_complete
    with_success = [
        r for r in rows
        if bool(r.get('source_complete')) and int(r.get('successful_safe_in_window_signatures') or 0) > 0
    ]
    dates_success = len({str(r.get('t0'))[:10] for r in with_success if r.get('t0')})

    reconciliation_ok = (
        len(files) == 4
        and len(rows) == EXPECTED_ROWS
        and len(set(mints)) == EXPECTED_ROWS
        and duplicate_mints == 0
        and duplicate_indices == 0
        and index_set_ok
        and outcomes_closed
        and timestamp_ok
    )

    if not reconciliation_ok or incomplete > 0:
        verdict = 'SIGNATURE_CEILING_UNRESOLVED'
    elif len(with_success) >= MIN_VIABLE:
        verdict = 'SIGNATURE_CEILING_VIABLE'
    else:
        verdict = 'SIGNATURE_CEILING_INSUFFICIENT'

    canon, rows_sha = canonical_sha(rows)
    (out / 'signature_ceiling_aggregated_rows.jsonl').write_text(canon, encoding='utf-8')
    receipt = {
        'lab': 'PMD-001',
        'stage': 'SIGNATURE_CEILING_AGGREGATE_V01_SHARDED',
        'economic_outcomes_opened': False,
        'manifest_sha256': EXPECTED_MANIFEST_SHA,
        'shard_files_found': len(files),
        'population_expected': EXPECTED_ROWS,
        'population_rows': len(rows),
        'unique_mints': len(set(mints)),
        'duplicate_mints': duplicate_mints,
        'unique_manifest_indices': len(set(valid_indices)),
        'duplicate_manifest_indices': duplicate_indices,
        'full_index_set_reconciled': index_set_ok,
        'source_complete_rows': source_complete,
        'source_incomplete_rows': incomplete,
        'rows_with_successful_safe_in_window_signature': len(with_success),
        'distinct_dates_with_successful_safe_in_window_signature': dates_success,
        'minimum_viable_rows': MIN_VIABLE,
        'timestamp_precision_amendment_applied': timestamp_ok,
        'outcome_wall_intact': outcomes_closed,
        'rows_sha256': rows_sha,
        'verdict': verdict,
    }
    (out / 'signature_ceiling_aggregate_receipt.json').write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if verdict in ('SIGNATURE_CEILING_VIABLE', 'SIGNATURE_CEILING_INSUFFICIENT') else 2


if __name__ == '__main__':
    raise SystemExit(main())

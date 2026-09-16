#!/usr/bin/env python3
"""Aggregate the 20 mandatory PMD-001 Cross-Date V0.4 row shards."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_ROWS = 20
EXPECTED_INDICES = set(range(EXPECTED_ROWS))
ARTIFACT_RE = re.compile(r'PMD-001-crossdate-v04-row-(\d+)$')


def artifact_index(path: Path) -> int | None:
    for parent in path.parents:
        m = ARTIFACT_RE.match(parent.name)
        if m:
            return int(m.group(1))
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--input-root', required=True)
    ap.add_argument('--out-dir', required=True)
    args = ap.parse_args()

    files = sorted(Path(args.input_root).rglob('source_rebuild_summary.jsonl'))
    rows: list[dict] = []
    indices: list[int] = []
    file_index_errors = 0
    for p in files:
        idx = artifact_index(p)
        parts = [json.loads(line) for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
        if idx is None or len(parts) != 1:
            file_index_errors += 1
        for r in parts:
            r = dict(r)
            r['crossdate_manifest_index'] = idx
            rows.append(r)
            if idx is not None:
                indices.append(idx)

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    mints = [r.get('mint') for r in rows]
    dates = {str(r.get('t0'))[:10] for r in rows if r.get('t0')}
    duplicate_mints = len(mints) - len(set(mints))
    duplicate_indices = len(indices) - len(set(indices))
    index_set_ok = set(indices) == EXPECTED_INDICES
    outcomes_closed = all(r.get('outcomes_opened') is False for r in rows)
    timestamp_ok = all(r.get('timestamp_precision_amendment_applied') is True for r in rows)
    transport_ok = all(r.get('block_transport') == 'json_rpc_batch_getBlock_json_with_individual_remediation' for r in rows)
    full_blocks_ok = all(r.get('full_blocks_persisted') is True for r in rows)
    complete = sum(bool(r.get('source_complete')) for r in rows)
    eligible = sum(bool(r.get('feature_source_eligible')) for r in rows)

    reconciliation_ok = (
        len(files) == EXPECTED_ROWS
        and len(rows) == EXPECTED_ROWS
        and len(set(mints)) == EXPECTED_ROWS
        and duplicate_mints == 0
        and len(dates) == EXPECTED_ROWS
        and duplicate_indices == 0
        and index_set_ok
        and file_index_errors == 0
        and outcomes_closed
        and timestamp_ok
        and transport_ok
        and full_blocks_ok
    )

    if not reconciliation_ok:
        verdict = 'BLOCK_FIRST_CROSSDATE_V04_TECHNICAL_INCOMPLETE'
    elif complete == EXPECTED_ROWS and eligible == EXPECTED_ROWS:
        verdict = 'BLOCK_FIRST_CROSSDATE_V04_PASS'
    else:
        verdict = 'BLOCK_FIRST_CROSSDATE_V04_PARTIAL_OR_FAIL'

    canon = ''.join(
        json.dumps(r, sort_keys=True, separators=(',', ':'), ensure_ascii=False) + '\n'
        for r in sorted(rows, key=lambda x: int(x.get('crossdate_manifest_index') if x.get('crossdate_manifest_index') is not None else -1))
    )
    rows_sha = hashlib.sha256(canon.encode('utf-8')).hexdigest()
    (out / 'pmd_crossdate_v04_rows.jsonl').write_text(canon, encoding='utf-8')
    receipt = {
        'lab': 'PMD-001',
        'stage': 'BLOCK_FIRST_CROSSDATE_ACCESS_V04_SHARDED_BATCH_JSON',
        'economic_outcomes_opened': False,
        'probe_rows': len(rows),
        'artifact_files_found': len(files),
        'unique_mints': len(set(mints)),
        'duplicate_mints': duplicate_mints,
        'distinct_dates': len(dates),
        'unique_manifest_indices': len(set(indices)),
        'duplicate_manifest_indices': duplicate_indices,
        'full_index_set_reconciled': index_set_ok,
        'file_index_errors': file_index_errors,
        'source_complete_mints': complete,
        'feature_source_eligible_mints': eligible,
        'timestamp_precision_amendment_applied': timestamp_ok,
        'transport_v03_applied': transport_ok,
        'full_blocks_persisted': full_blocks_ok,
        'outcome_wall_intact': outcomes_closed,
        'rows_sha256': rows_sha,
        'verdict': verdict,
    }
    (out / 'pmd_crossdate_v04_receipt.json').write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8'
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if verdict == 'BLOCK_FIRST_CROSSDATE_V04_PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())

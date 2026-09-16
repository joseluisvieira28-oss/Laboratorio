#!/usr/bin/env python3
"""Build the frozen PMD-001 20-date cross-date source-access probe manifest.

Selection is outcome-blind: earliest (T0,mint) per UTC migration date from the
already-frozen 1,012-candidate source-rebuild manifest. No replacement allowed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_FULL_ROWS = 1012
EXPECTED_DATES = 20
EXPECTED_PROBE_ROWS = 20


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read_jsonl(path: Path) -> list[dict]:
    rows=[]
    with path.open('r',encoding='utf-8') as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--out',default='pmd_crossdate_probe20_manifest_v01.jsonl')
    ap.add_argument('--receipt',default='pmd_crossdate_probe20_manifest_v01_receipt.json')
    args=ap.parse_args()

    src=Path(args.manifest)
    rows=read_jsonl(src)
    if len(rows)!=EXPECTED_FULL_ROWS:
        raise RuntimeError(f'full manifest rows {len(rows)} != {EXPECTED_FULL_ROWS}')
    rows.sort(key=lambda r:(str(r['t0']),r['mint']))

    seen_mints=set()
    per_date={}
    for r in rows:
        mint=r['mint']
        if mint in seen_mints:
            raise RuntimeError(f'duplicate mint: {mint}')
        seen_mints.add(mint)
        date=str(r['t0'])[:10]
        per_date.setdefault(date,r)

    if len(per_date)!=EXPECTED_DATES:
        raise RuntimeError(f'distinct dates {len(per_date)} != {EXPECTED_DATES}')

    selected=[per_date[d] for d in sorted(per_date)]
    if len(selected)!=EXPECTED_PROBE_ROWS:
        raise RuntimeError('cross-date selection did not yield exactly 20 rows')

    out=Path(args.out)
    with out.open('w',encoding='utf-8') as f:
        for i,r in enumerate(selected,1):
            rec={
                'lab':'PMD-001',
                'stage':'BLOCK_FIRST_CROSSDATE_ACCESS_V01',
                'outcomes_opened':False,
                'selection_rule':'earliest_(t0,mint)_per_UTC_migration_date',
                'probe_index':i,
                'migration_date_utc':str(r['t0'])[:10],
                'mint':r['mint'],
                't0':r['t0'],
            }
            f.write(json.dumps(rec,sort_keys=True)+'\n')

    receipt={
        'lab':'PMD-001',
        'stage':'BLOCK_FIRST_CROSSDATE_ACCESS_V01',
        'outcomes_opened':False,
        'source_manifest_sha256':sha256_file(src),
        'source_manifest_rows':len(rows),
        'probe_rows':len(selected),
        'probe_dates':[str(r['t0'])[:10] for r in selected],
        'probe_manifest_sha256':sha256_file(out),
        'selection_rule':'earliest_(t0,mint)_per_UTC_migration_date',
        'replacement_allowed':False,
        'pass':len(selected)==20 and len({str(r['t0'])[:10] for r in selected})==20,
    }
    Path(args.receipt).write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if receipt['pass'] else 2

if __name__=='__main__':
    raise SystemExit(main())

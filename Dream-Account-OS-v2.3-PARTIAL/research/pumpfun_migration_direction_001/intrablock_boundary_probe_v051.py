#!/usr/bin/env python3
"""PMD-001 V0.5.1 exact intrablock migration-boundary probe.

Technical correction only: joins canonical pool identity from the already-frozen
1,012-row manifest onto the unchanged 20-row cross-date probe by mint, then
reuses the V0.5 boundary method. No outcomes are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from source_rebuild_helius_v01 import Rpc, load_manifest
from intrablock_boundary_probe_v05 import PROBE_INDICES, process_row

EXPECTED_FULL_ROWS = 1012
EXPECTED_MANIFEST_SHA = '56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b'
EXPECTED_PROBES = {
    0:'9af7PmWRca2QYmknQehoLH19jG5ss9ajYFpgL8dMpump',
    1:'QHhbroZxDShtSXm9X2RqjpQP9FvpxbSTUWktPMopump',
    5:'7N3RPJC7ZxXyEnVyx8i83dcKb9QjMjV34cH2VKjypump',
    10:'71HtXHfexjKgem92Y5sPLPb6qkmtqWmPUzdKAcU9pump',
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--crossdate-manifest',required=True)
    ap.add_argument('--full-manifest',required=True)
    ap.add_argument('--out-dir',default='pmd_intrablock_boundary_probe_v051')
    ap.add_argument('--rpc-url',default='https://api.mainnet-beta.solana.com')
    ap.add_argument('--source-name',default='solana_public_rpc_intrablock_boundary_v051')
    ap.add_argument('--block-batch-size',type=int,default=4)
    args=ap.parse_args()

    cross_path=Path(args.crossdate_manifest)
    full_path=Path(args.full_manifest)
    if sha256_file(full_path)!=EXPECTED_MANIFEST_SHA:
        raise RuntimeError('frozen 1,012 manifest SHA mismatch')

    cross=load_manifest(cross_path)
    full=load_manifest(full_path)
    if len(cross)!=20:
        raise RuntimeError(f'expected 20 cross-date rows, found {len(cross)}')
    if len(full)!=EXPECTED_FULL_ROWS:
        raise RuntimeError(f'expected {EXPECTED_FULL_ROWS} full rows, found {len(full)}')

    by_mint={r['mint']:r for r in full}
    if len(by_mint)!=EXPECTED_FULL_ROWS:
        raise RuntimeError('duplicate mint in frozen full manifest')

    enriched=[]
    for i,r in enumerate(cross):
        mint=r['mint']
        src=by_mint.get(mint)
        if src is None:
            raise RuntimeError(f'cross-date mint absent from full manifest: {mint}')
        if str(src['t0']) != str(r['t0']):
            raise RuntimeError(f'T0 mismatch for {mint}')
        pool=src.get('pool_address')
        if not pool:
            raise RuntimeError(f'canonical pool missing in full manifest for {mint}')
        enriched.append({**r,'pool_address':pool})

    for i,mint in EXPECTED_PROBES.items():
        if enriched[i]['mint']!=mint:
            raise RuntimeError(f'frozen probe mismatch at index {i}')

    root=Path(args.out_dir); root.mkdir(parents=True,exist_ok=True)
    rpc=Rpc(args.rpc_url,args.source_name)
    summaries=[]
    for i in PROBE_INDICES:
        rec=process_row(rpc,enriched[i],i,root,args.block_batch_size)
        rec['pool_metadata_join']='frozen_1012_manifest_by_exact_mint'
        rec['full_manifest_sha256']=EXPECTED_MANIFEST_SHA
        summaries.append(rec)
        print(json.dumps(rec,sort_keys=True,ensure_ascii=False),flush=True)

    summary_path=root/'intrablock_boundary_probe_v051_summary.jsonl'
    summary_path.write_text(''.join(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n' for r in summaries),encoding='utf-8')
    feasible=all(bool(r.get('method_feasible_for_row')) for r in summaries)
    recovered=sum(
        1 for r in summaries
        if r['probe_index'] in (1,5)
        and r.get('method_feasible_for_row')
        and int(r.get('successful_pump_buy_sell_transactions_before_boundary') or 0)>0
    )
    receipt={
        'lab':'PMD-001','stage':'INTRABLOCK_BOUNDARY_FEASIBILITY_V051',
        'economic_outcomes_opened':False,'outcomes_opened':False,
        'full_manifest_sha256':EXPECTED_MANIFEST_SHA,
        'probe_indices':list(PROBE_INDICES),'probe_rows':len(summaries),
        'rows_method_feasible':sum(bool(r.get('method_feasible_for_row')) for r in summaries),
        'failed_precision_rows_recovered_with_preboundary_same_second_trades':recovered,
        'summary_sha256':hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        'verdict':'INTRABLOCK_BOUNDARY_METHOD_FEASIBLE' if feasible else 'INTRABLOCK_BOUNDARY_METHOD_UNRESOLVED',
        'full_population_v05_authorized':False,
    }
    (root/'intrablock_boundary_probe_v051_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if feasible else 2

if __name__=='__main__':
    raise SystemExit(main())

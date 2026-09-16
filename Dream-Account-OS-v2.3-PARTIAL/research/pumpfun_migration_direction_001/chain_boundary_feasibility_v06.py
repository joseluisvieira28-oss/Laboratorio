#!/usr/bin/env python3
"""PMD-001 V0.6 chain-exact migration boundary feasibility.

Outcome-blind. Locates the unique successful Pump migrate transaction that
actually creates the frozen canonical PumpSwap pool, rather than later
idempotent `Bonding curve already migrated` calls.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from source_rebuild_helius_v01 import Rpc, bonding_curve_pda, load_manifest, parse_ts, sha256_json
from source_rebuild_block_first_v03 import get_blocks_batched
from intrablock_boundary_probe_v05 import (
    PUMP_PROGRAM, PUMP_AMM, MIGRATE_DISC, pump_ix_kind, tx_signature,
    account_keys, outer_instructions, resolve_program, resolve_ix_accounts, ix_data,
)

BOUNDARY_LOOKBACK_SECONDS = 300
SIG_LIMIT = 1000
PROBE_INDICES = (0, 1, 5, 10)
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


def paginate_window(rpc: Rpc, pda: str, lower_second: float) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_rows: list[dict[str, Any]] = []
    before = None
    pages = 0
    crossed = False
    exhausted = False
    null_time = False
    while True:
        page = rpc.get_signatures(pda, before=before)
        pages += 1
        if not page:
            exhausted = True
            break
        all_rows.extend(page)
        times = [x.get('blockTime') for x in page]
        if any(x is None for x in times):
            null_time = True
        vals = [float(x) for x in times if x is not None]
        if vals and min(vals) < lower_second:
            crossed = True
            break
        if len(page) < SIG_LIMIT:
            exhausted = True
            break
        before = page[-1].get('signature')
        if not before:
            break
        if pages > 100:
            raise RuntimeError('pagination safety stop')

    by_sig: dict[str, dict[str, Any]] = {}
    conflicts = 0
    for r in all_rows:
        sig = r.get('signature')
        if not sig:
            continue
        if sig in by_sig and by_sig[sig] != r:
            conflicts += 1
        else:
            by_sig[sig] = r
    return list(by_sig.values()), {
        'signature_pages': pages,
        'crossed_lower_bound': crossed,
        'history_exhausted': exhausted,
        'null_block_time_seen': null_time,
        'signature_conflicts': conflicts,
    }


def exact_migrate_outer(item: dict[str, Any], mint: str, pda: str, pool: str) -> bool:
    if (item.get('meta') or {}).get('err') is not None:
        return False
    keys = account_keys(item)
    for ix in outer_instructions(item):
        if resolve_program(ix, keys) != PUMP_PROGRAM:
            continue
        if not ix_data(ix).startswith(MIGRATE_DISC):
            continue
        accounts = set(resolve_ix_accounts(ix, keys))
        if mint in accounts and pda in accounts and pool in accounts:
            return True
    return False


def is_actual_pool_creation_migration(item: dict[str, Any], mint: str, pda: str, pool: str) -> bool:
    if not exact_migrate_outer(item, mint, pda, pool):
        return False
    logs = (item.get('meta') or {}).get('logMessages') or []
    has_create_pool = any('Program log: Instruction: CreatePool' in str(x) for x in logs)
    has_pump_amm = any(f'Program {PUMP_AMM} invoke' in str(x) for x in logs)
    already_migrated = any('Bonding curve already migrated' in str(x) for x in logs)
    return bool(has_create_pool and has_pump_amm and not already_migrated)


def block_time_order(block_time: int, slot: int, tx_index: int) -> tuple[int, int, int]:
    return int(block_time), int(slot), int(tx_index)


def process_row(rpc: Rpc, row: dict[str, Any], probe_index: int, root: Path, batch_size: int) -> dict[str, Any]:
    mint = row['mint']
    pool = row['pool_address']
    pda = bonding_curve_pda(mint)
    corpus_t0 = parse_ts(row['t0'])
    corpus_second = int(math.floor(corpus_t0))
    search_lo = corpus_t0 - BOUNDARY_LOOKBACK_SECONDS

    sigs, paging = paginate_window(rpc, pda, search_lo)
    search_meta = [
        x for x in sigs
        if x.get('blockTime') is not None
        and search_lo <= float(x['blockTime']) <= float(corpus_second)
    ]
    slots = sorted({int(x['slot']) for x in search_meta if x.get('slot') is not None})
    fetched = get_blocks_batched(rpc, slots, batch_size) if slots else {}

    evidence_dir = root / 'blocks' / f'idx_{probe_index}_{mint}'
    evidence_dir.mkdir(parents=True, exist_ok=True)
    positions: dict[str, dict[str, Any]] = {}
    boundaries: list[dict[str, Any]] = []
    migrate_calls: list[dict[str, Any]] = []
    block_errors = 0
    block_evidence: list[dict[str, Any]] = []

    for slot in slots:
        rec = fetched.get(slot) or {}
        block = rec.get('block')
        if not isinstance(block, dict) or block.get('_rpc_error'):
            block_errors += 1
            continue
        btime = block.get('blockTime')
        bsha = sha256_json(block)
        block_evidence.append({
            'slot': slot,
            'block_time': btime,
            'retrieved_at_utc': rec.get('retrieved_at_utc'),
            'canonical_block_sha256': bsha,
            'transport': rec.get('transport'),
            'remediated': bool(rec.get('remediated')),
        })
        with gzip.open(evidence_dir / f'slot_{slot}.json.gz', 'wt', encoding='utf-8') as gf:
            json.dump({
                'lab':'PMD-001','stage':'CHAIN_EXACT_BOUNDARY_FEASIBILITY_V06','outcomes_opened':False,
                'probe_index':probe_index,'mint':mint,'slot':slot,
                'retrieved_at_utc':rec.get('retrieved_at_utc'),
                'canonical_block_sha256':bsha,'block':block,
            }, gf, sort_keys=True, ensure_ascii=False)

        for tx_index, item in enumerate(block.get('transactions') or []):
            if not isinstance(item, dict):
                continue
            sig = tx_signature(item)
            if sig:
                positions[sig] = {
                    'block_time': btime,
                    'slot': slot,
                    'transaction_index': tx_index,
                    'success': (item.get('meta') or {}).get('err') is None,
                    'transaction_sha256': sha256_json(item),
                    'item': item,
                }
            if exact_migrate_outer(item, mint, pda, pool):
                logs = (item.get('meta') or {}).get('logMessages') or []
                mc = {
                    'signature': sig,
                    'block_time': btime,
                    'slot': slot,
                    'transaction_index': tx_index,
                    'transaction_sha256': sha256_json(item),
                    'creates_pool': is_actual_pool_creation_migration(item, mint, pda, pool),
                    'already_migrated_log': any('Bonding curve already migrated' in str(x) for x in logs),
                    'create_pool_log': any('Program log: Instruction: CreatePool' in str(x) for x in logs),
                }
                migrate_calls.append(mc)
                if mc['creates_pool']:
                    boundaries.append(mc)

    unique_boundary_keys = {(x['slot'],x['transaction_index'],x['signature']) for x in boundaries}
    boundary = boundaries[0] if len(unique_boundary_keys) == 1 else None
    boundary_order = block_time_order(boundary['block_time'], boundary['slot'], boundary['transaction_index']) if boundary else None

    missing_positions: list[str] = []
    before: list[dict[str, Any]] = []
    at_after: list[dict[str, Any]] = []
    pump_trade_txs_before = 0
    trade_kinds = {'buy':0,'sell':0}

    for meta in search_meta:
        sig = str(meta.get('signature'))
        pos = positions.get(sig)
        if not pos:
            missing_positions.append(sig)
            continue
        order = block_time_order(pos['block_time'], pos['slot'], pos['transaction_index'])
        compact = {
            'signature': sig,
            'block_time': pos['block_time'],
            'slot': pos['slot'],
            'transaction_index': pos['transaction_index'],
            'success': pos['success'],
            'transaction_sha256': pos['transaction_sha256'],
        }
        if boundary_order is not None and order < boundary_order:
            before.append(compact)
            _m, kinds = pump_ix_kind(pos['item'], mint, pda, pool)
            if pos['success'] and kinds:
                pump_trade_txs_before += 1
                for k in set(kinds):
                    trade_kinds[k] = trade_kinds.get(k,0) + 1
        else:
            at_after.append(compact)

    paging_complete = bool(
        paging['signature_conflicts'] == 0
        and not paging['null_block_time_seen']
        and (paging['crossed_lower_bound'] or paging['history_exhausted'])
    )
    positions_complete = len(missing_positions) == 0
    unique_boundary = len(unique_boundary_keys) == 1
    boundary_not_after_corpus = bool(boundary and int(boundary['block_time']) <= corpus_second)
    boundary_within_frozen_horizon = bool(boundary and float(boundary['block_time']) >= search_lo)
    feasible = bool(
        unique_boundary and boundary_not_after_corpus and boundary_within_frozen_horizon
        and paging_complete and block_errors == 0 and positions_complete
    )

    raw = {
        'lab':'PMD-001','stage':'CHAIN_EXACT_BOUNDARY_FEASIBILITY_V06','outcomes_opened':False,
        'probe_index':probe_index,'mint':mint,'pool_address':pool,'bonding_curve_pda':pda,
        'corpus_t0':row['t0'],'corpus_t0_unix':corpus_t0,'corpus_t0_second':corpus_second,
        'search_lower_unix':search_lo,'paging':paging,
        'search_signature_meta':search_meta,'migrate_calls':migrate_calls,
        'qualifying_pool_creation_boundaries':boundaries,
        'block_evidence':block_evidence,'missing_signature_positions':missing_positions,
        'strictly_before_chain_boundary':before,'at_or_after_chain_boundary':at_after,
    }
    raw_path = root / f'probe_idx_{probe_index}_{mint}.json'
    raw_path.write_text(json.dumps(raw,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

    return {
        'lab':'PMD-001','stage':'CHAIN_EXACT_BOUNDARY_FEASIBILITY_V06','outcomes_opened':False,
        'probe_index':probe_index,'mint':mint,'pool_address':pool,'bonding_curve_pda':pda,
        'corpus_t0':row['t0'],'search_signatures':len(search_meta),'unique_slots':len(slots),
        'all_exact_migrate_calls':len(migrate_calls),
        'qualifying_pool_creation_boundaries':len(unique_boundary_keys),
        'boundary_found_unique':unique_boundary,
        'boundary_signature':boundary.get('signature') if boundary else None,
        'boundary_block_time':boundary.get('block_time') if boundary else None,
        'boundary_slot':boundary.get('slot') if boundary else None,
        'boundary_transaction_index':boundary.get('transaction_index') if boundary else None,
        'corpus_minus_boundary_seconds':(corpus_t0-float(boundary['block_time'])) if boundary else None,
        'transactions_before_boundary':len(before),
        'transactions_at_or_after_boundary':len(at_after),
        'successful_target_pump_buy_sell_transactions_before_boundary':pump_trade_txs_before,
        'pump_trade_kinds_before_boundary':trade_kinds,
        'paging_complete':paging_complete,'block_errors':block_errors,
        'missing_signature_positions':len(missing_positions),
        'method_feasible_for_row':feasible,
        'raw_evidence_file':str(raw_path),
        'raw_evidence_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }


def main() -> int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--crossdate-manifest',required=True)
    ap.add_argument('--full-manifest',required=True)
    ap.add_argument('--out-dir',default='pmd_chain_boundary_feasibility_v06')
    ap.add_argument('--rpc-url',default='https://api.mainnet-beta.solana.com')
    ap.add_argument('--source-name',default='solana_public_rpc_chain_boundary_v06')
    ap.add_argument('--block-batch-size',type=int,default=4)
    args=ap.parse_args()

    cross=load_manifest(Path(args.crossdate_manifest))
    full_path=Path(args.full_manifest)
    if sha256_file(full_path)!=EXPECTED_MANIFEST_SHA:
        raise RuntimeError('frozen full manifest SHA mismatch')
    full=load_manifest(full_path)
    if len(cross)!=20 or len(full)!=EXPECTED_FULL_ROWS:
        raise RuntimeError('frozen manifest row-count mismatch')
    by_mint={r['mint']:r for r in full}
    if len(by_mint)!=EXPECTED_FULL_ROWS:
        raise RuntimeError('duplicate mint in full manifest')

    enriched=[]
    for r in cross:
        src=by_mint.get(r['mint'])
        if not src or str(src['t0'])!=str(r['t0']) or not src.get('pool_address'):
            raise RuntimeError(f'frozen metadata join failed for {r["mint"]}')
        enriched.append({**r,'pool_address':src['pool_address']})

    for i,m in EXPECTED_PROBES.items():
        if enriched[i]['mint']!=m:
            raise RuntimeError(f'frozen probe mismatch at {i}')

    root=Path(args.out_dir); root.mkdir(parents=True,exist_ok=True)
    rpc=Rpc(args.rpc_url,args.source_name)
    summaries=[]
    for i in PROBE_INDICES:
        rec=process_row(rpc,enriched[i],i,root,args.block_batch_size)
        summaries.append(rec)
        print(json.dumps(rec,sort_keys=True,ensure_ascii=False),flush=True)

    summary_path=root/'chain_boundary_feasibility_v06_summary.jsonl'
    summary_path.write_text(''.join(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n' for r in summaries),encoding='utf-8')
    feasible=all(bool(r.get('method_feasible_for_row')) for r in summaries)
    receipt={
        'lab':'PMD-001','stage':'CHAIN_EXACT_BOUNDARY_FEASIBILITY_V06',
        'economic_outcomes_opened':False,'outcomes_opened':False,
        'probe_indices':list(PROBE_INDICES),'probe_rows':len(summaries),
        'rows_method_feasible':sum(bool(r.get('method_feasible_for_row')) for r in summaries),
        'rows_with_unique_pool_creation_boundary':sum(bool(r.get('boundary_found_unique')) for r in summaries),
        'failed_v04_rows_with_preboundary_target_trades':sum(
            1 for r in summaries if r['probe_index'] in (1,5)
            and r.get('method_feasible_for_row')
            and int(r.get('successful_target_pump_buy_sell_transactions_before_boundary') or 0)>0
        ),
        'summary_sha256':hashlib.sha256(summary_path.read_bytes()).hexdigest(),
        'verdict':'CHAIN_EXACT_BOUNDARY_METHOD_FEASIBLE' if feasible else 'CHAIN_EXACT_BOUNDARY_METHOD_UNRESOLVED',
        'crossdate_v06_authorized':bool(feasible),
        'full_population_v06_authorized':False,
    }
    (root/'chain_boundary_feasibility_v06_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if feasible else 2

if __name__=='__main__':
    raise SystemExit(main())

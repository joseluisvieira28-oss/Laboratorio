#!/usr/bin/env python3
"""PMD-001 chain-exact source rebuild collector V0.6.

Outcome-blind. Replaces corpus-time-only cutoff with the unique successful Pump
migrate transaction that actually creates the frozen canonical PumpSwap pool.
The predictive source window remains exactly 300 seconds and is re-anchored to
that causal on-chain boundary.
"""
from __future__ import annotations

import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path
from typing import Any

from source_rebuild_helius_v01 import (
    Rpc, bonding_curve_pda, load_manifest, parse_ts, sha256_json, tx_has_target,
)
from source_rebuild_block_first_v03 import get_blocks_batched, find_matches
from chain_boundary_feasibility_v06 import (
    paginate_window, is_actual_pool_creation_migration, exact_migrate_outer,
    block_time_order, BOUNDARY_LOOKBACK_SECONDS, EXPECTED_MANIFEST_SHA,
)
from intrablock_boundary_probe_v05 import tx_signature

WINDOW_SECONDS = 300
RETRIEVAL_ENVELOPE_SECONDS = 600
EXPECTED_FULL_ROWS = 1012


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def join_pool_metadata(rows: list[dict[str, Any]], full_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_mint = {r['mint']: r for r in full_rows}
    if len(by_mint) != len(full_rows):
        raise RuntimeError('duplicate mint in full manifest')
    out = []
    for r in rows:
        src = by_mint.get(r['mint'])
        if src is None:
            raise RuntimeError(f'mint absent from frozen full manifest: {r["mint"]}')
        if str(src['t0']) != str(r['t0']):
            raise RuntimeError(f'T0 mismatch for {r["mint"]}')
        pool = r.get('pool_address') or src.get('pool_address')
        if not pool:
            raise RuntimeError(f'pool_address missing for {r["mint"]}')
        out.append({**r, 'pool_address': pool})
    return out


def persist_block(
    *, root: Path, mint: str, slot: int, rec: dict[str, Any], store_full_blocks: bool,
    ledger_handle: Any,
) -> None:
    block = rec.get('block')
    retrieved_at = rec.get('retrieved_at_utc') or utc_now()
    transport = rec.get('transport') or 'unknown'
    remediated = bool(rec.get('remediated'))
    block_sha = sha256_json(block)
    ledger_handle.write(json.dumps({
        'lab':'PMD-001','stage':'CHAIN_EXACT_SOURCE_REBUILD_V06','outcomes_opened':False,
        'mint':mint,'slot':slot,
        'block_time':block.get('blockTime') if isinstance(block,dict) else None,
        'retrieved_at_utc':retrieved_at,'transport':transport,
        'remediated_individually':remediated,'canonical_block_sha256':block_sha,
        'block_error':block.get('_rpc_error') if isinstance(block,dict) else 'nonobject_block',
        'full_block_persisted':bool(store_full_blocks),
    },sort_keys=True,ensure_ascii=False)+'\n')
    ledger_handle.flush()
    if store_full_blocks:
        d = root / 'blocks' / mint
        d.mkdir(parents=True,exist_ok=True)
        with gzip.open(d/f'slot_{slot}.json.gz','wt',encoding='utf-8') as gf:
            json.dump({
                'lab':'PMD-001','stage':'CHAIN_EXACT_SOURCE_REBUILD_V06','outcomes_opened':False,
                'mint':mint,'slot':slot,'retrieved_at_utc':retrieved_at,
                'transport':transport,'canonical_block_sha256':block_sha,'block':block,
            },gf,sort_keys=True,ensure_ascii=False)


def scan_boundaries(blocks: dict[int, dict[str, Any]], mint: str, pda: str, pool: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    actual: list[dict[str, Any]] = []
    all_calls: list[dict[str, Any]] = []
    for slot in sorted(blocks):
        block = (blocks[slot] or {}).get('block')
        if not isinstance(block,dict) or block.get('_rpc_error'):
            continue
        btime = block.get('blockTime')
        for tx_index,item in enumerate(block.get('transactions') or []):
            if not isinstance(item,dict) or not exact_migrate_outer(item,mint,pda,pool):
                continue
            sig = tx_signature(item)
            logs = (item.get('meta') or {}).get('logMessages') or []
            rec = {
                'signature':sig,'block_time':btime,'slot':slot,'transaction_index':tx_index,
                'transaction_sha256':sha256_json(item),
                'creates_pool':is_actual_pool_creation_migration(item,mint,pda,pool),
                'already_migrated_log':any('Bonding curve already migrated' in str(x) for x in logs),
                'create_pool_log':any('Program log: Instruction: CreatePool' in str(x) for x in logs),
            }
            all_calls.append(rec)
            if rec['creates_pool']:
                actual.append(rec)
    return actual, all_calls


def map_positions(blocks: dict[int, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    pos: dict[str, dict[str, Any]] = {}
    for slot in sorted(blocks):
        block = (blocks[slot] or {}).get('block')
        if not isinstance(block,dict) or block.get('_rpc_error'):
            continue
        btime = block.get('blockTime')
        for tx_index,item in enumerate(block.get('transactions') or []):
            if not isinstance(item,dict):
                continue
            sig=tx_signature(item)
            if sig:
                pos[sig]={
                    'block_time':btime,'slot':slot,'transaction_index':tx_index,
                    'success':(item.get('meta') or {}).get('err') is None,
                    'transaction_sha256':sha256_json(item),'item':item,
                }
    return pos


def collect_one(rpc: Rpc, row: dict[str, Any], root: Path, store_full_blocks: bool, block_batch_size: int) -> dict[str, Any]:
    mint=row['mint']; pool=row['pool_address']; pda=bonding_curve_pda(mint)
    corpus_t0=parse_ts(row['t0']); corpus_second=int(math.floor(corpus_t0))
    retrieval_lo=corpus_t0-RETRIEVAL_ENVELOPE_SECONDS
    boundary_search_lo=corpus_t0-BOUNDARY_LOOKBACK_SECONDS

    sigs,paging=paginate_window(rpc,pda,retrieval_lo)
    by_sig={x['signature']:x for x in sigs if x.get('signature')}
    boundary_meta=[x for x in by_sig.values() if x.get('blockTime') is not None and boundary_search_lo<=float(x['blockTime'])<=corpus_second]
    boundary_slots=sorted({int(x['slot']) for x in boundary_meta if x.get('slot') is not None})
    boundary_fetched=get_blocks_batched(rpc,boundary_slots,block_batch_size) if boundary_slots else {}

    root.mkdir(parents=True,exist_ok=True)
    ledger_path=root/'block_hash_ledger.jsonl'
    persisted_slots:set[int]=set()
    with ledger_path.open('a',encoding='utf-8') as ledger:
        for slot in boundary_slots:
            rec=boundary_fetched.get(slot) or {'block':{'_rpc_error':'missing_boundary_fetch_result'},'retrieved_at_utc':utc_now(),'transport':'missing','remediated':False}
            persist_block(root=root,mint=mint,slot=slot,rec=rec,store_full_blocks=store_full_blocks,ledger_handle=ledger)
            persisted_slots.add(slot)

        boundary_block_errors=sum(
            1 for slot in boundary_slots
            if not isinstance((boundary_fetched.get(slot) or {}).get('block'),dict)
            or ((boundary_fetched.get(slot) or {}).get('block') or {}).get('_rpc_error')
        )
        boundaries,migrate_calls=scan_boundaries(boundary_fetched,mint,pda,pool)
        unique_keys={(x['slot'],x['transaction_index'],x['signature']) for x in boundaries}
        boundary=boundaries[0] if len(unique_keys)==1 else None

        if boundary:
            btime=float(boundary['block_time']); feature_lo=btime-WINDOW_SECONDS
            feature_meta=[x for x in by_sig.values() if x.get('blockTime') is not None and feature_lo<=float(x['blockTime'])<=btime]
            feature_slots=sorted({int(x['slot']) for x in feature_meta if x.get('slot') is not None})
            missing_slots=[s for s in feature_slots if s not in boundary_fetched]
            extra=get_blocks_batched(rpc,missing_slots,block_batch_size) if missing_slots else {}
            all_blocks=dict(boundary_fetched); all_blocks.update(extra)
            for slot in missing_slots:
                rec=extra.get(slot) or {'block':{'_rpc_error':'missing_feature_fetch_result'},'retrieved_at_utc':utc_now(),'transport':'missing','remediated':False}
                persist_block(root=root,mint=mint,slot=slot,rec=rec,store_full_blocks=store_full_blocks,ledger_handle=ledger)
                persisted_slots.add(slot)
        else:
            feature_lo=None; feature_meta=[]; feature_slots=[]; all_blocks=dict(boundary_fetched)

    feature_block_errors=sum(
        1 for slot in feature_slots
        if not isinstance((all_blocks.get(slot) or {}).get('block'),dict)
        or ((all_blocks.get(slot) or {}).get('block') or {}).get('_rpc_error')
    )
    positions=map_positions(all_blocks)
    boundary_order=block_time_order(boundary['block_time'],boundary['slot'],boundary['transaction_index']) if boundary else None

    pre_meta=[]; excluded_at_after=[]; missing_positions=[]
    target=successful=successful_target=0
    raw_dir=root/'raw'; raw_dir.mkdir(parents=True,exist_ok=True)
    raw_path=raw_dir/f'{mint}.jsonl'
    with raw_path.open('w',encoding='utf-8') as f:
        for meta in sorted(feature_meta,key=lambda x:(int(x.get('blockTime') or -1),int(x.get('slot') or -1),str(x.get('signature') or ''))):
            sig=str(meta.get('signature')); pos=positions.get(sig)
            if not pos:
                missing_positions.append(sig); continue
            order=block_time_order(pos['block_time'],pos['slot'],pos['transaction_index'])
            if boundary_order is None or order>=boundary_order:
                excluded_at_after.append(sig); continue
            pre_meta.append(meta)
            tx=pos['item']; is_success=meta.get('err') is None and pos['success']
            is_target=tx_has_target(tx,mint,pda)
            if is_success: successful+=1
            if is_target: target+=1
            if is_success and is_target: successful_target+=1
            f.write(json.dumps({
                'lab':'PMD-001','stage':'CHAIN_EXACT_SOURCE_REBUILD_V06','outcomes_opened':False,
                'mint':mint,'corpus_t0':row['t0'],'chain_boundary':boundary,
                'feature_window_lower_unix':feature_lo,'bonding_curve_pda':pda,
                'signature_meta':meta,'ledger_order':{
                    'block_time':pos['block_time'],'slot':pos['slot'],'transaction_index':pos['transaction_index']},
                'transaction':tx,'transaction_sha256':pos['transaction_sha256'],
                'target_program_mint_pda_match':is_target,
            },sort_keys=True,ensure_ascii=False)+'\n')

    paging_complete=bool(
        paging['signature_conflicts']==0 and not paging['null_block_time_seen']
        and (paging['crossed_lower_bound'] or paging['history_exhausted'])
    )
    boundary_unique=len(unique_keys)==1
    boundary_not_after=bool(boundary and float(boundary['block_time'])<=corpus_second)
    boundary_within_search=bool(boundary and float(boundary['block_time'])>=boundary_search_lo)
    feature_positions_complete=len(missing_positions)==0
    source_complete=bool(
        paging_complete and boundary_unique and boundary_not_after and boundary_within_search
        and boundary_block_errors==0 and feature_block_errors==0 and feature_positions_complete
    )
    eligible=bool(source_complete and successful_target>0)

    return {
        'lab':'PMD-001','stage':'CHAIN_EXACT_SOURCE_REBUILD_V06','outcomes_opened':False,
        'mint':mint,'t0':row['t0'],'pool_address':pool,'bonding_curve_pda':pda,
        'corpus_t0_unix':corpus_t0,'corpus_t0_second':corpus_second,
        'chain_boundary_signature':boundary.get('signature') if boundary else None,
        'chain_boundary_block_time':boundary.get('block_time') if boundary else None,
        'chain_boundary_slot':boundary.get('slot') if boundary else None,
        'chain_boundary_transaction_index':boundary.get('transaction_index') if boundary else None,
        'corpus_minus_chain_boundary_seconds':(corpus_t0-float(boundary['block_time'])) if boundary else None,
        'all_exact_migrate_calls_in_search':len(migrate_calls),
        'qualifying_pool_creation_boundaries':len(unique_keys),
        'feature_window_lower_unix':feature_lo,
        'pre_boundary_signatures':len(pre_meta),'at_or_after_boundary_signatures_excluded':len(excluded_at_after),
        'successful_pre_boundary_signatures':successful,'target_pre_boundary_transactions':target,
        'successful_target_pre_boundary_transactions':successful_target,
        'signature_pages':paging['signature_pages'],'signature_conflicts':paging['signature_conflicts'],
        'null_block_time_seen':paging['null_block_time_seen'],'boundary_search_slots':len(boundary_slots),
        'feature_slots':len(feature_slots),'boundary_block_errors':boundary_block_errors,
        'feature_block_errors':feature_block_errors,'missing_signature_positions':len(missing_positions),
        'retrieval_envelope_seconds':RETRIEVAL_ENVELOPE_SECONDS,'feature_window_seconds':WINDOW_SECONDS,
        'block_transport':'json_rpc_batch_getBlock_json_with_individual_remediation',
        'full_blocks_persisted':bool(store_full_blocks),
        'source_complete':source_complete,'feature_source_eligible':eligible,
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--full-manifest',required=True)
    ap.add_argument('--out-dir',required=True)
    ap.add_argument('--rpc-url',default='https://api.mainnet-beta.solana.com')
    ap.add_argument('--source-name',default='solana_public_rpc_chain_exact_v06')
    ap.add_argument('--start',type=int,default=0)
    ap.add_argument('--limit',type=int,default=None)
    ap.add_argument('--block-batch-size',type=int,default=4)
    ap.add_argument('--store-full-blocks',action='store_true')
    args=ap.parse_args()

    full_path=Path(args.full_manifest)
    if sha256_file(full_path)!=EXPECTED_MANIFEST_SHA:
        raise RuntimeError('frozen full manifest SHA mismatch')
    full=load_manifest(full_path)
    if len(full)!=EXPECTED_FULL_ROWS:
        raise RuntimeError('frozen full manifest row-count mismatch')
    rows=load_manifest(Path(args.manifest))
    rows=join_pool_metadata(rows,full)
    end=len(rows) if args.limit is None else min(len(rows),args.start+args.limit)
    selected=rows[args.start:end]
    if not selected:
        raise RuntimeError('empty selected slice')

    root=Path(args.out_dir); root.mkdir(parents=True,exist_ok=True)
    rpc=Rpc(args.rpc_url,args.source_name)
    summary_path=root/'source_rebuild_summary.jsonl'
    summaries=[]
    with summary_path.open('w',encoding='utf-8') as sf:
        for local_i,row in enumerate(selected):
            rec=collect_one(rpc,row,root,args.store_full_blocks,args.block_batch_size)
            rec['selected_manifest_index']=args.start+local_i
            rec['source_name']=args.source_name
            summaries.append(rec)
            sf.write(json.dumps(rec,sort_keys=True,ensure_ascii=False)+'\n'); sf.flush()
            print(json.dumps({
                'index':rec['selected_manifest_index'],'mint':rec['mint'],
                'boundary':rec['chain_boundary_signature'],'source_complete':rec['source_complete'],
                'feature_source_eligible':rec['feature_source_eligible'],
                'successful_target_pre_boundary_transactions':rec['successful_target_pre_boundary_transactions'],
            },sort_keys=True),flush=True)

    print(json.dumps({
        'lab':'PMD-001','stage':'CHAIN_EXACT_SOURCE_REBUILD_V06','outcomes_opened':False,
        'rows_attempted':len(summaries),'source_complete':sum(bool(x['source_complete']) for x in summaries),
        'feature_source_eligible':sum(bool(x['feature_source_eligible']) for x in summaries),
        'rpc_request_counter':rpc.counter,'summary_sha256':sha256_file(summary_path),
    },indent=2,sort_keys=True))
    return 0

if __name__=='__main__':
    raise SystemExit(main())

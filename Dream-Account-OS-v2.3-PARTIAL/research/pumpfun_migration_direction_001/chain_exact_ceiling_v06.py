#!/usr/bin/env python3
"""PMD-001 chain-exact signature/boundary ceiling V0.6.

Outcome-blind and feature-blind. For each frozen migration it resolves the
actual successful Pump migrate -> PumpSwap CreatePool boundary using transaction
bodies, then uses one finalized boundary block to recover exact within-second
ordering. It counts only whether any successful bonding-curve signature exists
strictly inside the unchanged 300-second pre-boundary window.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
from pathlib import Path
from typing import Any

from source_rebuild_helius_v01 import Rpc, bonding_curve_pda, load_manifest, parse_ts, body_missing
from source_rebuild_block_first_v03 import get_blocks_batched
from chain_boundary_feasibility_v06 import (
    paginate_window, is_actual_pool_creation_migration, block_time_order,
    BOUNDARY_LOOKBACK_SECONDS, EXPECTED_MANIFEST_SHA,
)
from intrablock_boundary_probe_v05 import tx_signature

EXPECTED_ROWS=1012
WINDOW_SECONDS=300
RETRIEVAL_ENVELOPE_SECONDS=600
MIN_VIABLE=1000


def sha256_file(path:Path)->str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def boundary_tx_index(block:Any, signature:str, mint:str, pda:str, pool:str)->tuple[int|None,int]:
    if not isinstance(block,dict) or block.get('_rpc_error'):
        return None,0
    hits=[]
    for i,item in enumerate(block.get('transactions') or []):
        if not isinstance(item,dict): continue
        sig=tx_signature(item)
        if sig==signature:
            hits.append((i,item))
    if len(hits)!=1: return None,len(hits)
    i,item=hits[0]
    if not is_actual_pool_creation_migration(item,mint,pda,pool):
        return None,1
    return i,1


def collect_one(rpc:Rpc,row:dict[str,Any],frozen_index:int)->dict[str,Any]:
    mint=row['mint']; pool=row.get('pool_address')
    if not pool:
        return {'frozen_manifest_index':frozen_index,'mint':mint,'t0':row['t0'],'source_resolved':False,
                'collector_error':'missing_pool_address','outcomes_opened':False}
    pda=bonding_curve_pda(mint); corpus_t0=parse_ts(row['t0']); corpus_second=int(math.floor(corpus_t0))
    retrieval_lo=corpus_t0-RETRIEVAL_ENVELOPE_SECONDS
    boundary_lo=corpus_t0-BOUNDARY_LOOKBACK_SECONDS
    try:
        sigs,paging=paginate_window(rpc,pda,retrieval_lo)
    except Exception as exc:
        return {'frozen_manifest_index':frozen_index,'mint':mint,'t0':row['t0'],'pool_address':pool,
                'bonding_curve_pda':pda,'source_resolved':False,'collector_error':f'{type(exc).__name__}: {exc}',
                'outcomes_opened':False}

    by_sig={x['signature']:x for x in sigs if x.get('signature')}
    boundary_meta=[x for x in by_sig.values() if x.get('blockTime') is not None and boundary_lo<=float(x['blockTime'])<=corpus_second]
    boundary_sigs=[str(x['signature']) for x in boundary_meta]
    try:
        tx_map=rpc.get_transactions(boundary_sigs) if boundary_sigs else {}
    except Exception as exc:
        return {'frozen_manifest_index':frozen_index,'mint':mint,'t0':row['t0'],'pool_address':pool,
                'bonding_curve_pda':pda,'source_resolved':False,'collector_error':f'{type(exc).__name__}: {exc}',
                'signature_pages':paging.get('signature_pages'),'outcomes_opened':False}

    missing_bodies=[s for s in boundary_sigs if body_missing(tx_map.get(s))]
    candidates=[]
    for meta in boundary_meta:
        sig=str(meta['signature']); tx=tx_map.get(sig)
        if body_missing(tx): continue
        if is_actual_pool_creation_migration(tx,mint,pda,pool):
            candidates.append({'signature':sig,'slot':int(meta['slot']),'block_time':int(meta['blockTime'])})

    unique={(x['signature'],x['slot'],x['block_time']) for x in candidates}
    boundary=candidates[0] if len(unique)==1 else None
    boundary_block_error=None; boundary_index=None; boundary_signature_hits=0; boundary_block_sha=None
    if boundary:
        try:
            rec=(get_blocks_batched(rpc,[int(boundary['slot'])],1) or {}).get(int(boundary['slot'])) or {}
            block=rec.get('block')
            if not isinstance(block,dict) or block.get('_rpc_error'):
                boundary_block_error=(block or {}).get('_rpc_error') if isinstance(block,dict) else 'nonobject_block'
            else:
                import hashlib as _hashlib
                canon=json.dumps(block,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
                boundary_block_sha=_hashlib.sha256(canon).hexdigest()
                boundary_index,boundary_signature_hits=boundary_tx_index(block,boundary['signature'],mint,pda,pool)
                if boundary_index is None:
                    boundary_block_error='boundary_signature_or_semantics_not_unique_in_block'
                else:
                    boundary['transaction_index']=boundary_index
        except Exception as exc:
            boundary_block_error=f'{type(exc).__name__}: {exc}'

    paging_complete=bool(
        paging.get('signature_conflicts')==0 and not paging.get('null_block_time_seen')
        and (paging.get('crossed_lower_bound') or paging.get('history_exhausted'))
    )
    boundary_unique=len(unique)==1
    boundary_within=bool(boundary and boundary_lo<=float(boundary['block_time'])<=corpus_second)
    block_complete=bool(boundary and boundary_index is not None and boundary_block_error is None and boundary_signature_hits==1)

    successful_pre=0; pre_total=0; same_second_pre=0; same_second_post=0; same_slot_unresolved=0
    feature_lo=None
    if boundary and boundary_index is not None:
        feature_lo=float(boundary['block_time'])-WINDOW_SECONDS
        for meta in by_sig.values():
            bt=meta.get('blockTime'); slot=meta.get('slot')
            if bt is None or slot is None: continue
            bt=float(bt); slot=int(slot)
            if not (feature_lo<=bt<=float(boundary['block_time'])): continue
            before=False
            if bt<float(boundary['block_time']):
                before=True
            elif bt==float(boundary['block_time']):
                if slot<int(boundary['slot']): before=True
                elif slot>int(boundary['slot']): before=False
                else:
                    # Need exact index only for signatures in the boundary slot.
                    # Reuse the already fetched boundary block by refetch-free lookup from tx map is impossible;
                    # query positions from the boundary block through a single deterministic call.
                    try:
                        rec2=(get_blocks_batched(rpc,[int(boundary['slot'])],1) or {}).get(int(boundary['slot'])) or {}
                        b2=rec2.get('block')
                        positions={}
                        if isinstance(b2,dict) and not b2.get('_rpc_error'):
                            for j,it in enumerate(b2.get('transactions') or []):
                                if isinstance(it,dict):
                                    s=tx_signature(it)
                                    if s: positions[s]=j
                        si=positions.get(str(meta['signature']))
                        if si is None:
                            same_slot_unresolved+=1
                            continue
                        before=si<int(boundary_index)
                    except Exception:
                        same_slot_unresolved+=1
                        continue
                if before: same_second_pre+=1
                else: same_second_post+=1
            if before:
                pre_total+=1
                if meta.get('err') is None: successful_pre+=1

    source_resolved=bool(
        paging_complete and not missing_bodies and boundary_unique and boundary_within and block_complete
        and same_slot_unresolved==0
    )
    return {
        'lab':'PMD-001','stage':'CHAIN_EXACT_CEILING_V06_SHARD','outcomes_opened':False,
        'frozen_manifest_index':frozen_index,'mint':mint,'t0':row['t0'],'pool_address':pool,
        'bonding_curve_pda':pda,'signature_pages':paging.get('signature_pages'),
        'signature_conflicts':paging.get('signature_conflicts'),'null_block_time_seen':paging.get('null_block_time_seen'),
        'boundary_search_signatures':len(boundary_sigs),'boundary_transaction_bodies_missing':len(missing_bodies),
        'qualifying_pool_creation_boundaries':len(unique),'chain_boundary_signature':boundary.get('signature') if boundary else None,
        'chain_boundary_block_time':boundary.get('block_time') if boundary else None,
        'chain_boundary_slot':boundary.get('slot') if boundary else None,
        'chain_boundary_transaction_index':boundary.get('transaction_index') if boundary else None,
        'boundary_block_sha256':boundary_block_sha,'boundary_block_error':boundary_block_error,
        'corpus_minus_chain_boundary_seconds':(corpus_t0-float(boundary['block_time'])) if boundary else None,
        'feature_window_lower_unix':feature_lo,'pre_boundary_signatures':pre_total,
        'successful_pre_boundary_signatures':successful_pre,'same_boundary_second_pre':same_second_pre,
        'same_boundary_second_at_or_after':same_second_post,'same_slot_position_unresolved':same_slot_unresolved,
        'source_resolved':source_resolved,'ceiling_has_successful_preboundary_signature':bool(source_resolved and successful_pre>0),
        'retrieval_envelope_seconds':RETRIEVAL_ENVELOPE_SECONDS,'feature_window_seconds':WINDOW_SECONDS,
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True); ap.add_argument('--out-dir',required=True)
    ap.add_argument('--rpc-url',default='https://api.mainnet-beta.solana.com'); ap.add_argument('--source-name',default='solana_public_rpc_chain_exact_ceiling_v06')
    ap.add_argument('--start',type=int,required=True); ap.add_argument('--limit',type=int,required=True)
    ap.add_argument('--pace-seconds',type=float,default=0.15)
    args=ap.parse_args()
    mp=Path(args.manifest)
    if sha256_file(mp)!=EXPECTED_MANIFEST_SHA: raise RuntimeError('frozen manifest SHA mismatch')
    rows=load_manifest(mp)
    if len(rows)!=EXPECTED_ROWS: raise RuntimeError('frozen manifest row-count mismatch')
    end=min(len(rows),args.start+args.limit); selected=rows[args.start:end]
    if len(selected)!=args.limit: raise RuntimeError('deterministic shard length mismatch')
    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True); details=out/'chain_exact_ceiling_details.jsonl'
    rpc=Rpc(args.rpc_url,args.source_name); collected=[]
    with details.open('w',encoding='utf-8') as f:
        for j,row in enumerate(selected):
            rec=collect_one(rpc,row,args.start+j); collected.append(rec)
            f.write(json.dumps(rec,sort_keys=True,ensure_ascii=False)+'\n'); f.flush()
            if (j+1)%10==0:
                print(json.dumps({'rows':j+1,'resolved':sum(bool(x.get('source_resolved')) for x in collected),'with_success':sum(bool(x.get('ceiling_has_successful_preboundary_signature')) for x in collected)},sort_keys=True),flush=True)
            if args.pace_seconds>0: time.sleep(args.pace_seconds)
    receipt={
        'lab':'PMD-001','stage':'CHAIN_EXACT_CEILING_V06_SHARD','economic_outcomes_opened':False,
        'start':args.start,'limit':args.limit,'rows':len(collected),
        'source_resolved_rows':sum(bool(x.get('source_resolved')) for x in collected),
        'rows_with_successful_preboundary_signature':sum(bool(x.get('ceiling_has_successful_preboundary_signature')) for x in collected),
        'details_sha256':sha256_file(details),'rpc_request_counter':rpc.counter,'scientific_verdict_authority':False,
    }
    (out/'chain_exact_ceiling_shard_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())

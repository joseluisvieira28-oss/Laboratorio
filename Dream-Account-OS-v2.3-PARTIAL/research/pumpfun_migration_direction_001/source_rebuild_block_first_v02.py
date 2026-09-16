#!/usr/bin/env python3
"""PMD-001 block-first source collector V0.2 — safe-second cutoff.

Outcome-blind. Applies TIMESTAMP_PRECISION_CUTOFF_AMENDMENT_V01: the whole
integer second containing T0 is quarantined from predictive/source-gate evidence.
Signature history identifies safe [T0-300s, floor(T0)) rows; every unique safe
in-window slot is fetched with full getBlock, and transaction bodies come only
from those block responses.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any

from source_rebuild_helius_v01 import (
    Rpc, bonding_curve_pda, load_manifest, parse_ts, sha256_json, tx_has_target,
)

WINDOW_SECONDS=300
SIG_LIMIT=1000


def find_matches(block:Any,signature:str)->list[Any]:
    out=[]
    if not isinstance(block,dict): return out
    for item in block.get('transactions') or []:
        tx=item.get('transaction') if isinstance(item,dict) else None
        sigs=tx.get('signatures') if isinstance(tx,dict) else None
        if isinstance(sigs,list) and signature in sigs: out.append(item)
    return out


def collect_one(rpc:Rpc,row:dict[str,Any],root:Path)->dict[str,Any]:
    mint=row['mint']; t0=parse_ts(row['t0']); lo=t0-WINDOW_SECONDS; safe_cutoff=float(math.floor(t0))
    pda=bonding_curve_pda(mint)

    all_sigs=[]; before=None; pages=0; crossed=False; exhausted=False; null_time=False
    while True:
        page=rpc.get_signatures(pda,before=before); pages+=1
        if not page:
            exhausted=True; break
        all_sigs.extend(page)
        times=[x.get('blockTime') for x in page]
        if any(x is None for x in times): null_time=True
        vals=[float(x) for x in times if x is not None]
        if vals and min(vals)<lo:
            crossed=True; break
        if len(page)<SIG_LIMIT:
            exhausted=True; break
        before=page[-1].get('signature')
        if not before: break
        if pages>100: raise RuntimeError(f'pagination safety stop: {mint}')

    by_sig={}; conflicts=0
    for x in all_sigs:
        sig=x.get('signature')
        if not sig: continue
        if sig in by_sig and by_sig[sig]!=x: conflicts+=1
        else: by_sig[sig]=x

    safe=[x for x in by_sig.values() if x.get('blockTime') is not None and lo<=float(x['blockTime'])<safe_cutoff]
    same_second=[x for x in by_sig.values() if x.get('blockTime') is not None and float(x['blockTime'])==safe_cutoff]
    safe.sort(key=lambda x:(x.get('slot') or -1,x.get('signature') or ''))
    slots=sorted({int(x['slot']) for x in safe if x.get('slot') is not None})

    block_dir=root/'blocks'/mint; block_dir.mkdir(parents=True,exist_ok=True)
    blocks={}; block_errors=0
    for slot in slots:
        try:
            block=rpc.get_block(slot)
            if not isinstance(block,dict): block={'_rpc_error':'null_or_nonobject_block'}
        except Exception as exc:
            block={'_rpc_error':f'{type(exc).__name__}: {exc}'}
        if block.get('_rpc_error'): block_errors+=1
        blocks[slot]=block
        evidence={
            'lab':'PMD-001','stage':'BLOCK_FIRST_REBUILD_V02_SAFE_CUTOFF','outcomes_opened':False,
            'source_name':rpc.source_name,'slot':slot,'block':block,
            'canonical_sha256':sha256_json(block),
        }
        with gzip.open(block_dir/f'slot_{slot}.json.gz','wt',encoding='utf-8') as gf:
            json.dump(evidence,gf,sort_keys=True,ensure_ascii=False)

    raw_dir=root/'raw'; raw_dir.mkdir(parents=True,exist_ok=True)
    raw_path=raw_dir/f'{mint}.jsonl'
    missing=0; duplicate_matches=0; target=0
    with raw_path.open('w',encoding='utf-8') as f:
        for meta in safe:
            sig=meta['signature']; slot=int(meta['slot']); matches=find_matches(blocks.get(slot),sig)
            if len(matches)==0: missing+=1; tx=None
            elif len(matches)>1: duplicate_matches+=1; tx=matches[0]
            else: tx=matches[0]
            is_target=tx_has_target(tx,mint,pda)
            if is_target: target+=1
            rec={
                'lab':'PMD-001','stage':'BLOCK_FIRST_REBUILD_V02_SAFE_CUTOFF','outcomes_opened':False,
                'source_name':rpc.source_name,'mint':mint,'t0':row['t0'],
                'safe_cutoff_unix_second':safe_cutoff,'same_second_quarantined':True,
                'bonding_curve_pda':pda,'signature_meta':meta,'feature_eligible_by_time':True,
                'target_pump_mint_pda_present':is_target,'transaction':tx,
                'raw_response_sha256':sha256_json(tx),
            }
            f.write(json.dumps(rec,sort_keys=True,ensure_ascii=False)+'\n')

    complete=(
        conflicts==0 and not null_time and (crossed or exhausted) and block_errors==0
        and missing==0 and duplicate_matches==0 and len(slots)>0 and len(safe)>0
    )
    return {
        'lab':'PMD-001','stage':'BLOCK_FIRST_REBUILD_V02_SAFE_CUTOFF','outcomes_opened':False,
        'source_name':rpc.source_name,'mint':mint,'t0':row['t0'],'safe_cutoff_unix_second':safe_cutoff,
        'bonding_curve_pda':pda,'window_seconds':WINDOW_SECONDS,'signature_pages':pages,
        'signatures_unique_seen':len(by_sig),'safe_in_window_signatures':len(safe),
        'same_second_signatures_quarantined':len(same_second),'unique_safe_in_window_slots':len(slots),
        'blocks_requested':len(slots),'block_errors':block_errors,'missing_signature_bodies':missing,
        'duplicate_signature_body_matches':duplicate_matches,'signature_conflicts':conflicts,
        'null_block_time_seen':null_time,'crossed_lower_bound':crossed,'history_exhausted':exhausted,
        'valid_target_pump_transactions':target,'source_complete':complete,
        'timestamp_precision_amendment_applied':True,'raw_file':str(raw_path),
        'raw_file_sha256':hashlib.sha256(raw_path.read_bytes()).hexdigest(),
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True); ap.add_argument('--out-dir',default='pmd_block_first_v02')
    ap.add_argument('--rpc-url',default=None); ap.add_argument('--source-name',default=None)
    ap.add_argument('--start',type=int,default=0); ap.add_argument('--limit',type=int,default=0)
    args=ap.parse_args()
    if args.rpc_url:
        url=args.rpc_url; source=args.source_name or 'generic_rpc_probe_safe_cutoff'
    else:
        key=os.environ.get('HELIUS_API_KEY')
        if not key:
            print('HELIUS_API_KEY required for authenticated archival route',file=sys.stderr); return 3
        url=f'https://mainnet.helius-rpc.com/?api-key={key}'; source='helius_archival_rpc_block_first_safe_cutoff'
    rows=load_manifest(Path(args.manifest))
    if args.start<0 or args.start>=len(rows): raise ValueError('--start out of range')
    rows=rows[args.start:]
    if args.limit>0: rows=rows[:args.limit]
    root=Path(args.out_dir); root.mkdir(parents=True,exist_ok=True); summary=root/'source_rebuild_summary.jsonl'; rpc=Rpc(url,source)
    with summary.open('w',encoding='utf-8') as sf:
        for row in rows:
            try: res=collect_one(rpc,row,root)
            except Exception as exc:
                res={'lab':'PMD-001','stage':'BLOCK_FIRST_REBUILD_V02_SAFE_CUTOFF','outcomes_opened':False,
                     'source_name':source,'mint':row['mint'],'t0':row['t0'],'source_complete':False,
                     'timestamp_precision_amendment_applied':True,'collector_error':f'{type(exc).__name__}: {exc}'}
            sf.write(json.dumps(res,sort_keys=True,ensure_ascii=False)+'\n'); sf.flush()
            print(json.dumps({k:res.get(k) for k in ('mint','source_complete','safe_in_window_signatures','same_second_signatures_quarantined','unique_safe_in_window_slots','valid_target_pump_transactions','collector_error') if k in res},sort_keys=True))
    print(json.dumps({'lab':'PMD-001','stage':'BLOCK_FIRST_REBUILD_V02_SAFE_CUTOFF','outcomes_opened':False,
                      'source_name':source,'rows_attempted':len(rows),'rpc_request_counter':rpc.counter,
                      'summary_path':str(summary)},sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())

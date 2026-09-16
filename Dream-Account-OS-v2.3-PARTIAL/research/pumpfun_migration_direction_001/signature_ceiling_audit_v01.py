#!/usr/bin/env python3
"""PMD-001 full-population signature ceiling audit V0.1.

Reads only the frozen source manifest and standard Solana signature metadata.
No transaction bodies, post-migration prices or economic outcomes are read.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from source_rebuild_helius_v01 import Rpc, bonding_curve_pda, load_manifest, parse_ts

EXPECTED_ROWS=1012
EXPECTED_MANIFEST_SHA='56a8836921b7d348597fa3e63f210adbfe8f34bd67321af797855d23c364243b'
WINDOW=300
SIG_LIMIT=1000
MIN_VIABLE=1000


def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(8*1024*1024),b''): h.update(c)
    return h.hexdigest()


def audit_one(rpc:Rpc,row:dict)->dict:
    mint=row['mint']; t0=parse_ts(row['t0']); lo=t0-WINDOW; pda=bonding_curve_pda(mint)
    before=None; pages=0; all_rows=[]; crossed=False; exhausted=False; null_time=False
    try:
        while True:
            page=rpc.get_signatures(pda,before=before); pages+=1
            if not page:
                exhausted=True; break
            all_rows.extend(page)
            ts=[x.get('blockTime') for x in page]
            if any(x is None for x in ts): null_time=True
            vals=[float(x) for x in ts if x is not None]
            if vals and min(vals)<lo:
                crossed=True; break
            if len(page)<SIG_LIMIT:
                exhausted=True; break
            before=page[-1].get('signature')
            if not before: break
            if pages>100: raise RuntimeError('pagination safety stop')
    except Exception as exc:
        return {'mint':mint,'t0':row['t0'],'bonding_curve_pda':pda,'source_complete':False,
                'collector_error':f'{type(exc).__name__}: {exc}','outcomes_opened':False}

    by_sig={}; conflicts=0
    for x in all_rows:
        sig=x.get('signature')
        if not sig: continue
        if sig in by_sig and by_sig[sig]!=x: conflicts+=1
        else: by_sig[sig]=x
    inwin=[x for x in by_sig.values() if x.get('blockTime') is not None and lo<=float(x['blockTime'])<t0]
    success=[x for x in inwin if x.get('err') is None]
    complete=(conflicts==0 and not null_time and (crossed or exhausted))
    return {
        'lab':'PMD-001','stage':'SIGNATURE_CEILING_AUDIT_V01','outcomes_opened':False,
        'mint':mint,'t0':row['t0'],'bonding_curve_pda':pda,'signature_pages':pages,
        'signatures_unique_seen':len(by_sig),'in_window_signatures':len(inwin),
        'successful_in_window_signatures':len(success),'signature_conflicts':conflicts,
        'null_block_time_seen':null_time,'crossed_lower_bound':crossed,'history_exhausted':exhausted,
        'source_complete':complete,
    }


def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument('--manifest',required=True)
    ap.add_argument('--out-dir',default='pmd_signature_ceiling_v01')
    ap.add_argument('--rpc-url',default=None)
    ap.add_argument('--source-name',default=None)
    ap.add_argument('--pace-seconds',type=float,default=0.25)
    args=ap.parse_args()

    mp=Path(args.manifest)
    if sha256_file(mp)!=EXPECTED_MANIFEST_SHA: raise RuntimeError('frozen manifest SHA mismatch')
    rows=load_manifest(mp)
    if len(rows)!=EXPECTED_ROWS: raise RuntimeError(f'manifest rows {len(rows)} != {EXPECTED_ROWS}')

    if args.rpc_url:
        url=args.rpc_url; source=args.source_name or 'generic_rpc_signature_audit'
    else:
        key=os.environ.get('HELIUS_API_KEY')
        if not key:
            print('HELIUS_API_KEY required unless --rpc-url provided',file=sys.stderr); return 3
        url=f'https://mainnet.helius-rpc.com/?api-key={key}'; source='helius_archival_signature_audit'

    out=Path(args.out_dir); out.mkdir(parents=True,exist_ok=True)
    details=out/'signature_ceiling_details.jsonl'; rpc=Rpc(url,source)
    audited=[]
    with details.open('w',encoding='utf-8') as f:
        for i,row in enumerate(rows,1):
            r=audit_one(rpc,row); r['source_name']=source; audited.append(r)
            f.write(json.dumps(r,sort_keys=True,ensure_ascii=False)+'\n'); f.flush()
            if i%25==0:
                print(json.dumps({'audited':i,'complete':sum(bool(x.get('source_complete')) for x in audited),
                                  'with_success':sum(bool(x.get('source_complete')) and int(x.get('successful_in_window_signatures') or 0)>0 for x in audited)},sort_keys=True))
            if args.pace_seconds>0: time.sleep(args.pace_seconds)

    complete=[r for r in audited if r.get('source_complete')]
    with_success=[r for r in complete if int(r.get('successful_in_window_signatures') or 0)>0]
    incomplete=[r for r in audited if not r.get('source_complete')]
    dates_success=len({str(r['t0'])[:10] for r in with_success})
    if incomplete:
        verdict='SIGNATURE_CEILING_UNRESOLVED'
    elif len(with_success)>=MIN_VIABLE:
        verdict='SIGNATURE_CEILING_VIABLE'
    else:
        verdict='SIGNATURE_CEILING_INSUFFICIENT'
    receipt={
        'lab':'PMD-001','stage':'SIGNATURE_CEILING_AUDIT_V01','outcomes_opened':False,
        'source_name':source,'manifest_sha256':EXPECTED_MANIFEST_SHA,'population_rows':len(rows),
        'source_complete_rows':len(complete),'source_incomplete_rows':len(incomplete),
        'rows_with_successful_in_window_signature':len(with_success),
        'distinct_dates_with_successful_in_window_signature':dates_success,
        'minimum_viable_rows':MIN_VIABLE,'verdict':verdict,
        'details_sha256':sha256_file(details),'rpc_request_counter':rpc.counter,
        'full_block_gate_run':False,'economic_outcomes_opened':False,
    }
    (out/'signature_ceiling_receipt.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if verdict in ('SIGNATURE_CEILING_VIABLE','SIGNATURE_CEILING_INSUFFICIENT') else 2

if __name__=='__main__':
    raise SystemExit(main())

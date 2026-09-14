#!/usr/bin/env python3
"""Transport-only remediation for STABLECOIN-EXCHANGE-FLOW-001 source QA.

Consumes the immutable source artifact from failed run 34896944142. It does not
rebuild or redefine the primary source dataset. It repeats the exact frozen
second-provider QA subset sequentially with conservative rate limiting.

No BTC outcomes, no 2025/2026, no live trading, no exchange mutation.
"""
from __future__ import annotations
import csv, hashlib, json, shutil, time
import urllib.request, urllib.error
from datetime import date, timedelta
from pathlib import Path

LAB='STABLECOIN-EXCHANGE-FLOW-001'
MVE='SEF-BINANCE-PUBLIC-USDT-ETH-1D-001'
SOURCE_RUN_ID=34896944142
SOURCE_ROOT=Path('source_artifact')
OUT=Path('artifacts/stablecoin_exchange_flow_daily_source_qa_remediated_v01')
QA='https://rpc.mevblocker.io'
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
BALANCE_OF='70a08231'
BASKET=[
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
START_DATE=date(2022,11,11)
END_DATE=date(2024,12,29)
MIN_INTERVAL_S=0.45
MAX_RETRIES=12
REQ_TIMEOUT=35
_last_call_started=0.0


def file_sha(p:Path)->str:
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def locate(name:str)->Path:
    xs=list(SOURCE_ROOT.rglob(name))
    if len(xs)!=1: raise RuntimeError(f'expected exactly one {name}, found {len(xs)}')
    return xs[0]

def balance_data(address:str)->str:
    return '0x'+BALANCE_OF+('0'*24)+address[2:].lower()

def throttle():
    global _last_call_started
    now=time.monotonic(); sleep_for=MIN_INTERVAL_S-(now-_last_call_started)
    if sleep_for>0: time.sleep(sleep_for)
    _last_call_started=time.monotonic()

def rpc_balance(address:str,block:int,rid:int):
    body=json.dumps({'jsonrpc':'2.0','id':rid,'method':'eth_call','params':[{'to':USDT,'data':balance_data(address)},hex(block)]},separators=(',',':')).encode()
    last=None
    for attempt in range(MAX_RETRIES):
        throttle()
        req=urllib.request.Request(QA,data=body,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'CryptoLab-SEF-QA-remediation/0.1'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=REQ_TIMEOUT) as r:
                raw=r.read(); p=json.loads(raw.decode())
                if r.status==200 and isinstance(p,dict) and isinstance(p.get('result'),str) and not p.get('error'):
                    return int(p['result'],16), hashlib.sha256(raw).hexdigest(), attempt+1
                last=f"HTTP{r.status}:{p.get('error') if isinstance(p,dict) else 'bad_json'}"
        except urllib.error.HTTPError as e:
            raw=e.read(); retry_after=e.headers.get('Retry-After') if e.headers else None
            last=f'HTTP{e.code}:{raw.decode(errors="replace")[:200]}'
            if e.code==429:
                try: wait=max(float(retry_after),1.0) if retry_after else min(20.0,1.0*(2**attempt))
                except Exception: wait=min(20.0,1.0*(2**attempt))
                time.sleep(wait)
                continue
        except Exception as e:
            last=f'{type(e).__name__}:{e}'
        time.sleep(min(12.0,0.5*(2**attempt)))
    raise RuntimeError(f'RPC_FAILED {QA} eth_call after {MAX_RETRIES}: {last}')

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    original_receipt_path=locate('SOURCE_DATASET_RECEIPT.json')
    csv_path=locate('USDT_BINANCE_PUBLIC_BASKET_DAILY_20221111_20241229.csv')
    audit_path=locate('USDT_BINANCE_PUBLIC_BASKET_BALANCES_AUDIT.jsonl')
    boundary_path=locate('UTC_BOUNDARY_BLOCKS.jsonl')
    orig=json.loads(original_receipt_path.read_text())

    # Fail closed unless this is exactly the known pre-outcome transport failure.
    if orig.get('classification')!='DATA_FAILURE': raise RuntimeError(f'unexpected original classification {orig.get("classification")}')
    if orig.get('btc_market_data_accessed') or orig.get('access_2025') or orig.get('access_2026'):
        raise RuntimeError('original source artifact violates governance')
    for k in ('boundary_invariants_pass','date_integrity_pass','net_flow_arithmetic_pass'):
        if orig.get(k) is not True: raise RuntimeError(f'original structural gate not pass: {k}')
    if orig.get('boundary_rows')!=780 or orig.get('signal_rows')!=779: raise RuntimeError('unexpected source row counts')
    if orig.get('qa_calls_expected')!=243 or orig.get('qa_error_count')!=23: raise RuntimeError('unexpected QA failure shape')
    errs=orig.get('qa_errors') or []
    if len(errs)!=23 or any('HTTP429' not in str(e.get('error')) for e in errs):
        raise RuntimeError('original QA failures are not exclusively HTTP429 transport failures')
    if file_sha(csv_path)!=orig.get('csv_sha256'): raise RuntimeError('original CSV hash mismatch')
    if file_sha(audit_path)!=orig.get('audit_jsonl_sha256'): raise RuntimeError('original audit hash mismatch')
    if file_sha(boundary_path)!=orig.get('boundary_jsonl_sha256'): raise RuntimeError('original boundary hash mismatch')

    # Load already-frozen primary state values and exact boundary blocks.
    primary={}
    with audit_path.open(encoding='utf-8') as f:
        for line in f:
            x=json.loads(line)
            ds=x['date']
            for b in x['balances']: primary[(ds,b['address'].lower())]=int(b['raw'])
    boundaries={}
    with boundary_path.open(encoding='utf-8') as f:
        for line in f:
            x=json.loads(line); boundaries[x['date']]=int(x['boundary_block'])

    dates=[]; d=START_DATE
    while d<=END_DATE:
        dates.append(d); d+=timedelta(days=1)
    qa_dates={START_DATE.isoformat(),END_DATE.isoformat()}
    qa_dates.update(d.isoformat() for d in dates if d.day==1)
    qa_dates=sorted(qa_dates)
    if len(qa_dates)!=27: raise RuntimeError(f'unexpected QA date count {len(qa_dates)}')
    expected_calls=len(qa_dates)*len(BASKET)
    if expected_calls!=243: raise RuntimeError(f'unexpected QA calls {expected_calls}')

    qa_rows=[]; errors=[]; mismatches=[]; idx=0
    for ds in qa_dates:
        if ds[:4] in ('2025','2026'): raise RuntimeError(f'forbidden QA date {ds}')
        block=boundaries.get(ds)
        if block is None: raise RuntimeError(f'missing frozen boundary {ds}')
        for address in BASKET:
            idx+=1
            p=primary.get((ds,address.lower()))
            if p is None: raise RuntimeError(f'missing frozen primary value {ds} {address}')
            try:
                q,h,attempts=rpc_balance(address,block,3000+idx)
                row={'date':ds,'address':address,'block':block,'primary_raw':p,'qa_raw':q,'exact_match':p==q,'response_sha256':h,'attempts':attempts}
                qa_rows.append(row)
                if p!=q: mismatches.append(row)
            except Exception as e:
                errors.append({'date':ds,'address':address,'block':block,'error':f'{type(e).__name__}:{e}'})

    # Preserve primary files byte-for-byte in the remediated artifact.
    out_csv=OUT/csv_path.name; out_audit=OUT/audit_path.name; out_boundary=OUT/boundary_path.name
    shutil.copyfile(csv_path,out_csv); shutil.copyfile(audit_path,out_audit); shutil.copyfile(boundary_path,out_boundary)
    qa_path=OUT/'QA_SECOND_PROVIDER_EXACT_MATCH.jsonl'
    with qa_path.open('w',encoding='utf-8') as f:
        for r in qa_rows: f.write(json.dumps(r,sort_keys=True,separators=(',',':'))+'\n')

    preserved=(file_sha(out_csv)==file_sha(csv_path) and file_sha(out_audit)==file_sha(audit_path) and file_sha(out_boundary)==file_sha(boundary_path))
    qa_pass=(not errors and not mismatches and len(qa_rows)==expected_calls and all(r['exact_match'] for r in qa_rows))
    cls='SOURCE_DATASET_PASS' if preserved and qa_pass else 'DATA_FAILURE'
    amendment=Path('labs/STABLECOIN_EXCHANGE_FLOW_001/SOURCE_DATASET_TECHNICAL_AMENDMENT_002_QA_RATE_LIMIT.md')
    receipt={
      'lab_id':LAB,'mve_id':MVE,'classification':cls,
      'source_failed_run_id':SOURCE_RUN_ID,
      'remediation':'sequential rate-limited repeat of exact frozen MEV Blocker QA subset only',
      'primary_provider':orig.get('primary_provider'),'qa_provider':QA,
      'baseline_date':orig.get('baseline_date'),'final_source_date':orig.get('final_source_date'),
      'boundary_rows':orig.get('boundary_rows'),'signal_rows':orig.get('signal_rows'),
      'boundary_invariants_pass':orig.get('boundary_invariants_pass'),'date_integrity_pass':orig.get('date_integrity_pass'),'net_flow_arithmetic_pass':orig.get('net_flow_arithmetic_pass'),
      'qa_date_count':len(qa_dates),'qa_dates':qa_dates,'qa_calls_expected':expected_calls,'qa_calls_completed':len(qa_rows),
      'qa_error_count':len(errors),'qa_errors':errors,'qa_mismatch_count':len(mismatches),'qa_mismatches':mismatches,'qa_exact_match_pass':qa_pass,
      'primary_artifacts_preserved_byte_for_byte':preserved,
      'csv_sha256':file_sha(out_csv),'audit_jsonl_sha256':file_sha(out_audit),'boundary_jsonl_sha256':file_sha(out_boundary),'qa_jsonl_sha256':file_sha(qa_path),
      'original_receipt_sha256':file_sha(original_receipt_path),'technical_amendment_002_sha256':file_sha(amendment),
      'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,'access_2025':False,'access_2026':False,
      'live_trading':False,'exchange_mutation':False,'post_outcome_tuning':False,
    }
    (OUT/'SOURCE_DATASET_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())

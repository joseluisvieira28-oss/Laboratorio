#!/usr/bin/env python3
"""Source-only QA transport remediation for STABLECOIN-EXCHANGE-FLOW-001.

The original full dRPC source build completed 780 boundaries and 779 signals,
but its prospectively fixed MEV Blocker QA subset suffered HTTP 429 on 23/243
individual eth_call requests. Before any BTC outcome access, this remediation
replays the exact same 27 QA dates using the already-probed 9-call MEV JSON-RPC
batch transport and compares every raw USDT balance against the immutable dRPC
source artifact.

No signal definition, date, address, outcome, cost, threshold, or hypothesis is
changed. No BTC, 2025, or 2026 data is accessed.
"""
from __future__ import annotations
import csv, hashlib, json, time, urllib.request, urllib.error
from pathlib import Path

LAB='STABLECOIN-EXCHANGE-FLOW-001'
MVE='SEF-BINANCE-PUBLIC-USDT-ETH-1D-001'
SOURCE_ROOT=Path('source_artifact')
OUT=Path('artifacts/stablecoin_exchange_flow_source_qa_remediation_v01')
QA_URL='https://rpc.mevblocker.io'
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
BALANCE_OF='70a08231'
BASKET=[
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
EXPECTED_SOURCE_RUN_ID=34896944142
MAX_RETRIES=8


def file_sha(p:Path):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for c in iter(lambda:f.read(1024*1024),b''): h.update(c)
    return h.hexdigest()

def balance_payload(address:str, block:int, rid:int):
    data='0x'+BALANCE_OF+('0'*24)+address[2:].lower()
    return {'jsonrpc':'2.0','id':rid,'method':'eth_call','params':[{'to':USDT,'data':data},hex(block)]}

def batch_balances(block:int):
    payload=[balance_payload(a,block,i+1) for i,a in enumerate(BASKET)]
    body=json.dumps(payload,separators=(',',':')).encode()
    last=None
    for attempt in range(MAX_RETRIES):
        req=urllib.request.Request(QA_URL,data=body,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'CryptoLab-SEF-QA-remediation/0.1'},method='POST')
        try:
            with urllib.request.urlopen(req,timeout=40) as r:
                raw=r.read(); p=json.loads(raw.decode())
                if r.status==200 and isinstance(p,list) and len(p)==len(BASKET):
                    byid={x.get('id'):x for x in p if isinstance(x,dict)}
                    vals={}; errors=[]
                    for i,a in enumerate(BASKET,1):
                        x=byid.get(i,{})
                        if x.get('error') or not isinstance(x.get('result'),str):
                            errors.append({'address':a,'error':x.get('error') or 'missing_result'})
                        else:
                            vals[a]=int(x['result'],16)
                    if not errors and len(vals)==len(BASKET):
                        return {'ok':True,'values':vals,'response_sha256':hashlib.sha256(raw).hexdigest(),'attempts':attempt+1,'http_status':r.status}
                    last=f'batch semantic errors {errors[:2]}'
                else:
                    last=f'bad batch status/shape status={r.status} type={type(p).__name__}'
        except urllib.error.HTTPError as e:
            raw=e.read(); last=f'HTTP{e.code}:{raw.decode(errors="replace")[:300]}'
        except Exception as e:
            last=f'{type(e).__name__}:{e}'
        time.sleep(min(8.0,0.5*(2**attempt)))
    return {'ok':False,'error':last}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    receipts=list(SOURCE_ROOT.rglob('SOURCE_DATASET_RECEIPT.json'))
    csvs=list(SOURCE_ROOT.rglob('USDT_BINANCE_PUBLIC_BASKET_DAILY_20221111_20241229.csv'))
    audits=list(SOURCE_ROOT.rglob('USDT_BINANCE_PUBLIC_BASKET_BALANCES_AUDIT.jsonl'))
    bounds=list(SOURCE_ROOT.rglob('UTC_BOUNDARY_BLOCKS.jsonl'))
    if not(len(receipts)==len(csvs)==len(audits)==len(bounds)==1):
        raise RuntimeError(f'incomplete immutable source artifact receipts={len(receipts)} csvs={len(csvs)} audits={len(audits)} bounds={len(bounds)}')
    src=json.loads(receipts[0].read_text())
    if src.get('classification')!='DATA_FAILURE':
        raise RuntimeError(f'expected original DATA_FAILURE, got {src.get("classification")}')
    hard_preconditions={
      'boundary_invariants_pass':src.get('boundary_invariants_pass') is True,
      'date_integrity_pass':src.get('date_integrity_pass') is True,
      'net_flow_arithmetic_pass':src.get('net_flow_arithmetic_pass') is True,
      'boundary_rows_780':src.get('boundary_rows')==780,
      'signal_rows_779':src.get('signal_rows')==779,
      'no_btc':src.get('btc_market_data_accessed') is False,
      'no_2025':src.get('access_2025') is False,
      'no_2026':src.get('access_2026') is False,
      'csv_hash_match':file_sha(csvs[0])==src.get('csv_sha256'),
      'audit_hash_match':file_sha(audits[0])==src.get('audit_jsonl_sha256'),
      'boundary_hash_match':file_sha(bounds[0])==src.get('boundary_jsonl_sha256'),
    }
    if not all(hard_preconditions.values()):
        raise RuntimeError(f'original source artifact failed non-transport preconditions: {hard_preconditions}')
    qa_dates=src.get('qa_dates')
    if not isinstance(qa_dates,list) or len(qa_dates)!=27:
        raise RuntimeError('prospectively fixed QA date list missing/wrong')

    boundary_by_date={}
    with bounds[0].open(encoding='utf-8') as f:
        for line in f:
            x=json.loads(line); boundary_by_date[x['date']]=x
    primary={}
    with audits[0].open(encoding='utf-8') as f:
        for line in f:
            x=json.loads(line)
            if x['date'] in qa_dates:
                primary[x['date']]={b['address']:int(b['raw']) for b in x['balances']}
    if set(primary)!=set(qa_dates): raise RuntimeError('QA dates not all present in primary audit')

    comparisons=[]; errors=[]; mismatches=[]
    for idx,ds in enumerate(qa_dates):
        b=boundary_by_date.get(ds)
        if not b: raise RuntimeError(f'missing boundary {ds}')
        block=int(b['boundary_block'])
        res=batch_balances(block)
        if not res['ok']:
            errors.append({'date':ds,'block':block,'error':res.get('error')})
        else:
            for a in BASKET:
                pv=primary[ds][a]; qv=res['values'][a]
                comparisons.append({'date':ds,'block':block,'address':a,'primary_raw':pv,'qa_raw':qv,'exact_match':pv==qv,'batch_response_sha256':res['response_sha256'],'attempts':res['attempts']})
                if pv!=qv: mismatches.append({'date':ds,'block':block,'address':a,'primary_raw':pv,'qa_raw':qv})
        time.sleep(0.30)

    expected=27*9
    exact=(not errors and not mismatches and len(comparisons)==expected and all(x['exact_match'] for x in comparisons))
    classification='SOURCE_DATASET_PASS' if exact else ('DATA_FAILURE' if mismatches else 'TECHNICAL_FAILURE')
    comp_path=OUT/'MEV_BATCH_QA_COMPARISONS.jsonl'
    with comp_path.open('w',encoding='utf-8') as f:
        for x in comparisons: f.write(json.dumps(x,sort_keys=True,separators=(',',':'))+'\n')
    receipt={
      'lab_id':LAB,'mve_id':MVE,'classification':classification,
      'remediation_type':'QA transport only: MEV Blocker 9-call batch; source values/signals unchanged',
      'original_source_run_id':EXPECTED_SOURCE_RUN_ID,'original_source_classification':src.get('classification'),
      'original_source_csv_sha256':src.get('csv_sha256'),'original_source_receipt_sha256':file_sha(receipts[0]),
      'hard_preconditions':hard_preconditions,'qa_provider':QA_URL,'qa_dates':qa_dates,'qa_date_count':len(qa_dates),
      'qa_calls_logical_expected':expected,'qa_calls_logical_completed':len(comparisons),'qa_batches_expected':27,'qa_batches_completed':27-len(errors),
      'qa_error_count':len(errors),'qa_errors':errors,'qa_mismatch_count':len(mismatches),'qa_mismatches':mismatches,
      'qa_exact_match_pass':exact,'comparison_jsonl_sha256':file_sha(comp_path),
      'boundary_rows':src.get('boundary_rows'),'signal_rows':src.get('signal_rows'),'date_integrity_pass':src.get('date_integrity_pass'),'net_flow_arithmetic_pass':src.get('net_flow_arithmetic_pass'),'boundary_invariants_pass':src.get('boundary_invariants_pass'),
      'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,'access_2025':False,'access_2026':False,
    }
    (OUT/'SOURCE_QA_REMEDIATION_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0

if __name__=='__main__': raise SystemExit(main())

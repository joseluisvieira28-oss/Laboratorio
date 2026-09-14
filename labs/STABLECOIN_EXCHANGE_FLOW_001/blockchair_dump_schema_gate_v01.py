#!/usr/bin/env python3
"""Outcome-blind schema/size probe of one protected Blockchair ERC-20 daily dump."""
from __future__ import annotations
import hashlib, json, urllib.error, urllib.request, zlib
from pathlib import Path

OUT=Path('artifacts/stablecoin_exchange_flow_dump_schema_gate_v01')
URL='https://gz.blockchair.com/ethereum/erc-20/transactions/blockchair_erc-20_transactions_20221111.tsv.gz'
MAX_READ=2*1024*1024

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    req=urllib.request.Request(URL,headers={'User-Agent':'CryptoLab-SEF-schema-probe/0.1','Range':f'bytes=0-{MAX_READ-1}'})
    result={'url':URL}
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read(MAX_READ)
            result.update({'status':r.status,'bytes_read':len(raw),'content_length':r.headers.get('Content-Length'),'content_range':r.headers.get('Content-Range'),'accept_ranges':r.headers.get('Accept-Ranges'),'content_type':r.headers.get('Content-Type'),'prefix_sha256':hashlib.sha256(raw).hexdigest()})
            decomp=zlib.decompressobj(16+zlib.MAX_WBITS)
            txt=decomp.decompress(raw).decode('utf-8',errors='replace')
            lines=txt.splitlines()
            result['decompressed_prefix_bytes']=len(txt.encode('utf-8'))
            result['header']=lines[0] if lines else None
            result['first_data_line']=lines[1] if len(lines)>1 else None
            result['lines_in_prefix']=len(lines)
    except urllib.error.HTTPError as e:
        result.update({'status':e.code,'error':e.read().decode('utf-8',errors='replace')[:1000]})
    except Exception as e:
        result.update({'status':None,'error':f'{type(e).__name__}:{e}'})

    header=(result.get('header') or '').split('\t')
    required={'block_id','transaction_hash','time','token_address','token_decimals','sender','recipient','value'}
    # Some Blockchair dump versions may use date instead of time; require enough semantics to identify day and transfer.
    semantic_ok=required.issubset(set(header)) or ({'block_id','transaction_hash','token_address','sender','recipient','value'}.issubset(set(header)) and ('date' in header or 'time' in header))
    classification='DUMP_SCHEMA_PASS' if result.get('status') in (200,206) and semantic_ok else 'DUMP_SCHEMA_FAIL'
    receipt={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':classification,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,'required_semantics_ok':semantic_ok,'probe':result}
    (OUT/'DUMP_SCHEMA_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())

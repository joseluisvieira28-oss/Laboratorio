#!/usr/bin/env python3
"""Pre-outcome transport-only gzip capability/equivalence gate for MEV Blocker."""
from __future__ import annotations
import gzip, hashlib, json, urllib.request
from pathlib import Path
OUT=Path('artifacts/stablecoin_exchange_flow_mevblocker_gzip_gate_v01')
RPC='https://rpc.mevblocker.io'
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
PADS=['0x'+'0'*24+x for x in sorted([
'47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','f977814e90da44bfa03b6295a0616a897441acec','a344c7ada83113b3b56941f6e85bf2eb425949f3','28c6c06298d514db089934071355e5743bf21d60','21a31ee1afc51d94c2efccaa2092ad1028285549','56eddb7aa87536c09ccc2793473599fd21a8b17f','dfd5293d8e347dfe59e90efd55b2956a1343963d','9696f59e4d72e237be84ffd425dcad154bf96976','4976a4a02f38326660d17bf34b431dc6e2eb2327'])]
A=15943061; B=A+3199

def payload():
    flt={'fromBlock':hex(A),'toBlock':hex(B),'address':USDT,'topics':[TRANSFER,None,PADS]}
    return json.dumps({'jsonrpc':'2.0','method':'eth_getLogs','params':[flt],'id':1},separators=(',',':')).encode()

def call(accept_gzip:bool):
    headers={'Content-Type':'application/json','User-Agent':'CryptoLab-SEF-gzip-gate/0.1'}
    if accept_gzip: headers['Accept-Encoding']='gzip'
    req=urllib.request.Request(RPC,data=payload(),headers=headers,method='POST')
    with urllib.request.urlopen(req,timeout=90) as r:
        wire=r.read(); ce=(r.headers.get('Content-Encoding') or '').lower()
        logical=gzip.decompress(wire) if ce=='gzip' else wire
        p=json.loads(logical.decode())
        logs=p.get('result') if isinstance(p,dict) else None
        if not isinstance(logs,list): raise RuntimeError(f'no log result: {p}')
        # provider JSON serialization can differ, so compare canonical logical payloads later
        canon=json.dumps(logs,sort_keys=True,separators=(',',':')).encode()
        return {'status':r.status,'content_encoding':ce or None,'wire_bytes':len(wire),'logical_bytes':len(logical),'wire_sha256':hashlib.sha256(wire).hexdigest(),'canonical_result_sha256':hashlib.sha256(canon).hexdigest(),'result_count':len(logs)}

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    plain=call(False); gz=call(True)
    equiv=(plain['result_count']==gz['result_count'] and plain['canonical_result_sha256']==gz['canonical_result_sha256'])
    compressed=(gz['content_encoding']=='gzip' and gz['wire_bytes']<gz['logical_bytes'])
    rec={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':'GZIP_EQUIVALENCE_PASS' if equiv else 'GZIP_EQUIVALENCE_FAILURE','gzip_transport_effective':compressed,'plain':plain,'gzip':gz,'exact_canonical_result_match':equiv,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
    (OUT/'MEVBLOCKER_GZIP_GATE_RECEIPT.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
    print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=='__main__': main()

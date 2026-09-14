#!/usr/bin/env python3
"""Read-only provider matrix for historical USDT Transfer logs.

Protected data only: 2022-11-11 and 2024-12-30/31 block windows.
No price/outcome/PnL access. No 2025/2026.
"""
from __future__ import annotations
import hashlib, json, urllib.request, urllib.error
from pathlib import Path

OUT=Path('artifacts/stablecoin_exchange_flow_rpc_provider_matrix_v01')
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
BASKET=[
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
PROVIDERS={
  'llama':'https://eth.llamarpc.com',
  'one_rpc':'https://public.1rpc.io/eth',
  'drpc':'https://eth.drpc.org',
  'cloudflare':'https://cloudflare-eth.com',
  'mevblocker':'https://rpc.mevblocker.io',
}
START_BLOCK=15943061
END_BLOCK=21519027

def pad(a:str)->str: return '0x'+'0'*24+a.lower()[2:]
PADS=[pad(x) for x in BASKET]

def rpc(url:str, method:str, params:list, rid:int)->dict:
    body=json.dumps({'jsonrpc':'2.0','method':method,'params':params,'id':rid},separators=(',',':')).encode()
    req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json','User-Agent':'CryptoLab-SEF-provider-matrix/0.1'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            raw=r.read(); payload=json.loads(raw.decode())
            return {'http_status':r.status,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'payload':payload}
    except urllib.error.HTTPError as e:
        raw=e.read(); return {'http_status':e.code,'bytes':len(raw),'text':raw.decode(errors='replace')[:800]}
    except Exception as e:
        return {'http_status':None,'error':f'{type(e).__name__}:{e}'}

def filt(a:int,b:int,direction:str)->dict:
    topics=[TRANSFER,None,None]
    topics[2 if direction=='inbound' else 1]=PADS
    return {'fromBlock':hex(a),'toBlock':hex(b),'address':USDT,'topics':topics}

def result_list(x):
    p=x.get('payload'); return p.get('result') if isinstance(p,dict) and isinstance(p.get('result'),list) else None

def block_ts(x):
    p=x.get('payload'); r=p.get('result') if isinstance(p,dict) else None
    return int(r['timestamp'],16) if isinstance(r,dict) and r.get('timestamp') else None

def compact(x):
    out={k:v for k,v in x.items() if k!='payload'}
    p=x.get('payload')
    if isinstance(p,dict) and p.get('error') is not None: out['rpc_error']=p.get('error')
    r=result_list(x)
    if r is not None: out['result_count']=len(r)
    ts=block_ts(x)
    if ts is not None: out['block_timestamp']=ts
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    receipt={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,'providers':{}}
    passes=[]
    rid=1
    for name,url in PROVIDERS.items():
        probes={}
        probes['start_block']=rpc(url,'eth_getBlockByNumber',[hex(START_BLOCK),False],rid); rid+=1
        probes['end_block']=rpc(url,'eth_getBlockByNumber',[hex(END_BLOCK),False],rid); rid+=1
        probes['start_in']=rpc(url,'eth_getLogs',[filt(START_BLOCK,START_BLOCK+399,'inbound')],rid); rid+=1
        probes['start_out']=rpc(url,'eth_getLogs',[filt(START_BLOCK,START_BLOCK+399,'outbound')],rid); rid+=1
        probes['end_in']=rpc(url,'eth_getLogs',[filt(END_BLOCK-399,END_BLOCK,'inbound')],rid); rid+=1
        probes['end_out']=rpc(url,'eth_getLogs',[filt(END_BLOCK-399,END_BLOCK,'outbound')],rid); rid+=1
        st,et=block_ts(probes['start_block']),block_ts(probes['end_block'])
        lists={k:result_list(v) for k,v in probes.items() if k.endswith('_in') or k.endswith('_out')}
        errors=[]
        if st is None or et is None: errors.append('BLOCK_METADATA_UNAVAILABLE')
        if st is not None and not (1668124800 <= st < 1668211200): errors.append('BAD_START_TIMESTAMP')
        if et is not None and not (1704067200 <= et < 1735689600): errors.append('BAD_END_TIMESTAMP')
        for k,v in lists.items():
            if v is None: errors.append(f'LOG_QUERY_FAILED:{k}')
        status='PASS' if not errors else 'FAIL'
        if status=='PASS': passes.append(name)
        receipt['providers'][name]={'url':url,'status':status,'errors':errors,'probes':{k:compact(v) for k,v in probes.items()}}
    receipt['passing_providers']=passes
    receipt['classification']='RPC_PROVIDER_MATRIX_PASS' if passes else 'RPC_PROVIDER_MATRIX_FAILURE'
    (OUT/'RPC_PROVIDER_MATRIX_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())

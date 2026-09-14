#!/usr/bin/env python3
"""Read-only Ethereum RPC historical log source gate for frozen Binance USDT basket.

Uses only protected 2022/2024 block ranges. No BTC prices/outcomes and no 2025/2026.
"""
from __future__ import annotations
import hashlib, json, urllib.request, urllib.error
from pathlib import Path

OUT=Path('artifacts/stablecoin_exchange_flow_rpc_gate_v01')
RPC='https://ethereum-rpc.publicnode.com'
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
BASKET=[
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
START_BLOCK=15943061  # dump first ERC-20 block at 2022-11-11 00:00:11 UTC
END_BLOCK=21519027    # previously protected 2024-12-31 00:59 UTC block

def pad(a:str)->str: return '0x'+'0'*24+a.lower()[2:]
PADS=[pad(x) for x in BASKET]

def rpc(method:str, params:list, rid:int)->dict:
    body=json.dumps({'jsonrpc':'2.0','method':method,'params':params,'id':rid},separators=(',',':')).encode()
    req=urllib.request.Request(RPC,data=body,headers={'Content-Type':'application/json','User-Agent':'CryptoLab-SEF-rpc-gate/0.1'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=45) as r:
            raw=r.read(); payload=json.loads(raw.decode())
            return {'http_status':r.status,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'payload':payload}
    except urllib.error.HTTPError as e:
        raw=e.read(); return {'http_status':e.code,'bytes':len(raw),'text':raw.decode(errors='replace')[:1000]}
    except Exception as e: return {'http_status':None,'error':f'{type(e).__name__}:{e}'}

def log_filter(a:int,b:int,direction:str)->dict:
    topics=[TRANSFER,None,None]
    if direction=='outbound': topics[1]=PADS
    else: topics[2]=PADS
    return {'fromBlock':hex(a),'toBlock':hex(b),'address':USDT,'topics':topics}

def count_result(x:dict):
    p=x.get('payload'); return len(p.get('result')) if isinstance(p,dict) and isinstance(p.get('result'),list) else None

def block_ts(x:dict):
    p=x.get('payload'); res=p.get('result') if isinstance(p,dict) else None
    return int(res['timestamp'],16) if isinstance(res,dict) and res.get('timestamp') else None

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    probes={
      'start_block':rpc('eth_getBlockByNumber',[hex(START_BLOCK),False],1),
      'end_block':rpc('eth_getBlockByNumber',[hex(END_BLOCK),False],2),
      'start_in':rpc('eth_getLogs',[log_filter(START_BLOCK,START_BLOCK+799,'inbound')],3),
      'start_out':rpc('eth_getLogs',[log_filter(START_BLOCK,START_BLOCK+799,'outbound')],4),
      'end_in':rpc('eth_getLogs',[log_filter(END_BLOCK-799,END_BLOCK,'inbound')],5),
      'end_out':rpc('eth_getLogs',[log_filter(END_BLOCK-799,END_BLOCK,'outbound')],6),
    }
    st=block_ts(probes['start_block']); et=block_ts(probes['end_block'])
    counts={k:count_result(v) for k,v in probes.items() if k.endswith('_in') or k.endswith('_out')}
    errors=[]
    if st is None or et is None: errors.append('BLOCK_METADATA_UNAVAILABLE')
    if st is not None and not (1668124800 <= st < 1668211200): errors.append(f'START_TIMESTAMP_OUTSIDE_2022_11_11:{st}')
    if et is not None and not (1704067200 <= et < 1735689600): errors.append(f'END_TIMESTAMP_OUTSIDE_2024:{et}')
    for k,v in counts.items():
        if v is None: errors.append(f'LOG_QUERY_FAILED:{k}')
    classification='RPC_HISTORICAL_LOGS_PASS' if not errors and sum(v or 0 for v in counts.values())>0 else ('RPC_HISTORICAL_LOGS_EMPTY' if not errors else 'RPC_SOURCE_FAILURE')
    # Strip full log payloads from receipt; retain deterministic hash and counts only.
    compact={}
    for k,v in probes.items():
        compact[k]={kk:vv for kk,vv in v.items() if kk!='payload'}
        compact[k]['result_count']=count_result(v)
        compact[k]['block_timestamp']=block_ts(v)
        if isinstance(v.get('payload'),dict) and v['payload'].get('error'): compact[k]['rpc_error']=v['payload']['error']
    receipt={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':classification,'rpc':RPC,'start_block':START_BLOCK,'end_block':END_BLOCK,'start_timestamp':st,'end_timestamp':et,'log_counts':counts,'errors':errors,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,'probes':compact}
    (OUT/'RPC_SOURCE_GATE_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())

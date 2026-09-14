#!/usr/bin/env python3
"""Read-only multi-provider Ethereum historical eth_getLogs gate.

Protected period only: 2022-11-11 and 2024-12-31 probes. No BTC prices,
returns, PnL, 2025, or 2026 data. Tests source feasibility only.
"""
from __future__ import annotations
import hashlib, json, urllib.request, urllib.error, time
from pathlib import Path

OUT=Path('artifacts/stablecoin_exchange_flow_rpc_multi_gate_v01')
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
BASKET=[
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
START_BLOCK=15943061
END_BLOCK=21519027
WINDOW=99
PROVIDERS={
  'drpc':'https://eth.drpc.org',
  'merkle':'https://eth.merkle.io',
  'blast':'https://eth-mainnet.public.blastapi.io',
  'mevblocker':'https://rpc.mevblocker.io',
  'tenderly':'https://gateway.tenderly.co/public/mainnet',
  '1rpc':'https://public.1rpc.io/eth',
  'llama':'https://eth.llamarpc.com',
}

def pad(a:str)->str: return '0x'+'0'*24+a.lower()[2:]
PADS=[pad(x) for x in BASKET]

def rpc(url:str, method:str, params:list, rid:int)->dict:
    body=json.dumps({'jsonrpc':'2.0','method':method,'params':params,'id':rid},separators=(',',':')).encode()
    req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'CryptoLab-SEF-multi-rpc-gate/0.1'},method='POST')
    t0=time.time()
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            raw=r.read(); elapsed=round(time.time()-t0,3)
            try: payload=json.loads(raw.decode())
            except Exception: payload=None
            return {'http_status':r.status,'bytes':len(raw),'elapsed_s':elapsed,'sha256':hashlib.sha256(raw).hexdigest(),'payload':payload,'text_prefix':raw.decode(errors='replace')[:500]}
    except urllib.error.HTTPError as e:
        raw=e.read(); return {'http_status':e.code,'bytes':len(raw),'elapsed_s':round(time.time()-t0,3),'text_prefix':raw.decode(errors='replace')[:800]}
    except Exception as e:
        return {'http_status':None,'elapsed_s':round(time.time()-t0,3),'error':f'{type(e).__name__}:{e}'}

def filt(a:int,b:int,direction:str)->dict:
    topics=[TRANSFER,None,None]
    if direction=='outbound': topics[1]=PADS
    else: topics[2]=PADS
    return {'fromBlock':hex(a),'toBlock':hex(b),'address':USDT,'topics':topics}

def compact(x:dict)->dict:
    p=x.get('payload')
    result=p.get('result') if isinstance(p,dict) else None
    err=p.get('error') if isinstance(p,dict) else None
    sample=None
    if isinstance(result,list) and result:
        row=result[0]
        sample={k:row.get(k) for k in ('blockNumber','blockTimestamp','transactionHash','logIndex','data','topics') if k in row}
    return {
      'http_status':x.get('http_status'),'bytes':x.get('bytes'),'elapsed_s':x.get('elapsed_s'),
      'sha256':x.get('sha256'),'result_count':len(result) if isinstance(result,list) else None,
      'rpc_error':err,'transport_error':x.get('error'),'text_prefix':x.get('text_prefix') if err or x.get('http_status')!=200 else None,
      'sample_log':sample,
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    providers={}
    for i,(name,url) in enumerate(PROVIDERS.items(),start=1):
        probes={
          'start_in':rpc(url,'eth_getLogs',[filt(START_BLOCK,START_BLOCK+WINDOW,'inbound')],i*10+1),
          'start_out':rpc(url,'eth_getLogs',[filt(START_BLOCK,START_BLOCK+WINDOW,'outbound')],i*10+2),
          'end_in':rpc(url,'eth_getLogs',[filt(END_BLOCK-WINDOW,END_BLOCK,'inbound')],i*10+3),
          'end_out':rpc(url,'eth_getLogs',[filt(END_BLOCK-WINDOW,END_BLOCK,'outbound')],i*10+4),
        }
        c={k:compact(v) for k,v in probes.items()}
        ok=all(v['http_status']==200 and v['result_count'] is not None and v['rpc_error'] is None for v in c.values())
        nonempty=sum(v['result_count'] or 0 for v in c.values()) if ok else 0
        providers[name]={'url':url,'pass':bool(ok and nonempty>0),'all_queries_valid':ok,'total_logs':nonempty,'probes':c}
    winners=[k for k,v in providers.items() if v['pass']]
    receipt={
      'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001',
      'classification':'RPC_PROVIDER_GATE_PASS' if winners else 'RPC_PROVIDER_GATE_BLOCKED',
      'winners':winners,'providers':providers,'start_block':START_BLOCK,'end_block':END_BLOCK,'window_blocks':WINDOW+1,
      'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,
    }
    (OUT/'RPC_MULTI_PROVIDER_GATE_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())

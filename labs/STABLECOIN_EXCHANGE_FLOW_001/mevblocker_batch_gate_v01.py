#!/usr/bin/env python3
"""Source-only historical JSON-RPC batch capability gate for MEV Blocker."""
import json, urllib.request, hashlib
from pathlib import Path
OUT=Path('artifacts/stablecoin_exchange_flow_mevblocker_batch_gate_v01')
RPC='https://rpc.mevblocker.io'
BLOCKS=[15943000,15943061,21519027]
def main():
    OUT.mkdir(parents=True,exist_ok=True)
    body=json.dumps([{'jsonrpc':'2.0','method':'eth_getBlockByNumber','params':[hex(b),False],'id':i+1} for i,b in enumerate(BLOCKS)],separators=(',',':')).encode()
    req=urllib.request.Request(RPC,data=body,headers={'Content-Type':'application/json','User-Agent':'CryptoLab-SEF-batch-gate/0.1'},method='POST')
    try:
      with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read(); p=json.loads(raw.decode())
        rows=[]
        if isinstance(p,list):
          byid={x.get('id'):x for x in p if isinstance(x,dict)}
          for i,b in enumerate(BLOCKS,1):
            x=byid.get(i,{}); result=x.get('result'); ts=int(result['timestamp'],16) if isinstance(result,dict) and result.get('timestamp') else None
            rows.append({'block':b,'timestamp':ts,'rpc_error':x.get('error')})
        ok=isinstance(p,list) and len(rows)==3 and all(x['timestamp'] is not None for x in rows)
        rec={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':'RPC_BATCH_PASS' if ok else 'RPC_BATCH_FAILURE','http_status':r.status,'response_bytes':len(raw),'response_sha256':hashlib.sha256(raw).hexdigest(),'rows':rows,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
    except Exception as e:
      rec={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','classification':'RPC_BATCH_FAILURE','error':f'{type(e).__name__}:{e}','access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
    (OUT/'MEVBLOCKER_BATCH_GATE_RECEIPT.json').write_text(json.dumps(rec,indent=2,sort_keys=True)+'\n')
    print(json.dumps(rec,indent=2,sort_keys=True))
if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations
import json, urllib.request, urllib.error, hashlib

RPC_CANDIDATES=['https://ethereum-rpc.publicnode.com','https://public.1rpc.io/eth','https://eth.drpc.org','https://eth.llamarpc.com']
POOL='0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2'
TOPIC0='0x804c9b842b2748a22bb64b345453a3de7ca54a6ca45ce00d415894979e22897a'
TOPIC1='0x000000000000000000000000a0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
WINDOWS=[('Q1',19000000,19000500),('Q2',19650000,19650500),('Q3',20300000,20300500),('Q4',20950000,20950500)]
BINANCE=[
 'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2023-01.zip',
 'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2023-12.zip',
 'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-01.zip',
 'https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1d/BTCUSDT-1d-2024-12.zip']

def rpc_on(endpoint, method, params):
    raw=json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params}).encode()
    req=urllib.request.Request(endpoint,data=raw,headers={'content-type':'application/json','user-agent':'AAVE-CREDIT-STRESS-001/0.1'})
    with urllib.request.urlopen(req,timeout=45) as r:
        obj=json.loads(r.read().decode())
    if 'error' in obj: raise RuntimeError(f"rpc error {method}: {obj['error']}")
    return obj['result']

def head(url):
    req=urllib.request.Request(url,method='HEAD',headers={'user-agent':'AAVE-CREDIT-STRESS-001/0.1'})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:
            return {'ok':200<=r.status<400,'status':r.status,'etag':r.headers.get('ETag'),'length':r.headers.get('Content-Length')}
    except Exception as e:
        return {'ok':False,'error':type(e).__name__+': '+str(e)}

def probe_endpoint(endpoint):
    out={'endpoint':endpoint}
    chain=rpc_on(endpoint,'eth_chainId',[]); out['chain_id']=chain
    code=rpc_on(endpoint,'eth_getCode',[POOL,'latest']); out['pool_code_nonempty']=bool(code and code!='0x')
    probes=[]
    for q,a,b in WINDOWS:
        ba=rpc_on(endpoint,'eth_getBlockByNumber',[hex(a),False]); bb=rpc_on(endpoint,'eth_getBlockByNumber',[hex(b),False])
        logs=rpc_on(endpoint,'eth_getLogs',[{'address':POOL,'fromBlock':hex(a),'toBlock':hex(b),'topics':[TOPIC0,TOPIC1]}])
        structural=[]
        for x in logs:
            structural.append({'blockNumber_present':bool(x.get('blockNumber')),'transactionHash_present':bool(x.get('transactionHash')),'logIndex_present':x.get('logIndex') is not None,'topics_count':len(x.get('topics',[])),'data_present':bool(x.get('data'))})
        probes.append({'quarter':q,'from_block':a,'to_block':b,'from_timestamp_hex':ba.get('timestamp'),'to_timestamp_hex':bb.get('timestamp'),'matching_log_count':len(logs),'structural_records':structural[:3]})
    out['quarter_probes']=probes
    return out

def main():
    receipt={'lab':'AAVE-CREDIT-STRESS-001','phase':'SOURCE_PROVENANCE_GATE_ONLY','economic_values_decoded':False,'btc_returns_computed':False,'regression_computed':False,'pnl_computed':False,'2025_accessed':False,'2026_accessed':False,'live_trading':False,'exchange_mutation':False,'rpc_attempts':[]}
    chosen=None
    for endpoint in RPC_CANDIDATES:
        try:
            probe=probe_endpoint(endpoint); receipt['rpc_attempts'].append({'endpoint':endpoint,'status':'SUCCESS'})
            chosen=probe; break
        except Exception as e:
            receipt['rpc_attempts'].append({'endpoint':endpoint,'status':'FAIL','error':type(e).__name__+': '+str(e)})
    try:
        receipt['binance']=[{'url':u,**head(u)} for u in BINANCE]
        if chosen is None:
            cls='SOURCE_ACQUISITION_TECHNICAL_FAILURE'
        else:
            receipt['rpc_selected']=chosen['endpoint']; receipt['chain_id']=chosen['chain_id']; receipt['pool_code_nonempty']=chosen['pool_code_nonempty']; receipt['quarter_probes']=chosen['quarter_probes']
            healthy = chosen['chain_id']=='0x1' and chosen['pool_code_nonempty'] and all(x['ok'] for x in receipt['binance'])
            valid_quarters=sum(1 for p in chosen['quarter_probes'] if p['matching_log_count']>0 and all(all(v for k,v in s.items() if k!='topics_count') and s['topics_count']>=2 for s in p['structural_records']))
            receipt['valid_quarter_probes']=valid_quarters
            if not healthy: cls='PROVENANCE_FAILURE'
            elif valid_quarters<4: cls='INSUFFICIENT_STRUCTURAL_SAMPLE'
            else: cls='SOURCE_DATA_PASS'
    except Exception as e:
        cls='PROVENANCE_FAILURE'; receipt['error']=type(e).__name__+': '+str(e)
    receipt['classification']=cls
    blob=json.dumps(receipt,sort_keys=True,separators=(',',':')).encode(); receipt['receipt_sha256']=hashlib.sha256(blob).hexdigest()
    print('AAVE_CS001_SOURCE_GATE_JSON='+json.dumps(receipt,sort_keys=True))
    print('AAVE_CS001_SOURCE_GATE='+cls)
    if cls!='SOURCE_DATA_PASS': raise SystemExit(2)

if __name__=='__main__': main()

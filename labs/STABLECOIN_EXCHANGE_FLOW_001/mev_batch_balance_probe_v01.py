#!/usr/bin/env python3
import json, urllib.request, urllib.error
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
SELECTOR='70a08231'
BASKET=['0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
BLOCK=15943060
URL='https://rpc.mevblocker.io'
def payload(a,i):
    data='0x'+SELECTOR+'0'*24+a[2:]
    return {'jsonrpc':'2.0','id':i,'method':'eth_call','params':[{'to':USDT,'data':data},hex(BLOCK)]}
body=json.dumps([payload(a,i+1) for i,a in enumerate(BASKET)],separators=(',',':')).encode()
req=urllib.request.Request(URL,data=body,headers={'Content-Type':'application/json','User-Agent':'CryptoLab-SEF-batch-probe/0.1'},method='POST')
try:
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read(); p=json.loads(raw.decode()); ok=isinstance(p,list) and len(p)==9 and all(isinstance(x.get('result'),str) for x in p)
        print(json.dumps({'classification':'MEV_BATCH_PASS' if ok else 'MEV_BATCH_FAIL','status':r.status,'items':len(p) if isinstance(p,list) else None,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False},indent=2))
except urllib.error.HTTPError as e:
    print(json.dumps({'classification':'MEV_BATCH_FAIL','status':e.code,'body':e.read().decode(errors='replace')[:500],'access_2025':False,'access_2026':False,'btc_market_data_accessed':False},indent=2))

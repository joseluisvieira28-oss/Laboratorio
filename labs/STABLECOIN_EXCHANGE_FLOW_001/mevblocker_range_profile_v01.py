#!/usr/bin/env python3
"""Profile safe historical eth_getLogs range on MEV Blocker, protected period only."""
from __future__ import annotations
import hashlib, json, time, urllib.request, urllib.error
from pathlib import Path
OUT=Path('artifacts/stablecoin_exchange_flow_mevblocker_range_profile_v01')
RPC='https://rpc.mevblocker.io'
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
BASKET=['0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
START=15943061
END=21519027
RANGES=[400,800,1600,3200,6400,12800]
def pad(a): return '0x'+'0'*24+a[2:].lower()
PADS=[pad(a) for a in BASKET]
def filt(a,b,d):
    t=[TRANSFER,None,None]; t[2 if d=='inbound' else 1]=PADS
    return {'fromBlock':hex(a),'toBlock':hex(b),'address':USDT,'topics':t}
def call(flt,rid):
    body=json.dumps({'jsonrpc':'2.0','method':'eth_getLogs','params':[flt],'id':rid},separators=(',',':')).encode()
    req=urllib.request.Request(RPC,data=body,headers={'Content-Type':'application/json','User-Agent':'CryptoLab-SEF-range-profile/0.1'},method='POST')
    t0=time.monotonic()
    try:
        with urllib.request.urlopen(req,timeout=60) as r:
            raw=r.read(); dt=time.monotonic()-t0; p=json.loads(raw.decode())
            result=p.get('result') if isinstance(p,dict) else None
            return {'http_status':r.status,'elapsed_s':round(dt,4),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'result_count':len(result) if isinstance(result,list) else None,'rpc_error':p.get('error') if isinstance(p,dict) else None}
    except urllib.error.HTTPError as e:
        raw=e.read(); return {'http_status':e.code,'elapsed_s':round(time.monotonic()-t0,4),'bytes':len(raw),'text':raw.decode(errors='replace')[:800]}
    except Exception as e: return {'http_status':None,'elapsed_s':round(time.monotonic()-t0,4),'error':f'{type(e).__name__}:{e}'}
def main():
    OUT.mkdir(parents=True,exist_ok=True); rows=[]; rid=1
    for anchor_name,anchor in [('start',START),('end',END)]:
      for n in RANGES:
        a=anchor if anchor_name=='start' else anchor-n+1; b=a+n-1
        for d in ('inbound','outbound'):
          r=call(filt(a,b,d),rid); rid+=1
          rows.append({'anchor':anchor_name,'range_blocks':n,'direction':d,'from_block':a,'to_block':b,**r})
        # fail-closed: stop increasing at this anchor once either direction fails
        last=rows[-2:]
        if any(x.get('result_count') is None for x in last): break
    ok=[x for x in rows if x.get('result_count') is not None]
    max_safe=max((x['range_blocks'] for x in ok),default=0)
    receipt={'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':'RANGE_PROFILE_PASS' if max_safe else 'RANGE_PROFILE_FAILURE','rpc':RPC,'max_observed_safe_range_blocks':max_safe,'rows':rows,'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False}
    (OUT/'MEVBLOCKER_RANGE_PROFILE_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print(json.dumps(receipt,indent=2,sort_keys=True))
if __name__=='__main__': main()

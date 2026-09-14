#!/usr/bin/env python3
"""Outcome-blind USDT basket balance/Transfer equivalence gate.

Tests whether change in total historical USDT balance of the frozen 9-address
Binance basket exactly equals Transfer-event inflow minus outflow over protected
2022/2024 sample windows. Also cross-checks historical balanceOf state between
independent archive RPC providers.

No BTC prices, returns, PnL, 2025, or 2026 data.
"""
from __future__ import annotations
import json, hashlib, urllib.request, urllib.error
from pathlib import Path

OUT=Path('artifacts/stablecoin_exchange_flow_balance_recon_v01')
USDT='0xdac17f958d2ee523a2206206994597c13d831ec7'
TRANSFER='0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'
BALANCE_OF='70a08231'
BASKET=[
'0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503','0xf977814e90da44bfa03b6295a0616a897441acec','0xa344c7ada83113b3b56941f6e85bf2eb425949f3','0x28c6c06298d514db089934071355e5743bf21d60','0x21a31ee1afc51d94c2efccaa2092ad1028285549','0x56eddb7aa87536c09ccc2793473599fd21a8b17f','0xdfd5293d8e347dfe59e90efd55b2956a1343963d','0x9696f59e4d72e237be84ffd425dcad154bf96976','0x4976a4a02f38326660d17bf34b431dc6e2eb2327']
PROVIDERS={'drpc':'https://eth.drpc.org','tenderly':'https://gateway.tenderly.co/public/mainnet'}
WINDOWS={'start_2022':(15943061,15943160),'end_2024':(21518928,21519027)}

def post(url:str,payload,timeout=40):
    body=json.dumps(payload,separators=(',',':')).encode()
    req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json','Accept':'application/json','User-Agent':'CryptoLab-SEF-balance-recon/0.1'},method='POST')
    try:
        with urllib.request.urlopen(req,timeout=timeout) as r:
            raw=r.read(); return r.status, raw, json.loads(raw.decode())
    except urllib.error.HTTPError as e:
        raw=e.read();
        try: p=json.loads(raw.decode())
        except Exception: p=None
        return e.code, raw, p

def pad_topic(a:str)->str: return '0x'+'0'*24+a[2:].lower()
PADS=[pad_topic(a) for a in BASKET]

def balance_call(a:str,block:int,rid:int):
    data='0x'+BALANCE_OF+('0'*24)+a[2:].lower()
    return {'jsonrpc':'2.0','id':rid,'method':'eth_call','params':[{'to':USDT,'data':data},hex(block)]}

def basket_balance(url:str,block:int):
    payload=[balance_call(a,block,i+1) for i,a in enumerate(BASKET)]
    status,raw,res=post(url,payload)
    if status!=200 or not isinstance(res,list): return {'ok':False,'status':status,'raw_sha256':hashlib.sha256(raw).hexdigest(),'error':'bad_batch_response'}
    byid={x.get('id'):x for x in res if isinstance(x,dict)}
    vals=[]; errs=[]
    for i,a in enumerate(BASKET,1):
        x=byid.get(i,{})
        if x.get('error') or not isinstance(x.get('result'),str): errs.append({'address':a,'error':x.get('error') or 'missing_result'})
        else: vals.append({'address':a,'raw':int(x['result'],16)})
    return {'ok':not errs and len(vals)==len(BASKET),'status':status,'raw_sha256':hashlib.sha256(raw).hexdigest(),'total_raw':sum(x['raw'] for x in vals),'balances':vals,'errors':errs}

def get_logs(url:str,a:int,b:int,direction:str,rid:int):
    topics=[TRANSFER,None,None]
    if direction=='out': topics[1]=PADS
    else: topics[2]=PADS
    f={'fromBlock':hex(a),'toBlock':hex(b),'address':USDT,'topics':topics}
    status,raw,p=post(url,{'jsonrpc':'2.0','id':rid,'method':'eth_getLogs','params':[f]})
    result=p.get('result') if isinstance(p,dict) else None
    return {'ok':status==200 and isinstance(result,list) and not p.get('error'),'status':status,'sha256':hashlib.sha256(raw).hexdigest(),'error':p.get('error') if isinstance(p,dict) else None,'logs':result if isinstance(result,list) else []}

def window_recon(url:str,a:int,b:int):
    before=basket_balance(url,a-1); after=basket_balance(url,b)
    ins=get_logs(url,a,b,'in',100); outs=get_logs(url,a,b,'out',101)
    in_sum=sum(int(x.get('data','0x0'),16) for x in ins['logs'])
    out_sum=sum(int(x.get('data','0x0'),16) for x in outs['logs'])
    delta=(after.get('total_raw')-before.get('total_raw')) if before.get('ok') and after.get('ok') else None
    event_net=in_sum-out_sum if ins['ok'] and outs['ok'] else None
    return {
      'before_block':a-1,'after_block':b,'before_total_raw':before.get('total_raw'),'after_total_raw':after.get('total_raw'),
      'balance_delta_raw':delta,'inbound_raw':in_sum if ins['ok'] else None,'outbound_raw':out_sum if outs['ok'] else None,
      'event_net_raw':event_net,'exact_match':delta is not None and event_net is not None and delta==event_net,
      'in_count':len(ins['logs']),'out_count':len(outs['logs']),
      'state_ok':before.get('ok') and after.get('ok'),'logs_ok':ins['ok'] and outs['ok'],
      'receipts':{'before_sha256':before.get('raw_sha256'),'after_sha256':after.get('raw_sha256'),'in_sha256':ins.get('sha256'),'out_sha256':outs.get('sha256')}
    }

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    provider_state={}
    for name,url in PROVIDERS.items():
        provider_state[name]={}
        for label,(a,b) in WINDOWS.items():
            provider_state[name][label]={'before':basket_balance(url,a-1),'after':basket_balance(url,b)}
    cross_provider=True
    for label in WINDOWS:
        d=provider_state['drpc'][label]; t=provider_state['tenderly'][label]
        if not(d['before']['ok'] and d['after']['ok'] and t['before']['ok'] and t['after']['ok']): cross_provider=False
        if d['before'].get('total_raw')!=t['before'].get('total_raw') or d['after'].get('total_raw')!=t['after'].get('total_raw'): cross_provider=False
    reconciliations={label:window_recon(PROVIDERS['drpc'],a,b) for label,(a,b) in WINDOWS.items()}
    equivalence=all(x['exact_match'] and x['state_ok'] and x['logs_ok'] for x in reconciliations.values())
    cls='BALANCE_TRANSFER_RECON_PASS' if cross_provider and equivalence else 'BALANCE_TRANSFER_RECON_FAIL'
    compact_state={}
    for pn,labels in provider_state.items():
        compact_state[pn]={}
        for label,ends in labels.items():
            compact_state[pn][label]={side:{k:v for k,v in obj.items() if k!='balances'} for side,obj in ends.items()}
    receipt={
      'lab_id':'STABLECOIN-EXCHANGE-FLOW-001','mve_id':'SEF-BINANCE-PUBLIC-USDT-ETH-1D-001','classification':cls,
      'cross_provider_state_exact_match':cross_provider,'transfer_state_equivalence_exact_match':equivalence,
      'providers':PROVIDERS,'windows':WINDOWS,'state_receipts':compact_state,'reconciliations':reconciliations,
      'measurement_identity':'sum(balanceOf basket)_b - sum(balanceOf basket)_(a-1) == inbound Transfer value - outbound Transfer value',
      'access_2025':False,'access_2026':False,'btc_market_data_accessed':False,'returns_computed':False,'pnl_computed':False,
    }
    (OUT/'BALANCE_TRANSFER_RECON_RECEIPT.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0
if __name__=='__main__': raise SystemExit(main())

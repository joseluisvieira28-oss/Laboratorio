#!/usr/bin/env python3
"""SQD filtered factory creation archive. No state/code prerequisite, no prices."""
import json
import time
import concurrent.futures as cf
from tmfcb_keccak import keccak
from tmfcb_v04_sources import fetch, TOKENS, FACTORY, PAIR, OUT, load_constant

URL = 'https://portal.sqd.dev/datasets/ethereum-mainnet/finalized-stream'
QUOTES = load_constant('tmfcb_v03_dex_factory_probe.py','QUOTES')
PAD = lambda a:'0x'+'0'*24+a[2:].lower()

def query(start,end,factory=FACTORY,event=PAIR):
    # Select only factory creation events, never token Transfer or pool Swap logs.
    addresses = [PAD(a) for a in TOKENS.values()]
    quotes = [PAD(a) for a in QUOTES.values()]
    return {'type':'evm','fromBlock':start,'toBlock':end,
      'fields':{'block':{'number':True,'hash':True,'timestamp':True},
                'log':{'address':True,'topics':True,'data':True,'transactionHash':True,'logIndex':True}},
      'logs':[{'address':[factory],'topic0':[event],'topic1':addresses,'topic2':quotes},
              {'address':[factory],'topic0':[event],'topic1':quotes,'topic2':addresses}]}

def scan_range(start,end,factory,event):
    pages=[]; creations=[]; cursor=start
    while cursor<=end:
        q=query(cursor,end,factory,event)
        for attempt in range(3):
            reply=fetch(URL,q)
            if reply['status']==200: break
            time.sleep(0.5*(attempt+1))
        raw=reply.pop('body',None)
        reply.update(start=cursor,end=end,query=q)
        pages.append(reply)
        if raw is None: return pages,creations,False
        blocks=[json.loads(line) for line in raw.splitlines() if line.strip()]
        if not blocks: return pages,creations,False
        for b in blocks:
            if 'error' in b: raise ValueError(b)
            h=b['header']
            if not cursor<=h['number']<=end: raise ValueError('range mismatch')
            if h['timestamp']>=1767225600: raise ValueError('2026 boundary violation')
            for log in b.get('logs',[]):
                if log['address'].lower()!=factory or log['topics'][0]!=event: raise ValueError('log allowlist violation')
                t0,t1=['0x'+t[-40:] for t in log['topics'][1:3]]
                if not ({t0,t1}&set(a.lower() for a in TOKENS.values())): raise ValueError('token mismatch')
                if not ({t0,t1}&set(a.lower() for a in QUOTES.values())): raise ValueError('quote mismatch')
                data=log['data'][2:]
                if len(data)!=128: raise ValueError('creation ABI length')
                is_v2=event==PAIR
                pool='0x'+(data[24:64] if is_v2 else data[88:128])
                creations.append({'block':h['number'],'blockHash':h['hash'],'timestamp':h['timestamp'],
                  'factory':factory,'token0':t0,'token1':t1,'pool':pool,
                  'fee':None if is_v2 else int(log['topics'][3],16),
                  'transactionHash':log['transactionHash'],'logIndex':log['logIndex']})
        last=blocks[-1]['header']['number']
        reply['processed_through']=last
        cursor=last+1
    return pages,creations,True

def main():
    # Replaced preliminary transport-EOF accounting: always paginate by header.
    assert keccak(b'PairCreated(address,address,address,uint256)')==PAIR
    factories=[(FACTORY,PAIR,10000835),('0x1f98431c8ad98523631ae4a59f267346ea31f984',
               keccak(b'PoolCreated(address,address,uint24,int24,address)'),12369621)]
    path=OUT/'factory_archive_paginated.json'
    result={'source':URL,'tokens':TOKENS,'quotes':QUOTES,'bounds_end':24000000,
            'scope':'creation metadata only; no assertion of liquidity or trading','ranges':[],
            'creations':[],'complete':False}
    jobs=[(s,min(s+999999,24000000),f,e) for f,e,begin in factories
          for s in range(begin,24000001,1000000)]
    with cf.ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(scan_range,*j):j for j in jobs}
        for future in cf.as_completed(futures):
            j=futures[future]
            try:
                pages,records,complete=future.result()
                result['ranges'].append({'from':j[0],'to':j[1],'factory':j[2],
                                         'complete':complete,'pages':pages})
                result['creations'].extend(records)
            except Exception as exc:
                result['ranges'].append({'from':j[0],'to':j[1],'factory':j[2],
                                         'complete':False,'error':str(exc)})
            result['creations'].sort(key=lambda x:(x['block'],x['logIndex']))
            path.write_text(json.dumps(result,indent=2),encoding='utf-8')
            print(json.dumps({'finished':len(result['ranges']),'total':len(jobs),
                             'creations':len(result['creations'])}),flush=True)
    result['complete']=all(r['complete'] for r in result['ranges'])
    path.write_text(json.dumps(result,indent=2),encoding='utf-8')

if __name__=='__main__': main()

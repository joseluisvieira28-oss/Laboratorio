"""Verify first-party preidentified deployment receipts and historical headers."""
import concurrent.futures as cf
import json
from tmfcb_v04_sources import fetch, TXS, OUT

TARGETS=dict(TXS)
TARGETS.update(POL_TOKEN_DEPLOY='0x2a88c595a815c6aac8bf6734ee12d939c7d0dce8965771330b72f2ebc3d673bd',
               POL_MIGRATOR_PROXY_DEPLOY='0x352acb72eddab7b1d810af8823b8ff22de00a3fcbb0c270870b0fa3834230752')
EPS=['https://ethereum-rpc.publicnode.com','https://cloudflare-eth.com']

def call(ep,method,params):
    rec=fetch(ep,{'jsonrpc':'2.0','id':1,'method':method,'params':params})
    raw=rec.pop('body',None); value=None
    if raw:
        parsed=json.loads(raw)
        rec['rpc_error']=parsed.get('error')
        value=parsed.get('result')
    rec.update(endpoint=ep,method=method,params=params)
    return rec,value

def verify(label,tx):
    row={'label':label,'preidentified_tx':tx,'receipts':[],'headers':[],'sqd_headers':[]}
    for ep in EPS:
        rec,value=call(ep,'eth_getTransactionReceipt',[tx])
        if value:
            rec['metadata']={k:value.get(k) for k in ['transactionHash','blockNumber','blockHash','status','contractAddress']}
            # Never inspect or retain receipt.logs.
        row['receipts'].append(rec)
    good=[r['metadata'] for r in row['receipts'] if r.get('metadata')]
    if not good: return row
    bn=int(good[0]['blockNumber'],16)
    for ep in ['https://ethereum-rpc.publicnode.com','https://1rpc.io/eth']:
        rec,b=call(ep,'eth_getBlockByNumber',[hex(bn),False])
        if b:
            if int(b['timestamp'],16)>=1767225600: raise ValueError('outside historical scope')
            rec['metadata']={k:b.get(k) for k in ['number','hash','timestamp']}
        row['headers'].append(rec)
    q={'type':'evm','fromBlock':bn,'toBlock':bn,'includeAllBlocks':True,
       'fields':{'block':{'number':True,'hash':True,'timestamp':True}}}
    rec=fetch('https://portal.sqd.dev/datasets/ethereum-mainnet/finalized-stream',q)
    raw=rec.pop('body',None)
    if raw: rec['metadata']=[json.loads(line)['header'] for line in raw.splitlines()]
    rec['query']=q; row['sqd_headers'].append(rec)
    headers=[r['metadata'] for r in row['headers'] if r.get('metadata')]
    row['receipt_matches_headers']=bool(headers) and all(r['blockHash']==h['hash'] for r in good for h in headers)
    row['deployment_not_automatically_activation']=True
    return row

def main():
    with cf.ThreadPoolExecutor(max_workers=3) as pool:
        result=list(pool.map(lambda kv:verify(*kv),TARGETS.items()))
    (OUT/'verified_deployment_receipts.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps([{'label':r['label'],'verified':r.get('receipt_matches_headers',False)} for r in result]))

if __name__=='__main__':main()

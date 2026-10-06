#!/usr/bin/env python3
"""Configuration / public historical-state acquisition only. Never borrower outcomes."""
import concurrent.futures
import gzip
import hashlib
import json
import os
from pathlib import Path
import time
import urllib.request
from Crypto.Hash import keccak

LAB = 'AAVE-GOV-LT-FORCED-DELEVERAGING-001'
START_TS, END_TS = 1640995200, 1767225599
OUT = Path(os.environ.get('AAVE_SOURCE_OUT', 'out/aave_gov_lt_forced_deleveraging'))
OUT.mkdir(parents=True, exist_ok=True)
RECEIPTS = []
NETWORKS = [
 ('ethereum-mainnet', 'https://ethereum-rpc.publicnode.com', 1, '0x64b761d848206f447fe2dd461b0c635ec39ebb27', '0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2'),
 ('polygon-mainnet', 'https://polygon-bor-rpc.publicnode.com', 137, '0x8145edddf43f50276641b55bd3ad95944510021e', '0x794a61358d6845594f94dc1db02a252b5b4814ad'),
 ('avalanche-mainnet', 'https://avalanche-c-chain-rpc.publicnode.com', 43114, '0x8145edddf43f50276641b55bd3ad95944510021e', '0x794a61358d6845594f94dc1db02a252b5b4814ad'),
 ('arbitrum-one', 'https://arbitrum-one-rpc.publicnode.com', 42161, '0x8145edddf43f50276641b55bd3ad95944510021e', '0x794a61358d6845594f94dc1db02a252b5b4814ad'),
 ('optimism-mainnet', 'https://optimism-rpc.publicnode.com', 10, '0x8145edddf43f50276641b55bd3ad95944510021e', '0x794a61358d6845594f94dc1db02a252b5b4814ad'),
 ('base-mainnet', 'https://base-rpc.publicnode.com', 8453, '0x5731a04b1e775f0fdd454bf70f3335886e9a96be', '0xa238dd80c259a72e81d7e4664a9801593f98d1c5'),
]

def digest(b): return hashlib.sha256(b).hexdigest()
def sig(s):
 k = keccak.new(digest_bits=256); k.update(s.encode()); return '0x'+k.hexdigest()
def integer(x): return int(x,16) if isinstance(x,str) and x.startswith('0x') else int(x)

def post(url, body, timeout=35):
 raw_request = json.dumps(body, sort_keys=True).encode()
 record = {'url':url, 'request':body, 'request_sha256':digest(raw_request), 'observed_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 for attempt in range(2):
  try:
   req = urllib.request.Request(url, data=raw_request, headers={'Content-Type':'application/json','User-Agent':LAB+'/source-v01'})
   with urllib.request.urlopen(req, timeout=timeout) as response:
    raw = response.read(); record.update(status=response.status,response_sha256=digest(raw),bytes=len(raw),attempt=attempt+1)
   path=OUT/(record['response_sha256']+'.json.gz')
   path.write_bytes(gzip.compress(raw,mtime=0)); record['raw_file']=path.name
   RECEIPTS.append(record); return raw
  except Exception as e:
   record.update(error=type(e).__name__+': '+str(e),attempt=attempt+1)
   if attempt == 0: time.sleep(1)
 RECEIPTS.append(record); raise RuntimeError(record['error'])

def rpc(url, method, params):
 assert method in {'eth_chainId','eth_getBlockByNumber','eth_call','eth_getCode','eth_getTransactionReceipt','eth_getLogs'}
 if method == 'eth_getLogs': assert params[0]['toBlock'] not in {'latest','pending'}
 if method in {'eth_call','eth_getCode'}: assert params[-1] not in {'latest','pending'}
 obj=json.loads(post(url,{'jsonrpc':'2.0','id':1,'method':method,'params':params}))
 if obj.get('error'): raise RuntimeError(json.dumps(obj['error']))
 if obj.get('result') is None: raise RuntimeError('null RPC result')
 return obj['result']

def block(url, n):
 b=rpc(url,'eth_getBlockByNumber',[hex(n),False])
 # Timestamp-only boundary queries are not market/borrower outcomes.
 return {'number':integer(b['number']),'timestamp':integer(b['timestamp']),'hash':b['hash']}

def lower_bound(url, ts, high, low=0):
 while low < high:
  mid=(low+high)//2
  if block(url,mid)['timestamp'] < ts: low=mid+1
  else: high=mid
 return low

def capability(net):
 name,url,chain,config,pool=net
 result={'dataset':name,'rpc':url,'chain_id':chain,'configurator':config,'pool':pool,'status':'SOURCE_BLOCKED'}
 try:
  if integer(rpc(url,'eth_chainId',[])) != chain: raise RuntimeError('wrong chain')
  # Genesis pruning is irrelevant to the V3 deployment; do not require it.
  # Resolve timestamps using header-only search; never log/state outcomes from 2026.
  high={'ethereum-mainnet':27000000,'polygon-mainnet':100000000,'avalanche-mainnet':100000000,'arbitrum-one':700000000,'optimism-mainnet':180000000,'base-mainnet':60000000}[name]
  # Upper bound may not exist; historical sentinel estimates use December 2025
  # start, then expand header-only until the end date is bracketed.
  for _ in range(30):
   try: hb=block(url,high); break
   except RuntimeError: high=high*9//10
  else: raise RuntimeError('cannot bracket historical boundary')
  if hb['timestamp'] <= END_TS: raise RuntimeError('upper header does not bracket 2025 end')
  floor=16490000 if name=='ethereum-mainnet' else 0
  first=lower_bound(url,START_TS,high,floor); last=lower_bound(url,END_TS+1,high,floor)-1
  result['from_block']=first;result['through_block']=last
  result['first_header']=block(url,first);result['last_header']=block(url,last)
  assert START_TS <= result['first_header']['timestamp'] <= END_TS
  assert result['last_header']['timestamp'] <= END_TS
  result['boundary_status']='PASS'
  code=rpc(url,'eth_getCode',[config,hex(last)])
  if code=='0x':raise RuntimeError('canonical configurator absent at historical boundary')
  result['configurator_code_sha256']=digest(code.encode())
  # Protocol reserve enumeration only, not any borrower balance/HF/outcome.
  reserves=rpc(url,'eth_call',[{'to':pool,'data':sig('getReservesList()')[:10]},hex(last)])
  result['historical_reserves_abi_sha256']=digest(reserves.encode())
  if len(reserves)<130:raise RuntimeError('invalid historical reserves ABI')
  result['status']='HISTORICAL_PROTOCOL_RPC_CAPABILITY_PASS'
 except Exception as e:result['failure']=str(e)
 return result

def census(net, capability_result):
 name,url,chain,config,pool=net
 portal='https://portal.sqd.dev/datasets/'+name+'/stream'
 first,last=capability_result['from_block'],capability_result['through_block']
 topics=[sig(s) for s in ['CollateralConfigurationChanged(address,uint256,uint256,uint256)','EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)','EModeCategoryCollateralConfigUpdated(uint8,uint16,uint16,uint16)','EModeAssetCategoryChanged(address,uint8,uint8)','AssetCollateralInEModeChanged(address,uint8,bool)']]
 rows=[];seen=set();cursor=first;pages=[]
 while cursor<=last:
  stop=min(last,cursor+4999999)
  body={'type':'evm','fromBlock':cursor,'toBlock':stop,'fields':{'block':{'number':True,'timestamp':True,'hash':True},'log':{'address':True,'topics':True,'data':True,'transactionHash':True,'logIndex':True}},'logs':[{'address':[config],'topic0':topics}]}
  raw=post(portal,body,120); blocks=[json.loads(line) for line in raw.splitlines() if line.strip()]
  tail=None
  for obj in blocks:
   h=obj.get('header',obj.get('block',{}));bn=integer(h['number']);ts=integer(h['timestamp'])
   assert cursor<=bn<=stop and START_TS<=ts<=END_TS
   assert tail is None or bn>=tail
   tail=bn
   for log in obj.get('logs',[]):
    assert log['address'].lower()==config and log['topics'][0].lower() in topics
    key=(log['transactionHash'].lower(),integer(log['logIndex']));assert key not in seen;seen.add(key)
    row={'chain_id':chain,'block':bn,'timestamp':ts,'block_hash':h.get('hash'),**log};rows.append(row)
  # Sparse/partial responses continue after last returned header. Empty response
  # is accepted only as a completed exact bounded SQD query, and is recorded.
  pages.append({'from':cursor,'to':stop,'last_returned':tail,'raw_sha256':digest(raw)})
  cursor=(tail+1) if tail is not None else stop+1
  if len(pages)%20==0:print(json.dumps({'dataset':name,'covered':cursor-1,'logs':len(rows)}),flush=True)
 histories={}; decreases=[]
 for row in sorted(rows,key=lambda r:(r['block'],integer(r['logIndex']))):
  if row['topics'][0].lower()!=topics[0]:continue
  assert len(row['topics'])==2 and len(row['data'])==194
  asset='0x'+row['topics'][1][-40:].lower();w=[int(row['data'][2+i*64:2+(i+1)*64],16) for i in range(3)]
  previous=histories.get(asset); row.update(asset=asset,ltv=w[0],lt=w[1],bonus=w[2],previous_lt=previous)
  if previous is not None and w[1]<previous:decreases.append(row)
  histories[asset]=w[1]
 episodes=[]
 for row in sorted(decreases,key=lambda r:(r['timestamp'],r['block'],integer(r['logIndex']))):
  if not episodes or row['timestamp']-episodes[-1]['start']>86400:episodes.append({'start':row['timestamp'],'txs':[]})
  if row['transactionHash'] not in episodes[-1]['txs']:episodes[-1]['txs'].append(row['transactionHash'])
 result={'dataset':name,'covered_through_block':cursor-1,'configuration_log_count':len(rows),'base_lt_decrease_logs':len(decreases),'potential_24h_episodes':len(episodes),'accepted_governance_shocks':0,'governance_lineage_status':'NOT_YET_ADJUDICATED','emode_configuration_logs':sum(r['topics'][0].lower()!=topics[0] for r in rows),'pages':pages,'rows':rows,'decreases':decreases,'episodes':episodes,'status':'CONFIGURATION_CENSUS_COMPLETE_NOT_SOURCE_GATE_PASS'}
 (OUT/(name+'_configuration_census.json')).write_text(json.dumps(result,indent=2)+'\n')
 return {k:v for k,v in result.items() if k not in {'pages','rows','decreases','episodes'}}

def main():
 assert sig('')=='0xc5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470'
 results=[]
 for net in NETWORKS:
  cap=capability(net);print(json.dumps(cap),flush=True);results.append(cap)
  if cap.get('boundary_status')=='PASS':
   try:cap['census']=census(net,cap)
   except Exception as e:cap['census']={'status':'SOURCE_BLOCKED','failure':str(e)}
 receipt={'lab_id':LAB,'phase':'SOURCE_ONLY','classification':'SOURCE_BLOCKED','reason':'Historical governance linkage / pre-signal borrower reconstruction not yet proved; never infer NO_EDGE from acquisition failure.','freeze_commit':'54743a9200eac68c0348c280379d6bfc5c3b8ace','start_timestamp':START_TS,'end_timestamp':END_TS,'networks':results,'requests':RECEIPTS,'economic_outcomes_opened':0,'borrower_behavior_opened':False,'development_runs':0,'2026_outcomes_opened':False}
 (OUT/'SOURCE_PROBE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
 print(json.dumps({'classification':receipt['classification'],'networks':len(results),'requests':len(RECEIPTS),'development_runs':0}),flush=True)

if __name__=='__main__':main()

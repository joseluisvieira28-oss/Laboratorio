#!/usr/bin/env python3
"""Source transport remediation. Configuration only; borrower identity before signals."""
import gzip,hashlib,json,time,urllib.request,urllib.error
from pathlib import Path
from source_probe_v01 import sig
OUT=Path('out/aave_gov_lt_v02');OUT.mkdir(parents=True,exist_ok=True)
RECORDS=[]
CONFIG='0x64b761d848206f447fe2dd461b0c635ec39ebb27'
POOL='0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2'
TOPICS=[sig(s) for s in ['CollateralConfigurationChanged(address,uint256,uint256,uint256)','EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)','EModeCategoryCollateralConfigUpdated(uint8,uint16,uint16,uint16)','EModeAssetCategoryChanged(address,uint8,uint8)','AssetCollateralInEModeChanged(address,uint8,bool)']]
PROVIDERS=['https://eth.drpc.org','https://eth-mainnet.g.alchemy.com/public','https://ethereum-rpc.publicnode.com','https://ethereum.publicnode.com','https://ethereum.public.blockpi.network/v1/rpc/public']
def sha(b):return hashlib.sha256(b).hexdigest()
def save(): (OUT/'request_receipts.json').write_text(json.dumps(RECORDS,indent=2))
def request(url,body):
 raw=json.dumps(body,sort_keys=True).encode();r={'url':url,'request':body,'request_sha256':sha(raw),'observed_at':time.time()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,data=raw,headers={'Content-Type':'application/json','Accept-Encoding':'gzip'}),timeout=25) as response:
   data=response.read();r.update(status=response.status,headers=dict(response.headers))
   if response.headers.get('Content-Encoding')=='gzip':data=gzip.decompress(data)
 except urllib.error.HTTPError as e:data=e.read();r.update(status=e.code,headers=dict(e.headers))
 except Exception as e:r['error']=str(e);RECORDS.append(r);save();raise
 r['response_sha256']=sha(data);(OUT/(sha(data)+'.gz')).write_bytes(gzip.compress(data,mtime=0));RECORDS.append(r);save()
 if r['status']!=200:raise RuntimeError('HTTP '+str(r['status'])+' '+data.decode(errors='replace')[:700])
 return data
def rpc(url,method,params):
 assert method in {'eth_getLogs','eth_getBlockByNumber','eth_call'}
 if method=='eth_getLogs':assert int(params[0]['toBlock'],16)<=24136052
 if method=='eth_call':assert int(params[-1],16)<19620893
 d=json.loads(request(url,{'jsonrpc':'2.0','id':1,'method':method,'params':params}))
 if d.get('error'):raise RuntimeError(json.dumps(d['error']))
 if d.get('result') is None:raise RuntimeError('NULL_RESULT')
 return d['result']
def logs(url,a,b,address,topics):
 result=rpc(url,'eth_getLogs',[{'address':address,'fromBlock':hex(a),'toBlock':hex(b),'topics':topics}])
 for l in result:assert a<=int(l['blockNumber'],16)<=b and not l.get('removed',False)
 return result
r={'classification':'SOURCE_BLOCKED','economic_outcomes_opened':0,'development_runs':0,'2026_outcomes_opened':False,'providers':[]}
for url in PROVIDERS:
 p={'url':url}
 try:
  # Known configuration transaction neighborhood, not borrower behavior.
  p['configuration_probe']=logs(url,19526280,19526290,CONFIG,[TOPICS]);p['status']='LOG_CAPABILITY_PASS'
 except Exception as e:p.update(status='FAIL',failure=str(e))
 r['providers'].append(p);print(json.dumps(p),flush=True)
# Repair identity-log range limits, before all known 2024 source witnesses.
for url in PROVIDERS:
 try:
  found=[]
  for a in range(16498000,16500001,100):
   found=logs(url,a,min(a+99,16500000),POOL,[sig('Borrow(address,address,address,uint256,uint8,uint256,uint16)')])
   if found:break
  if not found:continue
  first=min(found,key=lambda l:(int(l['blockNumber'],16),int(l['logIndex'],16)))
  # Borrow onBehalfOf is indexed topic2, per canonical Aave ABI.
  user='0x'+first['topics'][2][-40:];arg=user[2:].zfill(64)
  getters={}
  for s in ['getUserAccountData(address)','getUserConfiguration(address)','getUserEMode(address)']:
   value=rpc(url,'eth_call',[{'to':POOL,'data':sig(s)[:10]+arg},hex(19620892)])
   getters[s]={'abi_sha256':sha(value.encode()),'length':len(value)}
  r['borrower_capability']={'status':'PRE_SIGNAL_GETTER_CAPABILITY_PASS_NOT_FULL_ENUMERATION','provider':url,'identity_log':first,'snapshot_block':19620892,'getters':getters};break
 except Exception as e:r.setdefault('borrower_failures',[]).append({'url':url,'failure':str(e)})
(OUT/'progress.json').write_text(json.dumps(r,indent=2))
# Configuration census Ethereum 2023–2025. Independent of outcomes.
working=[p['url'] for p in r['providers'] if p['status']=='LOG_CAPABILITY_PASS']
rows=[];coverage=[];cursor=16490000;terminal=24136052;window=100000
checkpoint_path=OUT/'configuration_checkpoint.json'
if checkpoint_path.exists():
 cached=json.loads(checkpoint_path.read_text());assert cached['terminal']==terminal
 rows=cached['rows'];coverage=cached['coverage'];cursor=cached['cursor']
started=time.monotonic()
while working and cursor<=terminal:
 stop=min(terminal,cursor+window-1);success=False
 for url in working:
  try:
   batch=logs(url,cursor,stop,CONFIG,[TOPICS]);rows.extend(batch)
   coverage.append({'from':cursor,'to':stop,'provider':url,'response_sha256':RECORDS[-1]['response_sha256']})
   cursor=stop+1;success=True;break
  except Exception as e:r.setdefault('census_failures',[]).append({'url':url,'from':cursor,'to':stop,'error':str(e)})
 if not success:
  if window>100:window=max(100,window//10);continue
  break
 checkpoint={'cursor':cursor,'terminal':terminal,'rows':rows,'coverage':coverage,'complete':cursor>terminal}
 (OUT/'configuration_checkpoint.json').write_text(json.dumps(checkpoint,indent=2));print(json.dumps({'cursor':cursor,'rows':len(rows),'window':window}),flush=True)
 # Bounded acquisition; checkpoint resumable, never mark uncovered suffix as zero.
 if len(coverage)>=1500 or time.monotonic()-started>600:break
r.update(configuration_complete=cursor>terminal,configuration_cursor=cursor,configuration_log_count=len(rows),fully_accepted_shocks=0)
(OUT/'SOURCE_REMEDIATION_RECEIPT.json').write_text(json.dumps(r,indent=2));save();print(json.dumps(r),flush=True)

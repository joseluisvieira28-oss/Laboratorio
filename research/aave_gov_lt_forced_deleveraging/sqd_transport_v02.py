#!/usr/bin/env python3
"""Independent public configuration transport probe. No borrower behavior."""
import json,gzip,hashlib,time,urllib.request,urllib.error
from pathlib import Path
from urllib.parse import urlparse
from source_probe_v01 import sig
OUT=Path('out/aave_sqd_v02');OUT.mkdir(parents=True,exist_ok=True)
records=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def req(url,body=None):
 r={'url':url,'request':body,'observed_at':time.time()}
 raw=None if body is None else json.dumps(body,sort_keys=True).encode()
 try:
  with urllib.request.urlopen(urllib.request.Request(url,data=raw,headers={'Content-Type':'application/json','Accept-Encoding':'gzip'}),timeout=30) as res:
   b=res.read();r.update(status=res.status,headers=dict(res.headers))
   if res.headers.get('Content-Encoding')=='gzip':b=gzip.decompress(b)
 except urllib.error.HTTPError as e:b=e.read();r.update(status=e.code,headers=dict(e.headers))
 except Exception as e:r['error']=str(e);records.append(r);raise
 r['response_sha256']=sha(b);(OUT/(sha(b)+'.gz')).write_bytes(gzip.compress(b,mtime=0));records.append(r)
 if r['status']!=200:raise RuntimeError(str(r['status'])+' '+b.decode(errors='replace')[:700])
 return b
config='0x64b761d848206f447fe2dd461b0c635ec39ebb27'
topics=[sig(s) for s in ['CollateralConfigurationChanged(address,uint256,uint256,uint256)','EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)','EModeCategoryCollateralConfigUpdated(uint8,uint16,uint16,uint16)','EModeAssetCategoryChanged(address,uint8,uint8)','AssetCollateralInEModeChanged(address,uint8,bool)']]
base={'type':'evm','fields':{'block':{'number':True,'timestamp':True,'hash':True},'log':{'address':True,'topics':True,'data':True,'transactionHash':True,'logIndex':True}},'logs':[{'address':[config],'topic0':topics}]}
result={'economic_outcomes_opened':0,'2026_outcomes_opened':False,'classification':'SOURCE_BLOCKED','probes':[]}
for mode in ['legacy_worker','portal_finalized']:
 cursor=21525891;last=24136052;rows=[];coverage=[];started=time.monotonic();p={'mode':mode}
 try:
  while cursor<=last and time.monotonic()-started<480:
   stop=min(last,cursor+74999);body={**base,'fromBlock':cursor,'toBlock':stop}
   if mode=='legacy_worker':
    url=req(f'https://v2.archive.subsquid.io/network/ethereum-mainnet/{cursor}/worker').decode().strip().strip('"')
    parsed=urlparse(url);assert parsed.scheme=='https' and (parsed.hostname.endswith('.sqd-archive.net') or parsed.hostname.endswith('.subsquid.io'))
    blocks=json.loads(req(url,body))
   else:
    raw=req('https://portal.sqd.dev/datasets/ethereum-mainnet/finalized-stream',body)
    blocks=[json.loads(line) for line in raw.splitlines() if line.strip()]
   if not blocks:raise RuntimeError('EMPTY_WITHOUT_TERMINAL_WITNESS')
   previous=cursor-1
   for b in blocks:
    h=b['header'];bn=int(h['number']);assert cursor<=bn<=stop and bn>=previous and int(h['timestamp'])<=1767225599;previous=bn
    for log in b.get('logs',[]):rows.append({'header':h,'log':log})
   coverage.append({'from':cursor,'requested_to':stop,'covered_to':previous,'sha256':records[-1]['response_sha256']});cursor=previous+1
   (OUT/(mode+'_checkpoint.json')).write_text(json.dumps({'cursor':cursor,'terminal':last,'rows':rows,'coverage':coverage},indent=2))
   print(json.dumps({'mode':mode,'cursor':cursor,'rows':len(rows)}),flush=True)
  p.update(complete=cursor>last,cursor=cursor,log_count=len(rows))
 except Exception as e:p.update(failure=str(e),cursor=cursor,log_count=len(rows),complete=False)
 result['probes'].append(p);print(json.dumps(p),flush=True)
 (OUT/'receipt.json').write_text(json.dumps({**result,'requests':records},indent=2))
 if p.get('complete'):break

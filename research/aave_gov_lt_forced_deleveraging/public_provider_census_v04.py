#!/usr/bin/env python3
"""Alternative documented public RPC providers. Historical configuration only."""
import json,gzip,hashlib,time,urllib.request,urllib.error
from pathlib import Path
OUT=Path('out/aave_public_v04');OUT.mkdir(parents=True,exist_ok=True)
URLS=['https://eth.llamarpc.com','https://rpc.flashbots.net/fast','https://rpc.mevblocker.io']
CONFIG='0x64b761d848206f447fe2dd461b0c635ec39ebb27';FIRST,LAST=21525891,24136052
records=[]
def sha(b):return hashlib.sha256(b).hexdigest()
def rpc(url,method,params):
 assert method in {'eth_chainId','eth_getLogs','eth_getBlockByNumber'}
 body={'jsonrpc':'2.0','id':1,'method':method,'params':params};raw=json.dumps(body,sort_keys=True).encode();r={'url':url,'request':body,'request_sha256':sha(raw),'observed_at':time.time()}
 try:
  with urllib.request.urlopen(urllib.request.Request(url,data=raw,headers={'Content-Type':'application/json'}),timeout=25) as res:data=res.read();r.update(status=res.status,headers=dict(res.headers))
 except urllib.error.HTTPError as e:data=e.read();r.update(status=e.code,headers=dict(e.headers))
 except Exception as e:r['failure']=str(e);records.append(r);raise
 r['response_sha256']=sha(data);(OUT/(sha(data)+'.gz')).write_bytes(gzip.compress(data,mtime=0));records.append(r)
 (OUT/'requests.json').write_text(json.dumps(records,indent=2))
 if r['status']!=200:raise RuntimeError('HTTP '+str(r['status'])+' '+data.decode(errors='replace')[:500])
 d=json.loads(data)
 if d.get('error'):raise RuntimeError(json.dumps(d['error']))
 if d.get('result') is None:raise RuntimeError('NULL_RESULT')
 return d['result']
def logs(url,a,b):
 rows=rpc(url,'eth_getLogs',[{'address':CONFIG,'fromBlock':hex(a),'toBlock':hex(b)}])
 assert isinstance(rows,list)
 for l in rows:assert a<=int(l['blockNumber'],16)<=b and l['address'].lower()==CONFIG and not l.get('removed',False)
 return rows
r={'classification':'SOURCE_BLOCKED','economic_outcomes_opened':0,'development_runs':0,'2026_outcomes_opened':False,'providers':[]}
for url in URLS:
 p={'url':url}
 try:
  assert int(rpc(url,'eth_chainId',[]),16)==1
  h=rpc(url,'eth_getBlockByNumber',[hex(19526281),False]);assert h['hash']=='0x11dbc5f5d0eeb564699d02cd290524b33103ced00a8001f138d020f208f52a3c'
  known=logs(url,19526280,19526290);assert known;p['anchor_log_count']=len(known)
  cursor=FIRST;rows=[];coverage=[];started=time.monotonic();window=10000
  while cursor<=LAST and time.monotonic()-started<900:
   stop=min(LAST,cursor+window-1)
   try:batch=logs(url,cursor,stop)
   except Exception as e:
    p.setdefault('acquisition_failures',[]).append({'from':cursor,'to':stop,'failure':str(e)})
    if 'range' in str(e).lower() and window>1000:window=1000;continue
    raise
   rows.extend(batch);coverage.append({'from':cursor,'to':stop,'response_sha256':records[-1]['response_sha256']});cursor=stop+1
   (OUT/'checkpoint.json').write_text(json.dumps({'provider':url,'from':FIRST,'terminal':LAST,'cursor':cursor,'rows':rows,'coverage':coverage},indent=2))
   print(json.dumps({'provider':url,'cursor':cursor,'rows':len(rows)}),flush=True);time.sleep(.25)
  p.update(configuration_complete=cursor>LAST,frontier=cursor-1,configuration_logs=len(rows))
 except Exception as e:p['failure']=str(e)
 r['providers'].append(p);(OUT/'RECEIPT.json').write_text(json.dumps(r,indent=2));print(json.dumps(p),flush=True)
 if p.get('configuration_complete'):break
(OUT/'requests.json').write_text(json.dumps(records,indent=2))

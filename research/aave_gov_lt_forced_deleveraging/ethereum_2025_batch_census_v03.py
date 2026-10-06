#!/usr/bin/env python3
"""Public RPC batching, preserving each 100-block request and exact receipts."""
import concurrent.futures,gzip,hashlib,json,time,urllib.request,urllib.error,threading
from pathlib import Path
OUT=Path('out/aave_batch_v03');OUT.mkdir(parents=True,exist_ok=True)
URL='https://eth-mainnet.g.alchemy.com/public';CONFIG='0x64b761d848206f447fe2dd461b0c635ec39ebb27';FIRST,LAST=21525891,24136052
lock=threading.Lock()
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 raw=json.dumps(body,sort_keys=True).encode();record={'request':body,'request_sha256':sha(raw),'observed_at':time.time()}
 try:
  with urllib.request.urlopen(urllib.request.Request(URL,data=raw,headers={'Content-Type':'application/json'}),timeout=30) as res:data=res.read();status=res.status;headers=dict(res.headers)
 except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:data=str(e).encode();status=0;headers={}
 digest=sha(data);(OUT/(digest+'.gz')).write_bytes(gzip.compress(data,mtime=0));record.update(status=status,headers=headers,response_sha256=digest)
 with lock:
  with (OUT/'requests.jsonl').open('a') as f:f.write(json.dumps(record)+'\n')
 if status!=200:raise RuntimeError(str(status)+' '+data.decode(errors='replace')[:500])
 return json.loads(data),digest
def body(ranges):return [{'jsonrpc':'2.0','id':a,'method':'eth_getLogs','params':[{'address':CONFIG,'fromBlock':hex(a),'toBlock':hex(b)}]} for a,b in ranges]
def validate(result,ranges):
 assert isinstance(result,list) and len(result)==len(ranges)
 by_id={x['id']:x for x in result};assert len(by_id)==len(ranges)
 rows=[]
 for a,b in ranges:
  d=by_id[a];assert not d.get('error') and isinstance(d.get('result'),list)
  for l in d['result']:
   assert a<=int(l['blockNumber'],16)<=b and l['address'].lower()==CONFIG and not l.get('removed',False)
   if 'blockTimestamp' in l:assert int(l['blockTimestamp'],16)<=1767225599
   rows.append(l)
 return rows
r={'classification':'SOURCE_BLOCKED','economic_outcomes_opened':0,'development_runs':0,'2026_outcomes_opened':False}
try:
 probes=[(19526280+i*100,19526379+i*100) for i in range(10)]
 response,digest=post(body(probes));validate(response,probes);r['batch_capability']='PASS_10_INDEPENDENT_100_BLOCK_REQUESTS'
 ranges=[(a,min(a+99,LAST)) for a in range(FIRST,LAST+1,100)]
 groups=[ranges[i:i+10] for i in range(0,len(ranges),10)]
 coverage=[];rows=[];started=time.monotonic()
 def one(group):
  result,digest=post(body(group));logs=validate(result,group)
  return {'from':group[0][0],'to':group[-1][1],'response_sha256':digest,'rows':logs}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  for offset in range(0,len(groups),100):
   for x in pool.map(one,groups[offset:offset+100]):coverage.append({k:v for k,v in x.items() if k!='rows'});rows.extend(x['rows'])
   cursor=FIRST
   for c in sorted(coverage,key=lambda x:x['from']):assert c['from']==cursor;cursor=c['to']+1
   r.update(contiguous_frontier=cursor-1,census_complete=cursor>LAST,configuration_logs=len(rows))
   (OUT/'configuration_checkpoint.json').write_text(json.dumps({'receipt':r,'coverage':coverage,'rows':rows},indent=2));print(json.dumps(r),flush=True)
   if time.monotonic()-started>1200:break
except Exception as e:r['failure']=str(e)
(OUT/'RECEIPT.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True)

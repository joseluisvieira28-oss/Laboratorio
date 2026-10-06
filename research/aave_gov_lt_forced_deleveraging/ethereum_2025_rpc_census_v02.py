#!/usr/bin/env python3
"""Bounded unauthenticated Ethereum 2025 configuration census. No outcomes."""
import concurrent.futures,gzip,hashlib,json,threading,time,urllib.request,urllib.error
from pathlib import Path
OUT=Path('out/aave_2025_rpc_v02');OUT.mkdir(parents=True,exist_ok=True)
URL='https://eth-mainnet.g.alchemy.com/public';ADDRESS='0x64b761d848206f447fe2dd461b0c635ec39ebb27'
FIRST,LAST=21525891,24136052
lock=threading.Lock();covered={};failures=[];started=time.monotonic()
def sha(b):return hashlib.sha256(b).hexdigest()
def one(a):
 b=min(a+99,LAST);path=OUT/f'range_{a}_{b}.json'
 if path.exists():
  cached=json.loads(path.read_text());assert cached['from']==a and cached['to']==b and cached['status']=='PASS'
  return cached
 body={'jsonrpc':'2.0','id':1,'method':'eth_getLogs','params':[{'address':ADDRESS,'fromBlock':hex(a),'toBlock':hex(b)}]}
 raw=json.dumps(body,sort_keys=True).encode()
 for attempt in range(4):
  receipt={'request':body,'request_sha256':sha(raw),'observed_at':time.time(),'attempt':attempt+1}
  try:
   with urllib.request.urlopen(urllib.request.Request(URL,data=raw,headers={'Content-Type':'application/json'}),timeout=20) as res:data=res.read();status=res.status;headers=dict(res.headers)
  except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
  except Exception as e:data=str(e).encode();status=0;headers={}
  digest=sha(data);(OUT/(digest+'.gz')).write_bytes(gzip.compress(data,mtime=0))
  receipt.update(status=status,response_sha256=digest,headers=headers)
  with lock:
   with (OUT/'requests.jsonl').open('a') as f:f.write(json.dumps(receipt)+'\n')
  try:
   obj=json.loads(data)
   if status!=200 or obj.get('error') or not isinstance(obj.get('result'),list):raise ValueError('INVALID_RESPONSE')
   rows=obj['result']
   for row in rows:assert a<=int(row['blockNumber'],16)<=b and row['address'].lower()==ADDRESS and not row.get('removed',False)
   r={'from':a,'to':b,'status':'PASS','rows':rows,'response_sha256':digest}
   path.write_text(json.dumps(r));return r
  except Exception:
   if status not in {0,429,500,502,503,504,529}:break
   try:delay=min(45,float(headers.get('Retry-After',2**attempt)))
   except ValueError:delay=2**attempt
   time.sleep(delay)
 return {'from':a,'to':b,'status':'FAIL','response_sha256':digest,'http_status':status}
def checkpoint():
 keys=sorted(covered);cursor=FIRST
 for a in keys:
  if a!=cursor:break
  cursor=covered[a]['to']+1
 result={'classification':'SOURCE_BLOCKED','scope':'CONFIGURATION_ONLY_NOT_COMPLETE_SOURCE_GATE','from':FIRST,'through':LAST,'contiguous_frontier':cursor-1,'completed_ranges':len(covered),'failed_ranges':len(failures),'configuration_logs':sum(len(r['rows']) for r in covered.values()),'census_complete':cursor>LAST,'economic_outcomes_opened':0,'development_runs':0,'2026_outcomes_opened':False,'failures':failures}
 (OUT/'CENSUS_RECEIPT.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
# Four outstanding requests; batches keep checkpoint bounded and stop on persistent failures.
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 for start in range(FIRST,LAST+1,50000):
  ranges=list(range(start,min(start+50000,LAST+1),100))
  for result in pool.map(one,ranges):
   if result['status']=='PASS':covered[result['from']]=result
   else:failures.append(result)
  checkpoint()
  if failures or time.monotonic()-started>1800:break
checkpoint()

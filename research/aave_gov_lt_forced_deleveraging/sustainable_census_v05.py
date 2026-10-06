#!/usr/bin/env python3
"""One-time, rate-controlled public configuration backfill. No outcomes."""
import json,gzip,hashlib,time,urllib.request,urllib.error
from pathlib import Path
OUT=Path('out/aave_sustainable_v05');OUT.mkdir(parents=True,exist_ok=True)
URL='https://eth-mainnet.g.alchemy.com/public';CONFIG='0x64b761d848206f447fe2dd461b0c635ec39ebb27'
cache=Path(__file__).parent/'source_cache/ETHEREUM_2025_CONTIGUOUS_PREFIX_V02.json'
seed=json.loads(cache.read_text());FIRST,LAST=seed['cursor'],seed['terminal'];cursor=FIRST;rows=list(seed['rows']);coverage=[];started=time.monotonic();last_request=0
r={'classification':'SOURCE_BLOCKED','scope':'CONFIGURATION_ACQUISITION_ONLY','source_gate_pass':False,'hypothesis_status':'NOT_TESTED','economic_outcomes_opened':0,'development_runs':0,'2026_outcomes_opened':False,'initial_prefix':seed['cursor']-1,'terminal':LAST}
def sha(b):return hashlib.sha256(b).hexdigest()
def save():
 r.update(contiguous_frontier=cursor-1,configuration_census_complete=cursor>LAST,configuration_log_count=len(rows),acquired_groups=len(coverage))
 (OUT/'checkpoint.json').write_text(json.dumps({'receipt':r,'seed':{k:v for k,v in seed.items() if k!='rows'},'coverage':coverage,'rows':rows},indent=2))
 (OUT/'RECEIPT.json').write_text(json.dumps(r,indent=2))
def post(body):
 global last_request
 time.sleep(max(0,.6-(time.monotonic()-last_request)));last_request=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode();rec={'request':body,'request_sha256':sha(raw),'observed_at':time.time()}
 try:
  with urllib.request.urlopen(urllib.request.Request(URL,data=raw,headers={'Content-Type':'application/json'}),timeout=30) as res:data=res.read();status=res.status;headers=dict(res.headers)
 except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:data=str(e).encode();status=0;headers={}
 digest=sha(data);(OUT/(digest+'.gz')).write_bytes(gzip.compress(data,mtime=0));rec.update(http_status=status,headers=headers,response_sha256=digest)
 with (OUT/'requests.jsonl').open('a') as f:f.write(json.dumps(rec)+'\n')
 if status==200:return json.loads(data),digest
 if status in {0,429,500,502,503,504,529}:return {'transient_http':status,'headers':headers},digest
 raise RuntimeError('NON_RETRYABLE_HTTP_'+str(status))
def group(a):
 ranges=[(x,min(x+99,LAST)) for x in range(a,min(a+200,LAST+1),100)]
 requests=[{'jsonrpc':'2.0','id':x,'method':'eth_getLogs','params':[{'address':CONFIG,'fromBlock':hex(x),'toBlock':hex(y)}]} for x,y in ranges]
 successful={};hashes=[];pending=requests
 for attempt in range(9):
  response,digest=post(pending);hashes.append(digest)
  if isinstance(response,dict) and 'transient_http' in response:
   try:delay=float(response['headers'].get('retry-after',response['headers'].get('Retry-After',min(45,2**attempt))))
   except ValueError:delay=min(45,2**attempt)
   time.sleep(min(45,max(1,delay)));continue
  if not isinstance(response,list):raise RuntimeError('BATCH_RESPONSE_NOT_ARRAY')
  by_id={x['id']:x for x in response};assert len(by_id)==len(pending)
  retry=[]
  for req in pending:
   d=by_id[req['id']]
   if d.get('error'):
    if d['error'].get('code') in {429,-32005}:retry.append(req);continue
    raise RuntimeError('NON_RETRYABLE_RPC_'+json.dumps(d['error']))
   logs=d.get('result');assert isinstance(logs,list)
   lo=int(req['params'][0]['fromBlock'],16);hi=int(req['params'][0]['toBlock'],16)
   for l in logs:
    assert lo<=int(l['blockNumber'],16)<=hi and l['address'].lower()==CONFIG and not l.get('removed',False)
    if 'blockTimestamp' in l:assert int(l['blockTimestamp'],16)<=1767225599
   successful[req['id']]=logs
  pending=retry
  if not pending:
   result=[]
   for lo,hi in ranges:result.extend(successful[lo])
   return ranges[-1][1],result,hashes
  time.sleep(min(45,2**attempt))
 raise RuntimeError('RATE_OR_TRANSPORT_EXHAUSTED_AFTER_9_BOUNDED_ATTEMPTS')
save()
try:
 while cursor<=LAST:
  if time.monotonic()-started>10800:raise RuntimeError('3_HOUR_ACQUISITION_BUDGET_CHECKPOINT_SAVED')
  end,batch,hashes=group(cursor);coverage.append({'from':cursor,'to':end,'response_sha256s':hashes});rows.extend(batch);cursor=end+1
  # Write durable working checkpoint after every group; upload on completion/failure.
  if len(coverage)%25==0:save()
  if len(coverage)%250==0:print(json.dumps(r),flush=True)
 save()
except Exception as e:r['acquisition_failure']=type(e).__name__+': '+str(e);save()
print(json.dumps(r),flush=True)

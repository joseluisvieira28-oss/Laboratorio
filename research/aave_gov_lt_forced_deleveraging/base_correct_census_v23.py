#!/usr/bin/env python3
"""SOURCE-ONLY corrected Base V3 PoolConfigurator census through 2025.

Official AaveV3Base.POOL_CONFIGURATOR = 0x5731a04B1E775f0fdd454Bf70f3335886e9A96be.
Deployment block = 2357134 (2023-08-08). Matrix shards are deterministic,
non-overlapping slices of [DEPLOY_BLOCK, terminal_2025].
No borrower/economic outcomes.
"""
import gzip,hashlib,json,os,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

SHARD=int(os.environ["SHARD"]); TOTAL=int(os.environ.get("TOTAL_SHARDS","16"))
DEPLOY_BLOCK=2357134
END_TS=1767225599
CONFIG="0x5731a04b1e775f0fdd454bf70f3335886e9a96be"
URLS=["https://base-rpc.publicnode.com","https://mainnet.base.org","https://base.drpc.org","https://1rpc.io/base"]
OUT=Path(f"out/aave_base_correct_v23_shard_{SHARD}");OUT.mkdir(parents=True,exist_ok=True)
last_request=0.0; endpoint_i=0

def topic(s):
 k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
TOPICS=[topic("CollateralConfigurationChanged(address,uint256,uint256,uint256)"),topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)"),topic("EModeAssetCategoryChanged(address,uint8,uint8)"),topic("Upgraded(address)")]
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body,url=None):
 global last_request,endpoint_i
 time.sleep(max(0,.08-(time.monotonic()-last_request)));last_request=time.monotonic()
 if url is None:
  url=URLS[endpoint_i%len(URLS)];endpoint_i+=1
 raw=json.dumps(body,sort_keys=True).encode();rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time(),"source_url":url}
 try:
  req=urllib.request.Request(url,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=45) as res:data=res.read();status=res.status;headers=dict(res.headers)
 except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:data=str(e).encode();status=0;headers={}
 h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
 rec.update(http_status=status,response_sha256=h,headers=headers)
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps(rec)+"\n")
 try:d=json.loads(data)
 except Exception:d={"transport_body":data.decode(errors="replace")}
 return d,h,status,headers,url

def rpc(method,params):
 last=None
 for attempt in range(20):
  d,h,status,headers,url=post({"jsonrpc":"2.0","id":1,"method":method,"params":params});last=(d,status,url)
  if status==200 and isinstance(d,dict) and d.get("result") is not None:return d["result"],h,url
  err=d.get("error",{}) if isinstance(d,dict) else {}
  if status not in {0,400,403,429,500,502,503,504,529} and err.get("code") not in {None,429,-32005,-32603,-32000}:raise RuntimeError("NON_RETRYABLE_"+json.dumps(last))
  time.sleep(min(10,.5*(attempt+1)))
 raise RuntimeError("RPC_EXHAUSTED_"+method+"_"+json.dumps(last))

latest,_,_=rpc("eth_blockNumber",[]);latest=int(latest,16)
lo,hi=DEPLOY_BLOCK,latest
while lo<hi:
 mid=(lo+hi+1)//2;b,_,_=rpc("eth_getBlockByNumber",[hex(mid),False]);ts=int(b["timestamp"],16)
 if ts<=END_TS:lo=mid
 else:hi=mid-1
LAST=lo
span=LAST-DEPLOY_BLOCK+1
FIRST=DEPLOY_BLOCK+(span*SHARD)//TOTAL
SHARD_LAST=DEPLOY_BLOCK+(span*(SHARD+1))//TOTAL-1
fh,_,_=rpc("eth_getBlockByNumber",[hex(FIRST),False]);lh,_,_=rpc("eth_getBlockByNumber",[hex(SHARD_LAST),False])
assert int(fh["number"],16)==FIRST and int(lh["number"],16)==SHARD_LAST
cursor=FIRST;coverage=[];rows=[];started=time.monotonic()
receipt={"classification":"SOURCE_GATE_PENDING","scope":"BASE_CORRECT_POOLCONFIGURATOR_2023_2025_SHARD","chain":"base","shard":SHARD,"total_shards":TOTAL,"official_configurator":CONFIG,"deployment_block":DEPLOY_BLOCK,"global_terminal":LAST,"first":FIRST,"terminal":SHARD_LAST,"source_gate_pass":False,"hypothesis_status":"NOT_TESTED","economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
def save():
 receipt.update(contiguous_frontier=cursor-1,coverage_complete=cursor>SHARD_LAST,intervals=len(coverage),event_count=len(rows))
 (OUT/"checkpoint.json").write_text(json.dumps({"receipt":receipt,"first_header":fh,"terminal_header":lh,"coverage":coverage,"rows":rows},indent=2)+"\n")
 (OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
def get_logs(a,b):
 last=None
 for attempt in range(20):
  body={"jsonrpc":"2.0","id":a,"method":"eth_getLogs","params":[{"address":CONFIG,"fromBlock":hex(a),"toBlock":hex(b),"topics":[TOPICS]}]}
  d,h,status,headers,url=post(body);last=(d,status,url,h)
  if status==200 and isinstance(d,dict) and isinstance(d.get("result"),list):
   logs=d["result"]
   for x in logs:assert a<=int(x["blockNumber"],16)<=b and x["address"].lower()==CONFIG and x["topics"][0] in TOPICS and not x.get("removed",False)
   return logs,[h],url
  err=d.get("error",{}) if isinstance(d,dict) else {}
  if b>a and (status in {0,400,403,413,429,500,502,503,504,529} or err):return None,[h],url
  if status in {0,400,403,413,429,500,502,503,504,529}:time.sleep(min(10,.5*(attempt+1)));continue
  raise RuntimeError("NON_RETRYABLE_LOG_"+json.dumps(last))
 raise RuntimeError("LOG_EXHAUSTED_"+json.dumps(last))
def scan(a,b):
 logs,hashes,url=get_logs(a,b)
 if logs is not None:return [(a,b,logs,hashes,url)]
 if a==b:raise RuntimeError("UNRESOLVED_SINGLE_BLOCK_"+str(a))
 m=(a+b)//2
 return scan(a,m)+scan(m+1,b)

save()
try:
 while cursor<=SHARD_LAST:
  if time.monotonic()-started>18000:raise RuntimeError("5_HOUR_BUDGET_CHECKPOINT_SAVED")
  target=min(cursor+99999,SHARD_LAST)
  parts=scan(cursor,target)
  for a,b,logs,hashes,url in parts:
   assert a==cursor;coverage.append({"from":a,"to":b,"response_sha256s":hashes,"source_url":url});rows.extend(logs);cursor=b+1
  if len(coverage)%25==0:save()
 save()
except Exception as e:
 receipt["acquisition_failure"]=type(e).__name__+": "+str(e);save()
print(json.dumps(receipt),flush=True)

#!/usr/bin/env python3
"""SOURCE-ONLY Optimism V3 PoolConfigurator 2025 extension after audited V11."""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak
OUT=Path("out/aave_optimism_2025_v24");OUT.mkdir(parents=True,exist_ok=True)
URLS=["https://mainnet.optimism.io"]
CONFIG="0x8145edddf43f50276641b55bd3ad95944510021e"
FIRST=130045412
END_TS=1767225599
last_request=0.0;endpoint_i=0
def topic(s):
 k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
TOPICS=[topic("CollateralConfigurationChanged(address,uint256,uint256,uint256)"),topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)"),topic("EModeAssetCategoryChanged(address,uint8,uint8)"),topic("Upgraded(address)")]
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request,endpoint_i
 time.sleep(max(0,.12-(time.monotonic()-last_request)));last_request=time.monotonic()
 url=URLS[endpoint_i%len(URLS)];endpoint_i+=1
 raw=json.dumps(body,sort_keys=True).encode();rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time(),"source_url":url}
 try:
  req=urllib.request.Request(url,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=45) as res:data=res.read();status=res.status;headers=dict(res.headers)
 except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:data=str(e).encode();status=0;headers={}
 h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0));rec.update(http_status=status,response_sha256=h,headers=headers)
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps(rec)+"\n")
 try:d=json.loads(data)
 except Exception:d={"transport_body":data.decode(errors="replace")}
 return d,h,status,url
def rpc(method,params):
 last=None
 for attempt in range(18):
  d,h,status,url=post({"jsonrpc":"2.0","id":1,"method":method,"params":params});last=(d,status,url)
  if status==200 and isinstance(d,dict) and d.get("result") is not None:return d["result"],h,url
  time.sleep(min(10,.5*(attempt+1)))
 raise RuntimeError("RPC_EXHAUSTED_"+method+"_"+json.dumps(last))
latest,_,_=rpc("eth_blockNumber",[]);latest=int(latest,16)
lo,hi=FIRST-1,latest
while lo<hi:
 mid=(lo+hi+1)//2;b,_,_=rpc("eth_getBlockByNumber",[hex(mid),False]);ts=int(b["timestamp"],16)
 if ts<=END_TS:lo=mid
 else:hi=mid-1
LAST=lo
prev,_,_=rpc("eth_getBlockByNumber",[hex(FIRST-1),False]);fh,_,_=rpc("eth_getBlockByNumber",[hex(FIRST),False]);lh,_,_=rpc("eth_getBlockByNumber",[hex(LAST),False])
assert int(prev["timestamp"],16)<=1735689599<int(fh["timestamp"],16)
cursor=FIRST;coverage=[];rows=[];started=time.monotonic()
receipt={"classification":"SOURCE_GATE_PENDING","scope":"OPTIMISM_V3_CONFIGURATOR_SOURCE_ONLY_2025_EXTENSION","chain":"optimism","configurator":CONFIG,"stitch_prev_block":FIRST-1,"first":FIRST,"terminal":LAST,"terminal_timestamp":int(lh["timestamp"],16),"source_gate_pass":False,"hypothesis_status":"NOT_TESTED","economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
def save():
 receipt.update(contiguous_frontier=cursor-1,coverage_complete=cursor>LAST,intervals=len(coverage),event_count=len(rows))
 (OUT/"checkpoint.json").write_text(json.dumps({"receipt":receipt,"prev_header":prev,"first_header":fh,"terminal_header":lh,"coverage":coverage,"rows":rows},indent=2)+"\n")
 (OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
def getlogs(a,b):
 last=None
 for attempt in range(18):
  body={"jsonrpc":"2.0","id":a,"method":"eth_getLogs","params":[{"address":CONFIG,"fromBlock":hex(a),"toBlock":hex(b),"topics":[TOPICS]}]}
  d,h,status,url=post(body);last=(d,status,url,h)
  if status==200 and isinstance(d,dict) and isinstance(d.get("result"),list):return d["result"],[h],url
  time.sleep(min(8,.4*(attempt+1)))
 if b>a:return None,[last[3]],last[2]
 raise RuntimeError("LOG_EXHAUSTED_"+json.dumps(last))
def scan(a,b):
 logs,hashes,url=getlogs(a,b)
 if logs is not None:return [(a,b,logs,hashes,url)]
 m=(a+b)//2
 return scan(a,m)+scan(m+1,b)
save()
try:
 while cursor<=LAST:
  if time.monotonic()-started>18000:raise RuntimeError("5_HOUR_BUDGET_CHECKPOINT_SAVED")
  # V11 acquisition empirically established stable historical log windows
  # around 10k-20k blocks on the canonical public Optimism RPC.
  target=min(cursor+9999,LAST)
  for a,b,logs,hashes,url in scan(cursor,target):
   assert a==cursor
   for x in logs:assert a<=int(x["blockNumber"],16)<=b and x["address"].lower()==CONFIG and x["topics"][0] in TOPICS and not x.get("removed",False)
   coverage.append({"from":a,"to":b,"response_sha256s":hashes,"source_url":url});rows.extend(logs);cursor=b+1
  if len(coverage)%25==0:save()
 save()
except Exception as e:
 receipt["acquisition_failure"]=type(e).__name__+": "+str(e);save()
print(json.dumps(receipt),flush=True)

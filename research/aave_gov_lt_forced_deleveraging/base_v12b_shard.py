#!/usr/bin/env python3
"""SOURCE-ONLY Base V3 configurator continuation shards after V12 checkpoint.

Each shard is a fixed, non-overlapping block interval. No economic outcomes.
"""
import gzip,hashlib,json,os,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

BOUNDS=[
 (8780000,11391687),
 (11391688,14003375),
 (14003376,16615063),
 (16615064,19226751),
 (19226752,21838439),
 (21838440,24450126),
]
SHARD=int(os.environ["SHARD"])
FIRST,LAST=BOUNDS[SHARD]
OUT=Path(f"out/aave_base_v12b_shard_{SHARD}"); OUT.mkdir(parents=True,exist_ok=True)
URL="https://mainnet.base.org"
CONFIG="0x8145edddf43f50276641b55bd3ad95944510021e"
last_request=0.0
def topic(s):
 k=keccak.new(digest_bits=256); k.update(s.encode()); return "0x"+k.hexdigest()
TOPICS=[
 topic("CollateralConfigurationChanged(address,uint256,uint256,uint256)"),
 topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)"),
 topic("EModeAssetCategoryChanged(address,uint8,uint8)"),
 topic("Upgraded(address)")
]
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request
 time.sleep(max(0,.12-(time.monotonic()-last_request)));last_request=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode();rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time()}
 try:
  req=urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=45) as res:data=res.read();status=res.status;headers=dict(res.headers)
 except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:data=str(e).encode();status=0;headers={}
 h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
 rec.update(http_status=status,response_sha256=h,headers=headers)
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps(rec)+"\n")
 try:d=json.loads(data)
 except Exception:d={"transport_body":data.decode(errors="replace")}
 return d,h,status,headers
def rpc(method,params):
 for attempt in range(14):
  d,h,status,headers=post({"jsonrpc":"2.0","id":1,"method":method,"params":params})
  if status==200 and isinstance(d,dict) and d.get("result") is not None:return d["result"],h
  err=d.get("error",{}) if isinstance(d,dict) else {}
  if status not in {0,429,500,502,503,504,529} and err.get("code") not in {None,429,-32005,-32603}:
   raise RuntimeError("NON_RETRYABLE_"+json.dumps(d))
  try:delay=float(headers.get("retry-after",headers.get("Retry-After",min(30,2**attempt))))
  except Exception:delay=min(30,2**attempt)
  time.sleep(min(30,max(.5,delay)))
 raise RuntimeError("RPC_EXHAUSTED_"+method)

first_header,_=rpc("eth_getBlockByNumber",[hex(FIRST),False])
last_header,_=rpc("eth_getBlockByNumber",[hex(LAST),False])
assert int(first_header["number"],16)==FIRST and int(last_header["number"],16)==LAST
cursor=FIRST;coverage=[];rows=[]
receipt={"classification":"SOURCE_GATE_PENDING","scope":"BASE_V3_CONFIGURATOR_V12B_CONTINUATION_SHARD","chain":"base","shard":SHARD,"first":FIRST,"terminal":LAST,"rpc_public_unauthenticated":URL,"configurator":CONFIG,"source_gate_pass":False,"hypothesis_status":"NOT_TESTED","economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
def save():
 receipt.update(contiguous_frontier=cursor-1,coverage_complete=cursor>LAST,intervals=len(coverage),event_count=len(rows))
 (OUT/"checkpoint.json").write_text(json.dumps({"receipt":receipt,"first_header":first_header,"terminal_header":last_header,"coverage":coverage,"rows":rows},indent=2)+"\n")
 (OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
save()
try:
 while cursor<=LAST:
  b=min(cursor+299,LAST)
  for attempt in range(12):
   body={"jsonrpc":"2.0","id":cursor,"method":"eth_getLogs","params":[{"address":CONFIG,"fromBlock":hex(cursor),"toBlock":hex(b),"topics":[TOPICS]}]}
   d,h,status,headers=post(body)
   if status==200 and isinstance(d,dict) and isinstance(d.get("result"),list):
    logs=d["result"]
    for x in logs:
     assert cursor<=int(x["blockNumber"],16)<=b and x["address"].lower()==CONFIG and x["topics"][0] in TOPICS and not x.get("removed",False)
    coverage.append({"from":cursor,"to":b,"response_sha256s":[h]});rows.extend(logs);cursor=b+1
    if len(coverage)%200==0:save()
    break
   if status in {0,429,500,502,503,504,529}:
    time.sleep(min(30,2**attempt));continue
   raise RuntimeError("NON_RETRYABLE_LOG_"+json.dumps(d))
  else:raise RuntimeError("LOG_EXHAUSTED")
 save()
except Exception as e:
 receipt["acquisition_failure"]=type(e).__name__+": "+str(e);save()
print(json.dumps(receipt),flush=True)

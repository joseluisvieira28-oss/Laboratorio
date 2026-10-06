#!/usr/bin/env python3
"""Sustainable public SOURCE-ONLY scan of pre-2025 eMode and proxy upgrade events."""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak
OUT=Path("out/aave_emode_v07");OUT.mkdir(parents=True,exist_ok=True)
URL="https://eth-mainnet.g.alchemy.com/public"
CONFIG="0x64b761d848206f447fe2dd461b0c635ec39ebb27"
LAST=21525890
def topic(sig):
 k=keccak.new(digest_bits=256);k.update(sig.encode());return "0x"+k.hexdigest()
TOPICS=[
 topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)"),
 topic("EModeAssetCategoryChanged(address,uint8,uint8)"),
 topic("Upgraded(address)")
]
last_request=0
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request
 time.sleep(max(0,.6-(time.monotonic()-last_request)));last_request=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode();rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time()}
 try:
  with urllib.request.urlopen(urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json"}),timeout=35) as res:data=res.read();status=res.status;headers=dict(res.headers)
 except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:data=str(e).encode();status=0;headers={}
 h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0));rec.update(http_status=status,response_sha256=h,headers=headers)
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps(rec)+"\n")
 if status==200:return json.loads(data),h,headers
 if status in {0,429,500,502,503,504,529}:return {"transient_http":status},h,headers
 raise RuntimeError("NON_RETRYABLE_HTTP_"+str(status))
def single(method,params):
 for attempt in range(9):
  d,h,headers=post({"jsonrpc":"2.0","id":1,"method":method,"params":params})
  if isinstance(d,dict) and "result" in d:return d["result"],h
  if isinstance(d,dict) and d.get("error",{}).get("code") not in {429,-32005,None}:raise RuntimeError("NON_RETRYABLE_RPC_"+json.dumps(d["error"]))
  try:delay=float(headers.get("retry-after",headers.get("Retry-After",min(45,2**attempt))))
  except ValueError:delay=min(45,2**attempt)
  time.sleep(min(45,max(1,delay)))
 raise RuntimeError("SINGLE_EXHAUSTED_"+method)
# First block at which the proxy address has code.
lo,hi=0,LAST
while lo<hi:
 mid=(lo+hi)//2
 code,_=single("eth_getCode",[CONFIG,hex(mid)])
 if code=="0x":lo=mid+1
 else:hi=mid
FIRST=lo
header,_=single("eth_getBlockByNumber",[hex(FIRST),False])
assert header and int(header["number"],16)==FIRST
cursor=FIRST;coverage=[];rows=[];started=time.monotonic()
receipt={"classification":"SOURCE_GATE_PENDING","scope":"PRE_2025_EMODE_AND_CONFIGURATOR_UPGRADE_SOURCE_ONLY","source_gate_pass":False,"hypothesis_status":"NOT_TESTED","first_code_block":FIRST,"terminal":LAST,"topics":TOPICS,"economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
def save():
 receipt.update(contiguous_frontier=cursor-1,coverage_complete=cursor>LAST,groups=len(coverage),event_count=len(rows))
 (OUT/"checkpoint.json").write_text(json.dumps({"receipt":receipt,"first_header":header,"coverage":coverage,"rows":rows},indent=2))
 (OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2))
def group(a):
 ranges=[(x,min(x+99,LAST)) for x in range(a,min(a+200,LAST+1),100)]
 req=[{"jsonrpc":"2.0","id":x,"method":"eth_getLogs","params":[{"address":CONFIG,"fromBlock":hex(x),"toBlock":hex(y),"topics":[TOPICS]}]} for x,y in ranges]
 pending=req;successful={};hashes=[]
 for attempt in range(9):
  d,h,headers=post(pending);hashes.append(h)
  if isinstance(d,dict) and "transient_http" in d:time.sleep(min(45,2**attempt));continue
  if not isinstance(d,list):raise RuntimeError("BATCH_RESPONSE_NOT_ARRAY")
  by={x["id"]:x for x in d};retry=[]
  for q in pending:
   x=by.get(q["id"])
   if x is None:raise RuntimeError("MISSING_BATCH_ID")
   if x.get("error"):
    if x["error"].get("code") in {429,-32005}:retry.append(q);continue
    raise RuntimeError("NON_RETRYABLE_RPC_"+json.dumps(x["error"]))
   logs=x.get("result");assert isinstance(logs,list)
   a0=int(q["params"][0]["fromBlock"],16);b0=int(q["params"][0]["toBlock"],16)
   for l in logs:
    assert a0<=int(l["blockNumber"],16)<=b0 and l["address"].lower()==CONFIG and l["topics"][0] in TOPICS and not l.get("removed",False)
   successful[q["id"]]=logs
  pending=retry
  if not pending:
   result=[]
   for a0,b0 in ranges:result.extend(successful[a0])
   return ranges[-1][1],result,hashes
  time.sleep(min(45,2**attempt))
 raise RuntimeError("RATE_OR_TRANSPORT_EXHAUSTED")
save()
try:
 while cursor<=LAST:
  if time.monotonic()-started>18000:raise RuntimeError("5_HOUR_BUDGET_CHECKPOINT_SAVED")
  end,batch,hashes=group(cursor);coverage.append({"from":cursor,"to":end,"response_sha256s":hashes});rows.extend(batch);cursor=end+1
  if len(coverage)%25==0:save()
  if len(coverage)%500==0:print(json.dumps(receipt),flush=True)
 save()
except Exception as e:receipt["acquisition_failure"]=type(e).__name__+": "+str(e);save()
print(json.dumps(receipt),flush=True)

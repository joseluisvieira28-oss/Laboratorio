#!/usr/bin/env python3
"""SOURCE-ONLY Polygon V3 configurator census through 2024-12-31."""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

OUT=Path("out/aave_polygon_v08"); OUT.mkdir(parents=True,exist_ok=True)
URL="https://polygon-bor-rpc.publicnode.com"
CONFIG="0x8145edddf43f50276641b55bd3ad95944510021e"
END_TS=1735689599
last_request=0

def topic(sig):
 k=keccak.new(digest_bits=256); k.update(sig.encode()); return "0x"+k.hexdigest()
TOPICS=[
 topic("CollateralConfigurationChanged(address,uint256,uint256,uint256)"),
 topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)"),
 topic("EModeAssetCategoryChanged(address,uint8,uint8)"),
 topic("Upgraded(address)")
]
def sha(b): return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request
 time.sleep(max(0,.35-(time.monotonic()-last_request))); last_request=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode()
 rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time()}
 try:
  req=urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=45) as res: data=res.read(); status=res.status; headers=dict(res.headers)
 except urllib.error.HTTPError as e: data=e.read(); status=e.code; headers=dict(e.headers)
 except Exception as e: data=str(e).encode(); status=0; headers={}
 h=sha(data); (OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
 rec.update(http_status=status,response_sha256=h,headers=headers)
 with (OUT/"requests.jsonl").open("a") as f: f.write(json.dumps(rec)+"\n")
 try: parsed=json.loads(data)
 except Exception: parsed={"transport_body":data.decode(errors="replace")}
 return parsed,h,status,headers

def rpc(method,params):
 for attempt in range(10):
  d,h,status,headers=post({"jsonrpc":"2.0","id":1,"method":method,"params":params})
  if status==200 and isinstance(d,dict) and "result" in d: return d["result"],h
  err=d.get("error",{}) if isinstance(d,dict) else {}
  if status not in {0,429,500,502,503,504,529} and err.get("code") not in {None,429,-32005,-32603}: raise RuntimeError("NON_RETRYABLE_"+json.dumps(d))
  try: delay=float(headers.get("retry-after",headers.get("Retry-After",min(45,2**attempt))))
  except Exception: delay=min(45,2**attempt)
  time.sleep(min(45,max(1,delay)))
 raise RuntimeError("RPC_EXHAUSTED_"+method)

latest,_=rpc("eth_blockNumber",[]); latest=int(latest,16)
# terminal is the greatest available block timestamped no later than 2024-12-31 23:59:59 UTC
lo,hi=0,latest
while lo<hi:
 mid=(lo+hi+1)//2; b,_=rpc("eth_getBlockByNumber",[hex(mid),False]); ts=int(b["timestamp"],16)
 if ts<=END_TS: lo=mid
 else: hi=mid-1
LAST=lo
# first block where the official address-book configurator proxy has code
lo,hi=0,LAST
while lo<hi:
 mid=(lo+hi)//2; code,_=rpc("eth_getCode",[CONFIG,hex(mid)])
 if code=="0x": lo=mid+1
 else: hi=mid
FIRST=lo
first_header,_=rpc("eth_getBlockByNumber",[hex(FIRST),False])
terminal_header,_=rpc("eth_getBlockByNumber",[hex(LAST),False])
assert int(first_header["number"],16)==FIRST and int(terminal_header["number"],16)==LAST

cursor=FIRST; coverage=[]; rows=[]; started=time.monotonic()
receipt={"classification":"SOURCE_GATE_PENDING","scope":"POLYGON_V3_CONFIGURATOR_SOURCE_ONLY_THROUGH_2024","source_gate_pass":False,"hypothesis_status":"NOT_TESTED","chain":"polygon","rpc_public_unauthenticated":URL,"configurator":CONFIG,"first_code_block":FIRST,"terminal":LAST,"terminal_timestamp":int(terminal_header["timestamp"],16),"topics":TOPICS,"economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
def save():
 receipt.update(contiguous_frontier=cursor-1,coverage_complete=cursor>LAST,intervals=len(coverage),event_count=len(rows))
 (OUT/"checkpoint.json").write_text(json.dumps({"receipt":receipt,"first_header":first_header,"terminal_header":terminal_header,"coverage":coverage,"rows":rows},indent=2))
 (OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2))

def get_logs(a,b):
 for attempt in range(10):
  body={"jsonrpc":"2.0","id":a,"method":"eth_getLogs","params":[{"address":CONFIG,"fromBlock":hex(a),"toBlock":hex(b),"topics":[TOPICS]}]}
  d,h,status,headers=post(body)
  if status==200 and isinstance(d,dict) and isinstance(d.get("result"),list):
   logs=d["result"]
   for x in logs:
    assert a<=int(x["blockNumber"],16)<=b and x["address"].lower()==CONFIG and x["topics"][0] in TOPICS and not x.get("removed",False)
   return logs,[h]
  err=d.get("error",{}) if isinstance(d,dict) else {}
  # deterministic range/size errors are resolved by bisection, never recorded as absence
  if b>a and (status in {400,413,429,500,502,503,504,529} or err): return None,[h]
  if status in {0,429,500,502,503,504,529}:
   time.sleep(min(45,2**attempt)); continue
  raise RuntimeError("NON_RETRYABLE_LOG_"+json.dumps(d))
 raise RuntimeError("LOG_EXHAUSTED")

def scan(a,b):
 logs,hashes=get_logs(a,b)
 if logs is not None: return [(a,b,logs,hashes)]
 if a==b: raise RuntimeError("UNRESOLVED_SINGLE_BLOCK_"+str(a))
 m=(a+b)//2
 return scan(a,m)+scan(m+1,b)

save()
try:
 while cursor<=LAST:
  if time.monotonic()-started>19800: raise RuntimeError("5_5_HOUR_BUDGET_CHECKPOINT_SAVED")
  target=min(cursor+19999,LAST)
  parts=scan(cursor,target)
  for a,b,logs,hashes in parts:
   assert a==cursor
   coverage.append({"from":a,"to":b,"response_sha256s":hashes}); rows.extend(logs); cursor=b+1
  if len(coverage)%20==0: save()
  if len(coverage)%250==0: print(json.dumps(receipt),flush=True)
 save()
except Exception as e:
 receipt["acquisition_failure"]=type(e).__name__+": "+str(e); save()
print(json.dumps(receipt),flush=True)

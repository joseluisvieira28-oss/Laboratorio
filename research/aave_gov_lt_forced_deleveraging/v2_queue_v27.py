#!/usr/bin/env python3
"""SOURCE-ONLY Aave Governance V2 ProposalQueued proof for AIP-233 and AIP-288."""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak
OUT=Path("out/aave_v2_queue_v27");OUT.mkdir(parents=True,exist_ok=True)
URLS=["https://eth-mainnet.g.alchemy.com/public","https://ethereum-rpc.publicnode.com"]
GOV="0xec568fffba86c094cf06b22134b23074dfe2252c"
TARGETS={233:1685127000,288:1691510400}
last=0.;idx=0
def sig(s):
 k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
TOP=sig("ProposalQueued(uint256,uint256,address)")
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 global last,idx
 time.sleep(max(0,.12-(time.monotonic()-last)));last=time.monotonic()
 url=URLS[idx%len(URLS)];idx+=1
 raw=json.dumps(body,sort_keys=True).encode()
 try:
  req=urllib.request.Request(url,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=30) as res:data=res.read();status=res.status
 except urllib.error.HTTPError as e:data=e.read();status=e.code
 except Exception as e:data=str(e).encode();status=0
 h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps({"request":body,"url":url,"http_status":status,"response_sha256":h})+"\n")
 try:d=json.loads(data)
 except Exception:d={}
 return d,status
def rpc(method,params):
 for a in range(16):
  d,s=post({"jsonrpc":"2.0","id":1,"method":method,"params":params})
  if s==200 and d.get("result") is not None:return d["result"]
  time.sleep(min(5,.3*(a+1)))
 raise RuntimeError("RPC_EXHAUSTED_"+method)
def block_ts(n):
 b=rpc("eth_getBlockByNumber",[hex(n),False]);return int(b["timestamp"],16)
def block_at(ts):
 latest=int(rpc("eth_blockNumber",[]),16);lo,hi=16000000,latest
 while lo<hi:
  m=(lo+hi)//2
  if block_ts(m)<ts:lo=m+1
  else:hi=m
 return lo
rows=[]
for pid,approx in TARGETS.items():
 center=block_at(approx);found=[]
 # Scan +/- ~2 days in 100-block chunks; never accept provider error as absence.
 a=max(0,center-15000);z=center+15000
 while a<=z:
  b=min(a+99,z)
  q={"address":GOV,"fromBlock":hex(a),"toBlock":hex(b),"topics":[TOP]}
  try:logs=rpc("eth_getLogs",[q])
  except Exception:a=b+1;continue
  for l in logs:
   data=l["data"];proposal_id=int(data[2:66],16)
   if proposal_id==pid:
    execution_time=int(data[66:130],16)
    bn=int(l["blockNumber"],16);bh=rpc("eth_getBlockByNumber",[hex(bn),False])
    found.append({"proposal_id":pid,"queue_block":bn,"queue_timestamp":int(bh["timestamp"],16),"execution_time":execution_time,"queue_tx":l["transactionHash"],"log_index":int(l["logIndex"],16),"log":l})
  a=b+1
 row={"proposal_id":pid,"status":"PASS" if len(found)==1 else "SOURCE_BLOCKED","matches":found}
 rows.append(row);print(json.dumps({k:v for k,v in row.items() if k!="matches"}),flush=True)
receipt={"phase":"V2_PROPOSAL_QUEUE_SOURCE_ONLY","rows":rows,"all_unique":all(r["status"]=="PASS" for r in rows),"source_gate_pass":False,"hypothesis_status":"NOT_TESTED","economic_outcomes_opened":0,"development_runs":0}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")

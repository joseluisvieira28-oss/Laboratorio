#!/usr/bin/env python3
"""SOURCE-ONLY Optimism governance lineage probe for V11 candidate effects.

Discovers PayloadsController from PayloadExecuted(uint40) in each effect receipt,
then proves pre-effect queue state/log and immutable action target code hashes.
No borrower behaviour or economic outcomes are opened.
"""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

OUT=Path("out/aave_optimism_gov_v14"); OUT.mkdir(parents=True,exist_ok=True)
URL="https://mainnet.optimism.io"
CANDIDATES=[
"0x01580a23128ee97fdf9ddfc442ff65b5972c1f84952c7bafd213354cedde8d56",
"0x22c2eb7b02ae215657fdccfc4d923b78dc035eefa85d23950c8074fc925d9444",
"0x32d60434b74e59c69ecf7a06d38b67527245aff9c2e5eef7e3bc5da3e30fbac9",
"0x367cce6e426cdc69a071afeff846189b69db43f101163fb2710399f51c40d3f4",
"0x50097b7a4ae1464f7c78b3be86da487b15a4aa8f9e7b95784844a4c279145b1d",
"0x6d6f4750a7109b7322de3782ffdd6f7e6a99a079242a7929481802f7094a026f",
"0x99af268f6b4145c78bc2239bb21e84e196638704ad9a3a15dd808742535bd485",
"0xa8ecf8b94a86aac1e68db482e01282cc4e66a051cc7c97d816ed293443db9538",
"0xf646ec46e06384edbed76231bbb0fb92ea4d5de33f083079721684ca14047a50",
]
last_request=0.0
def ksig(s):
 k=keccak.new(digest_bits=256); k.update(s.encode()); return "0x"+k.hexdigest()
T_EXEC=ksig("PayloadExecuted(uint40)")
T_QUEUE=ksig("PayloadQueued(uint40)")
SEL_GET=ksig("getPayloadById(uint40)")[:10]

def sha(b): return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request
 time.sleep(max(0,.30-(time.monotonic()-last_request))); last_request=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode(); rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time()}
 try:
  req=urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=45) as res: data=res.read(); status=res.status; headers=dict(res.headers)
 except urllib.error.HTTPError as e: data=e.read(); status=e.code; headers=dict(e.headers)
 except Exception as e: data=str(e).encode(); status=0; headers={}
 h=sha(data); (OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
 rec.update(http_status=status,response_sha256=h,headers=headers)
 with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps(rec)+"\n")
 try: parsed=json.loads(data)
 except Exception: parsed={"transport_body":data.decode(errors="replace")}
 return parsed,h,status,headers

def rpc(method,params):
 for attempt in range(12):
  d,h,status,headers=post({"jsonrpc":"2.0","id":1,"method":method,"params":params})
  if status==200 and isinstance(d,dict) and "result" in d and d["result"] is not None:return d["result"],h
  err=d.get("error",{}) if isinstance(d,dict) else {}
  if status not in {0,429,500,502,503,504,529} and err.get("code") not in {None,429,-32005,-32603}:
   raise RuntimeError("NON_RETRYABLE_"+json.dumps(d))
  time.sleep(min(30,2**attempt))
 raise RuntimeError("RPC_EXHAUSTED_"+method)
def word(data,i): return int(data[2+i*64:2+(i+1)*64],16)
def block(n):
 b,_=rpc("eth_getBlockByNumber",[hex(n),False])
 return {"number":int(b["number"],16),"timestamp":int(b["timestamp"],16),"hash":b["hash"]}
def lower_bound_ts(ts,hi):
 lo=0
 while lo<hi:
  m=(lo+hi)//2; b,_=rpc("eth_getBlockByNumber",[hex(m),False])
  if int(b["timestamp"],16)<ts:lo=m+1
  else:hi=m
 return lo

rows=[]
for tx in CANDIDATES:
 row={"effect_tx":tx,"status":"SOURCE_BLOCKED","economic_outcomes_opened":0}
 try:
  rcpt,_=rpc("eth_getTransactionReceipt",[tx])
  assert rcpt and int(rcpt["status"],16)==1
  bn=int(rcpt["blockNumber"],16); hdr=block(bn)
  row["effect_block"]=bn; row["effect_header"]=hdr
  exec_logs=[l for l in rcpt["logs"] if l.get("topics") and l["topics"][0].lower()==T_EXEC]
  if len(exec_logs)!=1: raise RuntimeError("NO_UNIQUE_PAYLOAD_EXECUTED_IN_EFFECT_TX")
  ex=exec_logs[0]; controller=ex["address"].lower()
  if len(ex.get("topics",[]))>1: pid=int(ex["topics"][1],16)
  else: pid=word(ex["data"],0)
  row["payload_controller"]=controller; row["payload_id"]=pid; row["payload_executed_log"]=ex
  data,_=rpc("eth_call",[{"to":controller,"data":SEL_GET+format(pid,"064x")},hex(bn-1)])
  off=word(data,0)//32
  state=word(data,off+2); queued=word(data,off+4)
  row["pre_effect_payload_state_raw"]=state; row["queued_at"]=queued
  if not (queued>0 and queued<hdr["timestamp"]): raise RuntimeError("NO_PRE_EFFECT_QUEUE_TIMESTAMP")
  qb=lower_bound_ts(queued,bn)
  qhdr=block(qb)
  if qhdr["timestamp"]!=queued: raise RuntimeError("QUEUE_TIMESTAMP_NOT_EXACT_BLOCK_TIMESTAMP")
  qlogs,_=rpc("eth_getLogs",[{"address":controller,"fromBlock":hex(qb),"toBlock":hex(qb),"topics":[T_QUEUE]}])
  matches=[]
  for l in qlogs:
   try:
    qpid=int(l["topics"][1],16) if len(l.get("topics",[]))>1 else word(l["data"],0)
    if qpid==pid: matches.append(l)
   except Exception: pass
  if len(matches)!=1: raise RuntimeError("NO_UNIQUE_PAYLOAD_QUEUED_LOG")
  row["payload_queue_block"]=qb; row["payload_queue_header"]=qhdr; row["payload_queued_log"]=matches[0]
  # Decode action array using the same PayloadsController struct semantics already source-probed on Ethereum.
  arr_word=off+word(data,off+10)//32
  count=word(data,arr_word)
  if not (0<count<100): raise RuntimeError("INVALID_ACTION_COUNT")
  targets=[]
  for i in range(count):
   action_word=arr_word+1+word(data,arr_word+1+i)//32
   target="0x"+format(word(data,action_word),"040x")
   code,_=rpc("eth_getCode",[target,hex(qb)])
   if code=="0x": raise RuntimeError("EMPTY_ACTION_TARGET_CODE")
   targets.append({"target":target,"queued_code_sha256":sha(code.encode())})
  row["targets"]=targets
  row["signal_to_effect_seconds"]=hdr["timestamp"]-queued
  row["governance_lineage_status"]="PAYLOAD_QUEUE_EXECUTION_LINK_PASS"
  row["parameters_known_at_signal_status"]="TARGET_BYTECODE_HASHED_EXACT_PARAMETER_REPRODUCTION_PENDING"
  row["status"]="GOVERNANCE_LINEAGE_PARTIAL_PASS_PARAMETERS_PENDING"
 except Exception as e:
  row["failure"]=type(e).__name__+": "+str(e)
 rows.append(row); print(json.dumps(row),flush=True)

receipt={
 "lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001",
 "phase":"OPTIMISM_V14_GOVERNANCE_LINEAGE_SOURCE_ONLY",
 "candidate_count":len(CANDIDATES),
 "rows":rows,
 "payload_queue_execution_link_pass":sum(r.get("governance_lineage_status")=="PAYLOAD_QUEUE_EXECUTION_LINK_PASS" for r in rows),
 "fully_source_gated_independent_shocks":0,
 "source_gate_pass":False,
 "hypothesis_status":"NOT_TESTED",
 "economic_outcomes_opened":0,
 "development_runs":0,
 "outcomes_2026_opened":False
}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k!="rows"}),flush=True)

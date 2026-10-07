#!/usr/bin/env python3
"""SOURCE-ONLY Optimism governance lineage probe for the 9 V11 candidate effect txs."""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

OUT=Path("out/aave_optimism_governance_v14"); OUT.mkdir(parents=True,exist_ok=True)
URL="https://mainnet.optimism.io"
PC="0x0E1a3Af1f9cC76A62eD31eDedca291E63632e7c4".lower()
CANDIDATES=[
 (102694765,"0x01580a23128ee97fdf9ddfc442ff65b5972c1f84952c7bafd213354cedde8d56"),
 (112700259,"0x50097b7a4ae1464f7c78b3be86da487b15a4aa8f9e7b95784844a4c279145b1d"),
 (113767094,"0x367cce6e426cdc69a071afeff846189b69db43f101163fb2710399f51c40d3f4"),
 (115861036,"0x22c2eb7b02ae215657fdccfc4d923b78dc035eefa85d23950c8074fc925d9444"),
 (118593699,"0xa8ecf8b94a86aac1e68db482e01282cc4e66a051cc7c97d816ed293443db9538"),
 (119445983,"0x32d60434b74e59c69ecf7a06d38b67527245aff9c2e5eef7e3bc5da3e30fbac9"),
 (119923657,"0x6d6f4750a7109b7322de3782ffdd6f7e6a99a079242a7929481802f7094a026f"),
 (121043649,"0x99af268f6b4145c78bc2239bb21e84e196638704ad9a3a15dd808742535bd485"),
 (126090941,"0xf646ec46e06384edbed76231bbb0fb92ea4d5de33f083079721684ca14047a50"),
]
last_request=0.0; receipts=[]
def sig(s):
 k=keccak.new(digest_bits=256); k.update(s.encode()); return "0x"+k.hexdigest()
def sha(b): return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request
 time.sleep(max(0,.25-(time.monotonic()-last_request))); last_request=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode()
 rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time()}
 try:
  req=urllib.request.Request(URL,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
  with urllib.request.urlopen(req,timeout=45) as res: data=res.read(); status=res.status; headers=dict(res.headers)
 except urllib.error.HTTPError as e: data=e.read(); status=e.code; headers=dict(e.headers)
 except Exception as e: data=str(e).encode(); status=0; headers={}
 h=sha(data); (OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
 rec.update(http_status=status,response_sha256=h,headers=headers); receipts.append(rec)
 try: parsed=json.loads(data)
 except Exception: parsed={"transport_body":data.decode(errors="replace")}
 return parsed,status,headers
def rpc(method,params):
 for a in range(12):
  d,status,h=post({"jsonrpc":"2.0","id":1,"method":method,"params":params})
  if status==200 and isinstance(d,dict) and "result" in d:return d["result"]
  if status in {0,429,500,502,503,504,529}: time.sleep(min(30,2**a)); continue
  raise RuntimeError(f"{method}:{status}:{d}")
 raise RuntimeError("RPC_EXHAUSTED_"+method)
def word(data,i): return int(data[2+i*64:2+(i+1)*64],16)
def lower_bound(ts,hi,lo):
 while lo<hi:
  m=(lo+hi)//2; b=rpc("eth_getBlockByNumber",[hex(m),False]); t=int(b["timestamp"],16)
  if t<ts: lo=m+1
  else: hi=m
 return lo

rows=[]
for bn,tx in CANDIDATES:
 row={"effect_block":bn,"effect_tx":tx,"status":"V2_OR_DIRECT_LINEAGE_PENDING"}
 try:
  hdr=rpc("eth_getBlockByNumber",[hex(bn),False]); row["effect_timestamp"]=int(hdr["timestamp"],16)
  logs=rpc("eth_getLogs",[{"address":PC,"fromBlock":hex(bn),"toBlock":hex(bn),"topics":[sig("PayloadExecuted(uint40)")]}])
  logs=[l for l in logs if l["transactionHash"].lower()==tx.lower()]
  row["payload_executed_logs"]=logs
  if len(logs)==0:
   row["reason"]="NO_V3_PAYLOAD_EXECUTED_LOG_IN_EFFECT_TX"
   rows.append(row); continue
  if len(logs)!=1: raise RuntimeError("AMBIGUOUS_PAYLOAD_EXECUTION_LOGS")
  # PayloadExecuted(uint40) is non-indexed in governance v3 deployment ABI.
  pid=word(logs[0]["data"],0); row["payload_id"]=pid
  call=sig("getPayloadById(uint40)")[:10]+format(pid,"064x")
  pdata=rpc("eth_call",[{"to":PC,"data":call},hex(bn-1)])
  off=word(pdata,0)//32
  state=word(pdata,off+2); queued_at=word(pdata,off+4)
  row.update(pre_effect_payload_state=state,queued_at=queued_at,pre_effect_payload_abi_sha256=sha(pdata.encode()))
  if not (queued_at>0 and queued_at<row["effect_timestamp"]): raise RuntimeError("QUEUE_TIMESTAMP_NOT_PRE_EFFECT")
  qb=lower_bound(queued_at,bn,max(0,bn-5000000))
  qh=rpc("eth_getBlockByNumber",[hex(qb),False])
  row["queue_block"]=qb; row["queue_block_timestamp"]=int(qh["timestamp"],16)
  qlogs=rpc("eth_getLogs",[{"address":PC,"fromBlock":hex(max(0,qb-2)),"toBlock":hex(qb+2),"topics":[sig("PayloadQueued(uint40)")]}])
  qlogs=[l for l in qlogs if len(l.get("data",""))>=66 and word(l["data"],0)==pid]
  row["payload_queued_logs"]=qlogs
  if len(qlogs)!=1: raise RuntimeError("NO_UNIQUE_PAYLOAD_QUEUED_LOG")
  # Recover action target bytecode hashes as immutable source witness.
  array_word=off+word(pdata,off+10)//32
  count=word(pdata,array_word)
  if not (0<count<100): raise RuntimeError("INVALID_ACTION_COUNT")
  targets=[]
  for i in range(count):
   action_word=array_word+1+word(pdata,array_word+1+i)//32
   target="0x"+format(word(pdata,action_word),"040x")
   code=rpc("eth_getCode",[target,hex(qb)])
   if code=="0x": raise RuntimeError("EMPTY_TARGET_CODE")
   targets.append({"target":target,"queued_code_sha256":sha(code.encode())})
  row.update(status="V3_PAYLOAD_QUEUE_EXECUTION_LINK_PASS",targets=targets,signal_to_effect_seconds=row["effect_timestamp"]-queued_at,
             parameters_known_at_signal_status="BYTECODE_RECOVERED_NOT_YET_SEMANTICALLY_REPRODUCED",
             core_proposal_approval_status="NOT_YET_PROVED")
 except Exception as e:
  row["status"]="SOURCE_PROBE_ERROR"; row["failure"]=type(e).__name__+": "+str(e)
 rows.append(row); print(json.dumps(row),flush=True)

receipt={
 "lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001",
 "phase":"OPTIMISM_GOVERNANCE_LINEAGE_SOURCE_ONLY",
 "candidate_count":len(CANDIDATES),
 "v3_link_pass":sum(r["status"]=="V3_PAYLOAD_QUEUE_EXECUTION_LINK_PASS" for r in rows),
 "v2_or_direct_pending":sum(r["status"]=="V2_OR_DIRECT_LINEAGE_PENDING" for r in rows),
 "probe_errors":sum(r["status"]=="SOURCE_PROBE_ERROR" for r in rows),
 "source_gate_pass":False,
 "hypothesis_status":"NOT_TESTED",
 "economic_outcomes_opened":0,
 "development_runs":0,
 "outcomes_2026_opened":False,
 "rows":rows,
 "requests":receipts,
}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in {"rows","requests"}},indent=2))

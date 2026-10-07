#!/usr/bin/env python3
"""SOURCE-ONLY Optimism governance V2 lineage for the lone V11 legacy eMode candidate."""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

OUT=Path("out/aave_optimism_gov_v141"); OUT.mkdir(parents=True,exist_ok=True)
URL="https://mainnet.optimism.io"
EFFECT_TX="0x01580a23128ee97fdf9ddfc442ff65b5972c1f84952c7bafd213354cedde8d56"
EFFECT_BLOCK=102694765
EXECUTOR="0x7d9103572be58ffe99dc390e8246f02dcae6f611"
ACTION_ID=18
last_request=0.0
def sig(s):
 k=keccak.new(digest_bits=256); k.update(s.encode()); return "0x"+k.hexdigest()
T_EXEC=sig("ActionsSetExecuted(uint256,address,bytes[])")
T_QUEUE=sig("ActionsSetQueued(uint256,address[],uint256[],string[],bytes[],bool[],uint256)")
SEL_GET=sig("getActionsSetById(uint256)")[:10]
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request
 time.sleep(max(0,.30-(time.monotonic()-last_request)));last_request=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode(); rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time()}
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
 for attempt in range(12):
  d,h,status,headers=post({"jsonrpc":"2.0","id":1,"method":method,"params":params})
  if status==200 and isinstance(d,dict) and "result" in d and d["result"] is not None:return d["result"],h
  err=d.get("error",{}) if isinstance(d,dict) else {}
  if status not in {0,429,500,502,503,504,529} and err.get("code") not in {None,429,-32005,-32603}:raise RuntimeError("NON_RETRYABLE_"+json.dumps(d))
  time.sleep(min(30,2**attempt))
 raise RuntimeError("RPC_EXHAUSTED_"+method)
def header(bn):
 b,_=rpc("eth_getBlockByNumber",[hex(bn),False]);return {"number":int(b["number"],16),"timestamp":int(b["timestamp"],16),"hash":b["hash"]}
def logs_range(a,b):
 body={"jsonrpc":"2.0","id":a,"method":"eth_getLogs","params":[{"address":EXECUTOR,"fromBlock":hex(a),"toBlock":hex(b),"topics":[T_QUEUE,"0x"+format(ACTION_ID,"064x")]}]}
 d,h,status,headers=post(body)
 if status==200 and isinstance(d,dict) and isinstance(d.get("result"),list):return d["result"],[h]
 if a<b:return None,[h]
 raise RuntimeError("UNRESOLVED_SINGLE_BLOCK")
def scan(a,b):
 x,hs=logs_range(a,b)
 if x is not None:return [(a,b,x,hs)]
 m=(a+b)//2
 return scan(a,m)+scan(m+1,b)
row={"effect_tx":EFFECT_TX,"effect_block":EFFECT_BLOCK,"executor":EXECUTOR,"action_set_id":ACTION_ID,"status":"SOURCE_BLOCKED"}
try:
 receipt,_=rpc("eth_getTransactionReceipt",[EFFECT_TX])
 assert receipt and int(receipt["status"],16)==1
 ex=[l for l in receipt["logs"] if l["address"].lower()==EXECUTOR and l.get("topics") and l["topics"][0].lower()==T_EXEC and int(l["topics"][1],16)==ACTION_ID]
 assert len(ex)==1
 row["actions_set_executed_log"]=ex[0]
 # Search ~12 days of Optimism blocks; bisection handles provider range limits.
 start=max(0,EFFECT_BLOCK-550000)
 parts=scan(start,EFFECT_BLOCK-1)
 qs=[l for _,_,ls,_ in parts for l in ls]
 assert len(qs)==1
 q=qs[0]; qb=int(q["blockNumber"],16); qh=header(qb); eh=header(EFFECT_BLOCK)
 row["queue_block"]=qb; row["queue_header"]=qh; row["actions_set_queued_log"]=q
 row["queue_to_effect_seconds"]=eh["timestamp"]-qh["timestamp"]
 data,_=rpc("eth_call",[{"to":EXECUTOR,"data":SEL_GET+format(ACTION_ID,"064x")},hex(EFFECT_BLOCK-1)])
 row["pre_effect_actions_set_abi"]=data
 row["pre_effect_actions_set_abi_sha256"]=sha(data.encode())
 row["queue_event_data_sha256"]=sha(q["data"].encode())
 row["governance_lineage_status"]="V2_ACTIONSET_QUEUE_EXECUTION_LINK_PASS"
 row["parameters_known_at_queue_status"]="EXACT_QUEUE_EVENT_AND_PRE_EFFECT_ACTIONSET_ABI_RECOVERED_DECODE_PENDING"
 row["status"]="V2_GOVERNANCE_LINEAGE_PASS_PARAMETER_DECODE_PENDING"
except Exception as e:
 row["failure"]=type(e).__name__+": "+str(e)
receipt={"lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001","phase":"OPTIMISM_V14_1_GOVERNANCE_V2_SOURCE_ONLY","row":row,"source_gate_pass":False,"hypothesis_status":"NOT_TESTED","fully_source_gated_independent_shocks":0,"economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({**row,"pre_effect_actions_set_abi":row.get("pre_effect_actions_set_abi","")[:80]+"..."},flush=True))

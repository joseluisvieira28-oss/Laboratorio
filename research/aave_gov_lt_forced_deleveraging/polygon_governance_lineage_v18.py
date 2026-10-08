#!/usr/bin/env python3
"""SOURCE-ONLY Polygon governance lineage multi-endpoint transport remediation for provisional LT-decrease effects.

No borrower behaviour, economic outcomes, 2026 data, trading, or account access.
"""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

CHAINS={
 "polygon":{
  "url":"https://polygon-bor-rpc.publicnode.com",
  "candidates":[
   (43299439,"0x83afad9ff0c38534100b1a4626f99642d4250e93c04cd289b240c6768c4fe0c9"),
   (44972774,"0x4fcbf9258c3932cf76d36c83f052f9330c51cffd361ebc66151491481c5f8978"),
   (46180710,"0x8d128ca9c637576b6a0d967da565cff139a492a749108fed2ac35f4e9bf888a9"),
   (48845916,"0xa76d93fba3c709b11fdde86b1b1b92ac0b47ec978083414987218b1618e93d1d"),
   (50127249,"0x02efe2f6e301c2169f94218b338bdcaead73e2bc0bd039c9c440ae50edc5a251"),
   (50411394,"0x00bf99a3ba3b014a7753157eb633a54f17bf128c067ba883f10789aabc6c7d2f"),
   (50416783,"0x567d257898d99fed55a7c5b69771545f4f8452211f0fefc4e2cc0797f38389df"),
   (51373556,"0x4a68392fa153577d9c6a0580979c426bb708448d2c7d1f92b847e6b294cbdef2"),
   (55141862,"0x57e0f344b2922a31be65d520024d21ced0ff75f520e528805c600c357381317b"),
   (55679336,"0x632883fea7ce5790141cf187beda7181c7029c780bbe3beef30dcea5b78fbdb5"),
   (56426011,"0x71bf17962248f4a406c1b3cbb6b927391504832774f1a9175368bc706a977b09"),
   (56849317,"0x07eaf8fcfbb4a34bf3bbfb50de2116785eba6d74d5a2ac96a55f85d07fa15e98"),
   (68798642,"0xd99064b3668c92d453973ffa84cb56fd52fcc8720aae853f247fb00a853371ae"),
   (77674570,"0xaf73caa4050d0abf0a8b9bb0cb6b37b8c9ac74e1196a352a3e71d4d7e707ccb4"),
  ]},
 "avalanche":{
  "url":"https://api.avax.network/ext/bc/C/rpc",
  "candidates":[
   (33330336,"0x11e9651b84a651b1ce435447ab73e79a8ec2a3504deab4c27ec76678579c02fb"),
   (38264532,"0x59b8f6193d7aa5442fcff2ec739ac6355a6b78a0084be7156229f049f9738329"),
   (40310604,"0xce6ac8064744d211867be08855d0e66860a55875afe185ef79cd511d4f476d59"),
   (41287931,"0xa384379aea3b70bf3f56c3bafc01d8c0fa0464207367fd21135352ba65b320d7"),
   (43442632,"0xa3c46c26959c03b46a0937a91c6650cb9e12ee7ca05119786ae2216db4b721c5"),
   (44040670,"0x5cc4982eb7025f24d16f15adc99bf06d553e43d6b7b69ee96a0707d7fdd4db6f"),
   (44859561,"0x5e11d89fd7bb790e4eef4c39936abf490aa1fe23fb5818684bfe69b3b0f01104"),
   (45313008,"0xb15cb870965d67987456f2cc9f022b9487ca21e2648fefce4c4ad7bbf577d80a"),
   (51225548,"0xbf97694ed5c2e26b9f95bbf49b892e2cbef9b40e5011cd44d6e4c2a8122ea624"),
  ]},
 "arbitrum":{
  "url":"https://arb1.arbitrum.io/rpc",
  "candidates":[
   (95752233,"0x62124c8c75643d3d65cc7001628ee29eb13c5e8d3b25b51b79d9601b423224d3"),
   (154570606,"0xf6b23f657ee1c9981f70de679b94774c32ad21a000bbfbbc88a56339125bfaa5"),
   (162197166,"0xf36d02fe4f8e52681e96c2fc7893821be6bcd38859354dc0c69a860cf090eae3"),
   (194779349,"0x76a5cc2c78abb8823eb43e38ec1951d4b48e225e61e5407c18b1b9ca5077478d"),
   (199697258,"0xb91c08b19b5c0bbbfe1218bcdf9f86d90a44a185bc2f9b1570a5b2cbd1340bb9"),
   (206419712,"0x9313ad46a6ff44a55b43108a48508f29a9976858856e2005108fb0d60156d523"),
   (210212730,"0xded61a74f3a8fb11441dc68cadc53afd51afca41bbe31abeca9c8ccc5dbd2c26"),
   (259245043,"0x5c5186993fe7cbc0e3c4390c75745a01058db0cc32a9417d950db0863fbb550c"),
  ]},
}
import os
CHAIN=os.environ["CHAIN"]
URLS=[CHAINS[CHAIN]["url"],"https://polygon.drpc.org","https://1rpc.io/matic","https://polygon-mainnet.public.blastapi.io"]; CANDIDATES=CHAINS[CHAIN]["candidates"]
OUT=Path(f"out/aave_{CHAIN}_governance_v18"); OUT.mkdir(parents=True,exist_ok=True)
last_request=0.0
endpoint_i=0

def sig(s):
 k=keccak.new(digest_bits=256); k.update(s.encode()); return "0x"+k.hexdigest()
T_PAYLOAD_EXEC=sig("PayloadExecuted(uint40)")
T_PAYLOAD_QUEUE=sig("PayloadQueued(uint40)")
T_V2_EXEC=sig("ActionsSetExecuted(uint256,address,bytes[])")
SEL_GET_PAYLOAD=sig("getPayloadById(uint40)")[:10]
def sha(b):return hashlib.sha256(b).hexdigest()
def post(body):
 global last_request,endpoint_i
 time.sleep(max(0,.25-(time.monotonic()-last_request)));last_request=time.monotonic()
 url=URLS[endpoint_i%len(URLS)]; endpoint_i+=1
 raw=json.dumps(body,sort_keys=True).encode(); rec={"request":body,"request_sha256":sha(raw),"observed_at":time.time(),"source_url":url}
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
 return d,status,headers
def rpc(method,params):
 for attempt in range(12):
  d,status,headers=post({"jsonrpc":"2.0","id":1,"method":method,"params":params})
  if status==200 and isinstance(d,dict) and d.get("result") is not None:
   result=d["result"]
   if method=="eth_getTransactionReceipt" and not isinstance(result,dict):
    time.sleep(1); continue
   return result
  err=d.get("error",{}) if isinstance(d,dict) else {}
  if status not in {0,429,500,502,503,504,529} and err.get("code") not in {None,429,-32005,-32603}:
   raise RuntimeError("NON_RETRYABLE_"+json.dumps(d))
  time.sleep(min(30,2**attempt))
 raise RuntimeError("RPC_EXHAUSTED_"+method)
def word(data,i):return int(data[2+i*64:2+(i+1)*64],16)
def header(n):
 b=rpc("eth_getBlockByNumber",[hex(n),False])
 return {"number":int(b["number"],16),"timestamp":int(b["timestamp"],16),"hash":b["hash"]}
def lower_bound_ts(ts,hi):
 lo=max(0,hi-10000000)
 while lo<hi:
  m=(lo+hi)//2;b=rpc("eth_getBlockByNumber",[hex(m),False]);t=int(b["timestamp"],16)
  if t<ts:lo=m+1
  else:hi=m
 return lo

rows=[]
for bn,tx in CANDIDATES:
 row={"chain":CHAIN,"effect_block":bn,"effect_tx":tx,"status":"UNRESOLVED"}
 try:
  rcpt=rpc("eth_getTransactionReceipt",[tx]); assert rcpt and int(rcpt["status"],16)==1
  actual_bn=int(rcpt["blockNumber"],16); assert actual_bn==bn
  eh=header(bn); row["effect_timestamp"]=eh["timestamp"]
  p=[l for l in rcpt["logs"] if l.get("topics") and l["topics"][0].lower()==T_PAYLOAD_EXEC]
  if len(p)==1:
   ex=p[0]; controller=ex["address"].lower()
   pid=int(ex["topics"][1],16) if len(ex["topics"])>1 else word(ex["data"],0)
   row.update(governance_version="V3",payload_controller=controller,payload_id=pid,payload_executed_log=ex)
   pdata=rpc("eth_call",[{"to":controller,"data":SEL_GET_PAYLOAD+format(pid,"064x")},hex(bn-1)])
   off=word(pdata,0)//32; queued=word(pdata,off+4)
   if not (0<queued<eh["timestamp"]):raise RuntimeError("INVALID_PRE_EFFECT_QUEUE_TIMESTAMP")
   qb=lower_bound_ts(queued,bn); qh=header(qb)
   qlogs=rpc("eth_getLogs",[{"address":controller,"fromBlock":hex(max(0,qb-2)),"toBlock":hex(qb+2),"topics":[T_PAYLOAD_QUEUE]}])
   matches=[]
   for l in qlogs:
    try:
     qpid=int(l["topics"][1],16) if len(l.get("topics",[]))>1 else word(l["data"],0)
     if qpid==pid:matches.append(l)
    except:pass
   if len(matches)!=1:raise RuntimeError("NO_UNIQUE_PAYLOAD_QUEUE_LOG")
   arr=off+word(pdata,off+10)//32; count=word(pdata,arr)
   if not (0<count<100):raise RuntimeError("INVALID_ACTION_COUNT")
   targets=[]
   for i in range(count):
    aw=arr+1+word(pdata,arr+1+i)//32
    target="0x"+format(word(pdata,aw),"040x")
    code=rpc("eth_getCode",[target,hex(qb)])
    if code=="0x":raise RuntimeError("EMPTY_TARGET_CODE")
    targets.append({"target":target,"queued_code_sha256":sha(code.encode())})
   row.update(status="V3_QUEUE_EXECUTION_LINK_PASS",queued_at=queued,queue_block=qb,queue_timestamp=qh["timestamp"],
              signal_to_effect_seconds=eh["timestamp"]-queued,targets=targets,
              pre_effect_payload_abi_sha256=sha(pdata.encode()),exact_parameter_semantics_status="PENDING")
  else:
   v2=[l for l in rcpt["logs"] if l.get("topics") and l["topics"][0].lower()==T_V2_EXEC]
   if len(v2)==1:
    ex=v2[0]; aid=int(ex["topics"][1],16) if len(ex["topics"])>1 else word(ex["data"],0)
    row.update(governance_version="V2",executor=ex["address"].lower(),action_set_id=aid,
               actions_set_executed_log=ex,status="V2_EXECUTION_IDENTIFIED_QUEUE_PENDING")
   elif len(p)>1 or len(v2)>1:
    raise RuntimeError("AMBIGUOUS_GOVERNANCE_EXECUTION_LOG")
   else:
    row.update(status="NO_V3_OR_V2_EXECUTION_LOG_DIRECT_OR_OTHER_GOVERNANCE_PENDING")
 except Exception as e:
  row.update(status="SOURCE_PROBE_ERROR",failure=type(e).__name__+": "+str(e))
 rows.append(row);print(json.dumps(row),flush=True)

receipt={"lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001","phase":"POLYGON_GOVERNANCE_LINEAGE_V18_SOURCE_ONLY_MULTI_ENDPOINT_REMEDIATION",
 "chain":CHAIN,"candidate_count":len(rows),
 "v3_queue_execution_pass":sum(r["status"]=="V3_QUEUE_EXECUTION_LINK_PASS" for r in rows),
 "v2_execution_identified":sum(r["status"]=="V2_EXECUTION_IDENTIFIED_QUEUE_PENDING" for r in rows),
 "other_pending":sum(r["status"]=="NO_V3_OR_V2_EXECUTION_LOG_DIRECT_OR_OTHER_GOVERNANCE_PENDING" for r in rows),
 "probe_errors":sum(r["status"]=="SOURCE_PROBE_ERROR" for r in rows),
 "rows":rows,"source_gate_pass":False,"hypothesis_status":"NOT_TESTED",
 "fully_source_gated_independent_shocks":0,"economic_outcomes_opened":0,"development_runs":0,"outcomes_2026_opened":False}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k!="rows"},indent=2),flush=True)

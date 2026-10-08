#!/usr/bin/env python3
"""V35 SOURCE-ONLY on-chain Governance V3 Core queue receipt proof.

No borrower/economic outcomes. Verifies exact queued tx, GovernanceCore address,
ProposalQueued event/proposal id, successful receipt and block timestamp.
"""
import gzip,hashlib,json,time,urllib.error,urllib.request
from pathlib import Path
from Crypto.Hash import keccak

OUT=Path("out/aave_v3_core_queue_v35"); OUT.mkdir(parents=True,exist_ok=True)
URLS=["https://eth.drpc.org","https://ethereum-rpc.publicnode.com","https://rpc.flashbots.net"]
GOV="0x9aee0b04504cef83a65ac3f0e838d0593bcb2bc7"
ROWS=[
 (2,"0x57ba1ce62cae8f6e88a22b52d483803d38b7e225123dc2ee3d0315de8f3182a7",1705064471),
 (13,"0xd106f25ccc4c1cacc516d7dcc2f185ac3cb661ffc1d16dbb963861a308098b17",1707063383),
 (19,"0xa8424567c0c8da1684c9cb6ac2fba1da3c7f40ed3e0da6c931c991b9d3c239e0",1707234251),
 (55,"0xad1a5a3ad9c739b29d4abd598c8b87b3cd2096c3cb1732927b11bfcc419d84ef",1711407887),
 (71,"0x64f3e6585deac72933910502858606539c9fa224bb8509feb716781c5e5e7e07",1712699675),
 (87,"0x81c43e43e4346eddf9136857aee12efee8c4f0f8ea5fa0f424056cef55b3f6f8",1714404251),
 (100,"0x729a25004a2438496983bdb50e71a0354baa7615fb8ace3a9996121efec75b5c",1715359595),
 (114,"0x455e2220b4a2fce8cb3bf35ffddf7ed215732cc33a3e56343b312008fd668dd5",1717599515),
 (173,"0xf225096abe61536e2d7968606a83ff7e31d8f165b07a23723d2ea0a0d54c6ea7",1727694107),
 (256,"0x1ddf8cbb221410d26e6bdf0b7fe7c77a3917be1bd74639af4fc1e06e32b69e7a",1740918695),
 (260,"0xe94964608c66e1fce64b56d211fd5c76039ed70424f945b4e066a379bd08caed",1741354031),
]
def sig(s):
 k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
TOPIC=sig("ProposalQueued(uint256,uint128,uint128)")
def sha(b):return hashlib.sha256(b).hexdigest()
last=0.0;idx=0
def post(body):
 global last,idx
 time.sleep(max(0,.1-(time.monotonic()-last)));last=time.monotonic()
 raw=json.dumps(body,sort_keys=True).encode(); attempts=[]
 for _ in range(len(URLS)*3):
  url=URLS[idx%len(URLS)];idx+=1
  try:
   req=urllib.request.Request(url,data=raw,headers={"Content-Type":"application/json","User-Agent":"Aave-source-audit/1.0"})
   with urllib.request.urlopen(req,timeout=40) as res:data=res.read();status=res.status;headers=dict(res.headers)
  except urllib.error.HTTPError as e:data=e.read();status=e.code;headers=dict(e.headers)
  except Exception as e:data=str(e).encode();status=0;headers={}
  h=sha(data);(OUT/(h+".gz")).write_bytes(gzip.compress(data,mtime=0))
  rec={"request":body,"request_sha256":sha(raw),"source_url":url,"http_status":status,"response_sha256":h,"headers":headers}
  with (OUT/"requests.jsonl").open("a") as f:f.write(json.dumps(rec)+"\n")
  try:d=json.loads(data)
  except:d={}
  attempts.append((d,status,url,h))
  if status==200 and isinstance(d,dict) and d.get("result") is not None:return d["result"],h,url
  time.sleep(.4)
 raise RuntimeError("RPC_EXHAUSTED_"+json.dumps([(a[1],a[2]) for a in attempts]))
rows=[]
for pid,tx,expected_ts in ROWS:
 r,h,url=post({"jsonrpc":"2.0","id":pid,"method":"eth_getTransactionReceipt","params":[tx]})
 if not r or int(r["status"],16)!=1:raise RuntimeError(f"BAD_RECEIPT_{pid}")
 bn=int(r["blockNumber"],16)
 b,bh,burl=post({"jsonrpc":"2.0","id":pid,"method":"eth_getBlockByNumber","params":[hex(bn),False]})
 ts=int(b["timestamp"],16)
 logs=[x for x in r["logs"] if x["address"].lower()==GOV and x.get("topics") and x["topics"][0].lower()==TOPIC]
 exact=[x for x in logs if len(x["topics"])>1 and int(x["topics"][1],16)==pid]
 status="PASS" if len(exact)==1 and ts==expected_ts else "FAIL"
 rows.append({"proposal_id":pid,"queue_tx":tx,"queue_block":bn,"queue_timestamp":ts,"expected_timestamp":expected_ts,
              "receipt_response_sha256":h,"receipt_source":url,"header_response_sha256":bh,"header_source":burl,
              "governance_core":GOV,"proposal_queued_log_count":len(exact),"status":status,"log":exact[0] if len(exact)==1 else None})
receipt={"lab_id":"AAVE-GOV-LT-FORCED-DELEVERAGING-001","phase":"V35_V3_CORE_QUEUE_ONCHAIN_SOURCE_ONLY",
         "candidate_count":len(rows),"pass_count":sum(x["status"]=="PASS" for x in rows),
         "all_pass":all(x["status"]=="PASS" for x in rows),"rows":rows,
         "source_gate_pass":False,"hypothesis_status":"NOT_TESTED","economic_outcomes_opened":0,
         "development_runs":0,"outcomes_2026_opened":False}
(OUT/"RECEIPT.json").write_text(json.dumps(receipt,indent=2)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k!="rows"},indent=2),flush=True)
for x in rows:print(json.dumps({k:x[k] for k in ["proposal_id","queue_block","queue_timestamp","status"]}),flush=True)
if not receipt["all_pass"]: raise SystemExit(2)

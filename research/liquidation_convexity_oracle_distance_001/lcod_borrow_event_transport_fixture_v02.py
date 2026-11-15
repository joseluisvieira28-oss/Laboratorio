#!/usr/bin/env python3
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path

OUT=Path("artifacts/lcod_borrow_transport_fixture_v02.json")
RPC="https://eth-mainnet.public.blastapi.io"
SQD="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
BLOCK=25398769
ADDR="0x973a023a77420ba610f06b3858ad991df6d85a08"
TOPIC="0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd"

def post(url,payload,timeout=90):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"CryptoLab-LCOD-BorrowFixture/0.2"},method="POST")
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()

# Blast exact-block truth fixture.
raw=post(RPC,{"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{"fromBlock":hex(BLOCK),"toBlock":hex(BLOCK),"address":ADDR,"topics":[TOPIC]}]})
rpc_obj=json.loads(raw.decode());rpc_logs=rpc_obj.get("result") or []

# SQD exact identical fixture.
q={"type":"evm","fromBlock":BLOCK,"toBlock":BLOCK,
   "fields":{"block":{"number":True},"log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}},
   "logs":[{"address":[ADDR],"topic0":[TOPIC]}]}
sraw=post(SQD,q,90);txt=sraw.decode("utf-8","replace").strip()
try:sobj=json.loads(txt)
except Exception:
    sobj=[json.loads(x) for x in txt.splitlines() if x.strip()]
matches=[]
def walk(v,bn=None):
    if isinstance(v,dict):
        h=v.get("header")
        if isinstance(h,dict) and h.get("number") is not None:bn=h.get("number")
        if all(k in v for k in ("address","topics")):
            ts=[str(x).lower() for x in (v.get("topics") or [])]
            if str(v.get("address","")).lower()==ADDR and ts and ts[0]==TOPIC:
                matches.append({"transaction_hash":v.get("transactionHash") or v.get("transaction_hash"),"topic_count":len(ts),"block_context":bn})
        for z in v.values():walk(z,bn)
    elif isinstance(v,list):
        for z in v:walk(z,bn)
walk(sobj)

receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"BORROW_EVENT_TRANSPORT_FIXTURE_V0.2",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "fixture":{"block":BLOCK,"spoke":ADDR,"topic0":TOPIC},
 "blast":{"log_count":len(rpc_logs),"pass":len(rpc_logs)>=1,"raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw),
          "tx_hashes":[x.get("transactionHash") for x in rpc_logs[:10]]},
 "sqd":{"log_count":len(matches),"pass":len(matches)>=1,"raw_sha256":hashlib.sha256(sraw).hexdigest(),"raw_bytes":len(sraw),
        "response_type":type(sobj).__name__,"matches":matches[:10],"raw_prefix_sha256":hashlib.sha256(txt[:500].encode()).hexdigest()},
 "classification":"BORROW_FIXTURE_BOTH_PASS" if rpc_logs and matches else ("BORROW_FIXTURE_BLAST_PASS_SQD_BLOCKED" if rpc_logs else "BORROW_FIXTURE_TRUTH_BLOCKED"),
 "market_returns_opened":False,"liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))

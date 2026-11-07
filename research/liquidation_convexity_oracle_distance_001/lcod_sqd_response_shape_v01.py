#!/usr/bin/env python3
import json,hashlib,urllib.request
from pathlib import Path
from datetime import datetime,timezone

OUT=Path("artifacts/lcod_sqd_response_shape_v01.json")
URL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
ADDR="0x973a023a77420ba610f06b3858ad991df6d85a08"
TOPIC="0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd"
FROM=24720920
TO=26052830

q={"type":"evm","fromBlock":FROM,"toBlock":TO,
   "fields":{"block":{"number":True},"log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}},
   "logs":[{"address":[ADDR],"topic0":[TOPIC]}]}
req=urllib.request.Request(URL,data=json.dumps(q).encode(),headers={
 "Content-Type":"application/json","Accept":"application/json","User-Agent":"CryptoLab-LCOD-SQDShape/0.1"},method="POST")
with urllib.request.urlopen(req,timeout=120) as r:raw=r.read()
txt=raw.decode("utf-8","replace")
try: obj=json.loads(txt)
except Exception:
    obj=[json.loads(x) for x in txt.splitlines() if x.strip()]

def shape(v,depth=0):
    if depth>3:return type(v).__name__
    if isinstance(v,dict):
        return {k:shape(val,depth+1) for k,val in list(v.items())[:30]}
    if isinstance(v,list):
        return {"type":"list","len":len(v),"first":shape(v[0],depth+1) if v else None}
    return type(v).__name__

receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"SQD_LONG_RANGE_RESPONSE_SHAPE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "query":{"fromBlock":FROM,"toBlock":TO,"address":ADDR,"topic0":TOPIC},
 "raw_bytes":len(raw),"raw_sha256":hashlib.sha256(raw).hexdigest(),
 "response_python_type":type(obj).__name__,
 "shape":shape(obj),
 "raw_preview":txt[:4000],
 "market_returns_opened":False,"liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))

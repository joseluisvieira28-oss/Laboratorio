#!/usr/bin/env python3
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path

RPC="https://eth-mainnet.public.blastapi.io"
OUT=Path("artifacts/lcod_blast_borrow_range_capability_v01.json")
BLOCK=25398769
ADDR="0x973a023a77420ba610f06b3858ad991df6d85a08"
TOPIC="0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd"
EXPECTED="0x23ab5a8b2d50db9ead1c17d59ddf7f246c6cc0f38d9f8e6a6d5c30f70f2cbf8f"
WIDTHS=[1,101,1001,5001,10001,50001,100001,250001]

def rpc(method,params):
    req=urllib.request.Request(RPC,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),
      headers={"Content-Type":"application/json","User-Agent":"CryptoLab-LCOD-RangeProbe/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=90) as r:raw=r.read()
    x=json.loads(raw.decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result"),raw

rows=[]
for width in WIDTHS:
    half=(width-1)//2
    lo=BLOCK-half;hi=BLOCK+half
    row={"width_blocks":width,"from_block":lo,"to_block":hi}
    try:
        logs,raw=rpc("eth_getLogs",[{"fromBlock":hex(lo),"toBlock":hex(hi),"address":ADDR,"topics":[TOPIC]}])
        txs=[str(x.get("transactionHash") or "").lower() for x in logs]
        clean=all(str(x.get("address") or "").lower()==ADDR and x.get("topics") and str(x["topics"][0]).lower()==TOPIC for x in logs)
        row.update({"call_pass":True,"log_count":len(logs),"expected_tx_present":EXPECTED in txs,
                    "all_logs_match_filter":clean,"pass":EXPECTED in txs and clean,
                    "raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw)})
    except Exception as e:
        row.update({"call_pass":False,"pass":False,"error":f"{type(e).__name__}:{str(e)[:500]}"})
    rows.append(row)

eligible=[r["width_blocks"] for r in rows if r.get("pass") and r["width_blocks"]<=100001]
selected=max(eligible) if eligible else None
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001","stage":"BLAST_BORROW_RANGE_CAPABILITY_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"BLAST_BORROW_RANGE_CAPABILITY_PASS" if selected else "BLAST_BORROW_RANGE_CAPABILITY_BLOCKED",
 "selected_conservative_chunk_blocks":selected,"rows":rows,
 "market_returns_opened":False,"liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if not selected:raise SystemExit(2)

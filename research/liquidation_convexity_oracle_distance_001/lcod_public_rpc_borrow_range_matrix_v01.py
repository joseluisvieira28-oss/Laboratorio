#!/usr/bin/env python3
import hashlib,json,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path

OUT=Path("artifacts/lcod_public_rpc_borrow_range_matrix_v01.json")
BLOCK=25398769
ADDR="0x973a023a77420ba610f06b3858ad991df6d85a08"
TOPIC="0xef18174796a5d2f91d51dc5e907a4d7867bbd6e800f6225168e0453d581d0dcd"
EXPECTED="0x23ab5a8b2d50db9ead1c17d59ddf7f246c6cc0f38d9f8e6a6d5c30f70f2cbf8f"
WIDTHS=[1,101,1001,5001,10001,50001]

ENDPOINTS=[
 ("llamarpc","https://eth.llamarpc.com"),
 ("merkle","https://eth.merkle.io"),
 ("blast_public","https://eth-mainnet.public.blastapi.io"),
 ("blockpi_public","https://ethereum.blockpi.network/v1/rpc/public"),
 ("onfinality_public","https://eth.api.onfinality.io/public"),
 ("flashbots","https://rpc.flashbots.net"),
 ("publicnode","https://ethereum-rpc.publicnode.com"),
 ("one_rpc","https://1rpc.io/eth"),
 ("drpc","https://eth.drpc.org"),
 ("payload","https://rpc.payload.de"),
 ("cloudflare","https://cloudflare-eth.com"),
]

def call(url,lo,hi):
    payload={"jsonrpc":"2.0","id":1,"method":"eth_getLogs","params":[{
      "fromBlock":hex(lo),"toBlock":hex(hi),"address":ADDR,"topics":[TOPIC]}]}
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={
      "Content-Type":"application/json","User-Agent":"CryptoLab-LCOD-RPCMatrix/0.1"},method="POST")
    try:
        with urllib.request.urlopen(req,timeout=35) as r:raw=r.read()
    except urllib.error.HTTPError as e:
        body=e.read().decode(errors="replace")[:500]
        raise RuntimeError(f"HTTP_{e.code}:{body}")
    x=json.loads(raw.decode())
    if x.get("error"):raise RuntimeError(f"RPC_ERROR:{json.dumps(x['error'],sort_keys=True)[:500]}")
    return x.get("result") or [],raw

rows=[];winners={}
for name,url in ENDPOINTS:
    provider=[]
    for width in WIDTHS:
        half=(width-1)//2;lo=BLOCK-half;hi=BLOCK+half
        row={"width_blocks":width}
        try:
            logs,raw=call(url,lo,hi)
            txs=[str(z.get("transactionHash") or "").lower() for z in logs]
            clean=all(str(z.get("address") or "").lower()==ADDR and z.get("topics") and str(z["topics"][0]).lower()==TOPIC for z in logs)
            ok=EXPECTED in txs and clean
            row.update({"pass":ok,"log_count":len(logs),"expected_tx_present":EXPECTED in txs,
                        "raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw)})
        except Exception as e:
            row.update({"pass":False,"error":f"{type(e).__name__}:{str(e)[:700]}"})
        provider.append(row)
    eligible=[x["width_blocks"] for x in provider if x.get("pass")]
    winners[name]=max(eligible) if eligible else 0
    rows.append({"name":name,"url":url,"max_passing_width_blocks":winners[name],"probes":provider})

best=max(winners.values()) if winners else 0
best_names=sorted(k for k,v in winners.items() if v==best and best>0)
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"PUBLIC_RPC_BORROW_RANGE_MATRIX_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"PUBLIC_RPC_RANGE_ROUTE_PASS" if best>=1001 else "PUBLIC_RPC_RANGE_ROUTE_BLOCKED",
 "best_passing_width_blocks":best,"best_routes":best_names,"routes":rows,
 "truth_fixture_crosschecked_with_blast_and_sqd":True,
 "market_returns_opened":False,"liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt["classification"],"best_passing_width_blocks":best,"best_routes":best_names,
 "route_maxima":winners},indent=2))
if receipt["classification"]!="PUBLIC_RPC_RANGE_ROUTE_PASS":raise SystemExit(2)

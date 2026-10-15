#!/usr/bin/env python3
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path

OUT=Path("artifacts/cclm_cctp_v1_transport_smoke_v01.json")
PROBES=[
 {
  "name":"avalanche_deposit_for_burn",
  "rpc":"https://api.avax.network/ext/bc/C/rpc",
  "block":34152753,
  "address":"0x6b25532e1060ce10cc3b0a99e5683b91bfde6982",
  "topic":"0x2fa9ca894982930190727e75500a97d8dc500233a5065e0f3126c48fbe0343c0",
  "expected_min":1,
 },
 {
  "name":"ethereum_mint_and_withdraw",
  "rpc":"https://ethereum-rpc.publicnode.com",
  "block":18433832,
  "address":"0xbd3fa81b58ba92a82136038b25adec7066af3155",
  "topic":"0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6",
  "expected_min":1,
 },
]

def rpc(url,method,params):
    req=urllib.request.Request(url,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json","User-Agent":"CryptoLab-CCLM-001-Transport/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:x=json.loads(r.read().decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

rows=[];passed=True
for p in PROBES:
    row={k:v for k,v in p.items() if k!="rpc"}
    try:
        b=rpc(p["rpc"],"eth_getBlockByNumber",[hex(p["block"]),False])
        logs=rpc(p["rpc"],"eth_getLogs",[{"fromBlock":hex(p["block"]),"toBlock":hex(p["block"]),"address":p["address"],"topics":[p["topic"]]}]) or []
        row["block_timestamp"]=int(b["timestamp"],16) if b else None
        row["log_count"]=len(logs)
        row["logs"]=[{
          "transaction_hash":x.get("transactionHash"),
          "log_index":int(x.get("logIndex","0x0"),16),
          "block_number":int(x.get("blockNumber","0x0"),16),
          "data_sha256":hashlib.sha256((x.get("data") or "").encode()).hexdigest(),
          "topics":x.get("topics"),
        } for x in logs]
        row["pass"]=len(logs)>=p["expected_min"]
    except Exception as e:
        row["pass"]=False;row["error"]=f"{type(e).__name__}:{str(e)[:400]}"
    passed=passed and row["pass"];rows.append(row)

receipt={
 "lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001",
 "child_id":"CCLM-CCTP-USDC-001",
 "stage":"CCTP_V1_HISTORICAL_TRANSPORT_SMOKE",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"HISTORICAL_RPC_TRANSPORT_PASS" if passed else "HISTORICAL_RPC_TRANSPORT_FAILURE",
 "probes":rows,
 "market_outcomes_opened":False,"pnl_opened":False,"mutation":False,"access_2025":False,"access_2026":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))

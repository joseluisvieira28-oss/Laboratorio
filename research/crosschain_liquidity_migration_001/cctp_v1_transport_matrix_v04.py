#!/usr/bin/env python3
import hashlib,json,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path

OUT=Path("artifacts/cclm_cctp_v1_transport_matrix_v04.json")
BLOCK=18433832
ADDRESS="0xbd3fa81b58ba92a82136038b25adec7066af3155"
TOPIC="0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6"
ENDPOINTS=[
 ("llamarpc","https://eth.llamarpc.com"),
 ("merkle","https://eth.merkle.io"),
 ("blast_public","https://eth-mainnet.public.blastapi.io"),
 ("blockpi_public","https://ethereum.blockpi.network/v1/rpc/public"),
 ("onfinality_public","https://eth.api.onfinality.io/public"),
 ("flashbots","https://rpc.flashbots.net"),
 ("publicnode","https://ethereum-rpc.publicnode.com"),
]

def rpc(url,method,params):
    req=urllib.request.Request(
      url,
      data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),
      headers={"Content-Type":"application/json","User-Agent":"CryptoLab-CCLM-001-Transport/0.4"},
      method="POST",
    )
    try:
      with urllib.request.urlopen(req,timeout=25) as r:
        raw=r.read().decode()
    except urllib.error.HTTPError as e:
      body=e.read().decode(errors="replace")[:500]
      raise RuntimeError(f"HTTP_{e.code}:{body}")
    obj=json.loads(raw)
    if obj.get("error"):
      raise RuntimeError(f"RPC_ERROR:{json.dumps(obj['error'],sort_keys=True)[:500]}")
    return obj.get("result")

rows=[]; winners=[]
for name,url in ENDPOINTS:
    row={"name":name}
    try:
        row["chain_id"]=rpc(url,"eth_chainId",[])
        b=rpc(url,"eth_getBlockByNumber",[hex(BLOCK),False])
        row["block_present"]=bool(b)
        row["block_timestamp"]=int(b["timestamp"],16) if b else None
        logs=rpc(url,"eth_getLogs",[{
          "fromBlock":hex(BLOCK),
          "toBlock":hex(BLOCK),
          "address":ADDRESS,
          "topics":[TOPIC],
        }]) or []
        row["log_count"]=len(logs)
        row["logs"]=[{
          "tx":x.get("transactionHash"),
          "log_index":int(x.get("logIndex","0x0"),16),
          "data_sha256":hashlib.sha256((x.get("data") or "").encode()).hexdigest(),
        } for x in logs]
        row["pass"]=bool(b) and len(logs)>=1
        if row["pass"]: winners.append(name)
    except Exception as e:
        row["pass"]=False
        row["error"]=f"{type(e).__name__}:{str(e)[:700]}"
    rows.append(row)

receipt={
 "lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001",
 "child_id":"CCLM-CCTP-USDC-001",
 "stage":"ETHEREUM_HISTORICAL_RPC_TRANSPORT_MATRIX_V0.4",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "historical_block":BLOCK,
 "classification":"ETHEREUM_HISTORICAL_RPC_ROUTE_PASS" if winners else "SOURCE_ACCESS_BLOCKED_FREE_ETHEREUM_HISTORICAL_RPC",
 "winning_routes":winners,
 "probes":rows,
 "market_outcomes_opened":False,
 "pnl_opened":False,
 "mutation":False,
 "access_2025":False,
 "access_2026":False,
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))

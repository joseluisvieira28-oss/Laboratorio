#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path

URL="https://mcp.aave.com/"
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/aave_hf_crowding_001_schema_receipt.json")
TARGETS={"get_user_summary","get_user_positions","get_user_summary_history","get_market_history","get_protocol_history","get_asset_history","get_reserve_holders"}

payload={"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
req=urllib.request.Request(URL,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AAVE-HFC-001/1.1"},method="POST")
with urllib.request.urlopen(req,timeout=30) as r:
    data=json.loads(r.read().decode())

tools=(data.get("result") or {}).get("tools",[]) or []
selected={}
for t in tools:
    if t.get("name") in TARGETS:
        selected[t["name"]]={
            "description":t.get("description"),
            "inputSchema":t.get("inputSchema")
        }

receipt={
  "lab_id":"AAVE-HF-CROWDING-001",
  "probe_id":"AAVE-HFC-001-READ-SCHEMA-001",
  "classification":"READ_SCHEMA_COMPLETE" if TARGETS.issubset(selected.keys()) else "READ_SCHEMA_INCOMPLETE",
  "selected_tools":selected,
  "tool_calls_executed":["tools/list"],
  "wallet_addresses_opened":False,
  "health_factor_values_opened":False,
  "liquidation_outcomes_opened":False,
  "market_values_opened":False,
  "returns_opened":False,
  "pnl_opened":False,
  "action_tool_called":False,
  "mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
 "classification":receipt["classification"],
 "tools":{k:{"required":(v["inputSchema"] or {}).get("required",[]),"properties":sorted(((v["inputSchema"] or {}).get("properties") or {}).keys())} for k,v in selected.items()}
},indent=2))

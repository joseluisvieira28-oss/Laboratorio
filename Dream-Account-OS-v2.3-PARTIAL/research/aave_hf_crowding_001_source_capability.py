#!/usr/bin/env python3
import json, urllib.request
from pathlib import Path

URL="https://mcp.aave.com/"
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/aave_hf_crowding_001_source_capability_receipt.json")

payload={"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}
req=urllib.request.Request(
    URL,
    data=json.dumps(payload).encode(),
    headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AAVE-HFC-001/1.0"},
    method="POST",
)
with urllib.request.urlopen(req,timeout=30) as r:
    status=r.status
    data=json.loads(r.read().decode())

result=data.get("result",{})
tools=result.get("tools",[]) or []
rows=[]
for t in tools:
    schema=t.get("inputSchema") or {}
    rows.append({
        "name":t.get("name"),
        "description":(t.get("description") or "")[:500],
        "input_schema_top_level_keys":sorted(list(schema.keys()))
    })
names={x["name"] for x in rows if x["name"]}
blob=" ".join(((x["name"] or "")+" "+(x["description"] or "")).lower() for x in rows)

required=["get_user_summary","get_user_positions","get_user_summary_history"]
pass_exact=all(x in names for x in required)
market_cap=("market" in blob or "reserve" in blob)
history_cap=("history" in blob or "time-series" in blob or "time series" in blob)
passed=(status==200 and len(rows)>=1 and pass_exact and market_cap and history_cap)

receipt={
  "lab_id":"AAVE-HF-CROWDING-001",
  "source_gate_id":"AAVE-HFC-001-SOURCE-CAPABILITY-001",
  "http_status":status,
  "tool_count":len(rows),
  "required_exact_tools_present":{x:(x in names) for x in required},
  "market_or_reserve_read_capability_present":market_cap,
  "history_or_timeseries_read_capability_present":history_cap,
  "tools":rows,
  "classification":"OFFICIAL_AAVE_MCP_CREDIT_SOURCE_CAPABILITY_PASS" if passed else "OFFICIAL_AAVE_MCP_CREDIT_SOURCE_CAPABILITY_INSUFFICIENT",
  "wallet_addresses_opened":False,
  "health_factor_values_opened":False,
  "liquidation_outcomes_opened":False,
  "market_prices_opened":False,
  "returns_opened":False,
  "pnl_opened":False,
  "action_tool_called":False,
  "mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({
  "classification":receipt["classification"],
  "tool_count":receipt["tool_count"],
  "required_exact_tools_present":receipt["required_exact_tools_present"],
  "market_or_reserve_read_capability_present":market_cap,
  "history_or_timeseries_read_capability_present":history_cap
},indent=2))

#!/usr/bin/env python3
"""LCOD-001 source-capability probe.

Reads only Aave MCP tool schemas and a bounded sample of current v4 borrower
positions. It does not read any market-return outcome and never calls action
tools. Wallet addresses are hashed before persistence.
"""
import hashlib, json, re, urllib.request
from pathlib import Path

URL="https://mcp.aave.com/"
OUT=Path("research/liquidation_convexity_oracle_distance_001/runtime/source_capability_receipt.json")

def rpc(method,params):
    req=urllib.request.Request(
        URL,
        data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),
        headers={"Content-Type":"application/json","User-Agent":"CryptoLab-LCOD-001/0.1"},
        method="POST",
    )
    with urllib.request.urlopen(req,timeout=45) as r:
        x=json.loads(r.read().decode())
    if x.get("error"):
        raise RuntimeError(x["error"])
    return x.get("result")

def unwrap(x):
    if isinstance(x,dict) and x.get("structuredContent") is not None:
        return x["structuredContent"]
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:return json.loads(c.get("text",""))
                except Exception:pass
    return x

def call(name,args):
    return unwrap(rpc("tools/call",{"name":name,"arguments":args}))

def dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from dicts(v)
    elif isinstance(x,list):
        for v in x: yield from dicts(v)

catalog=rpc("tools/list",{})
tools={t.get("name"):t for t in (catalog or {}).get("tools",[])}
required=["get_markets","get_reserve_holders","get_user_positions","get_user_summary"]
missing=[x for x in required if x not in tools]

receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"SOURCE_CAPABILITY_PROBE",
 "required_tools_present":not missing,
 "missing_tools":missing,
 "action_tool_called":False,
 "mutation":False,
 "market_returns_opened":False,
 "pnl_opened":False,
 "wallet_addresses_retained":False,
}
if missing:
    receipt["classification"]="SOURCE_CAPABILITY_BLOCKED"
else:
    markets=call("get_markets",{"version":"v4"})
    reserve_ids=sorted({str(d.get("reserveId") or d.get("reserve_id")) for d in dicts(markets) if d.get("reserveId") or d.get("reserve_id")})
    wallets=[]
    for rid in reserve_ids[:8]:
        try:
            holders=call("get_reserve_holders",{"reserveId":rid,"side":"borrow","limit":10,"version":"v4"})
            for d in dicts(holders):
                for k in ("user","address","wallet"):
                    v=d.get(k)
                    if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):
                        wallets.append(v.lower()); break
        except Exception:
            pass
        if len(set(wallets))>=5: break
    wallets=sorted(set(wallets))[:5]

    samples=[]
    observed_keys=set()
    for w in wallets:
        pos=call("get_user_positions",{"user":w,"version":"v4"})
        summary=call("get_user_summary",{"user":w,"version":"v4"})
        keys=set()
        for d in dicts(pos):
            keys.update(map(str,d.keys()))
        observed_keys.update(keys)
        samples.append({
          "wallet_sha256":hashlib.sha256(w.encode()).hexdigest(),
          "position_topology_keys":sorted(keys),
          "position_object_count":sum(1 for _ in dicts(pos)),
          "summary_object_count":sum(1 for _ in dicts(summary)),
        })

    # We deliberately do not persist values. The probe asks only whether the
    # source exposes enough structural fields to justify a component collector.
    low={k.lower() for k in observed_keys}
    valueish=any(any(token in k for token in ("balance","amount","value","principal","debt","supply")) for k in low)
    reserveish=any("reserve" in k or "asset" in k or "token" in k for k in low)
    healthish=any("health" in k for k in low)
    receipt.update({
      "v4_reserve_count":len(reserve_ids),
      "sampled_borrower_count":len(wallets),
      "sample_schema":samples,
      "observed_position_keys":sorted(observed_keys),
      "component_value_field_present":valueish,
      "reserve_identity_field_present":reserveish,
      "health_field_present":healthish,
      "classification":"SOURCE_COMPONENT_SCHEMA_PASS" if wallets and valueish and reserveish else "SOURCE_COMPONENT_SCHEMA_INSUFFICIENT",
    })

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k!="sample_schema"},indent=2))

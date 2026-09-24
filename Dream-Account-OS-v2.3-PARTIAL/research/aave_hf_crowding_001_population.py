#!/usr/bin/env python3
import hashlib,json,urllib.request
from pathlib import Path

URL="https://mcp.aave.com/"
OUT=Path("Dream-Account-OS-v2.3-PARTIAL/runtime/aave_hf_crowding_001_population_receipt.json")

def rpc(method,params):
    req=urllib.request.Request(URL,data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode(),headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AAVE-HFC-001/1.2"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:
        x=json.loads(r.read().decode())
    if x.get("error"): raise RuntimeError(x["error"])
    return x.get("result")

catalog=rpc("tools/list",{})
tools={t.get("name"):t for t in (catalog or {}).get("tools",[])}
if "get_markets" not in tools or "get_reserve_holders" not in tools:
    raise SystemExit("required tools absent")

def call(name,args):
    return rpc("tools/call",{"name":name,"arguments":args})

markets=call("get_markets",{"version":"v4"})
# MCP tool results may wrap JSON/text. Normalize conservatively.
def unwrap(x):
    if isinstance(x,dict) and "structuredContent" in x and x["structuredContent"] is not None:
        return x["structuredContent"]
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:return json.loads(c.get("text",""))
                except:pass
    return x

m=unwrap(markets)
# Find reserve-like dictionaries recursively.
def dicts(x):
    if isinstance(x,dict):
        yield x
        for v in x.values(): yield from dicts(v)
    elif isinstance(x,list):
        for v in x: yield from dicts(v)

reserves={}
for d in dicts(m):
    rid=d.get("reserveId") or d.get("reserve_id")
    if rid is not None:
        reserves[str(rid)]=True

holder_rows=0; hashed=set(); queried=0; nonempty=0; errors=[]
for rid in sorted(reserves):
    try:
        h=unwrap(call("get_reserve_holders",{"reserveId":rid,"side":"borrow","limit":50,"version":"v4"}))
        queried+=1
        rows=[]
        for d in dicts(h):
            addr=d.get("user") or d.get("address") or d.get("wallet")
            if isinstance(addr,str) and addr.lower().startswith("0x") and len(addr)>=40:
                rows.append(addr.lower())
        if rows: nonempty+=1
        holder_rows+=len(rows)
        for a in rows:
            hashed.add(hashlib.sha256(a.encode()).hexdigest())
    except Exception as e:
        errors.append({"reserve_hash":hashlib.sha256(rid.encode()).hexdigest(),"error_type":type(e).__name__})

passed=len(reserves)>=5 and queried>=5 and len(hashed)>=25
receipt={
 "lab_id":"AAVE-HF-CROWDING-001",
 "stage":"BORROWER_POPULATION_SOURCE_CENSUS",
 "classification":"AAVE_V4_BORROWER_POPULATION_SOURCE_PASS" if passed else "AAVE_V4_BORROWER_POPULATION_SOURCE_INSUFFICIENT",
 "v4_reserve_count":len(reserves),
 "reserves_queried":queried,
 "reserves_with_borrow_holders":nonempty,
 "raw_holder_rows":holder_rows,
 "deduplicated_borrower_count":len(hashed),
 "borrower_sha256":sorted(hashed),
 "query_errors":errors,
 "health_factor_values_opened":False,
 "debt_values_retained":False,
 "collateral_values_retained":False,
 "price_values_retained":False,
 "returns_opened":False,
 "pnl_opened":False,
 "action_tool_called":False,
 "mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in ("borrower_sha256","query_errors")},indent=2))

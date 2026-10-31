#!/usr/bin/env python3
"""Read only original archived raw Velocity API JSON; no market network."""
import json,hashlib,pathlib
SRC=pathlib.Path("downloaded");OUT=pathlib.Path("artifacts/velocity_offline_schema_audit")
OUT.mkdir(exist_ok=True,parents=True)
def shape(x,depth=2):
    if isinstance(x,dict):
        return {"type":"object","keys":sorted(x.keys())[:40],
            "children":{k:shape(x[k],depth-1) for k in sorted(x.keys())[:15]} if depth>0 else {}}
    if isinstance(x,list):
        return {"type":"array","length":len(x),"first_element_type":type(x[0]).__name__ if x else None,
            "first_element_keys":sorted(x[0].keys())[:40] if x and isinstance(x[0],dict) else None}
    return {"type":type(x).__name__}
try:
    original=json.loads((SRC/"receipt.json").read_text())
    assert original["status"]=="SOURCE_BLOCKED_FAIL_CLOSED"
    assert original["reason"]=="STATS_MARKETS_SCHEMA_BAD"
    raw=(SRC/"00_stats_markets.json").read_bytes()
    assert original["source_receipts"][0]["raw_sha256"]==hashlib.sha256(raw).hexdigest()
    x=json.loads(raw)
    result={"study":"VELOCITY_V01A_POST_SOURCE_OFFLINE_SCHEMA_AUDIT","source_status_immutable":original["status"],
            "original_run":41227701534,"schema":shape(x),
            "raw_bytes_sha256":hashlib.sha256(raw).hexdigest(),"new_api_calls":0,
            "economic_edge_certified":False}
except Exception as e:
    result={"study":"VELOCITY_V01A_POST_SOURCE_OFFLINE_SCHEMA_AUDIT",
            "status":"AUDIT_BLOCKED","reason":type(e).__name__+":"+str(e)[:160],"new_api_calls":0}
result["status"]=result.get("status","OFFLINE_SCHEMA_REPRODUCED")
(OUT/"receipt.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps(result,indent=2,sort_keys=True))
if result["status"]=="AUDIT_BLOCKED":raise SystemExit(2)

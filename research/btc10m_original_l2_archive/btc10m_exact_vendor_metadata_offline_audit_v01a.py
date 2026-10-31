#!/usr/bin/env python3
import json,hashlib,pathlib
P=pathlib.Path("downloaded")
O=pathlib.Path("artifacts/btc10m_exact_l2_vendor_offline_audit_v01a")
O.mkdir(parents=True,exist_ok=True)
source=json.loads((P/"source_receipt.json").read_text())
assert source["status"]=="SOURCE_PAIR_IDENTITY_UNPROVEN"
result={"study":"BTC10M_L2_VENDOR_METADATA_OFFLINE_ORIGINAL_SOURCE_AUDIT","status":"OFFLINE_SOURCE_REPLAY","original_run_id":41234699496,"market_api_calls":0,"original_status_immutable":source["status"],"replies":{}}
for rec in source["requests"]:
    raw=(P/rec["file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==rec["raw_sha256"]
    obj=json.loads(raw)
    result["replies"][rec["file"]]=obj
(O/"audit.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print("ORIGINAL_PUBLIC_METADATA",json.dumps(result,sort_keys=True),flush=True)

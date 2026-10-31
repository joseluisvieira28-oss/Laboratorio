#!/usr/bin/env python3
"""OFFLINE ORIGINAL OKX 4 JSON provenance and nested archive details; no network."""
import hashlib,json,pathlib
D=pathlib.Path("downloaded");O=pathlib.Path("artifacts/btc10m_okx_official_raw_details_audit_v01a")
O.mkdir(parents=True,exist_ok=True)
orig=json.loads((D/"receipt.json").read_text())
assert orig["status"]=="FOUR_OFFICIAL_L2_ARCHIVE_SCOPES_LISTED_FILE_UNPROVEN"
out={"study":"OKX_OFFICIAL_L2_ORIGINAL_DETAILS_OFFLINE_AUDIT_V01A",
     "origin_run":41240149050,"source_http_calls":0,
     "data_outcomes_read":0,"status":"OFFLINE_RAW_HASHES_AND_NESTED_DETAILS_REPLAY",
     "results":[]}
for rec in orig["requests"]:
    raw=(D/rec["raw_file"]).read_bytes()
    assert hashlib.sha256(raw).hexdigest()==rec["raw_sha256"]
    j=json.loads(raw)
    d=j.get("data")
    assert j.get("code")=="0" and isinstance(d,list) and d
    group=[]
    for item in d:
        if not isinstance(item,dict):continue
        group.append({k:v for k,v in item.items() if k!="details"})
        group[-1]["details"]=item.get("details")
    out["results"].append({"day":rec["date"],"market":rec["market"],"original_raw_sha256":rec["raw_sha256"],"data":group})
(O/"audit.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print("OFFLINE_DETAILS",json.dumps(out,sort_keys=True),flush=True)

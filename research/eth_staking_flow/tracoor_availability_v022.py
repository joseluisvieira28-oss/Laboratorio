#!/usr/bin/env python3
import hashlib,json,urllib.request
from pathlib import Path

BASE="https://tracoor.mainnet.ethpandaops.io"
TARGETS={
 "control_2025-02-24":11127616,
 "control_2025-03-02":11170816,
 "control_2025-10-17":12819616,
 "missing_2025-02-25":11134816,
 "missing_2025-02-26":11142016,
 "missing_2025-02-27":11149216,
 "missing_2025-02-28":11156416,
 "missing_2025-03-01":11163616,
 "missing_2025-10-18":12826816,
 "missing_2025-10-19":12834016,
}
receipt={"lab_id":"ETH-STAKING-FLOW-001","stage":"V3_STAGEA_TRACOOR_AVAILABILITY_V0_2_2",
 "ssz_bodies_downloaded":False,"validator_counts_opened":False,"market_data_opened":False,
 "signal_evaluated":False,"returns_opened":False,"pnl_opened":False,
 "source_after_2026_08_31_opened":False,"targets":[]}

def post(payload):
    raw_body=json.dumps(payload,separators=(",",":")).encode()
    req=urllib.request.Request(BASE+"/v1/api/list-beacon-state",data=raw_body,
        headers={"User-Agent":"crypto-lab-tracoor-v022/1.0","Content-Type":"application/json","Accept":"application/json"},
        method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:
        raw=r.read()
        return r.status,r.headers.get("content-type"),raw,json.loads(raw)

transport_fail=False
root_conflict=False
exact_available=0
for name,slot in TARGETS.items():
    row={"name":name,"target_slot":slot}
    try:
        st,ct,raw,obj=post({"network":"mainnet","slot":slot,"pagination":{"limit":100,"offset":0,"order_by":"fetched_at ASC"}})
        row["http_status"]=st; row["content_type"]=ct; row["raw_bytes"]=len(raw); row["sha256"]=hashlib.sha256(raw).hexdigest()
        states=obj.get("beacon_states",[]) if isinstance(obj,dict) else []
        clean=[]
        for x in states if isinstance(states,list) else []:
            if not isinstance(x,dict): continue
            clean.append({k:x.get(k) for k in ["id","node","fetched_at","slot","epoch","state_root","node_version","network","beacon_implementation"]})
        row["records"]=clean
        row["record_count"]=len(clean)
        exact=[x for x in clean if int(x.get("slot") or -1)==slot and x.get("network")=="mainnet"]
        row["exact_mainnet_count"]=len(exact)
        roots=sorted({str(x.get("state_root")) for x in exact if x.get("state_root")})
        row["exact_state_roots"]=roots
        row["distinct_nodes"]=len({str(x.get("node")) for x in exact if x.get("node")})
        row["distinct_implementations"]=len({str(x.get("beacon_implementation")) for x in exact if x.get("beacon_implementation")})
        if exact: exact_available+=1
        if len(roots)>1: root_conflict=True
    except Exception as e:
        transport_fail=True; row["error"]=f"{type(e).__name__}:{str(e)[:500]}"
    receipt["targets"].append(row)

receipt["exact_slots_available"]=exact_available
if root_conflict:
    receipt["classification"]="SOURCE_PROVENANCE_FAILURE"
elif transport_fail:
    receipt["classification"]="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
elif exact_available==10:
    receipt["classification"]="TRACOOR_EXACT_STATE_ARCHIVE_AVAILABLE"
elif exact_available>0:
    receipt["classification"]="TRACOOR_ARCHIVE_PARTIAL"
else:
    receipt["classification"]="TRACOOR_ARCHIVE_UNAVAILABLE"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/ETH_STAKING_FLOW_001_TRACOOR_AVAILABILITY_V0_2_2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))

#!/usr/bin/env python3
import hashlib,json,urllib.request,urllib.error
from pathlib import Path

BASE="https://cbt.mainnet.ethpandaops.io/api/v1"
MODEL="mainnet.dim_validator_status"
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
FULL_RANGE=[10738816,15109216]

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-cbt-coverage-v021/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
        return r.status,r.headers.get("content-type"),raw,json.loads(raw)

receipt={
 "lab_id":"ETH-STAKING-FLOW-001",
 "stage":"V3_STAGEA_CBT_COVERAGE_V0_2_1",
 "model_id":MODEL,
 "position_unit":"slot",
 "validator_rows_opened":False,
 "queue_counts_opened":False,
 "market_data_opened":False,
 "signal_evaluated":False,
 "returns_opened":False,
 "pnl_opened":False,
 "source_after_2026_08_31_opened":False,
 "target_slots":TARGETS,
 "full_frozen_slot_range":FULL_RANGE,
 "debug":[],
}

try:
    url=f"{BASE}/models/transformations/{MODEL}/coverage"
    status,ctype,raw,obj=fetch(url)
    receipt["coverage_http_status"]=status
    receipt["coverage_content_type"]=ctype
    receipt["coverage_raw_bytes"]=len(raw)
    receipt["coverage_sha256"]=hashlib.sha256(raw).hexdigest()
    receipt["coverage_top_level_keys"]=sorted(obj.keys()) if isinstance(obj,dict) else []
    ranges=obj.get("ranges",[]) if isinstance(obj,dict) else []
    norm=[]
    for r in ranges if isinstance(ranges,list) else []:
        if not isinstance(r,dict): continue
        p=int(r["position"]); n=int(r["interval"])
        norm.append({"position":p,"interval":n,"end_exclusive":p+n})
    receipt["processed_range_count"]=len(norm)
    receipt["processed_ranges"]=norm
    receipt["processed_min_position"]=min((r["position"] for r in norm),default=None)
    receipt["processed_max_end_exclusive"]=max((r["end_exclusive"] for r in norm),default=None)
except Exception as e:
    receipt["classification"]="CBT_COVERAGE_METADATA_INCONCLUSIVE"
    receipt["coverage_error"]=f"{type(e).__name__}:{str(e)[:500]}"
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/ETH_STAKING_FLOW_001_CBT_COVERAGE_V0_2_1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    raise SystemExit(2)

def in_processed(slot):
    return any(r["position"] <= slot < r["end_exclusive"] for r in receipt["processed_ranges"])

all_ok=True
explicit_fail=False
for name,slot in TARGETS.items():
    row={"name":name,"slot":slot,"inside_processed_ranges":in_processed(slot)}
    try:
        u=f"{BASE}/models/transformations/{MODEL}/coverage/{slot}"
        st,ct,raw,obj=fetch(u)
        row["http_status"]=st
        row["raw_bytes"]=len(raw)
        row["sha256"]=hashlib.sha256(raw).hexdigest()
        row["top_level_keys"]=sorted(obj.keys()) if isinstance(obj,dict) else []
        if isinstance(obj,dict):
            # Source-metadata fields only; no row data exist on this endpoint.
            row["coverage_status"]=obj.get("coverage_status")
            row["blocking"]=obj.get("blocking")
            row["bounds"]=obj.get("bounds")
            row["gaps"]=obj.get("gaps")
            row["validation"]=obj.get("validation")
            row["model_id"]=obj.get("model_id")
            row["interval"]=obj.get("interval")
    except urllib.error.HTTPError as e:
        row["http_error"]=e.code
    except Exception as e:
        row["error"]=f"{type(e).__name__}:{str(e)[:300]}"

    cs=str(row.get("coverage_status","")).lower()
    debug_pass=(cs=="full_coverage" and row.get("blocking") is False)
    # Some server versions may not expose top-level status; processed-range membership
    # is necessary but not sufficient in that case.
    row["debug_full_coverage_pass"]=debug_pass
    if not row["inside_processed_ranges"] or cs in {"has_gaps","no_data","not_initialized"} or row.get("blocking") is True:
        explicit_fail=True
    if not (row["inside_processed_ranges"] and debug_pass):
        all_ok=False
    receipt["debug"].append(row)

receipt["targets_inside_processed_ranges"]=sum(1 for x in receipt["debug"] if x["inside_processed_ranges"])
receipt["targets_debug_full_coverage"]=sum(1 for x in receipt["debug"] if x["debug_full_coverage_pass"])
receipt["full_range_endpoints_inside_processed_ranges"]={
    "first":in_processed(FULL_RANGE[0]),
    "last":in_processed(FULL_RANGE[1]),
}
if all_ok:
    receipt["classification"]="CBT_COVERAGE_TARGETS_PASS"
elif explicit_fail:
    receipt["classification"]="CBT_COVERAGE_TARGETS_FAIL"
else:
    receipt["classification"]="CBT_COVERAGE_METADATA_INCONCLUSIVE"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/ETH_STAKING_FLOW_001_CBT_COVERAGE_V0_2_1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))
raise SystemExit(0)

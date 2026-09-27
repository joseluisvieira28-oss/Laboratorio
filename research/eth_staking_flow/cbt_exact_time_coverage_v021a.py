#!/usr/bin/env python3
import hashlib,json,urllib.request
from pathlib import Path

BASE="https://cbt.mainnet.ethpandaops.io/api/v1"
MODEL="mainnet.dim_validator_status"
TARGETS={
 "control_2025-02-24":1740355415,
 "control_2025-03-02":1740873815,
 "control_2025-10-17":1760659415,
 "missing_2025-02-25":1740441815,
 "missing_2025-02-26":1740528215,
 "missing_2025-02-27":1740614615,
 "missing_2025-02-28":1740701015,
 "missing_2025-03-01":1740787415,
 "missing_2025-10-18":1760745815,
 "missing_2025-10-19":1760832215,
}
FULL_RANGE=[1735689815,1788134615]

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-cbt-coverage-v021a/1.0","Accept":"application/json"})
    with urllib.request.urlopen(req,timeout=30) as r:
        raw=r.read()
        return r.status,r.headers.get("content-type"),raw,json.loads(raw)

receipt={"lab_id":"ETH-STAKING-FLOW-001","stage":"V3_STAGEA_CBT_COVERAGE_V0_2_1A",
 "model_id":MODEL,"position_unit":"unix_seconds",
 "validator_rows_opened":False,"queue_counts_opened":False,"market_data_opened":False,
 "signal_evaluated":False,"returns_opened":False,"pnl_opened":False,
 "source_after_2026_08_31_opened":False,"target_positions":TARGETS,
 "full_frozen_position_range":FULL_RANGE,"debug":[]}

try:
    url=f"{BASE}/models/transformations/{MODEL}/coverage"
    st,ct,raw,obj=fetch(url)
    receipt["coverage_http_status"]=st; receipt["coverage_content_type"]=ct
    receipt["coverage_raw_bytes"]=len(raw); receipt["coverage_sha256"]=hashlib.sha256(raw).hexdigest()
    ranges=obj.get("ranges",[]) if isinstance(obj,dict) else []
    norm=[]
    for r in ranges:
        p=int(r["position"]); n=int(r["interval"])
        norm.append({"position":p,"interval":n,"end_exclusive":p+n})
    receipt["processed_ranges"]=norm
    receipt["processed_range_count"]=len(norm)
    receipt["processed_min_position"]=min((r["position"] for r in norm),default=None)
    receipt["processed_max_end_exclusive"]=max((r["end_exclusive"] for r in norm),default=None)
except Exception as e:
    receipt["classification"]="CBT_COVERAGE_METADATA_INCONCLUSIVE"
    receipt["error"]=f"{type(e).__name__}:{str(e)[:500]}"
    Path("artifacts").mkdir(exist_ok=True)
    Path("artifacts/ETH_STAKING_FLOW_001_CBT_COVERAGE_V0_2_1A.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,sort_keys=True))
    raise SystemExit(0)

def inside(pos):
    return any(r["position"] <= pos < r["end_exclusive"] for r in receipt["processed_ranges"])

all_pass=True
explicit_fail=False
for name,pos in TARGETS.items():
    row={"name":name,"position":pos,"inside_processed_ranges":inside(pos)}
    try:
        st,ct,raw,obj=fetch(f"{BASE}/models/transformations/{MODEL}/coverage/{pos}")
        row["http_status"]=st; row["raw_bytes"]=len(raw); row["sha256"]=hashlib.sha256(raw).hexdigest()
        row["top_level_keys"]=sorted(obj.keys()) if isinstance(obj,dict) else []
        if isinstance(obj,dict):
            mc=obj.get("model_coverage") or {}
            row["model_coverage_status"]=mc.get("coverage_status")
            row["model_blocking"]=mc.get("blocking")
            row["model_bounds"]=mc.get("bounds")
            row["model_gaps"]=mc.get("gaps")
            val=obj.get("validation") or {}
            row["validation_in_bounds"]=val.get("in_bounds")
            row["validation_has_dependency_gaps"]=val.get("has_dependency_gaps")
            row["validation_reasons"]=val.get("reasons")
            row["can_process"]=obj.get("can_process")
    except Exception as e:
        row["error"]=f"{type(e).__name__}:{str(e)[:300]}"
    cs=str(row.get("model_coverage_status","")).lower()
    pass_debug=(cs=="full_coverage" and row.get("model_blocking") is False)
    row["debug_full_coverage_pass"]=pass_debug
    if (not row["inside_processed_ranges"] or cs in {"has_gaps","no_data","not_initialized"} or
        row.get("model_blocking") is True):
        explicit_fail=True
    if not (row["inside_processed_ranges"] and pass_debug):
        all_pass=False
    receipt["debug"].append(row)

receipt["targets_inside_processed_ranges"]=sum(x["inside_processed_ranges"] for x in receipt["debug"])
receipt["targets_debug_full_coverage"]=sum(x["debug_full_coverage_pass"] for x in receipt["debug"])
receipt["full_range_endpoints_inside_processed_ranges"]={"first":inside(FULL_RANGE[0]),"last":inside(FULL_RANGE[1])}
if all_pass:
    receipt["classification"]="CBT_COVERAGE_TARGETS_PASS"
elif explicit_fail:
    receipt["classification"]="CBT_COVERAGE_TARGETS_FAIL"
else:
    receipt["classification"]="CBT_COVERAGE_METADATA_INCONCLUSIVE"

Path("artifacts").mkdir(exist_ok=True)
Path("artifacts/ETH_STAKING_FLOW_001_CBT_COVERAGE_V0_2_1A.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,sort_keys=True))

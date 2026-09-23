#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys,collections
files=sorted(Path("monthly").glob("arq002_csp003_light_source_2022-*.json"))
r={"lab_id":"ARQ-002-CSP-003","gate":"LIGHT_SOURCE_CENSUS_2022_V0.1","classification":"RUNNING",
   "months":[],"economic_values_opened":False,"outcomes_opened":False,"errors":[]}
try:
    if len(files)!=12:raise RuntimeError(f"MONTH_COUNT:{len(files)}/12")
    miss=[];inv=[];days=0;dupes=0
    for p in files:
        x=json.loads(p.read_text())
        if x["classification"]!="SOURCE_MONTH_PASS":raise RuntimeError(f"MONTH_FAIL:{x['month']}:{x['errors']}")
        r["months"].append({"month":x["month"],"days_count":x["days_count"],"missing":x["metrics_missing_count"],
          "invalid":x["metrics_invalid_count"],"receipt_sha256":x["receipt_sha256"]})
        miss+=x["missing_slots"];inv+=x["invalid_slots"];days+=x["days_count"];dupes+=x["metrics_exact_dupes_removed"]
    if days!=365:raise RuntimeError(f"DAY_COUNT:{days}/365")
    r.update({"classification":"SOURCE_CENSUS_PASS","days_count":days,"missing_slots":miss,"invalid_slots":inv,
      "metrics_missing_count":len(miss),"metrics_invalid_count":len(inv),"metrics_exact_dupes_removed":dupes,
      "invalid_reason_counts":dict(collections.Counter(x["reason"] for x in inv))})
except Exception as e:
    r["classification"]="SOURCE_CENSUS_FAIL_CLOSED";r["errors"].append(f"{type(e).__name__}:{e}")
r["receipt_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(",",":")).encode()).hexdigest()
Path("ARQ002_CSP003_LIGHT_SOURCE_CENSUS_2022_V0.1.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":r["classification"],"missing":r.get("metrics_missing_count"),"invalid":r.get("metrics_invalid_count"),
"invalid_reasons":r.get("invalid_reason_counts"),"errors":r["errors"],"receipt_sha256":r["receipt_sha256"]},sort_keys=True))
sys.exit(0 if r["classification"]=="SOURCE_CENSUS_PASS" else 1)

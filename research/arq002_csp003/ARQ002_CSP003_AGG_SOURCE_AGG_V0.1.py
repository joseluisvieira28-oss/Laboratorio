#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
fs=sorted(Path("monthly").glob("arq002_csp003_agg_source_2022-*.json"))
r={"lab_id":"ARQ-002-CSP-003","gate":"AGG_SOURCE_CENSUS_2022_V0.1","classification":"RUNNING","months":[],"errors":[]}
try:
    if len(fs)!=12:raise RuntimeError(f"MONTH_COUNT:{len(fs)}/12")
    days=rows=0
    for p in fs:
        x=json.loads(p.read_text())
        if x["classification"]!="SOURCE_MONTH_PASS":raise RuntimeError(f"MONTH_FAIL:{x['month']}:{x['errors']}")
        r["months"].append({"month":x["month"],"days":x["days_count"],"rows_total":x["rows_total"],"receipt_sha256":x["receipt_sha256"]})
        days+=x["days_count"];rows+=x["rows_total"]
    if days!=365:raise RuntimeError(f"DAY_COUNT:{days}/365")
    r.update({"classification":"SOURCE_CENSUS_PASS","days_count":days,"agg_rows_total":rows})
except Exception as e:
    r["classification"]="SOURCE_CENSUS_FAIL_CLOSED";r["errors"].append(f"{type(e).__name__}:{e}")
r["receipt_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(",",":")).encode()).hexdigest()
Path("ARQ002_CSP003_AGG_SOURCE_CENSUS_2022_V0.1.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":r["classification"],"days":r.get("days_count"),"rows":r.get("agg_rows_total"),"errors":r["errors"],"receipt_sha256":r["receipt_sha256"]},sort_keys=True))
sys.exit(0 if r["classification"]=="SOURCE_CENSUS_PASS" else 1)

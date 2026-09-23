#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,calendar,sys
files=sorted(Path("monthly_receipts").glob("arq002_source_2024-*.json"))
rec={"lab_id":"ARQ-002-CSP-001","gate":"FULL_SOURCE_CENSUS_2024_V0.1","classification":"RUNNING",
     "months":[],"economic_values_reported":False,"outcomes_opened":False,
     "protected_2025_accessed":False,"protected_2026_accessed":False,"errors":[]}
try:
    if len(files)!=12: raise RuntimeError(f"MONTH_RECEIPT_COUNT:{len(files)}/12")
    total_days=0; total_agg=0; total_dupes=0
    warm=False
    for p in files:
        r=json.loads(p.read_text())
        if r.get("classification")!="SOURCE_MONTH_PASS": raise RuntimeError(f"MONTH_FAIL:{r.get('month')}:{r.get('errors')}")
        rec["months"].append({"month":r["month"],"days_count":r["days_count"],
                              "agg_rows_total":r["agg_rows_total"],
                              "metrics_exact_dupes_removed":r["metrics_exact_dupes_removed"],
                              "receipt_sha256":r["receipt_sha256"]})
        total_days+=r["days_count"]; total_agg+=r["agg_rows_total"]; total_dupes+=r["metrics_exact_dupes_removed"]
        if r["month"]=="2024-01":
            warm=bool(r.get("warmup",{}).get("pass"))
    if total_days!=366: raise RuntimeError(f"DAY_COUNT:{total_days}/366")
    if not warm: raise RuntimeError("WARMUP_FAIL")
    rec.update({"classification":"SOURCE_CENSUS_PASS","months_count":12,"days_count":total_days,
                "agg_rows_total":total_agg,"metrics_exact_dupes_removed":total_dupes,
                "warmup_2023_12_31_pass":True})
except Exception as e:
    rec["classification"]="SOURCE_CENSUS_FAIL_CLOSED"; rec["errors"].append(f"{type(e).__name__}:{e}")
rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
Path("ARQ002_CSP_FULL_SOURCE_CENSUS_2024_V0.1.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps(rec,sort_keys=True))
sys.exit(0 if rec["classification"]=="SOURCE_CENSUS_PASS" else 1)

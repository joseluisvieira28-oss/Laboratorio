#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys

files=sorted(Path("monthly_receipts").glob("arq002_csp002_source_2024-*.json"))
rec={"lab_id":"ARQ-002-CSP-002","gate":"FULL_SOURCE_CENSUS_2024_V0.1","classification":"RUNNING",
     "months":[],"economic_values_reported":False,"outcomes_opened":False,
     "protected_2025_accessed":False,"protected_2026_accessed":False,"errors":[]}
try:
    if len(files)!=12: raise RuntimeError(f"MONTH_RECEIPT_COUNT:{len(files)}/12")
    total_days=0; total_agg=0; total_obs=0; total_missing=0; total_dupes=0; missing=[]; warm=False
    for p in files:
        r=json.loads(p.read_text())
        if r.get("classification")!="SOURCE_MONTH_PASS":
            raise RuntimeError(f"MONTH_FAIL:{r.get('month')}:{r.get('errors')}")
        rec["months"].append({
          "month":r["month"],"days_count":r["days_count"],
          "agg_rows_total":r["agg_rows_total"],
          "metrics_observed_slots":r["metrics_observed_slots"],
          "metrics_missing_slots":r["metrics_missing_slots"],
          "metrics_exact_dupes_removed":r["metrics_exact_dupes_removed"],
          "receipt_sha256":r["receipt_sha256"]
        })
        total_days+=r["days_count"]; total_agg+=r["agg_rows_total"]
        total_obs+=r["metrics_observed_slots"]; total_missing+=r["metrics_missing_slots"]
        total_dupes+=r["metrics_exact_dupes_removed"]
        missing.extend(r["metrics_missing_timestamps_utc"])
        if r["month"]=="2024-01":
            warm=bool((r.get("warmup") or {}).get("pass"))
    if total_days!=366: raise RuntimeError(f"DAY_COUNT:{total_days}/366")
    if total_obs+total_missing!=366*288:
        raise RuntimeError(f"METRICS_SLOT_ACCOUNTING:{total_obs}+{total_missing}!={366*288}")
    if not warm: raise RuntimeError("WARMUP_FAIL")
    rec.update({
      "classification":"SOURCE_CENSUS_PASS",
      "months_count":12,"days_count":total_days,
      "agg_rows_total":total_agg,
      "metrics_expected_slots":366*288,
      "metrics_observed_slots":total_obs,
      "metrics_missing_slots":total_missing,
      "metrics_missing_timestamps_utc":sorted(missing),
      "metrics_exact_dupes_removed":total_dupes,
      "warmup_2023_12_31_pass":True
    })
except Exception as e:
    rec["classification"]="SOURCE_CENSUS_FAIL_CLOSED"; rec["errors"].append(f"{type(e).__name__}:{e}")
rec["receipt_sha256"]=hashlib.sha256(json.dumps(rec,sort_keys=True,separators=(",",":")).encode()).hexdigest()
Path("ARQ002_CSP002_FULL_SOURCE_CENSUS_2024_V0.1.json").write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps({
  "classification":rec["classification"],
  "days_count":rec.get("days_count"),
  "agg_rows_total":rec.get("agg_rows_total"),
  "metrics_expected_slots":rec.get("metrics_expected_slots"),
  "metrics_observed_slots":rec.get("metrics_observed_slots"),
  "metrics_missing_slots":rec.get("metrics_missing_slots"),
  "errors":rec["errors"],
  "receipt_sha256":rec["receipt_sha256"]
},sort_keys=True))
sys.exit(0 if rec["classification"]=="SOURCE_CENSUS_PASS" else 1)

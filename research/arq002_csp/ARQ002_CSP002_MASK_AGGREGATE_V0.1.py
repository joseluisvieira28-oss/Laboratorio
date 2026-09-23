#!/usr/bin/env python3
import json,hashlib,math,sys
from pathlib import Path
files=sorted(Path("mask_receipts").glob("arq002_csp002_mask_2024-*.json"))
r={"lab_id":"ARQ-002-CSP-002","classification":"RUNNING",
   "source_evidence_parent_run":35899452900,
   "strict_parent_passed_months":["2024-01","2024-03","2024-04","2024-05","2024-06","2024-07","2024-08","2024-09","2024-11","2024-12"],
   "rescanned_months":[],"masked_days":[],"economic_values_reported":False,"outcomes_opened":False,
   "protected_2025_accessed":False,"protected_2026_accessed":False,"errors":[]}
try:
    if len(files)!=2:raise RuntimeError(f"MASK_RECEIPTS:{len(files)}/2")
    elig=0;tot=0
    for p in files:
        x=json.loads(p.read_text())
        if x["classification"]!="SOURCE_MASK_MONTH_PASS":raise RuntimeError(f"MONTH_FAIL:{x['month']}")
        r["rescanned_months"].append({"month":x["month"],"eligible_days":x["eligible_days"],
                                      "total_days":x["total_days"],"masked_days":x["masked_days"],
                                      "receipt_sha256":x["receipt_sha256"]})
        elig+=x["eligible_days"];tot+=x["total_days"];r["masked_days"]+=x["masked_days"]
    # Ten strict-pass months contribute every calendar day: 366 - Feb(29) - Oct(31) = 306.
    total_eligible=306+elig
    coverage=total_eligible/366
    if coverage<0.99:raise RuntimeError(f"ANNUAL_COVERAGE:{coverage}")
    if sorted(r["masked_days"])!=["2024-02-16","2024-10-28"]:
        raise RuntimeError(f"MASK_LIST:{r['masked_days']}")
    r.update({"classification":"SOURCE_MASK_PASS","source_eligible_days":total_eligible,
              "calendar_days":366,"coverage_fraction":coverage,
              "coverage_percent":coverage*100})
except Exception as e:
    r["classification"]="SOURCE_MASK_FAIL_CLOSED";r["errors"].append(f"{type(e).__name__}:{e}")
r["receipt_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(",",":")).encode()).hexdigest()
Path("ARQ002_CSP002_SOURCE_MASK_RECEIPT_V0.1.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
print(json.dumps(r,sort_keys=True))
sys.exit(0 if r["classification"]=="SOURCE_MASK_PASS" else 1)

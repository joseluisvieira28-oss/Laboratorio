#!/usr/bin/env python3
from pathlib import Path
import json,hashlib
fs=sorted(Path("diag").glob("arq002_oi_diag_2024-*.json"))
r={"lab_id":"ARQ-002-SOURCE-DIAGNOSTIC","classification":"RUNNING","months":[],
   "invalid_oi_slots":[],"missing_slots":[],"returns_opened":False,"outcomes_opened":False,"errors":[]}
try:
  if len(fs)!=12:raise RuntimeError(f"MONTHS:{len(fs)}/12")
  for p in fs:
    x=json.loads(p.read_text())
    if x["classification"]!="SOURCE_DIAGNOSTIC_COMPLETE":raise RuntimeError(f"FAIL:{x['month']}")
    r["months"].append({"month":x["month"],"invalid_oi_count":x["invalid_oi_count"],"missing_count":x["missing_count"],"receipt_sha256":x["receipt_sha256"]})
    r["invalid_oi_slots"]+=x["invalid_oi_slots"];r["missing_slots"]+=x["missing_slots"]
  r["classification"]="SOURCE_DIAGNOSTIC_COMPLETE"
except Exception as e:
  r["classification"]="SOURCE_DIAGNOSTIC_FAIL_CLOSED";r["errors"].append(f"{type(e).__name__}:{e}")
r["invalid_oi_count"]=len(r["invalid_oi_slots"]);r["missing_count"]=len(r["missing_slots"])
r["receipt_sha256"]=hashlib.sha256(json.dumps(r,sort_keys=True,separators=(",",":")).encode()).hexdigest()
Path("ARQ002_OI_VALIDITY_DIAGNOSTIC_2024.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":r["classification"],"invalid_oi_count":r["invalid_oi_count"],"missing_count":r["missing_count"],"errors":r["errors"],"receipt_sha256":r["receipt_sha256"]},sort_keys=True))

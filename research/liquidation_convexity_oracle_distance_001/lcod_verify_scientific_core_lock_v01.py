#!/usr/bin/env python3
from __future__ import annotations
import json, subprocess
from pathlib import Path

HERE=Path("research/liquidation_convexity_oracle_distance_001")
LOCK=HERE/"LCOD_SCIENTIFIC_CORE_LOCK_V0.1.json"

lock=json.loads(LOCK.read_text())
errors=[]
actual={}
for path,expected in lock["files"].items():
    p=Path(path)
    if not p.exists():
        errors.append(f"MISSING_FILE:{path}")
        continue
    got=subprocess.check_output(["git","hash-object",str(p)],text=True).strip()
    actual[path]=got
    if got!=expected:
        errors.append(f"BLOB_MISMATCH:{path}:{expected}:{got}")

out={
  "lab_id":lock["lab_id"],
  "stage":"SCIENTIFIC_CORE_LOCK_VERIFICATION_V0.1",
  "classification":"SCIENTIFIC_CORE_LOCK_PASS" if not errors else "SCIENTIFIC_CORE_LOCK_FAIL",
  "scientific_core_fingerprint_sha256":lock["scientific_core_fingerprint_sha256"],
  "expected_files":lock["files"],
  "actual_files":actual,
  "errors":errors,
  "market_returns_opened":False,
  "liquidation_outcomes_opened":False,
  "pnl_opened":False,
  "promotion_credit":0
}
print(json.dumps(out,indent=2,sort_keys=True))
if errors:
    raise SystemExit(2)

#!/usr/bin/env python3
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

HERE=Path("research/liquidation_convexity_oracle_distance_001")
DIR=HERE/"forward_snapshots"
OUT=HERE/"LCOD_FORWARD_SERIES_INDEX_V0.1.json"

rows=[]
for p in sorted(DIR.glob("LCOD_FORWARD_SNAPSHOT_BLOCK_*.json")):
    try:
        x=json.loads(p.read_text())
    except Exception:
        rows.append({"file":p.name,"classification":"UNREADABLE"})
        continue
    rows.append({
        "file":p.name,
        "classification":x.get("classification"),
        "observation_role":x.get("observation_role"),
        "captured_at_utc":x.get("captured_at_utc"),
        "ethereum_block_number":x.get("ethereum_block_number"),
        "ethereum_block_hash":x.get("ethereum_block_hash"),
        "snapshot_sha256":x.get("snapshot_sha256"),
        "curve_sha256":x.get("curve",{}).get("curve_sha256"),
        "market_returns_opened":x.get("market_returns_opened"),
        "future_liquidation_outcomes_opened":x.get("future_liquidation_outcomes_opened"),
        "pnl_opened":x.get("pnl_opened"),
        "mutation":x.get("mutation")
    })

bad_boundary=[
    r for r in rows
    if r.get("market_returns_opened") is not False
    or r.get("future_liquidation_outcomes_opened") is not False
    or r.get("pnl_opened") is not False
    or r.get("mutation") is not False
]

valid=[
    r for r in rows
    if r.get("classification")=="FORWARD_MECHANICAL_SNAPSHOT_PASS"
    and r.get("observation_role")=="FORWARD_OBSERVATION"
    and r not in bad_boundary
]

def utc_day(s):
    if not s:return None
    return s[:10]

by_day={}
duplicates=[]
for r in sorted(valid,key=lambda z:(z.get("captured_at_utc") or "",z.get("ethereum_block_number") or 0)):
    d=utc_day(r.get("captured_at_utc"))
    if not d: continue
    if d in by_day:
        duplicates.append({"utc_day":d,"counted":by_day[d]["file"],"ignored":r["file"]})
    else:
        by_day[d]=r

canonical=list(by_day.values())
distinct_days=len(by_day)
count=len(canonical)
ready=count>=30 and distinct_days>=21 and not bad_boundary
classification=(
    "PREDICTOR_ONLY_VIABILITY_GATE_READY"
    if ready else
    "FORWARD_SERIES_BOUNDARY_BLOCKED"
    if bad_boundary else
    "FORWARD_SERIES_ACCUMULATING"
)

out={
  "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
  "stage":"PROSPECTIVE_MECHANICAL_STATE_SERIES_INDEX_V0.1",
  "captured_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "classification":classification,
  "canonical_successful_daily_observation_count":count,
  "distinct_utc_day_count":distinct_days,
  "required_observations":30,
  "required_distinct_utc_days":21,
  "diagnostic_or_noncanonical_file_count":len(rows)-len(valid),
  "duplicate_same_day_observation_count":len(duplicates),
  "boundary_violation_count":len(bad_boundary),
  "canonical_observations":canonical,
  "duplicates_ignored":duplicates,
  "boundary_violations":bad_boundary,
  "market_returns_opened":False,
  "future_liquidation_outcomes_opened":False,
  "pnl_opened":False,
  "mutation":False
}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
if bad_boundary:
    raise SystemExit(2)

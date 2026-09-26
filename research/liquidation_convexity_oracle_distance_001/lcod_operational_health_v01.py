#!/usr/bin/env python3
from __future__ import annotations

import json, os
from datetime import datetime, timezone, time
from pathlib import Path

HERE=Path("research/liquidation_convexity_oracle_distance_001")
INDEX=HERE/"LCOD_FORWARD_SERIES_INDEX_V0.1.json"
SNAPDIR=HERE/"forward_snapshots"
OUT=Path("artifacts/lcod_operational_health_v01.json")

raw=os.environ.get("HEARTBEAT_UTC")
dt=(datetime.fromisoformat(raw.replace("Z","+00:00")).astimezone(timezone.utc)
    if raw else datetime.now(timezone.utc))
today=dt.date().isoformat()
now_t=dt.time().replace(tzinfo=None)

idx=json.loads(INDEX.read_text())
same_day=[]
latest=None
for p in sorted(SNAPDIR.glob("LCOD_FORWARD_SNAPSHOT_BLOCK_*.json")):
    try:
        x=json.loads(p.read_text())
    except Exception:
        continue
    if x.get("classification")!="FORWARD_MECHANICAL_SNAPSHOT_PASS":
        continue
    if x.get("observation_role")!="FORWARD_OBSERVATION":
        continue
    ts=str(x.get("captured_at_utc",""))
    if latest is None or ts>str(latest.get("captured_at_utc","")):
        latest={"file":p.name,"captured_at_utc":ts,"block":x.get("ethereum_block_number"),"snapshot_sha256":x.get("snapshot_sha256")}
    if ts[:10]==today:
        same_day.append({"file":p.name,"captured_at_utc":ts,"block":x.get("ethereum_block_number")})

boundary=int(idx.get("boundary_violation_count",0))
dupes=int(idx.get("duplicate_same_day_observation_count",0))

if boundary:
    classification="BOUNDARY_BLOCKED"
elif dupes:
    classification="DUPLICATE_WARNING"
elif same_day:
    classification="HEALTHY_CANONICAL_DAY_PRESENT"
elif now_t < time(3,17):
    classification="BEFORE_CANONICAL_WINDOW"
elif now_t < time(12,0):
    classification="RECOVERY_WINDOW_OPEN_NO_OBSERVATION"
else:
    classification="MISSED_CANONICAL_DAY"

out={
  "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
  "stage":"FORWARD_OPERATIONAL_HEALTH_V0.1",
  "heartbeat_utc":dt.isoformat().replace("+00:00","Z"),
  "utc_day":today,
  "classification":classification,
  "same_day_canonical_observations":same_day,
  "same_day_canonical_count":len(same_day),
  "canonical_successful_daily_observation_count":idx.get("canonical_successful_daily_observation_count"),
  "distinct_utc_day_count":idx.get("distinct_utc_day_count"),
  "required_observations":idx.get("required_observations"),
  "required_distinct_utc_days":idx.get("required_distinct_utc_days"),
  "boundary_violation_count":boundary,
  "duplicate_same_day_observation_count":dupes,
  "latest_canonical_observation":latest,
  "market_returns_opened":False,
  "future_liquidation_outcomes_opened":False,
  "pnl_opened":False,
  "mutation":False,
  "promotion_credit":0
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))

if classification in ("BOUNDARY_BLOCKED","DUPLICATE_WARNING","MISSED_CANONICAL_DAY"):
    raise SystemExit(2)

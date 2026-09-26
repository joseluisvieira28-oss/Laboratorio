#!/usr/bin/env python3
from __future__ import annotations
import json, math
from pathlib import Path

HERE=Path("research/reth_nav_dislocation_001")
RECEIPT=HERE/"RETH_PREDICTOR_ONLY_CENSUS_RECEIPT_V0.1.json"
ROWS=HERE/"RETH_PREDICTOR_ONLY_CENSUS_ROWS_V0.1.json"
OUT=HERE/"RETH_STATE_CALIBRATION_RECEIPT_V0.1.json"

receipt=json.loads(RECEIPT.read_text())
rows_obj=json.loads(ROWS.read_text())

if receipt.get("classification")!="PREDICTOR_SOURCE_CENSUS_PASS":
    raise SystemExit("PREDICTOR_CENSUS_NOT_PASS")
rows=rows_obj.get("rows",[])
if len(rows)!=556 or receipt.get("valid_count")!=556 or receipt.get("invalid_count")!=0:
    raise SystemExit("CENSUS_NOT_EXACT_556_556")
if rows_obj.get("row_set_sha256")!=receipt.get("row_set_sha256"):
    raise SystemExit("ROW_SET_SHA_MISMATCH")

vals=[]
for r in rows:
    n=int(r["dislocation_exact"]["numerator"])
    d=int(r["dislocation_exact"]["denominator"])
    if d<=0: raise SystemExit("BAD_DENOMINATOR")
    vals.append((n,d,r))

# Exact rational ordering via cross multiplication.
def cmp_key(item):
    # Python key cannot compare rationals exactly directly; use Fraction.
    from fractions import Fraction
    return Fraction(item[0],item[1])

ordered=sorted(vals,key=cmp_key)

def nearest_rank(p):
    rank=max(1,math.ceil(p*len(ordered)))
    n,d,r=ordered[rank-1]
    return {
      "nearest_rank":rank,
      "numerator":str(n),
      "denominator":str(d),
      "ppb_trunc":str((n*1_000_000_000)//d),
      "source_index":r["index"],
      "source_block_number":r["block_number"]
    }

q05=nearest_rank(0.05)
q95=nearest_rank(0.95)

# Exact q05 < q95
if int(q05["numerator"])*int(q95["denominator"]) >= int(q95["numerator"])*int(q05["denominator"]):
    raise SystemExit("Q05_NOT_LESS_THAN_Q95")

discount=0
premium=0
neutral=0
for n,d,_ in vals:
    if n*int(q05["denominator"]) <= int(q05["numerator"])*d:
        discount+=1
    elif n*int(q95["denominator"]) >= int(q95["numerator"])*d:
        premium+=1
    else:
        neutral+=1

out={
  "lab_id":"RETH-NAV-DISLOCATION-001",
  "stage":"PREDICTOR_STATE_CALIBRATION_V0.1",
  "classification":"PREDICTOR_STATE_CALIBRATION_PASS",
  "source_census_row_set_sha256":receipt["row_set_sha256"],
  "source_count":556,
  "quantile_rule":{
    "method":"nearest_rank",
    "q05":q05,
    "q95":q95
  },
  "calibration_state_counts":{
    "DISCOUNT_EXTREME":discount,
    "NEUTRAL":neutral,
    "PREMIUM_EXTREME":premium
  },
  "direction_opened":false,
  "market_returns_opened":false,
  "holding_horizon_outcomes_opened":false,
  "pnl_opened":false,
  "mutation":false,
  "promotion_credit":0
}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))

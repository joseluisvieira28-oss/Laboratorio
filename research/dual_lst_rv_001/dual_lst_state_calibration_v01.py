#!/usr/bin/env python3
from __future__ import annotations
import json, math
from fractions import Fraction
from pathlib import Path

HERE=Path("research/dual_lst_rv_001")
REC=HERE/"DUAL_LST_PREDICTOR_CENSUS_RECEIPT_V0.1.json"
ROWS=HERE/"DUAL_LST_PREDICTOR_CENSUS_ROWS_V0.1.json"
OUT=HERE/"DUAL_LST_STATE_CALIBRATION_RECEIPT_V0.1.json"

rec=json.loads(REC.read_text())
rows_obj=json.loads(ROWS.read_text())

if rec.get("classification")!="PREDICTOR_CENSUS_PASS":
    raise SystemExit("PREDICTOR_CENSUS_NOT_PASS")
if rec.get("valid_count")!=556 or rec.get("invalid_count")!=0:
    raise SystemExit("PREDICTOR_CENSUS_NOT_EXACT_556")
if rows_obj.get("row_set_sha256")!=rec.get("row_set_sha256"):
    raise SystemExit("ROW_SET_SHA_MISMATCH")

rows=rows_obj.get("rows",[])
if len(rows)!=556:
    raise SystemExit("ROW_COUNT_NOT_556")

vals=[]
for r in rows:
    if r.get("valid") is not True:
        raise SystemExit("INVALID_CENSUS_ROW:"+str(r.get("index")))
    obj=r.get("dislocation_exact")
    if not obj:
        raise SystemExit("MISSING_DISLOCATION:"+str(r.get("index")))
    den=int(obj["denominator"])
    if den<=0:
        raise SystemExit("NONPOSITIVE_DEN:"+str(r.get("index")))
    vals.append((Fraction(int(obj["numerator"]),den),r))

ordered=sorted(vals,key=lambda x:x[0])

def nearest_rank(p:float):
    rank=max(1,math.ceil(p*len(ordered)))
    frac,row=ordered[rank-1]
    return {
      "nearest_rank":rank,
      "numerator":str(frac.numerator),
      "denominator":str(frac.denominator),
      "ppb_trunc":str((frac.numerator*1_000_000_000)//frac.denominator),
      "source_index":row["index"],
      "source_block_number":row["block_number"]
    }

q10=nearest_rank(0.10)
q90=nearest_rank(0.90)
fq10=Fraction(int(q10["numerator"]),int(q10["denominator"]))
fq90=Fraction(int(q90["numerator"]),int(q90["denominator"]))
if fq10>=fq90:
    raise SystemExit("Q10_NOT_LESS_THAN_Q90")

cheap=neutral=rich=0
for frac,_ in vals:
    if frac<=fq10: cheap+=1
    elif frac>=fq90: rich+=1
    else: neutral+=1

out={
  "lab_id":"DUAL-LST-RV-001",
  "stage":"PREDICTOR_STATE_CALIBRATION_V0.1",
  "classification":"PREDICTOR_STATE_CALIBRATION_PASS",
  "source_census_row_set_sha256":rec["row_set_sha256"],
  "source_count":556,
  "selected_pool":rec.get("selected_pool"),
  "quantile_rule":{"method":"nearest_rank","q10":q10,"q90":q90},
  "calibration_state_counts":{
    "RETH_CHEAP_EXTREME":cheap,
    "NEUTRAL":neutral,
    "RETH_RICH_EXTREME":rich
  },
  "future_returns_opened":False,
  "convergence_outcomes_opened":False,
  "direction_pnl_opened":False,
  "pnl_opened":False,
  "mutation":False,
  "promotion_credit":0
}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))

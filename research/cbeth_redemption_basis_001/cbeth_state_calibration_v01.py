#!/usr/bin/env python3
from __future__ import annotations
import json, math
from fractions import Fraction
from pathlib import Path

HERE=Path("research/cbeth_redemption_basis_001")
REC=HERE/"PREDICTOR_CENSUS_RECEIPT_V0.1.json"
ROWS=HERE/"PREDICTOR_CENSUS_ROWS_V0.1.json"
OUT=HERE/"STATE_CALIBRATION_RECEIPT_V0.1.json"

rec=json.loads(REC.read_text())
rows_obj=json.loads(ROWS.read_text())

if rec.get("classification")!="PREDICTOR_CENSUS_PASS":
    raise SystemExit("PREDICTOR_CENSUS_NOT_PASS")
if rows_obj.get("row_set_sha256")!=rec.get("row_set_sha256"):
    raise SystemExit("ROW_SET_SHA_MISMATCH")

rows=rows_obj.get("rows",[])
by_day={r["utc_day"]:r for r in rows if r.get("valid") is True}
cal=[r for r in rows if "2023-04-01" <= r.get("utc_day","") <= "2024-06-30"]

expected=457
if len(cal)!=expected:
    raise SystemExit(f"CALIBRATION_DAY_COUNT:{len(cal)}:{expected}")

vals=[]
for r in cal:
    if r.get("valid") is not True:
        raise SystemExit("INVALID_CALIBRATION_DAY:"+r.get("utc_day","?"))
    obj=r.get("signed_basis_exact")
    if not obj:
        raise SystemExit("MISSING_BASIS:"+r["utc_day"])
    den=int(obj["denominator"])
    if den<=0:
        raise SystemExit("NONPOSITIVE_DEN:"+r["utc_day"])
    vals.append((Fraction(int(obj["numerator"]),den),r["utc_day"]))

ordered=sorted(vals,key=lambda x:x[0])

def nearest_rank(p:float):
    rank=max(1,math.ceil(p*len(ordered)))
    frac,day=ordered[rank-1]
    return {
      "nearest_rank":rank,
      "numerator":str(frac.numerator),
      "denominator":str(frac.denominator),
      "ppb_trunc":str((frac.numerator*1_000_000_000)//frac.denominator),
      "source_day":day
    }

q10=nearest_rank(.10)
q90=nearest_rank(.90)
fq10=Fraction(int(q10["numerator"]),int(q10["denominator"]))
fq90=Fraction(int(q90["numerator"]),int(q90["denominator"]))
if fq10>=fq90:
    raise SystemExit("Q10_NOT_LESS_THAN_Q90")

neg=neu=pos=0
for f,_ in vals:
    if f<=fq10: neg+=1
    elif f>=fq90: pos+=1
    else: neu+=1

out={
  "lab_id":"CBETH-REDEMPTION-BASIS-001",
  "stage":"PREDICTOR_STATE_CALIBRATION_V0.1",
  "classification":"STATE_CALIBRATION_PASS",
  "source_census_row_set_sha256":rec["row_set_sha256"],
  "calibration_period":{"start":"2023-04-01","end":"2024-06-30"},
  "calibration_day_count":len(vals),
  "quantile_rule":{"method":"nearest_rank","q10":q10,"q90":q90},
  "calibration_state_counts":{"DISCOUNT_EXTREME":neg,"NEUTRAL":neu,"PREMIUM_EXTREME":pos},
  "future_mechanism_outcomes_opened":False,
  "market_returns_opened":False,
  "oos_2025_opened":False,
  "protected_2026_opened":False,
  "pnl_opened":False,
  "promotion_credit":0
}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))

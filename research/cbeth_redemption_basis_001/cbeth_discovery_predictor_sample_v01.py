#!/usr/bin/env python3
from __future__ import annotations
import json
from fractions import Fraction
from pathlib import Path
from datetime import date,timedelta

HERE=Path("research/cbeth_redemption_basis_001")
REC=HERE/"PREDICTOR_CENSUS_RECEIPT_V0.1.json"
ROWS=HERE/"PREDICTOR_CENSUS_ROWS_V0.1.json"
CAL=HERE/"STATE_CALIBRATION_RECEIPT_V0.1.json"
OUT=HERE/"DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json"
OUTROWS=HERE/"DISCOVERY_PREDICTOR_SAMPLE_ROWS_V0.1.json"

rec=json.loads(REC.read_text())
rows_obj=json.loads(ROWS.read_text())
cal=json.loads(CAL.read_text())

if rec.get("classification")!="PREDICTOR_CENSUS_PASS":
    raise SystemExit("PREDICTOR_CENSUS_NOT_PASS")
if cal.get("classification")!="STATE_CALIBRATION_PASS":
    raise SystemExit("CALIBRATION_NOT_PASS")
if rows_obj.get("row_set_sha256")!=rec.get("row_set_sha256"):
    raise SystemExit("ROW_SET_SHA_MISMATCH")

q10=cal["quantile_rule"]["q10"]
q90=cal["quantile_rule"]["q90"]
fq10=Fraction(int(q10["numerator"]),int(q10["denominator"]))
fq90=Fraction(int(q90["numerator"]),int(q90["denominator"]))

by_day={r["utc_day"]:r for r in rows_obj.get("rows",[])}

def days(start,end):
    d=date.fromisoformat(start); e=date.fromisoformat(end)
    out=[]
    while d<=e:
        out.append(d.isoformat())
        d+=timedelta(days=1)
    return out

def classify(r):
    if r.get("valid") is not True:
        raise ValueError("INVALID_DAY:"+r.get("utc_day","?"))
    obj=r.get("signed_basis_exact")
    if not obj:
        raise ValueError("MISSING_BASIS:"+r["utc_day"])
    f=Fraction(int(obj["numerator"]),int(obj["denominator"]))
    if f<=fq10: return "DISCOUNT_EXTREME",f
    if f>=fq90: return "PREMIUM_EXTREME",f
    return "NEUTRAL",f

errors=[]
pred_day="2024-06-30"
try:
    pred_state,_=classify(by_day[pred_day])
except Exception as e:
    pred_state=None
    errors.append("PREDECESSOR:"+str(e))

rows=[]
for d in days("2024-07-01","2024-12-31"):
    try:
        r=by_day[d]
        state,f=classify(r)
        rows.append({
          "utc_day":d,
          "state":state,
          "signed_basis_exact":{"numerator":str(f.numerator),"denominator":str(f.denominator)},
          "signed_basis_ppb_trunc":str((f.numerator*1_000_000_000)//f.denominator),
          "block_number":r["block_number"],
          "block_hash":r["block_hash"]
        })
    except Exception as e:
        errors.append("DISCOVERY_DAY:"+d+":"+str(e))

events=[]
prev=pred_state
for r in rows:
    d=r["state"]=="DISCOUNT_EXTREME" and prev!="DISCOUNT_EXTREME"
    p=r["state"]=="PREMIUM_EXTREME" and prev!="PREMIUM_EXTREME"
    if d or p:
        events.append({
          "utc_day":r["utc_day"],
          "state":r["state"],
          "signed_basis_exact":r["signed_basis_exact"],
          "signed_basis_ppb_trunc":r["signed_basis_ppb_trunc"],
          "block_number":r["block_number"],
          "block_hash":r["block_hash"]
        })
    prev=r["state"]

dc=sum(1 for e in events if e["state"]=="DISCOUNT_EXTREME")
pc=sum(1 for e in events if e["state"]=="PREMIUM_EXTREME")

if errors or len(rows)!=184:
    classification="PREDICTOR_SOURCE_BLOCKED"
elif len(events)<20 or dc<6 or pc<6:
    classification="PREDICTOR_INSUFFICIENT_SAMPLE"
else:
    classification="PREDICTOR_SAMPLE_PASS"

out={
  "lab_id":"CBETH-REDEMPTION-BASIS-001",
  "stage":"DISCOVERY_PREDICTOR_SAMPLE_GATE_V0.1",
  "classification":classification,
  "discovery_period":{"start":"2024-07-01","end":"2024-12-31"},
  "boundary_predecessor_day":pred_day,
  "q10":q10,"q90":q90,
  "valid_day_count":len(rows),
  "expected_day_count":184,
  "transition_event_count":len(events),
  "discount_extreme_event_count":dc,
  "premium_extreme_event_count":pc,
  "errors":errors,
  "future_mechanism_outcomes_opened":False,
  "market_returns_opened":False,
  "oos_2025_opened":False,
  "protected_2026_opened":False,
  "pnl_opened":False,
  "promotion_credit":0
}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
OUTROWS.write_text(json.dumps({"lab_id":out["lab_id"],"rows":rows,"events":events},indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
if classification=="PREDICTOR_SOURCE_BLOCKED":
    raise SystemExit(2)

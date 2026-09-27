#!/usr/bin/env python3
from __future__ import annotations
import json, random
from fractions import Fraction
from pathlib import Path
from datetime import date,timedelta

HERE=Path("research/cbeth_redemption_basis_001")
REC=HERE/"PREDICTOR_CENSUS_RECEIPT_V0.1.json"
ROWS=HERE/"PREDICTOR_CENSUS_ROWS_V0.1.json"
SAMPLE=HERE/"DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json"
SROWS=HERE/"DISCOVERY_PREDICTOR_SAMPLE_ROWS_V0.1.json"
OUT=HERE/"MECHANISM_DISCOVERY_RESULT_V0.1.json"

rec=json.loads(REC.read_text())
rows_obj=json.loads(ROWS.read_text())
sample=json.loads(SAMPLE.read_text())
srows=json.loads(SROWS.read_text())

if rec.get("classification")!="PREDICTOR_CENSUS_PASS":
    raise SystemExit("PREDICTOR_CENSUS_NOT_PASS")
if sample.get("classification")!="PREDICTOR_SAMPLE_PASS":
    raise SystemExit("PREDICTOR_SAMPLE_NOT_PASS")
if sample.get("future_mechanism_outcomes_opened") is not False:
    raise SystemExit("SAMPLE_BOUNDARY_ALREADY_OPEN")
if rows_obj.get("row_set_sha256")!=rec.get("row_set_sha256"):
    raise SystemExit("ROW_SET_SHA_MISMATCH")

events=srows.get("events",[])
if len(events)!=sample.get("transition_event_count"):
    raise SystemExit("EVENT_COUNT_MISMATCH")

eligible=[e for e in events if e["utc_day"]<="2024-12-19"]
dc=[e for e in eligible if e["state"]=="DISCOUNT_EXTREME"]
pc=[e for e in eligible if e["state"]=="PREMIUM_EXTREME"]

base={
  "lab_id":"CBETH-REDEMPTION-BASIS-001",
  "stage":"MECHANISM_DISCOVERY_V0.1",
  "primary_horizon_calendar_days":12,
  "secondary_diagnostic_calendar_days":3,
  "predictor_event_count":len(events),
  "mechanism_eligible_event_count":len(eligible),
  "eligible_discount_event_count":len(dc),
  "eligible_premium_event_count":len(pc),
  "market_returns_opened":False,
  "oos_2025_opened":False,
  "protected_2026_opened":False,
  "pnl_opened":False,
  "mutation":False,
  "promotion_credit":0
}

# Critical firewall: do not read any future basis row unless the frozen
# boundary-censored sample minimum has already passed.
if len(eligible)<20 or len(dc)<6 or len(pc)<6:
    base.update({
      "classification":"MECHANISM_OUTCOME_INSUFFICIENT_SAMPLE",
      "future_mechanism_outcomes_opened":False,
      "rows":[]
    })
    OUT.write_text(json.dumps(base,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in base.items() if k!="rows"},indent=2,sort_keys=True))
    raise SystemExit(0)

by_day={r["utc_day"]:r for r in rows_obj.get("rows",[]) if r.get("valid") is True}

def plus(day:str,n:int)->str:
    return (date.fromisoformat(day)+timedelta(days=n)).isoformat()

def basis_from_obj(obj)->Fraction:
    return Fraction(int(obj["numerator"]),int(obj["denominator"]))

result_rows=[]
for i,e in enumerate(eligible):
    t=e["utc_day"]
    entry=basis_from_obj(e["signed_basis_exact"])
    fday=plus(t,12)
    future_row=by_day.get(fday)
    if not future_row:
        raise SystemExit("MISSING_PRIMARY_FUTURE_DAY:"+t+":"+fday)
    future=basis_from_obj(future_row["signed_basis_exact"])

    if e["state"]=="DISCOUNT_EXTREME":
        closure=future-entry
    elif e["state"]=="PREMIUM_EXTREME":
        closure=entry-future
    else:
        raise SystemExit("NON_EXTREME_EVENT:"+t)

    d3=plus(t,3)
    diag_row=by_day.get(d3)
    diag=None
    if diag_row:
        b3=basis_from_obj(diag_row["signed_basis_exact"])
        diag=(b3-entry) if e["state"]=="DISCOUNT_EXTREME" else (entry-b3)

    result_rows.append({
      "event_index":i,
      "event_day":t,
      "state":e["state"],
      "entry_basis_exact":{"numerator":str(entry.numerator),"denominator":str(entry.denominator)},
      "future_12d_day":fday,
      "future_12d_basis_exact":{"numerator":str(future.numerator),"denominator":str(future.denominator)},
      "signed_closure_12d_exact":{"numerator":str(closure.numerator),"denominator":str(closure.denominator)},
      "signed_closure_3d_diagnostic_exact":None if diag is None else {"numerator":str(diag.numerator),"denominator":str(diag.denominator)}
    })

vals=[basis_from_obj(r["signed_closure_12d_exact"]) for r in result_rows]
dvals=[basis_from_obj(r["signed_closure_12d_exact"]) for r in result_rows if r["state"]=="DISCOUNT_EXTREME"]
pvals=[basis_from_obj(r["signed_closure_12d_exact"]) for r in result_rows if r["state"]=="PREMIUM_EXTREME"]
diagvals=[
    basis_from_obj(r["signed_closure_3d_diagnostic_exact"])
    for r in result_rows if r["signed_closure_3d_diagnostic_exact"] is not None
]

def mean(xs):
    return sum(xs,Fraction(0,1))/len(xs)

def fstr(x:Fraction|None):
    if x is None: return None
    return format(float(x),".18g")

rng=random.Random(20260927)
boots=[]
n=len(vals)
for _ in range(10_000):
    boots.append(mean([vals[rng.randrange(n)] for __ in range(n)]))
boots.sort()
lo=boots[249]
hi=boots[9749]

pooled=mean(vals)
dm=mean(dvals)
pm=mean(pvals)
passed=pooled>0 and lo>0 and dm>0 and pm>0
classification="MECHANISM_DISCOVERY_PASS" if passed else "MECHANISM_DISCOVERY_FAIL"

base.update({
  "classification":classification,
  "future_mechanism_outcomes_opened":True,
  "pooled_mean_signed_closure_12d":fstr(pooled),
  "discount_mean_signed_closure_12d":fstr(dm),
  "premium_mean_signed_closure_12d":fstr(pm),
  "bootstrap":{
    "seed":20260927,
    "resamples":10000,
    "percentile_95_lower":fstr(lo),
    "percentile_95_upper":fstr(hi)
  },
  "secondary_3d_diagnostic":{
    "valid_count":len(diagvals),
    "mean_signed_closure":None if not diagvals else fstr(mean(diagvals)),
    "can_rescue_primary":False
  },
  "rows":result_rows
})
OUT.write_text(json.dumps(base,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in base.items() if k!="rows"},indent=2,sort_keys=True))

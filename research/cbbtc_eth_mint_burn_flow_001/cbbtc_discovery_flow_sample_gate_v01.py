#!/usr/bin/env python3
from __future__ import annotations
import json
from fractions import Fraction
from pathlib import Path
from datetime import date, timedelta

HERE=Path("research/cbbtc_eth_mint_burn_flow_001")
REC=HERE/"FLOW_CENSUS_RECEIPT_V0.1.json"
DAILY=HERE/"DAILY_FLOW_V0.1.json"
CAL=HERE/"FLOW_STATE_CALIBRATION_RECEIPT_V0.1.json"
OUT=HERE/"DISCOVERY_FLOW_PREDICTOR_SAMPLE_RECEIPT_V0.1.json"
ROWS=HERE/"DISCOVERY_FLOW_PREDICTOR_SAMPLE_ROWS_V0.1.json"

rec=json.loads(REC.read_text())
daily_obj=json.loads(DAILY.read_text())
cal=json.loads(CAL.read_text())

if rec.get("classification")!="PREDICTOR_FLOW_CENSUS_PASS":
    raise SystemExit("FLOW_CENSUS_NOT_PASS")
if cal.get("classification")!="FLOW_STATE_CALIBRATION_PASS":
    raise SystemExit("FLOW_CALIBRATION_NOT_PASS")

q10=cal["quantile_rule"]["q10"]
q90=cal["quantile_rule"]["q90"]
fq10=Fraction(int(q10["numerator"]),int(q10["denominator"]))
fq90=Fraction(int(q90["numerator"]),int(q90["denominator"]))

by_day={r["utc_day"]:r for r in daily_obj.get("days",[])}

def dates(start,end):
    d=date.fromisoformat(start); e=date.fromisoformat(end)
    out=[]
    while d<=e:
        out.append(d.isoformat()); d+=timedelta(days=1)
    return out

def classify(r):
    obj=r.get("net_flow_rate_exact")
    if not obj:
        raise ValueError("MISSING_RATE:"+r["utc_day"])
    den=int(obj["denominator"])
    if den<=0:
        raise ValueError("NONPOSITIVE_DEN:"+r["utc_day"])
    f=Fraction(int(obj["numerator"]),den)
    if f<=fq10: return "NEGATIVE_EXTREME",f
    if f>=fq90: return "POSITIVE_EXTREME",f
    return "NEUTRAL",f

errors=[]
pred_day="2025-06-30"
if pred_day not in by_day:
    errors.append("MISSING_PREDECESSOR")
    pred_state=None
else:
    try:
        pred_state,_=classify(by_day[pred_day])
    except Exception as e:
        errors.append(str(e)); pred_state=None

rows=[]
for d in dates("2025-07-01","2025-12-31"):
    r=by_day.get(d)
    if not r:
        errors.append("MISSING_DAY:"+d)
        continue
    try:
        state,f=classify(r)
        rows.append({
          "utc_day":d,
          "state":state,
          "net_flow_rate_exact":{"numerator":str(f.numerator),"denominator":str(f.denominator)},
          "net_flow_rate_ppb_trunc":str((f.numerator*1_000_000_000)//f.denominator),
          "mint_count":r["mint_count"],
          "burn_count":r["burn_count"],
          "net_mint_minus_burn_raw":r["net_mint_minus_burn_raw"],
          "prior_supply_raw":r["prior_supply_raw"]
        })
    except Exception as e:
        errors.append(str(e))

events=[]
prev=pred_state
for r in rows:
    is_neg=r["state"]=="NEGATIVE_EXTREME" and prev!="NEGATIVE_EXTREME"
    is_pos=r["state"]=="POSITIVE_EXTREME" and prev!="POSITIVE_EXTREME"
    if is_neg or is_pos:
        events.append({
          "utc_day":r["utc_day"],
          "state":r["state"],
          "net_flow_rate_exact":r["net_flow_rate_exact"],
          "net_flow_rate_ppb_trunc":r["net_flow_rate_ppb_trunc"]
        })
    prev=r["state"]

neg=sum(1 for e in events if e["state"]=="NEGATIVE_EXTREME")
pos=sum(1 for e in events if e["state"]=="POSITIVE_EXTREME")

if errors:
    classification="FLOW_PREDICTOR_SOURCE_BLOCKED"
elif len(rows)!=184:
    classification="FLOW_PREDICTOR_SOURCE_BLOCKED"
elif len(events)<20 or neg<6 or pos<6:
    classification="FLOW_PREDICTOR_INSUFFICIENT_SAMPLE"
else:
    classification="FLOW_PREDICTOR_SAMPLE_PASS"

out={
  "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
  "stage":"DISCOVERY_FLOW_PREDICTOR_SAMPLE_GATE_V0.1",
  "classification":classification,
  "discovery_period":{"start":"2025-07-01","end":"2025-12-31"},
  "boundary_predecessor_day":pred_day,
  "q10":q10,"q90":q90,
  "valid_day_count":len(rows),
  "expected_day_count":184,
  "transition_event_count":len(events),
  "negative_extreme_event_count":neg,
  "positive_extreme_event_count":pos,
  "errors":errors,
  "market_returns_opened":False,
  "direction_opened":False,
  "pnl_opened":False,
  "protected_2026_opened":False,
  "promotion_credit":0
}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
ROWS.write_text(json.dumps({"lab_id":out["lab_id"],"rows":rows,"events":events},indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))
if classification=="FLOW_PREDICTOR_SOURCE_BLOCKED":
    raise SystemExit(2)

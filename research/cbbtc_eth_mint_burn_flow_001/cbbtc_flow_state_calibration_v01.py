#!/usr/bin/env python3
from __future__ import annotations
import json, math
from fractions import Fraction
from pathlib import Path

HERE=Path("research/cbbtc_eth_mint_burn_flow_001")
REC=HERE/"FLOW_CENSUS_RECEIPT_V0.1.json"
DAILY=HERE/"DAILY_FLOW_V0.1.json"
OUT=HERE/"FLOW_STATE_CALIBRATION_RECEIPT_V0.1.json"

rec=json.loads(REC.read_text())
daily_obj=json.loads(DAILY.read_text())

if rec.get("classification")!="PREDICTOR_FLOW_CENSUS_PASS":
    raise SystemExit("FLOW_CENSUS_NOT_PASS")
if rec.get("supply_reconciliation",{}).get("exact_equal") is not True:
    raise SystemExit("SUPPLY_RECONCILIATION_NOT_EXACT")

rows=daily_obj.get("days",[])
by_day={r["utc_day"]:r for r in rows}

cal_days=[r for r in rows if "2024-10-01" <= r["utc_day"] <= "2025-06-30"]
if not cal_days:
    raise SystemExit("CALIBRATION_EMPTY")

vals=[]
for r in cal_days:
    obj=r.get("net_flow_rate_exact")
    if not obj:
        raise SystemExit("INVALID_CALIBRATION_RATE:"+r["utc_day"])
    den=int(obj["denominator"])
    if den<=0:
        raise SystemExit("NONPOSITIVE_CALIBRATION_DEN:"+r["utc_day"])
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
      "source_day":row["utc_day"]
    }

q10=nearest_rank(0.10)
q90=nearest_rank(0.90)
fq10=Fraction(int(q10["numerator"]),int(q10["denominator"]))
fq90=Fraction(int(q90["numerator"]),int(q90["denominator"]))
if fq10>=fq90:
    raise SystemExit("Q10_NOT_LESS_THAN_Q90")

neg=neu=pos=0
for frac,_ in vals:
    if frac<=fq10: neg+=1
    elif frac>=fq90: pos+=1
    else: neu+=1

out={
  "lab_id":"CBBTC-ETH-MINT-BURN-FLOW-001",
  "stage":"FLOW_STATE_CALIBRATION_V0.1",
  "classification":"FLOW_STATE_CALIBRATION_PASS",
  "source_daily_series_sha256":rec.get("daily_series_sha256"),
  "calibration_period":{"start":"2024-10-01","end":"2025-06-30"},
  "calibration_day_count":len(vals),
  "quantile_rule":{"method":"nearest_rank","q10":q10,"q90":q90},
  "calibration_state_counts":{"NEGATIVE_EXTREME":neg,"NEUTRAL":neu,"POSITIVE_EXTREME":pos},
  "market_returns_opened":False,
  "direction_opened":False,
  "pnl_opened":False,
  "protected_2026_opened":False,
  "promotion_credit":0
}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))

#!/usr/bin/env python3
from __future__ import annotations
import json, random
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec=80
SRC=Path("artifacts/reth_mechanism_discovery/RETH_MECHANISM_DISCOVERY_SOURCE_V0.1.json")
OUT=Path("artifacts/reth_mechanism_discovery/RETH_MECHANISM_DISCOVERY_RESULT_V0.1.json")

x=json.loads(SRC.read_text())
if x.get("classification")!="MECHANISM_DISCOVERY_SOURCE_PASS":
    raise SystemExit("MECHANISM_SOURCE_NOT_PASS")

def rat(obj):
    return Decimal(obj["numerator"])/Decimal(obj["denominator"])

def mean(vals):
    return sum(vals,Decimal(0))/Decimal(len(vals))

rows=[]
for r in x.get("rows",[]):
    entry=rat(r["entry_dislocation_exact"])
    future=rat(r["primary"]["dislocation_exact"])
    if r["state"]=="DISCOUNT_EXTREME":
        closure=future-entry
    elif r["state"]=="PREMIUM_EXTREME":
        closure=entry-future
    else:
        raise SystemExit("NON_EXTREME_EVENT")
    frac=closure/abs(entry) if entry!=0 else None
    sec=None
    if r.get("secondary",{}).get("valid"):
        sf=rat(r["secondary"]["dislocation_exact"])
        sec=(sf-entry) if r["state"]=="DISCOUNT_EXTREME" else (entry-sf)
    rows.append({
      "event_index":r["event_index"],
      "entry_block_number":r["entry_block_number"],
      "state":r["state"],
      "signed_closure_7200":closure,
      "closure_fraction_7200":frac,
      "signed_closure_21600_diagnostic":sec
    })

n=len(rows)
dc=[r["signed_closure_7200"] for r in rows if r["state"]=="DISCOUNT_EXTREME"]
pc=[r["signed_closure_7200"] for r in rows if r["state"]=="PREMIUM_EXTREME"]
vals=[r["signed_closure_7200"] for r in rows]

if n<30 or len(dc)<10 or len(pc)<10:
    classification="MECHANISM_DISCOVERY_INSUFFICIENT_SAMPLE"
    boot_lo=None
    boot_hi=None
else:
    rng=random.Random(20260926)
    boots=[]
    for _ in range(10000):
        sample=[vals[rng.randrange(n)] for __ in range(n)]
        boots.append(mean(sample))
    boots.sort()
    lo_idx=max(0,int(0.025*len(boots))-1)
    hi_idx=min(len(boots)-1,int(0.975*len(boots))-1)
    boot_lo=boots[lo_idx]
    boot_hi=boots[hi_idx]
    pooled=mean(vals)
    dm=mean(dc)
    pm=mean(pc)
    passed=pooled>0 and boot_lo>0 and dm>0 and pm>0
    classification="MECHANISM_DISCOVERY_PASS" if passed else "MECHANISM_DISCOVERY_FAIL"

def s(v):
    return None if v is None else format(v,"f")

sec=[r["signed_closure_21600_diagnostic"] for r in rows if r["signed_closure_21600_diagnostic"] is not None]
result={
  "lab_id":"RETH-NAV-DISLOCATION-001",
  "stage":"MECHANISM_DISCOVERY_V0.1",
  "classification":classification,
  "primary_horizon_blocks":7200,
  "secondary_diagnostic_horizon_blocks":21600,
  "event_count":n,
  "discount_event_count":len(dc),
  "premium_event_count":len(pc),
  "pooled_mean_signed_closure_7200":s(mean(vals)) if vals else None,
  "discount_mean_signed_closure_7200":s(mean(dc)) if dc else None,
  "premium_mean_signed_closure_7200":s(mean(pc)) if pc else None,
  "bootstrap":{
    "seed":20260926,
    "resamples":10000,
    "percentile_95_lower":s(boot_lo),
    "percentile_95_upper":s(boot_hi)
  },
  "secondary_diagnostic":{
    "valid_count":len(sec),
    "mean_signed_closure_21600":s(mean(sec)) if sec else None,
    "can_rescue_primary":False
  },
  "market_returns_opened":False,
  "pnl_opened":False,
  "mutation":False,
  "promotion_credit":0,
  "rows":[
    {
      **{k:v for k,v in r.items() if k not in ("signed_closure_7200","closure_fraction_7200","signed_closure_21600_diagnostic")},
      "signed_closure_7200":s(r["signed_closure_7200"]),
      "closure_fraction_7200":s(r["closure_fraction_7200"]),
      "signed_closure_21600_diagnostic":s(r["signed_closure_21600_diagnostic"])
    } for r in rows
  ]
}
OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in result.items() if k!="rows"},indent=2,sort_keys=True))

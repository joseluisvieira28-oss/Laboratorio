#!/usr/bin/env python3
from __future__ import annotations
import json, random
from decimal import Decimal, getcontext
from pathlib import Path

getcontext().prec=80
SRC=Path("artifacts/dual_lst_rv_001/mechanism/DUAL_LST_MECHANISM_DISCOVERY_SOURCE_V0.1.json")
OUT=Path("artifacts/dual_lst_rv_001/mechanism/DUAL_LST_MECHANISM_DISCOVERY_RESULT_V0.1.json")

x=json.loads(SRC.read_text())
if x.get("classification")!="MECHANISM_DISCOVERY_SOURCE_PASS":
    raise SystemExit("MECHANISM_SOURCE_NOT_PASS")

def rat(obj):
    return Decimal(obj["numerator"])/Decimal(obj["denominator"])
def mean(xs):
    return sum(xs,Decimal(0))/Decimal(len(xs))

rows=[]
for r in x.get("rows",[]):
    entry=rat(r["entry_dislocation_exact"])
    future=rat(r["primary"]["dislocation_exact"])
    if r["state"]=="RETH_CHEAP_EXTREME":
        closure=future-entry
    elif r["state"]=="RETH_RICH_EXTREME":
        closure=entry-future
    else:
        raise SystemExit("NON_EXTREME_EVENT")
    frac=closure/abs(entry) if entry!=0 else None
    sec=None
    if r.get("secondary",{}).get("valid"):
        sf=rat(r["secondary"]["dislocation_exact"])
        sec=(sf-entry) if r["state"]=="RETH_CHEAP_EXTREME" else (entry-sf)
    rows.append({
      "event_index":r["event_index"],"entry_block_number":r["entry_block_number"],"state":r["state"],
      "signed_closure_7200":closure,"closure_fraction_7200":frac,
      "signed_closure_21600_diagnostic":sec
    })

vals=[r["signed_closure_7200"] for r in rows]
cheap=[r["signed_closure_7200"] for r in rows if r["state"]=="RETH_CHEAP_EXTREME"]
rich=[r["signed_closure_7200"] for r in rows if r["state"]=="RETH_RICH_EXTREME"]
n=len(vals)

if n<20 or len(cheap)<6 or len(rich)<6:
    cls="MECHANISM_DISCOVERY_INSUFFICIENT_SAMPLE";lo=hi=None
else:
    rng=random.Random(20260927)
    boots=[]
    for _ in range(10000):
        boots.append(mean([vals[rng.randrange(n)] for __ in range(n)]))
    boots.sort()
    lo=boots[max(0,int(.025*len(boots))-1)]
    hi=boots[min(len(boots)-1,int(.975*len(boots))-1)]
    passed=mean(vals)>0 and lo>0 and mean(cheap)>0 and mean(rich)>0
    cls="MECHANISM_DISCOVERY_PASS" if passed else "MECHANISM_DISCOVERY_FAIL"

sec=[r["signed_closure_21600_diagnostic"] for r in rows if r["signed_closure_21600_diagnostic"] is not None]
fmt=lambda v:None if v is None else format(v,"f")
out={
 "lab_id":"DUAL-LST-RV-001","stage":"MECHANISM_DISCOVERY_V0.1","classification":cls,
 "primary_horizon_blocks":7200,"secondary_diagnostic_horizon_blocks":21600,
 "event_count":n,"cheap_event_count":len(cheap),"rich_event_count":len(rich),
 "pooled_mean_signed_closure_7200":fmt(mean(vals)) if vals else None,
 "cheap_mean_signed_closure_7200":fmt(mean(cheap)) if cheap else None,
 "rich_mean_signed_closure_7200":fmt(mean(rich)) if rich else None,
 "bootstrap":{"seed":20260927,"resamples":10000,"percentile_95_lower":fmt(lo),"percentile_95_upper":fmt(hi)},
 "secondary_diagnostic":{"valid_count":len(sec),"mean_signed_closure_21600":fmt(mean(sec)) if sec else None,"can_rescue_primary":False},
 "future_returns_opened":True,"market_returns_opened":False,"pnl_opened":False,"mutation":False,"promotion_credit":0
}
OUT.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps(out,indent=2,sort_keys=True))

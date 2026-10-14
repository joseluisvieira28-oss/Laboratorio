from __future__ import annotations

import argparse
import json
import math
import pathlib
from collections import defaultdict
from datetime import datetime, timezone

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(parents=True,exist_ok=True)

def nearest_rank(vals,q):
    vals=sorted(vals)
    if not vals:
        return None
    idx=max(0,min(len(vals)-1,math.ceil(q*len(vals))-1))
    return vals[idx]

ap=argparse.ArgumentParser()
ap.add_argument("--input",default=str(OUT/"forward_raw_v0_1.jsonl"))
ap.add_argument("--engineering-smoke",action="store_true")
args=ap.parse_args()

path=pathlib.Path(args.input)
records=[]
with path.open("r",encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        env=json.loads(line)
        msg=env.get("message") or {}
        topic=msg.get("topic","")
        if not topic.startswith("allLiquidation."):
            continue
        data=msg.get("data") or []
        if not isinstance(data,list):
            data=[data]
        for x in data:
            try:
                T=int(x["T"])
                sym=str(x["s"])
                side=str(x["S"])
                v=float(x["v"])
                p=float(x["p"])
            except Exception:
                continue
            records.append({"T":T,"symbol":sym,"side":side,"notional":v*p})

bins=defaultdict(lambda:{"long":0.0,"short":0.0})
for x in records:
    bucket=(x["T"]//5000)*5000
    k=(x["symbol"],bucket)
    if x["side"]=="Buy":
        bins[k]["long"]+=x["notional"]
    elif x["side"]=="Sell":
        bins[k]["short"]+=x["notional"]

per_symbol=defaultdict(list)
for (sym,bucket),x in bins.items():
    total=x["long"]+x["short"]
    if total>0:
        per_symbol[sym].append(total)

first=min((x["T"] for x in records),default=None)
last=max((x["T"] for x in records),default=None)
span_hours=((last-first)/3_600_000) if first is not None and last is not None else 0.0
ready=(span_hours>=24.0 and len(records)>=500)
canonical=ready and not args.engineering_smoke

thresholds={}
for sym,vals in sorted(per_symbol.items()):
    thresholds[sym]={
        "nonempty_5s_windows":len(vals),
        "eligible":len(vals)>=30,
        "q95_nearest_rank_usdt":nearest_rank(vals,0.95) if len(vals)>=30 else None,
        "q90_descriptive_usdt":nearest_rank(vals,0.90) if vals else None,
        "q99_descriptive_usdt":nearest_rank(vals,0.99) if vals else None,
    }

receipt={
    "lab_id":"LIQUIDATION-PRESSURE-002-FORWARD",
    "phase":"SOURCE_ONLY_Q95_CALIBRATION_V0.1",
    "mve_id":"LP2-BYBIT-REV5S-Q95-H30-V1",
    "raw_liquidation_records":len(records),
    "nonempty_5s_windows":len(bins),
    "observed_span_hours":span_hours,
    "minimum_hours_required":24,
    "minimum_records_required":500,
    "ready_for_canonical_freeze":ready,
    "canonical_thresholds_emitted":canonical,
    "quantile_rule":"nearest-rank q95, ceil(q*N)-1 zero-based",
    "thresholds":thresholds,
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "verdict":(
        "SOURCE_CALIBRATION_PASS_READY_TO_FREEZE"
        if canonical else
        "ENGINEERING_SMOKE_ONLY"
        if args.engineering_smoke else
        "CALIBRATION_NOT_READY"
    ),
    "generated_at_utc":datetime.now(timezone.utc).isoformat(),
}
name="source_calibration_canonical_v0_1.json" if canonical else "source_calibration_preview_v0_1.json"
(OUT/name).write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))

if not args.engineering_smoke and not ready:
    raise SystemExit(3)

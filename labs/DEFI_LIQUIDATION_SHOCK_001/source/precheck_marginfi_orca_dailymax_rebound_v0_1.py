#!/usr/bin/env python3
import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--calibration-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_DAILYMAX_REBOUND_PREOUTCOME_RECEIPT_V0.1.json"
ROWS=OUT/"MARGINFI_ORCA_DAILYMAX_REBOUND_SELECTED_V0.1.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

cr=find_one(args.calibration_root,"MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_RECEIPT_V0.1.json")
cc=find_one(args.calibration_root,"MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_CASCADES_V0.1.ndjson")
errors=[]
if cr is None or cc is None:
    errors.append("calibration_artifact_missing_or_duplicate")
rows=[]
if not errors:
    r=json.loads(cr.read_text())
    if r.get("classification")!="MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_PASS":
        errors.append("calibration_not_pass")
    rows=[json.loads(x) for x in cc.read_text().splitlines() if x.strip()]

by={}
for r in rows:
    d=r["decision_time"][:10]
    cur=by.get(d)
    key=(-float(r["flow_turnover_intensity"]),r["decision_time"],r["cascade_id"])
    if cur is None:
        by[d]=(key,r)
    else:
        if key<cur[0]:by[d]=(key,r)
selected=[v[1] for k,v in sorted(by.items())]
selected.sort(key=lambda r:r["decision_time"])
f1=[r for r in selected if r["decision_time"]<"2024-09-01T00:00:00+00:00"]
f2=[r for r in selected if r["decision_time"]>="2024-09-01T00:00:00+00:00"]
gate={"selected_days_ge_25":len(selected)>=25,"f1_ge_15":len(f1)>=15,"f2_ge_8":len(f2)>=8}
classification=("MARGINFI_ORCA_DAILYMAX_REBOUND_PREOUTCOME_READY"
                if not errors and all(gate.values())
                else "MARGINFI_ORCA_DAILYMAX_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE")
with ROWS.open("w") as fh:
    for r in selected:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
receipt={
 "schema_version":"0.1","classification":classification,
 "authority":"MARGINFI_ORCA_DAILYMAX_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "calibration_cascade_count":len(rows),"selected_day_count":len(selected),
 "f1_selected_count":len(f1),"f2_selected_count":len(f2),"gate":gate,
 "error_count":len(errors),"errors":errors,"selected_file":str(ROWS),
 "firewall":{"feature_only":True,"ohlc_read":False,"returns_read":False,"pnl_read":False,
             "jul_sep_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))

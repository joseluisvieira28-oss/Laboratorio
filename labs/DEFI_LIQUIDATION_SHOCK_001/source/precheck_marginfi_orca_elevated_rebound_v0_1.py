#!/usr/bin/env python3
import argparse,json
from pathlib import Path

Q75=1.205342817822632e-05

ap=argparse.ArgumentParser()
ap.add_argument("--calibration-root",required=True)
ap.add_argument("--q75-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_ELEVATED_REBOUND_PREOUTCOME_RECEIPT_V0.1.json"
ROWS=OUT/"MARGINFI_ORCA_ELEVATED_REBOUND_PREOUTCOME_SELECTED_V0.1.ndjson"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

cr=find_one(args.calibration_root,"MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_RECEIPT_V0.1.json")
cc=find_one(args.calibration_root,"MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_CASCADES_V0.1.ndjson")
qr=find_one(args.q75_root,"MARGINFI_ORCA_ELEVATED_FLOW_Q75_CALIBRATION_RECEIPT_V0.1.json")
errors=[]
if cr is None or cc is None or qr is None:
    errors.append("calibration_or_q75_artifact_missing_or_duplicate")
rows=[]
if not errors:
    c=json.loads(cr.read_text());q=json.loads(qr.read_text())
    if c.get("classification")!="MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_PASS":
        errors.append("parent_calibration_not_pass")
    if q.get("classification")!="MARGINFI_ORCA_ELEVATED_FLOW_Q75_CALIBRATION_PASS":
        errors.append("q75_calibration_not_pass")
    if abs(float(q.get("q75_flow_turnover_intensity",-1))-Q75)>1e-18:
        errors.append("q75_mismatch")
    rows=[json.loads(x) for x in cc.read_text().splitlines() if x.strip()]

selected=[r for r in rows if float(r.get("flow_turnover_intensity",-1))>=Q75]
selected.sort(key=lambda r:r["decision_time"])
f1=[r for r in selected if r["decision_time"]<"2024-09-01T00:00:00+00:00"]
f2=[r for r in selected if r["decision_time"]>="2024-09-01T00:00:00+00:00"]
days=len({r["decision_time"][:10] for r in selected})
gate={
 "selected_ge_35":len(selected)>=35,
 "distinct_days_ge_10":days>=10,
 "f1_ge_20":len(f1)>=20,
 "f2_ge_8":len(f2)>=8
}
classification=("MARGINFI_ORCA_ELEVATED_REBOUND_PREOUTCOME_READY"
                if not errors and all(gate.values())
                else "MARGINFI_ORCA_ELEVATED_REBOUND_PREOUTCOME_INSUFFICIENT_SAMPLE")

with ROWS.open("w") as fh:
    for r in selected:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

receipt={
 "schema_version":"0.1","classification":classification,
 "authority":"MARGINFI_ORCA_ELEVATED_FLOW_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "threshold_q75":Q75,
 "calibration_cascade_count":len(rows),
 "selected_count":len(selected),
 "distinct_selected_days":days,
 "f1_selected_count":len(f1),
 "f2_selected_count":len(f2),
 "gate":gate,
 "error_count":len(errors),"errors":errors,
 "selected_file":str(ROWS),
 "firewall":{"feature_only":True,"ohlc_read":False,"returns_read":False,"pnl_read":False,
             "jul_sep_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))

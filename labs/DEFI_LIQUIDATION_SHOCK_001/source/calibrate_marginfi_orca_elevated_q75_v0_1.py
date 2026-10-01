#!/usr/bin/env python3
import argparse,json,math
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--calibration-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_ELEVATED_FLOW_Q75_CALIBRATION_RECEIPT_V0.1.json"

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

cr=find_one(args.calibration_root,"MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_RECEIPT_V0.1.json")
cc=find_one(args.calibration_root,"MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_CASCADES_V0.1.ndjson")
errors=[]
if cr is None or cc is None: errors.append("calibration_artifact_missing_or_duplicate")
rows=[]
if not errors:
    r=json.loads(cr.read_text())
    if r.get("classification")!="MARGINFI_ORCA_FLOW_TURNOVER_CALIBRATION_PASS":
        errors.append("parent_calibration_not_pass")
    rows=[json.loads(x) for x in cc.read_text().splitlines() if x.strip()]

vals=sorted(float(r["flow_turnover_intensity"]) for r in rows)
N=len(vals);rank=math.ceil(0.75*N) if N else 0;q75=vals[rank-1] if rank else None
classification="MARGINFI_ORCA_ELEVATED_FLOW_Q75_CALIBRATION_PASS" if not errors and N==192 and q75 and q75>0 else "MARGINFI_ORCA_ELEVATED_FLOW_Q75_CALIBRATION_BLOCKED"
receipt={
 "schema_version":"0.1","classification":classification,
 "authority":"MARGINFI_ORCA_ELEVATED_FLOW_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "parent_calibration_run":36816611039,"parent_artifact_id":11141731925,
 "N":N,"quantile_method":"nearest_rank","quantile_p":0.75,"nearest_rank":rank,
 "q75_flow_turnover_intensity":q75,
 "min_intensity":vals[0] if vals else None,"max_intensity":vals[-1] if vals else None,
 "error_count":len(errors),"errors":errors,
 "firewall":{"feature_only":True,"ohlc_read":False,"returns_read":False,"pnl_read":False,
             "jul_sep_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="MARGINFI_ORCA_ELEVATED_FLOW_Q75_CALIBRATION_PASS": raise SystemExit(2)

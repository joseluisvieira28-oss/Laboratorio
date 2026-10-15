#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE=Path("research/cbeth_redemption_basis_001")
ART=Path("artifacts")
MAN_DIR=ART/"cbeth_continuation"
MAN_DIR.mkdir(parents=True,exist_ok=True)
MAN=MAN_DIR/"CBETH_CONTINUATION_MANIFEST_V0.1.json"

manifest={
  "lab_id":"CBETH-REDEMPTION-BASIS-001",
  "stage":"CONTINUATION_V0.1",
  "started_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "classification":"RUNNING",
  "completed_stages":[],
  "future_mechanism_outcomes_opened":False,
  "market_returns_opened":False,
  "oos_2025_opened":False,
  "protected_2026_opened":False,
  "pnl_opened":False,
  "mutation":False,
  "promotion_credit":0
}

def write():
    manifest["updated_at_utc"]=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    MAN.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")

def run(cmd):
    print("+"," ".join(cmd),flush=True)
    return subprocess.run(cmd,check=False).returncode

def load(p):
    return json.loads(Path(p).read_text())

def copy_if(src,dst):
    src=Path(src); dst=Path(dst)
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(src,dst)
    return True

def stop(cls,code=0,blocker=None):
    manifest["classification"]=cls
    if blocker is not None:
        manifest["blocker"]=blocker
    write()
    raise SystemExit(code)

write()

# Gate 1: source only.
rc=run(["node",str(HERE/"cbeth_source_probe_v01.mjs")])
source_art=ART/"CBETH_REDEMPTION_BASIS_SOURCE_GATE_RECEIPT_V0.1.json"
source_dst=HERE/"SOURCE_GATE_RECEIPT_V0.1.json"
if not copy_if(source_art,source_dst):
    stop("TECHNICAL_SOURCE_GATE_BLOCKED",2,"source_receipt_missing")
source=load(source_dst)
manifest["source_classification"]=source.get("classification")
manifest["source_gates"]=source.get("gates")
if source.get("classification")=="SOURCE_BLOCKED":
    stop("SOURCE_BLOCKED",0)
if rc!=0 or source.get("classification")!="SOURCE_PASS":
    stop("TECHNICAL_SOURCE_GATE_BLOCKED",2,"unexpected_source_state")
manifest["completed_stages"].append("SOURCE_PASS")
write()

# Gate 1.5: prove direct-vs-Multicall scientific bytes are identical.
rc=run(["node",str(HERE/"cbeth_multicall_equivalence_v01c.mjs")])
eq_art=ART/"cbeth_transport"/"CBETH_MULTICALL_TRANSPORT_EQUIVALENCE_RECEIPT_V0.1C.json"
eq_dst=HERE/"MULTICALL_TRANSPORT_EQUIVALENCE_RECEIPT_V0.1C.json"
if not copy_if(eq_art,eq_dst):
    stop("TECHNICAL_MULTICALL_EQUIVALENCE_BLOCKED",2,"equivalence_receipt_missing")
eq=load(eq_dst)
manifest["multicall_equivalence_classification"]=eq.get("classification")
if rc!=0 or eq.get("classification")!="MULTICALL_TRANSPORT_EQUIVALENCE_PASS":
    stop("MULTICALL_TRANSPORT_EQUIVALENCE_BLOCKED",2)
manifest["completed_stages"].append("MULTICALL_TRANSPORT_EQUIVALENCE_PASS")
write()

# Gate 2: complete 2023-2024 predictor-only census.
rc=run(["node",str(HERE/"cbeth_predictor_census_v01.mjs")])
census_art=ART/"cbeth_census"/"CBETH_PREDICTOR_CENSUS_RECEIPT_V0.1.json"
rows_art=ART/"cbeth_census"/"CBETH_PREDICTOR_CENSUS_ROWS_V0.1.json"
census_dst=HERE/"PREDICTOR_CENSUS_RECEIPT_V0.1.json"
rows_dst=HERE/"PREDICTOR_CENSUS_ROWS_V0.1.json"
copy_if(census_art,census_dst); copy_if(rows_art,rows_dst)
if not census_dst.exists() or not rows_dst.exists():
    stop("TECHNICAL_PREDICTOR_CENSUS_BLOCKED",2,"census_evidence_missing")
census=load(census_dst)
manifest["census_classification"]=census.get("classification")
manifest["census_valid_day_count"]=census.get("valid_day_count")
manifest["census_invalid_day_count"]=census.get("invalid_day_count")
manifest["selected_pool"]=census.get("selected_pool")
if census.get("classification")=="PREDICTOR_CENSUS_BLOCKED":
    stop("PREDICTOR_CENSUS_BLOCKED",0)
if rc!=0 or census.get("classification")!="PREDICTOR_CENSUS_PASS":
    stop("TECHNICAL_PREDICTOR_CENSUS_BLOCKED",2,"unexpected_census_state")
manifest["completed_stages"].append("PREDICTOR_CENSUS_PASS")
write()

# Gate 3: exact pre-frozen q10/q90.
rc=run([sys.executable,str(HERE/"cbeth_state_calibration_v01.py")])
cal_path=HERE/"STATE_CALIBRATION_RECEIPT_V0.1.json"
if rc!=0 or not cal_path.exists():
    stop("STATE_CALIBRATION_BLOCKED",2)
cal=load(cal_path)
if cal.get("classification")!="STATE_CALIBRATION_PASS":
    stop("STATE_CALIBRATION_BLOCKED",2)
manifest["state_calibration_classification"]=cal.get("classification")
manifest["q10"]=cal.get("quantile_rule",{}).get("q10")
manifest["q90"]=cal.get("quantile_rule",{}).get("q90")
manifest["completed_stages"].append("STATE_CALIBRATION_PASS")
write()

# Gate 4: outcome-blind 2024H2 predictor sample.
rc=run([sys.executable,str(HERE/"cbeth_discovery_predictor_sample_v01.py")])
sample_path=HERE/"DISCOVERY_PREDICTOR_SAMPLE_RECEIPT_V0.1.json"
if not sample_path.exists():
    stop("TECHNICAL_PREDICTOR_SAMPLE_BLOCKED",2,"sample_receipt_missing")
sample=load(sample_path)
manifest["predictor_sample_classification"]=sample.get("classification")
manifest["transition_event_count"]=sample.get("transition_event_count")
manifest["discount_extreme_event_count"]=sample.get("discount_extreme_event_count")
manifest["premium_extreme_event_count"]=sample.get("premium_extreme_event_count")
if rc!=0 or sample.get("classification")=="PREDICTOR_SOURCE_BLOCKED":
    stop("PREDICTOR_SOURCE_BLOCKED",0)
if sample.get("classification")=="PREDICTOR_INSUFFICIENT_SAMPLE":
    stop("PREDICTOR_INSUFFICIENT_SAMPLE",0)
if sample.get("classification")!="PREDICTOR_SAMPLE_PASS":
    stop("TECHNICAL_PREDICTOR_SAMPLE_BLOCKED",2,"unexpected_sample_state")
manifest["completed_stages"].append("PREDICTOR_SAMPLE_PASS")
write()

# Gate 5: the mechanism program itself enforces the post-censor 20/6/6
# firewall BEFORE it reads future basis rows.
rc=run([sys.executable,str(HERE/"cbeth_mechanism_discovery_v01.py")])
mech_path=HERE/"MECHANISM_DISCOVERY_RESULT_V0.1.json"
if rc!=0 or not mech_path.exists():
    stop("TECHNICAL_MECHANISM_DISCOVERY_BLOCKED",2)
mech=load(mech_path)
cls=mech.get("classification")
manifest["mechanism_classification"]=cls
manifest["mechanism_eligible_event_count"]=mech.get("mechanism_eligible_event_count")
manifest["eligible_discount_event_count"]=mech.get("eligible_discount_event_count")
manifest["eligible_premium_event_count"]=mech.get("eligible_premium_event_count")
manifest["future_mechanism_outcomes_opened"]=bool(mech.get("future_mechanism_outcomes_opened",False))
manifest["completed_stages"].append(cls)

if cls=="MECHANISM_OUTCOME_INSUFFICIENT_SAMPLE":
    stop(cls,0)
if cls=="MECHANISM_DISCOVERY_FAIL":
    stop(cls,0)
if cls=="MECHANISM_DISCOVERY_PASS":
    stop("MECHANISM_DISCOVERY_PASS_PENDING_SEPARATE_OOS_AUTHORITY",0)
stop("TECHNICAL_MECHANISM_DISCOVERY_BLOCKED",2,"unexpected_mechanism_state")

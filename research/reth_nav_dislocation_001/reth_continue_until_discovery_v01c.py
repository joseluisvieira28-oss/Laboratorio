#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE=Path("research/reth_nav_dislocation_001")
ART=Path("artifacts")
MAN_DIR=ART/"continuation"
MAN_DIR.mkdir(parents=True,exist_ok=True)
MAN=MAN_DIR/"RETH_CONTINUATION_MANIFEST_V0.1C.json"

manifest={
  "lab_id":"RETH-NAV-DISLOCATION-001",
  "stage":"CONTINUATION_ORCHESTRATOR_V0.1C",
  "started_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
  "scientific_code_sha":os.environ.get("GITHUB_SHA"),
  "classification":"RUNNING",
  "completed_stages":[],
  "future_dislocation_outcomes_opened":False,
  "market_returns_opened":False,
  "pnl_opened":False,
  "oos_opened":False,
  "protected_holdout_opened":False,
  "mutation":False,
  "promotion_credit":0,
}

def write_manifest():
    manifest["updated_at_utc"]=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
    MAN.write_text(json.dumps(manifest,indent=2,sort_keys=True)+"\n")

def run(cmd):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd,check=False).returncode

def load(path):
    return json.loads(Path(path).read_text())

def cp(src,dst):
    src=Path(src); dst=Path(dst)
    if src.exists():
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(src,dst)
        return True
    return False

def stop(classification, exit_code, blocker=None):
    manifest["classification"]=classification
    if blocker:
        manifest["blocker"]=blocker
    write_manifest()
    raise SystemExit(exit_code)

write_manifest()

# GATE 1: split transport + blockHash equivalence.
rc=run(["node",str(HERE/"reth_split_transport_equivalence_v01c.mjs")])
eq_art=ART/"RETH_SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_RECEIPT_V0.1C.json"
eq_dst=HERE/"RETH_SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_RECEIPT_V0.1C.json"
if not cp(eq_art,eq_dst):
    stop("SPLIT_TRANSPORT_EQUIVALENCE_BLOCKED",2,"equivalence_receipt_missing")
eq=load(eq_dst)
manifest["equivalence_classification"]=eq.get("classification")
if rc!=0 or eq.get("classification")!="SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS":
    stop("SPLIT_TRANSPORT_EQUIVALENCE_BLOCKED",2)
manifest["completed_stages"].append("SPLIT_TRANSPORT_BLOCKHASH_EQUIVALENCE_PASS")
write_manifest()

# GATE 2: exact 556-point predictor-only census.
rc=run(["node",str(HERE/"reth_predictor_census_full_v01c.mjs")])
census_art=ART/"out"/"RETH_PREDICTOR_ONLY_CENSUS_RECEIPT_V0.1.json"
rows_art=ART/"out"/"RETH_PREDICTOR_ONLY_CENSUS_ROWS_V0.1.json"
census_dst=HERE/"RETH_PREDICTOR_ONLY_CENSUS_RECEIPT_V0.1.json"
rows_dst=HERE/"RETH_PREDICTOR_ONLY_CENSUS_ROWS_V0.1.json"
cp(census_art,census_dst); cp(rows_art,rows_dst)
if not census_dst.exists() or not rows_dst.exists():
    stop("PREDICTOR_SOURCE_CENSUS_BLOCKED",2,"census_evidence_missing")
census=load(census_dst)
manifest["census_classification"]=census.get("classification")
manifest["census_valid_count"]=census.get("valid_count")
manifest["census_invalid_count"]=census.get("invalid_count")
if rc!=0 or census.get("classification")!="PREDICTOR_SOURCE_CENSUS_PASS":
    stop("PREDICTOR_SOURCE_CENSUS_BLOCKED",2)
manifest["completed_stages"].append("PREDICTOR_SOURCE_CENSUS_PASS")
write_manifest()

# GATE 3: pre-frozen q05/q95 calibration.
rc=run([sys.executable,str(HERE/"reth_state_calibration_v01.py")])
cal_path=HERE/"RETH_STATE_CALIBRATION_RECEIPT_V0.1.json"
if rc!=0 or not cal_path.exists():
    stop("PREDICTOR_STATE_CALIBRATION_BLOCKED",2)
cal=load(cal_path)
manifest["state_calibration_classification"]=cal.get("classification")
if cal.get("classification")!="PREDICTOR_STATE_CALIBRATION_PASS":
    stop("PREDICTOR_STATE_CALIBRATION_BLOCKED",2)
manifest["q05"]=cal.get("quantile_rule",{}).get("q05")
manifest["q95"]=cal.get("quantile_rule",{}).get("q95")
manifest["completed_stages"].append("PREDICTOR_STATE_CALIBRATION_PASS")
write_manifest()

# GATE 4: outcome-blind Discovery predictor sample.
rc=run(["node",str(HERE/"reth_discovery_predictor_sample_gate_v01c.mjs")])
disc_dir=ART/"reth_discovery_predictor"
disc_receipt_art=disc_dir/"RETH_DISCOVERY_PREDICTOR_SAMPLE_GATE_RECEIPT_V0.1.json"
disc_rows_art=disc_dir/"RETH_DISCOVERY_PREDICTOR_ROWS_V0.1.json"
disc_receipt_dst=HERE/"RETH_DISCOVERY_PREDICTOR_SAMPLE_GATE_RECEIPT_V0.1.json"
disc_rows_dst=HERE/"RETH_DISCOVERY_PREDICTOR_ROWS_V0.1.json"
cp(disc_receipt_art,disc_receipt_dst); cp(disc_rows_art,disc_rows_dst)
if not disc_receipt_dst.exists():
    stop("DISCOVERY_PREDICTOR_SOURCE_BLOCKED",2,"discovery_predictor_receipt_missing")
disc=load(disc_receipt_dst)
manifest["discovery_predictor_classification"]=disc.get("classification")
manifest["transition_event_count"]=disc.get("transition_event_count")
manifest["discount_extreme_event_count"]=disc.get("discount_extreme_event_count")
manifest["premium_extreme_event_count"]=disc.get("premium_extreme_event_count")
if rc!=0 or disc.get("classification")=="DISCOVERY_PREDICTOR_SOURCE_BLOCKED":
    stop("DISCOVERY_PREDICTOR_SOURCE_BLOCKED",2)
manifest["completed_stages"].append(disc.get("classification"))
write_manifest()
if disc.get("classification")=="DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE":
    stop("DISCOVERY_PREDICTOR_INSUFFICIENT_SAMPLE",0)
if disc.get("classification")!="DISCOVERY_PREDICTOR_SAMPLE_PASS":
    stop("DISCOVERY_PREDICTOR_GATE_UNKNOWN",2)

# GATE 5: mechanism Discovery opens only the already-frozen future dislocation state.
manifest["future_dislocation_outcomes_opened"]=True
write_manifest()
rc=run(["node",str(HERE/"reth_mechanism_discovery_source_v01c.mjs")])
mech_dir=ART/"reth_mechanism_discovery"
mech_src_art=mech_dir/"RETH_MECHANISM_DISCOVERY_SOURCE_V0.1.json"
mech_src_dst=HERE/"RETH_MECHANISM_DISCOVERY_SOURCE_V0.1.json"
cp(mech_src_art,mech_src_dst)
if rc!=0 or not mech_src_dst.exists():
    stop("MECHANISM_DISCOVERY_SOURCE_BLOCKED",2)
mech_src=load(mech_src_dst)
manifest["mechanism_source_classification"]=mech_src.get("classification")
if mech_src.get("classification")!="MECHANISM_DISCOVERY_SOURCE_PASS":
    stop("MECHANISM_DISCOVERY_SOURCE_BLOCKED",2)
manifest["completed_stages"].append("MECHANISM_DISCOVERY_SOURCE_PASS")
write_manifest()

rc=run([sys.executable,str(HERE/"reth_mechanism_discovery_analyze_v01.py")])
mech_res_art=mech_dir/"RETH_MECHANISM_DISCOVERY_RESULT_V0.1.json"
mech_res_dst=HERE/"RETH_MECHANISM_DISCOVERY_RESULT_V0.1.json"
cp(mech_res_art,mech_res_dst)
if rc!=0 or not mech_res_dst.exists():
    stop("MECHANISM_DISCOVERY_ANALYSIS_BLOCKED",2)
res=load(mech_res_dst)
manifest["mechanism_discovery_classification"]=res.get("classification")
manifest["completed_stages"].append(res.get("classification"))
stop(res.get("classification","MECHANISM_DISCOVERY_UNKNOWN"),0)

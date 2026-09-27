#!/usr/bin/env python3
import argparse, hashlib, json, os, subprocess
from pathlib import Path

BASE=Path("labs/DEFI_LIQUIDATION_SHOCK_001")
OUT=BASE/"FINAL_PRE_DISCOVERY_AUTHORITY_RECEIPT_V0.1.json"

REQUIRED_DOCS=[
 "PRE_DISCOVERY_TEMPORAL_HOLDOUT_FREEZE_V0.1.md",
 "CASCADE_CLUSTERING_FREEZE_V0.1.md",
 "SOURCE_SAMPLE_GATE_FREEZE_V0.1.md",
 "OUTCOME_STATISTICAL_AUTHORITY_FREEZE_V0.1.md",
 "MARKET_DATA_SOURCE_GATE_FREEZE_V0.1.md",
 "MARKET_DATA_MAPPING_REGISTRY_FREEZE_V0.1.md",
 "MARKET_DATA_MAPPING_SAMPLE_ADEQUACY_ADDENDUM_V0.2.md",
 "MARKET_DATA_ROUTE_METADATA_PROBE_FREEZE_V0.1.md",
 "MARKET_MAPPING_REQUIREMENTS_FREEZE_V0.1.md",
 "MARKET_MAPPING_REQUIREMENTS_ARTIFACT_SELECTION_FREEZE_V0.1.md",
 "GLOBAL_FIELD_COVERAGE_FINAL_GATE_FREEZE_V0.1.md",
 "GLOBAL_FIELD_COVERAGE_FINAL_GATE_VERSION_PRECEDENCE_ADDENDUM_V0.2.md",
 "FINAL_PRE_DISCOVERY_DESIGN_SCAFFOLD_V0.1.md",
 "FINAL_PRE_DISCOVERY_AUTHORITY_EXECUTION_FREEZE_V0.1.md",
 "KAMINO_HISTORICAL_ACCOUNT_LAYOUT_ADDENDUM_V0.2.md",
 "KAMINO_LAYOUT_RECOVERY_PRECEDENCE_ADDENDUM_V0.2.md",
 "KAMINO_UNIT_METADATA_TRANSFER_IDENTITY_ADDENDUM_V0.2.md",
 "KAMINO_UNIT_METADATA_RECOVERY_PRECEDENCE_ADDENDUM_V0.3.md",
 "KAMINO_TEMPORAL_DECODER_AND_UNIT_AUTHORITY_ADDENDUM_V0.3.md",
 "DRIFT_MARKET_UNIT_REGISTRY_TEMPORAL_ADDENDUM_V0.3.md",
 "GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_ADDENDUM_V0.3.md",
 "SOURCE_SAMPLE_GATE_KAMINO_UNIT_PRECEDENCE_ADDENDUM_V0.2.md",
 "GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_ADDENDUM_V0.2.md",
 "SAVE0C_HISTORICAL_RESERVE_REGISTRY_RETIREMENT_ADDENDUM_V0.2.md",
 "SAVE0C_UNIT_METADATA_SOURCE_COMPLETION_FREEZE_V0.2.md",
 "MARGINFI_BANK_UNIT_SOURCE_COMPLETION_FREEZE_V0.2.md",
 "SAVE0C_UNIT_METADATA_SOURCE_COMPLETION_CORRECTION_V0.3.1.md",
 "MARKET_DATA_SOURCE_FEASIBILITY_ADDENDUM_V0.2.md",
 "FINAL_PRE_DISCOVERY_AUTHORITY_DOCUMENT_SET_ADDENDUM_V0.2.md",
 "FINAL_PRE_DISCOVERY_AUTHORITY_DOCUMENT_SET_ADDENDUM_V0.3.md",
 "GLOBAL_FIELD_COVERAGE_FINAL_GATE_VERSION_PRECEDENCE_ADDENDUM_V0.4.md",
 "GLOBAL_FIELD_FINALIZER_ARTIFACT_SELECTION_ADDENDUM_V0.4.md",
 "SOURCE_SAMPLE_GATE_SAVE11_UNIT_PRECEDENCE_ADDENDUM_V0.3.md",
 "FINAL_PRE_DISCOVERY_PREREQUISITE_ARTIFACT_SELECTION_FREEZE_V0.1.md",
]

def find_json(root,name):
    hits=sorted(Path(root).rglob(name))
    if not hits:return None,None
    return json.loads(hits[0].read_text()),str(hits[0])

def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as fh:
        for b in iter(lambda:fh.read(1024*1024),b""):h.update(b)
    return h.hexdigest()

def git(cmd):
    try:
        return subprocess.check_output(["git",*cmd],text=True).strip()
    except Exception:
        return None

ap=argparse.ArgumentParser()
ap.add_argument("--global-field",required=True)
ap.add_argument("--sample-gate",required=True)
ap.add_argument("--market-data",required=True)
args=ap.parse_args()

errors=[];checks={}

gf,gfp=find_json(args.global_field,"GLOBAL_FIELD_COVERAGE_FINAL_RECEIPT_V0.1.json")
sg,sgp=find_json(args.sample_gate,"SOURCE_CLUSTER_SAMPLE_GATE_RECEIPT_V0.1.json")
md,mdp=find_json(args.market_data,"MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json")

required=[
 ("global_field",gf,"GLOBAL_FIELD_COVERAGE_FINAL_PASS",gfp),
 ("sample_gate",sg,"SOURCE_SAMPLE_GATE_PASS",sgp),
 ("market_data",md,"MARKET_DATA_SOURCE_PASS",mdp),
]
for name,obj,expected,path in required:
    actual=(obj or {}).get("classification")
    ok=actual==expected
    checks[name]={"path":path,"receipt_sha256":sha256(path) if path else None,
                  "classification":actual,"expected":expected,"pass":ok}
    if obj is None:
        errors.append({"reason":"missing_prerequisite_receipt","name":name})
    elif not ok:
        errors.append({"reason":"prerequisite_not_pass","name":name,"classification":actual,"expected":expected})

doc_hashes={}
for name in REQUIRED_DOCS:
    p=BASE/name
    if not p.exists():
        errors.append({"reason":"missing_frozen_document","document":name})
        continue
    doc_hashes[name]={"sha256":sha256(p),"bytes":p.stat().st_size}

blocked=any("BLOCKED_FAIL_CLOSED" in str((x[1] or {}).get("classification","")) for x in required)
if blocked:
    classification="FINAL_PRE_DISCOVERY_BLOCKED_FAIL_CLOSED"
elif errors:
    classification="FINAL_PRE_DISCOVERY_PENDING"
else:
    classification="FINAL_PRE_DISCOVERY_AUTHORITY_PASS"

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,
 "prerequisites":checks,
 "frozen_document_hashes":doc_hashes,
 "git":{"commit":git(["rev-parse","HEAD"]),"branch":git(["rev-parse","--abbrev-ref","HEAD"])},
 "authorized_if_pass":{
   "market_outcome_window":"source-mapped 2021-2024 only",
   "phase_order":["DISCOVERY","OOS_AFTER_DISCOVERY_ADJUDICATION"],
   "protected_2025_2026":True
 },
 "firewall_at_creation":{
   "prices_opened":False,"returns_opened":False,"pnl_opened":False,
   "economic_outcomes_opened":False,"protected_2025_2026_opened":False,
   "post_outcome_tuning":False,"live_trading":False,"orders":False,
   "wallets":False,"exchange_mutation":False,"merge_main":False
 },
 "error_count":len(errors),"errors":errors
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="FINAL_PRE_DISCOVERY_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if classification!="FINAL_PRE_DISCOVERY_AUTHORITY_PASS":raise SystemExit(3)

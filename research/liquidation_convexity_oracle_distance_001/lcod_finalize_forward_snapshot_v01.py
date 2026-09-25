#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, os
from pathlib import Path
from datetime import datetime, timezone

HERE=Path("research/liquidation_convexity_oracle_distance_001")
POP=HERE/"LCOD_BLOCK_PINNED_ACTIVE_POPULATION_RECEIPT.json"
COMP=HERE/"LCOD_FULL_SAME_BLOCK_COMPONENT_RECONSTRUCTION_RECEIPT.json"
CURVE=HERE/"LCOD_CANONICAL_COLLATERAL_STRESS_CURVE_RECEIPT.json"
OUT=Path("artifacts/lcod_forward_mechanical_snapshot_v01.json")

def load(p):
    return json.loads(p.read_text())

def sha_obj(x):
    raw=json.dumps(x,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(raw).hexdigest()

pop,comp,curve=map(load,(POP,COMP,CURVE))

if pop.get("classification")!="BLOCK_PINNED_ACTIVE_POPULATION_PASS":
    raise SystemExit("POPULATION_GATE_NOT_PASS")
if comp.get("classification")!="FULL_SAME_BLOCK_COMPONENT_PASS":
    raise SystemExit("COMPONENT_GATE_NOT_PASS")
if curve.get("classification")!="CANONICAL_MECHANICAL_CURVE_PASS":
    raise SystemExit("CURVE_GATE_NOT_PASS")

for k in ("ethereum_block_number","ethereum_block_hash"):
    if str(pop.get(k)).lower()!=str(comp.get(k)).lower() or str(pop.get(k)).lower()!=str(curve.get(k)).lower():
        raise SystemExit("PROVENANCE_"+k.upper()+"_MISMATCH")

active_sha=pop.get("canonical_active_pair_set_sha256")
if active_sha!=comp.get("canonical_active_pair_set_sha256") or active_sha!=curve.get("canonical_active_pair_set_sha256"):
    raise SystemExit("ACTIVE_SET_SHA_MISMATCH")
if not comp.get("active_set_match"):
    raise SystemExit("ACTIVE_SET_REPRODUCTION_NOT_PASS")
if float(comp.get("count_coverage",0))<0.90 or float(comp.get("debt_coverage",0))<0.90:
    raise SystemExit("COMPONENT_COVERAGE_GATE_NOT_PASS")

rows=comp.get("rows",[])
if len(rows)!=int(comp.get("active_population_count",-1)):
    raise SystemExit("COMPONENT_ROW_COUNT_MISMATCH")

event=os.environ.get("GITHUB_EVENT_NAME","local")
role="FORWARD_OBSERVATION" if event in ("schedule","push") else "DIAGNOSTIC_ONLY"
captured=datetime.now(timezone.utc).isoformat().replace("+00:00","Z")

receipt={
  "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
  "stage":"PROSPECTIVE_MECHANICAL_STATE_OBSERVATION_V0.1",
  "classification":"FORWARD_MECHANICAL_SNAPSHOT_PASS",
  "observation_role":role,
  "captured_at_utc":captured,
  "canonical_cadence":"03:17 UTC daily",
  "ethereum_block_number":pop["ethereum_block_number"],
  "ethereum_block_hash":pop["ethereum_block_hash"],
  "population":{
    "historical_candidate_pair_count":pop.get("historical_candidate_pair_count"),
    "active_debt_pair_count":pop.get("active_debt_pair_count"),
    "inactive_pair_count":pop.get("inactive_pair_count"),
    "borrow_event_count":pop.get("borrow_event_count"),
    "canonical_active_pair_set_sha256":active_sha,
    "contiguous_complete_coverage":pop.get("contiguous_complete_coverage"),
    "all_chunks_pass":pop.get("all_chunks_pass"),
    "borrow_decode_error_count":pop.get("borrow_decode_error_count"),
    "uad_error_count":pop.get("uad_error_count")
  },
  "components":{
    "included_pair_count":comp.get("included_pair_count"),
    "excluded_pair_count":comp.get("excluded_pair_count"),
    "count_coverage":comp.get("count_coverage"),
    "debt_coverage":comp.get("debt_coverage"),
    "total_active_debt_value_ray":comp.get("total_active_debt_value_ray"),
    "included_debt_value_ray":comp.get("included_debt_value_ray"),
    "component_rows_sha256":sha_obj(rows),
    "frozen_hf_relative_tolerance":comp.get("frozen_hf_relative_tolerance"),
    "exact_debt_equality_required":comp.get("exact_debt_equality_required"),
    "all_scientific_calls_block_pinned":comp.get("all_scientific_calls_block_pinned")
  },
  "curve":{
    "baseline":curve.get("baseline"),
    "points":curve.get("points"),
    "geometry":curve.get("geometry"),
    "curve_sha256":curve.get("curve_sha256"),
    "frozen_stress_bps":[0,25,50,75,100,150,200,300,500]
  },
  "workflow":{
    "github_run_id":os.environ.get("GITHUB_RUN_ID"),
    "github_run_attempt":os.environ.get("GITHUB_RUN_ATTEMPT"),
    "github_event_name":event,
    "git_sha":os.environ.get("GITHUB_SHA")
  },
  "predictor_only_accumulation_gate":{
    "minimum_canonical_successful_daily_observations":30,
    "minimum_distinct_utc_days":21,
    "outcomes_opened":False
  },
  "raw_wallet_addresses_retained":False,
  "market_returns_opened":False,
  "future_liquidation_outcomes_opened":False,
  "pnl_opened":False,
  "live_trading":False,
  "mutation":False
}
receipt["snapshot_sha256"]=sha_obj({k:v for k,v in receipt.items() if k!="snapshot_sha256"})
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))

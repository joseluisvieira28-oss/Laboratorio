#!/usr/bin/env python3
from __future__ import annotations

import json, subprocess
from pathlib import Path

HERE=Path("research/liquidation_convexity_oracle_distance_001")
ADJ=HERE/"LCOD_FORWARD_PROVENANCE_ADJUDICATION_001.json"
LOCK=HERE/"LCOD_SCIENTIFIC_CORE_LOCK_V0.1.json"
SNAPDIR=HERE/"forward_snapshots"

adj=json.loads(ADJ.read_text())
lock=json.loads(LOCK.read_text())
errors=[]

if adj.get("classification")!="PROVENANCE_EQUIVALENCE_PASS":
    errors.append("ADJUDICATION_NOT_PASS")
if adj.get("scientific_core_fingerprint_sha256")!=lock.get("scientific_core_fingerprint_sha256"):
    errors.append("FINGERPRINT_LOCK_MISMATCH")
if adj.get("scientific_core_blob_shas")!=lock.get("files"):
    errors.append("CORE_BLOB_MAP_LOCK_MISMATCH")
if adj.get("scientific_core_changed_between_observed_shas") is not False:
    errors.append("SCIENTIFIC_CORE_CHANGE_FLAG_NOT_FALSE")
for flag in ("outcome_data_opened","market_returns_opened","liquidation_outcomes_opened","pnl_opened","snapshot_mutated"):
    if adj.get(flag) is not False:
        errors.append(f"BAD_ADJUDICATION_FLAG:{flag}")

target=adj.get("target_snapshot",{})
snap_path=SNAPDIR/str(target.get("file",""))
if not snap_path.exists():
    errors.append("TARGET_SNAPSHOT_MISSING")
    snap={}
else:
    snap=json.loads(snap_path.read_text())
    if snap.get("snapshot_sha256")!=target.get("snapshot_sha256"):
        errors.append("TARGET_SNAPSHOT_SHA_MISMATCH")
    if int(snap.get("ethereum_block_number",-1))!=int(target.get("ethereum_block_number",-2)):
        errors.append("TARGET_BLOCK_MISMATCH")
    if snap.get("workflow",{}).get("scientific_code_sha") is not None:
        errors.append("ORIGINAL_MISSING_SHA_ASSUMPTION_CHANGED")
    for flag in ("market_returns_opened","future_liquidation_outcomes_opened","pnl_opened","mutation"):
        if snap.get(flag) is not False:
            errors.append(f"SNAPSHOT_BOUNDARY_FLAG:{flag}")

commits=set()
obs=adj.get("observed_job_checkout_shas",{})
if obs.get("prepare"): commits.add(obs["prepare"])
for sha in obs.get("classify_population",{}): commits.add(sha)
if obs.get("aggregate_population"): commits.add(obs["aggregate_population"])
if obs.get("reconstruct_and_curve"): commits.add(obs["reconstruct_and_curve"])

historical={}
for commit in sorted(commits):
    historical[commit]={}
    for path,expected in lock["files"].items():
        try:
            got=subprocess.check_output(["git","rev-parse",f"{commit}:{path}"],text=True,stderr=subprocess.STDOUT).strip()
        except subprocess.CalledProcessError:
            errors.append(f"HISTORICAL_BLOB_UNREADABLE:{commit}:{path}")
            continue
        historical[commit][path]=got
        if got!=expected:
            errors.append(f"HISTORICAL_BLOB_MISMATCH:{commit}:{path}:{expected}:{got}")

out={
    "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
    "stage":"FORWARD_PROVENANCE_ADJUDICATION_VERIFICATION_V0.1",
    "classification":"PROVENANCE_ADJUDICATION_VERIFIED" if not errors else "PROVENANCE_ADJUDICATION_BLOCKED",
    "adjudication_id":adj.get("adjudication_id"),
    "target_snapshot_sha256":target.get("snapshot_sha256"),
    "scientific_core_fingerprint_sha256":lock.get("scientific_core_fingerprint_sha256"),
    "observed_commit_count":len(commits),
    "historical_blob_shas":historical,
    "errors":errors,
    "outcomes_opened":False,
    "promotion_credit":0
}
print(json.dumps(out,indent=2,sort_keys=True))
if errors:
    raise SystemExit(2)

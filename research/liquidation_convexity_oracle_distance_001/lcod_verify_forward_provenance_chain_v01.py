#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, subprocess
from pathlib import Path

HERE=Path("research/liquidation_convexity_oracle_distance_001")
INDEX=HERE/"LCOD_FORWARD_SERIES_INDEX_V0.1.json"
LOCK=HERE/"LCOD_SCIENTIFIC_CORE_LOCK_V0.1.json"
ADJ=HERE/"LCOD_FORWARD_PROVENANCE_ADJUDICATION_001.json"
SNAPDIR=HERE/"forward_snapshots"

def load(p):
    return json.loads(p.read_text())

def snapshot_self_hash(x):
    y={k:v for k,v in x.items() if k!="snapshot_sha256"}
    raw=json.dumps(y,sort_keys=True,separators=(",",":"),default=str).encode()
    return hashlib.sha256(raw).hexdigest()

idx=load(INDEX)
lock=load(LOCK)
adj=load(ADJ)
errors=[]
rows=[]

def verify_core_at_commit(commit):
    actual={}
    for path,expected in lock["files"].items():
        try:
            got=subprocess.check_output(["git","rev-parse",f"{commit}:{path}"],text=True,stderr=subprocess.STDOUT).strip()
        except subprocess.CalledProcessError:
            return False, actual, f"UNREADABLE_COMMIT_OR_PATH:{commit}:{path}"
        actual[path]=got
        if got!=expected:
            return False, actual, f"SCIENTIFIC_CORE_DRIFT:{commit}:{path}:{expected}:{got}"
    return True, actual, None

for item in idx.get("canonical_observations",[]):
    fname=item.get("file")
    p=SNAPDIR/fname
    if not p.exists():
        errors.append(f"MISSING_SNAPSHOT:{fname}")
        continue
    x=load(p)
    row={
        "file":fname,
        "ethereum_block_number":x.get("ethereum_block_number"),
        "snapshot_sha256":x.get("snapshot_sha256"),
        "scientific_code_sha":x.get("workflow",{}).get("scientific_code_sha"),
        "provenance_mode":None,
        "scientific_core_fingerprint_sha256":lock.get("scientific_core_fingerprint_sha256")
    }

    recomputed=snapshot_self_hash(x)
    row["recomputed_snapshot_sha256"]=recomputed
    if recomputed!=x.get("snapshot_sha256"):
        errors.append(f"SNAPSHOT_SELF_HASH_MISMATCH:{fname}")

    for flag in ("market_returns_opened","future_liquidation_outcomes_opened","pnl_opened","mutation"):
        if x.get(flag) is not False:
            errors.append(f"BOUNDARY_FLAG:{fname}:{flag}")

    direct=x.get("workflow",{}).get("scientific_code_sha")
    if direct not in (None,""):
        ok,actual,err=verify_core_at_commit(direct)
        row["provenance_mode"]="DIRECT_CODE_SHA"
        row["historical_core_blob_shas"]=actual
        if not ok:
            errors.append(f"{fname}:{err}")
    else:
        target=adj.get("target_snapshot",{})
        checks=[
            adj.get("classification")=="PROVENANCE_EQUIVALENCE_PASS",
            target.get("file")==fname,
            target.get("snapshot_sha256")==x.get("snapshot_sha256"),
            int(target.get("ethereum_block_number",-1))==int(x.get("ethereum_block_number",-2)),
            adj.get("scientific_core_changed_between_observed_shas") is False,
            adj.get("scientific_core_fingerprint_sha256")==lock.get("scientific_core_fingerprint_sha256"),
            adj.get("snapshot_mutated") is False,
            adj.get("market_returns_opened") is False,
            adj.get("liquidation_outcomes_opened") is False,
            adj.get("pnl_opened") is False,
        ]
        row["provenance_mode"]="ADJUDICATED_EQUIVALENCE"
        if not all(checks):
            errors.append(f"ADJUDICATION_INVALID_FOR:{fname}")

    rows.append(row)

out={
    "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
    "stage":"FORWARD_PROVENANCE_CHAIN_V0.1",
    "classification":"FORWARD_PROVENANCE_CHAIN_PASS" if not errors else "FORWARD_PROVENANCE_CHAIN_BLOCKED",
    "canonical_snapshot_count":len(rows),
    "scientific_core_fingerprint_sha256":lock.get("scientific_core_fingerprint_sha256"),
    "snapshots":rows,
    "errors":errors,
    "market_returns_opened":False,
    "future_liquidation_outcomes_opened":False,
    "pnl_opened":False,
    "promotion_credit":0
}
print(json.dumps(out,indent=2,sort_keys=True))
if errors:
    raise SystemExit(2)

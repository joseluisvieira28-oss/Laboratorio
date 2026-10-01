#!/usr/bin/env python3
import json, pathlib, sys

P=pathlib.Path(__file__).with_name("LINEAGE_REGISTRY_V0.2.json")
r=json.loads(P.read_text(encoding="utf-8"))
errors=[]
required={"TERMINAL_NO_EDGE","SOURCE_BLOCKED","TIER2_QUASE_DIAMANTE","FORWARD_ONLY","OPERATOR_LIVE"}
seen={c["case_type"] for c in r["cases"]}
if seen != required: errors.append(f"case coverage mismatch: {seen}")
for c in r["cases"]:
    if c["case_type"]=="SOURCE_BLOCKED" and c["scientific_verdict"]=="NO_EDGE":
        errors.append("BLOCKED collapsed into NO_EDGE")
    if c["case_type"]=="OPERATOR_LIVE" and c["promotion"]!="NO_SCIENTIFIC_CREDIT":
        errors.append("operator lane leaked scientific credit")
    if c["case_type"]=="FORWARD_ONLY" and c["execution"]!="NOT_AUTHORIZED":
        errors.append("forward-only lane gained execution authority")
if r["negative_control"]["expected"]!="DATA_FAILURE_NOT_NO_EDGE":
    errors.append("negative control corrupted")
if r["rules"]["unresolved_same_plane_conflict"]!="FAIL_CLOSED":
    errors.append("conflict policy not fail-closed")
if errors:
    print(json.dumps({"status":"FAIL_CLOSED","errors":errors},indent=2)); sys.exit(1)
print(json.dumps({"status":"PASS","cases":len(r["cases"]),"negative_control":"PASS","branch_census":r["branch_census"]["count"]},indent=2))

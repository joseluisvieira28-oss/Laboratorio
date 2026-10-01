#!/usr/bin/env python3
import json, pathlib, sys
p=pathlib.Path(__file__).with_name("SEMANTIC_CENSUS_V0.3.json")
r=json.loads(p.read_text(encoding="utf-8"))
e=[]
if r["census"]["branch_count"] != 579: e.append("branch census drift")
if "PARTIAL_SEMANTIC_ADJUDICATION" not in r["census"]["coverage_claim"]: e.append("semantic overclaim")
if r["supersession_policy"]["automatic"] != "NEVER_CANONICAL_BY_VERSION_NUMBER_ALONE": e.append("unsafe supersession")
states={x["state"] for x in r["discoveries"]}
for need in ["TERMINAL_NO_EDGE","INSUFFICIENT_SAMPLE","SOURCE_BLOCKED","SOURCE_ONLY","FORWARD_ONLY","VALIDATED_MECHANISM"]:
    if need not in states:e.append("missing state "+need)
l2=next(x for x in r["discoveries"] if x["id"]=="L2-RESILIENCY-001")
if l2["state"]!="VALIDATED_MECHANISM" or "DO_NOT_PROMOTE" not in l2["next"]:e.append("L2 routing error")
pob=next(x for x in r["discoveries"] if x["id"]=="PREDICTION-ORACLE-BASIS-001")
if pob["state"]!="SOURCE_BLOCKED":e.append("POB blocker lost")
if e:
 print(json.dumps({"status":"FAIL_CLOSED","errors":e},indent=2));sys.exit(1)
print(json.dumps({"status":"PASS","branches":579,"semantically_adjudicated_discoveries":len(r["discoveries"]),"review_queue":len(r["lineage_candidates"]["high_value_review_queue"])},indent=2))

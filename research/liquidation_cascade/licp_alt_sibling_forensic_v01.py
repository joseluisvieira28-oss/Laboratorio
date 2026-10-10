#!/usr/bin/env python3
"""Forensic replay of original immutable archived receipts only.
Only structural fields of each row are emitted. No economic reranking or mutations.
"""
from __future__ import annotations
import argparse, hashlib, json, sys, traceback
from collections import defaultdict
from pathlib import Path

EXPECTED_RUNS={"old":"37789379322","green":"37930397916","latest":"37937441095"}
BTC="BTC_CONFIRMED";ALT="ALT_SECOND_WAVE"
def canonical(z):
 return json.dumps(z,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
def verified_receipts(folder,run):
 original=folder/"current"/"licp001_forward_observation_v01.json"
 if not original.is_file():raise RuntimeError(f"CANONICAL_CURRENT_RECEIPT_MISSING:{run}")
 data=original.read_bytes();d=json.loads(data)
 if str(d.get("github_run_id"))!=run or d.get("status")!="FORWARD_OBSERVATION" or d.get("live_trading") is not False:
  raise RuntimeError("ORIGINAL_CANONICAL_RUN_ID_BAD:"+run)
 receipt_files=list((folder/"durable_ledger"/"receipts").glob("*.json"))
 if not receipt_files:raise RuntimeError(f"IMMUTABLE_LEDGER_ARCHIVED_RECEIPTS_MISSING:{run}")
 return d,hashlib.sha256(data).hexdigest(),sorted(receipt_files)
def attributes(r):
 meta=r.get("meta",{})
 if r.get("family")==ALT:
  ignition=meta.get("btc_episode",{}).get("ignition",{})
 else:ignition=meta.get("ignition",{})
 return {"family":r.get("family"),"episode_id":r.get("episode_id"),
    "asset":r.get("propagation_asset"),"pressure":r.get("pressure"),
    "event_wall_ms":r.get("event_wall_ms"),"event_local_ns":r.get("event_local_ns"),
    "ignition_venue_ts":ignition.get("ignition_venue_ts"),
    "full_row_sha256":hashlib.sha256(canonical(r)).hexdigest(),
    "targets_present":sorted(r.get("targets",{}).keys())}
def duplicate_diagnosis(d):
 rows=d.get("records",[]);groups=defaultdict(list)
 for i,r in enumerate(rows):
  t=attributes(r);t["index"]=i
  groups[(t["family"],t["episode_id"])].append(t)
 dup=[]
 for (family,eid),vals in groups.items():
  if len(vals)<2:continue
  asset_set={x["asset"] for x in vals}
  same_asset=len(asset_set)<len(vals)
  verdict=("ALT_DISTINCT_ASSET_SIBLINGS" if family==ALT and not same_asset and
       asset_set<={"ETHUSDT","SOLUSDT"} else "GENUINE_POSSIBLE_SAME_ID_CONFLICT")
  dup.append({"family":family,"episode_id":eid,"status":verdict,
      "rows":vals,"asset_set":sorted(str(x) for x in asset_set)})
 return {"raw_count":len(rows),"btc_primary_count":sum(r.get("family")==BTC for r in rows),
  "ALT_secondary_count":sum(r.get("family")==ALT for r in rows),
  "intra_receipt_original_key_collisions":dup}
def main():
 p=argparse.ArgumentParser()
 for name in EXPECTED_RUNS:p.add_argument(f"--{name}",required=True)
 p.add_argument("--out",required=True)
 args=p.parse_args();dst=Path(args.out)
 try:
  results={}
  for name,run in EXPECTED_RUNS.items():
   folder=Path(getattr(args,name))
   cur,rawsha,receipts=verified_receipts(folder,run)
   diag=duplicate_diagnosis(cur)
   results[name]={"run":run,"original_receipt_sha256":rawsha,
     "source_git_commit":cur.get("github_sha"),
     "archived_accepted_receipt_files":len(receipts),
     "source_started_ms":cur.get("started_wall_ms"),
     "source_ended_ms":cur.get("ended_wall_ms"),**diag}
  latest=results["latest"]["intra_receipt_original_key_collisions"]
  old=results["old"]["intra_receipt_original_key_collisions"]
  if not latest or not old:raise RuntimeError("EXPECTED_BOTH_FAILED_RUN_COLLISION_GROUPS_MISSING")
  if any(x["status"]!="ALT_DISTINCT_ASSET_SIBLINGS" for x in latest+old):
   diagnosis="GENUINE_CONFLICT__DO_NOT_REPAIR_AUTOMATICALLY"
  else:diagnosis="ALT_SIBLING_STRUCTURAL_KEY_COLLISION_CONFIRMED"
  report={"status":diagnosis,"studied_original_run_artifact_ids":[11563520826,11617105136,11620565051],
    "original_receipt_diagnostics":results,
    "baseline_last_green_BTC_independent_episodes":10,
    "minimum_first20_gate":20,"minimum_distinct_utc_dates":3,
    "original_frozen_science_unchanged":True,
    "economic_data_source_already_opened":True,
    "economic_outcomes_recomputed":False,"new_executable_edge_credit":False,"live_go":False,
    "note":"Distinct ETHUSDT and SOLUSDT ALT rows share a BTC ignition episode_id by causal design. Audit primary family strictly by BTC identity; no ALT events count toward primary."}
  dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
  print("LICP_ALT_SIBLING_FORENSIC",json.dumps({
   "status":diagnosis,"per_run":[{"run":d["run"],"btc":d["btc_primary_count"],
       "alt":d["ALT_secondary_count"],
       "collisions":d["intra_receipt_original_key_collisions"]} for d in results.values()]
  },sort_keys=True),flush=True)
  if diagnosis!="ALT_SIBLING_STRUCTURAL_KEY_COLLISION_CONFIRMED":sys.exit(2)
 except Exception as e:
  dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_text(json.dumps({"status":"FORENSIC_FAIL_CLOSED","reason":repr(e),"live_go":False},indent=2)+"\n")
  traceback.print_exc();sys.exit(2)
if __name__=="__main__":main()

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
def duplicate_diagnosis(receipt_files):
 groups=defaultdict(list)
 raw_count=0;btc=alt=0
 for p in receipt_files:
  d=json.loads(Path(p).read_text())
  if d.get("status")!="FORWARD_OBSERVATION":
   raise ValueError("NON_CANONICAL_ACCEPTED_RECEIPT")
  for i,r in enumerate(d.get("records",[])):
   t=attributes(r);t["index"]=i
   t["source_receipt_run"]=str(d.get("github_run_id"))
   t["source_receipt_sha256"]=hashlib.sha256(Path(p).read_bytes()).hexdigest()
   raw_count+=1;btc+=int(t["family"]==BTC);alt+=int(t["family"]==ALT)
   groups[(t["family"],t["episode_id"])].append(t)
 dup=[]
 for (family,eid),vals in groups.items():
  differing={x["full_row_sha256"] for x in vals}
  if len(differing)<=1:continue # byte-identical repeat is idempotent
  asset_set={x["asset"] for x in vals}
  hashes_by_asset=defaultdict(set)
  for x in vals:hashes_by_asset[x["asset"]].add(x["full_row_sha256"])
  same_asset_variation=any(len(h)>1 for h in hashes_by_asset.values())
  legit=(family==ALT and asset_set=={"ETHUSDT","SOLUSDT"} and not same_asset_variation)
  dup.append({"family":family,"episode_id":eid,
    "status":"ALT_DISTINCT_ASSET_SIBLINGS" if legit else "GENUINE_POSSIBLE_SAME_ID_CONFLICT",
    "rows":vals,"asset_set":sorted(str(x) for x in asset_set),
    "record_count":len(vals)})
 return {"raw_count":raw_count,"btc_primary_count":btc,
  "ALT_secondary_count":alt,
  "restored_ledger_original_key_divergences":dup}

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
   diag=duplicate_diagnosis(receipts)
   results[name]={"run":run,"original_receipt_sha256":rawsha,
     "source_git_commit":cur.get("github_sha"),
     "archived_accepted_receipt_files":len(receipts),
     "source_started_ms":cur.get("started_wall_ms"),
     "source_ended_ms":cur.get("ended_wall_ms"),**diag}
  latest=results["latest"]["restored_ledger_original_key_divergences"]
  old=results["old"]["restored_ledger_original_key_divergences"]
  print("ARCHIVED_COLLISION_GROUP_CENSUS",json.dumps({name:{
   "restored_receipts":results[name]["archived_accepted_receipt_files"],
   "raw_count":results[name]["raw_count"],
   "collision_groups":len(results[name]["restored_ledger_original_key_divergences"]),
   "alt_groups":[{"id":g["episode_id"],"assets":g["asset_set"],"status":g["status"]}
    for g in results[name]["restored_ledger_original_key_divergences"]]} for name in results},sort_keys=True),flush=True)
  if not latest and not old:raise RuntimeError("ORIGINAL_FAILED_V03_ARCHIVES_HAVE_NO_DIFFERING_KEY_ROWS")
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
       "collisions":d["restored_ledger_original_key_divergences"]} for d in results.values()]
  },sort_keys=True),flush=True)
  if diagnosis!="ALT_SIBLING_STRUCTURAL_KEY_COLLISION_CONFIRMED":sys.exit(2)
 except Exception as e:
  dst.parent.mkdir(parents=True,exist_ok=True)
  dst.write_text(json.dumps({"status":"FORENSIC_FAIL_CLOSED","reason":repr(e),"live_go":False},indent=2)+"\n")
  traceback.print_exc();sys.exit(2)
if __name__=="__main__":main()

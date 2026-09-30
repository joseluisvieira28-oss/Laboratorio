#!/usr/bin/env python3
import argparse,json
from collections import defaultdict
from pathlib import Path

MONTHS=("202407","202408","202409")
ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_RECEIPT_V0.1.json"

errs=[];monthly={}
for m in MONTHS:
    hits=sorted(ROOT.rglob(f"MARGINFI_SOL_ROUTE_MIGRATION_{m}_RECEIPT_V0.1.json"))
    if len(hits)!=1:
        errs.append(f"{m}:receipt_count:{len(hits)}");continue
    o=json.loads(hits[0].read_text());monthly[m]=o
    if o.get("classification")!="MARGINFI_SOL_ROUTE_MIGRATION_MONTH_PASS":errs.append(f"{m}:not_pass")
    if int(o.get("sample_count",-1))!=128:errs.append(f"{m}:sample_count")
    if int(o.get("complete_count",-1))!=128:errs.append(f"{m}:complete_count")
    if int(o.get("identity_conflict_count",-1))!=0:errs.append(f"{m}:identity_conflict")
    if int(o.get("source_evidence_incomplete",-1))!=0:errs.append(f"{m}:incomplete")

programs=set()
presence={}
for m,o in monthly.items():
    d={x["programId"]:{"count":int(x["count"]),"share":float(x["share"])} for x in o.get("after_program_transaction_presence") or []}
    presence[m]=d;programs|=set(d)

comparison=[]
candidates=[]
for p in sorted(programs):
    row={"programId":p}
    for m in MONTHS:
        x=presence.get(m,{}).get(p,{"count":0,"share":0.0})
        row[m]={"count":x["count"],"share":x["share"]}
    j=row["202407"]["share"];a=row["202408"]["share"];s=row["202409"]["share"]
    aug_flag=(a>=0.10 and (j==0 or a>=2*j))
    sep_flag=(s>=0.10 and (j==0 or s>=2*j))
    row["route_migration_candidate"]=bool(aug_flag or sep_flag)
    row["candidate_reason"]=(["AUG_SHARE_GE_10_AND_GE_2X_JUL"] if aug_flag else [])+(["SEP_SHARE_GE_10_AND_GE_2X_JUL"] if sep_flag else [])
    comparison.append(row)
    if row["route_migration_candidate"]:candidates.append(row)

comparison.sort(key=lambda r:(not r["route_migration_candidate"],
                              -max(r["202408"]["share"],r["202409"]["share"]),
                              r["programId"]))
classification="MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_BLOCKED" if errs else "MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_PASS"
receipt={
 "schema_version":"0.1","lab_id":"DLS-MARGINFI-SOL-ROUTE-MIGRATION-001","classification":classification,
 "authority":"MARGINFI_SOL_ROUTE_MIGRATION_V0_1_SOURCE_FREEZE_2026-09-30.md",
 "months":{m:{
   "population_count":monthly[m]["population_count"],
   "sample_count":monthly[m]["sample_count"],
   "complete_count":monthly[m]["complete_count"],
   "zero_after_transaction_count":monthly[m]["zero_after_transaction_count"]
 } for m in MONTHS if m in monthly},
 "program_presence_comparison":comparison,
 "route_migration_candidate_count":len(candidates),
 "route_migration_candidates":candidates,
 "program_semantics_labeled":False,
 "error_count":len(errs),"errors":errs,
 "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
             "market_2024_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"months":receipt["months"],
 "candidate_count":len(candidates),"candidates":candidates[:20]},indent=2))
if classification!="MARGINFI_SOL_ROUTE_MIGRATION_SOURCE_PASS":raise SystemExit(2)

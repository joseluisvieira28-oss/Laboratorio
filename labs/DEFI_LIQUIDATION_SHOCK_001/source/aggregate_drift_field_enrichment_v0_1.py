#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--receipts",required=True)
ap.add_argument("--source-authority",required=True)
args=ap.parse_args()

ROOT=Path(args.receipts); AUTH=Path(args.source_authority)
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json")
CLASSES=["liquidate_perp","liquidate_spot","liquidate_borrow_for_perp_pnl","liquidate_perp_pnl_for_deposit"]
EXPECTED_PARTITIONS=86

final=None
for p in AUTH.rglob("DRIFT_EVENT_CENSUS_FINAL_AUTHORITY_RECEIPT_V0.1.json"):
    final=json.loads(p.read_text()); break
if final is None: raise SystemExit("missing_final_drift_authority_receipt")

errors=[]
if final.get("classification")!="DRIFT_FOUR_CLASS_EVENT_CENSUS_SOURCE_PASS":
    errors.append({"reason":"source_authority_not_pass","classification":final.get("classification")})

expected_classes={}
for cls in CLASSES:
    ent=((final.get("classes") or {}).get(cls) or {})
    expected_classes[cls]=int(ent.get("successful_instruction_count") or 0)
    if expected_classes[cls]<=0:
        errors.append({"reason":"source_authority_missing_class_count","class":cls})

receipts=[]
for p in sorted(ROOT.rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("protocol")=="drift" and r.get("classification") in ("FIELD_ENRICHMENT_PARTITION_PASS","FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED"):
        r["_file"]=str(p);receipts.append(r)

seen=set()
for r in receipts:
    pid=r.get("partition_id")
    if not pid: errors.append({"reason":"missing_partition_id","file":r.get("_file")})
    elif pid in seen: errors.append({"reason":"duplicate_partition_id","partition_id":pid})
    seen.add(pid)

if len(receipts)!=EXPECTED_PARTITIONS:
    errors.append({"reason":"partition_count_mismatch","observed":len(receipts),"expected":EXPECTED_PARTITIONS})
pass_count=sum(1 for r in receipts if r.get("classification")=="FIELD_ENRICHMENT_PARTITION_PASS")
if pass_count!=EXPECTED_PARTITIONS:
    errors.append({"reason":"partition_pass_count_mismatch","observed":pass_count,"expected":EXPECTED_PARTITIONS})

baseline_total=sum(int(r.get("baseline_success_count") or 0) for r in receipts)
enriched_total=sum(int(r.get("enriched_success_count") or 0) for r in receipts)
missing=sum(int(r.get("missing_count") or 0) for r in receipts)
extra=sum(int(r.get("extra_count") or 0) for r in receipts)
dup=sum(int(r.get("duplicate_count") or 0) for r in receipts)
conflict=sum(int(r.get("semantic_conflict_count") or 0) for r in receipts)
banom=sum(int(r.get("baseline_anomaly_count") or 0) for r in receipts)
qanom=sum(int(r.get("query_anomaly_count") or 0) for r in receipts)
accounts=sum(int(r.get("nonempty_accounts_count") or 0) for r in receipts)
market=sum(int(r.get("market_identity_count") or 0) for r in receipts)
abi=sum(int(r.get("abi_shape_valid_count") or 0) for r in receipts)

class_obs={cls:{"baseline":0,"enriched":0,"expected":expected_classes[cls]} for cls in CLASSES}
for r in receipts:
    cc=r.get("class_counts") or {}
    for cls in CLASSES:
        class_obs[cls]["baseline"]+=int(((cc.get(cls) or {}).get("baseline") or 0))
        class_obs[cls]["enriched"]+=int(((cc.get(cls) or {}).get("enriched") or 0))

for cls,v in class_obs.items():
    if v["baseline"]!=v["expected"] or v["enriched"]!=v["expected"]:
        errors.append({"reason":"class_population_mismatch","class":cls,**v})

expected_total=sum(expected_classes.values())
if baseline_total!=expected_total or enriched_total!=expected_total:
    errors.append({"reason":"total_population_mismatch","baseline":baseline_total,"enriched":enriched_total,"expected":expected_total})
if any((missing,extra,dup,conflict,banom,qanom)):
    errors.append({"reason":"join_or_semantic_nonzero","missing":missing,"extra":extra,"duplicate":dup,
                   "semantic_conflict":conflict,"baseline_anomaly":banom,"query_anomaly":qanom})
if accounts!=expected_total or market!=expected_total or abi!=expected_total:
    errors.append({"reason":"field_coverage_incomplete","accounts":accounts,"market_identity":market,
                   "abi_shape":abi,"expected":expected_total})

receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"DRIFT_FIELD_ENRICHMENT_POPULATION_PASS" if not errors else "DRIFT_FIELD_ENRICHMENT_POPULATION_BLOCKED_FAIL_CLOSED",
 "source_authority_classification":final.get("classification"),"source_expected_class_counts":expected_classes,
 "partition_receipt_count":len(receipts),"partition_pass_count":pass_count,
 "baseline_success_count":baseline_total,"enriched_success_count":enriched_total,"expected_success_count":expected_total,
 "class_counts":class_obs,"missing_count":missing,"extra_count":extra,"duplicate_count":dup,
 "semantic_conflict_count":conflict,"baseline_anomaly_count":banom,"query_anomaly_count":qanom,
 "nonempty_accounts_count":accounts,"market_identity_count":market,"abi_shape_valid_count":abi,
 "error_count":len(errors),"errors":errors,
 "semantic_scope":"common account roles + protocol-native market indexes + ABI shape; economic argument values excluded",
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"token_balances":False,"token_amounts":False,"token_decimals":False,
             "limit_price_values":False,"requested_max_amount_values":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if receipt["classification"]!="DRIFT_FIELD_ENRICHMENT_POPULATION_PASS":raise SystemExit(2)

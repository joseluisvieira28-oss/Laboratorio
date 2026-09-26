#!/usr/bin/env python3
import argparse, json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
args=ap.parse_args()
ROOT=Path(args.root)
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/GLOBAL_FIELD_COVERAGE_FINAL_RECEIPT_V0.1.json")

def find_json(name):
    hits=list(ROOT.rglob(name))
    if not hits:return None,None
    # deterministic: lexical first, but duplicate differing receipts are a conflict
    objs=[]
    for p in sorted(hits):
        try:objs.append((p,json.loads(p.read_text())))
        except Exception:continue
    if not objs:return None,None
    first=objs[0][1]
    for p,o in objs[1:]:
        if o!=first:
            return first,{"reason":"duplicate_receipt_content_conflict","name":name,"files":[str(x[0]) for x in objs]}
    return first,None

required={
 "kamino_save11_field":(["KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json"],"KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS"),
 "marginfi_save0c_field":(["MARGINFI_SAVE0C_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json"],"MARGINFI_SAVE0C_FIELD_ENRICHMENT_POPULATION_PASS"),
 "drift_field":(["DRIFT_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json"],"DRIFT_FIELD_ENRICHMENT_POPULATION_PASS"),
 "kamino_save11_units":(["KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json"],"KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS"),
 "save0c_units":(["SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.2.json","SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json"],"SAVE0C_UNIT_METADATA_POPULATION_PASS"),
 "marginfi_units":(["MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.2.json","MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.1.json"],"MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS"),
 "drift_units":(["DRIFT_MARKET_UNIT_REGISTRY_POPULATION_RECEIPT_V0.1.json"],"DRIFT_MARKET_UNIT_REGISTRY_POPULATION_PASS"),
}

def select_receipt(names):
    for name in names:
        obj,conf=find_json(name)
        if obj is not None or conf is not None:
            return name,obj,conf
    return None,None,None

errors=[];checks={};selected={}
for key,(names,expected) in required.items():
    name,obj,conf=select_receipt(names)
    selected[key]=(name,obj)
    if conf:
        errors.append(conf)
    if obj is None:
        checks[key]={"present":False,"expected":expected,"candidate_names":names}
        errors.append({"reason":"missing_required_receipt","key":key,"candidate_names":names})
        continue
    actual=obj.get("classification")
    ok=(actual==expected)
    checks[key]={"present":True,"selected_receipt":name,"classification":actual,"expected":expected,"pass":ok}
    if not ok:
        errors.append({"reason":"required_classification_mismatch","key":key,"selected_receipt":name,
                       "actual":actual,"expected":expected})

# Explicit zero-missing/conflict checks from available receipts.
def nonzero(obj,fields,prefix):
    for f in fields:
        v=obj.get(f)
        if isinstance(v,(int,float)) and v!=0:
            errors.append({"reason":"required_zero_field_nonzero","receipt":prefix,"field":f,"value":v})

for key,(names,expected) in required.items():
    name,obj=selected.get(key,(None,None))
    if not obj:continue
    nonzero(obj,[
      "missing_count","extra_count","duplicate_count","semantic_conflict_count",
      "baseline_anomaly_count","query_anomaly_count","source_conflict_count",
      "unresolved_required_field_count","guessed_decimal_count","guessed_mapping_count"
    ],key)
    if key=="save0c_units":
        if int(obj.get("collateral_underlying_unmapped_event_count") or 0)!=0:
            errors.append({"reason":"save0c_unmapped_collateral_underlying","count":obj.get("collateral_underlying_unmapped_event_count")})
    if key=="marginfi_units":
        if int(obj.get("unmapped_asset_bank_count") or 0)!=0:
            errors.append({"reason":"marginfi_unmapped_asset_banks","count":obj.get("unmapped_asset_bank_count")})
    if key=="drift_units":
        if (obj.get("unresolved_spot_market_indexes") or []) or (obj.get("unresolved_perp_market_indexes") or []):
            errors.append({"reason":"drift_unresolved_market_indexes",
                           "spot":obj.get("unresolved_spot_market_indexes") or [],
                           "perp":obj.get("unresolved_perp_market_indexes") or []})

classification="GLOBAL_FIELD_COVERAGE_FINAL_PASS" if not errors else "GLOBAL_FIELD_COVERAGE_PENDING_SOURCE_COMPLETION"
# Any explicit blocked fail-closed receipt upgrades global taxonomy to BLOCKED.
for key,c in checks.items():
    actual=c.get("classification")
    if isinstance(actual,str) and "BLOCKED_FAIL_CLOSED" in actual:
        classification="GLOBAL_FIELD_COVERAGE_BLOCKED_FAIL_CLOSED"

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":classification,
 "frozen_gate":"GLOBAL_FIELD_COVERAGE_FINAL_GATE_FREEZE_V0.1.md",
 "checks":checks,"error_count":len(errors),"errors":errors,
 "source_authorities_already_closed":{
   "kamino_save11":"KAMINO_SAVE11_EVENT_CENSUS_SOURCE_PASS + independent audit PASS",
   "marginfi_save0c":"MARGINFI_SAVE0C_EVENT_CENSUS_SOURCE_PASS",
   "drift":"DRIFT_FOUR_CLASS_EVENT_CENSUS_SOURCE_PASS"
 },
 "decoder_transport_authorities_already_closed":[
   "FIELD_ENRICHMENT_TRANSPORT_8_OF_8_PASS",
   "FIELD_ENRICHMENT_CANONICAL_JOIN_3_OF_3_FAMILY_PASS",
   "FIELD_DECODER_AUTHORITY_8_OF_8_CLASS_PASS",
   "FIELD_DECODER_IMPLEMENTATION_8_OF_8_PASS"
 ],
 "amount_semantics_firewall":{
   "requested_or_max_argument_values_authorized":False,
   "realized_transfer_amounts_authorized":False,
   "prices_authorized":False,
   "usd_notional_authorized":False,
   "returns_authorized":False,
   "pnl_authorized":False
 },
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"token_amounts":False,"requested_amount_values":False,
             "realized_transfer_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="GLOBAL_FIELD_COVERAGE_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if classification!="GLOBAL_FIELD_COVERAGE_FINAL_PASS":raise SystemExit(3)

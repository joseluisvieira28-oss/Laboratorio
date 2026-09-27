#!/usr/bin/env python3
import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--original-field",required=True)
ap.add_argument("--kamino-field-recovery",required=True)
ap.add_argument("--original-unit",required=True)
ap.add_argument("--kamino-unit-v03",required=True)
ap.add_argument("--save11-field-v04",required=True)
ap.add_argument("--save11-unit-v04",required=True)
args=ap.parse_args()

FIELD_OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.3.json")
UNIT_OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.4.json")

EXPECTED={"kamino":60699,"save11":13300}
K_FIELD_ORIG=["kamino-202311","kamino-202312","kamino-202401","kamino-202402","kamino-202403","kamino-202404","kamino-202405"]
K_FIELD_REC=[f"kamino-2024{m:02d}" for m in range(6,13)]
K_UNIT_ORIG=["kamino-202311","kamino-202312","kamino-202401","kamino-202402"]
K_UNIT_REC=[f"kamino-2024{m:02d}" for m in range(3,13)]
SAVE=[f"save11-2024{m:02d}" for m in range(7,13)]

def scan(root,kind):
    out={}
    for p in sorted(Path(root).rglob("*.json")):
        try:r=json.loads(p.read_text())
        except Exception:continue
        pid=r.get("partition_id")
        if not pid:continue
        c=str(r.get("classification",""))
        if kind=="field" and not c.startswith("FIELD_ENRICHMENT_PARTITION_"):continue
        if kind=="unit" and not c.startswith("KAMINO_SAVE11_UNIT_METADATA_PARTITION_"):continue
        out.setdefault(pid,[]).append((p,r))
    return out

of=scan(args.original_field,"field")
kf=scan(args.kamino_field_recovery,"field")
ou=scan(args.original_unit,"unit")
ku=scan(args.kamino_unit_v03,"unit")
sf=scan(args.save11_field_v04,"field")
su=scan(args.save11_unit_v04,"unit")

def choose(src,pid,label,errors):
    hits=src.get(pid,[])
    if len(hits)!=1:
        errors.append({"reason":"receipt_count","source":label,"partition_id":pid,"observed":len(hits),"expected":1})
        return None
    return {"source":label,"file":str(hits[0][0]),"receipt":hits[0][1]}

field_errors=[];field_selected={}
for pid in K_FIELD_ORIG:
    x=choose(of,pid,"ORIGINAL_FIELD_V0.1",field_errors)
    if x:field_selected[pid]=x
for pid in K_FIELD_REC:
    x=choose(kf,pid,"KAMINO_FIELD_RECOVERY_V0.2",field_errors)
    if x:field_selected[pid]=x
for pid in SAVE:
    x=choose(sf,pid,"SAVE11_FIELD_RECOVERY_V0.4",field_errors)
    if x:field_selected[pid]=x

field_protocols={}
for protocol,expected,expected_parts in [("kamino",60699,14),("save11",13300,6)]:
    items=[x for pid,x in field_selected.items() if x["receipt"].get("protocol")==protocol]
    vals={k:sum(int(x["receipt"].get(k) or 0) for x in items) for k in [
      "baseline_success_count","enriched_success_count","missing_count","extra_count","duplicate_count",
      "semantic_conflict_count","baseline_anomaly_count","nonempty_accounts_count",
      "full_instruction_data_count","exact_abi_shape_count"
    ]}
    ppass=sum(1 for x in items if x["receipt"].get("classification")=="FIELD_ENRICHMENT_PARTITION_PASS")
    if len(items)!=expected_parts:field_errors.append({"reason":"field_partition_count","protocol":protocol,"observed":len(items),"expected":expected_parts})
    if ppass!=expected_parts:field_errors.append({"reason":"field_partition_pass_count","protocol":protocol,"observed":ppass,"expected":expected_parts})
    if vals["baseline_success_count"]!=expected or vals["enriched_success_count"]!=expected:
        field_errors.append({"reason":"field_population_count","protocol":protocol,"baseline":vals["baseline_success_count"],
                             "enriched":vals["enriched_success_count"],"expected":expected})
    for k in ["missing_count","extra_count","duplicate_count","semantic_conflict_count","baseline_anomaly_count"]:
        if vals[k]!=0:field_errors.append({"reason":"field_required_zero_nonzero","protocol":protocol,"field":k,"value":vals[k]})
    for k in ["nonempty_accounts_count","full_instruction_data_count","exact_abi_shape_count"]:
        if vals[k]!=expected:field_errors.append({"reason":"field_coverage_incomplete","protocol":protocol,"field":k,"value":vals[k],"expected":expected})
    field_protocols[protocol]={"partition_count":len(items),"partition_pass_count":ppass,"expected_success_count":expected,**vals}

field_class="KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS" if not field_errors else "KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_BLOCKED_FAIL_CLOSED"
field_receipt={
 "schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":field_class,
 "precedence_authorities":["KAMINO_LAYOUT_RECOVERY_PRECEDENCE_ADDENDUM_V0.2.md",
                           "SAVE11_TRAILING_DATA_AND_UNIT_AUTHORITY_ADDENDUM_V0.4.md"],
 "protocols":field_protocols,"selected_partition_count":len(field_selected),
 "selected_receipts":[{"partition_id":pid,"source":x["source"],"file":x["file"],"classification":x["receipt"].get("classification")}
                      for pid,x in sorted(field_selected.items())],
 "error_count":len(field_errors),"errors":field_errors,
 "firewall":{"prices":False,"returns":False,"pnl":False,"economic_outcomes":False,"token_amounts":False,
             "requested_amount_values":False,"trailing_byte_value_emitted":False,
             "protected_market_outcomes_2025_2026":False,"post_outcome_tuning":False,
             "live_trading":False,"merge_main":False}
}

unit_errors=[];unit_selected={}
for pid in K_UNIT_ORIG:
    x=choose(ou,pid,"ORIGINAL_UNIT_V0.1",unit_errors)
    if x:unit_selected[pid]=x
for pid in K_UNIT_REC:
    x=choose(ku,pid,"KAMINO_UNIT_AUTHORITY_V0.3",unit_errors)
    if x:unit_selected[pid]=x
for pid in SAVE:
    x=choose(su,pid,"SAVE11_UNIT_RECOVERY_V0.4",unit_errors)
    if x:unit_selected[pid]=x

unit_protocols={};registry={};resolution={}
for protocol,expected,expected_parts in [("kamino",60699,14),("save11",13300,6)]:
    items=[x for pid,x in unit_selected.items() if x["receipt"].get("protocol")==protocol]
    vals={k:sum(int(x["receipt"].get(k) or 0) for x in items) for k in [
      "baseline_success_count","enriched_success_count","unit_complete_event_count","missing_count","extra_count",
      "baseline_anomaly_count","query_anomaly_count","unit_conflict_count"
    ]}
    ppass=sum(1 for x in items if x["receipt"].get("classification")=="KAMINO_SAVE11_UNIT_METADATA_PARTITION_PASS")
    if len(items)!=expected_parts:unit_errors.append({"reason":"unit_partition_count","protocol":protocol,"observed":len(items),"expected":expected_parts})
    if ppass!=expected_parts:unit_errors.append({"reason":"unit_partition_pass_count","protocol":protocol,"observed":ppass,"expected":expected_parts})
    if vals["baseline_success_count"]!=expected or vals["enriched_success_count"]!=expected or vals["unit_complete_event_count"]!=expected:
        unit_errors.append({"reason":"unit_population_count","protocol":protocol,"baseline":vals["baseline_success_count"],
                            "enriched":vals["enriched_success_count"],"unit_complete":vals["unit_complete_event_count"],"expected":expected})
    for k in ["missing_count","extra_count","baseline_anomaly_count","query_anomaly_count","unit_conflict_count"]:
        if vals[k]!=0:unit_errors.append({"reason":"unit_required_zero_nonzero","protocol":protocol,"field":k,"value":vals[k]})
    unit_protocols[protocol]={"partition_count":len(items),"partition_pass_count":ppass,"expected_success_count":expected,**vals}
    for x in items:
        r=x["receipt"]
        for key in ["direct_pair_resolution_role_count","transfer_identity_fallback_role_count",
                    "primary_plus_crosscheck_role_count","primary_optional_missing_role_count"]:
            resolution[key]=resolution.get(key,0)+int(r.get(key) or 0)
        for e in r.get("event_units") or []:
            for role in ("debt_underlying","collateral_token","collateral_underlying"):
                u=e.get(role) or {};mint=u.get("mint");dec=u.get("decimals")
                if mint is not None and dec is not None:
                    k=(protocol,role,mint,int(dec));registry[k]=registry.get(k,0)+1

unit_class="KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS" if not unit_errors else "KAMINO_SAVE11_UNIT_METADATA_POPULATION_BLOCKED_FAIL_CLOSED"
unit_receipt={
 "schema_version":"0.4","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":unit_class,
 "precedence_authorities":["KAMINO_UNIT_METADATA_RECOVERY_PRECEDENCE_ADDENDUM_V0.3.md",
                           "SAVE11_TRAILING_DATA_AND_UNIT_AUTHORITY_ADDENDUM_V0.4.md"],
 "protocols":unit_protocols,"selected_partition_count":len(unit_selected),
 "selected_receipts":[{"partition_id":pid,"source":x["source"],"file":x["file"],"classification":x["receipt"].get("classification")}
                      for pid,x in sorted(unit_selected.items())],
 "resolution_counts":resolution,
 "unit_registry":[{"protocol":k[0],"role":k[1],"mint":k[2],"decimals":k[3],"event_observation_count":v}
                  for k,v in sorted(registry.items())],
 "error_count":len(unit_errors),"errors":unit_errors,"amount_fields_requested":False,
 "firewall":{"prices":False,"returns":False,"pnl":False,"economic_outcomes":False,
             "token_amounts":False,"token_balance_amounts":False,"requested_amount_values":False,
             "protected_market_outcomes_2025_2026":False,"post_outcome_tuning":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"merge_main":False}
}

FIELD_OUT.write_text(json.dumps(field_receipt,indent=2,sort_keys=True)+"\n")
UNIT_OUT.write_text(json.dumps(unit_receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"field_classification":field_class,"field_error_count":len(field_errors),
                  "unit_classification":unit_class,"unit_error_count":len(unit_errors)},indent=2))

if field_class!="KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS" or unit_class!="KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS":
    raise SystemExit(2)

#!/usr/bin/env python3
import argparse, json
from pathlib import Path
from datetime import datetime

ap=argparse.ArgumentParser()
ap.add_argument("--receipts",required=True)
ap.add_argument("--field-coverage",required=True)
ap.add_argument("--registry",required=True)
args=ap.parse_args()

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_MARKET_UNIT_REGISTRY_POPULATION_RECEIPT_V0.1.json")

def load_named(root,name):
    hits=sorted(Path(root).rglob(name))
    if not hits:return None
    return json.loads(hits[0].read_text())

def t(s): return datetime.fromisoformat(s.replace("Z","+00:00"))

field=load_named(args.field_coverage,"DRIFT_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json")
reg=load_named(args.registry,"DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_TEMPORAL_RECEIPT_V0.3.json")
errors=[]
if not field:
    errors.append({"reason":"missing_drift_field_enrichment_receipt"})
elif field.get("classification")!="DRIFT_FIELD_ENRICHMENT_POPULATION_PASS":
    errors.append({"reason":"field_enrichment_not_pass","classification":field.get("classification")})
if not reg:
    errors.append({"reason":"missing_temporal_registry_receipt"})
elif reg.get("classification")!="DRIFT_HISTORICAL_MARKET_UNIT_REGISTRY_TEMPORAL_SOURCE_PASS":
    errors.append({"reason":"temporal_registry_not_pass","classification":reg.get("classification")})

spot_reg=(reg or {}).get("spot_registry") or {}
perp_reg=(reg or {}).get("perp_registry") or {}

def resolve(registry,idx,ts):
    ent=registry.get(str(int(idx)))
    if not ent:return None,"market_index_absent"
    when=t(ts)
    hits=[]
    for v in ent.get("versions") or []:
        try:
            lo=t(v["effective_from"]); hi=t(v["effective_until"])
        except Exception:
            continue
        if lo<=when<hi:hits.append(v)
    if len(hits)==1:return hits[0],None
    if not hits:return None,"no_version_at_event_time"
    return None,"ambiguous_versions_at_event_time"

partition_receipts=[]
for p in sorted(Path(args.receipts).rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("protocol")=="drift" and str(r.get("classification","")).startswith("FIELD_ENRICHMENT_PARTITION_"):
        partition_receipts.append((p,r))

EXPECTED_PARTITIONS=86
if len(partition_receipts)!=EXPECTED_PARTITIONS:
    errors.append({"reason":"partition_receipt_count_mismatch","observed":len(partition_receipts),"expected":EXPECTED_PARTITIONS})

unresolved=[]; lookup_conflicts=[]; spot_usage={}; perp_usage={}
event_count=0; spot_lookup_count=0; perp_lookup_count=0
for p,r in partition_receipts:
    if r.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":
        errors.append({"reason":"partition_not_pass","partition_id":r.get("partition_id"),"classification":r.get("classification")})
        continue
    for e in r.get("enriched_rows") or []:
        event_count+=1
        ts=e.get("timestamp"); mi=e.get("market_identity") or {}
        refs=[]
        if "asset_spot_market_index" in mi: refs.append(("spot","asset_spot_market_index",mi["asset_spot_market_index"]))
        if "liability_spot_market_index" in mi: refs.append(("spot","liability_spot_market_index",mi["liability_spot_market_index"]))
        if "spot_market_index" in mi: refs.append(("spot","spot_market_index",mi["spot_market_index"]))
        if "perp_market_index" in mi: refs.append(("perp","perp_market_index",mi["perp_market_index"]))
        for typ,role,idx in refs:
            ver,err=resolve(spot_reg if typ=="spot" else perp_reg,idx,ts)
            if typ=="spot":spot_lookup_count+=1
            else:perp_lookup_count+=1
            if err:
                unresolved.append({"partition_id":r.get("partition_id"),"signature":e.get("signature"),
                                   "timestamp":ts,"type":typ,"role":role,"market_index":idx,"reason":err})
                continue
            if typ=="spot":
                if not ver.get("mint") or ver.get("decimals") is None:
                    lookup_conflicts.append({"signature":e.get("signature"),"type":typ,"market_index":idx,
                                             "reason":"resolved_spot_version_missing_unit","version":ver})
                    continue
                k=(int(idx),ver["mint"],int(ver["decimals"]),ver["effective_from"],ver["effective_until"])
                spot_usage[k]=spot_usage.get(k,0)+1
            else:
                if int(ver.get("base_precision") or 0)!=1000000000 or int(ver.get("quote_precision") or 0)!=1000000:
                    lookup_conflicts.append({"signature":e.get("signature"),"type":typ,"market_index":idx,
                                             "reason":"resolved_perp_precision_mismatch","version":ver})
                    continue
                k=(int(idx),ver.get("symbol"),ver.get("base_asset_symbol"),ver["effective_from"],ver["effective_until"])
                perp_usage[k]=perp_usage.get(k,0)+1

field_expected=int((field or {}).get("expected_success_count") or 0)
if field_expected and event_count!=field_expected:
    errors.append({"reason":"event_count_mismatch_vs_field_authority","observed":event_count,"expected":field_expected})

if lookup_conflicts:
    classification="DRIFT_MARKET_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED"
elif unresolved:
    classification="DRIFT_MARKET_UNIT_REGISTRY_PENDING_SOURCE_COMPLETION"
elif errors:
    classification="DRIFT_MARKET_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED"
else:
    classification="DRIFT_MARKET_UNIT_REGISTRY_POPULATION_PASS"

receipt={
 "schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "field_enrichment_classification":(field or {}).get("classification"),
 "temporal_registry_classification":(reg or {}).get("classification"),
 "partition_receipt_count":len(partition_receipts),"event_count":event_count,
 "spot_lookup_count":spot_lookup_count,"perp_lookup_count":perp_lookup_count,
 "unresolved_lookup_count":len(unresolved),"unresolved_lookups":unresolved[:200],
 "lookup_conflict_count":len(lookup_conflicts),"lookup_conflicts":lookup_conflicts[:200],
 "spot_versions_used":[{"market_index":k[0],"mint":k[1],"decimals":k[2],
                        "effective_from":k[3],"effective_until":k[4],"lookup_count":v}
                       for k,v in sorted(spot_usage.items())],
 "perp_versions_used":[{"market_index":k[0],"symbol":k[1],"base_asset_symbol":k[2],
                        "effective_from":k[3],"effective_until":k[4],
                        "base_precision":1000000000,"base_precision_exp":9,
                        "quote_precision":1000000,"quote_precision_exp":6,"lookup_count":v}
                       for k,v in sorted(perp_usage.items())],
 "error_count":len(errors),"errors":errors,
 "temporal_rule":"latest authenticated source registry version effective at each frozen event timestamp",
 "firewall":{"prices":False,"oracle_values":False,"usd_notional":False,"returns":False,"pnl":False,
             "direction":False,"economic_outcomes":False,"token_amounts":False,
             "requested_max_amount_values":False,"limit_price_values":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"paid_source":False,"account_creation":False,
             "post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt[k] for k in ["classification","partition_receipt_count","event_count",
                                         "spot_lookup_count","perp_lookup_count",
                                         "unresolved_lookup_count","lookup_conflict_count","error_count"]},indent=2))
if classification=="DRIFT_MARKET_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED":raise SystemExit(2)
if classification!="DRIFT_MARKET_UNIT_REGISTRY_POPULATION_PASS":raise SystemExit(3)

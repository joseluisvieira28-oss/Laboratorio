#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(sys.argv[1])
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARGINFI_BANK_UNIT_REGISTRY_RECEIPT_V0.1.json")
EXPECTED_EVENTS=266647; EXPECTED_PARTITIONS=23
recs=[]
for p in sorted(ROOT.rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("protocol")=="marginfi" and str(r.get("classification","")).startswith("MARGINFI_BANK_UNIT_REGISTRY_PARTITION_"):
        recs.append(r)
errors=[]; seen=set(); registry={}; asset=set();liab=set()
baseline=enriched=missing=extra=banom=metamiss=conflicts=0
for r in recs:
    pid=r.get("partition_id")
    if not pid or pid in seen:errors.append({"reason":"bad_or_duplicate_partition_id","partition_id":pid})
    seen.add(pid)
    if r.get("classification")!="MARGINFI_BANK_UNIT_REGISTRY_PARTITION_PASS":
        errors.append({"reason":"partition_not_pass","partition_id":pid,"classification":r.get("classification")})
    baseline+=int(r.get("baseline_success_count") or 0);enriched+=int(r.get("enriched_success_count") or 0)
    missing+=int(r.get("missing_count") or 0);extra+=int(r.get("extra_count") or 0)
    banom+=int(r.get("baseline_anomaly_count") or 0);metamiss+=int(r.get("metadata_missing_event_count") or 0)
    conflicts+=int(r.get("conflict_count") or 0)
    asset.update(r.get("asset_banks") or []);liab.update(r.get("liab_banks") or [])
    for x in r.get("liability_bank_unit_observations") or []:
        b=x["bank"];pair=(x["mint"],int(x["decimals"]))
        if b in registry and registry[b]!=pair:
            errors.append({"reason":"cross_partition_bank_unit_conflict","bank":b,
                           "prior":{"mint":registry[b][0],"decimals":registry[b][1]},
                           "new":{"mint":pair[0],"decimals":pair[1]}})
        registry[b]=pair
if len(recs)!=EXPECTED_PARTITIONS:errors.append({"reason":"partition_count_mismatch","observed":len(recs),"expected":EXPECTED_PARTITIONS})
if baseline!=EXPECTED_EVENTS or enriched!=EXPECTED_EVENTS:errors.append({"reason":"event_count_mismatch","baseline":baseline,"enriched":enriched,"expected":EXPECTED_EVENTS})
if any((missing,extra,banom,metamiss,conflicts)):errors.append({"reason":"partition_nonzero_errors","missing":missing,"extra":extra,"baseline_anomaly":banom,"metadata_missing_events":metamiss,"conflicts":conflicts})
unmapped_asset=sorted(asset-set(registry))
if errors:
    classification="MARGINFI_BANK_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED"
elif unmapped_asset:
    classification="MARGINFI_BANK_UNIT_REGISTRY_PARTIAL_SOURCE_COVERAGE"
else:
    classification="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "partition_count":len(recs),"baseline_success_count":baseline,"enriched_success_count":enriched,
 "unique_asset_bank_count":len(asset),"unique_liab_bank_count":len(liab),"registry_bank_count":len(registry),
 "unmapped_asset_bank_count":len(unmapped_asset),"unmapped_asset_banks":unmapped_asset,
 "bank_registry":[{"bank":b,"mint":p[0],"decimals":p[1]} for b,p in sorted(registry.items())],
 "error_count":len(errors),"errors":errors,"amount_fields_requested":False,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
             "token_amounts":False,"token_balance_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
             "account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="MARGINFI_BANK_UNIT_REGISTRY_BLOCKED_FAIL_CLOSED":raise SystemExit(2)

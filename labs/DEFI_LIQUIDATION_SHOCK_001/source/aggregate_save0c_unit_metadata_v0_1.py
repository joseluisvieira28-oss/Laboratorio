#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(sys.argv[1])
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/SAVE0C_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json")
EXPECTED=66628;EXPECTED_PARTITIONS=37
recs=[]
for p in sorted(ROOT.rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("protocol")=="save0c" and str(r.get("classification","")).startswith("SAVE0C_UNIT_METADATA_PARTITION_"):
        recs.append(r)
errors=[];seen=set();unmapped={}
baseline=enriched=direct=mapped=missing=extra=banom=qanom=conflicts=0
for r in recs:
    pid=r.get("partition_id")
    if not pid or pid in seen:errors.append({"reason":"bad_or_duplicate_partition_id","partition_id":pid})
    seen.add(pid)
    if r.get("classification")=="SAVE0C_UNIT_METADATA_PARTITION_BLOCKED_FAIL_CLOSED":
        errors.append({"reason":"partition_blocked","partition_id":pid})
    baseline+=int(r.get("baseline_success_count") or 0);enriched+=int(r.get("enriched_success_count") or 0)
    direct+=int(r.get("direct_unit_complete_event_count") or 0);mapped+=int(r.get("collateral_underlying_mapped_event_count") or 0)
    missing+=int(r.get("missing_count") or 0);extra+=int(r.get("extra_count") or 0)
    banom+=int(r.get("baseline_anomaly_count") or 0);qanom+=int(r.get("query_anomaly_count") or 0);conflicts+=int(r.get("conflict_count") or 0)
    for x in r.get("unmapped_reserves") or []:
        unmapped[x["reserve"]]=unmapped.get(x["reserve"],0)+int(x.get("event_count") or 0)
if len(recs)!=EXPECTED_PARTITIONS:errors.append({"reason":"partition_count_mismatch","observed":len(recs),"expected":EXPECTED_PARTITIONS})
if baseline!=EXPECTED or enriched!=EXPECTED or direct!=EXPECTED:
    errors.append({"reason":"population_or_direct_unit_count_mismatch","baseline":baseline,"enriched":enriched,"direct":direct,"expected":EXPECTED})
if any((missing,extra,banom,qanom,conflicts)):
    errors.append({"reason":"nonzero_source_or_join_errors","missing":missing,"extra":extra,"baseline_anomaly":banom,"query_anomaly":qanom,"conflicts":conflicts})
if errors:classification="SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED"
elif mapped==EXPECTED:classification="SAVE0C_UNIT_METADATA_POPULATION_PASS"
else:classification="SAVE0C_UNIT_METADATA_PARTIAL_SOURCE_COVERAGE"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "partition_count":len(recs),"baseline_success_count":baseline,"enriched_success_count":enriched,
 "direct_unit_complete_event_count":direct,"collateral_underlying_mapped_event_count":mapped,
 "collateral_underlying_unmapped_event_count":EXPECTED-mapped,
 "unique_unmapped_reserve_count":len(unmapped),
 "unmapped_reserves":[{"reserve":r,"event_count":n} for r,n in sorted(unmapped.items(),key=lambda kv:(-kv[1],kv[0]))],
 "error_count":len(errors),"errors":errors,"amount_fields_requested":False,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
             "token_amounts":False,"token_balance_amounts":False,"protected_market_outcomes_2025_2026":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
             "account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="SAVE0C_UNIT_METADATA_BLOCKED_FAIL_CLOSED":raise SystemExit(2)

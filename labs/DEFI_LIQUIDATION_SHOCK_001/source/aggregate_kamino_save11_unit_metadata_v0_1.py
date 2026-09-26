#!/usr/bin/env python3
import json,sys
from pathlib import Path
ROOT=Path(sys.argv[1])
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.1.json")
EXPECTED={"kamino":60699,"save11":13300}
EXPECTED_PARTITIONS={"kamino":14,"save11":6}
recs=[]
for p in sorted(ROOT.rglob("*.json")):
    try:r=json.loads(p.read_text())
    except Exception:continue
    if r.get("protocol") in EXPECTED and str(r.get("classification","")).startswith("KAMINO_SAVE11_UNIT_METADATA_PARTITION_"):
        recs.append(r)
errors=[];protocols={};seen_ids=set();registry={}
for protocol in EXPECTED:
    items=[r for r in recs if r["protocol"]==protocol]
    for r in items:
        pid=r.get("partition_id")
        if not pid or pid in seen_ids:errors.append({"reason":"bad_or_duplicate_partition_id","partition_id":pid})
        seen_ids.add(pid)
    baseline=sum(int(r.get("baseline_success_count") or 0) for r in items)
    enriched=sum(int(r.get("enriched_success_count") or 0) for r in items)
    unit=sum(int(r.get("unit_complete_event_count") or 0) for r in items)
    bad=sum(int(r.get("missing_count") or 0)+int(r.get("extra_count") or 0)+
            int(r.get("baseline_anomaly_count") or 0)+int(r.get("query_anomaly_count") or 0)+
            int(r.get("unit_conflict_count") or 0) for r in items)
    part_pass=sum(1 for r in items if r.get("classification")=="KAMINO_SAVE11_UNIT_METADATA_PARTITION_PASS")
    if len(items)!=EXPECTED_PARTITIONS[protocol]:
        errors.append({"reason":"partition_count_mismatch","protocol":protocol,"observed":len(items),"expected":EXPECTED_PARTITIONS[protocol]})
    if part_pass!=EXPECTED_PARTITIONS[protocol]:
        errors.append({"reason":"partition_pass_count_mismatch","protocol":protocol,"observed":part_pass,"expected":EXPECTED_PARTITIONS[protocol]})
    if baseline!=EXPECTED[protocol] or enriched!=EXPECTED[protocol] or unit!=EXPECTED[protocol]:
        errors.append({"reason":"population_or_unit_count_mismatch","protocol":protocol,
                       "baseline":baseline,"enriched":enriched,"unit_complete":unit,"expected":EXPECTED[protocol]})
    if bad:
        errors.append({"reason":"nonzero_partition_errors","protocol":protocol,"count":bad})
    protocols[protocol]={"partition_count":len(items),"partition_pass_count":part_pass,
                         "baseline_success_count":baseline,"enriched_success_count":enriched,
                         "unit_complete_event_count":unit,"expected_success_count":EXPECTED[protocol]}
    for r in items:
        for e in r.get("event_units") or []:
            for role in ("debt_underlying","collateral_token","collateral_underlying"):
                u=e.get(role) or {}
                k=(protocol,role,u.get("mint"),u.get("decimals"))
                if k[2] is not None and k[3] is not None:registry[k]=registry.get(k,0)+1
classification="KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS" if not errors else "KAMINO_SAVE11_UNIT_METADATA_POPULATION_BLOCKED_FAIL_CLOSED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "partition_receipt_count":len(recs),"protocols":protocols,"error_count":len(errors),"errors":errors,
 "unit_registry":[{"protocol":k[0],"role":k[1],"mint":k[2],"decimals":k[3],"event_observation_count":v}
                  for k,v in sorted(registry.items())],
 "amount_fields_requested":False,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"token_amounts":False,"token_balance_amounts":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS":raise SystemExit(2)

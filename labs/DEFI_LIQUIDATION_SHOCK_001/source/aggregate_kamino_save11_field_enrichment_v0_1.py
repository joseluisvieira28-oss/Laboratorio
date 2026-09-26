#!/usr/bin/env python3
import json, sys
from pathlib import Path

ROOT=Path(sys.argv[1])
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.1.json")
EXPECTED={"kamino":60699,"save11":13300}
EXPECTED_PARTITIONS={"kamino":14,"save11":6}

receipts=[]
for p in sorted(ROOT.rglob("*.json")):
    try:
        with p.open("r",encoding="utf-8") as fh:r=json.load(fh)
    except Exception:continue
    if r.get("classification") in ("FIELD_ENRICHMENT_PARTITION_PASS","FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED") and r.get("protocol") in EXPECTED:
        r["_file"]=str(p);receipts.append(r)

errors=[]; protocols={}; seen_ids=set()
for protocol in EXPECTED:
    items=[r for r in receipts if r["protocol"]==protocol]
    for r in items:
        pid=r.get("partition_id")
        if not pid: errors.append({"reason":"missing_partition_id","file":r.get("_file")})
        elif pid in seen_ids: errors.append({"reason":"duplicate_partition_id","partition_id":pid})
        seen_ids.add(pid)
    part_pass=sum(1 for r in items if r.get("classification")=="FIELD_ENRICHMENT_PARTITION_PASS")
    baseline=sum(int(r.get("baseline_success_count") or 0) for r in items)
    enriched=sum(int(r.get("enriched_success_count") or 0) for r in items)
    missing=sum(int(r.get("missing_count") or 0) for r in items)
    extra=sum(int(r.get("extra_count") or 0) for r in items)
    dup=sum(int(r.get("duplicate_count") or 0) for r in items)
    conflict=sum(int(r.get("semantic_conflict_count") or 0) for r in items)
    banom=sum(int(r.get("baseline_anomaly_count") or 0) for r in items)
    nonempty=sum(int(r.get("nonempty_accounts_count") or 0) for r in items)
    full=sum(int(r.get("full_instruction_data_count") or 0) for r in items)
    abi=sum(int(r.get("exact_abi_shape_count") or 0) for r in items)

    if len(items)!=EXPECTED_PARTITIONS[protocol]:
        errors.append({"reason":"partition_count_mismatch","protocol":protocol,"observed":len(items),"expected":EXPECTED_PARTITIONS[protocol]})
    if part_pass!=EXPECTED_PARTITIONS[protocol]:
        errors.append({"reason":"partition_pass_count_mismatch","protocol":protocol,"observed":part_pass,"expected":EXPECTED_PARTITIONS[protocol]})
    if baseline!=EXPECTED[protocol] or enriched!=EXPECTED[protocol]:
        errors.append({"reason":"population_count_mismatch","protocol":protocol,"baseline":baseline,"enriched":enriched,"expected":EXPECTED[protocol]})
    if any((missing,extra,dup,conflict,banom)):
        errors.append({"reason":"join_or_semantic_nonzero","protocol":protocol,"missing":missing,"extra":extra,"duplicate":dup,"conflicts":conflict,"baseline_anomaly":banom})
    if nonempty!=EXPECTED[protocol] or full!=EXPECTED[protocol] or abi!=EXPECTED[protocol]:
        errors.append({"reason":"abi_or_field_coverage_incomplete","protocol":protocol,"nonempty_accounts":nonempty,
                       "full_instruction_data":full,"exact_abi_shape":abi,"expected":EXPECTED[protocol]})

    protocols[protocol]={"partition_count":len(items),"partition_pass_count":part_pass,
      "baseline_success_count":baseline,"enriched_success_count":enriched,"expected_success_count":EXPECTED[protocol],
      "missing_count":missing,"extra_count":extra,"duplicate_count":dup,"semantic_conflict_count":conflict,
      "baseline_anomaly_count":banom,"nonempty_accounts_count":nonempty,"full_instruction_data_count":full,
      "exact_abi_shape_count":abi}

receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS" if not errors else "KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_BLOCKED_FAIL_CLOSED",
 "partition_receipt_count":len(receipts),"protocols":protocols,"error_count":len(errors),"errors":errors,
 "semantic_scope":"account roles + ABI shape + instruction schema only; no numeric argument values, balances, decimals, prices or outcomes",
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,"economic_outcomes":False,
             "token_balances":False,"token_amounts":False,"token_decimals":False,
             "protected_market_outcomes_2025_2026":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"paid_source":False,"account_creation":False,"post_outcome_tuning":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if receipt["classification"]!="KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS":raise SystemExit(2)

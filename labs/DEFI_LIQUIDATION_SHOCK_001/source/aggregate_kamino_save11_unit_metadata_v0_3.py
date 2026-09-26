#!/usr/bin/env python3
import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--original",required=True)
ap.add_argument("--recovery",required=True)
args=ap.parse_args()

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_UNIT_METADATA_POPULATION_RECEIPT_V0.3.json")
EXPECTED={"kamino":60699,"save11":13300}
ORIG_K=["kamino-202311","kamino-202312","kamino-202401","kamino-202402"]
REC_K=[f"kamino-2024{m:02d}" for m in range(3,13)]
SAVE=[f"save11-2024{m:02d}" for m in range(7,13)]

def scan(root):
    out={}
    for p in sorted(Path(root).rglob("*.json")):
        try:r=json.loads(p.read_text())
        except Exception:continue
        if r.get("protocol") not in EXPECTED:continue
        if not str(r.get("classification","")).startswith("KAMINO_SAVE11_UNIT_METADATA_PARTITION_"):continue
        pid=r.get("partition_id")
        if pid:out.setdefault(pid,[]).append((p,r))
    return out

orig=scan(args.original);rec=scan(args.recovery)
errors=[];selected={};superseded=[]
for pid in ORIG_K+SAVE:
    hits=orig.get(pid,[])
    if len(hits)!=1:
        errors.append({"reason":"original_partition_receipt_count","partition_id":pid,"observed":len(hits),"expected":1})
        continue
    selected[pid]={"source":"V0.1_ORIGINAL","file":str(hits[0][0]),"receipt":hits[0][1]}
for pid in REC_K:
    hits=rec.get(pid,[])
    if len(hits)!=1:
        errors.append({"reason":"v03_recovery_partition_receipt_count","partition_id":pid,"observed":len(hits),"expected":1})
        continue
    selected[pid]={"source":"V0.3_CURRENT_KAMINO_UNIT_AUTHORITY","file":str(hits[0][0]),"receipt":hits[0][1]}
    for p,r in orig.get(pid,[]):
        superseded.append({"partition_id":pid,"file":str(p),"classification":r.get("classification")})

protocols={};registry={};resolution_counts={"TOKEN_BALANCE_PAIR_DIRECT":0,"SINGLE_TOKEN_BALANCE_PLUS_SUCCESSFUL_TRANSFER_IDENTITY":0}
for protocol,expected_n,expected_parts in [("kamino",60699,14),("save11",13300,6)]:
    items=[x for x in selected.values() if x["receipt"].get("protocol")==protocol]
    baseline=sum(int(x["receipt"].get("baseline_success_count") or 0) for x in items)
    enriched=sum(int(x["receipt"].get("enriched_success_count") or 0) for x in items)
    unit=sum(int(x["receipt"].get("unit_complete_event_count") or 0) for x in items)
    missing=sum(int(x["receipt"].get("missing_count") or 0) for x in items)
    extra=sum(int(x["receipt"].get("extra_count") or 0) for x in items)
    banom=sum(int(x["receipt"].get("baseline_anomaly_count") or 0) for x in items)
    qanom=sum(int(x["receipt"].get("query_anomaly_count") or 0) for x in items)
    conflicts=sum(int(x["receipt"].get("unit_conflict_count") or 0) for x in items)
    ppass=sum(1 for x in items if x["receipt"].get("classification")=="KAMINO_SAVE11_UNIT_METADATA_PARTITION_PASS")

    if len(items)!=expected_parts:
        errors.append({"reason":"selected_partition_count_mismatch","protocol":protocol,"observed":len(items),"expected":expected_parts})
    if ppass!=expected_parts:
        errors.append({"reason":"selected_partition_pass_count_mismatch","protocol":protocol,"observed":ppass,"expected":expected_parts})
    if baseline!=expected_n or enriched!=expected_n or unit!=expected_n:
        errors.append({"reason":"population_or_unit_count_mismatch","protocol":protocol,"baseline":baseline,
                       "enriched":enriched,"unit_complete":unit,"expected":expected_n})
    if any((missing,extra,banom,qanom,conflicts)):
        errors.append({"reason":"nonzero_selected_partition_errors","protocol":protocol,"missing":missing,"extra":extra,
                       "baseline_anomaly":banom,"query_anomaly":qanom,"unit_conflict":conflicts})

    protocols[protocol]={"partition_count":len(items),"partition_pass_count":ppass,
                         "baseline_success_count":baseline,"enriched_success_count":enriched,
                         "unit_complete_event_count":unit,"expected_success_count":expected_n,
                         "missing_count":missing,"extra_count":extra,"baseline_anomaly_count":banom,
                         "query_anomaly_count":qanom,"unit_conflict_count":conflicts}

    for x in items:
        r=x["receipt"]
        resolution_counts["TOKEN_BALANCE_PAIR_DIRECT"] += int(r.get("direct_pair_resolution_role_count") or 0)
        resolution_counts["SINGLE_TOKEN_BALANCE_PLUS_SUCCESSFUL_TRANSFER_IDENTITY"] += int(r.get("transfer_identity_fallback_role_count") or 0)
        for e in r.get("event_units") or []:
            for role in ("debt_underlying","collateral_token","collateral_underlying"):
                u=e.get(role) or {}
                mint=u.get("mint");dec=u.get("decimals")
                if mint is not None and dec is not None:
                    k=(protocol,role,mint,int(dec))
                    registry[k]=registry.get(k,0)+1

classification="KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS" if not errors else "KAMINO_SAVE11_UNIT_METADATA_POPULATION_BLOCKED_FAIL_CLOSED"
receipt={"schema_version":"0.3","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "precedence_authority":"KAMINO_UNIT_METADATA_RECOVERY_PRECEDENCE_ADDENDUM_V0.3.md",
 "source_authorities":["KAMINO_HISTORICAL_ACCOUNT_LAYOUT_ADDENDUM_V0.2.md",
                       "KAMINO_UNIT_METADATA_TRANSFER_IDENTITY_ADDENDUM_V0.2.md",
                       "KAMINO_TEMPORAL_DECODER_AND_UNIT_AUTHORITY_ADDENDUM_V0.3.md"],
 "protocols":protocols,"selected_partition_count":len(selected),
 "selected_receipts":[{"partition_id":pid,"source":x["source"],"file":x["file"],
                       "classification":x["receipt"].get("classification")} for pid,x in sorted(selected.items())],
 "superseded_original_receipts":superseded,
 "resolution_counts":resolution_counts,
 "unit_registry":[{"protocol":k[0],"role":k[1],"mint":k[2],"decimals":k[3],"event_observation_count":v}
                  for k,v in sorted(registry.items())],
 "error_count":len(errors),"errors":errors,"amount_fields_requested":False,
 "firewall":{"prices":False,"returns":False,"pnl":False,"economic_outcomes":False,
             "token_amounts":False,"token_balance_amounts":False,
             "protected_market_outcomes_2025_2026":False,"post_outcome_tuning":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "paid_source":False,"account_creation":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="KAMINO_SAVE11_UNIT_METADATA_POPULATION_PASS":raise SystemExit(2)

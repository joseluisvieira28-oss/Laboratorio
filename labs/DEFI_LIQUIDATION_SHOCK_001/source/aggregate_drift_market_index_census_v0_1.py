#!/usr/bin/env python3
import argparse,json
from pathlib import Path

EXPECTED={
 "liquidate_perp":1953488,
 "liquidate_spot":619719,
 "liquidate_borrow_for_perp_pnl":3370,
 "liquidate_perp_pnl_for_deposit":79343
}
EXPECTED_TOTAL=sum(EXPECTED.values())
EXPECTED_PARTITIONS=86
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/DRIFT_MARKET_INDEX_CENSUS_RECEIPT_V0.1.json")

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
args=ap.parse_args()
root=Path(args.root)

agg=None
parts=[]
for p in root.rglob("*.json"):
    try:o=json.loads(p.read_text())
    except Exception:continue
    if o.get("classification")=="DRIFT_FIELD_ENRICHMENT_POPULATION_PASS":
        agg=o
    elif o.get("protocol")=="drift" and o.get("classification") in ("FIELD_ENRICHMENT_PARTITION_PASS","FIELD_ENRICHMENT_PARTITION_FAIL_CLOSED"):
        parts.append(o)

errors=[]
if agg is None:
    errors.append({"reason":"missing_population_enrichment_pass_receipt"})
else:
    if agg.get("classification")!="DRIFT_FIELD_ENRICHMENT_POPULATION_PASS":
        errors.append({"reason":"population_enrichment_not_pass","classification":agg.get("classification")})
    if int(agg.get("enriched_success_count") or 0)!=EXPECTED_TOTAL:
        errors.append({"reason":"population_enrichment_total_mismatch","observed":agg.get("enriched_success_count"),"expected":EXPECTED_TOTAL})

if len(parts)!=EXPECTED_PARTITIONS:
    errors.append({"reason":"partition_count_mismatch","observed":len(parts),"expected":EXPECTED_PARTITIONS})

class_counts={k:0 for k in EXPECTED}
perp_counts={}
spot_counts={}
bad_rows=[]
seen_partitions=set()

def bump(d,k,role,cls):
    x=d.setdefault(str(k),{"total_observations":0,"roles":{},"classes":{}})
    x["total_observations"]+=1
    x["roles"][role]=x["roles"].get(role,0)+1
    x["classes"][cls]=x["classes"].get(cls,0)+1

for r in parts:
    pid=r.get("partition_id")
    if not pid or pid in seen_partitions:
        errors.append({"reason":"bad_or_duplicate_partition_id","partition_id":pid})
    seen_partitions.add(pid)
    if r.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":
        errors.append({"reason":"partition_not_pass","partition_id":pid,"classification":r.get("classification")})
        continue
    rows=r.get("enriched_rows") or []
    if len(rows)!=int(r.get("enriched_success_count") or -1):
        errors.append({"reason":"partition_row_count_mismatch","partition_id":pid,"rows":len(rows),"declared":r.get("enriched_success_count")})
    for e in rows:
        cls=e.get("class") or e.get("instruction_class")
        mi=e.get("market_identity")
        if cls not in EXPECTED or not isinstance(mi,dict):
            bad_rows.append({"partition_id":pid,"signature":e.get("signature"),"reason":"missing_class_or_market_identity","class":cls})
            continue
        class_counts[cls]+=1
        try:
            if cls=="liquidate_perp":
                v=int(mi["perp_market_index"]); bump(perp_counts,v,"perp_market_index",cls)
            elif cls=="liquidate_spot":
                a=int(mi["asset_spot_market_index"]); b=int(mi["liability_spot_market_index"])
                bump(spot_counts,a,"asset_spot_market_index",cls); bump(spot_counts,b,"liability_spot_market_index",cls)
            elif cls in ("liquidate_borrow_for_perp_pnl","liquidate_perp_pnl_for_deposit"):
                pidx=int(mi["perp_market_index"]); sidx=int(mi["spot_market_index"])
                bump(perp_counts,pidx,"perp_market_index",cls); bump(spot_counts,sidx,"spot_market_index",cls)
        except Exception:
            bad_rows.append({"partition_id":pid,"signature":e.get("signature"),"reason":"market_index_decode_missing","class":cls,"market_identity":mi})

for cls,n in EXPECTED.items():
    if class_counts[cls]!=n:
        errors.append({"reason":"class_count_mismatch","class":cls,"observed":class_counts[cls],"expected":n})
if sum(class_counts.values())!=EXPECTED_TOTAL:
    errors.append({"reason":"total_event_count_mismatch","observed":sum(class_counts.values()),"expected":EXPECTED_TOTAL})
if bad_rows:
    errors.append({"reason":"bad_market_identity_rows","count":len(bad_rows)})

classification="DRIFT_MARKET_INDEX_CENSUS_POPULATION_PASS" if not errors else "DRIFT_MARKET_INDEX_CENSUS_BLOCKED_FAIL_CLOSED"
receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "population_enrichment_classification":agg.get("classification") if agg else None,
 "partition_count":len(parts),"event_count":sum(class_counts.values()),"expected_event_count":EXPECTED_TOTAL,
 "class_counts":class_counts,
 "perp_market_indexes":[{"market_index":int(k),**v} for k,v in sorted(perp_counts.items(),key=lambda kv:int(kv[0]))],
 "spot_market_indexes":[{"market_index":int(k),**v} for k,v in sorted(spot_counts.items(),key=lambda kv:int(kv[0]))],
 "unique_perp_market_index_count":len(perp_counts),"unique_spot_market_index_count":len(spot_counts),
 "bad_market_identity_row_count":len(bad_rows),"bad_market_identity_examples":bad_rows[:100],
 "error_count":len(errors),"errors":errors,
 "firewall":{"prices":False,"usd_notional":False,"returns":False,"pnl":False,"direction":False,
             "economic_outcomes":False,"token_amounts":False,"requested_max_amount_values":False,
             "limit_price_values":False,"protected_market_outcomes_2025_2026":False,"live_trading":False,
             "orders":False,"wallets":False,"exchange_mutation":False,"paid_source":False,
             "account_creation":False,"post_outcome_tuning":False,"merge_main":False}
}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="DRIFT_MARKET_INDEX_CENSUS_POPULATION_PASS":raise SystemExit(2)

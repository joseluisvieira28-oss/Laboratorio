#!/usr/bin/env python3
import argparse,json
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--original",required=True)
ap.add_argument("--recovery",required=True)
args=ap.parse_args()
OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_RECEIPT_V0.2.json")
EXPECTED={"kamino":60699,"save11":13300}
ORIG_K=[f"kamino-{y}{m:02d}" for y,m in [(2023,11),(2023,12),(2024,1),(2024,2),(2024,3),(2024,4),(2024,5)]]
REC_K=[f"kamino-2024{m:02d}" for m in range(6,13)]
SAVE=[f"save11-2024{m:02d}" for m in range(7,13)]

def scan(root):
    out={}
    for p in sorted(Path(root).rglob("*.json")):
        try:r=json.loads(p.read_text())
        except Exception:continue
        if r.get("protocol") not in EXPECTED or not str(r.get("classification","")).startswith("FIELD_ENRICHMENT_PARTITION_"):continue
        pid=r.get("partition_id")
        if not pid:continue
        out.setdefault(pid,[]).append((p,r))
    return out

orig=scan(args.original);rec=scan(args.recovery)
errors=[];selected={};superseded=[]
for pid in ORIG_K+SAVE:
    hits=orig.get(pid,[])
    if len(hits)!=1:
        errors.append({"reason":"original_partition_receipt_count","partition_id":pid,"observed":len(hits),"expected":1});continue
    selected[pid]={"source":"V0.1_ORIGINAL","file":str(hits[0][0]),"receipt":hits[0][1]}
for pid in REC_K:
    hits=rec.get(pid,[])
    if len(hits)!=1:
        errors.append({"reason":"recovery_partition_receipt_count","partition_id":pid,"observed":len(hits),"expected":1});continue
    selected[pid]={"source":"V0.2_HISTORICAL_LAYOUT_RECOVERY","file":str(hits[0][0]),"receipt":hits[0][1]}
    for p,r in orig.get(pid,[]):
        superseded.append({"partition_id":pid,"file":str(p),"classification":r.get("classification")})

protocols={}
for protocol,expected_n,expected_parts in [("kamino",60699,14),("save11",13300,6)]:
    items=[x for pid,x in selected.items() if x["receipt"].get("protocol")==protocol]
    baseline=sum(int(x["receipt"].get("baseline_success_count") or 0) for x in items)
    enriched=sum(int(x["receipt"].get("enriched_success_count") or 0) for x in items)
    missing=sum(int(x["receipt"].get("missing_count") or 0) for x in items)
    extra=sum(int(x["receipt"].get("extra_count") or 0) for x in items)
    dup=sum(int(x["receipt"].get("duplicate_count") or 0) for x in items)
    conflict=sum(int(x["receipt"].get("semantic_conflict_count") or 0) for x in items)
    banom=sum(int(x["receipt"].get("baseline_anomaly_count") or 0) for x in items)
    nonempty=sum(int(x["receipt"].get("nonempty_accounts_count") or 0) for x in items)
    full=sum(int(x["receipt"].get("full_instruction_data_count") or 0) for x in items)
    abi=sum(int(x["receipt"].get("exact_abi_shape_count") or 0) for x in items)
    ppass=sum(1 for x in items if x["receipt"].get("classification")=="FIELD_ENRICHMENT_PARTITION_PASS")
    if len(items)!=expected_parts:errors.append({"reason":"selected_partition_count_mismatch","protocol":protocol,"observed":len(items),"expected":expected_parts})
    if ppass!=expected_parts:errors.append({"reason":"selected_partition_pass_count_mismatch","protocol":protocol,"observed":ppass,"expected":expected_parts})
    if baseline!=expected_n or enriched!=expected_n:errors.append({"reason":"population_count_mismatch","protocol":protocol,"baseline":baseline,"enriched":enriched,"expected":expected_n})
    if any((missing,extra,dup,conflict,banom)):errors.append({"reason":"join_or_semantic_nonzero","protocol":protocol,"missing":missing,"extra":extra,"duplicate":dup,"conflict":conflict,"baseline_anomaly":banom})
    if nonempty!=expected_n or full!=expected_n or abi!=expected_n:errors.append({"reason":"field_coverage_incomplete","protocol":protocol,"nonempty":nonempty,"full_data":full,"abi":abi,"expected":expected_n})
    protocols[protocol]={"partition_count":len(items),"partition_pass_count":ppass,"baseline_success_count":baseline,
                         "enriched_success_count":enriched,"expected_success_count":expected_n,
                         "missing_count":missing,"extra_count":extra,"duplicate_count":dup,
                         "semantic_conflict_count":conflict,"baseline_anomaly_count":banom,
                         "nonempty_accounts_count":nonempty,"full_instruction_data_count":full,
                         "exact_abi_shape_count":abi}

classification="KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS" if not errors else "KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_BLOCKED_FAIL_CLOSED"
receipt={"schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "precedence_authority":"KAMINO_LAYOUT_RECOVERY_PRECEDENCE_ADDENDUM_V0.2.md",
 "protocols":protocols,"selected_partition_count":len(selected),
 "selected_receipts":[{"partition_id":pid,"source":x["source"],"file":x["file"],
                       "classification":x["receipt"].get("classification")} for pid,x in sorted(selected.items())],
 "superseded_original_receipts":superseded,
 "error_count":len(errors),"errors":errors,
 "firewall":{"prices":False,"returns":False,"pnl":False,"economic_outcomes":False,
             "token_amounts":False,"protected_market_outcomes_2025_2026":False,
             "post_outcome_tuning":False,"live_trading":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="KAMINO_SAVE11_FIELD_ENRICHMENT_POPULATION_PASS":raise SystemExit(2)

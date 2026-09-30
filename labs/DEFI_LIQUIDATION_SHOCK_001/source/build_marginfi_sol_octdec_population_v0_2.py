#!/usr/bin/env python3
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

SOL="So11111111111111111111111111111111111111112"
EXPECTED={
 "202410":{"partition_id":"marginfi-202410","start":"2024-10-01T00:00:00Z","end":"2024-11-01T00:00:00Z","count":1432},
 "202411":{"partition_id":"marginfi-202411","start":"2024-11-01T00:00:00Z","end":"2024-12-01T00:00:00Z","count":10141},
 "202412":{"partition_id":"marginfi-202412","start":"2024-12-01T00:00:00Z","end":"2025-01-01T00:00:00Z","count":4880},
}
ap=argparse.ArgumentParser()
ap.add_argument("--field-oct-root",required=True)
ap.add_argument("--field-nov-root",required=True)
ap.add_argument("--field-dec-root",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_RECEIPT_V0.2.json"
ROWS=OUT/"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_V0.2.ndjson"

def addrkey(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])

def find_json(root,pred):
    hits=[]
    for p in Path(root).rglob("*.json"):
        try:o=json.loads(p.read_text())
        except Exception:continue
        if pred(o):hits.append((p,o))
    return hits

roots={"202410":args.field_oct_root,"202411":args.field_nov_root,"202412":args.field_dec_root}
errors=[];fields={}
for m,root in roots.items():
    exp=EXPECTED[m]
    h=find_json(root,lambda o:o.get("partition_id")==exp["partition_id"])
    if len(h)!=1:
        errors.append(f"{m}:field_receipt_count={len(h)}");continue
    o=h[0][1];fields[m]=o
    if o.get("classification")!="FIELD_ENRICHMENT_PARTITION_PASS":errors.append(f"{m}:field_not_pass")
    if o.get("protocol")!="marginfi" or o.get("instruction_class")!="lending_account_liquidate":errors.append(f"{m}:field_identity_mismatch")
    if o.get("effective_start")!=exp["start"] or o.get("effective_end")!=exp["end"]:errors.append(f"{m}:window_mismatch")
    if int(o.get("baseline_success_count",-1))!=exp["count"] or int(o.get("enriched_success_count",-1))!=exp["count"]:
        errors.append(f"{m}:population_count_mismatch")
    for k in ("missing_count","extra_count","duplicate_count","semantic_conflict_count","baseline_anomaly_count"):
        if int(o.get(k,-1))!=0:errors.append(f"{m}:{k}_nonzero")

bh=find_json(args.bank_registry_root,lambda o:o.get("classification")=="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS")
if len(bh)!=1:errors.append(f"bank_receipt_count={len(bh)}")
registry={}
if len(bh)==1:registry={x["bank"]:x["mint"] for x in bh[0][1].get("bank_registry") or []}
solbanks={b for b,m in registry.items() if m==SOL}
if not solbanks:errors.append("no_sol_bank_mapping")

population=[];month_counts=Counter();missing_liab=[]
if not errors:
    for m in ("202410","202411","202412"):
        for r in fields[m].get("enriched_rows") or []:
            sem=r.get("semantic_accounts") or {}
            if sem.get("asset_bank") not in solbanks:continue
            liab_bank=sem.get("liab_bank");liab_mint=registry.get(liab_bank)
            if not liab_mint or liab_mint==SOL:
                missing_liab.append({"month":m,"signature":r.get("signature"),"instructionAddress":r.get("instructionAddress"),"liab_bank":liab_bank})
                continue
            row={
              "signature":r["signature"],"slot":r["slot"],"timestamp":r["timestamp"],
              "transactionIndex":r.get("transactionIndex"),"instructionAddress":r["instructionAddress"],
              "asset_bank":sem.get("asset_bank"),"liab_bank":liab_bank,
              "asset_mint":SOL,"liab_mint":liab_mint
            }
            population.append(row);month_counts[m]+=1
if missing_liab:errors.append(f"missing_or_invalid_liability_mapping:{len(missing_liab)}")

population.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
ids=[ident(r) for r in population]
dup=len(ids)-len(set(ids))
if dup:errors.append(f"population_duplicates:{dup}")
classification="MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_PASS" if not errors and population else "MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_BLOCKED"

with ROWS.open("w") as fh:
    for r in population:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
receipt={
 "schema_version":"0.2","lab_id":"DLS-MARGINFI-ORCA-EXTREME-FLOW-REBOUND-002",
 "classification":classification,
 "authority":"MARGINFI_ORCA_EXTREME_FLOW_REBOUND_V0_2_PRE_OUTCOME_FREEZE_2026-09-30.md",
 "field_partition_counts":{m:EXPECTED[m]["count"] for m in EXPECTED},
 "sol_bank_count":len(solbanks),"sol_population_count":len(population),
 "month_sol_population_counts":dict(sorted(month_counts.items())),
 "duplicate_identity_count":dup,"error_count":len(errors),"errors":errors,
 "missing_liability_mapping_examples":missing_liab[:100],
 "rows_file":str(ROWS),"rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
             "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,
             "merge_main":False,"post_outcome_tuning":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification!="MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_PASS":raise SystemExit(2)

#!/usr/bin/env python3
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

SOL="So11111111111111111111111111111111111111112"
SC=16

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--field-root",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_JULSEP_SOURCE_202408_RECEIPT_V0.1.json"
ROWS=OUT/"MARGINFI_SOL_JULSEP_SOURCE_202408_ROWS_V0.1.ndjson"
POP=OUT/"MARGINFI_SOL_JULSEP_POPULATION_202408_V0.1.ndjson"

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(x):return x["signature"]+"|"+addrkey(x["instructionAddress"])
def load_nd(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def find_json(root,pred):
    hits=[]
    for p in Path(root).rglob("*.json"):
        try:o=json.loads(p.read_text())
        except Exception:continue
        if pred(o):hits.append((p,o))
    return hits

errors=[]
fh=find_json(args.field_root,lambda o:o.get("partition_id")=="marginfi-202408")
bh=find_json(args.bank_registry_root,lambda o:o.get("classification")=="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS")
if len(fh)!=1:errors.append(f"field_hit_count:{len(fh)}")
if len(bh)!=1:errors.append(f"bank_hit_count:{len(bh)}")
if errors:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_SOL_JULSEP_SOURCE_MONTH_BLOCKED","errors":errors},indent=2)+"\n")
    raise SystemExit(2)
field=fh[0][1];bank=bh[0][1]
for k,v in [("classification","FIELD_ENRICHMENT_PARTITION_PASS"),("protocol","marginfi"),("instruction_class","lending_account_liquidate")]:
    if field.get(k)!=v:errors.append(f"field_{k}_mismatch")
if field.get("effective_start")!="2024-08-01T00:00:00Z" or field.get("effective_end")!="2024-09-01T00:00:00Z":
    errors.append("field_window_mismatch")
if int(field.get("baseline_success_count",-1))!=13056 or int(field.get("enriched_success_count",-1))!=13056:
    errors.append("field_count_mismatch")
for k in ("missing_count","extra_count","duplicate_count","semantic_conflict_count","baseline_anomaly_count"):
    if int(field.get(k,-1))!=0:errors.append(k+"_nonzero")
registry={x["bank"]:x["mint"] for x in bank.get("bank_registry") or []}
solbanks={b for b,m in registry.items() if m==SOL}
canonical=[]
for r in field.get("enriched_rows") or []:
    sem=r.get("semantic_accounts") or {}
    if sem.get("asset_bank") in solbanks:
        canonical.append({
          "signature":r["signature"],"slot":r["slot"],"timestamp":r["timestamp"],
          "transactionIndex":r.get("transactionIndex"),"instructionAddress":r["instructionAddress"],
          "asset_bank":sem.get("asset_bank"),"liab_bank":sem.get("liab_bank"),
          "asset_mint":SOL,"liab_mint":registry.get(sem.get("liab_bank"))
        })
canonical_ids={ident(x) for x in canonical}
if len(canonical_ids)!=len(canonical):errors.append("canonical_population_duplicate")
if len(canonical)!=7677:errors.append(f"canonical_sol_count:{len(canonical)}")

receipts=[];pop=[];rows=[]
for si in range(SC):
    rh=sorted(ROOT.rglob(f"MARGINFI_SOL_AUGUST_SOURCE_SHARD_{si:02d}_RECEIPT_V0.1.json"))
    ph=sorted(ROOT.rglob(f"MARGINFI_SOL_AUGUST_SOURCE_SHARD_{si:02d}_POPULATION_V0.1.ndjson"))
    wh=sorted(ROOT.rglob(f"MARGINFI_SOL_AUGUST_SOURCE_SHARD_{si:02d}_ROWS_V0.1.ndjson"))
    if len(rh)!=1 or len(ph)!=1 or len(wh)!=1:
        errors.append(f"shard_{si:02d}:file_count:{len(rh)}/{len(ph)}/{len(wh)}");continue
    rr=json.loads(rh[0].read_text());receipts.append(rr)
    if rr.get("classification")!="MARGINFI_SOL_AUGUST_SOURCE_SHARD_COMPLETE":errors.append(f"shard_{si:02d}:not_complete")
    if int(rr.get("shard_index",-1))!=si or int(rr.get("shard_count",-1))!=SC:errors.append(f"shard_{si:02d}:identity_mismatch")
    if int(rr.get("canonical_sol_population_count",-1))!=7677:errors.append(f"shard_{si:02d}:canonical_count_mismatch")
    p=load_nd(ph[0]);w=load_nd(wh[0])
    if len(p)!=int(rr.get("sol_population_count",-1)):errors.append(f"shard_{si:02d}:population_count_mismatch")
    if len(w)!=int(rr.get("route_member_count",-1)):errors.append(f"shard_{si:02d}:route_count_mismatch")
    pop.extend(p);rows.extend(w)

pids=[ident(x) for x in pop];rids=[ident(x) for x in rows]
pdup=len(pids)-len(set(pids));rdup=len(rids)-len(set(rids))
if len(receipts)!=SC:errors.append(f"receipt_count:{len(receipts)}")
if pdup:errors.append(f"population_duplicates:{pdup}")
if rdup:errors.append(f"route_duplicates:{rdup}")
if set(pids)!=canonical_ids:
    errors.append(f"canonical_union_mismatch:missing={len(canonical_ids-set(pids))}:extra={len(set(pids)-canonical_ids)}")
if not set(rids).issubset(set(pids)):errors.append("route_not_subset_population")

I=sum(1 for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE")
D=sum(1 for r in rows if r.get("classification")=="DIRECTION_PROVEN")
A=sum(1 for r in rows if r.get("classification")=="DIRECTION_AMBIGUOUS")
C=sum(1 for r in rows if r.get("classification")=="CONTRADICTION")
complete=len(rows)-I
source_complete_rate=complete/len(rows) if rows else 0.0
direction_rate=D/complete if complete else 0.0

classification="MARGINFI_SOL_JULSEP_SOURCE_MONTH_BLOCKED" if errors else "MARGINFI_SOL_JULSEP_SOURCE_MONTH_COMPLETE"

pop.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
with POP.open("w") as fh:
    for r in pop:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

rec={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "month":"202408","authority":"MARGINFI_SOL_EXTREME_FLOW_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md",
 "transport_authority":"MARGINFI_SOL_AUGUST_SOURCE_HASH_SHARDING_FALLBACK_V0.1.md",
 "field_partition":{"partition_id":"marginfi-202408","classification":field.get("classification"),
                    "baseline_success_count":field.get("baseline_success_count"),
                    "enriched_success_count":field.get("enriched_success_count")},
 "shard_count":len(receipts),"sol_bank_count":len(solbanks),"sol_population_count":len(pop),
 "route_member_count":len(rows),"not_route_count":len(pop)-len(rows),
 "population_duplicate_count":pdup,"route_duplicate_count":rdup,
 "source_evidence_incomplete":I,"source_complete_count":complete,"source_complete_rate":source_complete_rate,
 "direction_proven":D,"direction_ambiguous":A,"contradictions":C,"direction_rate_complete":direction_rate,
 "error_count":len(errors),"errors":errors,
 "population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),
 "rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"pnl":False,"jul_sep_market_outcomes_opened":False,
             "oct_dec_2024_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}}
RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps(rec,indent=2,sort_keys=True))
if classification.endswith("_BLOCKED"):raise SystemExit(2)

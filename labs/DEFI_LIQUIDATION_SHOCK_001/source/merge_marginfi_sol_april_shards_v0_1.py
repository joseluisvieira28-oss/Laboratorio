#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path

SOL="So11111111111111111111111111111111111111112"
EXPECTED=[
 ("a1","2024-04-01T00:00:00Z","2024-04-13T00:00:00Z"),
 ("a2","2024-04-13T00:00:00Z","2024-04-14T00:00:00Z"),
 ("a3","2024-04-14T00:00:00Z","2024-04-16T00:00:00Z"),
 ("a4","2024-04-16T00:00:00Z","2024-04-17T00:00:00Z"),
 ("a5","2024-04-17T00:00:00Z","2024-05-01T00:00:00Z"),
]

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--field-root",required=True)
ap.add_argument("--bank-registry-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_APRJUN_SOURCE_202404_RECEIPT_V0.1.json"
ROWS=OUT/"MARGINFI_SOL_APRJUN_SOURCE_202404_ROWS_V0.1.ndjson"
POP=OUT/"MARGINFI_SOL_APRJUN_POPULATION_202404_V0.1.ndjson"

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

errors=[];pop=[];rows=[];receipts=[]
for sid,start,end in EXPECTED:
    rh=sorted(ROOT.rglob(f"MARGINFI_SOL_APRIL_SHARD_{sid}_RECEIPT_V0.1.json"))
    ph=sorted(ROOT.rglob(f"MARGINFI_SOL_APRIL_SHARD_{sid}_POPULATION_V0.1.ndjson"))
    wh=sorted(ROOT.rglob(f"MARGINFI_SOL_APRIL_SHARD_{sid}_ROWS_V0.1.ndjson"))
    if len(rh)!=1 or len(ph)!=1 or len(wh)!=1:
        errors.append(f"{sid}:file_count:{len(rh)}/{len(ph)}/{len(wh)}");continue
    r=json.loads(rh[0].read_text());receipts.append(r)
    if r.get("classification")!="MARGINFI_SOL_APRIL_SOURCE_SHARD_COMPLETE":errors.append(f"{sid}:not_complete")
    if r.get("shard_id")!=sid or r.get("start")!=start or r.get("end")!=end:errors.append(f"{sid}:interval_mismatch")
    p=load_nd(ph[0]);w=load_nd(wh[0])
    if len(p)!=int(r.get("sol_population_count",-1)):errors.append(f"{sid}:population_count_mismatch")
    if len(w)!=int(r.get("route_member_count",-1)):errors.append(f"{sid}:route_count_mismatch")
    pop.extend(p);rows.extend(w)

# Recompute exact canonical SOL population identity set from immutable April field partition.
field_hits=find_json(args.field_root,lambda o:o.get("partition_id")=="marginfi-202404" and o.get("classification")=="FIELD_ENRICHMENT_PARTITION_PASS")
bank_hits=find_json(args.bank_registry_root,lambda o:o.get("classification")=="MARGINFI_BANK_UNIT_REGISTRY_POPULATION_PASS")
if len(field_hits)!=1 or len(bank_hits)!=1:
    errors.append(f"authority_hit_count:{len(field_hits)}/{len(bank_hits)}")
    canonical_ids=set()
else:
    field=field_hits[0][1];bank=bank_hits[0][1]
    registry={x["bank"]:x["mint"] for x in bank.get("bank_registry") or []}
    solbanks={b for b,m in registry.items() if m==SOL}
    canonical_ids=set()
    for r in field.get("enriched_rows") or []:
        sem=r.get("semantic_accounts") or {}
        if sem.get("asset_bank") not in solbanks:continue
        canonical_ids.add(r["signature"]+"|"+addrkey(r["instructionAddress"]))

pids=[ident(x) for x in pop];rids=[ident(x) for x in rows]
pdup=len(pids)-len(set(pids));rdup=len(rids)-len(set(rids))
if pdup:errors.append(f"population_duplicates:{pdup}")
if rdup:errors.append(f"route_duplicates:{rdup}")
if not set(rids).issubset(set(pids)):errors.append("route_not_subset_population")
if set(pids)!=canonical_ids:
    errors.append(f"canonical_identity_mismatch:observed={len(set(pids))}:canonical={len(canonical_ids)}")
if len(receipts)!=5:errors.append(f"shard_receipt_count:{len(receipts)}")

I=sum(1 for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE")
D=sum(1 for r in rows if r.get("classification")=="DIRECTION_PROVEN")
A=sum(1 for r in rows if r.get("classification")=="DIRECTION_AMBIGUOUS")
C=sum(1 for r in rows if r.get("classification")=="CONTRADICTION")
complete=len(rows)-I

classification="MARGINFI_SOL_APRJUN_SOURCE_MONTH_COMPLETE" if not errors else "MARGINFI_SOL_APRJUN_SOURCE_MONTH_BLOCKED"

pop.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
with POP.open("w") as fh:
    for r in pop:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

rec={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "month":"202404","authority":"MARGINFI_SOL_FLOW_TURNOVER_IMPACT_V0_1_PRE_OUTCOME_FREEZE_2026-09-30.md",
 "transport_fallback":"MARGINFI_SOL_APRJUN_SOURCE_DAILY_TRANSPORT_FALLBACK_V0.1.md",
 "sol_population_count":len(pop),"canonical_sol_population_count":len(canonical_ids),
 "route_member_count":len(rows),"source_evidence_incomplete":I,"source_complete_count":complete,
 "source_complete_rate":complete/len(rows) if rows else 0.0,"direction_proven":D,"direction_ambiguous":A,
 "contradictions":C,"direction_rate_complete":D/complete if complete else 0.0,
 "population_duplicate_count":pdup,"route_duplicate_count":rdup,"error_count":len(errors),"errors":errors,
 "population_file":str(POP),"rows_file":str(ROWS),
 "population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),"rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"pnl":False,"apr_jun_market_outcomes_opened":False,
             "jul_sep_2024_opened":False,"market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}}
RECEIPT.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
print(json.dumps(rec,indent=2,sort_keys=True))
if classification!="MARGINFI_SOL_APRJUN_SOURCE_MONTH_COMPLETE":raise SystemExit(2)

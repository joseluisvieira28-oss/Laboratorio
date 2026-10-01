#!/usr/bin/env python3
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_RECEIPT_V0.1.json"
ROWS=OUT/"MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_ROWS_V0.1.ndjson"
POP=OUT/"MARGINFI_SOL_JULSEP_SOURCE_POPULATION_V0.1.ndjson"

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(x):return x["signature"]+"|"+addrkey(x["instructionAddress"])
def load_nd(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]

errors=[];receipts=[];pop=[];rows=[]
for m in ("202407","202408","202409"):
    rh=sorted(ROOT.rglob(f"MARGINFI_SOL_JULSEP_SOURCE_{m}_RECEIPT_V0.1.json"))
    ph=sorted(ROOT.rglob(f"MARGINFI_SOL_JULSEP_POPULATION_{m}_V0.1.ndjson"))
    wh=sorted(ROOT.rglob(f"MARGINFI_SOL_JULSEP_SOURCE_{m}_ROWS_V0.1.ndjson"))
    if len(rh)!=1 or len(ph)!=1 or len(wh)!=1:
        errors.append(f"{m}:file_count:{len(rh)}/{len(ph)}/{len(wh)}");continue
    r=json.loads(rh[0].read_text());receipts.append(r)
    if r.get("classification")!="MARGINFI_SOL_JULSEP_SOURCE_MONTH_COMPLETE":errors.append(f"{m}:month_not_complete")
    p=load_nd(ph[0]);w=load_nd(wh[0])
    if len(p)!=int(r.get("sol_population_count",-1)):errors.append(f"{m}:population_count_mismatch")
    if len(w)!=int(r.get("route_member_count",-1)):errors.append(f"{m}:route_count_mismatch")
    pop.extend(p);rows.extend(w)

pids=[ident(x) for x in pop];rids=[ident(x) for x in rows]
pdup=len(pids)-len(set(pids));rdup=len(rids)-len(set(rids))
if pdup:errors.append(f"population_duplicates:{pdup}")
if rdup:errors.append(f"route_duplicates:{rdup}")
if not set(rids).issubset(set(pids)):errors.append("route_not_subset_population")
if len(receipts)!=3:errors.append(f"monthly_receipt_count:{len(receipts)}")

I=sum(1 for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE")
D=sum(1 for r in rows if r.get("classification")=="DIRECTION_PROVEN")
A=sum(1 for r in rows if r.get("classification")=="DIRECTION_AMBIGUOUS")
C=sum(1 for r in rows if r.get("classification")=="CONTRADICTION")
complete=len(rows)-I
source_complete_rate=complete/len(rows) if rows else 0.0
direction_rate=D/complete if complete else 0.0

if errors:
    classification="MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_BLOCKED"
elif not rows:
    classification="MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PARTIAL"
elif source_complete_rate>=.95 and direction_rate>=.90 and C==0:
    classification="MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PASS"
else:
    classification="MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_PARTIAL"

pop.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
with POP.open("w") as fh:
    for r in pop:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

hops=Counter(str(r["hop_count"]) for r in rows if r.get("hop_count") is not None)
sem=Counter(r.get("route_semantic") for r in rows if r.get("route_semantic"))
days=Counter(str(r.get("timestamp",""))[:10] for r in rows if r.get("timestamp"))
liabs=Counter(r.get("liab_mint") for r in rows if r.get("liab_mint"))
reasons=Counter(r.get("reason") for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE" and r.get("reason"))

receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "authority":"MARGINFI_SOL_FLOW_EXHAUSTION_REBOUND_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "monthly_receipt_count":len(receipts),"sol_population_count":len(pop),"route_member_count":len(rows),
 "population_duplicate_count":pdup,"route_duplicate_count":rdup,
 "source_evidence_incomplete":I,"source_complete_count":complete,"source_complete_rate":source_complete_rate,
 "direction_proven":D,"direction_ambiguous":A,"contradictions":C,"direction_rate_complete":direction_rate,
 "hop_count_distribution":dict(sorted(hops.items(),key=lambda kv:int(kv[0]))),
 "route_semantic_counts":dict(sorted(sem.items())),
 "liability_mint_counts":dict(sorted(liabs.items(),key=lambda kv:(-kv[1],kv[0]))),
 "route_member_day_counts":dict(sorted(days.items())),
 "incomplete_reason_counts":dict(sorted(reasons.items())),
 "error_count":len(errors),"errors":errors,
 "population_file":str(POP),"rows_file":str(ROWS),
 "population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),
 "rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"pnl":False,"feb_mar_market_outcomes_opened":False,
             "jan_2024_validation_used":False,"jul_sep_market_outcomes_opened":False,"market_2025_opened":False,
             "market_2026_opened":False,"live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False}}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="MARGINFI_SOL_JULSEP_SIGNED_FLOW_SOURCE_BLOCKED":raise SystemExit(2)

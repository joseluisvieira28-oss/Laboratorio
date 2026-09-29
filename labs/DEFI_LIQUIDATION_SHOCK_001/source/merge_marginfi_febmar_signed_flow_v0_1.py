#!/usr/bin/env python3
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

EXPECTED=[
 ("fm-01","2024-02-01T00:00:00Z","2024-02-06T00:00:00Z"),
 ("fm-02","2024-02-06T00:00:00Z","2024-02-11T00:00:00Z"),
 ("fm-03","2024-02-11T00:00:00Z","2024-02-16T00:00:00Z"),
 ("fm-04","2024-02-16T00:00:00Z","2024-02-21T00:00:00Z"),
 ("fm-05","2024-02-21T00:00:00Z","2024-02-26T00:00:00Z"),
 ("fm-06","2024-02-26T00:00:00Z","2024-03-02T00:00:00Z"),
 ("fm-07","2024-03-02T00:00:00Z","2024-03-07T00:00:00Z"),
 ("fm-08","2024-03-07T00:00:00Z","2024-03-12T00:00:00Z"),
 ("fm-09","2024-03-12T00:00:00Z","2024-03-17T00:00:00Z"),
 ("fm-10","2024-03-17T00:00:00Z","2024-03-22T00:00:00Z"),
 ("fm-11","2024-03-22T00:00:00Z","2024-03-27T00:00:00Z"),
 ("fm-12","2024-03-27T00:00:00Z","2024-04-01T00:00:00Z"),
]

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_RECEIPT_V0.1.json"
POP=OUT/"MARGINFI_JUPITER_FEBMAR_SOURCE_POPULATION_V0.1.ndjson"
MEM=OUT/"MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_ROWS_V0.1.ndjson"

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(x):return x["signature"]+"|"+addrkey(x["instructionAddress"])
def load_nd(path):
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]

errors=[];receipts=[];pop=[];mem=[]
for sid,start,end in EXPECTED:
    rh=sorted(ROOT.rglob(f"MARGINFI_FEBMAR_SOURCE_SHARD_{sid}_RECEIPT_V0.1.json"))
    ph=sorted(ROOT.rglob(f"MARGINFI_FEBMAR_SOURCE_SHARD_{sid}_POPULATION_V0.1.ndjson"))
    mh=sorted(ROOT.rglob(f"MARGINFI_FEBMAR_SOURCE_SHARD_{sid}_MEMBERS_V0.1.ndjson"))
    if len(rh)!=1 or len(ph)!=1 or len(mh)!=1:
        errors.append(f"{sid}:artifact_file_count:{len(rh)}/{len(ph)}/{len(mh)}");continue
    r=json.loads(rh[0].read_text());receipts.append(r)
    if r.get("classification")!="MARGINFI_FEBMAR_SOURCE_SHARD_COMPLETE":
        errors.append(f"{sid}:not_complete")
    if r.get("shard_id")!=sid or r.get("start")!=start or r.get("end")!=end:
        errors.append(f"{sid}:interval_or_id_mismatch")
    if int(r.get("duplicate_identity_count",-1))!=0 or int(r.get("anomaly_count",-1))!=0:
        errors.append(f"{sid}:structural_nonzero")
    pr=load_nd(ph[0]);mr=load_nd(mh[0])
    if len(pr)!=int(r.get("population_count",-1)):errors.append(f"{sid}:population_count_mismatch")
    if len(mr)!=int(r.get("route_member_count",-1)):errors.append(f"{sid}:member_count_mismatch")
    pop.extend(pr);mem.extend(mr)

pop_ids=[ident(x) for x in pop];mem_ids=[ident(x) for x in mem]
pop_dup=len(pop_ids)-len(set(pop_ids));mem_dup=len(mem_ids)-len(set(mem_ids))
if pop_dup:errors.append(f"population_duplicates:{pop_dup}")
if mem_dup:errors.append(f"member_duplicates:{mem_dup}")
if not set(mem_ids).issubset(set(pop_ids)):errors.append("members_not_subset_population")
if len(receipts)!=12:errors.append(f"receipt_total:{len(receipts)}")

I=sum(1 for r in mem if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE")
D=sum(1 for r in mem if r.get("classification")=="DIRECTION_PROVEN")
A=sum(1 for r in mem if r.get("classification")=="DIRECTION_AMBIGUOUS")
C=sum(1 for r in mem if r.get("classification")=="CONTRADICTION")
complete=len(mem)-I
source_complete_rate=complete/len(mem) if mem else 0.0
direction_rate=D/complete if complete else 0.0

if errors:
    classification="MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_BLOCKED"
elif not mem:
    classification="MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PARTIAL"
elif source_complete_rate>=.95 and direction_rate>=.90 and C==0:
    classification="MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PASS"
else:
    classification="MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_PARTIAL"

pop.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
mem.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
with POP.open("w") as fh:
    for r in pop:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")
with MEM.open("w") as fh:
    for r in mem:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

assets=Counter(r.get("asset_mint") for r in mem if r.get("asset_mint"))
liabs=Counter(r.get("liab_mint") for r in mem if r.get("liab_mint"))
hops=Counter(str(r.get("hop_count")) for r in mem if r.get("hop_count") is not None)
sem=Counter(r.get("route_semantic") for r in mem if r.get("route_semantic"))
days=Counter(str(r.get("timestamp",""))[:10] for r in mem if r.get("timestamp"))
reasons=Counter(r.get("reason") for r in mem if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE" and r.get("reason"))

receipt={
 "schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "authority":"MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_TEMPORAL_SOURCE_EXTENSION_FREEZE_V0.1.md",
 "window":{"start":"2024-02-01T00:00:00Z","end":"2024-04-01T00:00:00Z"},
 "shard_count":len(receipts),"population_count":len(pop),"route_member_count":len(mem),
 "population_duplicate_count":pop_dup,"member_duplicate_count":mem_dup,
 "source_evidence_incomplete":I,"source_complete_count":complete,"source_complete_rate":source_complete_rate,
 "direction_proven":D,"direction_ambiguous":A,"contradictions":C,"direction_rate_complete":direction_rate,
 "asset_mint_counts":dict(sorted(assets.items(),key=lambda kv:(-kv[1],kv[0]))),
 "liability_mint_counts":dict(sorted(liabs.items(),key=lambda kv:(-kv[1],kv[0]))),
 "hop_count_distribution":dict(sorted(hops.items(),key=lambda kv:int(kv[0]))),
 "route_semantic_counts":dict(sorted(sem.items())),
 "route_member_day_counts":dict(sorted(days.items())),
 "incomplete_reason_counts":dict(sorted(reasons.items())),
 "error_count":len(errors),"errors":errors,
 "population_file":str(POP),"members_file":str(MEM),
 "population_sha256":hashlib.sha256(POP.read_bytes()).hexdigest(),
 "members_sha256":hashlib.sha256(MEM.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"pnl":False,"market_outcomes_feb_mar_2024":False,
             "jan_2024_reused_for_reversion_validation":False,"apr_jun_2024_holdout_opened":False,
             "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="MARGINFI_JUPITER_FEBMAR_SIGNED_FLOW_SOURCE_BLOCKED":raise SystemExit(2)

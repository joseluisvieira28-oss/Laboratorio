#!/usr/bin/env python3
import argparse,hashlib,json
from collections import Counter,defaultdict
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--source-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);SRC=Path(args.source_root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_RECEIPT_V0.1.json"
ROWS=OUT/"MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_ROWS_V0.1.ndjson"

def addrkey(v):return json.dumps(v,separators=(",",":"),sort_keys=True)
def ident(r):return r["signature"]+"|"+addrkey(r["instructionAddress"])
def load_nd(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

sp=find_one(SRC,"MARGINFI_SOL_OCTDEC_SOURCE_POPULATION_V0.1.ndjson")
sr=find_one(SRC,"MARGINFI_SOL_OCTDEC_POPULATION_RECEIPT_V0.1.json")
errors=[]
if sp is None or sr is None:
    errors.append("canonical_source_population_or_receipt_missing")
    canonical=[]
else:
    srec=json.loads(sr.read_text())
    if srec.get("classification")!="MARGINFI_SOL_OCTDEC_POPULATION_PASS":
        errors.append("canonical_source_not_pass")
    canonical=load_nd(sp)
expected_count=int(srec.get("sol_population_count",-1)) if 'srec' in locals() else -1
if expected_count<=0 or len(canonical)!=expected_count:errors.append(f"canonical_population_count:{len(canonical)} expected:{expected_count}")
canon_ids=[ident(r) for r in canonical]
if len(canon_ids)!=len(set(canon_ids)):errors.append("canonical_population_duplicates")

receipts=[];rows=[]
for i in range(16):
    sid=f"orca-{i:02d}"
    rh=sorted(ROOT.rglob(f"MARGINFI_ORCA_OCTDEC_SOURCE_SHARD_{sid}_RECEIPT_V0.1.json"))
    wh=sorted(ROOT.rglob(f"MARGINFI_ORCA_OCTDEC_SOURCE_SHARD_{sid}_ROWS_V0.1.ndjson"))
    if len(rh)!=1 or len(wh)!=1:
        errors.append(f"{sid}:file_count:{len(rh)}/{len(wh)}");continue
    r=json.loads(rh[0].read_text());receipts.append(r)
    if r.get("classification")!="MARGINFI_ORCA_OCTDEC_SOURCE_SHARD_PASS":errors.append(f"{sid}:not_pass")
    w=load_nd(wh[0])
    if len(w)!=int(r.get("adjudication_count",-1)):errors.append(f"{sid}:row_count_mismatch")
    if int(r.get("assigned_count",-1))!=len(w):errors.append(f"{sid}:assigned_count_mismatch")
    rows.extend(w)

rids=[ident(r) for r in rows]
dup=len(rids)-len(set(rids))
missing=sorted(set(canon_ids)-set(rids))
extra=sorted(set(rids)-set(canon_ids))
if len(receipts)!=16:errors.append(f"receipt_count:{len(receipts)}")
if dup:errors.append(f"duplicate_identities:{dup}")
if missing:errors.append(f"missing_identities:{len(missing)}")
if extra:errors.append(f"extra_identities:{len(extra)}")
if len(rows)!=len(canonical):errors.append(f"merged_row_count:{len(rows)} expected:{len(canonical)}")

presence=[r for r in rows if r.get("classification")!="NOT_ORCA_ROUTE"]
incomplete=[r for r in presence if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE"]
complete=[r for r in presence if r.get("classification")!="SOURCE_EVIDENCE_INCOMPLETE"]
direction=[r for r in complete if r.get("classification")=="DIRECTION_PROVEN"]
amb=[r for r in complete if r.get("classification")=="DIRECTION_AMBIGUOUS"]
contr=[r for r in presence if r.get("classification")=="CONTRADICTION"]
source_complete_rate=len(complete)/len(presence) if presence else 0.0
direction_rate=len(direction)/len(complete) if complete else 0.0

if errors:
    classification="MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_BLOCKED"
elif not presence:
    classification="MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PARTIAL"
elif source_complete_rate>=.95 and direction_rate>=.90 and len(contr)==0:
    classification="MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PASS"
else:
    classification="MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_PARTIAL"

rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],addrkey(r["instructionAddress"])))
with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

month_pop=Counter(str(r.get("timestamp",""))[:7] for r in rows)
month_presence=Counter(str(r.get("timestamp",""))[:7] for r in presence)
month_complete=Counter(str(r.get("timestamp",""))[:7] for r in complete)
month_direction=Counter(str(r.get("timestamp",""))[:7] for r in direction)
types=Counter();sem=Counter();reasons=Counter();liabs=Counter()
for r in rows:
    for x in r.get("decoded_route") or []:
        if x.get("type"):types[x["type"]]+=1
    if r.get("route_semantic"):sem[r["route_semantic"]]+=1
    if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE" and r.get("reason"):reasons[r["reason"]]+=1
    if r.get("classification")=="DIRECTION_PROVEN" and r.get("liab_mint"):liabs[r["liab_mint"]]+=1
exact=sum(1 for r in direction if r.get("exact_route_input_amount") is not None)

receipt={"schema_version":"0.1","lab_id":"DLS-MARGINFI-ORCA-OCTDEC-SIGNED-FLOW-001",
 "classification":classification,
 "authority":"MARGINFI_ORCA_TOPQ_REBOUND_OOS_V0_1_PRE_OUTCOME_FREEZE_2026-10-01.md",
 "canonical_population_count":len(canonical),"shard_receipt_count":len(receipts),
 "merged_adjudication_count":len(rows),"duplicate_identity_count":dup,
 "missing_identity_count":len(missing),"extra_identity_count":len(extra),
 "orca_presence_count":len(presence),"not_orca_route_count":len(rows)-len(presence),
 "source_evidence_incomplete":len(incomplete),"source_complete_count":len(complete),
 "source_complete_rate":source_complete_rate,"direction_proven":len(direction),
 "direction_ambiguous":len(amb),"contradictions":len(contr),
 "direction_rate_complete":direction_rate,
 "exact_input_amount_proven":exact,
 "exact_input_amount_rate_direction_proven":exact/len(direction) if direction else 0.0,
 "month_population_counts":dict(sorted(month_pop.items())),
 "month_orca_presence_counts":dict(sorted(month_presence.items())),
 "month_source_complete_counts":dict(sorted(month_complete.items())),
 "month_direction_proven_counts":dict(sorted(month_direction.items())),
 "instruction_type_counts":dict(types),"route_semantic_counts":dict(sem),
 "incomplete_reason_counts":dict(reasons),
 "liability_mint_counts":dict(sorted(liabs.items(),key=lambda kv:(-kv[1],kv[0]))),
 "error_count":len(errors),"errors":errors,
 "rows_file":str(ROWS),"rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"ohlc":False,"returns":False,"pnl":False,
             "oct_dec_market_outcomes_opened":False,"market_2025_opened":False,
             "market_2025_opened":False,"market_2026_opened":False,
             "live_trading":False,"orders":False,"wallets":False,
             "exchange_mutation":False,"merge_main":False,"post_decode_tuning":False}}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))
if classification=="MARGINFI_ORCA_OCTDEC_SIGNED_FLOW_SOURCE_BLOCKED":raise SystemExit(2)

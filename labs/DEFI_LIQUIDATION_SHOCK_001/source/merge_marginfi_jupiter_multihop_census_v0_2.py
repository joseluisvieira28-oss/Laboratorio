#!/usr/bin/env python3
import argparse,hashlib,json
from collections import Counter
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--members-root",required=True)
ap.add_argument("--shards-root",required=True)
ap.add_argument("--calibration-root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
RECEIPT=OUT/"MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_RECEIPT_V0.2.json"
ROWS=OUT/"MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_ROWS_V0.2.ndjson"

def addrkey(x):return json.dumps(x,separators=(",",":"),sort_keys=True)
def ident(x):return x["signature"]+"|"+addrkey(x["instructionAddress"])
def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    return hits[0] if len(hits)==1 else None

errors=[]
mrec=find_one(args.members_root,"MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_RECEIPT_V0.2.json")
mfile=find_one(args.members_root,"MARGINFI_JUPITER_ROUTE_CLASS_MEMBERS_V0.2.ndjson")
crec=find_one(args.calibration_root,"MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_RECEIPT_V0.2.json")
if mrec is None or mfile is None:errors.append("membership_evidence_missing_or_duplicate")
if crec is None:errors.append("calibration_receipt_missing_or_duplicate")
if errors:
    RECEIPT.write_text(json.dumps({"classification":"MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_BLOCKED","errors":errors},indent=2)+"\n")
    raise SystemExit(2)

mr=json.loads(mrec.read_text());cr=json.loads(crec.read_text())
if mr.get("classification")!="MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS":errors.append("membership_not_pass")
if cr.get("classification")!="MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_PASS":errors.append("calibration_not_pass")
expected_members=[json.loads(x) for x in mfile.read_text().splitlines() if x.strip()]
expected={ident(x) for x in expected_members}
if len(expected)!=len(expected_members):errors.append("membership_identity_duplicates")
if len(expected_members)!=int(mr.get("member_count",-1)):errors.append("membership_count_mismatch")

receipts=[]
rows=[]
seen_shards=set()
for rp in sorted(Path(args.shards_root).rglob("MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_*_RECEIPT_V0.2.json")):
    r=json.loads(rp.read_text())
    si=int(r.get("shard_index",-1))
    if si in seen_shards:
        errors.append(f"duplicate_shard_receipt_{si:02d}");continue
    seen_shards.add(si);receipts.append(r)
    if r.get("classification")!="MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_COMPLETE":errors.append(f"shard_not_complete_{si:02d}")
    if int(r.get("shard_count",-1))!=16:errors.append(f"shard_count_not_16_{si:02d}")
    if int(r.get("population_member_count",-1))!=len(expected_members):errors.append(f"population_count_mismatch_{si:02d}")
    row_hits=sorted(rp.parent.glob(f"MARGINFI_JUPITER_MULTI_HOP_SOURCE_SHARD_{si:02d}_ROWS_V0.2.ndjson"))
    if len(row_hits)!=1:
        errors.append(f"row_file_missing_or_duplicate_{si:02d}");continue
    shard_rows=[json.loads(x) for x in row_hits[0].read_text().splitlines() if x.strip()]
    if len(shard_rows)!=int(r.get("assigned_count",-1)) or len(shard_rows)!=int(r.get("sample_count",-1)):
        errors.append(f"shard_row_count_mismatch_{si:02d}")
    rows.extend(shard_rows)

if seen_shards!=set(range(16)):
    errors.append("shard_set_not_exact_0_15")

ids=[ident(x) for x in rows]
idset=set(ids)
duplicate_count=len(ids)-len(idset)
missing=sorted(expected-idset)
extra=sorted(idset-expected)
if duplicate_count:errors.append(f"duplicate_member_rows_{duplicate_count}")
if missing:errors.append(f"missing_member_rows_{len(missing)}")
if extra:errors.append(f"extra_member_rows_{len(extra)}")
if len(rows)!=len(expected_members):errors.append("merged_row_count_mismatch")

if errors:
    receipt={
      "schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001",
      "classification":"MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_BLOCKED",
      "errors":errors,"expected_population":len(expected_members),"merged_rows":len(rows),
      "duplicate_count":duplicate_count,"missing_count":len(missing),"extra_count":len(extra),
      "firewall":{"prices":False,"returns":False,"pnl":False,"market_2025_opened":False,"market_2026_opened":False,
                  "live_trading":False,"orders":False,"exchange_mutation":False,"merge_main":False}
    }
    RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    raise SystemExit(2)

rows.sort(key=lambda x:(x.get("rank",""),x["signature"],addrkey(x["instructionAddress"])))
with ROWS.open("w") as fh:
    for r in rows:fh.write(json.dumps(r,separators=(",",":"),sort_keys=True)+"\n")

N=len(rows)
I=sum(1 for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE")
D=sum(1 for r in rows if r.get("classification")=="DIRECTION_PROVEN")
A=sum(1 for r in rows if r.get("classification")=="DIRECTION_AMBIGUOUS")
C=sum(1 for r in rows if r.get("classification")=="CONTRADICTION")
complete=N-I
source_complete_rate=complete/N if N else 0.0
direction_rate=D/complete if complete else 0.0

if source_complete_rate>=.95 and direction_rate>=.90 and C==0:
    classification="MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_PASS"
else:
    classification="MARGINFI_JUPITER_MULTI_HOP_SIGNED_FLOW_SOURCE_PARTIAL"

hop=Counter(str(r["hop_count"]) for r in rows if r.get("hop_count") is not None)
sem=Counter(r.get("route_semantic") for r in rows if r.get("route_semantic"))
reasons=Counter(r.get("reason") for r in rows if r.get("classification")=="SOURCE_EVIDENCE_INCOMPLETE" and r.get("reason"))

receipt={
 "schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "authority":"MARGINFI_JUPITER_FULL_MULTI_HOP_SIGNED_FLOW_CENSUS_FREEZE_V0.2.md",
 "sharding_authority":"MARGINFI_JUPITER_FULL_MULTI_HOP_CENSUS_SHARDING_ADDENDUM_V0.2.md",
 "calibration_authority":"MARGINFI_JUPITER_MULTI_HOP_DIRECTION_CALIBRATION_PASS",
 "population_member_count":len(expected_members),"merged_row_count":N,"shard_count":16,
 "source_evidence_incomplete":I,"source_complete_count":complete,"source_complete_rate":source_complete_rate,
 "direction_proven":D,"direction_ambiguous":A,"contradictions":C,"direction_rate_complete":direction_rate,
 "duplicate_count":0,"missing_count":0,"extra_count":0,
 "hop_count_distribution":dict(sorted(hop.items(),key=lambda x:int(x[0]))),
 "route_semantic_counts":dict(sorted(sem.items())),
 "incomplete_reason_counts":dict(sorted(reasons.items())),
 "rows_file":str(ROWS),"rows_sha256":hashlib.sha256(ROWS.read_bytes()).hexdigest(),
 "firewall":{"prices":False,"returns":False,"pnl":False,"usd_notional":False,
   "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,
   "wallets":False,"exchange_mutation":False,"merge_main":False}
}
RECEIPT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2,sort_keys=True))

#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path

EXPECTED=[
 ("mfi-01","2024-01-01T00:00:00Z","2024-01-05T00:00:00Z"),
 ("mfi-02","2024-01-05T00:00:00Z","2024-01-09T00:00:00Z"),
 ("mfi-03","2024-01-09T00:00:00Z","2024-01-13T00:00:00Z"),
 ("mfi-04","2024-01-13T00:00:00Z","2024-01-17T00:00:00Z"),
 ("mfi-05","2024-01-17T00:00:00Z","2024-01-21T00:00:00Z"),
 ("mfi-06","2024-01-21T00:00:00Z","2024-01-25T00:00:00Z"),
 ("mfi-07","2024-01-25T00:00:00Z","2024-01-29T00:00:00Z"),
 ("mfi-08","2024-01-29T00:00:00Z","2024-02-01T00:00:00Z")
]
GLOBAL_N=10381

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
R=OUT/"MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_RECEIPT_V0.2.json"
M=OUT/"MARGINFI_JUPITER_ROUTE_CLASS_MEMBERS_V0.2.ndjson"

def identity(x):
    return x["signature"]+"|"+json.dumps(x["instructionAddress"],separators=(",",":"),sort_keys=True)

errors=[];receipts=[];members=[];seen_ids=set();dups=0
for sid,start,end in EXPECTED:
    hits=sorted(ROOT.rglob(f"MARGINFI_JUPITER_ROUTE_SHARD_{sid}_RECEIPT_V0.1.json"))
    mhits=sorted(ROOT.rglob(f"MARGINFI_JUPITER_ROUTE_SHARD_{sid}_MEMBERS_V0.1.ndjson"))
    if len(hits)!=1:
        errors.append(f"{sid}:receipt_count={len(hits)}");continue
    if len(mhits)!=1:
        errors.append(f"{sid}:members_count={len(mhits)}");continue
    r=json.loads(hits[0].read_text());receipts.append(r)
    if r.get("classification")!="MARGINFI_JUPITER_ROUTE_SHARD_PASS":errors.append(f"{sid}:classification={r.get('classification')}")
    if r.get("shard_id")!=sid or r.get("start")!=start or r.get("end")!=end:errors.append(f"{sid}:boundary_mismatch")
    if any(int(r.get(k,-1))!=0 for k in ("missing_count","extra_count","anomaly_count")):errors.append(f"{sid}:nonzero_reconciliation_error")
    with mhits[0].open() as fh:
        for line in fh:
            if not line.strip():continue
            x=json.loads(line);k=identity(x)
            if k in seen_ids:dups+=1
            seen_ids.add(k);members.append(x)

canonical=sum(int(r.get("canonical_population_count",0)) for r in receipts)
recovered=sum(int(r.get("recovered_population_count",0)) for r in receipts)
declared=sum(int(r.get("member_count",0)) for r in receipts)
if canonical!=GLOBAL_N:errors.append(f"global_canonical_count={canonical}")
if recovered!=GLOBAL_N:errors.append(f"global_recovered_count={recovered}")
if dups:errors.append(f"duplicate_member_identity_count={dups}")
if len(members)!=declared:errors.append(f"member_count_mismatch parsed={len(members)} declared={declared}")
if len(members)<=0:errors.append("global_member_count_zero")

members.sort(key=lambda x:(x["timestamp"],x["slot"],x["signature"],json.dumps(x["instructionAddress"])))
with M.open("w") as fh:
    for x in members:fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")

classification="MARGINFI_JUPITER_ROUTE_CLASS_MEMBERSHIP_PASS" if not errors else "MARGINFI_JUPITER_ROUTE_CLASS_BLOCKED"
out={
 "schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "authority":"MARGINFI_JUPITER_POST_LIQUIDATION_ROUTE_CLASS_FREEZE_V0.1.md",
 "transport_addendum":"MARGINFI_JUPITER_ROUTE_CLASS_TRANSPORT_SHARDING_ADDENDUM_V0.2.md",
 "shard_count":len(receipts),"expected_shard_count":8,
 "canonical_population_count":canonical,"recovered_population_count":recovered,
 "member_count":len(members),"member_rate":len(members)/GLOBAL_N if GLOBAL_N else None,
 "duplicate_member_identity_count":dups,"errors":errors,
 "members_file":str(M),"members_sha256":hashlib.sha256(M.read_bytes()).hexdigest(),
 "shards":[{"shard_id":r.get("shard_id"),"classification":r.get("classification"),
            "canonical_population_count":r.get("canonical_population_count"),"recovered_population_count":r.get("recovered_population_count"),
            "member_count":r.get("member_count"),"request_count":r.get("request_count")} for r in receipts],
 "firewall":{"token_balances":False,"token_amounts":False,"prices":False,"returns":False,"pnl":False,
   "market_direction":False,"market_2025_opened":False,"market_2026_opened":False,
   "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}
}
R.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:out[k] for k in ("classification","shard_count","canonical_population_count","recovered_population_count","member_count","member_rate","duplicate_member_identity_count","errors")},indent=2))
if errors:raise SystemExit(2)

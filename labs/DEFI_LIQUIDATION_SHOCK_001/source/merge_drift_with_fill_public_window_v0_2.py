#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path

EXPECTED=[
 ("wf2-01","2024-07-30T17:21:13Z","2024-08-10T00:00:00Z"),
 ("wf2-02","2024-08-10T00:00:00Z","2024-08-20T00:00:00Z"),
 ("wf2-03","2024-08-20T00:00:00Z","2024-09-01T00:00:00Z"),
 ("wf2-04","2024-09-01T00:00:00Z","2024-09-11T00:00:00Z"),
 ("wf2-05","2024-09-11T00:00:00Z","2024-09-21T00:00:00Z"),
 ("wf2-06","2024-09-21T00:00:00Z","2024-10-01T00:00:00Z"),
 ("wf2-07","2024-10-01T00:00:00Z","2024-10-11T00:00:00Z"),
 ("wf2-08","2024-10-11T00:00:00Z","2024-10-21T00:00:00Z"),
 ("wf2-09","2024-10-21T00:00:00Z","2024-11-01T00:00:00Z"),
 ("wf2-10","2024-11-01T00:00:00Z","2024-11-11T00:00:00Z"),
 ("wf2-11","2024-11-11T00:00:00Z","2024-11-21T00:00:00Z"),
 ("wf2-12","2024-11-21T00:00:00Z","2024-12-01T00:00:00Z"),
 ("wf2-13","2024-12-01T00:00:00Z","2024-12-11T00:00:00Z"),
 ("wf2-14","2024-12-11T00:00:00Z","2024-12-21T00:00:00Z"),
 ("wf2-15","2024-12-21T00:00:00Z","2025-01-01T00:00:00Z")
]

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--outdir",default="labs/DEFI_LIQUIDATION_SHOCK_001")
args=ap.parse_args()
ROOT=Path(args.root);OUT=Path(args.outdir);OUT.mkdir(parents=True,exist_ok=True)
R=OUT/"DRIFT_WITH_FILL_PUBLIC_WINDOW_RECEIPT_V0.2.json"
M=OUT/"DRIFT_WITH_FILL_PUBLIC_WINDOW_V0.2.ndjson"

errors=[];receipts=[];rows=[];seen=set();dups=0
for sid,start,end in EXPECTED:
    rh=sorted(ROOT.rglob(f"DRIFT_WITH_FILL_CENSUS_{sid}_RECEIPT_V0.1.json"))
    dh=sorted(ROOT.rglob(f"DRIFT_WITH_FILL_CENSUS_{sid}_V0.1.ndjson"))
    if len(rh)!=1:
        errors.append(f"{sid}:receipt_count={len(rh)}");continue
    if len(dh)!=1:
        errors.append(f"{sid}:data_count={len(dh)}");continue
    r=json.loads(rh[0].read_text());receipts.append(r)
    if r.get("classification") not in ("DRIFT_WITH_FILL_CENSUS_PASS","DRIFT_WITH_FILL_CENSUS_ZERO"):
        errors.append(f"{sid}:classification={r.get('classification')}")
    w=r.get("window") or {}
    if r.get("partition")!=sid or w.get("start")!=start or w.get("end_exclusive")!=end:
        errors.append(f"{sid}:boundary_mismatch")
    if int(r.get("error_count",-1))!=0:
        errors.append(f"{sid}:error_count={r.get('error_count')}")
    local=0
    with dh[0].open() as fh:
        for line in fh:
            if not line.strip():continue
            x=json.loads(line)
            k=x["signature"]+"|"+json.dumps(x["instructionAddress"],separators=(",",":"))
            if k in seen:dups+=1
            seen.add(k);rows.append(x);local+=1
    if local!=int(r.get("realized_count",-1)):
        errors.append(f"{sid}:realized_count_mismatch parsed={local} receipt={r.get('realized_count')}")

if len(receipts)!=len(EXPECTED):errors.append(f"receipt_total={len(receipts)}")
if dups:errors.append(f"duplicate_identity_count={dups}")
if not rows:errors.append("global_realized_count_zero")

rows.sort(key=lambda x:(x["timestamp"],x["slot"],x["signature"],json.dumps(x["instructionAddress"])))
with M.open("w") as fh:
    for x in rows:fh.write(json.dumps(x,separators=(",",":"),sort_keys=True)+"\n")

by_market={}
for x in rows:
    k=str(x.get("market_index"));by_market[k]=by_market.get(k,0)+1

classification="DRIFT_WITH_FILL_PUBLIC_WINDOW_PASS" if not errors else "DRIFT_WITH_FILL_PUBLIC_WINDOW_BLOCKED"
out={
 "schema_version":"0.2","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "authority":"DRIFT_WITH_FILL_PUBLIC_SOURCE_WINDOW_ADDENDUM_V0.1.md",
 "transport_addendum":"DRIFT_WITH_FILL_TRANSPORT_SHARDING_ADDENDUM_V0.2.md",
 "window":{"start":"2024-07-30T17:21:13Z","end_exclusive":"2025-01-01T00:00:00Z"},
 "shard_count":len(receipts),"expected_shard_count":len(EXPECTED),
 "realized_count":len(rows),"duplicate_identity_count":dups,"market_index_counts":by_market,
 "errors":errors,"census_file":str(M),"census_sha256":hashlib.sha256(M.read_bytes()).hexdigest(),
 "shards":[{"partition":r.get("partition"),"classification":r.get("classification"),
            "realized_count":r.get("realized_count"),"request_count":r.get("request_count"),
            "error_count":r.get("error_count")} for r in receipts],
 "firewall":{"prices":False,"returns":False,"pnl":False,"direction":False,
   "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,
   "orders":False,"wallets":False,"exchange_mutation":False,"merge_main":False}
}
R.write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:out[k] for k in ("classification","shard_count","realized_count","duplicate_identity_count","market_index_counts","errors")},indent=2))
if errors:raise SystemExit(2)

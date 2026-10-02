#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
import sys
BASE=Path(__file__).resolve().parents[1];SRC=BASE/"source";sys.path.insert(0,str(SRC))
import run_route_a3a_protected_2025_partition_v0_1 as a3a
EXPECTED=[
 ("2025-05-01T00:00:00Z","2025-05-09T00:00:00Z"),
 ("2025-05-09T00:00:00Z","2025-05-17T00:00:00Z"),
 ("2025-05-17T00:00:00Z","2025-05-25T00:00:00Z"),
 ("2025-05-25T00:00:00Z","2025-06-01T00:00:00Z"),
]
ap=argparse.ArgumentParser();ap.add_argument("--root",required=True);ap.add_argument("--out",required=True);a=ap.parse_args()
root=Path(a.root);shards=[]
for i,(ws,we) in enumerate(EXPECTED):
    hits=list(root.rglob(f"kamino-may-shard-{i}.json"))
    if len(hits)!=1:raise SystemExit(f"shard_identity_{i}_count={len(hits)}")
    r=json.loads(hits[0].read_text())
    assert r["classification"]=="SHARD_SOURCE_PASS"
    assert r["shard_index"]==i and r["window_start"]==ws and r["window_end"]==we
    assert r["error_count"]==0
    shards.append(r)
rows=[];seen=set();dups=[]
for r in shards:
    for x in r["rows"]:
        ident=(x["signature"],tuple(x["instructionAddress"]))
        if ident in seen:dups.append(ident)
        seen.add(ident);rows.append(x)
if dups:raise SystemExit("cross_shard_duplicate_canonical_instruction")
rows.sort(key=lambda x:(x["timestamp"],x["signature"],json.dumps(x["instructionAddress"],separators=(",",":"))))
transport={
 "route":"A3C_GTFA_SHARDED_KAMINO_MAY",
 "parent_route":"A3B_GTFA_STREAMING_PROGRAM_HISTORY",
 "shard_count":4,
 "shard_hash_chains":[r["transport"]["hash_chain"] for r in shards],
 "rpc_calls":sum(r["transport"]["rpc_calls"] for r in shards),
 "full_pages":sum(r["transport"]["full_pages"] for r in shards),
 "full_transaction_count":sum(r["transport"]["full_transaction_count"] for r in shards),
 "market_data_read":False,"economic_outcomes_opened":False,"trading_authority":"NONE"
}
pr=a3a.blank_receipt("kamino","2025-05-01T00:00:00Z","2025-06-01T00:00:00Z",transport)
pr["rows"]=rows
pr["successful_instruction_count"]=len(rows)
pr["unique_collateral_mint_count"]=len({x["collateral_mint"] for x in rows})
pr["sol_collateral_event_count"]=sum(x["collateral_mint"]==a3a.TARGET for x in rows)
pr["error_count"]=0;pr["errors"]=[];pr["duplicate_count"]=0;pr["duplicates"]=[]
Path(a.out).write_text(json.dumps(pr,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":pr["classification"],"successful_instruction_count":len(rows),
 "sol_collateral_event_count":pr["sol_collateral_event_count"],"full_transaction_count":transport["full_transaction_count"],
 "full_pages":transport["full_pages"]},sort_keys=True))

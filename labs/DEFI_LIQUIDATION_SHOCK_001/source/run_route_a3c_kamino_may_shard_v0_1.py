#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
SRC=BASE/"source";sys.path.insert(0,str(SRC))
import run_route_a3b_protected_2025_partition_v0_1 as a3b
import run_route_a3a_protected_2025_partition_v0_1 as a3a

SHARDS=[
 ("2025-05-01T00:00:00Z","2025-05-09T00:00:00Z"),
 ("2025-05-09T00:00:00Z","2025-05-17T00:00:00Z"),
 ("2025-05-17T00:00:00Z","2025-05-25T00:00:00Z"),
 ("2025-05-25T00:00:00Z","2025-06-01T00:00:00Z"),
]

def ts(s): return int(__import__("datetime").datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def main():
    ap=argparse.ArgumentParser();ap.add_argument("--shard",type=int,required=True);ap.add_argument("--outdir",required=True);a=ap.parse_args()
    if not 0<=a.shard<len(SHARDS):raise SystemExit("bad_shard")
    start_iso,end_iso=SHARDS[a.shard];start,end=ts(start_iso),ts(end_iso)
    out=Path(a.outdir);out.mkdir(parents=True,exist_ok=True)
    cfg=a3a.a2.cfg();program=cfg["kamino"]["program"];rpc=a3a.RPC()
    rows=[];seen=set();txhash={};dups=0;errors=[]
    def consume(item):
        nonlocal dups
        sig=a3a.item_sig(item);h=a3a.stable_hash(item)
        if sig in txhash:
            if txhash[sig]!=h:raise RuntimeError("duplicate_signature_payload_conflict")
            dups+=1;return
        txhash[sig]=h
        n=a3a.a2.normalize(item)
        if n["err"] is not None:raise RuntimeError("status_filter_returned_failed_transaction")
        if not(start<=int(n["timestamp"])<end):raise RuntimeError("transaction_outside_shard")
        for proto,ix in a3a.a2.matches(n,cfg):
            if proto!="kamino":continue
            if not a3a.canonical_2025_shape("kamino",ix):raise RuntimeError("canonical_2025_shape_conflict:kamino")
            if ix["path"] is None:raise RuntimeError("relevant_instruction_path_ambiguous:kamino")
            ident=(sig,tuple(ix["path"]))
            if ident in seen:raise RuntimeError("duplicate_canonical_instruction")
            seen.add(ident)
            rows.append({
              "protocol":"kamino","instruction_class":a3a.CLASSES["kamino"],"signature":sig,
              "instructionAddress":ix["path"],"slot":int(n["slot"]), "timestamp":a3a.iso_z(int(n["timestamp"])),
              "account_count":len(ix["accounts"]),"data_length":len(ix["data"]),
              "collateral_mint":ix["accounts"][8],"unit_resolution":"DIRECT_WITHDRAW_LIQUIDITY_MINT_ACCOUNT"
            })
    diag={}
    try:diag=a3b.stream_full(rpc,program,start,end,consume)
    except Exception as e:errors.append({"reason":str(e)[:300]})
    rows.sort(key=lambda x:(x["timestamp"],x["signature"],json.dumps(x["instructionAddress"],separators=(",",":"))))
    rec={
      "lab_id":"DEFI-LIQUIDATION-SHOCK-001","schema":"DLS_A3C_KAMINO_MAY_SHARD_V0.1",
      "shard_index":a.shard,"window_start":start_iso,"window_end":end_iso,
      "classification":"SHARD_SOURCE_PASS" if not errors else "SHARD_SOURCE_BLOCKED",
      "rows":rows,"successful_instruction_count":len(rows),
      "sol_collateral_event_count":sum(x["collateral_mint"]==a3a.TARGET for x in rows),
      "error_count":len(errors),"errors":errors,"duplicate_transport_hits":dups,
      "transport":{"route":"A3C_GTFA_SHARDED_KAMINO_MAY","rpc_calls":rpc.calls,
        "full_pages":diag.get("pages",0),"full_transaction_count":diag.get("count",0),
        "hash_chain":diag.get("hash_chain"),"market_data_read":False,
        "economic_outcomes_opened":False,"trading_authority":"NONE"},
      "firewall":{"prices_2025_opened":False,"returns_2025_opened":False,"pnl_2025_opened":False,
        "prices_2026_opened":False,"post_outcome_tuning":False}
    }
    p=out/f"kamino-may-shard-{a.shard}.json";p.write_text(json.dumps(rec,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:rec[k] for k in ["shard_index","classification","successful_instruction_count","sol_collateral_event_count","error_count","transport"]},sort_keys=True))
    if errors:raise SystemExit(2)
if __name__=="__main__":main()

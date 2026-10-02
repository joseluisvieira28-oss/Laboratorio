#!/usr/bin/env python3
from __future__ import annotations
import argparse,hashlib,json,sys
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
SRC=BASE/"source"
sys.path.insert(0,str(SRC))
import run_route_a3a_protected_2025_partition_v0_1 as a3a

def stream_full(rpc,address,start,end,on_item):
    token=None;seen=set();pages=0;count=0;chain=b""
    while True:
        opts={"transactionDetails":"full","sortOrder":"asc","limit":1000,
              "filters":{"blockTime":{"gte":start,"lt":end},"status":"succeeded"}}
        if token:opts["paginationToken"]=token
        res,h=rpc.call("getTransactionsForAddress",[address,opts])
        if not isinstance(res,dict) or not isinstance(res.get("data"),list):
            raise RuntimeError("gtfa_schema")
        data=res["data"]
        chain=hashlib.sha256(chain+bytes.fromhex(h)).digest()
        nxt=res.get("paginationToken")
        if not data:
            if nxt is not None:raise RuntimeError("empty_page_with_continuation")
            return {"pages":pages,"count":count,"hash_chain":chain.hex()}
        pages+=1;count+=len(data)
        for item in data:on_item(item)
        if nxt is None:
            return {"pages":pages,"count":count,"hash_chain":chain.hex()}
        if not isinstance(nxt,str) or not nxt or nxt==token or nxt in seen:
            raise RuntimeError("pagination_nonadvancing")
        seen.add(nxt);token=nxt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--group",choices=sorted(a3a.PROGRAM_GROUPS),required=True)
    ap.add_argument("--month",required=True)
    ap.add_argument("--outdir",required=True)
    args=ap.parse_args()
    if not (len(args.month)==2 and 1<=int(args.month)<=12):raise SystemExit("bad_month")
    start,end,start_iso,end_iso=a3a.month_bounds(args.month)
    outdir=Path(args.outdir);outdir.mkdir(parents=True,exist_ok=True)
    cfg=a3a.a2.cfg();members=a3a.PROGRAM_GROUPS[args.group]
    programs={cfg[p]["program"] for p in members}
    if len(programs)!=1:raise RuntimeError("group_program_mismatch")
    program=next(iter(programs));rpc=a3a.RPC();errors=[];rows={p:[] for p in members}
    tx_hash={};seen_ix=set();transport_dups=0

    def consume(item):
        nonlocal transport_dups
        sig=a3a.item_sig(item);h=a3a.stable_hash(item)
        if sig in tx_hash:
            if tx_hash[sig]!=h:raise RuntimeError("duplicate_signature_payload_conflict")
            transport_dups+=1;return
        tx_hash[sig]=h
        try:n=a3a.a2.normalize(item)
        except Exception as exc:
            raise RuntimeError("program_transaction_normalize_error:"+type(exc).__name__) from exc
        if n["err"] is not None:raise RuntimeError("status_filter_returned_failed_transaction")
        if not(start<=int(n["timestamp"])<end):raise RuntimeError("transaction_outside_partition")
        for proto,ix in a3a.a2.matches(n,cfg):
            if proto not in members:continue
            if not a3a.canonical_2025_shape(proto,ix):
                raise RuntimeError("canonical_2025_shape_conflict:"+proto)
            if ix["path"] is None:raise RuntimeError("relevant_instruction_path_ambiguous:"+proto)
            ident=(proto,sig,tuple(ix["path"]))
            if ident in seen_ix:raise RuntimeError("duplicate_canonical_instruction")
            seen_ix.add(ident)
            r={"protocol":proto,"instruction_class":a3a.CLASSES[proto],"signature":sig,
               "instructionAddress":ix["path"],"slot":int(n["slot"]),
               "timestamp":a3a.iso_z(int(n["timestamp"])),"account_count":len(ix["accounts"]),
               "data_length":len(ix["data"])}
            if proto=="marginfi":
                r["_mapping_account"]=ix["accounts"][1]
            elif proto=="save0c":
                r["_mapping_account"]=ix["accounts"][4]
            elif proto=="kamino":
                r["collateral_mint"]=ix["accounts"][8]
                r["unit_resolution"]="DIRECT_WITHDRAW_LIQUIDITY_MINT_ACCOUNT"
            elif proto=="save11":
                primary,optional=a3a.a2.unit(n,ix)
                if len(primary)!=1:raise RuntimeError("save11_unit_primary_not_exact_one")
                r["collateral_mint"],r["collateral_decimals"]=primary[0]
                r["unit_resolution"]="PRIMARY_RESERVE_VAULT_TOKEN_BALANCE"
                r["optional_unit_crosscheck_present"]=bool(optional)
            rows[proto].append(r)

    stream_diag={}
    try:
        stream_diag=stream_full(rpc,program,start,end,consume)
        if args.group=="marginfi":
            a3a.resolve_marginfi(rows["marginfi"],rpc,cfg["marginfi"],errors)
        if args.group=="save":
            a3a.resolve_save0c(rows["save0c"],rpc,cfg["save0c"],errors)
        for proto in members:
            unresolved=[r for r in rows[proto] if not r.get("collateral_mint")]
            if unresolved:errors.append({"reason":"unresolved_collateral_mint","protocol":proto,"count":len(unresolved)})
    except Exception as exc:
        errors.append({"reason":str(exc)[:300]})

    transport={"route":"A3B_GTFA_STREAMING_PROGRAM_HISTORY","program":program,"rpc_calls":rpc.calls,
      "initial_window":{"start":start_iso,"end":end_iso},
      "full_pages":stream_diag.get("pages",0),"full_transaction_count":stream_diag.get("count",0),
      "hash_chain":stream_diag.get("hash_chain"),"transport_duplicate_signature_hits":transport_dups,
      "market_data_read":False,"economic_outcomes_opened":False,"trading_authority":"NONE"}

    any_block=False
    for proto in members:
        pr=a3a.blank_receipt(proto,start_iso,end_iso,transport)
        clean=[{k:v for k,v in r.items() if not k.startswith("_")} for r in rows[proto]]
        clean.sort(key=lambda x:(x["timestamp"],x["signature"],json.dumps(x["instructionAddress"],separators=(",",":"))))
        pr["rows"]=clean
        pr["successful_instruction_count"]=len(clean)
        pr["unique_collateral_mint_count"]=len({x["collateral_mint"] for x in clean})
        pr["sol_collateral_event_count"]=sum(x["collateral_mint"]==a3a.TARGET for x in clean)
        pr["error_count"]=len(errors);pr["errors"]=errors[:200]
        if errors:
            pr["classification"]="PROTECTED_2025_PROTOCOL_SOURCE_BLOCKED";any_block=True
        (outdir/f"{proto}-2025{args.month}.json").write_text(json.dumps(pr,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"protocol":proto,"month":args.month,"classification":pr["classification"],
          "successful_instruction_count":pr["successful_instruction_count"],
          "sol_collateral_event_count":pr["sol_collateral_event_count"],
          "error_count":pr["error_count"],"rpc_calls":rpc.calls,
          "full_pages":transport["full_pages"],"full_transaction_count":transport["full_transaction_count"]},
          sort_keys=True),flush=True)
    if any_block:raise SystemExit(2)

if __name__=="__main__":main()

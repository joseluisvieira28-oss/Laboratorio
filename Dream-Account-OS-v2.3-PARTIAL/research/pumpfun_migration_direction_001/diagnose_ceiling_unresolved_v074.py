#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, math
from collections import Counter
from pathlib import Path
from source_rebuild_helius_v01 import Rpc, bonding_curve_pda, load_manifest, parse_ts
from chain_boundary_feasibility_v06 import paginate_window
from source_rebuild_block_first_v03 import get_blocks_batched
from intrablock_boundary_probe_v05 import (
    PUMP_PROGRAM, PUMP_AMM, tx_signature, account_keys, outer_instructions,
    resolve_program, resolve_ix_accounts, ix_data
)
from chain_boundary_semantics_v07 import SUPPORTED_MIGRATION_DISCRIMINATORS, is_actual_pool_creation_migration_v07

TARGET_INDICES=(15,283,284)
FROZEN_LOOKBACK=300
DIAGNOSTIC_LOOKBACK=1800
MAX_NEAREST_OUTSIDE=128

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--manifest",required=True)
    ap.add_argument("--out-dir",required=True)
    ap.add_argument("--rpc-url",default="https://api.mainnet-beta.solana.com")
    a=ap.parse_args()
    rows=load_manifest(Path(a.manifest))
    rpc=Rpc(a.rpc_url,"pmd_v074_unresolved_diagnostic")
    out=[]
    for idx in TARGET_INDICES:
        row=rows[idx]; mint=row["mint"]; pool=row["pool_address"]; pda=bonding_curve_pda(mint)
        t0=parse_ts(row["t0"]); upper=int(math.floor(t0))
        sigs,paging=paginate_window(rpc,pda,t0-DIAGNOSTIC_LOOKBACK)
        ext=[x for x in sigs if x.get("blockTime") is not None and t0-DIAGNOSTIC_LOOKBACK<=float(x["blockTime"])<=upper]
        ext=sorted(ext,key=lambda x:(float(x["blockTime"]),int(x.get("slot") or -1)),reverse=True)
        frozen=[x for x in ext if float(x["blockTime"])>=t0-FROZEN_LOOKBACK]
        selected=frozen if frozen else ext[:MAX_NEAREST_OUTSIDE]
        wanted={str(x["signature"]) for x in selected if x.get("signature")}
        slots=sorted({int(x["slot"]) for x in selected if x.get("slot") is not None})
        fetched=get_blocks_batched(rpc,slots,4) if slots else {}
        txmap={}
        block_errors=0
        for slot in slots:
            rec=fetched.get(slot) or {}; block=rec.get("block")
            if not isinstance(block,dict) or block.get("_rpc_error"):
                block_errors+=1; continue
            for item in block.get("transactions") or []:
                if not isinstance(item,dict): continue
                sig=tx_signature(item)
                if sig in wanted: txmap[sig]=item
        observations=[]; disc_counter=Counter(); actual=[]
        for meta in selected:
            sig=str(meta.get("signature")); item=txmap.get(sig)
            if not item: continue
            keys=account_keys(item); pump_ix=[]
            for ix in outer_instructions(item):
                if resolve_program(ix,keys)!=PUMP_PROGRAM: continue
                data=ix_data(ix); disc=bytes(data[:8]) if len(data)>=8 else b""
                accounts=set(resolve_ix_accounts(ix,keys))
                name=SUPPORTED_MIGRATION_DISCRIMINATORS.get(disc)
                d={
                    "disc_hex":disc.hex(),"supported_variant":name,
                    "has_mint":mint in accounts,"has_pda":pda in accounts,"has_pool":pool in accounts
                }
                pump_ix.append(d); disc_counter[(disc.hex(),str(name))]+=1
            logs=(item.get("meta") or {}).get("logMessages") or []
            rec={
                "signature":sig,"block_time":meta.get("blockTime"),"slot":meta.get("slot"),
                "lag_to_t0_seconds":t0-float(meta["blockTime"]),
                "success":(item.get("meta") or {}).get("err") is None,
                "pump_outer_instructions":pump_ix,
                "create_pool_log":any("Program log: Instruction: CreatePool" in str(x) for x in logs),
                "pump_amm_log":any(f"Program {PUMP_AMM} invoke" in str(x) for x in logs),
                "already_migrated_log":any("Bonding curve already migrated" in str(x) for x in logs),
                "actual_v07_boundary":is_actual_pool_creation_migration_v07(item,mint,pda,pool),
            }
            observations.append(rec)
            if rec["actual_v07_boundary"]: actual.append(rec)
        out.append({
            "lab":"PMD-001","stage":"V074_UNRESOLVED_SOURCE_DIAGNOSTIC","economic_outcomes_opened":False,
            "scientific_verdict_authority":False,"frozen_manifest_index":idx,"mint":mint,"pool_address":pool,
            "bonding_curve_pda":pda,"t0":row["t0"],"mint_suffix_pump":str(mint).endswith("pump"),
            "paging":paging,"diagnostic_lookback_seconds":DIAGNOSTIC_LOOKBACK,
            "frozen_lookback_seconds":FROZEN_LOOKBACK,"signatures_in_diagnostic_window":len(ext),
            "signatures_in_frozen_window":len(frozen),"selected_signatures":len(selected),
            "nearest_signature_lag_seconds":(t0-float(ext[0]["blockTime"])) if ext else None,
            "block_errors":block_errors,"selected_bodies_recovered":len(txmap),
            "actual_v07_boundaries_selected":len(actual),
            "actual_boundaries":[{k:r[k] for k in ("signature","block_time","slot","lag_to_t0_seconds")} for r in actual],
            "pump_discriminator_counts":[{"disc_hex":k[0],"supported_variant":k[1],"count":v} for k,v in sorted(disc_counter.items())],
            "observations":observations,
        })
    p=Path(a.out_dir); p.mkdir(parents=True,exist_ok=True)
    (p/"v074_unresolved_diagnostic.json").write_text(json.dumps(out,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps([{k:r[k] for k in ("frozen_manifest_index","mint","mint_suffix_pump","signatures_in_diagnostic_window","signatures_in_frozen_window","nearest_signature_lag_seconds","actual_v07_boundaries_selected")} for r in out],indent=2))
    return 0
if __name__=="__main__": raise SystemExit(main())

#!/usr/bin/env python3
"""MSEL-002 source-only dual-provider transport qualification.

Reacquires ONLY:
- frozen start/end boundary proof;
- end anchor;
- successful Token Mint Authority signature census in the exact 12h window.

It fetches no candidate future outcomes and no transaction bodies used for prevalence.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
import collect_onchain_identity_prevalence_v01 as v1

PROVIDERS = [
    ("official-mainnet-beta", "https://api.mainnet-beta.solana.com"),
    ("uniblock", "https://api.uniblock.dev/uni/v1/json-rpc?chainId=solana"),
]
OUT = Path("transport_qualification_v01")

def sig_digest(rows):
    h=hashlib.sha256()
    for r in sorted(rows,key=lambda x:(int(x["slot"]),str(x["signature"]))):
        h.update((str(r["slot"])+"|"+str(r["block_time"])+"|"+str(r["signature"])+"\n").encode())
    return h.hexdigest()

def run_provider(name,url,w):
    provider_dir=OUT/name
    provider_dir.mkdir(parents=True,exist_ok=True)
    v1.OUT_DIR=provider_dir
    v1.RAW_DIR=provider_dir/"raw_rpc"
    rpc=v1.Rpc(url)
    start=v1.find_first_confirmed_at_or_after(rpc,int(w["source_start"]))
    end=v1.find_first_confirmed_at_or_after(rpc,int(w["source_end"]))
    boundary_ok=(start[3] < int(w["source_start"]) <= start[1] and
                 end[3] < int(w["source_end"]) <= end[1])
    if not boundary_ok:
        raise RuntimeError(f"{name}: boundary proof failed")
    anchor=v1.find_authority_anchor_after(rpc,end[0],int(w["source_end"]))
    rows=v1.collect_authority_signatures(rpc,str(anchor["signature"]),int(w["source_start"]),int(w["source_end"]))
    if not rows:
        raise RuntimeError(f"{name}: zero authority signatures")
    result={
        "provider":name,"url":url,
        "start":{"slot":start[0],"time":start[1],"prev_slot":start[2],"prev_time":start[3]},
        "end":{"slot":end[0],"time":end[1],"prev_slot":end[2],"prev_time":end[3]},
        "anchor":anchor,
        "signature_count":len(rows),
        "signature_set_sha256":sig_digest(rows),
        "first_signature":rows[0],
        "last_signature":rows[-1],
        "rpc_receipt_count":len(rpc.receipts),
        "raw_rpc_file_count":len(list((provider_dir/"raw_rpc").glob("*.json"))),
    }
    (provider_dir/"summary.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    (provider_dir/"signatures.jsonl").write_text("".join(json.dumps(x,sort_keys=True,separators=(",",":"))+"\n" for x in rows))
    (provider_dir/"rpc_receipts.json").write_text(json.dumps(rpc.receipts,indent=2,sort_keys=True)+"\n")
    return result

def main():
    if OUT.exists():
        import shutil; shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    w=v1.frozen_window()
    if [w["source_start"],w["candidate_start"],w["source_end"]] != [1757101139,1757122739,1757144339]:
        raise RuntimeError("frozen window drift")
    results=[]
    failure=None
    try:
        for name,url in PROVIDERS:
            results.append(run_provider(name,url,w))
        a,b=results
        exact=(a["signature_count"]==b["signature_count"] and
               a["signature_set_sha256"]==b["signature_set_sha256"] and
               a["start"]==b["start"] and a["end"]==b["end"])
        expected_count=(a["signature_count"]==9564 and b["signature_count"]==9564)
        classification="UNIBLOCK_TRANSPORT_QUALIFICATION_PASS" if exact and expected_count else "UNIBLOCK_TRANSPORT_QUALIFICATION_FAIL"
        if not exact: failure="provider boundary/signature census disagreement"
        elif not expected_count: failure=f"signature count drift official={a['signature_count']} uniblock={b['signature_count']}"
    except Exception as exc:
        classification="UNIBLOCK_TRANSPORT_QUALIFICATION_TECHNICAL_FAILURE"
        failure=f"{type(exc).__name__}: {str(exc)[:1500]}"
    receipt={
        "lab_id":"MSEL-002",
        "classification":classification,
        "failure":failure,
        "window":w,
        "providers":results,
        "safety":{
            "prevalence_computed":False,
            "transaction_bodies_for_prevalence_fetched":False,
            "economic_outcomes_opened":False,
            "graduation_or_migration_opened":False,
            "returns_opened":False,
            "live_trading":False,
            "chain_mutation":False,
        }
    }
    (OUT/"qualification_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
        "classification":classification,
        "failure":failure,
        "providers":[{"provider":x["provider"],"count":x["signature_count"],"sha256":x["signature_set_sha256"]} for x in results],
        "economic_outcomes_opened":False
    },sort_keys=True))
    return 0 if classification=="UNIBLOCK_TRANSPORT_QUALIFICATION_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())

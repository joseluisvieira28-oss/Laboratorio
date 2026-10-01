#!/usr/bin/env python3
import argparse,json,time,urllib.request,urllib.error
from collections import Counter,defaultdict
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
MARGINFI="MFv2hWf31Z9kbCa1snEPYctwafyhdvnV7FZnsebVacA"
JUPITER="JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4"

ap=argparse.ArgumentParser()
ap.add_argument("--root",required=True)
ap.add_argument("--sample-per-month",type=int,default=5)
ap.add_argument("--out",default="labs/DEFI_LIQUIDATION_SHOCK_001/MARGINFI_OCTDEC_POST_LIQUIDATION_ROUTE_MIGRATION_PROBE_V0.1.json")
args=ap.parse_args()

def find_pop(month):
    hits=sorted(Path(args.root).rglob(f"MARGINFI_SOL_OCTDEC_POPULATION_{month}_V0.1.ndjson"))
    if len(hits)!=1:
        raise RuntimeError(f"population_{month}_hit_count={len(hits)}")
    return hits[0]

def rpc_tx(sig,retries=8):
    body={"jsonrpc":"2.0","id":1,"method":"getTransaction","params":[sig,{"encoding":"json","maxSupportedTransactionVersion":0,"commitment":"finalized"}]}
    raw=json.dumps(body).encode()
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(RPC,data=raw,headers={"Content-Type":"application/json","User-Agent":"crypto-lab-marginfi-route-migration-v01/0.1"},method="POST")
            with urllib.request.urlopen(q,timeout=45) as r:
                obj=json.loads(r.read().decode())
            if obj.get("error"):
                last=obj["error"]
                time.sleep(min(20,2**i)); continue
            return obj.get("result")
        except urllib.error.HTTPError as e:
            last={"http":e.code,"body":e.read().decode("utf-8","replace")[:300]}
            time.sleep(min(20,2**i))
        except Exception as e:
            last={"error":type(e).__name__,"detail":str(e)[:300]}
            time.sleep(min(20,2**i))
    raise RuntimeError(f"rpc_exhausted:{last}")

def keystr(x):
    if isinstance(x,str): return x
    if isinstance(x,dict): return x.get("pubkey") or x.get("key") or str(x)
    return str(x)

months=["202410","202411","202412"]
sample=[]
for m in months:
    rows=[json.loads(x) for x in find_pop(m).read_text().splitlines() if x.strip()]
    rows.sort(key=lambda r:(r["timestamp"],r["slot"],r["signature"],json.dumps(r["instructionAddress"])))
    for r in rows[:args.sample_per_month]:
        sample.append({**r,"month":m})

records=[];program_counts=Counter();after_counts=Counter();errors=[]
for r in sample:
    try:
        tx=rpc_tx(r["signature"])
        if not tx:
            records.append({"month":r["month"],"signature":r["signature"],"slot":r["slot"],"status":"RPC_NULL"})
            continue
        msg=tx["transaction"]["message"];meta=tx.get("meta") or {}
        keys=[keystr(x) for x in msg.get("accountKeys") or []]
        la=meta.get("loadedAddresses") or {}
        keys += [keystr(x) for x in la.get("writable") or []] + [keystr(x) for x in la.get("readonly") or []]
        tops=[]
        for i,ins in enumerate(msg.get("instructions") or []):
            pi=ins.get("programIdIndex")
            pid=keys[pi] if isinstance(pi,int) and pi<len(keys) else ins.get("programId")
            tops.append({"outer_index":i,"program_id":pid})
            if pid: program_counts[pid]+=1
        inn=[]
        for grp in meta.get("innerInstructions") or []:
            outer=grp.get("index")
            for j,ins in enumerate(grp.get("instructions") or []):
                pi=ins.get("programIdIndex")
                pid=keys[pi] if isinstance(pi,int) and pi<len(keys) else ins.get("programId")
                inn.append({"outer_index":outer,"inner_index":j,"program_id":pid})
                if pid: program_counts[pid]+=1
        # source population instructionAddress is top-level [N] in this regime.
        liq_outer=(r.get("instructionAddress") or [None])[0]
        after=[]
        for x in tops:
            if isinstance(liq_outer,int) and x["outer_index"]>liq_outer and x["program_id"]:
                after.append(x["program_id"]);after_counts[x["program_id"]]+=1
        for x in inn:
            if isinstance(liq_outer,int) and x["outer_index"]>=liq_outer and x["program_id"] and x["program_id"]!=MARGINFI:
                after.append(x["program_id"]);after_counts[x["program_id"]]+=1
        records.append({
          "month":r["month"],"signature":r["signature"],"slot":r["slot"],"timestamp":r["timestamp"],
          "liquidation_instruction_address":r["instructionAddress"],"liability_mint":r.get("liab_mint"),
          "status":"PASS","jupiter_present_anywhere":JUPITER in [x["program_id"] for x in tops+inn],
          "top_level_programs":tops,"inner_programs":inn,"post_or_with_liquidation_program_ids":after
        })
        time.sleep(.25)
    except Exception as e:
        errors.append({"month":r["month"],"signature":r["signature"],"error":type(e).__name__,"detail":str(e)[:500]})

out={
 "schema_version":"0.1",
 "lab_id":"DEFI-LIQUIDATION-SHOCK-001",
 "classification":"MARGINFI_OCTDEC_ROUTE_MIGRATION_PROBE_COMPLETE" if not errors else "MARGINFI_OCTDEC_ROUTE_MIGRATION_PROBE_PARTIAL",
 "purpose":"source-only diagnostic of post-liquidation execution-route regime change; no market outcomes",
 "sample_per_month":args.sample_per_month,
 "sample_count":len(sample),"resolved_count":sum(1 for r in records if r.get("status")=="PASS"),
 "rpc_null_count":sum(1 for r in records if r.get("status")=="RPC_NULL"),
 "error_count":len(errors),"errors":errors,
 "jupiter_present_count":sum(1 for r in records if r.get("jupiter_present_anywhere")),
 "post_or_with_liquidation_program_counts":after_counts.most_common(),
 "all_program_counts":program_counts.most_common(),
 "records":records,
 "firewall":{"prices":False,"returns":False,"pnl":False,"oct_dec_2024_market_outcomes_opened":False,
             "market_2025_opened":False,"market_2026_opened":False,"live_trading":False,"orders":False,
             "wallets":False,"exchange_mutation":False,"merge_main":False}
}
Path(args.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:out[k] for k in ["classification","sample_count","resolved_count","rpc_null_count","error_count","jupiter_present_count","post_or_with_liquidation_program_counts"]},indent=2))

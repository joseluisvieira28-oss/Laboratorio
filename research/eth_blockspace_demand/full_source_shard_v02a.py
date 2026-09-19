#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json, os, sys, time
from pathlib import Path
from typing import Any
import requests

LAB="ETH-BLOCKSPACE-DEMAND-001"
START=13_000_000
STOP=21_500_000
STRIDE=1_800
TARGETS=list(range(START,STOP+1,STRIDE))
EXPECTED=4_723
CUTOFF=1_735_689_600
PROVIDERS=("https://eth.drpc.org","https://rpc.flashbots.net")
REQUIRED=("number","hash","parentHash","timestamp","gasLimit","gasUsed","baseFeePerGas")
SHARD_ID=int(os.environ.get("SHARD_ID","0"))
SHARD_COUNT=int(os.environ.get("SHARD_COUNT","8"))
OUT=Path("eth_blockspace_full_source_v02")/f"shard_{SHARD_ID:02d}"
OUT.mkdir(parents=True,exist_ok=True)

assert len(TARGETS)==EXPECTED
assert 0<=SHARD_ID<SHARD_COUNT

sessions={ep:requests.Session() for ep in PROVIDERS}

def rpc(ep:str,method:str,params:list[Any],retries:int=8)->Any:
    last=None
    for i in range(retries):
        try:
            r=sessions[ep].post(ep,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},
                headers={"Content-Type":"application/json","User-Agent":f"{LAB}/full-source-v0.2"},
                timeout=(8,25))
            if r.status_code in (429,500,502,503,504):
                raise RuntimeError(f"HTTP_{r.status_code}")
            r.raise_for_status()
            o=r.json()
            if o.get("error") is not None: raise RuntimeError(f"rpc_error:{o['error']}")
            return o.get("result")
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(min(0.75*(2**i),12.0))
    raise RuntimeError(f"{type(last).__name__}:{str(last)[:160]}")

def qi(x:Any)->int:
    if not isinstance(x,str) or not x.startswith("0x"): raise ValueError("quantity")
    return int(x,16)

def parse(ep:str,b:int)->dict[str,Any]:
    o=rpc(ep,"eth_getBlockByNumber",[hex(b),False])
    if not isinstance(o,dict): raise RuntimeError("null_block")
    miss=[f for f in REQUIRED if o.get(f) is None]
    if miss: raise RuntimeError("missing:"+",".join(miss))
    n=qi(o["number"]); ts=qi(o["timestamp"]); gl=qi(o["gasLimit"]); gu=qi(o["gasUsed"]); bf=qi(o["baseFeePerGas"])
    if n!=b: raise RuntimeError("identity_number")
    if ts>=CUTOFF: raise RuntimeError("PROTECTED_PERIOD")
    if gl<=0 or gu<0 or gu>gl or bf<=0: raise RuntimeError("header_sanity")
    return {"block_number":n,"block_hash":str(o["hash"]).lower(),"parent_hash":str(o["parentHash"]).lower(),
            "timestamp":ts,"gas_limit":gl,"gas_used":gu,"base_fee_per_gas":bf}

def main()->int:
    chain={}
    for ep in PROVIDERS:
        try: chain[ep]=(rpc(ep,"eth_chainId",[])=="0x1")
        except Exception: chain[ep]=False
    rows=[]; errors=[]; audit_required=0; audit_pass=0; fallback_count=0; protected=False
    mine=[(i,b) for i,b in enumerate(TARGETS) if i%SHARD_COUNT==SHARD_ID]
    for pos,(i,b) in enumerate(mine,1):
        primary=PROVIDERS[i%2]; secondary=PROVIDERS[1-(i%2)]
        is_audit=(i%20==0)
        if is_audit: audit_required+=1
        a=None; used=primary; fallback=False
        try:
            a=parse(primary,b)
        except Exception as e:
            if "PROTECTED_PERIOD" in str(e): protected=True
            try:
                a=parse(secondary,b); used=secondary; fallback=True; fallback_count+=1
            except Exception as e2:
                if "PROTECTED_PERIOD" in str(e2): protected=True
                errors.append({"index":i,"block_number":b,"stage":"PRIMARY_AND_FALLBACK","error":f"{type(e2).__name__}:{str(e2)[:180]}"})
                continue
        audit_ok=None
        if is_audit:
            try:
                x=parse(PROVIDERS[0],b); y=parse(PROVIDERS[1],b)
                audit_ok=(x["block_hash"]==y["block_hash"] and x["timestamp"]==y["timestamp"] and x["block_number"]==y["block_number"])
                if audit_ok: audit_pass+=1
                else: errors.append({"index":i,"block_number":b,"stage":"CROSS_PROVIDER_IDENTITY","error":"DISAGREEMENT"})
            except Exception as e:
                if "PROTECTED_PERIOD" in str(e): protected=True
                audit_ok=False
                errors.append({"index":i,"block_number":b,"stage":"CROSS_PROVIDER_AUDIT","error":f"{type(e).__name__}:{str(e)[:180]}"})
        if a is not None:
            rows.append({**a,"global_index":i,"assigned_provider":primary,"provider_used":used,
                         "fallback_used":fallback,"audit_required":is_audit,"audit_pass":audit_ok,
                         "gas_utilization":a["gas_used"]/a["gas_limit"],
                         "sample_block_base_fee_burn_wei":a["base_fee_per_gas"]*a["gas_used"]})
        time.sleep(0.10)

    csvp=OUT/f"ETH_BLOCKSPACE_SOURCE_SHARD_{SHARD_ID:02d}.csv"
    fields=["global_index","block_number","block_hash","parent_hash","timestamp","gas_limit","gas_used","base_fee_per_gas",
            "assigned_provider","provider_used","fallback_used","audit_required","audit_pass","gas_utilization","sample_block_base_fee_burn_wei"]
    with csvp.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(sorted(rows,key=lambda x:x["global_index"]))
    rec={"lab_id":LAB,"status":"SHARD_PASS" if all(chain.values()) and not protected and audit_pass==audit_required else "SHARD_SOURCE_FAILURE",
         "shard_id":SHARD_ID,"shard_count":SHARD_COUNT,"targets_assigned":len(mine),"rows_persisted":len(rows),
         "chain_id_ok":chain,"cross_audit_required":audit_required,"cross_audit_pass":audit_pass,
         "fallback_count":fallback_count,"error_count":len(errors),"errors":errors[:100],
         "protected_period_accessed":protected,
         "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
         "csv_sha256":hashlib.sha256(csvp.read_bytes()).hexdigest()}
    (OUT/f"ETH_BLOCKSPACE_SOURCE_SHARD_{SHARD_ID:02d}_RECEIPT.json").write_text(json.dumps(rec,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({k:rec[k] for k in ["status","shard_id","targets_assigned","rows_persisted","cross_audit_required","cross_audit_pass","fallback_count","error_count","protected_period_accessed"]},sort_keys=True))
    return 0 if rec["status"]=="SHARD_PASS" else 2

if __name__=="__main__": sys.exit(main())

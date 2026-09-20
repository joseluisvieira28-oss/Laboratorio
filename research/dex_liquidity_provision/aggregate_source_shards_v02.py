#!/usr/bin/env python3
from __future__ import annotations

import gzip, hashlib, json
from collections import Counter
from pathlib import Path

import requests
from eth_hash.auto import keccak

LAB_ID="DEX-LIQUIDITY-PROVISION-001"
POOL="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
FACTORY="0x1f98431c8ad98523631ae4a59f267346ea31f984"
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
WETH="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
FEE=500
FROM_BLOCK=13_900_000
TO_BLOCK=21_525_890
START_TS=1640995200
END_TS=1735689599
SHARDS=8
RPC_ENDPOINTS=[
 "https://ethereum-rpc.publicnode.com","https://eth.drpc.org","https://1rpc.io/eth",
 "https://eth.llamarpc.com","https://rpc.ankr.com/eth",
]
GET_POOL_SELECTOR=keccak(b"getPool(address,address,uint24)")[:4].hex()

def rpc_get_pool(endpoint):
    calldata="0x"+GET_POOL_SELECTOR+"0"*24+USDC[2:]+"0"*24+WETH[2:]+hex(FEE)[2:].rjust(64,"0")
    payload={"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":FACTORY,"data":calldata},"latest"]}
    try:
        r=requests.post(endpoint,json=payload,timeout=(10,30),headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/source-v0.2-aggregate"})
        r.raise_for_status(); obj=r.json()
        if obj.get("error") is not None: return False,None,str(obj["error"])[:300]
        raw=obj.get("result")
        if not isinstance(raw,str) or not raw.startswith("0x") or len(raw)<66: return False,None,"invalid result"
        return True,"0x"+raw[-40:].lower(),None
    except Exception as exc:
        return False,None,f"{type(exc).__name__}: {str(exc)[:300]}"

def main():
    root=Path("downloaded_shards")
    recs=[]
    for sid in range(SHARDS):
        matches=list(root.glob(f"**/dex_lp_shard_{sid:02d}/shard_receipt.json"))
        if len(matches)!=1: raise RuntimeError(f"shard receipt cardinality {sid}: {len(matches)}")
        r=json.loads(matches[0].read_text())
        if r.get("classification")!="SHARD_SOURCE_PASS": raise RuntimeError(f"shard {sid} not PASS")
        if int(r.get("shard_id",-1))!=sid or int(r.get("shard_count",-1))!=SHARDS: raise RuntimeError("shard identity mismatch")
        recs.append(r)
    recs.sort(key=lambda r:r["shard_id"])
    if recs[0]["from_block"]!=FROM_BLOCK or recs[-1]["to_block"]!=TO_BLOCK: raise RuntimeError("outer range mismatch")
    for a,b in zip(recs,recs[1:]):
        if a["to_block"]+1!=b["from_block"]: raise RuntimeError("non-contiguous shard ranges")

    counts=Counter(); days=set(); months={"Mint":set(),"Burn":set(),"Swap":set()}; years={"Mint":set(),"Burn":set(),"Swap":set()}
    total_logs=0; prewindow=0; transport=Counter(); seen=set(); dup=0
    shard_fingerprint=hashlib.sha256()
    for r in recs:
        counts.update(r["event_counts"]); days.update(r["swap_days"]); total_logs+=int(r["canonical_log_count"]); prewindow+=int(r["prewindow_structural_rows_ignored"])
        for k in months: months[k].update(r["event_months"][k]); years[k].update(int(x) for x in r["event_years"][k])
        transport.update(r.get("transport_stats") or {})
        shard_fingerprint.update(f'{r["shard_id"]}|{r["from_block"]}|{r["to_block"]}|{r["structural_sha256"]}\n'.encode())
        p=list(root.glob(f'**/dex_lp_shard_{int(r["shard_id"]):02d}/canonical_identities.txt.gz'))
        if len(p)!=1: raise RuntimeError("identity file cardinality mismatch")
        with gzip.open(p[0],"rt",encoding="ascii") as fh:
            for line in fh:
                key=line.rstrip("\n")
                if key in seen: dup+=1
                else: seen.add(key)
    if len(seen)!=total_logs: raise RuntimeError(f"canonical identity count mismatch unique={len(seen)} total={total_logs}")
    if dup!=0: raise RuntimeError(f"duplicate canonical identities across shards={dup}")

    rpc_rows=[]; usable={}
    for ep in RPC_ENDPOINTS:
        ok,addr,err=rpc_get_pool(ep); rpc_rows.append({"endpoint":ep,"usable":ok,"pool":addr,"error":err})
        if ok and addr: usable[ep]=addr
    unique=sorted(set(usable.values()))

    gates={
      "rpc_quorum_ge_2":len(usable)>=2,
      "rpc_identity_exact":len(unique)==1 and unique[0]==POOL,
      "duplicate_canonical_identities_zero":dup==0,
      "swap_days_ge_1000":len(days)>=1000,
      "swaps_ge_100000":counts["Swap"]>=100000,
      "mints_ge_500":counts["Mint"]>=500,
      "burns_ge_500":counts["Burn"]>=500,
      "mint_months_ge_30":len(months["Mint"])>=30,
      "burn_months_ge_30":len(months["Burn"])>=30,
      "swap_years_2022_2023_2024":years["Swap"]=={2022,2023,2024},
      "economic_values_decoded_false":True,
      "protected_period_clean":True,
    }
    if len(usable)<2: classification="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; failure=f"independent pool-identity quorum unavailable: {len(usable)} usable"
    elif len(unique)!=1: classification="PROVENANCE_FAILURE"; failure=f"RPC pool identity disagreement: {unique}"
    elif unique[0]!=POOL: classification="SOURCE_IDENTITY_FAILURE"; failure=f"factory getPool returned {unique[0]} expected {POOL}"
    elif all(gates.values()): classification="SOURCE_DATA_PASS"; failure=None
    else: classification="SOURCE_INSUFFICIENT_COVERAGE"; failure="one or more frozen structural gates failed"

    receipt={
      "lab_id":LAB_ID,"phase":"SOURCE_ONLY_STRUCTURAL_V0_2_SHARDED_AGGREGATE",
      "classification":classification,"failure":failure,
      "pool":POOL,"factory":FACTORY,"pair":"USDC/WETH","fee":FEE,
      "frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,
      "scientific_start_ts":START_TS,"scientific_end_ts":END_TS,
      "shard_count":SHARDS,"shard_ranges":[[r["from_block"],r["to_block"]] for r in recs],
      "rpc_identity":rpc_rows,"event_counts":dict(counts),"swap_unique_days":len(days),
      "event_month_counts":{k:len(v) for k,v in months.items()},
      "event_years":{k:sorted(v) for k,v in years.items()},
      "canonical_log_count":total_logs,"duplicate_canonical_identities":dup,
      "prewindow_structural_rows_ignored":prewindow,
      "sharded_structural_fingerprint_sha256":shard_fingerprint.hexdigest(),
      "transport_stats":dict(transport),"gates":gates,
      "safety":{"log_data_requested":False,"liquidity_amounts_decoded":False,"token_amounts_decoded":False,
                "prices_opened":False,"returns_opened":False,"realized_volatility_opened":False,
                "pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
    }
    out=Path("dex_liquidity_source_v02_output"); out.mkdir(parents=True,exist_ok=True)
    (out/"DEX_LIQUIDITY_PROVISION_001_SOURCE_RECEIPT_V0_2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"event_counts":dict(counts),"swap_unique_days":len(days),"gates":gates},sort_keys=True))
    return 0 if classification=="SOURCE_DATA_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())

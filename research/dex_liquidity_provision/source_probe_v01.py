#!/usr/bin/env python3
from __future__ import annotations

import hashlib, json, sys, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID="DEX-LIQUIDITY-PROVISION-001"
PORTAL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
FACTORY="0x1f98431c8ad98523631ae4a59f267346ea31f984"
USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
WETH="0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2"
FEE=500
FROM_BLOCK=13_900_000
TO_BLOCK=21_525_890
START_TS=1640995200
END_TS=1735689599
WINDOW=75_000
TRANSIENT={429,500,502,503,504,529}

RPC_ENDPOINTS=[
 "https://ethereum-rpc.publicnode.com",
 "https://eth.drpc.org",
 "https://1rpc.io/eth",
 "https://eth.llamarpc.com",
 "https://rpc.ankr.com/eth",
]

def topic(sig:str)->str:
    return "0x"+keccak(sig.encode()).hex()

T_MINT=topic("Mint(address,address,int24,int24,uint128,uint256,uint256)")
T_BURN=topic("Burn(address,int24,int24,uint128,uint256,uint256)")
T_SWAP=topic("Swap(address,address,int256,int256,uint160,uint128,int24)")
TOPICS={T_MINT:"Mint",T_BURN:"Burn",T_SWAP:"Swap"}
GET_POOL_SELECTOR=keccak(b"getPool(address,address,uint24)")[:4].hex()

def rpc_get_pool(endpoint:str)->tuple[bool,str|None,str|None]:
    calldata="0x"+GET_POOL_SELECTOR
    calldata+="0"*24+USDC[2:]
    calldata+="0"*24+WETH[2:]
    calldata+=hex(FEE)[2:].rjust(64,"0")
    payload={"jsonrpc":"2.0","id":1,"method":"eth_call","params":[{"to":FACTORY,"data":calldata},"latest"]}
    try:
        r=requests.post(endpoint,json=payload,timeout=(10,30),headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/source-v0.1"})
        r.raise_for_status()
        obj=r.json()
        if obj.get("error") is not None:
            return False,None,str(obj["error"])[:300]
        raw=obj.get("result")
        if not isinstance(raw,str) or not raw.startswith("0x") or len(raw)<66:
            return False,None,"invalid result"
        addr="0x"+raw[-40:].lower()
        return True,addr,None
    except Exception as exc:
        return False,None,f"{type(exc).__name__}: {str(exc)[:300]}"

def post_portal(body:dict[str,Any],stats:Counter[str])->requests.Response:
    last=None
    for attempt in range(20):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,headers={
                "Content-Type":"application/json","Accept-Encoding":"gzip",
                "User-Agent":f"{LAB_ID}/source-v0.1"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["transient_retries"]+=1
                retry=r.headers.get("Retry-After")
                r.close()
                if attempt<19:
                    try: delay=float(retry) if retry else min(60.0,1.5*(2**attempt))
                    except ValueError: delay=min(20.0,1.5*(2**attempt))
                    time.sleep(delay); continue
            r.raise_for_status()
            stats["successful_http_responses"]+=1
            return r
        except Exception as exc:
            last=exc
            stats["network_retries"]+=1
            if attempt<7:
                time.sleep(min(20.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def stream_logs(stats:Counter[str]):
    cursor=FROM_BLOCK
    while cursor<=TO_BLOCK:
        rt=min(TO_BLOCK,cursor+WINDOW-1)
        body={
          "type":"evm","fromBlock":cursor,"toBlock":rt,
          "fields":{
            "block":{"number":True,"timestamp":True},
            "log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}
          },
          "logs":[{"address":[POOL],"topic0":[T_MINT,T_BURN,T_SWAP]}]
        }
        r=post_portal(body,stats)
        page_last=None; rows=0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                obj=json.loads(raw)
                if isinstance(obj,dict) and obj.get("error"):
                    raise RuntimeError(f"portal error: {obj['error']}")
                h=obj.get("header") or obj.get("block") or {}
                bn=int(h["number"])
                if not(cursor<=bn<=rt):
                    raise RuntimeError("row outside requested window")
                if page_last is not None and bn<page_last:
                    raise RuntimeError("non-monotonic page")
                page_last=bn; rows+=1
                yield obj
        finally:
            r.close()
        stats["portal_rows"]+=rows
        cursor=(page_last+1) if page_last is not None else (rt+1)

def main()->int:
    outdir=Path("dex_liquidity_source_output"); outdir.mkdir(parents=True,exist_ok=True)
    dst=outdir/"DEX_LIQUIDITY_PROVISION_001_SOURCE_RECEIPT_V0_1.json"
    receipt:dict[str,Any]={}
    stats=Counter()
    try:
        rpc_rows=[]
        usable={}
        for ep in RPC_ENDPOINTS:
            ok,addr,err=rpc_get_pool(ep)
            rpc_rows.append({"endpoint":ep,"usable":ok,"pool":addr,"error":err})
            if ok and addr: usable[ep]=addr
        unique=sorted(set(usable.values()))
        if len(usable)<2:
            classification="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
            failure=f"independent pool-identity quorum unavailable: {len(usable)} usable"
        elif len(unique)!=1:
            classification="PROVENANCE_FAILURE"
            failure=f"RPC pool identity disagreement: {unique}"
        elif unique[0]!=POOL:
            classification="SOURCE_IDENTITY_FAILURE"
            failure=f"factory getPool returned {unique[0]} expected {POOL}"
        else:
            classification=None; failure=None

        counts=Counter(); seen=set(); days=set(); swap_day_set=set(); months_by_event={"Mint":set(),"Burn":set(),"Swap":set()}; years_by_event={"Mint":set(),"Burn":set(),"Swap":set()}
        structural=hashlib.sha256()
        prewindow_rows=0
        if classification is None:
            for obj in stream_logs(stats):
                h=obj.get("header") or obj.get("block") or {}
                bn=int(h["number"]); ts=int(h["timestamp"])
                if ts>END_TS:
                    raise RuntimeError("protected-period timestamp encountered")
                for log in obj.get("logs") or []:
                    addr=str(log.get("address","")).lower()
                    if addr!=POOL: raise RuntimeError("unexpected pool address")
                    topics=[str(x).lower() for x in (log.get("topics") or [])]
                    if not topics or topics[0] not in TOPICS: raise RuntimeError("unexpected event topic")
                    tx=str(log.get("transactionHash","")).lower()
                    li=log.get("logIndex")
                    li=int(li,16) if isinstance(li,str) and li.startswith("0x") else int(li)
                    key=(tx,li)
                    if key in seen: raise RuntimeError("duplicate canonical log identity")
                    seen.add(key)
                    if ts<START_TS:
                        prewindow_rows+=1
                        continue
                    ev=TOPICS[topics[0]]
                    dt=datetime.fromtimestamp(ts,tz=timezone.utc)
                    day=dt.date().isoformat(); month=f"{dt.year:04d}-{dt.month:02d}"
                    counts[ev]+=1; days.add(day); months_by_event[ev].add(month); years_by_event[ev].add(dt.year)
                    if ev=="Swap": swap_day_set.add(day)
                    structural.update(f"{bn}|{ts}|{tx}|{li}|{ev}\n".encode())

            # Operational hardening only: derive unique Swap UTC days during the same
            # immutable structural pass instead of re-downloading the frozen corpus.
            # Scientific window, source, event definitions and gates are unchanged.
            swap_days=len(swap_day_set)

            gates={
              "rpc_quorum_ge_2":len(usable)>=2,
              "rpc_identity_exact":len(unique)==1 and unique[0]==POOL,
              "swap_days_ge_1000":swap_days>=1000,
              "swaps_ge_100000":counts["Swap"]>=100000,
              "mints_ge_500":counts["Mint"]>=500,
              "burns_ge_500":counts["Burn"]>=500,
              "mint_months_ge_30":len(months_by_event["Mint"])>=30,
              "burn_months_ge_30":len(months_by_event["Burn"])>=30,
              "swap_years_2022_2023_2024":years_by_event["Swap"]=={2022,2023,2024},
              "economic_values_decoded_false":True,
              "protected_period_clean":True,
            }
            if all(gates.values()):
                classification="SOURCE_DATA_PASS"; failure=None
            else:
                classification="SOURCE_INSUFFICIENT_COVERAGE"; failure="one or more frozen structural gates failed"
        else:
            gates={}

        receipt={
          "lab_id":LAB_ID,"phase":"SOURCE_ONLY_STRUCTURAL_V0_1","classification":classification,"failure":failure,
          "pool":POOL,"factory":FACTORY,"pair":"USDC/WETH","fee":FEE,
          "frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,
          "scientific_start_ts":START_TS,"scientific_end_ts":END_TS,
          "rpc_identity":rpc_rows,"event_counts":dict(counts),
          "swap_unique_days":swap_days if classification not in ("SOURCE_ACQUISITION_TECHNICAL_FAILURE","PROVENANCE_FAILURE","SOURCE_IDENTITY_FAILURE") else 0,
          "event_month_counts":{k:len(v) for k,v in months_by_event.items()},
          "event_years":{k:sorted(v) for k,v in years_by_event.items()},
          "canonical_log_count":len(seen),"prewindow_structural_rows_ignored":prewindow_rows,
          "structural_sha256":structural.hexdigest(),"transport_stats":dict(stats),"gates":gates,
          "safety":{"log_data_requested":False,"liquidity_amounts_decoded":False,"token_amounts_decoded":False,
                    "prices_opened":False,"returns_opened":False,"realized_volatility_opened":False,
                    "pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        }
    except Exception as exc:
        receipt={
          "lab_id":LAB_ID,"phase":"SOURCE_ONLY_STRUCTURAL_V0_1",
          "classification":"SOURCE_ACQUISITION_TECHNICAL_FAILURE",
          "failure":f"{type(exc).__name__}: {str(exc)[:1200]}",
          "transport_stats":dict(stats),
          "safety":{"log_data_requested":False,"liquidity_amounts_decoded":False,"token_amounts_decoded":False,
                    "prices_opened":False,"returns_opened":False,"realized_volatility_opened":False,
                    "pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"event_counts":receipt.get("event_counts"),"swap_unique_days":receipt.get("swap_unique_days"),"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if receipt["classification"]=="SOURCE_DATA_PASS" else 2

if __name__=="__main__":
    sys.exit(main())

#!/usr/bin/env python3
from __future__ import annotations

import gzip, hashlib, json, os, sys, time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID="DEX-LIQUIDITY-PROVISION-001"
PORTAL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
FROM_BLOCK=13_900_000
TO_BLOCK=21_525_890
START_TS=1640995200
END_TS=1735689599
WINDOW=50_000
TRANSIENT={429,500,502,503,504,529}

def topic(sig:str)->str:
    return "0x"+keccak(sig.encode()).hex()

T_MINT=topic("Mint(address,address,int24,int24,uint128,uint256,uint256)")
T_BURN=topic("Burn(address,int24,int24,uint128,uint256,uint256)")
T_SWAP=topic("Swap(address,address,int256,int256,uint160,uint128,int24)")
TOPICS={T_MINT:"Mint",T_BURN:"Burn",T_SWAP:"Swap"}

def partition(sid:int,count:int)->tuple[int,int]:
    total=TO_BLOCK-FROM_BLOCK+1
    base,rem=divmod(total,count)
    start=FROM_BLOCK + sid*base + min(sid,rem)
    size=base + (1 if sid<rem else 0)
    return start,start+size-1

def post(body:dict[str,Any],stats:Counter[str])->requests.Response:
    last=None
    for attempt in range(20):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,headers={
                "Content-Type":"application/json","Accept-Encoding":"gzip",
                "User-Agent":f"{LAB_ID}/source-v0.2-sharded"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["transient_retries"]+=1
                retry=r.headers.get("Retry-After")
                r.close()
                if attempt<19:
                    try: delay=float(retry) if retry else min(60.0,1.5*(2**attempt))
                    except ValueError: delay=min(60.0,1.5*(2**attempt))
                    time.sleep(delay); continue
            r.raise_for_status()
            stats["successful_http_responses"]+=1
            return r
        except Exception as exc:
            last=exc; stats["network_retries"]+=1
            if attempt<19:
                time.sleep(min(60.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def main()->int:
    sid=int(os.environ["DEX_SHARD_ID"]); n=int(os.environ.get("DEX_SHARD_COUNT","8"))
    if not 0<=sid<n: raise RuntimeError("invalid shard id")
    lo,hi=partition(sid,n)
    out=Path(f"dex_lp_shard_{sid:02d}"); out.mkdir(parents=True,exist_ok=True)
    receipt_path=out/"shard_receipt.json"
    ids_path=out/"canonical_identities.txt.gz"
    stats=Counter()
    try:
        counts=Counter(); seen=set(); swap_days=set()
        months={"Mint":set(),"Burn":set(),"Swap":set()}
        years={"Mint":set(),"Burn":set(),"Swap":set()}
        structural=hashlib.sha256(); prewindow=0
        with gzip.open(ids_path,"wt",encoding="ascii") as ids:
            cursor=lo
            while cursor<=hi:
                rt=min(hi,cursor+WINDOW-1)
                body={
                    "type":"evm","fromBlock":cursor,"toBlock":rt,
                    "fields":{
                        "block":{"number":True,"timestamp":True},
                        "log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}
                    },
                    "logs":[{"address":[POOL],"topic0":[T_MINT,T_BURN,T_SWAP]}]
                }
                r=post(body,stats); last=None; rows=0
                try:
                    for raw in r.iter_lines(decode_unicode=True):
                        if not raw: continue
                        obj=json.loads(raw)
                        if isinstance(obj,dict) and obj.get("error"): raise RuntimeError(f"portal error: {obj['error']}")
                        h=obj.get("header") or obj.get("block") or {}
                        bn=int(h["number"]); ts=int(h["timestamp"])
                        if not(cursor<=bn<=rt): raise RuntimeError("row outside requested window")
                        if last is not None and bn<last: raise RuntimeError("non-monotonic page")
                        last=bn; rows+=1
                        if ts>END_TS: raise RuntimeError("protected-period timestamp encountered")
                        for log in obj.get("logs") or []:
                            if str(log.get("address","")).lower()!=POOL: raise RuntimeError("unexpected pool address")
                            topics=[str(x).lower() for x in (log.get("topics") or [])]
                            if not topics or topics[0] not in TOPICS: raise RuntimeError("unexpected event topic")
                            tx=str(log.get("transactionHash","")).lower()
                            li=log.get("logIndex")
                            li=int(li,16) if isinstance(li,str) and li.startswith("0x") else int(li)
                            key=f"{tx}|{li}"
                            if key in seen: raise RuntimeError("duplicate canonical log identity within shard")
                            seen.add(key)
                            ids.write(key+"\n")
                            if ts<START_TS:
                                prewindow+=1; continue
                            ev=TOPICS[topics[0]]
                            dt=datetime.fromtimestamp(ts,tz=timezone.utc)
                            day=dt.date().isoformat(); month=f"{dt.year:04d}-{dt.month:02d}"
                            counts[ev]+=1; months[ev].add(month); years[ev].add(dt.year)
                            if ev=="Swap": swap_days.add(day)
                            structural.update(f"{bn}|{ts}|{tx}|{li}|{ev}\n".encode())
                finally:
                    r.close()
                stats["portal_rows"]+=rows
                cursor=(last+1) if last is not None else (rt+1)

        receipt={
            "lab_id":LAB_ID,"phase":"SOURCE_ONLY_STRUCTURAL_V0_2_SHARD",
            "classification":"SHARD_SOURCE_PASS","shard_id":sid,"shard_count":n,
            "from_block":lo,"to_block":hi,
            "event_counts":dict(counts),"swap_days":sorted(swap_days),
            "event_months":{k:sorted(v) for k,v in months.items()},
            "event_years":{k:sorted(v) for k,v in years.items()},
            "canonical_log_count":len(seen),"prewindow_structural_rows_ignored":prewindow,
            "structural_sha256":structural.hexdigest(),"transport_stats":dict(stats),
            "safety":{"log_data_requested":False,"liquidity_amounts_decoded":False,"token_amounts_decoded":False,
                      "prices_opened":False,"returns_opened":False,"realized_volatility_opened":False,
                      "pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        }
        code=0
    except Exception as exc:
        receipt={
            "lab_id":LAB_ID,"phase":"SOURCE_ONLY_STRUCTURAL_V0_2_SHARD",
            "classification":"SHARD_SOURCE_TECHNICAL_FAILURE","shard_id":sid,"shard_count":n,
            "from_block":lo,"to_block":hi,"failure":f"{type(exc).__name__}: {str(exc)[:1200]}",
            "transport_stats":dict(stats),
            "safety":{"prices_opened":False,"returns_opened":False,"pnl_opened":False,
                      "accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}
        }
        code=2
    receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"shard":sid,"range":[lo,hi],
                      "event_counts":receipt.get("event_counts"),"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return code

if __name__=="__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

POOL="0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640"
PORTAL_DATASET="https://portal.sqd.dev/datasets/ethereum-mainnet"
PORTAL_STREAM=PORTAL_DATASET+"/stream"
TRANSIENT={429,500,502,503,504,529}
SIX_H=6*3600

SIG_MINT="Mint(address,address,int24,int24,uint128,uint256,uint256)"
SIG_BURN="Burn(address,int24,int24,uint128,uint256,uint256)"
SIG_SWAP="Swap(address,address,int256,int256,uint160,uint128,int24)"

def topic(sig:str)->str:
    return "0x"+keccak(sig.encode()).hex()

T_MINT=topic(SIG_MINT)
T_BURN=topic(SIG_BURN)
T_SWAP=topic(SIG_SWAP)
TOPICS={T_MINT:"Mint",T_BURN:"Burn",T_SWAP:"Swap"}

PHASES={
    "discovery":(1640995200,1704067200),
    "replication":(1704067200,1735689600),
}

def load_freeze(path:Path)->dict[str,Any]:
    f=json.loads(path.read_text(encoding="utf-8"))
    assert f["lab_id"]=="DEX-LIQUIDITY-PROVISION-001"
    assert f["status"]=="FROZEN_BEFORE_ECONOMIC_FIELD_ACCESS"
    assert f["source_binding"]["source_gate_run_id"]==35530732777
    assert f["source_binding"]["source_gate_artifact_id"]==10612116802
    assert f["source_binding"]["source_gate_verdict"]=="SOURCE_DATA_PASS"
    assert f["source_binding"]["pool"].lower()==POOL
    assert f["observation"]["cadence"]=="6H_UTC_NONOVERLAPPING"
    assert f["observation"]["feature_window"]=="[t-6h,t)"
    assert f["observation"]["outcome_window"]=="[t,t+6h)"
    assert f["firewalls"]["no_2025"] is True and f["firewalls"]["no_2026"] is True
    return f

def get_json(url:str, attempts:int=12)->dict[str,Any]:
    last=None
    for attempt in range(attempts):
        try:
            r=requests.get(url,timeout=(10,45),headers={"User-Agent":"DEX-LIQUIDITY-PROVISION-001/discovery-v01"})
            if r.status_code in TRANSIENT:
                r.close(); time.sleep(min(30.0,1.5*(2**attempt))); continue
            r.raise_for_status()
            return r.json()
        except Exception as exc:
            last=exc
            if attempt<attempts-1:
                time.sleep(min(30.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def resolve_block(ts:int)->int:
    j=get_json(f"{PORTAL_DATASET}/timestamps/{ts}/block")
    n=int(j["block_number"])
    if n<=0: raise RuntimeError("invalid resolved block")
    return n

def partition(lo:int,hi:int,sid:int,count:int)->tuple[int,int]:
    total=hi-lo+1
    base,rem=divmod(total,count)
    start=lo+sid*base+min(sid,rem)
    size=base+(1 if sid<rem else 0)
    return start,start+size-1

def post_stream(body:dict[str,Any],stats:dict[str,int])->requests.Response:
    last=None
    for attempt in range(20):
        try:
            r=requests.post(
                PORTAL_STREAM,json=body,timeout=(20,180),stream=True,
                headers={"Content-Type":"application/json","Accept-Encoding":"gzip",
                         "User-Agent":"DEX-LIQUIDITY-PROVISION-001/discovery-v01"}
            )
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
            last=exc
            stats["network_retries"]+=1
            if attempt<19:
                time.sleep(min(60.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def parse_log_index(v:Any)->int:
    if isinstance(v,int): return v
    if isinstance(v,str):
        return int(v,16) if v.startswith("0x") else int(v)
    raise ValueError("invalid logIndex")

def words(data:Any)->list[str]:
    if not isinstance(data,str) or not data.startswith("0x"):
        raise ValueError("log.data not hex")
    h=data[2:]
    if len(h)%64!=0:
        raise ValueError("log.data word alignment")
    return [h[i:i+64] for i in range(0,len(h),64)]

def main()->int:
    ap=argparse.ArgumentParser()
    ap.add_argument("--phase",choices=sorted(PHASES),required=True)
    ap.add_argument("--shard-id",type=int,required=True)
    ap.add_argument("--shard-count",type=int,default=8)
    ap.add_argument("--freeze",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    load_freeze(args.freeze)
    if not 0<=args.shard_id<args.shard_count: raise RuntimeError("invalid shard id")

    start_ts,end_ts=PHASES[args.phase]
    if end_ts>1735689600: raise RuntimeError("protected period access forbidden")

    phase_lo=resolve_block(start_ts)
    phase_hi=resolve_block(end_ts-1)
    if phase_hi<phase_lo: raise RuntimeError("resolved phase range invalid")
    lo,hi=partition(phase_lo,phase_hi,args.shard_id,args.shard_count)

    args.out.mkdir(parents=True,exist_ok=True)
    price_path=args.out/"minute_prices.jsonl.gz"
    lp_path=args.out/"lp_buckets.jsonl.gz"
    receipt_path=args.out/"shard_receipt.json"

    stats=defaultdict(int)
    minute_last:dict[int,tuple[int,int,int]]={}
    lp:dict[int,list[int]]=defaultdict(lambda:[0,0,0,0])
    seen=set()
    event_counts=defaultdict(int)
    malformed=0
    prewindow=0
    min_ts=None; max_ts=None
    cursor=lo

    try:
        while cursor<=hi:
            rt=min(hi,cursor+50_000-1)
            body={
                "type":"evm","fromBlock":cursor,"toBlock":rt,
                "fields":{
                    "block":{"number":True,"timestamp":True},
                    "log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
                },
                "logs":[{"address":[POOL],"topic0":[T_MINT,T_BURN,T_SWAP]}]
            }
            r=post_stream(body,stats)
            last=None; rows=0
            try:
                for raw in r.iter_lines(decode_unicode=True):
                    if not raw: continue
                    obj=json.loads(raw)
                    if isinstance(obj,dict) and obj.get("error"):
                        raise RuntimeError(f"portal error: {obj['error']}")
                    h=obj.get("header") or obj.get("block") or {}
                    bn=int(h["number"]); ts=int(h["timestamp"])
                    if not(cursor<=bn<=rt): raise RuntimeError("row outside requested window")
                    if last is not None and bn<last: raise RuntimeError("non-monotonic portal page")
                    last=bn; rows+=1
                    if ts>=end_ts:
                        raise RuntimeError(f"PROTECTED_PHASE_BOUNDARY_VIOLATION_{ts}")
                    if ts<start_ts:
                        prewindow+=1
                        continue
                    min_ts=ts if min_ts is None else min(min_ts,ts)
                    max_ts=ts if max_ts is None else max(max_ts,ts)
                    for log in obj.get("logs") or []:
                        if str(log.get("address","")).lower()!=POOL:
                            raise RuntimeError("unexpected pool")
                        tops=[str(x).lower() for x in (log.get("topics") or [])]
                        if not tops or tops[0] not in TOPICS:
                            raise RuntimeError("unexpected topic")
                        tx=str(log.get("transactionHash","")).lower()
                        li=parse_log_index(log.get("logIndex"))
                        key=f"{tx}|{li}"
                        if key in seen:
                            raise RuntimeError("duplicate canonical log identity within shard")
                        seen.add(key)
                        ev=TOPICS[tops[0]]
                        w=words(log.get("data"))
                        event_counts[ev]+=1
                        if ev=="Mint":
                            if len(w)!=4: raise RuntimeError(f"MINT_DATA_WORDS_{len(w)}")
                            amount=int(w[1],16)
                            b=ts-(ts%SIX_H)
                            lp[b][0]+=amount; lp[b][2]+=1
                        elif ev=="Burn":
                            if len(w)!=3: raise RuntimeError(f"BURN_DATA_WORDS_{len(w)}")
                            amount=int(w[0],16)
                            b=ts-(ts%SIX_H)
                            lp[b][1]+=amount; lp[b][3]+=1
                        else:
                            if len(w)!=5: raise RuntimeError(f"SWAP_DATA_WORDS_{len(w)}")
                            sqrtp=int(w[2],16)
                            if sqrtp<=0: raise RuntimeError("nonpositive sqrtPriceX96")
                            minute=ts-(ts%60)
                            order=(bn,li,sqrtp)
                            prev=minute_last.get(minute)
                            if prev is None or (bn,li)>(prev[0],prev[1]):
                                minute_last[minute]=order
            finally:
                r.close()
            stats["portal_rows"]+=rows
            # SQD may return a partial terminal block range; continue from last returned block.
            cursor=(last+1) if last is not None else (rt+1)

        with gzip.open(price_path,"wt",encoding="utf-8") as fh:
            for minute in sorted(minute_last):
                bn,li,sqrtp=minute_last[minute]
                fh.write(json.dumps({"minute_ts":minute,"block_number":bn,"log_index":li,"sqrtPriceX96":sqrtp},
                                    separators=(",",":"))+"\n")
        with gzip.open(lp_path,"wt",encoding="utf-8") as fh:
            for b in sorted(lp):
                mint,burn,mc,bc=lp[b]
                fh.write(json.dumps({"bucket_start_ts":b,"mint_liquidity":mint,"burn_liquidity":burn,
                                     "mint_count":mc,"burn_count":bc},separators=(",",":"))+"\n")

        receipt={
            "lab_id":"DEX-LIQUIDITY-PROVISION-001",
            "phase":args.phase,
            "classification":"ECONOMIC_SOURCE_SHARD_PASS",
            "shard_id":args.shard_id,"shard_count":args.shard_count,
            "phase_start_ts":start_ts,"phase_end_exclusive_ts":end_ts,
            "resolved_phase_from_block":phase_lo,"resolved_phase_to_block":phase_hi,
            "from_block":lo,"to_block":hi,
            "canonical_log_count":len(seen),
            "event_counts":dict(event_counts),
            "minute_price_rows":len(minute_last),
            "lp_bucket_rows":len(lp),
            "prewindow_block_rows_ignored":prewindow,
            "min_event_ts":min_ts,"max_event_ts":max_ts,
            "transport_stats":dict(stats),
            "source_integrity_failures":0,
            "safety":{"opened_2025":False,"opened_2026":False,"pnl_opened":False,
                      "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False}
        }
        receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"classification":receipt["classification"],"phase":args.phase,"shard":args.shard_id,
                          "range":[lo,hi],"events":dict(event_counts),"minute_prices":len(minute_last),"lp_buckets":len(lp)},
                         sort_keys=True))
        return 0
    except Exception as exc:
        receipt={
            "lab_id":"DEX-LIQUIDITY-PROVISION-001","phase":args.phase,
            "classification":"ECONOMIC_SOURCE_SHARD_FAILURE",
            "shard_id":args.shard_id,"shard_count":args.shard_count,
            "from_block":lo,"to_block":hi,
            "failure":f"{type(exc).__name__}: {str(exc)[:1200]}",
            "transport_stats":dict(stats),"source_integrity_failures":1,
            "safety":{"opened_2025":False,"opened_2026":False,"pnl_opened":False,
                      "live_trading":False,"orders":False,"wallets":False,"exchange_mutation":False}
        }
        receipt_path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps(receipt,sort_keys=True))
        return 2

if __name__=="__main__":
    raise SystemExit(main())

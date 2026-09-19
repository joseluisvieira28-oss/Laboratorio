#!/usr/bin/env python3
"""2024-only canonical daily snapshot calendar for AAVE-LIQUIDATION-OVERHANG-001 replication."""
from __future__ import annotations

import datetime as dt
import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
SOURCE_FROM_BLOCK=16_490_000
START_DATE=dt.date(2024,1,1)
END_DATE=dt.date(2024,12,31)
NO_2025_TS=int(dt.datetime(2025,1,1,tzinfo=dt.timezone.utc).timestamp())
PROVIDERS=[
    "https://eth-mainnet.public.blastapi.io",
    "https://rpc.mevblocker.io",
    "https://ethereum.blinklabs.xyz/",
]
PRIMARY=PROVIDERS[0]
TRANSIENT={429,500,502,503,504,529}


def rpc_one(endpoint:str, method:str, params:list[Any], stats:Counter[str])->Any:
    headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/replication-calendar-v0.1"}
    last=None
    for attempt in range(4):
        try:
            r=requests.post(endpoint,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},
                            headers=headers,timeout=(10,45))
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["transient_retries"]+=1
                r.close(); time.sleep(1.5*(attempt+1)); continue
            r.raise_for_status(); o=r.json(); r.close()
            if o.get("error") is not None: raise RuntimeError(str(o["error"]))
            stats["usable_results"]+=1
            return o.get("result")
        except Exception as exc:
            last=exc; stats["errors"]+=1
            if attempt<3: time.sleep(1.5*(attempt+1))
    raise RuntimeError(f"{endpoint} {method}: {last}")


def block_tuple(endpoint:str,bn:int,stats:Counter[str])->tuple[int,int,str]:
    o=rpc_one(endpoint,"eth_getBlockByNumber",[hex(bn),False],stats)
    if not isinstance(o,dict): raise RuntimeError("block result not object")
    num=int(o["number"],16); ts=int(o["timestamp"],16); h=str(o["hash"]).lower()
    if num!=bn or not h.startswith("0x"): raise RuntimeError("invalid block identity")
    if ts>=NO_2025_TS: raise RuntimeError("2025 block header access forbidden")
    return num,ts,h


def primary_ts(bn:int, stats:Counter[str])->int:
    return block_tuple(PRIMARY,bn,stats)[1]


def locate_first_at_or_after(target_ts:int, lo:int, hi:int, stats:Counter[str])->int:
    if target_ts>=NO_2025_TS: raise RuntimeError("2025 target forbidden")
    if primary_ts(lo,stats)>=target_ts:
        while lo>SOURCE_FROM_BLOCK and primary_ts(lo,stats)>=target_ts:
            hi=lo; lo=max(SOURCE_FROM_BLOCK,lo-2500)
    while primary_ts(hi,stats)<target_ts:
        lo=hi+1; hi+=2500
    while lo<hi:
        mid=(lo+hi)//2
        if primary_ts(mid,stats)>=target_ts: hi=mid
        else: lo=mid+1
    return lo


def verify_boundary(bn:int,target_ts:int,provider_stats:dict[str,Counter[str]])->dict[str,Any]:
    accepted=[]; errors={}
    for ep in PROVIDERS:
        try:
            cur=block_tuple(ep,bn,provider_stats[ep])
            prev=block_tuple(ep,bn-1,provider_stats[ep])
            accepted.append((ep,cur,prev))
        except Exception as exc:
            errors[ep]=f"{type(exc).__name__}: {str(exc)[:300]}"
    if len(accepted)<2: raise RuntimeError(f"snapshot block quorum<2 at {bn}: {errors}")
    cur_set={(x[1][0],x[1][1],x[1][2]) for x in accepted}
    prev_set={(x[2][0],x[2][1],x[2][2]) for x in accepted}
    if len(cur_set)!=1 or len(prev_set)!=1:
        raise RuntimeError(f"snapshot block provider disagreement at {bn}")
    cur=next(iter(cur_set)); prev=next(iter(prev_set))
    if not (prev[1] < target_ts <= cur[1]):
        raise RuntimeError(f"block {bn} does not bracket target timestamp {target_ts}")
    return {
        "block":bn,"timestamp":cur[1],"hash":cur[2],
        "previous_block":bn-1,"previous_timestamp":prev[1],"previous_hash":prev[2],
        "usable_provider_count":len(accepted),"provider_errors":errors,
    }


def main()->int:
    out=Path("replication_calendar_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_REPLICATION_CALENDAR_2024_V0_1.json"
    stats={ep:Counter() for ep in PROVIDERS}; receipt={}
    try:
        days=[]; d=START_DATE; prev=None
        while d<=END_DATE:
            target=int(dt.datetime(d.year,d.month,d.day,tzinfo=dt.timezone.utc).timestamp())
            if prev is None:
                lo=18_900_000; hi=18_920_000
            else:
                lo=prev+5_000; hi=prev+9_000
            bn=locate_first_at_or_after(target,lo,hi,stats[PRIMARY])
            proof=verify_boundary(bn,target,stats)
            if proof["timestamp"]>=NO_2025_TS:
                raise RuntimeError("2024 snapshot crossed into 2025")
            days.append({"date":d.isoformat(),"target_timestamp":target,**proof})
            prev=bn; d+=dt.timedelta(days=1)

        if len(days)!=366: raise RuntimeError(f"expected 366 snapshots, got {len(days)}")
        if len({x["block"] for x in days})!=366: raise RuntimeError("duplicate snapshot block")
        if days[-1]["date"]!="2024-12-31": raise RuntimeError("terminal replication date mismatch")

        receipt={
            "lab_id":LAB_ID,
            "classification":"REPLICATION_CALENDAR_PASS",
            "start_date":START_DATE.isoformat(),
            "end_date":END_DATE.isoformat(),
            "snapshot_count":len(days),
            "snapshots":days,
            "replication_state_from_block":days[0]["block"],
            "replication_state_to_block":days[-1]["block"],
            "replication_outcome_from_block":days[0]["block"],
            "replication_outcome_to_block":days[-1]["block"]-1,
            "paired_outcome_window_count":365,
            "right_censored_terminal_date":"2024-12-31",
            "opened_2025_boundary_header":False,
            "rpc_stats":{k:dict(v) for k,v in stats.items()},
            "safety":{
                "opened_2024_predictor":False,"opened_2024_outcomes":False,
                "opened_2025_or_2026":False,"market_returns_opened":False,
                "pnl_opened":False,"live_trading":False,"exchange_mutation":False,
            },
        }
    except Exception as exc:
        receipt={
            "lab_id":LAB_ID,
            "classification":"REPLICATION_ACQUISITION_TECHNICAL_FAILURE",
            "failure":f"{type(exc).__name__}: {str(exc)[:1500]}",
            "rpc_stats":{k:dict(v) for k,v in stats.items()},
            "safety":{"opened_2024_predictor":False,"opened_2024_outcomes":False,
                      "opened_2025_or_2026":False,"market_returns_opened":False,
                      "pnl_opened":False,"live_trading":False,"exchange_mutation":False},
        }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"snapshot_count":receipt.get("snapshot_count"),
                      "state_from_block":receipt.get("replication_state_from_block"),
                      "state_to_block":receipt.get("replication_state_to_block"),
                      "paired_outcomes":receipt.get("paired_outcome_window_count")},sort_keys=True))
    return 0 if receipt["classification"]=="REPLICATION_CALENDAR_PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())

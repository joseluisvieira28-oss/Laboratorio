#!/usr/bin/env python3
"""2024-only canonical daily snapshot calendar for AAVE-LIQUIDATION-OVERHANG-001 replication."""
from __future__ import annotations
import datetime as dt, json, time
from collections import Counter
from pathlib import Path
from typing import Any
import requests

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
TO_BLOCK=21_525_890
START_DATE=dt.date(2024,1,1)
END_DATE=dt.date(2024,12,31)
MAX_TS=int(dt.datetime(2025,1,1,tzinfo=dt.timezone.utc).timestamp())-1
PROVIDERS=["https://eth-mainnet.public.blastapi.io","https://rpc.mevblocker.io","https://ethereum.blinklabs.xyz/"]
PRIMARY=PROVIDERS[0]
TRANSIENT={429,500,502,503,504,529}

def rpc_one(endpoint:str,method:str,params:list[Any],stats:Counter[str])->Any:
    headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/replication-calendar-v0.1"}
    last=None
    for attempt in range(4):
        try:
            r=requests.post(endpoint,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},headers=headers,timeout=(10,45))
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["transient_retries"]+=1; r.close(); time.sleep(1.5*(attempt+1)); continue
            r.raise_for_status(); o=r.json(); r.close()
            if o.get("error") is not None: raise RuntimeError(str(o["error"]))
            stats["usable_results"]+=1; return o.get("result")
        except Exception as exc:
            last=exc; stats["errors"]+=1
            if attempt<3: time.sleep(1.5*(attempt+1))
    raise RuntimeError(f"{endpoint} {method}: {last}")

def block_tuple(endpoint:str,bn:int,stats:Counter[str])->tuple[int,int,str]:
    o=rpc_one(endpoint,"eth_getBlockByNumber",[hex(bn),False],stats)
    if not isinstance(o,dict): raise RuntimeError("block result not object")
    num=int(o["number"],16); ts=int(o["timestamp"],16); h=str(o["hash"]).lower()
    if num!=bn or not h.startswith("0x"): raise RuntimeError("invalid block identity")
    return num,ts,h

def primary_ts(bn:int,stats:Counter[str])->int: return block_tuple(PRIMARY,bn,stats)[1]

def locate_first_at_or_after(target_ts:int,lo:int,hi:int,stats:Counter[str])->int:
    while primary_ts(hi,stats)<target_ts:
        lo=hi+1; hi=min(TO_BLOCK,hi+2500)
        if lo>TO_BLOCK: raise RuntimeError("target escaped frozen 2024 block envelope")
    while lo<hi:
        mid=(lo+hi)//2
        if primary_ts(mid,stats)>=target_ts: hi=mid
        else: lo=mid+1
    return lo

def verify_boundary(bn:int,target_ts:int,provider_stats:dict[str,Counter[str]])->dict[str,Any]:
    accepted=[]; errors={}
    for ep in PROVIDERS:
        try:
            cur=block_tuple(ep,bn,provider_stats[ep]); prev=block_tuple(ep,bn-1,provider_stats[ep])
            accepted.append((ep,cur,prev))
        except Exception as exc: errors[ep]=f"{type(exc).__name__}: {str(exc)[:300]}"
    if len(accepted)<2: raise RuntimeError(f"snapshot block quorum<2 at {bn}: {errors}")
    cur_set={(x[1][0],x[1][1],x[1][2]) for x in accepted}; prev_set={(x[2][0],x[2][1],x[2][2]) for x in accepted}
    if len(cur_set)!=1 or len(prev_set)!=1: raise RuntimeError(f"snapshot block provider disagreement at {bn}")
    cur=next(iter(cur_set)); prev=next(iter(prev_set))
    if not(prev[1]<target_ts<=cur[1]): raise RuntimeError(f"block {bn} does not bracket target timestamp {target_ts}")
    if cur[1]>MAX_TS: raise RuntimeError("snapshot crossed into 2025")
    return {"block":bn,"timestamp":cur[1],"hash":cur[2],"previous_block":bn-1,"previous_timestamp":prev[1],"previous_hash":prev[2],"usable_provider_count":len(accepted),"provider_errors":errors}

def load_discovery_boundary()->int:
    hits=[]
    for p in Path("downloaded_discovery_calendar").rglob("*.json"):
        x=json.loads(p.read_text())
        if x.get("classification")=="DISCOVERY_CALENDAR_PASS": hits.append(x)
    if len(hits)!=1: raise RuntimeError(f"expected one canonical 2023 calendar, got {len(hits)}")
    b=hits[0]["boundary_2024_header_only"]
    if int(b["timestamp"])<int(dt.datetime(2024,1,1,tzinfo=dt.timezone.utc).timestamp()): raise RuntimeError("invalid inherited 2024 boundary")
    return int(b["first_2024_block"])

def main()->int:
    out=Path("replication_calendar_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_REPLICATION_CALENDAR_2024_V0_1.json"
    stats={ep:Counter() for ep in PROVIDERS}
    try:
        first=load_discovery_boundary()
        days=[]; d=START_DATE; prev=None
        while d<=END_DATE:
            target=int(dt.datetime(d.year,d.month,d.day,tzinfo=dt.timezone.utc).timestamp())
            if prev is None:
                bn=first
            else:
                bn=locate_first_at_or_after(target,prev+5000,min(TO_BLOCK,prev+9000),stats[PRIMARY])
            proof=verify_boundary(bn,target,stats)
            days.append({"date":d.isoformat(),"target_timestamp":target,**proof})
            prev=bn; d+=dt.timedelta(days=1)
        if len(days)!=366: raise RuntimeError(f"expected 366 snapshots, got {len(days)}")
        if len({x["block"] for x in days})!=366: raise RuntimeError("duplicate snapshot block")
        terminal=[]
        for ep in PROVIDERS:
            try: terminal.append((ep,block_tuple(ep,TO_BLOCK,stats[ep])))
            except Exception: pass
        if len(terminal)<2: raise RuntimeError("TO_BLOCK archive quorum<2")
        if len({x[1] for x in terminal})!=1: raise RuntimeError("TO_BLOCK provider disagreement")
        term=terminal[0][1]
        if term[1]>MAX_TS: raise RuntimeError("TO_BLOCK timestamp crossed 2024 ceiling")
        receipt={"lab_id":LAB_ID,"classification":"REPLICATION_CALENDAR_PASS","start_date":START_DATE.isoformat(),"end_date":END_DATE.isoformat(),
                 "snapshot_count":len(days),"snapshots":days,"replication_event_from_block":days[0]["block"],"replication_event_to_block":TO_BLOCK,
                 "terminal_2024_block":{"block":term[0],"timestamp":term[1],"hash":term[2]},
                 "rpc_stats":{k:dict(v) for k,v in stats.items()},
                 "safety":{"opened_2024_predictor":False,"opened_2024_outcomes":False,"opened_2025_or_2026":False,"market_returns_opened":False,"pnl_opened":False,"live_trading":False,"exchange_mutation":False}}
    except Exception as exc:
        receipt={"lab_id":LAB_ID,"classification":"REPLICATION_ACQUISITION_TECHNICAL_FAILURE","failure":f"{type(exc).__name__}: {str(exc)[:1500]}",
                 "rpc_stats":{k:dict(v) for k,v in stats.items()},
                 "safety":{"opened_2024_predictor":False,"opened_2024_outcomes":False,"opened_2025_or_2026":False,"market_returns_opened":False,"pnl_opened":False,"live_trading":False,"exchange_mutation":False}}
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"snapshot_count":receipt.get("snapshot_count"),"from_block":receipt.get("replication_event_from_block"),"to_block":receipt.get("replication_event_to_block")},sort_keys=True))
    return 0 if receipt["classification"]=="REPLICATION_CALENDAR_PASS" else 2
if __name__=="__main__": raise SystemExit(main())

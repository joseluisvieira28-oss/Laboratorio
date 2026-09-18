#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID="STETH-REDEMPTION-BASIS-002"
START_TS=int(datetime(2023,5,16,12,0,0,tzinfo=timezone.utc).timestamp())
END_TS=int(datetime(2024,12,31,12,0,0,tzinfo=timezone.utc).timestamp())
HEADER_CEILING_TS=int(datetime(2024,12,31,23,59,59,tzinfo=timezone.utc).timestamp())
EXPECTED_SNAPSHOTS=596

STETH="0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84".lower()
QUEUE="0x889edC2eDab5f40e902b864aD4d7AdE8E412F9B1".lower()
CURVE="0xDC24316b9AE028F1497c275EB9192a3Ea0f67022".lower()
ACTIVATION_TX="0x592d68a259af899fb435da0ac08c2fd500cb423f37f1d8ce8e3120cb84186b21"
EXPECTED_ACTIVATION_BLOCK=17_266_004

PROVIDERS=[
 "https://eth-mainnet.public.blastapi.io",
 "https://rpc.mevblocker.io",
 "https://ethereum.blinklabs.xyz/",
]
QUORUM=2

SQD="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
TRANSIENT={429,500,502,503,504,529}
HEADER_SEARCH_LO=17_250_000
HEADER_SEARCH_HI=21_525_890
EVENT_SPAN=40_000
SQD_WINDOW=20_000

EVENTS={
 "WithdrawalRequested":(QUEUE,"WithdrawalRequested(uint256,address,address,uint256,uint256)"),
 "WithdrawalsFinalized":(QUEUE,"WithdrawalsFinalized(uint256,uint256,uint256,uint256,uint256)"),
 "WithdrawalClaimed":(QUEUE,"WithdrawalClaimed(uint256,address,address,uint256)"),
 "TokenRebased":(STETH,"TokenRebased(uint256,uint256,uint256,uint256,uint256,uint256,uint256)"),
 "TokenExchange":(CURVE,"TokenExchange(address,int128,uint256,int128,uint256)"),
}

def selector(sig:str)->str:
    return "0x"+keccak(sig.encode())[:4].hex()

def topic(sig:str)->str:
    return "0x"+keccak(sig.encode()).hex()

def enc_i128(x:int)->str:
    return int(x).to_bytes(32,"big",signed=True).hex()

def enc_u256(x:int)->str:
    return int(x).to_bytes(32,"big",signed=False).hex()

def call_data(sig:str,args:list[int])->str:
    h=selector(sig)[2:]
    if sig.startswith("get_dy("):
        h+=enc_i128(args[0])+enc_i128(args[1])+enc_u256(args[2])
    else:
        h+="".join(enc_u256(x) for x in args)
    return "0x"+h

STATE_CALLS={
 "curve_get_dy":(CURVE,"get_dy(int128,int128,uint256)",[0,1,10**19]),
 "curve_fee":(CURVE,"fee()",[]),
 "queue_last_request_id":(QUEUE,"getLastRequestId()",[]),
 "queue_last_finalized_request_id":(QUEUE,"getLastFinalizedRequestId()",[]),
 "queue_unfinalized_steth":(QUEUE,"unfinalizedStETH()",[]),
}

def rpc(ep:str,method:str,params:list[Any],stats:Counter[str],retries:int=3)->dict[str,Any]:
    last=None
    for k in range(retries):
        try:
            r=requests.post(ep,json={"jsonrpc":"2.0","id":1,"method":method,"params":params},
                            timeout=(10,45),headers={"Content-Type":"application/json","User-Agent":LAB_ID+"/source-v0.1"})
            stats["rpc_http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["rpc_transient"]+=1
                r.close(); time.sleep(1.2*(k+1)); continue
            r.raise_for_status(); o=r.json(); r.close()
            if o.get("error") is not None:
                return {"ok":False,"error":str(o["error"])[:240]}
            return {"ok":True,"result":o.get("result")}
        except Exception as e:
            last=e; stats["rpc_errors"]+=1
            if k<retries-1: time.sleep(1.2*(k+1))
    return {"ok":False,"error":f"{type(last).__name__}: {str(last)[:240]}"}

def block_header(ep:str,bn:int,stats:Counter[str])->dict[str,Any]:
    o=rpc(ep,"eth_getBlockByNumber",[hex(bn),False],stats)
    if not o["ok"] or not isinstance(o.get("result"),dict):
        raise RuntimeError(f"block header unavailable {bn}: {o.get('error')}")
    h=o["result"]; ts=int(h["timestamp"],16)
    if ts>HEADER_CEILING_TS:
        raise RuntimeError("PROTECTED_PERIOD_HEADER_REJECTED")
    return h

def map_first_at_or_after(ep:str,target:int,stats:Counter[str])->tuple[int,int,str]:
    lo,hi=HEADER_SEARCH_LO,HEADER_SEARCH_HI
    hlo=block_header(ep,lo,stats); hhi=block_header(ep,hi,stats)
    if int(hlo["timestamp"],16)>target or int(hhi["timestamp"],16)<target:
        raise RuntimeError("timestamp outside frozen header bracket")
    while lo<hi:
        mid=(lo+hi)//2
        h=block_header(ep,mid,stats)
        if int(h["timestamp"],16)<target: lo=mid+1
        else: hi=mid
    h=block_header(ep,lo,stats); prev=block_header(ep,lo-1,stats)
    ts=int(h["timestamp"],16); pts=int(prev["timestamp"],16)
    if ts<target or pts>=target:
        raise RuntimeError("first-block-at-or-after invariant failed")
    return lo,ts,str(h.get("hash","")).lower()

def valid_hex_result(o:dict[str,Any])->bool:
    x=o.get("result")
    return bool(o.get("ok") and isinstance(x,str) and x.startswith("0x") and len(x)>2)

def provider_probe(ep:str,stats:Counter[str])->dict[str,Any]:
    row={"provider":ep}
    chain=rpc(ep,"eth_chainId",[],stats)
    if not valid_hex_result(chain) or int(chain["result"],16)!=1:
        row["fatal"]="wrong/unavailable chainId"; return row

    act=rpc(ep,"eth_getTransactionReceipt",[ACTIVATION_TX],stats)
    if not act.get("ok") or not isinstance(act.get("result"),dict) or not act["result"].get("blockNumber"):
        row["activation_receipt_accessible"]=False
    else:
        row["activation_receipt_accessible"]=True
        row["activation_block"]=int(act["result"]["blockNumber"],16)

    try:
        sb,sts,sh=map_first_at_or_after(ep,START_TS,stats)
        eb,ets,eh=map_first_at_or_after(ep,END_TS,stats)
        row.update({"start_block":sb,"start_timestamp":sts,"start_hash":sh,
                    "end_block":eb,"end_timestamp":ets,"end_hash":eh})
    except Exception as e:
        row["fatal"]=f"timestamp mapping: {type(e).__name__}: {str(e)[:240]}"
        return row

    row["code"]={}
    row["state_calls"]={}
    for label,bn in (("start",row["start_block"]),("end",row["end_block"])):
        row["code"][label]={}
        for name,addr in (("steth",STETH),("queue",QUEUE),("curve",CURVE)):
            o=rpc(ep,"eth_getCode",[addr,hex(bn)],stats)
            x=o.get("result")
            row["code"][label][name]=bool(o.get("ok") and isinstance(x,str) and x not in ("0x","0x0",""))
        row["state_calls"][label]={}
        for name,(addr,sig,args) in STATE_CALLS.items():
            o=rpc(ep,"eth_call",[{"to":addr,"data":call_data(sig,args)},hex(bn)],stats)
            row["state_calls"][label][name]=valid_hex_result(o)
            if not row["state_calls"][label][name] and o.get("error"):
                row["state_calls"][label][name+"_error"]=o["error"]
    return row

def sqd_post(body:dict[str,Any],stats:Counter[str])->requests.Response:
    last=None
    for k in range(8):
        try:
            r=requests.post(SQD,json=body,stream=True,timeout=(20,180),
                            headers={"Content-Type":"application/json","Accept-Encoding":"gzip","User-Agent":LAB_ID+"/sqd-source-v0.1"})
            stats["sqd_http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["sqd_transient"]+=1; r.close(); time.sleep(min(20,1.5*(2**k))); continue
            r.raise_for_status(); return r
        except Exception as e:
            last=e; stats["sqd_errors"]+=1
            if k<7: time.sleep(min(20,1.5*(2**k)))
    raise RuntimeError(str(last))

def sqd_event_window(address:str,topic0:str,start:int,end:int,stats:Counter[str])->list[dict[str,Any]]:
    cursor=start; out=[]; seen=set()
    while cursor<=end:
        rt=min(end,cursor+SQD_WINDOW-1)
        body={"type":"evm","fromBlock":cursor,"toBlock":rt,
              "fields":{"block":{"number":True,"timestamp":True},
                        "log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}},
              "logs":[{"address":[address],"topic0":[topic0]}]}
        r=sqd_post(body,stats); page_last=None; rows=0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                obj=json.loads(raw)
                if isinstance(obj,dict) and obj.get("error"):
                    raise RuntimeError(f"SQD error {obj['error']}")
                h=obj.get("header") or obj.get("block") or {}
                bn=int(h["number"]); ts=int(h["timestamp"])
                if not (cursor<=bn<=rt): raise RuntimeError("SQD row outside request")
                if page_last is not None and bn<page_last: raise RuntimeError("SQD non-monotonic")
                page_last=bn; rows+=1
                if ts>HEADER_CEILING_TS: raise RuntimeError("protected-period SQD timestamp")
                for log in obj.get("logs") or []:
                    tx=str(log.get("transactionHash","")).lower()
                    li=log.get("logIndex")
                    li=int(li,16) if isinstance(li,str) and li.startswith("0x") else int(li)
                    key=(tx,li)
                    if not tx or key in seen: raise RuntimeError("missing/duplicate canonical log identity")
                    seen.add(key)
                    out.append({"block":bn,"timestamp":ts,"transactionHash":tx,"logIndex":li,
                                "address":str(log.get("address","")).lower(),
                                "topic0":str((log.get("topics") or [""])[0]).lower()})
        finally:
            r.close()
        stats["sqd_windows"]+=1; stats["sqd_rows"]+=rows
        if page_last is None:
            stats["sqd_empty_windows"]+=1; cursor=rt+1
        else:
            cursor=page_last+1
    return out

def identity_digest(rows:list[dict[str,Any]])->str:
    return hashlib.sha256("\n".join(
        f"{r['block']}|{r['transactionHash']}|{r['logIndex']}|{r['address']}|{r['topic0']}"
        for r in sorted(rows,key=lambda x:(x["block"],x["transactionHash"],x["logIndex"]))
    ).encode()).hexdigest()

def main()->int:
    stats=Counter(); provider_rows=[]
    for ep in PROVIDERS:
        try: provider_rows.append(provider_probe(ep,stats))
        except Exception as e: provider_rows.append({"provider":ep,"fatal":f"{type(e).__name__}: {str(e)[:300]}"})

    activation_blocks=[r.get("activation_block") for r in provider_rows if r.get("activation_receipt_accessible")]
    start_blocks=[r.get("start_block") for r in provider_rows if r.get("start_block") is not None]
    end_blocks=[r.get("end_block") for r in provider_rows if r.get("end_block") is not None]
    activation_ok=len(activation_blocks)>=QUORUM and len(set(activation_blocks))==1 and activation_blocks[0]==EXPECTED_ACTIVATION_BLOCK
    start_ok=len(start_blocks)>=QUORUM and len(set(start_blocks))==1
    end_ok=len(end_blocks)>=QUORUM and len(set(end_blocks))==1

    failure=None; classification=None
    if not activation_ok or not start_ok or not end_ok:
        classification="PROVENANCE_FAILURE"
        failure="activation or edge timestamp mapping quorum failed"
    else:
        start_block=start_blocks[0]; end_block=end_blocks[0]
        if start_block<=EXPECTED_ACTIVATION_BLOCK:
            classification="PROVENANCE_FAILURE"; failure="first frozen snapshot does not postdate activation block"
        else:
            code_quorum=True; call_quorum=True
            for edge in ("start","end"):
                for name in ("steth","queue","curve"):
                    if sum(1 for r in provider_rows if (r.get("code") or {}).get(edge,{}).get(name))<QUORUM:
                        code_quorum=False
                for name in STATE_CALLS:
                    if sum(1 for r in provider_rows if (r.get("state_calls") or {}).get(edge,{}).get(name))<QUORUM:
                        call_quorum=False
            if not code_quorum:
                classification="PROVENANCE_FAILURE"; failure="historical bytecode quorum failed"
            elif not call_quorum:
                classification="SOURCE_ACQUISITION_TECHNICAL_FAILURE"; failure="historical state-call quorum failed"
            else:
                event_receipts={}
                try:
                    ranges=[(start_block,min(end_block,start_block+EVENT_SPAN)),
                            (max(start_block,end_block-EVENT_SPAN),end_block)]
                    for name,(addr,sig) in EVENTS.items():
                        all_rows=[]
                        for a,b in ranges:
                            all_rows.extend(sqd_event_window(addr,topic(sig),a,b,stats))
                        dedup={(x["transactionHash"],x["logIndex"]):x for x in all_rows}
                        rows=list(dedup.values())
                        event_receipts[name]={"count":len(rows),"identity_sha256":identity_digest(rows)}
                    missing=[k for k,v in event_receipts.items() if int(v["count"])<1]
                    if missing:
                        classification="INSUFFICIENT_SOURCE_COVERAGE"; failure="zero bounded source logs for "+",".join(missing)
                    else:
                        classification="SOURCE_DATA_PASS"; failure=None
                except Exception as e:
                    classification="SOURCE_ACQUISITION_TECHNICAL_FAILURE"
                    failure=f"SQD bounded event acquisition: {type(e).__name__}: {str(e)[:500]}"
                    event_receipts={}
    receipt={
      "lab_id":LAB_ID,
      "phase":"SOURCE_GATE_V0_1_OUTCOME_BLIND",
      "classification":classification,
      "failure":failure,
      "frozen_first_snapshot_utc":"2023-05-16T12:00:00Z",
      "frozen_last_snapshot_utc":"2024-12-31T12:00:00Z",
      "expected_daily_snapshot_population":EXPECTED_SNAPSHOTS,
      "expected_activation_block":EXPECTED_ACTIVATION_BLOCK,
      "provider_count":len(PROVIDERS),
      "quorum_required":QUORUM,
      "activation_quorum_pass":activation_ok,
      "start_mapping_quorum_pass":start_ok,
      "end_mapping_quorum_pass":end_ok,
      "agreed_start_block":start_blocks[0] if start_ok else None,
      "agreed_end_block":end_blocks[0] if end_ok else None,
      "provider_receipts":provider_rows,
      "bounded_event_receipts":locals().get("event_receipts",{}),
      "transport_stats":dict(stats),
      "safety":{
        "state_values_printed_or_interpreted":False,
        "event_payloads_decoded":False,
        "market_prices_opened":False,
        "returns_opened":False,
        "pnl_opened":False,
        "accessed_2025_or_2026":False,
        "live_trading":False,
        "exchange_mutation":False
      }
    }
    out=Path("out/steth_redemption_basis_002"); out.mkdir(parents=True,exist_ok=True)
    p=out/"STETH_REDEMPTION_BASIS_002_SOURCE_GATE_V0_1.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({
      "classification":classification,
      "start_block":receipt["agreed_start_block"],
      "end_block":receipt["agreed_end_block"],
      "event_counts":{k:v["count"] for k,v in receipt["bounded_event_receipts"].items()},
      "market_prices_opened":False,"returns_opened":False,"pnl_opened":False
    },sort_keys=True))
    return 0 if classification=="SOURCE_DATA_PASS" else 2

if __name__=="__main__":
    raise SystemExit(main())

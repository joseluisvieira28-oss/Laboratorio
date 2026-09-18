#!/usr/bin/env python3
"""Open only the frozen 2023 Aave LiquidationCall outcome after predictor persistence."""
from __future__ import annotations

import bisect
import json
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
PORTAL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL="0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
INITIAL_ORACLE="0x54586be62e3c3580375ae3723c145253060ca0c2"
WINDOW=75_000
TRANSIENT={429,500,502,503,504,529}
RPC_ENDPOINTS=[
    "https://eth-mainnet.public.blastapi.io",
    "https://rpc.mevblocker.io",
    "https://ethereum.blinklabs.xyz/",
]
T_LIQ="0x"+keccak(b"LiquidationCall(address,address,address,uint256,uint256,address,bool)").hex()
SEL_PRICE=keccak(b"getAssetPrice(address)")[:4].hex()


def as_int(v:Any)->int:
    if isinstance(v,int): return v
    if isinstance(v,str): return int(v,16) if v.startswith("0x") else int(v)
    raise TypeError("bad integer")


def taddr(t:str)->str:
    t=str(t).lower()
    if not t.startswith("0x") or len(t)!=66: raise ValueError("bad indexed address")
    return "0x"+t[-40:]


def words(data:str,n:int)->list[int]:
    h=str(data)[2:] if str(data).startswith("0x") else ""
    if len(h)<64*n or len(h)%64: raise ValueError("bad ABI data")
    return [int(h[i*64:(i+1)*64],16) for i in range(n)]


def calldata(selector:str,addr:str)->str:
    return "0x"+selector+"0"*24+addr[2:]


def load_one(root:str,classification:str)->dict[str,Any]:
    xs=[]
    for p in Path(root).rglob("*.json"):
        o=json.loads(p.read_text())
        if o.get("classification")==classification: xs.append(o)
    if len(xs)!=1: raise RuntimeError(f"expected one {classification} under {root}, got {len(xs)}")
    return xs[0]


def post_portal(body:dict[str,Any],stats:Counter[str])->requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,
                headers={"Content-Type":"application/json","Accept-Encoding":"gzip",
                         "User-Agent":f"{LAB_ID}/discovery-outcomes-v0.1"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["transient_retries"]+=1; r.close()
                if attempt<7: time.sleep(min(20.0,1.5*(2**attempt))); continue
            r.raise_for_status(); stats["successful_http_responses"]+=1; return r
        except Exception as exc:
            last=exc; stats["network_errors"]+=1
            if attempt<7: time.sleep(min(20.0,1.5*(2**attempt))); continue
    raise RuntimeError(str(last))


def stream(start:int,end:int,stats:Counter[str]):
    cursor=start
    while cursor<=end:
        rt=min(end,cursor+WINDOW-1)
        body={"type":"evm","fromBlock":cursor,"toBlock":rt,
              "fields":{"block":{"number":True,"timestamp":True},
                        "log":{"address":True,"topics":True,"data":True,
                               "transactionHash":True,"logIndex":True}},
              "logs":[{"address":[POOL],"topic0":[T_LIQ]}]}
        page=None; page_last=None
        for attempt in range(8):
            r=post_portal(body,stats); local=[]; last=None
            try:
                for raw in r.iter_lines(decode_unicode=True):
                    if not raw: continue
                    obj=json.loads(raw)
                    if isinstance(obj,dict) and obj.get("error"): raise RuntimeError(str(obj["error"]))
                    h=obj.get("header") or obj.get("block") or {}; bn=int(h["number"])
                    if not(cursor<=bn<=rt): raise RuntimeError("row outside window")
                    if last is not None and bn<last: raise RuntimeError("non-monotonic page")
                    last=bn; local.append(obj)
            except requests.RequestException:
                stats["stream_read_failures"]+=1; r.close()
                if attempt<7:
                    stats["stream_read_retries"]+=1
                    time.sleep(min(20.0,1.5*(2**attempt))); continue
                raise
            finally:
                r.close()
            page=local; page_last=last; stats["stream_window_successes"]+=1; break
        if page is None: raise RuntimeError("stream retry budget exhausted")
        stats["portal_rows"]+=len(page)
        for obj in page: yield obj
        if page_last is None:
            cursor=rt+1; stats["empty_windows"]+=1
        else:
            cursor=page_last+1


def rpc_batch(endpoint:str,items:list[dict[str,Any]],stats:Counter[str])->dict[int,int]:
    out={}; session=requests.Session()
    headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/discovery-outcomes-v0.1"}
    for start in range(0,len(items),40):
        chunk=items[start:start+40]
        payload=[{"jsonrpc":"2.0","id":i,"method":"eth_call",
                  "params":[{"to":x["to"],"data":x["data"]},hex(int(x["block"]))]}
                 for i,x in enumerate(chunk,start=start)]
        resp=None
        for attempt in range(4):
            try:
                r=session.post(endpoint,json=payload,headers=headers,timeout=(10,45))
                stats["http_attempts"]+=1
                if r.status_code in TRANSIENT:
                    stats["transient_retries"]+=1; r.close(); time.sleep(1.5*(attempt+1)); continue
                r.raise_for_status(); resp=r.json(); r.close(); break
            except Exception:
                stats["errors"]+=1
                if attempt<3: time.sleep(1.5*(attempt+1))
        if not isinstance(resp,list):
            stats["failed_batches"]+=1; continue
        byid={x.get("id"):x for x in resp if isinstance(x,dict)}
        for i in range(start,start+len(chunk)):
            o=byid.get(i)
            if not o or o.get("error") is not None:
                stats["rpc_errors"]+=1; continue
            v=o.get("result")
            if not isinstance(v,str) or not v.startswith("0x"):
                stats["invalid"]+=1; continue
            try:
                out[i]=int(v,16); stats["usable"]+=1
            except ValueError:
                stats["invalid"]+=1
    session.close(); return out


def main()->int:
    out=Path("discovery_outcome_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_DISCOVERY_OUTCOME_2023_V0_1.json"
    transport=Counter(); rpcstats={ep:Counter() for ep in RPC_ENDPOINTS}
    try:
        pred=load_one("downloaded_discovery_predictor","DISCOVERY_PREDICTOR_PASS")
        cal=load_one("downloaded_discovery_calendar","DISCOVERY_CALENDAR_PASS")
        glob=load_one("downloaded_discovery_global","DISCOVERY_GLOBAL_SOURCE_PASS")
        days=pred["daily_predictor"]; snaps=cal["snapshots"]
        if len(days)!=334 or len(snaps)!=334: raise RuntimeError("predictor/calendar count mismatch")
        if any(x["date"]!=snaps[i]["date"] for i,x in enumerate(days)): raise RuntimeError("predictor/calendar date mismatch")
        decimals={k.lower():int(v) for k,v in pred["reserve_decimals"].items()}
        blocks=[int(x["block"]) for x in snaps]
        start_block=blocks[0]; end_block=int(cal["discovery_event_to_block"])

        oracle_events=sorted(glob.get("oracle_update_events") or [],key=lambda x:(int(x["block"]),int(x["logIndex"])))
        oracle_blocks=[int(x["block"]) for x in oracle_events]
        oracle_values=[str(x["new"]).lower() for x in oracle_events]

        def oracle_at(bn:int)->str:
            j=bisect.bisect_right(oracle_blocks,bn)-1
            return oracle_values[j] if j>=0 else INITIAL_ORACLE

        events=[]; seen=set()
        for obj in stream(start_block,end_block,transport):
            h=obj.get("header") or obj.get("block") or {}; bn=int(h["number"]); ts=int(h["timestamp"])
            if ts>=1704067200: raise RuntimeError("2024 liquidation outcome opened")
            for log in sorted(obj.get("logs") or [],key=lambda x:as_int(x.get("logIndex"))):
                topics=[str(x).lower() for x in (log.get("topics") or [])]
                if len(topics)<4 or topics[0]!=T_LIQ: raise RuntimeError("LiquidationCall ABI")
                tx=str(log.get("transactionHash","")).lower(); li=as_int(log.get("logIndex"))
                key=(tx,li)
                if key in seen: raise RuntimeError("duplicate liquidation log")
                seen.add(key)
                collateral=taddr(topics[1]); debt=taddr(topics[2]); user=taddr(topics[3])
                if debt not in decimals or collateral not in decimals:
                    raise RuntimeError(f"liquidation reserve outside canonical 37: debt={debt} collateral={collateral}")
                w=words(log.get("data",""),4)
                debt_to_cover=w[0]; collateral_amount=w[1]
                events.append({
                    "block":bn,"timestamp":ts,"tx":tx,"logIndex":li,
                    "collateral":collateral,"debt":debt,"user":user,
                    "debtToCover":debt_to_cover,"collateralAmount":collateral_amount,
                    "oracle":oracle_at(bn),
                })

        # Deduplicate historical price targets.
        price_keys=[]; key_to_index={}
        for e in events:
            for asset in (e["debt"],e["collateral"]):
                k=(int(e["block"]),str(e["oracle"]).lower(),asset)
                if k not in key_to_index:
                    key_to_index[k]=len(price_keys)
                    price_keys.append(k)
        targets=[{"block":b,"to":oracle,"data":calldata(SEL_PRICE,asset)}
                 for b,oracle,asset in price_keys]
        vals_by_ep={}
        for ep in RPC_ENDPOINTS:
            vals_by_ep[ep]=rpc_batch(ep,targets,rpcstats[ep])
        prices={}
        for i,k in enumerate(price_keys):
            vals={ep:m[i] for ep,m in vals_by_ep.items() if i in m}
            if len(vals)<2: raise RuntimeError(f"liquidation price quorum<2 for {k}")
            if len(set(vals.values()))!=1: raise RuntimeError(f"liquidation price disagreement for {k}: {vals}")
            v=next(iter(vals.values()))
            if v<=0: raise RuntimeError(f"nonpositive liquidation oracle price for {k}")
            prices[k]=v

        daily=[{
            "date":x["date"],"snapshot_block":int(x["snapshot_block"]),
            "next24h_liquidation_debt_notional":"0",
            "liquidation_event_count":0,
            "liquidated_borrower_count":0,
            "collateral_seized_oracle_notional":"0",
        } for x in days]
        borrowers=[set() for _ in daily]
        debt_sums=[0]*len(daily); coll_sums=[0]*len(daily); event_counts=[0]*len(daily)
        excluded_snapshot_block_events=0

        for e in events:
            bn=int(e["block"])
            di=bisect.bisect_right(blocks,bn)-1
            if di<0: continue
            if bn==blocks[di]:
                excluded_snapshot_block_events+=1
                continue
            if di>=len(daily): continue
            if di<len(blocks)-1 and bn>=blocks[di+1]:
                raise RuntimeError("outcome assignment crossed next snapshot")
            debt_price=prices[(bn,e["oracle"],e["debt"])]
            coll_price=prices[(bn,e["oracle"],e["collateral"])]
            debt_sums[di]+=int(e["debtToCover"])*debt_price//(10**decimals[e["debt"]])
            coll_sums[di]+=int(e["collateralAmount"])*coll_price//(10**decimals[e["collateral"]])
            event_counts[di]+=1; borrowers[di].add(e["user"])

        for i,row in enumerate(daily):
            row["next24h_liquidation_debt_notional"]=str(debt_sums[i])
            row["liquidation_event_count"]=event_counts[i]
            row["liquidated_borrower_count"]=len(borrowers[i])
            row["collateral_seized_oracle_notional"]=str(coll_sums[i])

        receipt={
            "lab_id":LAB_ID,
            "classification":"DISCOVERY_OUTCOME_PASS",
            "predictor_sha256":pred["predictor_sha256"],
            "snapshot_count":len(daily),
            "liquidation_log_count":len(events),
            "excluded_snapshot_block_liquidation_events":excluded_snapshot_block_events,
            "positive_outcome_days":sum(1 for x in daily if int(x["next24h_liquidation_debt_notional"])>0),
            "daily_outcome":daily,
            "unique_price_target_count":len(price_keys),
            "transport_stats":dict(transport),
            "archive_rpc_stats":{ep:dict(s) for ep,s in rpcstats.items()},
            "safety":{
                "future_liquidation_outcomes_opened":True,
                "opened_2024_predictor":False,"opened_2024_outcomes":False,
                "opened_2025_or_2026":False,
                "market_returns_opened":False,"pnl_opened":False,
                "live_trading":False,"exchange_mutation":False,
            },
        }
    except Exception as exc:
        klass="DISCOVERY_PROVENANCE_FAILURE" if "disagreement" in str(exc) or "outside canonical" in str(exc) or "2024" in str(exc) else "DISCOVERY_ACQUISITION_TECHNICAL_FAILURE"
        receipt={
            "lab_id":LAB_ID,"classification":klass,
            "failure":f"{type(exc).__name__}: {str(exc)[:1600]}",
            "transport_stats":dict(transport),
            "archive_rpc_stats":{ep:dict(s) for ep,s in rpcstats.items()},
            "safety":{"future_liquidation_outcomes_opened":True,
                      "opened_2024_predictor":False,"opened_2024_outcomes":False,
                      "opened_2025_or_2026":False,"market_returns_opened":False,
                      "pnl_opened":False,"live_trading":False,"exchange_mutation":False},
        }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],
                      "liquidation_logs":receipt.get("liquidation_log_count"),
                      "positive_outcome_days":receipt.get("positive_outcome_days"),
                      "price_targets":receipt.get("unique_price_target_count"),
                      "opened_2024_outcomes":False,"market_returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if receipt["classification"]=="DISCOVERY_OUTCOME_PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())

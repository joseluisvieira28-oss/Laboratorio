#!/usr/bin/env python3
"""2024-only global/eMode/oracle replay for AAVE-LIQUIDATION-OVERHANG-001 replication."""
from __future__ import annotations

import json
import time
from collections import Counter
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
PORTAL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL="0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
CONFIGURATOR="0x64b761d848206f447fe2dd461b0c635ec39ebb27"
PROVIDER="0x2f39d218133afab8f2b819b1066c7e434ad94e9e"
INITIAL_ORACLE="0x54586be62e3c3580375ae3723c145253060ca0c2"
FROM_BLOCK=16_490_000
WINDOW=75_000
TRANSIENT={429,500,502,503,504,529}
RPC_ENDPOINTS=[
    "https://eth-mainnet.public.blastapi.io",
    "https://rpc.mevblocker.io",
    "https://ethereum.blinklabs.xyz/",
]


def topic(sig:str)->str: return "0x"+keccak(sig.encode()).hex()
T_USER_EMODE=topic("UserEModeSet(address,uint8)")
T_EMODE_ADDED=topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)")
T_PRICE_ORACLE_UPDATED=topic("PriceOracleUpdated(address,address)")
T_POOL_UPDATED=topic("PoolUpdated(address,address)")
T_CONFIG_UPDATED=topic("PoolConfiguratorUpdated(address,address)")
T_BORROW=topic("Borrow(address,address,address,uint256,uint8,uint256,uint16)")
GET_PRICE_ORACLE_SELECTOR="0x"+keccak(b"getPriceOracle()")[:4].hex()


def as_int(v:Any)->int:
    if isinstance(v,int): return v
    if isinstance(v,str): return int(v,16) if v.startswith("0x") else int(v)
    raise TypeError("bad int")


def taddr(t:str)->str:
    t=str(t).lower()
    if not t.startswith("0x") or len(t)!=66: raise ValueError("bad indexed address")
    return "0x"+t[-40:]


def words(data:str,n:int)->list[int]:
    h=str(data)[2:] if str(data).startswith("0x") else ""
    if len(h)<64*n or len(h)%64: raise ValueError("bad ABI data")
    return [int(h[i*64:(i+1)*64],16) for i in range(n)]


def post_portal(body:dict[str,Any],stats:Counter[str])->requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,
                headers={"Content-Type":"application/json","Accept-Encoding":"gzip",
                         "User-Agent":f"{LAB_ID}/replication-global-v0.1"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                stats["transient_retries"]+=1; r.close()
                if attempt<7: time.sleep(min(20.0,1.5*(2**attempt))); continue
            r.raise_for_status(); stats["successful_http_responses"]+=1; return r
        except Exception as exc:
            last=exc; stats["network_errors"]+=1
            if attempt<7: time.sleep(min(20.0,1.5*(2**attempt))); continue
    raise RuntimeError(str(last))


def stream(start:int,end:int,filters:list[dict[str,Any]],stats:Counter[str]):
    cursor=start
    while cursor<=end:
        rt=min(end,cursor+WINDOW-1)
        body={"type":"evm","fromBlock":cursor,"toBlock":rt,
              "fields":{"block":{"number":True,"timestamp":True},
                        "log":{"address":True,"topics":True,"data":True,
                               "transactionHash":True,"logIndex":True}},
              "logs":filters}
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
                stats["stream_read_failures"]+=1
                r.close()
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


def rpc_batch(endpoint:str,items:list[dict[str,Any]],stats:Counter[str])->dict[int,str]:
    out={}; session=requests.Session()
    headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/replication-global-v0.1"}
    for start in range(0,len(items),50):
        chunk=items[start:start+50]
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
            if not o or o.get("error") is not None: stats["rpc_errors"]+=1; continue
            v=o.get("result")
            if isinstance(v,str) and v.startswith("0x"):
                out[i]=v.lower(); stats["usable"]+=1
    session.close(); return out


def decode_address_result(v:str)->str:
    h=v[2:]
    if len(h)<64: raise ValueError("short address result")
    return "0x"+h[-40:]


def main()->int:
    out=Path("replication_global_output"); out.mkdir(parents=True,exist_ok=True)
    dst=out/"AAVE_LIQUIDATION_OVERHANG_001_REPLICATION_GLOBAL_2024_V0_1.json"
    transport=Counter(); rpcstats={ep:Counter() for ep in RPC_ENDPOINTS}
    try:
        cal_files=list(Path("downloaded_replication_calendar").rglob("*.json"))
        if len(cal_files)!=1: raise RuntimeError("expected exactly one calendar receipt")
        cal=json.loads(cal_files[0].read_text())
        if cal.get("classification")!="REPLICATION_CALENDAR_PASS": raise RuntimeError("calendar not PASS")
        snaps=cal["snapshots"]; to_block=int(cal["replication_state_to_block"])

        filters=[
            {"address":[POOL],"topic0":[T_USER_EMODE,T_BORROW]},
            {"address":[CONFIGURATOR],"topic0":[T_EMODE_ADDED]},
            {"address":[PROVIDER],"topic0":[T_PRICE_ORACLE_UPDATED,T_POOL_UPDATED,T_CONFIG_UPDATED]},
        ]
        user_events=[]; category_events=[]; oracle_events=[]
        provider_events=[]; borrow_mode_counts=Counter(); seen=set()
        for obj in stream(FROM_BLOCK,to_block,filters,transport):
            h=obj.get("header") or obj.get("block") or {}; bn=int(h["number"])
            for log in sorted(obj.get("logs") or [],key=lambda x:as_int(x.get("logIndex"))):
                addr=str(log.get("address","")).lower()
                topics=[str(x).lower() for x in (log.get("topics") or [])]
                if not topics: raise RuntimeError("log without topic0")
                t0=topics[0]; tx=str(log.get("transactionHash","")).lower(); li=as_int(log.get("logIndex"))
                key=(tx,li)
                if key in seen: raise RuntimeError("duplicate canonical global log")
                seen.add(key)
                if addr==POOL and t0==T_USER_EMODE:
                    if len(topics)<2: raise RuntimeError("UserEModeSet ABI")
                    cid=words(log.get("data",""),1)[0]
                    user_events.append({"block":bn,"logIndex":li,"user":taddr(topics[1]),"category":cid})
                elif addr==POOL and t0==T_BORROW:
                    w=words(log.get("data",""),4)
                    mode=int(w[2])
                    borrow_mode_counts[str(mode)]+=1
                elif addr==CONFIGURATOR and t0==T_EMODE_ADDED:
                    if len(topics)<2: raise RuntimeError("EModeCategoryAdded ABI")
                    cid=as_int(topics[1]); w=words(log.get("data",""),4)
                    category_events.append({
                        "block":bn,"logIndex":li,"category":cid,
                        "ltv":w[0],"liquidationThreshold":w[1],
                        "liquidationBonus":w[2],
                        "oracle":"0x"+format(w[3],"040x")[-40:],
                    })
                elif addr==PROVIDER and t0==T_PRICE_ORACLE_UPDATED:
                    if len(topics)<3: raise RuntimeError("PriceOracleUpdated ABI")
                    oracle_events.append({"block":bn,"logIndex":li,"old":taddr(topics[1]),"new":taddr(topics[2])})
                elif addr==PROVIDER and t0 in (T_POOL_UPDATED,T_CONFIG_UPDATED):
                    if len(topics)<3: raise RuntimeError("provider address update ABI")
                    provider_events.append({
                        "block":bn,"logIndex":li,
                        "event":"PoolUpdated" if t0==T_POOL_UPDATED else "PoolConfiguratorUpdated",
                        "old":taddr(topics[1]),"new":taddr(topics[2]),
                    })
                else:
                    raise RuntimeError("unexpected global event")

        if any(int(k)!=2 for k,v in borrow_mode_counts.items() if int(v)>0):
            raise RuntimeError(f"stable/non-variable Borrow mode observed: {dict(borrow_mode_counts)}")

        # PoolUpdated / PoolConfiguratorUpdated identify implementation transitions
        # behind the stable canonical proxies. R1 already proved the proxy/source
        # lineage; retain these events as diagnostics without misclassifying their
        # implementation addresses as proxy escapes.

        oracle_events.sort(key=lambda z:(z["block"],z["logIndex"]))
        daily_oracle=[]; current=INITIAL_ORACLE; oi=0
        for s in snaps:
            b=int(s["block"])
            while oi<len(oracle_events) and oracle_events[oi]["block"]<=b:
                current=oracle_events[oi]["new"]; oi+=1
            daily_oracle.append({"date":s["date"],"block":b,"oracle":current})

        # Cross-check getPriceOracle() at every frozen daily snapshot.
        targets=[{"block":x["block"],"to":PROVIDER,"data":GET_PRICE_ORACLE_SELECTOR} for x in daily_oracle]
        vals_by_ep={}
        for ep in RPC_ENDPOINTS:
            vals_by_ep[ep]=rpc_batch(ep,targets,rpcstats[ep])
        for i,row in enumerate(daily_oracle):
            vals={}
            for ep,m in vals_by_ep.items():
                if i in m:
                    vals[ep]=decode_address_result(m[i])
            if len(vals)<2: raise RuntimeError(f"price-oracle quorum<2 on {row['date']}")
            if len(set(vals.values()))!=1: raise RuntimeError(f"price-oracle disagreement on {row['date']}: {vals}")
            actual=next(iter(vals.values()))
            if actual!=row["oracle"]:
                raise RuntimeError(f"oracle replay mismatch on {row['date']}: replay={row['oracle']} rpc={actual}")
            row["usable_provider_count"]=len(vals)

        nonzero_category_oracles=sorted({
            e["oracle"] for e in category_events
            if int(e["category"])!=0 and int(e["oracle"],16)!=0
        })
        if nonzero_category_oracles:
            raise RuntimeError(f"nonzero eMode category price source requires explicit implementation: {nonzero_category_oracles}")

        receipt={
            "lab_id":LAB_ID,
            "classification":"REPLICATION_GLOBAL_SOURCE_PASS",
            "frozen_from_block":FROM_BLOCK,
            "frozen_to_block":to_block,
            "snapshot_count":len(snaps),
            "borrow_mode_counts":dict(sorted(borrow_mode_counts.items())),
            "user_emode_events":user_events,
            "emode_category_events":category_events,
            "oracle_update_events":oracle_events,
            "provider_update_events":provider_events,
            "daily_oracle":daily_oracle,
            "nonzero_emode_category_oracles":nonzero_category_oracles,
            "canonical_log_count":len(seen),
            "transport_stats":dict(transport),
            "archive_rpc_stats":{ep:dict(s) for ep,s in rpcstats.items()},
            "safety":{
                "predictor_computed":False,"future_liquidation_outcomes_opened":False,
                "opened_2024_predictor":False,"opened_2024_outcomes":False,"opened_2025_or_2026":False,
                "market_returns_opened":False,"pnl_opened":False,
                "live_trading":False,"exchange_mutation":False,
            },
        }
    except Exception as exc:
        klass="REPLICATION_PROVENANCE_FAILURE" if "stable/non-variable" in str(exc) or "escaped frozen" in str(exc) or "category price source" in str(exc) or "oracle replay mismatch" in str(exc) or "disagreement" in str(exc) else "REPLICATION_ACQUISITION_TECHNICAL_FAILURE"
        receipt={
            "lab_id":LAB_ID,"classification":klass,
            "failure":f"{type(exc).__name__}: {str(exc)[:1500]}",
            "transport_stats":dict(transport),
            "archive_rpc_stats":{ep:dict(s) for ep,s in rpcstats.items()},
            "safety":{"predictor_computed":False,"future_liquidation_outcomes_opened":False,
                      "opened_2024_predictor":False,"opened_2024_outcomes":False,"opened_2025_or_2026":False,
                      "market_returns_opened":False,"pnl_opened":False,
                      "live_trading":False,"exchange_mutation":False},
        }
    dst.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],
                      "borrow_mode_counts":receipt.get("borrow_mode_counts"),
                      "user_emode_events":len(receipt.get("user_emode_events",[])),
                      "category_events":len(receipt.get("emode_category_events",[])),
                      "daily_oracles":len(receipt.get("daily_oracle",[]))},sort_keys=True))
    return 0 if receipt["classification"]=="REPLICATION_GLOBAL_SOURCE_PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())

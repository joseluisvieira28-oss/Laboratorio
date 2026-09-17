#!/usr/bin/env python3
"""Global R1 state/provenance gate for AAVE-LIQUIDATION-OVERHANG-001.

Must run only after the deterministic scaled-ledger audit passes. Reconstructs
eMode configuration/user state, provider implementation/oracle transitions, oracle
source-mapping history, and validates historical Aave oracle prices at the four
frozen audit blocks. No HF, overhang, future outcomes, returns or PnL.
"""
from __future__ import annotations

import json
import os
import sys
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
TO_BLOCK=21_525_890
AUDIT_BLOCKS=[17_748_972,19_007_945,20_266_917,21_525_890]
WINDOW=75_000
TRANSIENT={429,500,502,503,504,529}
RPC_ENDPOINTS=["https://ethereum-rpc.publicnode.com","https://eth.drpc.org","https://1rpc.io/eth","https://eth.llamarpc.com","https://rpc.ankr.com/eth"]


def topic(sig:str)->str: return "0x"+keccak(sig.encode()).hex()
T_USER_EMODE=topic("UserEModeSet(address,uint8)")
T_EMODE_ADDED=topic("EModeCategoryAdded(uint8,uint256,uint256,uint256,address,string)")
T_POOL_UPDATED=topic("PoolUpdated(address,address)")
T_CONFIG_UPDATED=topic("PoolConfiguratorUpdated(address,address)")
T_ORACLE_UPDATED=topic("PriceOracleUpdated(address,address)")
T_ASSET_SOURCE=topic("AssetSourceUpdated(address,address)")
T_FALLBACK=topic("FallbackOracleUpdated(address)")
T_BASE=topic("BaseCurrencySet(address,uint256)")
PRICE_SELECTOR=keccak(b"getAssetPrice(address)")[:4].hex()


def as_int(v:Any)->int:
    if isinstance(v,int): return v
    if isinstance(v,str): return int(v,16) if v.startswith("0x") else int(v)
    raise TypeError("bad int")

def taddr(t:str)->str:
    t=str(t).lower()
    if len(t)!=66: raise ValueError("bad topic address")
    return "0x"+t[-40:]

def words(data:str,n:int)->list[int]:
    s=str(data); h=s[2:] if s.startswith("0x") else ""
    if len(h)<64*n or len(h)%64: raise ValueError("bad ABI data")
    return [int(h[i*64:(i+1)*64],16) for i in range(n)]

def post(body:dict[str,Any],stats:Counter[str])->requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,headers={"Content-Type":"application/json","Accept-Encoding":"gzip","User-Agent":f"{LAB_ID}/r1-global-v0.1"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                last=RuntimeError(f"transient HTTP {r.status_code}"); r.close()
                if attempt<7:
                    stats["transient_retries"]+=1; time.sleep(min(20.0,1.5*(2**attempt))); continue
                raise last
            r.raise_for_status(); stats["successful_http_responses"]+=1; return r
        except (requests.RequestException,RuntimeError) as exc:
            last=exc
            if attempt<7:
                stats["network_retries"]+=1; time.sleep(min(20.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def stream(start:int,end:int,filters:list[dict[str,Any]],stats:Counter[str]):
    cursor=start
    while cursor<=end:
        rt=min(end,cursor+WINDOW-1)
        body={"type":"evm","fromBlock":cursor,"toBlock":rt,
              "fields":{"block":{"number":True,"timestamp":True},"log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}},"logs":filters}
        r=post(body,stats); last=None; rows=0
        try:
            for raw in r.iter_lines(decode_unicode=True):
                if not raw: continue
                obj=json.loads(raw)
                if isinstance(obj,dict) and obj.get("error"): raise RuntimeError(f"portal error: {obj['error']}")
                h=obj.get("header") or obj.get("block") or {}; bn=int(h["number"])
                if not(cursor<=bn<=rt): raise RuntimeError("row outside window")
                if last is not None and bn<last: raise RuntimeError("non-monotonic page")
                last=bn; rows+=1; yield obj
        finally: r.close()
        stats["portal_rows"]+=rows
        if rows==0 or last is None: cursor=rt+1; stats["empty_windows"]+=1
        else: cursor=last+1

def load(root:str,classification:str)->dict[str,Any]:
    for p in Path(root).rglob("*.json"):
        o=json.loads(p.read_text(encoding="utf-8"))
        if o.get("classification")==classification: return o
    raise FileNotFoundError(f"{classification} not found")

def rpc_batches(endpoint:str,targets:list[dict[str,Any]],stats:Counter[str])->dict[int,int]:
    out={}; session=requests.Session(); headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/r1-global-v0.1"}
    for start in range(0,len(targets),40):
        chunk=targets[start:start+40]; payload=[]
        for idx,t in enumerate(chunk,start=start):
            calldata="0x"+PRICE_SELECTOR+"0"*24+t["asset"][2:]
            payload.append({"jsonrpc":"2.0","id":idx,"method":"eth_call","params":[{"to":t["oracle"],"data":calldata},hex(t["block"])]})
        resp=None
        for attempt in range(3):
            try:
                r=session.post(endpoint,json=payload,headers=headers,timeout=(10,45)); stats["http_attempts"]+=1
                if r.status_code in TRANSIENT:
                    stats["transient_retries"]+=1; r.close(); time.sleep(1.5*(attempt+1)); continue
                r.raise_for_status(); resp=r.json(); r.close(); break
            except Exception:
                stats["errors"]+=1
                if attempt<2: time.sleep(1.5*(attempt+1))
        if not isinstance(resp,list): stats["failed_or_nonbatch"]+=1; continue
        byid={x.get("id"):x for x in resp if isinstance(x,dict)}
        for idx in range(start,start+len(chunk)):
            o=byid.get(idx)
            if not o or o.get("error") is not None: stats["rpc_errors"]+=1; continue
            rr=o.get("result")
            if not isinstance(rr,str) or not rr.startswith("0x"): stats["invalid"]+=1; continue
            try: out[idx]=int(rr,16); stats["usable"]+=1
            except ValueError: stats["invalid"]+=1
    session.close(); return out

def main()->int:
    outdir=Path("r1_global_state_output"); outdir.mkdir(parents=True,exist_ok=True)
    path=outdir/"AAVE_LIQUIDATION_OVERHANG_001_R1_GLOBAL_STATE_V0_1.json"
    stats:Counter[str]=Counter(); receipt:dict[str,Any]={}
    try:
        audit=load("downloaded_r1_audit","R1_AUDIT_PASS")
        bootstrap=load("downloaded_r0_bootstrap","RECONSTRUCTION_R0_BOOTSTRAP_PASS")
        reserves={u.lower():m for u,m in bootstrap["reserves"].items()}
        if len(reserves)!=37: raise RuntimeError("reserve universe not 37")

        filters=[
            {"address":[POOL],"topic0":[T_USER_EMODE]},
            {"address":[CONFIGURATOR],"topic0":[T_EMODE_ADDED]},
            {"address":[PROVIDER],"topic0":[T_POOL_UPDATED,T_CONFIG_UPDATED,T_ORACLE_UPDATED]},
        ]
        categories:dict[int,dict[str,Any]]={}; user_modes:dict[str,int]={}; counts:Counter[str]=Counter(); transitions=[]; seen=set(); violations=[]
        for obj in stream(FROM_BLOCK,TO_BLOCK,filters,stats):
            h=obj.get("header") or obj.get("block") or {}; bn=int(h["number"])
            for log in sorted(obj.get("logs") or [],key=lambda x:as_int(x.get("logIndex"))):
                topics=[str(x).lower() for x in (log.get("topics") or [])]; t0=topics[0] if topics else ""
                tx=str(log.get("transactionHash","")).lower(); li=as_int(log.get("logIndex")); key=(tx,li)
                if key in seen: raise RuntimeError("duplicate global canonical log")
                seen.add(key)
                if t0==T_EMODE_ADDED:
                    if len(topics)<2: raise RuntimeError("EModeCategoryAdded ABI")
                    cid=as_int(topics[1]); w=words(log.get("data",""),4); oracle="0x"+format(w[3],"040x")[-40:]
                    categories[cid]={"block":bn,"ltv":w[0],"liquidationThreshold":w[1],"liquidationBonus":w[2],"oracle":oracle}; counts["EModeCategoryAdded"]+=1
                elif t0==T_USER_EMODE:
                    if len(topics)<2: raise RuntimeError("UserEModeSet ABI")
                    user=taddr(topics[1]); cid=words(log.get("data",""),1)[0]
                    if cid!=0 and cid not in categories:
                        violations.append({"block":bn,"user":user,"category":cid,"reason":"undefined_category_at_user_set"})
                    user_modes[user]=cid; counts["UserEModeSet"]+=1
                elif t0 in (T_POOL_UPDATED,T_CONFIG_UPDATED,T_ORACLE_UPDATED):
                    if len(topics)<3: raise RuntimeError("provider update ABI")
                    name={T_POOL_UPDATED:"PoolUpdated",T_CONFIG_UPDATED:"PoolConfiguratorUpdated",T_ORACLE_UPDATED:"PriceOracleUpdated"}[t0]
                    row={"block":bn,"logIndex":li,"event":name,"old":taddr(topics[1]),"new":taddr(topics[2])}; transitions.append(row); counts[name]+=1
                else: raise RuntimeError("unexpected global event")

        oracle_trans=[x for x in transitions if x["event"]=="PriceOracleUpdated"]
        active_oracles={INITIAL_ORACLE}
        for x in oracle_trans: active_oracles.add(x["new"])
        oracle_filters=[{"address":sorted(active_oracles),"topic0":[T_ASSET_SOURCE,T_FALLBACK,T_BASE]}]
        oracle_counts:Counter[str]=Counter(); oracle_rows=[]
        for obj in stream(FROM_BLOCK,TO_BLOCK,oracle_filters,stats):
            h=obj.get("header") or obj.get("block") or {}; bn=int(h["number"])
            for log in obj.get("logs") or []:
                topics=[str(x).lower() for x in (log.get("topics") or [])]; t0=topics[0]
                if t0==T_ASSET_SOURCE:
                    if len(topics)<3: raise RuntimeError("AssetSourceUpdated ABI")
                    oracle_rows.append({"block":bn,"oracle":str(log["address"]).lower(),"event":"AssetSourceUpdated","asset":taddr(topics[1]),"source":taddr(topics[2])}); oracle_counts["AssetSourceUpdated"]+=1
                elif t0==T_FALLBACK:
                    if len(topics)<2: raise RuntimeError("FallbackOracleUpdated ABI")
                    oracle_rows.append({"block":bn,"oracle":str(log["address"]).lower(),"event":"FallbackOracleUpdated","fallback":taddr(topics[1])}); oracle_counts["FallbackOracleUpdated"]+=1
                elif t0==T_BASE:
                    if len(topics)<2: raise RuntimeError("BaseCurrencySet ABI")
                    unit=words(log.get("data",""),1)[0]
                    oracle_rows.append({"block":bn,"oracle":str(log["address"]).lower(),"event":"BaseCurrencySet","base":taddr(topics[1]),"unit":str(unit)}); oracle_counts["BaseCurrencySet"]+=1
                else: raise RuntimeError("unexpected oracle config event")

        def oracle_at(block:int)->str:
            current=INITIAL_ORACLE
            for x in sorted(oracle_trans,key=lambda z:(z["block"],z["logIndex"])):
                if x["block"]<=block: current=x["new"]
            return current
        targets=[]
        for b in AUDIT_BLOCKS:
            oracle=oracle_at(b)
            for asset,m in sorted(reserves.items()):
                if int(m["init_block"])<=b: targets.append({"block":b,"asset":asset,"oracle":oracle})
        vals_by_ep={}; rpcstats={}
        for ep in RPC_ENDPOINTS:
            cs:Counter[str]=Counter(); vals_by_ep[ep]=rpc_batches(ep,targets,cs); rpcstats[ep]=dict(cs)
        price_failures=[]; technical=provenance=False
        for i,t in enumerate(targets):
            vals={ep:v[i] for ep,v in vals_by_ep.items() if i in v}; uniq=sorted(set(vals.values()))
            if len(vals)<2:
                technical=True; price_failures.append({**t,"failure":"INSUFFICIENT_ARCHIVE_RPC_QUORUM","values":{k:str(v) for k,v in vals.items()}})
            elif len(uniq)!=1:
                provenance=True; price_failures.append({**t,"failure":"ARCHIVE_RPC_PRICE_DISAGREEMENT","values":{k:str(v) for k,v in vals.items()}})
            elif uniq[0]<=0:
                provenance=True; price_failures.append({**t,"failure":"NONPOSITIVE_AAVE_ORACLE_PRICE","value":str(uniq[0])})

        if violations:
            classification="RECONSTRUCTION_RECONCILIATION_FAILURE"; failure=f"eMode violations={len(violations)}"
        elif provenance:
            classification="RECONSTRUCTION_PROVENANCE_FAILURE"; failure=f"oracle price provenance failures={len(price_failures)}"
        elif technical:
            classification="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"; failure=f"archive oracle quorum failures={len(price_failures)}"
        else:
            classification="R1_GLOBAL_STATE_PASS"; failure=None
        receipt={"classification":classification,"failure":failure,"event_counts":dict(counts),
                 "emode_category_count":len(categories),"user_emode_state_count":len(user_modes),"emode_violations":violations[:100],
                 "provider_transitions":transitions,"active_oracles":sorted(active_oracles),"oracle_config_event_counts":dict(oracle_counts),
                 "oracle_config_events":oracle_rows,"oracle_price_validation_target_count":len(targets),
                 "oracle_price_validation_failure_count":len(price_failures),"oracle_price_validation_failures":price_failures[:200],
                 "archive_rpc_stats":rpcstats,"transport_stats":dict(stats)}
    except Exception as exc:
        receipt={"classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE","failure":f"{type(exc).__name__}: {str(exc)[:1200]}","transport_stats":dict(stats)}
    receipt.update({"lab_id":LAB_ID,"phase":"R1_GLOBAL_STATE_AND_ORACLE_PROVENANCE_OUTCOME_BLIND","frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,
                    "safety":{"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,
                              "market_return_prices_opened":False,"aave_protocol_oracle_prices_validated":True,
                              "returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}})
    path.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"emode_categories":receipt.get("emode_category_count"),"oracle_price_targets":receipt.get("oracle_price_validation_target_count"),"oracle_price_failures":receipt.get("oracle_price_validation_failure_count"),"health_factor_computed":False,"overhang_computed":False,"returns_opened":False,"pnl_opened":False},sort_keys=True))
    return 0 if receipt["classification"]=="R1_GLOBAL_STATE_PASS" else 2

if __name__=="__main__": sys.exit(main())

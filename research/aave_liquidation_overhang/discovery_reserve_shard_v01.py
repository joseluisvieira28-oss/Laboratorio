#!/usr/bin/env python3
"""2023 Discovery reserve shard: token-native replay + daily point-in-time valuation."""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import requests
from eth_hash.auto import keccak

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
PORTAL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL="0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
CONFIGURATOR="0x64b761d848206f447fe2dd461b0c635ec39ebb27"
FROM_BLOCK=16_490_000
RAY=10**27
WINDOW=75_000
TRANSIENT={429,500,502,503,504,529}
RPC_ENDPOINTS=[
    "https://eth-mainnet.public.blastapi.io",
    "https://rpc.mevblocker.io",
    "https://ethereum.blinklabs.xyz/",
]


def topic(sig:str)->str: return "0x"+keccak(sig.encode()).hex()
T_MINT=topic("Mint(address,address,uint256,uint256,uint256)")
T_BURN=topic("Burn(address,address,uint256,uint256,uint256)")
T_BALANCE_TRANSFER=topic("BalanceTransfer(address,address,uint256,uint256)")
T_INITIALIZED=topic("Initialized(address,address,address,address,uint8,string,string,bytes)")
T_COLL_ON=topic("ReserveUsedAsCollateralEnabled(address,address)")
T_COLL_OFF=topic("ReserveUsedAsCollateralDisabled(address,address)")
T_COLL_CFG=topic("CollateralConfigurationChanged(address,uint256,uint256,uint256)")
T_EMODE_ASSET=topic("EModeAssetCategoryChanged(address,uint8,uint8)")
SEL_NORM_INCOME=keccak(b"getReserveNormalizedIncome(address)")[:4].hex()
SEL_NORM_DEBT=keccak(b"getReserveNormalizedVariableDebt(address)")[:4].hex()
SEL_PRICE=keccak(b"getAssetPrice(address)")[:4].hex()


def as_int(v:Any)->int:
    if isinstance(v,int): return v
    if isinstance(v,str): return int(v,16) if v.startswith("0x") else int(v)
    raise TypeError("bad integer")


def topic_addr(t:str)->str:
    t=str(t).lower()
    if not t.startswith("0x") or len(t)!=66: raise ValueError("bad address topic")
    return "0x"+t[-40:]


def addr_topic(a:str)->str:
    a=a.lower()
    if not a.startswith("0x") or len(a)!=42: raise ValueError("bad address")
    return "0x"+"0"*24+a[2:]


def words(data:str,n:int)->list[int]:
    h=str(data)[2:] if str(data).startswith("0x") else ""
    if len(h)<64*n or len(h)%64: raise ValueError("bad ABI data")
    return [int(h[i*64:(i+1)*64],16) for i in range(n)]


def ray_div(a:int,b:int)->int:
    if b==0: raise ZeroDivisionError("rayDiv zero")
    return (a*RAY+b//2)//b


def ray_mul(a:int,b:int)->int:
    return (a*b+RAY//2)//RAY


def percent_mul(value:int,pct:int)->int:
    return (value*pct+5000)//10000


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
                         "User-Agent":f"{LAB_ID}/discovery-reserve-v0.1"})
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
    headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/discovery-reserve-v0.1"}
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
    sid=int(os.environ.get("DISCOVERY_RESERVE_SHARD_ID","0"))
    scount=int(os.environ.get("DISCOVERY_RESERVE_SHARD_COUNT","8"))
    out=Path("discovery_reserve_shards"); out.mkdir(parents=True,exist_ok=True)
    meta_path=out/f"reserve_shard_{sid:02d}_meta.json"
    rows_path=out/f"reserve_shard_{sid:02d}_rows.jsonl.gz"
    transport=Counter(); rpcstats={ep:Counter() for ep in RPC_ENDPOINTS}
    try:
        cal=load_one("downloaded_discovery_calendar","DISCOVERY_CALENDAR_PASS")
        glob=load_one("downloaded_discovery_global","DISCOVERY_GLOBAL_SOURCE_PASS")
        bootstrap=load_one("downloaded_r0_bootstrap","RECONSTRUCTION_R0_BOOTSTRAP_PASS")
        snaps=cal["snapshots"]; to_block=int(cal["discovery_event_to_block"])
        if len(snaps)!=334: raise RuntimeError("calendar snapshot count mismatch")

        reserves_all=sorted((u.lower(),m) for u,m in bootstrap["reserves"].items())
        if len(reserves_all)!=37: raise RuntimeError("R0 reserve universe not 37")
        selected_all=[(u,m) for i,(u,m) in enumerate(reserves_all) if i%scount==sid]
        selected=[(u,m) for u,m in selected_all if int(m["init_block"])<=to_block]
        if not selected: raise RuntimeError("empty active 2023 reserve shard")

        token_meta={}; atoken_for={}; vdebt_for={}; init_block={}
        for u,m in selected:
            at=str(m["aToken"]).lower(); vd=str(m["variableDebtToken"]).lower()
            token_meta[at]={"kind":"ATOKEN","reserve":u}
            token_meta[vd]={"kind":"VARIABLE_DEBT","reserve":u}
            atoken_for[u]=at; vdebt_for[u]=vd; init_block[u]=int(m["init_block"])

        # Separate deterministic aToken Initialized pass to avoid the historical
        # dispatch-order bug that R1 V0.2 had to remediate.
        decimals={}
        dec_filters=[{"address":sorted(atoken_for.values()),"topic0":[T_INITIALIZED]}]
        for obj in stream(FROM_BLOCK,to_block,dec_filters,transport):
            for log in obj.get("logs") or []:
                addr=str(log.get("address","")).lower(); topics=[str(x).lower() for x in (log.get("topics") or [])]
                if len(topics)<3 or topics[0]!=T_INITIALIZED: raise RuntimeError("Initialized ABI")
                reserve=topic_addr(topics[1]); pool=topic_addr(topics[2])
                if reserve not in atoken_for or atoken_for[reserve]!=addr or pool!=POOL:
                    raise RuntimeError("Initialized identity mismatch")
                dec=words(log.get("data",""),3)[2]
                if dec>255: raise RuntimeError("invalid decimals")
                if reserve in decimals and decimals[reserve]!=dec: raise RuntimeError("decimals changed")
                decimals[reserve]=dec
        # Discovery-period eligibility: reserves initialized only after the
        # frozen 2023 event ceiling are canonical master identities but cannot
        # contribute state in this partition and therefore do not require a
        # pre-existing aToken Initialized/decimals event inside 2023.
        decimals_required=[u for u,_ in selected if init_block[u]<=to_block]
        missing_dec=[u for u in decimals_required if u not in decimals]
        if missing_dec: raise RuntimeError(f"missing active-Discovery reserve decimals: {missing_dec}")

        daily_oracle={x["date"]:x["oracle"] for x in glob["daily_oracle"]}
        # Acquire exact normalized indices and Aave prices for each active reserve/day.
        targets=[]; target_keys=[]
        for s in snaps:
            b=int(s["block"]); day=s["date"]; oracle=daily_oracle[day]
            for reserve,_m in selected:
                if init_block[reserve]>b: continue
                targets.extend([
                    {"block":b,"to":POOL,"data":calldata(SEL_NORM_INCOME,reserve)},
                    {"block":b,"to":POOL,"data":calldata(SEL_NORM_DEBT,reserve)},
                    {"block":b,"to":oracle,"data":calldata(SEL_PRICE,reserve)},
                ])
                target_keys.extend([
                    (day,reserve,"norm_income"),(day,reserve,"norm_debt"),(day,reserve,"price")
                ])
        vals_by_ep={}
        for ep in RPC_ENDPOINTS:
            vals_by_ep[ep]=rpc_batch(ep,targets,rpcstats[ep])
        market=defaultdict(dict)
        for i,key in enumerate(target_keys):
            vals={ep:m[i] for ep,m in vals_by_ep.items() if i in m}
            if len(vals)<2: raise RuntimeError(f"daily reserve RPC quorum<2 for {key}")
            if len(set(vals.values()))!=1: raise RuntimeError(f"daily reserve RPC disagreement for {key}: {vals}")
            v=next(iter(vals.values()))
            if v<=0: raise RuntimeError(f"nonpositive daily reserve value for {key}: {v}")
            day,reserve,kind=key
            market[(day,reserve)][kind]=v

        underlyings=[u for u,_ in selected]
        underlying_topics=[addr_topic(u) for u in underlyings]
        filters=[
            {"address":sorted(token_meta),"topic0":[T_MINT,T_BURN,T_BALANCE_TRANSFER]},
            {"address":[POOL],"topic0":[T_COLL_ON,T_COLL_OFF],"topic1":underlying_topics},
            {"address":[CONFIGURATOR],"topic0":[T_COLL_CFG,T_EMODE_ASSET],"topic1":underlying_topics},
        ]

        balances=defaultdict(dict)
        flags={}
        cfg_lt={u:0 for u in underlyings}
        cfg_emode={u:0 for u in underlyings}
        counts=Counter(); seen=set(); negative=[]; debt_transfer_count=0
        current_tx=None; touched_tx=set(); stale_flag_diagnostics=0
        snapshot_index=0; row_count=0; row_hash=hashlib.sha256()
        gz=gzip.open(rows_path,"wt",encoding="utf-8")

        def bal(token,user): return balances[token].get(user,0)
        def setbal(token,user,value,bn,li):
            if value==0: balances[token].pop(user,None)
            else: balances[token][user]=value
            if value<0:
                negative.append({"block":bn,"logIndex":li,"token":token,"user":user,"balance":str(value)})

        def flush_tx():
            nonlocal touched_tx,stale_flag_diagnostics
            for reserve,user in touched_tx:
                if flags.get((reserve,user),False) and bal(atoken_for[reserve],user)==0:
                    stale_flag_diagnostics+=1
            touched_tx=set()

        def emit_snapshot(idx:int):
            nonlocal row_count
            s=snaps[idx]; day=s["date"]; b=int(s["block"])
            for reserve,_m in selected:
                if init_block[reserve]>b: continue
                lt=cfg_lt[reserve]
                if lt is None: raise RuntimeError(f"missing liquidation threshold at {day} {reserve}")
                dec=decimals[reserve]; md=market.get((day,reserve))
                if not md or set(md)!={"norm_income","norm_debt","price"}:
                    raise RuntimeError(f"incomplete daily market state {day} {reserve}")
                users=set(balances[atoken_for[reserve]])|set(balances[vdebt_for[reserve]])
                for user in sorted(users):
                    debt_scaled=bal(vdebt_for[reserve],user)
                    coll_scaled=bal(atoken_for[reserve],user) if flags.get((reserve,user),False) else 0
                    if debt_scaled==0 and coll_scaled==0: continue
                    if debt_scaled<0 or coll_scaled<0: raise RuntimeError("negative scaled state at snapshot")
                    coll_under=ray_mul(coll_scaled,md["norm_income"]) if coll_scaled else 0
                    debt_under=ray_mul(debt_scaled,md["norm_debt"]) if debt_scaled else 0
                    unit=10**dec
                    coll_value=(coll_under*md["price"])//unit if coll_under else 0
                    debt_value=(debt_under*md["price"])//unit if debt_under else 0
                    row={
                        "d":idx,"u":user,"r":reserve,
                        "c":str(coll_value),"q":str(debt_value),
                        "lt":int(lt),"ec":int(cfg_emode[reserve]),
                    }
                    line=json.dumps(row,separators=(",",":"),sort_keys=True)
                    gz.write(line+"\n"); row_hash.update((line+"\n").encode()); row_count+=1

        for obj in stream(FROM_BLOCK,to_block,filters,transport):
            header=obj.get("header") or obj.get("block") or {}; bn=int(header["number"])
            while snapshot_index<len(snaps) and int(snaps[snapshot_index]["block"])<bn:
                flush_tx(); emit_snapshot(snapshot_index); snapshot_index+=1

            logs=sorted(obj.get("logs") or [],key=lambda x:as_int(x.get("logIndex")))
            for log in logs:
                addr=str(log.get("address","")).lower(); topics=[str(x).lower() for x in (log.get("topics") or [])]
                if not topics: raise RuntimeError("log without topic0")
                t0=topics[0]; tx=str(log.get("transactionHash","")).lower(); li=as_int(log.get("logIndex"))
                key=(tx,li)
                if key in seen: raise RuntimeError("duplicate canonical log")
                seen.add(key)
                if current_tx is not None and tx!=current_tx: flush_tx()
                current_tx=tx

                if addr in token_meta:
                    meta=token_meta[addr]; reserve=meta["reserve"]; kind=meta["kind"]
                    if t0==T_MINT:
                        if len(topics)<3: raise RuntimeError("Mint ABI")
                        user=topic_addr(topics[2]); value,inc,index=words(log.get("data",""),3)[:3]
                        if value>inc: delta=ray_div(value-inc,index)
                        elif value<inc: delta=-ray_div(inc-value,index)
                        else: delta=0
                        setbal(addr,user,bal(addr,user)+delta,bn,li); counts[f"{kind}_MINT"]+=1
                        if kind=="ATOKEN": touched_tx.add((reserve,user))
                    elif t0==T_BURN:
                        if len(topics)<2: raise RuntimeError("Burn ABI")
                        user=topic_addr(topics[1]); value,inc,index=words(log.get("data",""),3)[:3]
                        delta=-ray_div(value+inc,index)
                        setbal(addr,user,bal(addr,user)+delta,bn,li); counts[f"{kind}_BURN"]+=1
                        if kind=="ATOKEN": touched_tx.add((reserve,user))
                    elif t0==T_BALANCE_TRANSFER:
                        if kind=="VARIABLE_DEBT":
                            debt_transfer_count+=1; counts["VARIABLE_DEBT_BALANCE_TRANSFER"]+=1
                        else:
                            if len(topics)<3: raise RuntimeError("BalanceTransfer ABI")
                            fr=topic_addr(topics[1]); to=topic_addr(topics[2]); value,_index=words(log.get("data",""),2)[:2]
                            setbal(addr,fr,bal(addr,fr)-value,bn,li)
                            setbal(addr,to,bal(addr,to)+value,bn,li)
                            touched_tx.add((reserve,fr)); touched_tx.add((reserve,to)); counts["ATOKEN_BALANCE_TRANSFER"]+=1
                    else:
                        raise RuntimeError("unexpected token topic")
                elif addr==POOL:
                    if len(topics)<3: raise RuntimeError("collateral flag ABI")
                    reserve=topic_addr(topics[1]); user=topic_addr(topics[2])
                    flags[(reserve,user)]=(t0==T_COLL_ON)
                    touched_tx.add((reserve,user))
                    counts["CollateralEnabled" if t0==T_COLL_ON else "CollateralDisabled"]+=1
                elif addr==CONFIGURATOR:
                    if len(topics)<2: raise RuntimeError("Configurator ABI")
                    reserve=topic_addr(topics[1])
                    if t0==T_COLL_CFG:
                        _ltv,threshold,_bonus=words(log.get("data",""),3)[:3]
                        cfg_lt[reserve]=threshold; counts["CollateralConfigurationChanged"]+=1
                    elif t0==T_EMODE_ASSET:
                        _old,new=words(log.get("data",""),2)[:2]
                        cfg_emode[reserve]=new; counts["EModeAssetCategoryChanged"]+=1
                    else:
                        raise RuntimeError("unexpected Configurator topic")
                else:
                    raise RuntimeError("unexpected source address")

            while snapshot_index<len(snaps) and int(snaps[snapshot_index]["block"])==bn:
                flush_tx(); emit_snapshot(snapshot_index); snapshot_index+=1

        flush_tx()
        while snapshot_index<len(snaps):
            emit_snapshot(snapshot_index); snapshot_index+=1
        gz.close()

        if negative: raise RuntimeError(f"negative scaled states observed: {len(negative)}")
        if debt_transfer_count: raise RuntimeError(f"variable-debt BalanceTransfer observed: {debt_transfer_count}")

        meta={
            "lab_id":LAB_ID,
            "classification":"DISCOVERY_RESERVE_SHARD_PASS",
            "shard_id":sid,"shard_count":scount,
            "selected_reserves":underlyings,
            "assigned_reserves_full_r1":[u for u,_m in selected_all],
            "post_2023_reserves_excluded":[u for u,m in selected_all if int(m["init_block"])>to_block],
            "snapshot_count":len(snaps),
            "row_count":row_count,
            "row_sha256":row_hash.hexdigest(),
            "decimals":{k:int(v) for k,v in decimals.items()},
            "event_counts":dict(sorted(counts.items())),
            "canonical_log_count":len(seen),
            "stale_collateral_flag_zero_scaled_diagnostic_count":stale_flag_diagnostics,
            "transport_stats":dict(transport),
            "archive_rpc_stats":{ep:dict(s) for ep,s in rpcstats.items()},
            "safety":{
                "health_factor_computed":False,"overhang_computed":False,
                "future_liquidation_outcomes_opened":False,"opened_2024_outcomes":False,
                "opened_2025_or_2026":False,"market_returns_opened":False,
                "pnl_opened":False,"live_trading":False,"exchange_mutation":False,
            },
        }
    except Exception as exc:
        try:
            if 'gz' in locals(): gz.close()
        except Exception:
            pass
        meta={
            "lab_id":LAB_ID,"classification":"DISCOVERY_RECONSTRUCTION_FAILURE",
            "shard_id":sid,"shard_count":scount,
            "failure":f"{type(exc).__name__}: {str(exc)[:1600]}",
            "transport_stats":dict(transport),
            "archive_rpc_stats":{ep:dict(s) for ep,s in rpcstats.items()},
            "safety":{"health_factor_computed":False,"overhang_computed":False,
                      "future_liquidation_outcomes_opened":False,"opened_2024_outcomes":False,
                      "opened_2025_or_2026":False,"market_returns_opened":False,
                      "pnl_opened":False,"live_trading":False,"exchange_mutation":False},
        }
    meta_path.write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":meta["classification"],"shard":sid,
                      "reserves":len(meta.get("selected_reserves",[])),
                      "rows":meta.get("row_count"),"snapshots":meta.get("snapshot_count")},sort_keys=True))
    return 0 if meta["classification"]=="DISCOVERY_RESERVE_SHARD_PASS" else 2


if __name__=="__main__":
    raise SystemExit(main())

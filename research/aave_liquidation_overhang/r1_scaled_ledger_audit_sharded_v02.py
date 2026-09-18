#!/usr/bin/env python3
"""Sharded transport remediation for AAVE-LIQUIDATION-OVERHANG-001 R1 audit V0.2.

Operational-only remediation. Scientific semantics are inherited unchanged from
AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2.
"""
from __future__ import annotations
import hashlib, json, os, sys, time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable
import requests
from eth_hash.auto import keccak

LAB_ID="AAVE-LIQUIDATION-OVERHANG-001"
PORTAL="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
POOL="0x87870bca3f3fd6335c3f4ce8392d69350b4fa4e2"
FROM_BLOCK=16_490_000
TO_BLOCK=21_525_890
AUDIT_BLOCKS=[17_748_972,19_007_945,20_266_917,21_525_890]
SAMPLE_SIZE=16
RAY=10**27
WINDOW=75_000
TRANSIENT={429,500,502,503,504,529}
SHARDS=[
 (16_490_000,17_119_486),(17_119_487,17_748_973),
 (17_748_974,18_378_460),(18_378_461,19_007_946),
 (19_007_947,19_637_432),(19_637_433,20_266_918),
 (20_266_919,20_896_404),(20_896_405,21_525_890),
]
RPC_ENDPOINTS=[
 "https://ethereum-rpc.publicnode.com","https://eth.drpc.org",
 "https://1rpc.io/eth","https://eth.llamarpc.com","https://rpc.ankr.com/eth",
]
BORROW_TOPIC="0x"+keccak(b"Borrow(address,address,address,uint256,uint8,uint256,uint16)").hex()
MINT_TOPIC="0x"+keccak(b"Mint(address,address,uint256,uint256,uint256)").hex()
BURN_TOPIC="0x"+keccak(b"Burn(address,address,uint256,uint256,uint256)").hex()
BALANCE_TRANSFER_TOPIC="0x"+keccak(b"BalanceTransfer(address,address,uint256,uint256)").hex()
SCALED_BALANCE_SELECTOR=keccak(b"scaledBalanceOf(address)")[:4].hex()

def taddr(topic:str)->str:
    t=str(topic).lower()
    if not t.startswith("0x") or len(t)!=66: raise ValueError("invalid indexed address topic")
    return "0x"+t[-40:]

def atopic(addr:str)->str:
    a=addr.lower()
    if not a.startswith("0x") or len(a)!=42: raise ValueError("invalid address")
    return "0x"+"0"*24+a[2:]

def as_int(v:Any)->int:
    if isinstance(v,int): return v
    if isinstance(v,str): return int(v,16) if v.startswith("0x") else int(v)
    raise TypeError("bad int")

def ray_div(a:int,b:int)->int:
    if b==0: raise ZeroDivisionError("rayDiv denominator zero")
    return (a*RAY+b//2)//b

def words(data:str,n:int)->list[int]:
    d=str(data)
    if not d.startswith("0x"): raise ValueError("log data missing 0x")
    h=d[2:]
    if len(h)<64*n or len(h)%64: raise ValueError("invalid ABI data length")
    return [int(h[i*64:(i+1)*64],16) for i in range(n)]

def post(body:dict[str,Any],stats:Counter[str])->requests.Response:
    last=None
    for attempt in range(8):
        try:
            r=requests.post(PORTAL,json=body,timeout=(20,180),stream=True,
                headers={"Content-Type":"application/json","Accept-Encoding":"gzip",
                         "User-Agent":f"{LAB_ID}/r1-sharded-v0.2"})
            stats["http_attempts"]+=1
            if r.status_code in TRANSIENT:
                last=RuntimeError(f"transient HTTP {r.status_code}"); r.close()
                if attempt<7:
                    stats["transient_retries"]+=1
                    time.sleep(min(20.0,1.5*(2**attempt))); continue
                raise last
            if r.status_code==204:
                r.close(); raise RuntimeError("unexpected Portal 204")
            r.raise_for_status(); stats["successful_http_responses"]+=1; return r
        except (requests.RequestException,RuntimeError) as exc:
            last=exc
            if attempt<7:
                stats["network_retries"]+=1
                time.sleep(min(20.0,1.5*(2**attempt))); continue
            raise
    raise RuntimeError(str(last))

def stream_range(start:int,end:int,filters:list[dict[str,Any]],include_data:bool,stats:Counter[str])->Iterable[dict[str,Any]]:
    cursor=start
    while cursor<=end:
        rt=min(end,cursor+WINDOW-1)
        lf={"address":True,"topics":True,"transactionHash":True,"logIndex":True}
        if include_data: lf["data"]=True
        body={"type":"evm","fromBlock":cursor,"toBlock":rt,
              "fields":{"block":{"number":True,"timestamp":True},"log":lf},"logs":filters}
        page=None; last=None
        for sa in range(8):
            r=post(body,stats); local=[]; ll=None
            try:
                for raw in r.iter_lines(decode_unicode=True):
                    if not raw: continue
                    obj=json.loads(raw)
                    if isinstance(obj,dict) and obj.get("error"): raise RuntimeError(f"portal error: {obj['error']}")
                    h=obj.get("header") or obj.get("block") or {}
                    bn=int(h["number"])
                    if not(cursor<=bn<=rt): raise RuntimeError("row outside requested range")
                    if ll is not None and bn<ll: raise RuntimeError("non-monotonic page")
                    ll=bn; local.append(obj)
            except requests.RequestException:
                stats["stream_read_failures"]+=1
                if sa<7:
                    stats["stream_read_retries"]+=1; time.sleep(min(20.0,1.5*(2**sa))); continue
                raise
            finally: r.close()
            page=local; last=ll; break
        if page is None: raise RuntimeError("stream retry budget exhausted")
        if not page:
            stats["empty_windows"]+=1; cursor=rt+1; continue
        stats["portal_rows"]+=len(page)
        for obj in page: yield obj
        cursor=int(last)+1

def load_one(root:str,classification:str|None=None)->dict[str,Any]:
    files=sorted(Path(root).rglob("*.json"))
    if len(files)!=1: raise RuntimeError(f"expected one json under {root}, got {len(files)}")
    obj=json.loads(files[0].read_text(encoding="utf-8"))
    if classification and obj.get("classification")!=classification:
        raise RuntimeError(f"{root} classification {obj.get('classification')} != {classification}")
    return obj

def load_bootstrap()->dict[str,Any]:
    return load_one("downloaded_r0_bootstrap","RECONSTRUCTION_R0_BOOTSTRAP_PASS")

def build_token_maps(bootstrap:dict[str,Any]):
    reserves=bootstrap.get("reserves") or {}
    if len(reserves)!=37: raise RuntimeError("reserve count != 37")
    meta={}; atokens=[]; debts=[]
    for u,m in reserves.items():
        at=str(m["aToken"]).lower(); vd=str(m["variableDebtToken"]).lower(); ul=u.lower()
        if len(at)!=42 or len(vd)!=42 or at in meta or vd in meta: raise RuntimeError("invalid token map")
        meta[at]={"kind":"ATOKEN","underlying":ul}; meta[vd]={"kind":"VARIABLE_DEBT","underlying":ul}
        atokens.append(at); debts.append(vd)
    return meta,atokens,debts

def borrower_shard()->int:
    sid=int(os.environ["SHARD_ID"]); start,end=SHARDS[sid]
    out=Path("r1_borrower_shards"); out.mkdir(parents=True,exist_ok=True)
    stats=Counter(); users=set(); seen=set(); ids=[]
    failure=None
    try:
        for obj in stream_range(start,end,[{"address":[POOL],"topic0":[BORROW_TOPIC]}],False,stats):
            h=obj.get("header") or obj.get("block") or {}; bn=int(h["number"])
            for log in obj.get("logs") or []:
                topics=log.get("topics") or []
                if len(topics)<3 or str(topics[0]).lower()!=BORROW_TOPIC: raise RuntimeError("malformed Borrow")
                tx=str(log.get("transactionHash","")).lower(); li=as_int(log.get("logIndex")); key=(tx,li)
                if key in seen: raise RuntimeError("duplicate Borrow identity inside shard")
                seen.add(key); ids.append(f"{bn}|{tx}|{li}"); users.add(taddr(topics[2]))
    except Exception as exc: failure=f"{type(exc).__name__}: {str(exc)[:1000]}"
    c="BORROW_SHARD_PASS" if failure is None else "RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
    receipt={"lab_id":LAB_ID,"phase":"R1_BORROWER_SHARD_V0_2","classification":c,"failure":failure,
             "shard_id":sid,"from_block":start,"to_block":end,"borrow_log_count":len(seen),
             "borrowers":sorted(users),"identity_digest_sha256":hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest(),
             "transport_stats":dict(stats),"safety":safety()}
    (out/f"borrower_shard_{sid:02d}.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"shard":sid,"classification":c,"borrow_logs":len(seen),"borrowers":len(users)},sort_keys=True))
    return 0 if c=="BORROW_SHARD_PASS" else 2

def borrower_aggregate()->int:
    out=Path("r1_borrower_sample"); out.mkdir(parents=True,exist_ok=True)
    files=sorted(Path("downloaded_borrower_shards").rglob("*.json")); failure=None
    try:
        if len(files)!=8: raise RuntimeError(f"expected 8 borrower shards, got {len(files)}")
        rs=[json.loads(p.read_text()) for p in files]; rs.sort(key=lambda x:int(x["shard_id"]))
        users=set(); total=0
        for i,r in enumerate(rs):
            if r.get("classification")!="BORROW_SHARD_PASS": raise RuntimeError(f"shard {i} not pass")
            if (int(r["from_block"]),int(r["to_block"]))!=SHARDS[i]: raise RuntimeError("shard range mismatch")
            users.update(r.get("borrowers") or []); total+=int(r["borrow_log_count"])
        if total!=204_952: raise RuntimeError(f"Borrow total {total} != 204952")
        if len(users)<SAMPLE_SIZE: raise RuntimeError("insufficient borrowers")
        ranked=sorted(users,key=lambda a:(keccak(bytes.fromhex(a[2:])),a)); sample=ranked[:SAMPLE_SIZE]
        sample_sha=hashlib.sha256("\n".join(sample).encode()).hexdigest()
        receipt={"lab_id":LAB_ID,"phase":"R1_BORROWER_GLOBAL_SAMPLE_V0_2","classification":"BORROW_SAMPLE_PASS",
                 "borrow_log_count":total,"unique_borrower_count":len(users),"sample_borrowers":sample,
                 "sample_sha256":sample_sha,"shard_ranges":SHARDS,"safety":safety()}
    except Exception as exc:
        receipt={"lab_id":LAB_ID,"phase":"R1_BORROWER_GLOBAL_SAMPLE_V0_2",
                 "classification":"RECONSTRUCTION_RECONCILIATION_FAILURE",
                 "failure":f"{type(exc).__name__}: {str(exc)[:1200]}","safety":safety()}
    (out/"AAVE_R1_BORROW_SAMPLE_V0_2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"borrowers":receipt.get("unique_borrower_count"),"sample":len(receipt.get("sample_borrowers") or [])},sort_keys=True))
    return 0 if receipt["classification"]=="BORROW_SAMPLE_PASS" else 2

def token_shard()->int:
    sid=int(os.environ["SHARD_ID"]); start,end=SHARDS[sid]
    out=Path("r1_token_shards"); out.mkdir(parents=True,exist_ok=True)
    stats=Counter(); failure=None
    try:
        sample_receipt=load_one("downloaded_borrow_sample","BORROW_SAMPLE_PASS")
        bootstrap=load_bootstrap(); meta,atokens,debts=build_token_maps(bootstrap)
        sample=[x.lower() for x in sample_receipt["sample_borrowers"]]; ss=set(sample); st=[atopic(x) for x in sample]
        all_tokens=atokens+debts
        filters=[
            {"address":all_tokens,"topic0":[MINT_TOPIC],"topic2":st},
            {"address":all_tokens,"topic0":[BURN_TOPIC],"topic1":st},
            {"address":atokens,"topic0":[BALANCE_TRANSFER_TOPIC],"topic1":st},
            {"address":atokens,"topic0":[BALANCE_TRANSFER_TOPIC],"topic2":st},
            {"address":debts,"topic0":[BALANCE_TRANSFER_TOPIC]},
        ]
        deltas=defaultdict(int); counts=Counter(); seen=set(); ids=[]; debt_bt=0
        for obj in stream_range(start,end,filters,True,stats):
            h=obj.get("header") or obj.get("block") or {}; bn=int(h["number"])
            for log in obj.get("logs") or []:
                addr=str(log.get("address","")).lower(); topics=[str(x).lower() for x in (log.get("topics") or [])]
                if addr not in meta or not topics: raise RuntimeError("unexpected token log")
                tx=str(log.get("transactionHash","")).lower(); li=as_int(log.get("logIndex")); key=(tx,li)
                if key in seen:
                    counts["filter_overlap_duplicates"]+=1; continue
                seen.add(key); ids.append(f"{bn}|{tx}|{li}")
                t0=topics[0]; kind=meta[addr]["kind"]
                if t0==MINT_TOPIC:
                    if len(topics)<3: raise RuntimeError("Mint ABI")
                    user=taddr(topics[2])
                    if user not in ss: raise RuntimeError("Mint escaped sample")
                    value,bi,index=words(str(log.get("data","")),3)[:3]
                    if index==0: raise RuntimeError("Mint index zero")
                    delta=ray_div(value-bi,index) if value>bi else (-ray_div(bi-value,index) if value<bi else 0)
                    deltas[(user,addr,bn)]+=delta; counts[f"{kind}_MINT"]+=1
                elif t0==BURN_TOPIC:
                    if len(topics)<2: raise RuntimeError("Burn ABI")
                    user=taddr(topics[1])
                    if user not in ss: raise RuntimeError("Burn escaped sample")
                    value,bi,index=words(str(log.get("data","")),3)[:3]
                    if index==0: raise RuntimeError("Burn index zero")
                    deltas[(user,addr,bn)]-=ray_div(value+bi,index); counts[f"{kind}_BURN"]+=1
                elif t0==BALANCE_TRANSFER_TOPIC:
                    if kind=="VARIABLE_DEBT":
                        debt_bt+=1; counts["VARIABLE_DEBT_BALANCE_TRANSFER"]+=1; continue
                    if len(topics)<3: raise RuntimeError("BalanceTransfer ABI")
                    fr=taddr(topics[1]); to=taddr(topics[2]); value,index=words(str(log.get("data","")),2)[:2]
                    if index==0: raise RuntimeError("BalanceTransfer index zero")
                    if fr in ss: deltas[(fr,addr,bn)]-=value
                    if to in ss: deltas[(to,addr,bn)]+=value
                    if fr not in ss and to not in ss: raise RuntimeError("BalanceTransfer escaped sample")
                    counts["ATOKEN_BALANCE_TRANSFER"]+=1
                else: raise RuntimeError("unexpected token topic")
        rows=[{"user":u,"token":t,"block":b,"delta":str(d)} for (u,t,b),d in sorted(deltas.items())]
        receipt={"lab_id":LAB_ID,"phase":"R1_TOKEN_DELTA_SHARD_V0_2","classification":"TOKEN_SHARD_PASS",
                 "shard_id":sid,"from_block":start,"to_block":end,"sample_sha256":sample_receipt["sample_sha256"],
                 "unique_event_count":len(seen),"canonical_event_digest_sha256":hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest(),
                 "event_counts":dict(counts),"variable_debt_balance_transfer_count":debt_bt,
                 "delta_rows":rows,"transport_stats":dict(stats),"safety":safety()}
    except Exception as exc:
        receipt={"lab_id":LAB_ID,"phase":"R1_TOKEN_DELTA_SHARD_V0_2",
                 "classification":"RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE",
                 "shard_id":sid,"from_block":start,"to_block":end,
                 "failure":f"{type(exc).__name__}: {str(exc)[:1200]}","transport_stats":dict(stats),"safety":safety()}
    (out/f"token_shard_{sid:02d}.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"shard":sid,"classification":receipt["classification"],"events":receipt.get("unique_event_count"),"delta_rows":len(receipt.get("delta_rows") or [])},sort_keys=True))
    return 0 if receipt["classification"]=="TOKEN_SHARD_PASS" else 2

def replay_targets(block_deltas,meta):
    targets=[]; negatives=[]
    for (user,token),byblock in sorted(block_deltas.items()):
        bal=0; touched=False; bs=sorted(byblock.items()); pos=0
        for ab in AUDIT_BLOCKS:
            while pos<len(bs) and bs[pos][0]<=ab:
                bn,d=bs[pos]; bal+=d; touched=True
                if bal<0: negatives.append({"user":user,"token":token,"kind":meta[token]["kind"],"underlying":meta[token]["underlying"],"block":bn,"balance":str(bal),"delta":str(d)})
                pos+=1
            if touched: targets.append({"user":user,"token":token,"kind":meta[token]["kind"],"underlying":meta[token]["underlying"],"block":ab,"replayed_scaled_balance":str(bal)})
    return targets,negatives

def rpc_batch(endpoint,items,stats):
    out={}; ses=requests.Session(); headers={"Content-Type":"application/json","User-Agent":f"{LAB_ID}/r1-sharded-v0.2"}
    for start in range(0,len(items),40):
        chunk=items[start:start+40]; payload=[]
        for idx,t in enumerate(chunk,start=start):
            data="0x"+SCALED_BALANCE_SELECTOR+"0"*24+t["user"][2:]
            payload.append({"jsonrpc":"2.0","id":idx,"method":"eth_call","params":[{"to":t["token"],"data":data},hex(int(t["block"]))]})
        resp=None
        for attempt in range(3):
            try:
                r=ses.post(endpoint,json=payload,headers=headers,timeout=(10,45)); stats["http_attempts"]+=1
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
            if isinstance(rr,str) and rr.startswith("0x"):
                try: out[idx]=int(rr,16); stats["usable_results"]+=1
                except ValueError: stats["invalid_results"]+=1
            else: stats["invalid_results"]+=1
    ses.close(); return out

def validate_targets(targets):
    vals={}; stats={}
    for ep in RPC_ENDPOINTS:
        cs=Counter(); vals[ep]=rpc_batch(ep,targets,cs); stats[ep]=dict(cs)
    fails=[]; tech=prov=rec=False
    for i,t in enumerate(targets):
        got={ep:v[i] for ep,v in vals.items() if i in v}; uniq=sorted(set(got.values())); expected=int(t["replayed_scaled_balance"]); f=None
        if len(got)<2: f="INSUFFICIENT_ARCHIVE_RPC_QUORUM"; tech=True
        elif len(uniq)!=1: f="ARCHIVE_RPC_DISAGREEMENT"; prov=True
        elif uniq[0]!=expected: f="REPLAY_MISMATCH"; rec=True
        if f: fails.append({**t,"failure":f,"usable_endpoint_values":{k:str(v) for k,v in got.items()}})
    c="RECONSTRUCTION_PROVENANCE_FAILURE" if prov else ("RECONSTRUCTION_RECONCILIATION_FAILURE" if rec else ("RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE" if tech else "R1_AUDIT_PASS"))
    return c,fails,stats

def audit_aggregate()->int:
    out=Path("r1_scaled_ledger_audit_output"); out.mkdir(parents=True,exist_ok=True)
    receipt={"lab_id":LAB_ID,"phase":"R1_SCALED_LEDGER_AUDIT_SHARDED_V0_2_OUTCOME_BLIND",
             "protocol":"AAVE_LIQUIDATION_OVERHANG_001_R1_EXECUTION_PROTOCOL_V0_2",
             "frozen_from_block":FROM_BLOCK,"frozen_to_block":TO_BLOCK,"audit_blocks":AUDIT_BLOCKS,"safety":safety()}
    try:
        sample=load_one("downloaded_borrow_sample","BORROW_SAMPLE_PASS"); bootstrap=load_bootstrap(); meta,_,_=build_token_maps(bootstrap)
        files=sorted(Path("downloaded_token_shards").rglob("*.json"))
        if len(files)!=8: raise RuntimeError(f"expected 8 token shards, got {len(files)}")
        rs=[json.loads(p.read_text()) for p in files]; rs.sort(key=lambda x:int(x["shard_id"]))
        bd=defaultdict(lambda:defaultdict(int)); counts=Counter(); debt=0; event_total=0
        for i,r in enumerate(rs):
            if r.get("classification")!="TOKEN_SHARD_PASS": raise RuntimeError(f"token shard {i} not pass")
            if (int(r["from_block"]),int(r["to_block"]))!=SHARDS[i]: raise RuntimeError("token shard range mismatch")
            if r.get("sample_sha256")!=sample["sample_sha256"]: raise RuntimeError("sample digest mismatch")
            counts.update(r.get("event_counts") or {}); debt+=int(r.get("variable_debt_balance_transfer_count",0)); event_total+=int(r.get("unique_event_count",0))
            for row in r.get("delta_rows") or []:
                bd[(row["user"],row["token"])][int(row["block"])]+=int(row["delta"])
        targets,negatives=replay_targets(bd,meta)
        receipt.update({"unique_borrower_count":sample["unique_borrower_count"],"sample_borrowers":sample["sample_borrowers"],
                        "sample_sha256":sample["sample_sha256"],"scaled_event_counts":dict(sorted(counts.items())),
                        "unique_token_event_count":event_total,"touched_user_token_pairs":len(bd),
                        "validation_target_count":len(targets),"negative_replay_states":negatives[:100],
                        "variable_debt_balance_transfer_count":debt})
        if debt:
            receipt["classification"]="RECONSTRUCTION_PROVENANCE_FAILURE"; receipt["failure"]="variable-debt BalanceTransfer observed despite non-transferability"
        elif negatives:
            receipt["classification"]="RECONSTRUCTION_RECONCILIATION_FAILURE"; receipt["failure"]=f"negative scaled replay state(s): {len(negatives)}"
        elif not targets:
            receipt["classification"]="RECONSTRUCTION_INSUFFICIENT_COVERAGE"; receipt["failure"]="no deterministic historical validation targets"
        else:
            c,fails,rpcstats=validate_targets(targets); receipt["classification"]=c; receipt["validation_failures"]=fails[:250]
            receipt["validation_failure_count"]=len(fails); receipt["archive_rpc_stats"]=rpcstats
            receipt["validated_target_count"]=len(targets)-len(fails)
            receipt["target_digest_sha256"]=hashlib.sha256("\n".join(f"{t['block']}|{t['user']}|{t['token']}|{t['replayed_scaled_balance']}" for t in targets).encode()).hexdigest()
            receipt["validation_targets"]=targets
    except Exception as exc:
        receipt["classification"]="RECONSTRUCTION_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1200]}"
    (out/"AAVE_LIQUIDATION_OVERHANG_001_R1_SCALED_LEDGER_AUDIT_V0_2.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":receipt["classification"],"sample_size":len(receipt.get("sample_borrowers") or []),"touched_pairs":receipt.get("touched_user_token_pairs"),"validation_targets":receipt.get("validation_target_count"),"validation_failures":receipt.get("validation_failure_count")},sort_keys=True))
    return 0 if receipt["classification"]=="R1_AUDIT_PASS" else 2

def safety():
    return {"health_factor_computed":False,"overhang_computed":False,"future_liquidation_outcome_computed":False,
            "market_prices_opened":False,"returns_opened":False,"pnl_opened":False,
            "accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}

def main()->int:
    phase=os.environ.get("R1_PHASE","")
    return {"borrower_shard":borrower_shard,"borrower_aggregate":borrower_aggregate,
            "token_shard":token_shard,"audit_aggregate":audit_aggregate}.get(phase,lambda: (_ for _ in ()).throw(RuntimeError(f"unknown R1_PHASE {phase}")))()

if __name__=="__main__": sys.exit(main())

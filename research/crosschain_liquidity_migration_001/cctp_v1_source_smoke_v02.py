#!/usr/bin/env python3
"""CCLM CCTP V1 hybrid historical source smoke V0.2.

Ethereum: Blast public RPC for historical block boundaries + SQD Portal for logs.
Avalanche: official C-Chain RPC for boundaries and logs.
Source cohort: 2023-08-20 UTC.
Destination settlement window: through 2023-08-22 UTC.
No market outcomes.
"""
from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from cctp_v1_message import decode_single_dynamic_bytes_abi, parse_cctp_message_v1

OUT=Path("artifacts/cclm_cctp_v1_source_smoke_v02.json")

CHAINS={
  0:{
    "name":"Ethereum",
    "boundary_rpc":"https://eth-mainnet.public.blastapi.io",
    "log_transport":"sqd",
    "message_transmitter":"0x0a992d191deec32afe36203ad87d7d289a738f81",
    "token_messenger":"0xbd3fa81b58ba92a82136038b25adec7066af3155",
    "usdc":"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
  },
  1:{
    "name":"Avalanche",
    "boundary_rpc":"https://api.avax.network/ext/bc/C/rpc",
    "log_transport":"rpc",
    "message_transmitter":"0x8186359af5f57fbb40c6b14a588d2a59c0c29880",
    "token_messenger":"0x6b25532e1060ce10cc3b0a99e5683b91bfde6982",
    "usdc":"0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e",
  },
}

TOPIC_SENT="0x8c5261668696ce22758910d05bab8f186d6eb247ceac2af2e82c7dc17669b036"
TOPIC_RECEIVED="0x58200b4c34ae05ee816d710053fff3fb75af4395915d3d2a771b24aa10e3cc5d"
TOPIC_DEPOSIT="0x2fa9ca894982930190727e75500a97d8dc500233a5065e0f3126c48fbe0343c0"
TOPIC_MINT="0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6"

SOURCE_START=int(datetime(2023,8,20,tzinfo=timezone.utc).timestamp())
SOURCE_END=int(datetime(2023,8,21,tzinfo=timezone.utc).timestamp())-1
DEST_END=int(datetime(2023,8,23,tzinfo=timezone.utc).timestamp())-1

def post_json(url,payload,timeout=60):
    req=urllib.request.Request(
      url,
      data=json.dumps(payload).encode(),
      headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"CryptoLab-CCLM-001/0.2"},
      method="POST",
    )
    with urllib.request.urlopen(req,timeout=timeout) as r:
        raw=r.read()
    return raw

def rpc(url,method,params,timeout=45):
    raw=post_json(url,{"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout)
    obj=json.loads(raw.decode())
    if obj.get("error"):
        raise RuntimeError(f"{method}:{obj['error']}")
    return obj.get("result")

def get_block(url,n):
    return rpc(url,"eth_getBlockByNumber",[hex(n),False])

def block_ts(b):
    return int(b["timestamp"],16)

def find_block_at_or_after(url,target_ts):
    lo=0
    hi=int(rpc(url,"eth_blockNumber",[]),16)
    while lo<hi:
        mid=(lo+hi)//2
        b=get_block(url,mid)
        if b is None:
            raise RuntimeError(f"MISSING_BLOCK:{mid}")
        if block_ts(b)<target_ts: lo=mid+1
        else: hi=mid
    return lo

def rpc_logs(url,address,topics,start,end,span=2000):
    out=[]; cur=start
    while cur<=end:
        hi=min(end,cur+span-1)
        try:
            rows=rpc(url,"eth_getLogs",[{
              "fromBlock":hex(cur),"toBlock":hex(hi),
              "address":address,"topics":[topics],
            }],60) or []
            out.extend(rows)
            cur=hi+1
        except Exception:
            if span<=50: raise
            # retry only the unresolved suffix with a smaller deterministic chunk
            span=max(50,span//2)
    return out

def parse_json_or_ndjson(raw):
    txt=raw.decode("utf-8","replace").strip()
    if not txt:return []
    try:return json.loads(txt)
    except Exception:
        out=[]
        for line in txt.splitlines():
            line=line.strip()
            if line:
                out.append(json.loads(line))
        return out

def sqd_logs(address,topic0s,start,end):
    query={
      "type":"evm",
      "fromBlock":start,
      "toBlock":end,
      "fields":{
        "block":{"number":True,"timestamp":True,"hash":True},
        "log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}
      },
      "logs":[{"address":[address],"topic0":topic0s}],
    }
    raw=post_json("https://portal.sqd.dev/datasets/ethereum-mainnet/stream",query,90)
    obj=parse_json_or_ndjson(raw)
    result=[]

    def walk(v,block_number=None):
        if isinstance(v,dict):
            bn=block_number
            header=v.get("header")
            if isinstance(header,dict) and header.get("number") is not None:
                bn=header.get("number")
            block=v.get("block")
            if isinstance(block,dict) and block.get("number") is not None:
                bn=block.get("number")
            if v.get("blockNumber") is not None:
                bn=v.get("blockNumber")
            if all(k in v for k in ("address","topics","data")):
                topics=v.get("topics") or []
                if str(v.get("address","")).lower()==address.lower() and topics and str(topics[0]).lower() in {x.lower() for x in topic0s}:
                    if isinstance(bn,str):
                        try: bn=int(bn,16) if bn.startswith("0x") else int(bn)
                        except Exception: bn=None
                    li=v.get("logIndex",v.get("log_index",0))
                    if isinstance(li,str):
                        try: li=int(li,16) if li.startswith("0x") else int(li)
                        except Exception: li=0
                    result.append({
                      "address":str(v["address"]).lower(),
                      "topics":[str(x).lower() for x in topics],
                      "data":str(v.get("data","0x")).lower(),
                      "transactionHash":v.get("transactionHash") or v.get("transaction_hash"),
                      "blockNumber":hex(bn) if isinstance(bn,int) else None,
                      "logIndex":hex(li if isinstance(li,int) else 0),
                    })
            for child in v.values(): walk(child,bn)
        elif isinstance(v,list):
            for child in v: walk(child,block_number)
    walk(obj)
    # Recursive traversal can encounter references more than once in some response shapes.
    uniq={}
    for x in result:
        key=(x.get("transactionHash"),x.get("logIndex"),x.get("topics",[None])[0],x.get("data"))
        uniq[key]=x
    return list(uniq.values()), hashlib.sha256(raw).hexdigest(), len(raw)

def get_logs(domain,address,topic0s,start,end):
    cfg=CHAINS[domain]
    if cfg["log_transport"]=="sqd":
        logs,raw_hash,raw_bytes=sqd_logs(address,topic0s,start,end)
        return logs,{"transport":"SQD_PORTAL","raw_sha256":raw_hash,"raw_bytes":raw_bytes}
    rows=rpc_logs(cfg["boundary_rpc"],address,topic0s,start,end)
    canonical=json.dumps(rows,sort_keys=True,separators=(",",":")).encode()
    return rows,{"transport":"OFFICIAL_RPC","raw_sha256":hashlib.sha256(canonical).hexdigest(),"raw_bytes":len(canonical)}

def b32_addr(addr):
    return "0x"+"0"*24+addr.lower().replace("0x","")

def decode_received(log):
    topics=log.get("topics") or []
    raw=bytes.fromhex((log.get("data") or "0x")[2:])
    if len(topics)<3 or len(raw)<128:return None
    source_domain=int.from_bytes(raw[0:32],"big")
    sender="0x"+raw[32:64].hex()
    offset=int.from_bytes(raw[64:96],"big")
    if offset+32>len(raw):return None
    n=int.from_bytes(raw[offset:offset+32],"big")
    body=raw[offset+32:offset+32+n]
    if len(body)!=n:return None
    return {
      "source_domain":source_domain,
      "nonce":int(topics[2],16),
      "sender":sender.lower(),
      "body_hex":"0x"+body.hex(),
      "tx_hash":str(log.get("transactionHash") or "").lower(),
    }

def decode_mint(log):
    topics=log.get("topics") or []
    raw=bytes.fromhex((log.get("data") or "0x")[2:])
    if len(topics)<3 or len(raw)<32:return None
    return {
      "recipient":"0x"+topics[1][-40:].lower(),
      "token":"0x"+topics[2][-40:].lower(),
      "amount_atomic":int.from_bytes(raw[0:32],"big"),
      "tx_hash":str(log.get("transactionHash") or "").lower(),
    }

receipt={
 "lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001",
 "child_id":"CCLM-CCTP-USDC-001",
 "stage":"CCTP_V1_HYBRID_SOURCE_SMOKE_V0.2",
 "window":{"source_start":"2023-08-20T00:00:00Z","source_end":"2023-08-20T23:59:59Z","destination_pair_end":"2023-08-22T23:59:59Z"},
 "chains":{},"routes":[],"errors":[],
 "market_outcomes_opened":False,"pnl_opened":False,"mutation":False,
 "access_2025":False,"access_2026":False,
}

try:
    bounds={}
    for domain,cfg in CHAINS.items():
        s=find_block_at_or_after(cfg["boundary_rpc"],SOURCE_START)
        se=find_block_at_or_after(cfg["boundary_rpc"],SOURCE_END+1)-1
        de=find_block_at_or_after(cfg["boundary_rpc"],DEST_END+1)-1
        bounds[domain]=(s,se,de)
        receipt["chains"][str(domain)]={"name":cfg["name"],"source_start_block":s,"source_end_block":se,"destination_end_block":de}

    logs={}
    for domain,cfg in CHAINS.items():
        s,se,de=bounds[domain]
        sent,ev1=get_logs(domain,cfg["message_transmitter"],[TOPIC_SENT],s,se)
        dep,ev2=get_logs(domain,cfg["token_messenger"],[TOPIC_DEPOSIT],s,se)
        recv,ev3=get_logs(domain,cfg["message_transmitter"],[TOPIC_RECEIVED],s,de)
        mint,ev4=get_logs(domain,cfg["token_messenger"],[TOPIC_MINT],s,de)
        logs[domain]={"sent":sent,"deposits":dep,"received":recv,"mints":mint}
        receipt["chains"][str(domain)].update({
          "message_sent_logs":len(sent),"deposit_for_burn_logs":len(dep),
          "message_received_logs":len(recv),"mint_and_withdraw_logs":len(mint),
          "evidence":[ev1,ev2,ev3,ev4],
        })

    for sd,dd in ((0,1),(1,0)):
        source=[]
        for log in logs[sd]["sent"]:
            try:
                payload=decode_single_dynamic_bytes_abi(log.get("data","0x"))
                msg=parse_cctp_message_v1(payload)
            except Exception:
                continue
            if msg.source_domain!=sd or msg.destination_domain!=dd:continue
            if msg.sender.lower()!=b32_addr(CHAINS[sd]["token_messenger"]):continue
            if msg.recipient.lower()!=b32_addr(CHAINS[dd]["token_messenger"]):continue
            if msg.burn.burn_token[-40:].lower()!=CHAINS[sd]["usdc"][-40:].lower():continue
            source.append({
              "nonce":msg.nonce,"sender":msg.sender.lower(),"body_hex":"0x"+payload[116:].hex(),
              "amount_atomic":msg.burn.amount_atomic,"mint_recipient":"0x"+msg.burn.mint_recipient[-40:].lower(),
              "source_tx":str(log.get("transactionHash") or "").lower(),
              "message_sha256":hashlib.sha256(payload).hexdigest(),
            })

        recv_index={}
        for log in logs[dd]["received"]:
            x=decode_received(log)
            if x and x["source_domain"]==sd:
                recv_index.setdefault((sd,x["nonce"]),[]).append(x)
        mint_index={}
        for log in logs[dd]["mints"]:
            x=decode_mint(log)
            if x: mint_index.setdefault(x["tx_hash"],[]).append(x)

        paired=unpaired=ambiguous=mismatch=0; samples=[]
        reason_counts={"NO_RECEIVED_NONCE":0,"RECEIVED_SEMANTIC_MISMATCH":0,"AMBIGUOUS_RECEIVED":0,"MINT_OR_AMOUNT_MISMATCH":0}
        unpaired_diagnostics=[]
        for x in source:
            raw_candidates=recv_index.get((sd,x["nonce"]),[])
            if not raw_candidates:
                unpaired+=1; reason_counts["NO_RECEIVED_NONCE"]+=1
                if len(unpaired_diagnostics)<30: unpaired_diagnostics.append({"nonce":x["nonce"],"reason":"NO_RECEIVED_NONCE","source_tx":x["source_tx"]})
                continue
            cand=[d for d in raw_candidates if d["sender"]==x["sender"] and d["body_hex"].lower()==x["body_hex"].lower()]
            if not cand:
                unpaired+=1; reason_counts["RECEIVED_SEMANTIC_MISMATCH"]+=1
                if len(unpaired_diagnostics)<30: unpaired_diagnostics.append({"nonce":x["nonce"],"reason":"RECEIVED_SEMANTIC_MISMATCH","received_candidates":len(raw_candidates),"source_tx":x["source_tx"]})
                continue
            if len(cand)!=1:
                ambiguous+=1; reason_counts["AMBIGUOUS_RECEIVED"]+=1
                if len(unpaired_diagnostics)<30: unpaired_diagnostics.append({"nonce":x["nonce"],"reason":"AMBIGUOUS_RECEIVED","candidate_count":len(cand),"source_tx":x["source_tx"]})
                continue
            d=cand[0]
            m=[z for z in mint_index.get(d["tx_hash"],[]) if z["amount_atomic"]==x["amount_atomic"] and z["token"]==CHAINS[dd]["usdc"] and z["recipient"]==x["mint_recipient"]]
            if len(m)!=1:
                mismatch+=1; reason_counts["MINT_OR_AMOUNT_MISMATCH"]+=1
                if len(unpaired_diagnostics)<30: unpaired_diagnostics.append({"nonce":x["nonce"],"reason":"MINT_OR_AMOUNT_MISMATCH","mint_candidates_in_tx":len(mint_index.get(d["tx_hash"],[])),"source_tx":x["source_tx"],"destination_tx":d["tx_hash"]})
                continue
            paired+=1
            if len(samples)<5:samples.append({"nonce":x["nonce"],"amount_atomic":x["amount_atomic"],"source_tx":x["source_tx"],"destination_tx":d["tx_hash"],"message_sha256":x["message_sha256"]})
        received_nonces=sorted({nonce for (src,nonce) in recv_index if src==sd})
        receipt["routes"].append({
          "source_domain":sd,"destination_domain":dd,"source_messages":len(source),"paired":paired,"unpaired":unpaired,
          "ambiguous":ambiguous,"mint_or_amount_mismatch":mismatch,"samples":samples,
          "source_nonces":sorted(x["nonce"] for x in source),
          "destination_received_nonces_for_source":received_nonces,
          "nonce_overlap_count":len(set(x["nonce"] for x in source) & set(received_nonces)),
          "unpaired_reason_counts":reason_counts,
          "unpaired_diagnostics":unpaired_diagnostics,
        })

    total=sum(x["source_messages"] for x in receipt["routes"])
    paired=sum(x["paired"] for x in receipt["routes"])
    receipt["pair_rate"]=paired/total if total else None
    receipt["classification"]="SOURCE_SMOKE_NO_EVENTS" if total==0 else ("SOURCE_SMOKE_PASS" if paired==total else "SOURCE_SMOKE_PARTIAL")
except Exception as e:
    receipt["classification"]="SOURCE_SMOKE_TECHNICAL_FAILURE"
    receipt["errors"].append(f"{type(e).__name__}:{str(e)[:800]}")

OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":receipt.get("classification"),"pair_rate":receipt.get("pair_rate"),"routes":receipt.get("routes"),"errors":receipt.get("errors")},indent=2))

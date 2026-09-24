#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from cctp_v1_message import decode_single_dynamic_bytes_abi,parse_cctp_message_v1

OUT=Path("artifacts/cclm_cctp_v1_terminal_settlement_audit_v01.json")
AVAX="https://api.avax.network/ext/bc/C/rpc"
ETH="https://eth-mainnet.public.blastapi.io"
SQD="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
AVAX_MT="0x8186359af5f57fbb40c6b14a588d2a59c0c29880"
AVAX_TM="0x6b25532e1060ce10cc3b0a99e5683b91bfde6982"
AVAX_USDC="0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e"
ETH_MT="0x0a992d191deec32afe36203ad87d7d289a738f81"
ETH_TM="0xbd3fa81b58ba92a82136038b25adec7066af3155"
ETH_USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
TOPIC_SENT="0x8c5261668696ce22758910d05bab8f186d6eb247ceac2af2e82c7dc17669b036"
TOPIC_RECEIVED="0x58200b4c34ae05ee816d710053fff3fb75af4395915d3d2a771b24aa10e3cc5d"
TOPIC_MINT="0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6"
S0=int(datetime(2023,8,20,tzinfo=timezone.utc).timestamp())
S1=int(datetime(2023,8,21,tzinfo=timezone.utc).timestamp())-1
CUT=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp())-1

def post(url,payload,timeout=90):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"CryptoLab-CCLM-001-Terminal/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()

def rpc(url,method,params):
    obj=json.loads(post(url,{"jsonrpc":"2.0","id":1,"method":method,"params":params},60).decode())
    if obj.get("error"):raise RuntimeError(f"{method}:{obj['error']}")
    return obj.get("result")

def find_block(url,ts):
    lo=0;hi=int(rpc(url,"eth_blockNumber",[]),16)
    while lo<hi:
        mid=(lo+hi)//2;b=rpc(url,"eth_getBlockByNumber",[hex(mid),False])
        if int(b["timestamp"],16)<ts:lo=mid+1
        else:hi=mid
    return lo

def logs_rpc(url,address,topic,start,end,span=2000):
    out=[];cur=start
    while cur<=end:
        hi=min(end,cur+span-1)
        try:
            out.extend(rpc(url,"eth_getLogs",[{"fromBlock":hex(cur),"toBlock":hex(hi),"address":address,"topics":[topic]}]) or [])
            cur=hi+1
        except Exception:
            if span<=50:raise
            span=max(50,span//2)
    return out

def b32(addr):return "0x"+"0"*24+addr.lower().replace("0x","")

def parse_any(raw):
    txt=raw.decode("utf-8","replace").strip()
    try:return json.loads(txt)
    except Exception:return [json.loads(x) for x in txt.splitlines() if x.strip()]

def sqd_nonce_logs(start,end,nonce):
    nonce_topic="0x"+int(nonce).to_bytes(32,"big").hex()
    q={
      "type":"evm","fromBlock":start,"toBlock":end,
      "fields":{"block":{"number":True,"timestamp":True},"log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}},
      "logs":[{"address":[ETH_MT],"topic0":[TOPIC_RECEIVED],"topic2":[nonce_topic]}],
    }
    raw=post(SQD,q,90);obj=parse_any(raw);found=[]
    def walk(v,bn=None):
        if isinstance(v,dict):
            if isinstance(v.get("header"),dict) and v["header"].get("number") is not None:bn=v["header"]["number"]
            if v.get("blockNumber") is not None:bn=v["blockNumber"]
            if str(v.get("address","")).lower()==ETH_MT and isinstance(v.get("topics"),list) and v["topics"] and str(v["topics"][0]).lower()==TOPIC_RECEIVED:
                found.append({"topics":[str(x).lower() for x in v["topics"]],"data":str(v.get("data","0x")).lower(),"transactionHash":v.get("transactionHash") or v.get("transaction_hash"),"blockNumber":bn})
            for z in v.values():walk(z,bn)
        elif isinstance(v,list):
            for z in v:walk(z,bn)
    walk(obj)
    uniq={}
    for x in found:uniq[(x["transactionHash"],tuple(x["topics"]),x["data"])]=x
    return list(uniq.values()),hashlib.sha256(raw).hexdigest(),len(raw)

def decode_received(log):
    t=log["topics"];raw=bytes.fromhex(log["data"][2:])
    if len(t)<3 or len(raw)<128:return None
    sd=int.from_bytes(raw[0:32],"big");sender="0x"+raw[32:64].hex();off=int.from_bytes(raw[64:96],"big")
    if off+32>len(raw):return None
    n=int.from_bytes(raw[off:off+32],"big");body=raw[off+32:off+32+n]
    if len(body)!=n:return None
    return {"source_domain":sd,"nonce":int(t[2],16),"sender":sender.lower(),"body_hex":"0x"+body.hex(),"tx":str(log.get("transactionHash") or "").lower()}

def mint_logs_from_receipt(tx):
    rec=rpc(ETH,"eth_getTransactionReceipt",[tx])
    out=[]
    for log in (rec or {}).get("logs",[]):
        topics=[str(x).lower() for x in log.get("topics",[])]
        if str(log.get("address","")).lower()!=ETH_TM or not topics or topics[0]!=TOPIC_MINT:continue
        raw=bytes.fromhex((log.get("data") or "0x")[2:])
        if len(topics)>=3 and len(raw)>=32:
            out.append({"recipient":"0x"+topics[1][-40:],"token":"0x"+topics[2][-40:],"amount":int.from_bytes(raw[:32],"big")})
    return out

receipt={"lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001","child_id":"CCLM-CCTP-USDC-001","stage":"CCTP_V1_TERMINAL_SETTLEMENT_AUDIT_V0.1","captured_at_utc":datetime.now(timezone.utc).isoformat(),"market_outcomes_opened":False,"pnl_opened":False,"mutation":False,"access_2025":False,"access_2026":False}
try:
    avs=find_block(AVAX,S0);ave=find_block(AVAX,S1+1)-1
    ets=find_block(ETH,S0);ete=find_block(ETH,CUT+1)-1
    sent=logs_rpc(AVAX,AVAX_MT,TOPIC_SENT,avs,ave)
    source={}
    for log in sent:
        try:msg=parse_cctp_message_v1(decode_single_dynamic_bytes_abi(log.get("data","0x")))
        except Exception:continue
        if msg.source_domain!=1 or msg.destination_domain!=0:continue
        if msg.sender.lower()!=b32(AVAX_TM) or msg.recipient.lower()!=b32(ETH_TM):continue
        if msg.burn.burn_token[-40:].lower()!=AVAX_USDC[-40:]:continue
        source[msg.nonce]={"nonce":msg.nonce,"sender":msg.sender.lower(),"body_hex":"0x"+decode_single_dynamic_bytes_abi(log.get("data","0x"))[116:].hex(),"amount":msg.burn.amount_atomic,"recipient":"0x"+msg.burn.mint_recipient[-40:].lower(),"source_tx":str(log.get("transactionHash") or "").lower()}
    rows=[];counts={}
    for nonce,x in sorted(source.items()):
        try:
            candidates,raw_hash,raw_bytes=sqd_nonce_logs(ets,ete,nonce)
            exact=[]
            for log in candidates:
                d=decode_received(log)
                if d and d["source_domain"]==1 and d["nonce"]==nonce and d["sender"]==x["sender"] and d["body_hex"].lower()==x["body_hex"].lower():exact.append(d)
            if not exact:status="NOT_RECEIVED_BY_CUTOFF"
            elif len(exact)!=1:status="AMBIGUOUS_RECEIVED"
            else:
                m=mint_logs_from_receipt(exact[0]["tx"])
                ok=[z for z in m if z["token"]==ETH_USDC and z["recipient"]==x["recipient"] and z["amount"]==x["amount"]]
                status="SETTLED_CANONICAL" if len(ok)==1 else "MINT_OR_AMOUNT_MISMATCH"
            row={"nonce":nonce,"status":status,"source_tx":x["source_tx"],"destination_tx":exact[0]["tx"] if len(exact)==1 else None,"sqd_raw_sha256":raw_hash,"sqd_raw_bytes":raw_bytes,"candidate_received_logs":len(candidates)}
        except Exception as e:
            status="TECHNICAL_FAILURE";row={"nonce":nonce,"status":status,"source_tx":x["source_tx"],"error":f"{type(e).__name__}:{str(e)[:500]}"}
        counts[status]=counts.get(status,0)+1;rows.append(row)
    settled=counts.get("SETTLED_CANONICAL",0)
    receipt.update({"source_cohort_size":len(source),"destination_cutoff":"2024-12-31T23:59:59Z","status_counts":counts,"settled_rate":settled/len(source) if source else None,"rows":rows})
    receipt["classification"]="TERMINAL_SETTLEMENT_AUDIT_PASS" if source and settled==len(source) else ("TERMINAL_SETTLEMENT_AUDIT_PARTIAL" if source else "TERMINAL_SETTLEMENT_AUDIT_NO_SOURCE")
except Exception as e:
    receipt["classification"]="TERMINAL_SETTLEMENT_AUDIT_TECHNICAL_FAILURE";receipt["error"]=f"{type(e).__name__}:{str(e)[:700]}"

OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:receipt.get(k) for k in ("classification","source_cohort_size","status_counts","settled_rate","error")},indent=2))

#!/usr/bin/env python3
import hashlib,json,urllib.request
from datetime import datetime,timezone
from pathlib import Path

RPC="https://api.avax.network/ext/bc/C/rpc"
MT="0x8186359af5f57fbb40c6b14a588d2a59c0c29880"
TM="0x6b25532e1060ce10cc3b0a99e5683b91bfde6982"
DEST_USDC="0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e"
SOURCE_TM="0xbd3fa81b58ba92a82136038b25adec7066af3155"
SOURCE_USDC="0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
TOPIC_RECEIVED="0x58200b4c34ae05ee816d710053fff3fb75af4395915d3d2a771b24aa10e3cc5d"
TOPIC_MINT="0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6"
TXS=[
 "0x634bb8aa7cc276dd5b40b7d03bcb18de1763faf9f7cf13bb778b00ce4c2318d1",
 "0xb7b9fef5c25a37b47ac136105dae3f319a21475f35a02d4dd713d42c55867d8e",
]
FIXED_NONCES={31476,31477,40913,40914}
OUT=Path("artifacts/cclm002_batch_order_adjudication_v01.json")

def rpc(method,params):
    data=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(RPC,data=data,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-CCLM002-BatchOrder/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r:x=json.loads(r.read().decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

def b32(addr):return "0x"+"0"*24+addr.lower().replace("0x","")

def parse_received(log):
    ts=log.get("topics") or [];raw=bytes.fromhex((log.get("data") or "0x")[2:])
    if len(ts)<3 or len(raw)<128:return None
    sd=int.from_bytes(raw[:32],"big");sender="0x"+raw[32:64].hex();off=int.from_bytes(raw[64:96],"big")
    if off+32>len(raw):return None
    n=int.from_bytes(raw[off:off+32],"big");body=raw[off+32:off+32+n]
    if len(body)!=132:return None
    return {"kind":"RECEIVED","log_index":int(log["logIndex"],16),"source_domain":sd,"nonce":int(ts[2],16),
      "sender":sender.lower(),"body_version":int.from_bytes(body[:4],"big"),
      "burn_token":"0x"+body[4:36].hex(),"recipient":"0x"+body[36:68].hex(),
      "amount":int.from_bytes(body[68:100],"big"),"body_sha256":hashlib.sha256(body).hexdigest()}

def parse_mint(log):
    ts=log.get("topics") or [];raw=bytes.fromhex((log.get("data") or "0x")[2:])
    if len(ts)<3 or len(raw)<32:return None
    return {"kind":"MINT","log_index":int(log["logIndex"],16),
      "recipient":"0x"+ts[1][-40:].lower(),"token":"0x"+ts[2][-40:].lower(),
      "amount":int.from_bytes(raw[:32],"big")}

rows=[];all_pairs=[];ok=True
for tx in TXS:
    rc=rpc("eth_getTransactionReceipt",[tx])
    relevant=[]
    for log in rc.get("logs",[]):
        addr=str(log.get("address","")).lower();topic0=(log.get("topics") or [None])[0]
        if addr==TM and topic0 and topic0.lower()==TOPIC_MINT:
            x=parse_mint(log)
            if x:relevant.append(x)
        elif addr==MT and topic0 and topic0.lower()==TOPIC_RECEIVED:
            x=parse_received(log)
            if x and x["source_domain"]==0 and x["sender"]==b32(SOURCE_TM) and x["body_version"]==0 and x["burn_token"][-40:].lower()==SOURCE_USDC[-40:].lower():
                relevant.append(x)
    relevant.sort(key=lambda x:x["log_index"])
    pairs=[];previous_received=-1
    for i,x in enumerate(relevant):
        if x["kind"]!="RECEIVED":continue
        if x["nonce"] not in FIXED_NONCES:
            previous_received=x["log_index"]
            continue
        candidates=[m for m in relevant if m["kind"]=="MINT" and previous_received<m["log_index"]<x["log_index"]
                    and m["token"]==DEST_USDC and m["amount"]==x["amount"]
                    and m["recipient"]==("0x"+x["recipient"][-40:].lower())]
        if len(candidates)==1:
            m=candidates[0]
            pairs.append({"nonce":x["nonce"],"mint_log_index":m["log_index"],"received_log_index":x["log_index"],
                          "amount":x["amount"],"body_sha256":x["body_sha256"],"pass":True})
        else:
            pairs.append({"nonce":x["nonce"],"received_log_index":x["log_index"],"candidate_count":len(candidates),"pass":False})
            ok=False
        previous_received=x["log_index"]
    rows.append({"transaction_hash":tx,"receipt_block":int(rc["blockNumber"],16),"relevant_event_order":relevant,"pairs":pairs,
                 "receipt_logs_sha256":hashlib.sha256(json.dumps(rc.get("logs",[]),sort_keys=True,separators=(",",":")).encode()).hexdigest()})
    all_pairs.extend(pairs)

if len(all_pairs)!=4:ok=False
if len({(r["transaction_hash"],p.get("mint_log_index")) for r in rows for p in r["pairs"] if p.get("pass")})!=4:ok=False
receipt={"lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001","child_id":"CCLM-CCTP-SETTLED-FLOW-002",
 "stage":"BATCH_ORDER_ADJUDICATION_V0.1","captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"BATCHING_PARSER_BUG_CONFIRMED" if ok else "BATCH_PAIRING_UNRESOLVED",
 "fixed_transaction_count":len(TXS),"fixed_message_pair_count":len(all_pairs),"transactions":rows,
 "canonical_rule_changed":False,"market_outcomes_opened":False,"pnl_opened":False,"mutation":False}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if not ok:raise SystemExit(2)

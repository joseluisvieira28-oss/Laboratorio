#!/usr/bin/env python3
import hashlib,json,urllib.request,urllib.error,time
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
OUT=Path("artifacts/cclm002_semantic_mismatch_diagnostic_v01.json")

def rpc(method,params,timeout=60):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for a in range(5):
        try:
            req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-CCLM002-Diag/0.1"},method="POST")
            with urllib.request.urlopen(req,timeout=timeout) as r:x=json.loads(r.read().decode())
            if x.get("error"):raise RuntimeError(x["error"])
            return x.get("result")
        except Exception as e:
            last=e
            if a==4:raise
            time.sleep(1.5*(a+1))
    raise last

def block(n):return rpc("eth_getBlockByNumber",[hex(n),False])
def ts(b):return int(b["timestamp"],16)
def find_block(target):
    lo=0;hi=int(rpc("eth_blockNumber",[]),16)
    while lo<hi:
        mid=(lo+hi)//2;b=block(mid)
        if ts(b)<target:lo=mid+1
        else:hi=mid
    return lo

def logs(address,topic,start,end):
    out=[];cur=start;span=2000
    while cur<=end:
        hi=min(end,cur+span-1)
        try:
            out.extend(rpc("eth_getLogs",[{"fromBlock":hex(cur),"toBlock":hex(hi),"address":address,"topics":[[topic]]}],60) or [])
            cur=hi+1
        except Exception:
            if span<=50:raise
            span=max(50,span//2)
    return out

def b32(addr):return "0x"+"0"*24+addr.lower().replace("0x","")

def recv(log):
    topics=log.get("topics") or [];raw=bytes.fromhex((log.get("data") or "0x")[2:])
    if len(topics)<3 or len(raw)<128:return None
    sd=int.from_bytes(raw[:32],"big");sender="0x"+raw[32:64].hex()
    off=int.from_bytes(raw[64:96],"big")
    if off+32>len(raw):return None
    n=int.from_bytes(raw[off:off+32],"big");body=raw[off+32:off+32+n]
    if len(body)!=132:return None
    return {"source_domain":sd,"nonce":int(topics[2],16),"sender":sender.lower(),"body":body,
            "tx":str(log.get("transactionHash") or "").lower(),"block":int(log.get("blockNumber","0x0"),16)}

def burn(body):
    return {"version":int.from_bytes(body[:4],"big"),"burn_token":"0x"+body[4:36].hex(),
            "recipient":"0x"+body[36:68].hex(),"amount":int.from_bytes(body[68:100],"big")}

def mint(log):
    t=log.get("topics") or [];raw=bytes.fromhex((log.get("data") or "0x")[2:])
    if len(t)<3 or len(raw)<32:return None
    return {"recipient":"0x"+t[1][-40:].lower(),"token":"0x"+t[2][-40:].lower(),
            "amount":int.from_bytes(raw[:32],"big"),"log_index":int(log.get("logIndex","0x0"),16),
            "tx":str(log.get("transactionHash") or "").lower()}

months=[("2024-03",datetime(2024,3,1,tzinfo=timezone.utc),datetime(2024,4,1,tzinfo=timezone.utc)),
        ("2024-04",datetime(2024,4,1,tzinfo=timezone.utc),datetime(2024,5,1,tzinfo=timezone.utc))]
cases=[];evidence=[]
for label,a,z in months:
    s=find_block(int(a.timestamp()));e=find_block(int(z.timestamp()))-1
    rr=logs(MT,TOPIC_RECEIVED,s,e);mm=logs(TM,TOPIC_MINT,s,e)
    raw=json.dumps({"received":rr,"mints":mm},sort_keys=True,separators=(",",":")).encode()
    evidence.append({"month":label,"raw_sha256":hashlib.sha256(raw).hexdigest(),"received_logs":len(rr),"mint_logs":len(mm)})
    by={}
    for l in mm:
        m=mint(l)
        if m:by.setdefault(m["tx"],[]).append(m)
    for l in rr:
        x=recv(l)
        if not x or x["source_domain"]!=0 or x["sender"]!=b32(SOURCE_TM):continue
        b=burn(x["body"])
        if b["version"]!=0 or b["burn_token"][-40:].lower()!=SOURCE_USDC[-40:].lower():continue
        target_rec="0x"+b["recipient"][-40:].lower()
        cands=by.get(x["tx"],[])
        exact=[m for m in cands if m["token"]==DEST_USDC and m["amount"]==b["amount"] and m["recipient"]==target_rec]
        if len(exact)==1:continue
        if not cands:reason="NO_MINT_EVENT_IN_TX"
        elif len(exact)>1:reason="MULTIPLE_EXACT_MATCHES"
        else:
            token_ok=[m for m in cands if m["token"]==DEST_USDC]
            amount_ok=[m for m in cands if m["amount"]==b["amount"]]
            rec_ok=[m for m in cands if m["recipient"]==target_rec]
            oks=sum(bool(q) for q in (token_ok,amount_ok,rec_ok))
            if not token_ok and amount_ok and rec_ok:reason="DEST_TOKEN_MISMATCH"
            elif token_ok and not amount_ok and rec_ok:reason="AMOUNT_MISMATCH"
            elif token_ok and amount_ok and not rec_ok:reason="RECIPIENT_MISMATCH"
            else:reason="COMBINATION_MISMATCH"
        cases.append({"month":label,"nonce":x["nonce"],"destination_tx":x["tx"],"block":x["block"],
                      "source_amount_atomic":b["amount"],"target_recipient":target_rec,
                      "body_sha256":hashlib.sha256(x["body"]).hexdigest(),"reason":reason,
                      "mint_candidates":cands})

expected=4
counts={}
for x in cases:counts[x["reason"]]=counts.get(x["reason"],0)+1
if len(cases)!=expected:cls="SOURCE_SEMANTICS_UNRESOLVED"
elif all(x["reason"] in {"NO_MINT_EVENT_IN_TX","DEST_TOKEN_MISMATCH","AMOUNT_MISMATCH","RECIPIENT_MISMATCH","COMBINATION_MISMATCH","MULTIPLE_EXACT_MATCHES"} for x in cases):
    cls="PROTOCOL_NONCANONICAL_CONFIRMED"
else:cls="SOURCE_SEMANTICS_UNRESOLVED"
receipt={"lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001","child_id":"CCLM-CCTP-SETTLED-FLOW-002",
 "stage":"SEMANTIC_MISMATCH_DIAGNOSTIC_V0.1","captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "expected_case_count":expected,"observed_case_count":len(cases),"reason_counts":counts,"cases":cases,
 "evidence":evidence,"classification":cls,"canonical_rule_changed":False,
 "market_outcomes_opened":False,"pnl_opened":False,"mutation":False}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))

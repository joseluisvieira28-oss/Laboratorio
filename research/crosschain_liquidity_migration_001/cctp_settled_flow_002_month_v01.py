#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,urllib.request,urllib.error,time,os
from datetime import datetime,timezone
from pathlib import Path

MONTH=os.environ.get("CCLM_MONTH","2023-05")
year,month=map(int,MONTH.split("-"))
if not (2023<=year<=2024 and 1<=month<=12):
    raise SystemExit("INVALID_MONTH")
if (year,month)<(2023,5) or (year,month)>(2024,12):
    raise SystemExit("MONTH_OUTSIDE_FROZEN_PILOT")
start=datetime(year,month,1,tzinfo=timezone.utc)
if month==12:
    nxt=datetime(year+1,1,1,tzinfo=timezone.utc)
else:
    nxt=datetime(year,month+1,1,tzinfo=timezone.utc)
START_TS=int(start.timestamp())
END_TS=int(nxt.timestamp())-1
OUT=Path(f"artifacts/cclm_cctp_settled_flow_002_month_{MONTH}.json")

CHAINS={
  0:{
    "name":"Ethereum",
    "boundary_rpc":"https://eth-mainnet.public.blastapi.io",
    "transport":"sqd",
    "message_transmitter":"0x0a992d191deec32afe36203ad87d7d289a738f81",
    "token_messenger":"0xbd3fa81b58ba92a82136038b25adec7066af3155",
    "usdc":"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
  },
  1:{
    "name":"Avalanche",
    "boundary_rpc":"https://api.avax.network/ext/bc/C/rpc",
    "transport":"rpc",
    "message_transmitter":"0x8186359af5f57fbb40c6b14a588d2a59c0c29880",
    "token_messenger":"0x6b25532e1060ce10cc3b0a99e5683b91bfde6982",
    "usdc":"0xb97ef9ef8734c71904d8002f8b6bc66dd9c48a6e",
  }
}
TOPIC_RECEIVED="0x58200b4c34ae05ee816d710053fff3fb75af4395915d3d2a771b24aa10e3cc5d"
TOPIC_MINT="0x1b2a7ff080b8cb6ff436ce0372e399692bbfb6d4ae5766fd8d58a7b8cc6142e6"

def post(url,payload,timeout=60):
    raw=json.dumps(payload).encode()
    last=None
    for attempt in range(5):
        try:
            req=urllib.request.Request(url,data=raw,headers={
              "Content-Type":"application/json","Accept":"application/json","User-Agent":"CryptoLab-CCLM-SETTLED-002/0.1"
            },method="POST")
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.read()
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
            last=e
            if attempt==4: raise
            time.sleep(2.0*(attempt+1))
    raise last

def rpc(url,method,params,timeout=45):
    x=json.loads(post(url,{"jsonrpc":"2.0","id":1,"method":method,"params":params},timeout).decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

def block_ts(b):return int(b["timestamp"],16)
def block(url,n):return rpc(url,"eth_getBlockByNumber",[hex(n),False])
def find_block(url,target):
    lo=0;hi=int(rpc(url,"eth_blockNumber",[]),16)
    while lo<hi:
        mid=(lo+hi)//2;b=block(url,mid)
        if block_ts(b)<target:lo=mid+1
        else:hi=mid
    return lo

def parse_json_or_ndjson(raw):
    t=raw.decode("utf-8","replace").strip()
    if not t:return []
    try:return json.loads(t)
    except Exception:return [json.loads(x) for x in t.splitlines() if x.strip()]

def sqd_logs(address,topics,start,end):
    q={"type":"evm","fromBlock":start,"toBlock":end,
       "fields":{"block":{"number":True},"log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}},
       "logs":[{"address":[address],"topic0":topics}]}
    raw=post("https://portal.sqd.dev/datasets/ethereum-mainnet/stream",q,90)
    obj=parse_json_or_ndjson(raw);out=[]
    def walk(v,bn=None):
        if isinstance(v,dict):
            h=v.get("header")
            if isinstance(h,dict) and h.get("number") is not None:bn=h.get("number")
            if v.get("blockNumber") is not None:bn=v.get("blockNumber")
            if all(k in v for k in ("address","topics","data")):
                ts=v.get("topics") or []
                if str(v.get("address","")).lower()==address.lower() and ts and str(ts[0]).lower() in {x.lower() for x in topics}:
                    li=v.get("logIndex",0)
                    if isinstance(li,str):li=int(li,16) if li.startswith("0x") else int(li)
                    if isinstance(bn,str):bn=int(bn,16) if bn.startswith("0x") else int(bn)
                    out.append({"address":str(v["address"]).lower(),"topics":[str(x).lower() for x in ts],
                                "data":str(v["data"]).lower(),"transactionHash":v.get("transactionHash"),
                                "logIndex":hex(li or 0),"blockNumber":hex(bn) if isinstance(bn,int) else None})
            for z in v.values():walk(z,bn)
        elif isinstance(v,list):
            for z in v:walk(z,bn)
    walk(obj)
    uniq={(x["transactionHash"],x["logIndex"],x["topics"][0],x["data"]):x for x in out}
    return list(uniq.values()),{"transport":"SQD_PORTAL","raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw)}

def rpc_logs(url,address,topics,start,end):
    out=[];cur=start;span=2000
    while cur<=end:
        hi=min(end,cur+span-1)
        try:
            rows=rpc(url,"eth_getLogs",[{"fromBlock":hex(cur),"toBlock":hex(hi),"address":address,"topics":[topics]}],60) or []
            out.extend(rows);cur=hi+1
        except Exception:
            if span<=50:raise
            span=max(50,span//2)
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    return out,{"transport":"OFFICIAL_RPC","raw_sha256":hashlib.sha256(raw).hexdigest(),"raw_bytes":len(raw)}

def logs(domain,address,topics,start,end):
    c=CHAINS[domain]
    return sqd_logs(address,topics,start,end) if c["transport"]=="sqd" else rpc_logs(c["boundary_rpc"],address,topics,start,end)

def b32(addr):return "0x"+"0"*24+addr.lower().replace("0x","")

def decode_received(log):
    ts=log.get("topics") or [];raw=bytes.fromhex((log.get("data") or "0x")[2:])
    if len(ts)<3 or len(raw)<128:return None
    source=int.from_bytes(raw[0:32],"big");sender="0x"+raw[32:64].hex()
    off=int.from_bytes(raw[64:96],"big")
    if off+32>len(raw):return None
    n=int.from_bytes(raw[off:off+32],"big");body=raw[off+32:off+32+n]
    if len(body)!=132:return None
    return {"source_domain":source,"nonce":int(ts[2],16),"sender":sender.lower(),"body":body,
            "tx":str(log.get("transactionHash") or "").lower()}

def parse_burn_body(body):
    if len(body)!=132:return None
    return {"version":int.from_bytes(body[0:4],"big"),"burn_token":"0x"+body[4:36].hex(),
            "mint_recipient":"0x"+body[36:68].hex(),"amount":int.from_bytes(body[68:100],"big")}

def decode_mint(log):
    ts=log.get("topics") or [];raw=bytes.fromhex((log.get("data") or "0x")[2:])
    if len(ts)<3 or len(raw)<32:return None
    return {"recipient":"0x"+ts[1][-40:].lower(),"token":"0x"+ts[2][-40:].lower(),
            "amount":int.from_bytes(raw[:32],"big"),"tx":str(log.get("transactionHash") or "").lower()}

receipt={"lab_id":"CROSSCHAIN-LIQUIDITY-MIGRATION-001","child_id":"CCLM-CCTP-SETTLED-FLOW-002",
 "stage":"SETTLED_FLOW_MONTHLY_SOURCE_SCALE_V0.1","window_month":MONTH,
 "window_start_utc":start.isoformat(),"window_end_utc":datetime.fromtimestamp(END_TS,tz=timezone.utc).isoformat(),"routes":[],
 "market_outcomes_opened":False,"pnl_opened":False,"mutation":False,"access_2025":False,"access_2026":False}
try:
    total=0;mismatches=0
    for dd in (0,1):
        sd=1-dd;c=CHAINS[dd]
        s=find_block(c["boundary_rpc"],START_TS);e=find_block(c["boundary_rpc"],END_TS+1)-1
        rec,evr=logs(dd,c["message_transmitter"],[TOPIC_RECEIVED],s,e)
        mint,evm=logs(dd,c["token_messenger"],[TOPIC_MINT],s,e)
        mint_by_tx={}
        for l in mint:
            x=decode_mint(l)
            if x:mint_by_tx.setdefault(x["tx"],[]).append(x)
        canonical=[];route_mismatch=0
        for l in rec:
            x=decode_received(l)
            if not x or x["source_domain"]!=sd:continue
            if x["sender"]!=b32(CHAINS[sd]["token_messenger"]):continue
            b=parse_burn_body(x["body"])
            if not b or b["version"]!=0:continue
            if b["burn_token"][-40:].lower()!=CHAINS[sd]["usdc"][-40:].lower():continue
            cand=[m for m in mint_by_tx.get(x["tx"],[]) if m["token"]==CHAINS[dd]["usdc"] and m["amount"]==b["amount"] and m["recipient"]==("0x"+b["mint_recipient"][-40:].lower())]
            if len(cand)!=1:
                route_mismatch+=1;continue
            canonical.append({"source_domain":sd,"destination_domain":dd,"nonce":x["nonce"],"amount_atomic":b["amount"],
                              "destination_tx":x["tx"],"body_sha256":hashlib.sha256(x["body"]).hexdigest()})
        total+=len(canonical);mismatches+=route_mismatch
        receipt["routes"].append({"source_domain":sd,"destination_domain":dd,"received_logs_total":len(rec),
          "mint_logs_total":len(mint),"canonical_settled_flows":len(canonical),"semantic_mismatch_count":route_mismatch,
          "samples":canonical[:10],"evidence":[evr,evm]})
    receipt["canonical_settled_flows_total"]=total
    receipt["semantic_mismatch_count"]=mismatches
    receipt["classification"]="SOURCE_SETTLED_FLOW_SMOKE_PASS" if total>=1 and mismatches==0 else "SOURCE_SETTLED_FLOW_SMOKE_PARTIAL"
except Exception as e:
    receipt["classification"]="SOURCE_SETTLED_FLOW_MONTH_TECHNICAL_FAILURE";receipt["error"]=f"{type(e).__name__}:{str(e)[:800]}"
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))

#!/usr/bin/env python3
from __future__ import annotations
import hashlib,json,urllib.request,time
from datetime import datetime,timezone
from pathlib import Path
from Crypto.Hash import keccak

OUT=Path("artifacts/lcod_borrow_log_block_pin_universe_v01.json")
RPC="https://eth-mainnet.public.blastapi.io"
SQD="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"

SPOKES=[
"0x973a023A77420ba610f06b3858aD991Df6d85A08",
"0x58131E79531caB1d52301228d1f7b842F26B9649",
"0xba1B3D55D249692b669A164024A838309B7508AF",
"0xD8B93635b8C6d0fF98CbE90b5988E3F2d1Cd9da1",
"0x65407b940966954b23dfA3caA5C0702bB42984DC",
"0x7EC68b5695e803e98a21a9A05d744F28b0a7753D",
"0x94e7A5dCbE816e498b89aB752661904E2F56c485",
"0xAD75cE6354f87F3135cE10621d385d8D1e2562C2",
"0x956d8e0A89cfa3744428C4641b5a53B56167a7f9",
"0xbF10BDfE177dE0336aFD7fcCF80A904E15386219",
"0x3131FE68C4722e726fe6B2819ED68e514395B9a4",
"0xe1900480ac69f0B296841Cd01cC37546d92F35Cd",
"0x774b9655413c34809c1f1b16b654465A89EBE989",
]
SPOKES=[x.lower() for x in SPOKES]

def k256(s):
    k=keccak.new(digest_bits=256);k.update(s.encode());return "0x"+k.hexdigest()
BORROW_TOPIC=k256("Borrow(uint256,address,address,uint256,uint256)")
UAD_SELECTOR=k256("getUserAccountData(address)")[2:10]

def http_post(url,obj,timeout=90):
    raw=json.dumps(obj,separators=(",",":")).encode()
    req=urllib.request.Request(url,data=raw,headers={
      "Content-Type":"application/json","Accept":"application/json",
      "User-Agent":"CryptoLab-LCOD-BorrowUniverse/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()

def rpc(method,params):
    x=json.loads(http_post(RPC,{"jsonrpc":"2.0","id":1,"method":method,"params":params},45).decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

def parse_json_or_ndjson(raw):
    t=raw.decode("utf-8","replace").strip()
    if not t:return []
    try:return json.loads(t)
    except Exception:return [json.loads(x) for x in t.splitlines() if x.strip()]

def sqd_borrow_logs(to_block):
    q={"type":"evm","fromBlock":0,"toBlock":to_block,
       "fields":{"block":{"number":True},"log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}},
       "logs":[{"address":SPOKES,"topic0":[BORROW_TOPIC]}]}
    raw=http_post(SQD,q,180)
    obj=parse_json_or_ndjson(raw)
    out=[];malformed=0
    def walk(v,bn=None):
        nonlocal malformed
        if isinstance(v,dict):
            h=v.get("header")
            if isinstance(h,dict) and h.get("number") is not None:bn=h.get("number")
            if v.get("blockNumber") is not None:bn=v.get("blockNumber")
            if all(k in v for k in ("address","topics")):
                addr=str(v.get("address","")).lower()
                topics=[str(x).lower() for x in (v.get("topics") or [])]
                if addr in SPOKES and topics and topics[0]==BORROW_TOPIC.lower():
                    if len(topics)<4 or len(topics[3])!=66:
                        malformed+=1
                    else:
                        user="0x"+topics[3][-40:]
                        li=v.get("logIndex",0)
                        if isinstance(li,str):li=int(li,16) if li.startswith("0x") else int(li)
                        bnum=bn
                        if isinstance(bnum,str):bnum=int(bnum,16) if bnum.startswith("0x") else int(bnum)
                        out.append((addr,user.lower(),str(v.get("transactionHash") or "").lower(),int(li or 0),int(bnum or 0)))
            for z in v.values():walk(z,bn)
        elif isinstance(v,list):
            for z in v:walk(z,bn)
    walk(obj)
    uniq={(a,u,tx,li,bn) for a,u,tx,li,bn in out}
    return sorted(uniq),malformed,hashlib.sha256(raw).hexdigest(),len(raw)

def batch_uad(pairs,block_n,batch_size=80):
    results={};errors=[]
    block_hex=hex(block_n)
    for off in range(0,len(pairs),batch_size):
        part=pairs[off:off+batch_size]
        req=[]
        key={}
        for i,(spoke,user) in enumerate(part):
            rid=off+i+1
            data="0x"+UAD_SELECTOR+("0"*24)+user[2:]
            req.append({"jsonrpc":"2.0","id":rid,"method":"eth_call","params":[{"to":spoke,"data":data},block_hex]})
            key[rid]=(spoke,user)
        raw=http_post(RPC,req,90)
        arr=json.loads(raw.decode())
        for x in arr:
            pair=key.get(x.get("id"))
            if not pair:continue
            if x.get("error"):
                errors.append({"pair_sha256":hashlib.sha256(("::".join(pair)).encode()).hexdigest(),"error":str(x["error"])[:300]})
                continue
            val=x.get("result")
            try:
                b=bytes.fromhex(val[2:])
                if len(b)<32*7:raise ValueError("SHORT_UAD")
                words=[int.from_bytes(b[i:i+32],"big") for i in range(0,32*7,32)]
                results[pair]={"total_debt_value_ray":words[4],"health_factor":words[2],"borrow_count":words[6]}
            except Exception as e:
                errors.append({"pair_sha256":hashlib.sha256(("::".join(pair)).encode()).hexdigest(),"error":f"{type(e).__name__}:{e}"})
        time.sleep(0.05)
    return results,errors

final=rpc("eth_getBlockByNumber",["finalized",False])
N=int(final["number"],16);block_hash=final["hash"].lower()

logs,malformed,raw_sha,raw_bytes=sqd_borrow_logs(N)
candidate_pairs=sorted({(a,u) for a,u,tx,li,bn in logs})
per_spoke_events={s:0 for s in SPOKES};per_spoke_candidates={s:0 for s in SPOKES}
for a,u,tx,li,bn in logs:per_spoke_events[a]+=1
for a,u in candidate_pairs:per_spoke_candidates[a]+=1

uad,errors=batch_uad(candidate_pairs,N)
debt_pairs=sorted(p for p,v in uad.items() if int(v["total_debt_value_ray"])>0)
per_spoke_debt={s:0 for s in SPOKES}
for a,u in debt_pairs:per_spoke_debt[a]+=1

pair_hashes=[hashlib.sha256((a+"::"+u).encode()).hexdigest() for a,u in debt_pairs]
universe_sha=hashlib.sha256("\n".join(sorted(pair_hashes)).encode()).hexdigest()
queried_spokes=[s for s in SPOKES if s in per_spoke_events]

passed=(len(queried_spokes)==len(SPOKES) and malformed==0 and not errors and len(debt_pairs)>0)
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"BORROW_LOG_BLOCK_PIN_UNIVERSE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"BORROW_LOG_BLOCK_PIN_UNIVERSE_PASS" if passed else "BORROW_LOG_BLOCK_PIN_UNIVERSE_BLOCKED",
 "ethereum_block_number":N,"ethereum_block_hash":block_hash,"block_tag_policy":"finalized",
 "borrow_event_topic0":BORROW_TOPIC,
 "pinned_spoke_count":len(SPOKES),"queried_spoke_count":len(queried_spokes),
 "borrow_event_count":len(logs),"malformed_borrow_event_count":malformed,
 "candidate_pair_count":len(candidate_pairs),"current_debt_pair_count":len(debt_pairs),
 "per_spoke_event_count":per_spoke_events,"per_spoke_candidate_pair_count":per_spoke_candidates,
 "per_spoke_current_debt_pair_count":per_spoke_debt,
 "archive_raw_sha256":raw_sha,"archive_raw_bytes":raw_bytes,
 "canonical_universe_sha256":universe_sha,
 "pair_hash_sample":sorted(pair_hashes)[:20],
 "uad_error_count":len(errors),"uad_errors":errors[:50],
 "raw_wallet_retained":False,"all_uad_calls_block_pinned":True,
 "curve_computed":False,"market_returns_opened":False,"liquidation_outcomes_opened":False,
 "pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if not passed:raise SystemExit(2)

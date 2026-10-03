#!/usr/bin/env python3
import base64,hashlib,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
from web3 import Web3

MCP="https://mcp.aave.com/"
RPC="https://eth-mainnet.public.blastapi.io"
SQD="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
OUT=Path("artifacts/lcod_borrow_event_universe_v01.json")

SPOKES=[
"0x973a023a77420ba610f06b3858ad991df6d85a08",
"0x58131e79531cab1d52301228d1f7b842f26b9649",
"0xba1b3d55d249692b669a164024a838309b7508af",
"0xd8b93635b8c6d0ff98cbe90b5988e3f2d1cd9da1",
"0x65407b940966954b23dfa3caa5c0702bb42984dc",
"0x7ec68b5695e803e98a21a9a05d744f28b0a7753d",
"0x94e7a5dcbe816e498b89ab752661904e2f56c485",
"0xad75ce6354f87f3135ce10621d385d8d1e2562c2",
"0x956d8e0a89cfa3744428c4641b5a53b56167a7f9",
"0xbf10bdfe177de0336afd7fccf80a904e15386219",
"0x3131fe68c4722e726fe6b2819ed68e514395b9a4",
"0xe1900480ac69f0b296841cd01cc37546d92f35cd",
"0x774b9655413c34809c1f1b16b654465a89ebe989",
]
BORROW_TOPIC=Web3.keccak(text="Borrow(uint256,address,address,uint256,uint256)").hex().lower()

def post(url,payload,timeout=120):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers={
      "Content-Type":"application/json","Accept":"application/json","User-Agent":"CryptoLab-LCOD-BorrowUniverse/0.1"
    },method="POST")
    with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()

def mcp_rpc(method,params):
    raw=post(MCP,{"jsonrpc":"2.0","id":1,"method":method,"params":params},60)
    x=json.loads(raw.decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

def unwrap(x):
    if isinstance(x,dict) and x.get("structuredContent") is not None:
        y=x["structuredContent"];return y.get("data") if isinstance(y,dict) and "data" in y else y
    if isinstance(x,dict) and "content" in x:
        for c in x["content"]:
            if isinstance(c,dict) and c.get("type")=="text":
                try:
                    y=json.loads(c.get("text",""));return y.get("data") if isinstance(y,dict) and "data" in y else y
                except Exception:pass
    return x.get("data") if isinstance(x,dict) and "data" in x else x

def tool(name,args):return unwrap(mcp_rpc("tools/call",{"name":name,"arguments":args}))

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from walk(v)
    elif isinstance(x,list):
        for v in x:yield from walk(v)

def decode_reserve_id(s):
    try:
        raw=base64.b64decode(s+"="*((-len(s))%4)).decode()
        chain,spoke,rid=raw.split("::")
        if chain!="1" or not re.fullmatch(r"0x[a-fA-F0-9]{40}",spoke):return None
        return spoke.lower(),int(rid),s
    except Exception:return None

def holder_addresses(x):
    out=set()
    for d in walk(x):
        for k in ("user","address","wallet"):
            v=d.get(k)
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):
                out.add(v.lower())
    return out

def parse_json_or_ndjson(raw):
    t=raw.decode("utf-8","replace").strip()
    if not t:return []
    try:return json.loads(t)
    except Exception:return [json.loads(line) for line in t.splitlines() if line.strip()]

w3=Web3(Web3.HTTPProvider(RPC,request_kwargs={"timeout":45}))
final=w3.eth.get_block("finalized")
N=int(final["number"]);block_hash=final["hash"].hex()

# Event-derived universe.
query={"type":"evm","fromBlock":0,"toBlock":N,
 "fields":{"block":{"number":True},"log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}},
 "logs":[{"address":SPOKES,"topic0":[BORROW_TOPIC]}]}
raw=post(SQD,query,180)
obj=parse_json_or_ndjson(raw)
event_pairs=set();event_count=0;decode_errors=0;spoke_counts={s:0 for s in SPOKES}
def scan(v):
    global event_count,decode_errors
    if isinstance(v,dict):
        addr=str(v.get("address") or "").lower()
        topics=v.get("topics")
        if addr in spoke_counts and isinstance(topics,list) and topics and str(topics[0]).lower()==BORROW_TOPIC:
            event_count+=1;spoke_counts[addr]+=1
            if len(topics)<4:
                decode_errors+=1
            else:
                t=str(topics[3]).lower().replace("0x","")
                user="0x"+t[-40:]
                if not re.fullmatch(r"0x[a-f0-9]{40}",user):decode_errors+=1
                else:event_pairs.add(addr+"::"+user)
        for z in v.values():scan(z)
    elif isinstance(v,list):
        for z in v:scan(z)
scan(obj)

# Independent current MCP universe.
markets=tool("get_markets",{"version":"v4","chainId":1})
opaque=sorted({str(d.get("reserveId")) for d in walk(markets) if isinstance(d.get("reserveId"),str)})
decoded=sorted(x for x in (decode_reserve_id(s) for s in opaque) if x is not None and x[0] in set(SPOKES))
current_pairs=set();mcp_errors=[];pages=0
for spoke,rid,opaque_id in decoded:
    cursor=None;seen=set()
    for _ in range(200):
        args={"reserveId":opaque_id,"side":"borrow","limit":50,"version":"v4"}
        if cursor:args["cursor"]=cursor
        try:page=tool("get_reserve_holders",args)
        except Exception as e:
            mcp_errors.append(f"{spoke}:{rid}:{type(e).__name__}");break
        pages+=1
        for u in holder_addresses(page):current_pairs.add(spoke+"::"+u)
        curs=[]
        for d in walk(page):
            x=d.get("nextCursor") or d.get("next_cursor")
            if isinstance(x,str) and x.strip():curs.append(x.strip())
        curs=list(dict.fromkeys(curs))
        if not curs:break
        if len(curs)!=1 or curs[0] in seen:
            mcp_errors.append(f"{spoke}:{rid}:CURSOR_AMBIGUOUS_OR_LOOP");break
        seen.add(curs[0]);cursor=curs[0]

missing=sorted(current_pairs-event_pairs)
coverage=(len(current_pairs & event_pairs)/len(current_pairs)) if current_pairs else 0.0
passed=(event_count>0 and decode_errors==0 and not mcp_errors and coverage==1.0 and len(SPOKES)==13)
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"BORROW_EVENT_UNIVERSE_SOURCE_GATE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"BORROW_EVENT_UNIVERSE_SOURCE_PASS" if passed else "BORROW_EVENT_UNIVERSE_SOURCE_BLOCKED",
 "ethereum_block_number":N,"ethereum_block_hash":block_hash,
 "address_book_commit":"f08dbd218a1da7ea1ac3bb0e387652fdb9f98042",
 "aave_v4_commit":"40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f",
 "borrow_event_topic":BORROW_TOPIC,"queried_spoke_count":len(SPOKES),
 "spoke_event_counts":spoke_counts,"borrow_event_count":event_count,
 "event_unique_pair_count":len(event_pairs),"event_decode_error_count":decode_errors,
 "mcp_current_unique_pair_count":len(current_pairs),"mcp_pages":pages,"mcp_errors":mcp_errors,
 "current_pairs_covered_by_event_universe":len(current_pairs & event_pairs),
 "current_pair_coverage":coverage,"missing_current_pair_count":len(missing),
 "missing_current_pair_sha256":[hashlib.sha256(x.encode()).hexdigest() for x in missing[:100]],
 "sqd_raw_sha256":hashlib.sha256(raw).hexdigest(),"sqd_raw_bytes":len(raw),
 "raw_wallet_retained":False,"curve_computed":False,"market_returns_opened":False,
 "liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps(receipt,indent=2))
if not passed:raise SystemExit(2)

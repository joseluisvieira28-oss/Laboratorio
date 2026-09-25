#!/usr/bin/env python3
from __future__ import annotations
import base64,hashlib,json,re,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from web3 import Web3

OUT=Path("artifacts/lcod_borrow_event_block_census_v01.json")
RPC="https://eth-mainnet.public.blastapi.io"
MCP="https://mcp.aave.com/"
SQD="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"

SPOKES={
"BLUECHIP":"0x973a023A77420ba610f06b3858aD991Df6d85A08",
"ETHENA_CORRELATED":"0x58131E79531caB1d52301228d1f7b842F26B9649",
"ETHENA_ECOSYSTEM":"0xba1B3D55D249692b669A164024A838309B7508AF",
"FOREX":"0xD8B93635b8C6d0fF98CbE90b5988E3F2d1Cd9da1",
"GOLD":"0x65407b940966954b23dfA3caA5C0702bB42984DC",
"LOMBARD_BTC":"0x7EC68b5695e803e98a21a9A05d744F28b0a7753D",
"MAIN":"0x94e7A5dCbE816e498b89aB752661904E2F56c485",
"PAXG_GOLD":"0xAD75cE6354f87F3135cE10621d385d8D1e2562C2",
"USDG_PENDLE":"0x956d8e0A89cfa3744428C4641b5a53B56167a7f9",
"ETHERFI_ESPOKE":"0xbF10BDfE177dE0336aFD7fcCF80A904E15386219",
"KELP_ESPOKE":"0x3131FE68C4722e726fe6B2819ED68e514395B9a4",
"LIDO_ESPOKE":"0xe1900480ac69f0B296841Cd01cC37546d92F35Cd",
"USDG_MAPLE_ESPOKE":"0x774b9655413c34809c1f1b16b654465A89EBE989",
}
SPOKES={k:v.lower() for k,v in SPOKES.items()}
ADDR_SET=set(SPOKES.values())
TOPIC0=Web3.keccak(text="Borrow(uint256,address,address,uint256,uint256)").hex().lower()
SELECTOR=Web3.keccak(text="getUserAccountData(address)")[:4].hex()

def post(url,payload,timeout=120):
    raw=json.dumps(payload).encode()
    last=None
    for a in range(7):
        try:
            req=urllib.request.Request(url,data=raw,headers={"Content-Type":"application/json","Accept":"application/json","User-Agent":"CryptoLab-LCOD-BorrowCensus/0.1"},method="POST")
            with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError) as e:
            last=e
            if a==6:raise
            time.sleep(min(1.0*(2**a),12))
    raise last

def rpc(method,params):
    raw=post(RPC,{"jsonrpc":"2.0","id":1,"method":method,"params":params},60)
    x=json.loads(raw.decode())
    if x.get("error"):raise RuntimeError(x["error"])
    return x.get("result")

def parse_json_or_ndjson(raw):
    txt=raw.decode("utf-8","replace").strip()
    if not txt:return []
    try:return json.loads(txt)
    except Exception:return [json.loads(x) for x in txt.splitlines() if x.strip()]

def sqd_borrow_logs(to_block):
    q={"type":"evm","fromBlock":0,"toBlock":to_block,
       "fields":{"block":{"number":True},"log":{"address":True,"topics":True,"data":True,"transactionHash":True,"logIndex":True}},
       "logs":[{"address":sorted(ADDR_SET),"topic0":[TOPIC0]}]}
    raw=post(SQD,q,180)
    obj=parse_json_or_ndjson(raw);out=[]
    def walk(v,bn=None):
        if isinstance(v,dict):
            h=v.get("header")
            if isinstance(h,dict) and h.get("number") is not None:bn=h.get("number")
            if v.get("blockNumber") is not None:bn=v.get("blockNumber")
            if all(k in v for k in ("address","topics")):
                addr=str(v.get("address","")).lower();ts=[str(x).lower() for x in (v.get("topics") or [])]
                if addr in ADDR_SET and ts and ts[0]==TOPIC0 and len(ts)>=4:
                    b=bn
                    if isinstance(b,str):b=int(b,16) if b.startswith("0x") else int(b)
                    user="0x"+ts[3][-40:]
                    if re.fullmatch(r"0x[a-f0-9]{40}",user):
                        out.append((addr,user,int(b) if b is not None else None))
            for z in v.values():walk(z,bn)
        elif isinstance(v,list):
            for z in v:walk(z,bn)
    walk(obj)
    return out,hashlib.sha256(raw).hexdigest(),len(raw)

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

def walk(v):
    if isinstance(v,dict):
        yield v
        for z in v.values():yield from walk(z)
    elif isinstance(v,list):
        for z in v:yield from walk(z)

def decode_reserve_id(s):
    try:
        raw=base64.b64decode(s+"="*((-len(s))%4)).decode()
        chain,spoke,rid=raw.split("::")
        if chain!="1":return None
        return spoke.lower(),int(rid)
    except Exception:return None

def addresses(v):
    out=set()
    for d in walk(v):
        for k in ("user","address","wallet"):
            x=d.get(k)
            if isinstance(x,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",x):
                out.add(x.lower());break
    return out

def next_cursor(v):
    xs=[]
    for d in walk(v):
        x=d.get("nextCursor") or d.get("next_cursor")
        if isinstance(x,str) and x.strip():xs.append(x.strip())
    xs=list(dict.fromkeys(xs))
    if len(xs)>1:raise RuntimeError("AMBIGUOUS_CURSOR")
    return xs[0] if xs else None

def batch_active(pairs,block_n):
    items=list(pairs);active=[];errors=[]
    block_hex=hex(block_n)
    for base_i in range(0,len(items),75):
        chunk=items[base_i:base_i+75];payload=[]
        for j,(spoke,user) in enumerate(chunk):
            data="0x"+SELECTOR+("0"*24)+user[2:]
            payload.append({"jsonrpc":"2.0","id":j+1,"method":"eth_call","params":[{"to":spoke,"data":data},block_hex]})
        try:raw=post(RPC,payload,90);resp=json.loads(raw.decode())
        except Exception as e:
            errors.append(f"BATCH_TRANSPORT:{base_i}:{type(e).__name__}:{str(e)[:160]}");continue
        by={int(x.get("id")):x for x in resp if isinstance(x,dict) and x.get("id") is not None}
        for j,pair in enumerate(chunk):
            x=by.get(j+1)
            if not x or x.get("error"):
                errors.append(f"ETH_CALL:{hashlib.sha256((pair[0]+'::'+pair[1]).encode()).hexdigest()}:{x.get('error') if x else 'MISSING'}")
                continue
            h=x.get("result") or "0x";b=bytes.fromhex(h[2:])
            if len(b)<32*7:
                errors.append(f"SHORT_RETURN:{hashlib.sha256((pair[0]+'::'+pair[1]).encode()).hexdigest()}");continue
            total_debt=int.from_bytes(b[4*32:5*32],"big")
            if total_debt>0:active.append(pair)
        time.sleep(0.15)
    return set(active),errors

latest=int(rpc("eth_blockNumber",[]),16)
final=rpc("eth_getBlockByNumber",["finalized",False])
N=int(final["number"],16);N_hash=str(final["hash"]).lower()

logs,raw_sha,raw_bytes=sqd_borrow_logs(latest)
parse_errors=sum(1 for _,_,bn in logs if bn is None)
all_history={(a,u) for a,u,bn in logs if bn is not None}
history_at_n={(a,u) for a,u,bn in logs if bn is not None and bn<=N}
per_spoke={a:0 for a in ADDR_SET}
for a,u,bn in logs:
    if a in per_spoke:per_spoke[a]+=1

# Current MCP contradiction check.
mcp_pairs=set();mcp_errors=[]
markets=tool("get_markets",{"version":"v4","chainId":1})
reserve_ids=sorted({str(d.get("reserveId")) for d in walk(markets) if isinstance(d.get("reserveId"),str)})
for opaque in reserve_ids:
    dec=decode_reserve_id(opaque)
    if not dec:continue
    spoke,rid=dec
    if spoke not in ADDR_SET:continue
    cursor=None;seen=set()
    for _ in range(1000):
        args={"reserveId":opaque,"side":"borrow","limit":50,"version":"v4"}
        if cursor:args["cursor"]=cursor
        try:page=tool("get_reserve_holders",args)
        except Exception as e:
            mcp_errors.append(f"{spoke}:{rid}:{type(e).__name__}:{str(e)[:150]}");break
        for u in addresses(page):mcp_pairs.add((spoke,u))
        nxt=next_cursor(page)
        if not nxt:break
        if nxt in seen:mcp_errors.append(f"CURSOR_LOOP:{spoke}:{rid}");break
        seen.add(nxt);cursor=nxt
missing_current=sorted(mcp_pairs-all_history)
active_at_n,call_errors=batch_active(sorted(history_at_n),N)

pass_gate=(len(SPOKES)==13 and parse_errors==0 and len(logs)>0 and not mcp_errors and not missing_current and not call_errors and len(active_at_n)>0)

def ph(pair):return hashlib.sha256((pair[0]+"::"+pair[1]).encode()).hexdigest()
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"BORROW_EVENT_BLOCK_PINNED_POPULATION_GATE_V0.1",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"BORROW_EVENT_BLOCK_CENSUS_PASS" if pass_gate else "BORROW_EVENT_BLOCK_CENSUS_BLOCKED",
 "protocol_source_commit":"40232a0a91150d8ee5cab42bd3ddd0baf4ffff9f",
 "address_book_commit":"f08dbd218a1da7ea1ac3bb0e387652fdb9f98042",
 "official_spoke_count":len(SPOKES),"spokes":{k:v for k,v in sorted(SPOKES.items())},
 "borrow_topic0":TOPIC0,"latest_block_scanned":latest,
 "finalized_block_number":N,"finalized_block_hash":N_hash,
 "borrow_log_count":len(logs),"unique_borrow_pair_count_latest":len(all_history),
 "unique_borrow_pair_count_at_finalized":len(history_at_n),
 "borrow_log_count_by_spoke":{k:per_spoke[v] for k,v in SPOKES.items()},
 "sqd_raw_sha256":raw_sha,"sqd_raw_bytes":raw_bytes,"event_parse_errors":parse_errors,
 "current_mcp_borrow_pair_count":len(mcp_pairs),"mcp_errors":mcp_errors,
 "current_mcp_pairs_missing_from_borrow_history_count":len(missing_current),
 "current_mcp_pairs_missing_hashes":[ph(x) for x in missing_current[:100]],
 "active_debt_pairs_at_finalized":len(active_at_n),
 "active_pair_set_sha256":hashlib.sha256("\n".join(sorted(ph(x) for x in active_at_n)).encode()).hexdigest(),
 "block_call_errors":call_errors[:100],
 "production_invariant":"drawnShares increases only in borrow(); same path emits indexed Borrow user; repay/liquidation decrease debt",
 "raw_wallet_addresses_retained":False,
 "curve_computed":False,"market_returns_opened":False,"liquidation_outcomes_opened":False,
 "pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in ("spokes","borrow_log_count_by_spoke")},indent=2))
if not pass_gate:raise SystemExit(2)

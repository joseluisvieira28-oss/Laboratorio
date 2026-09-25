#!/usr/bin/env python3
import base64,hashlib,json,re,time,urllib.request,urllib.error
from datetime import datetime,timezone
from pathlib import Path
from web3 import Web3

MCP="https://mcp.aave.com/"
RPC="https://eth-mainnet.public.blastapi.io"
SQD="https://portal.sqd.dev/datasets/ethereum-mainnet/stream"
OUT=Path("artifacts/lcod_borrow_event_block_census_v03.json")

SPOKES={
"BLUECHIP":("0x973a023a77420ba610f06b3858ad991df6d85a08",24720920),
"ETHENA_CORRELATED":("0x58131e79531cab1d52301228d1f7b842f26b9649",24720926),
"ETHENA_ECOSYSTEM":("0xba1b3d55d249692b669a164024a838309b7508af",24720923),
"FOREX":("0xd8b93635b8c6d0ff98cbe90b5988e3f2d1cd9da1",24720917),
"GOLD":("0x65407b940966954b23dfa3caa5c0702bb42984dc",24720914),
"LOMBARD_BTC":("0x7ec68b5695e803e98a21a9a05d744f28b0a7753d",24720911),
"MAIN":("0x94e7a5dcbe816e498b89ab752661904e2f56c485",24720899),
"PAXG_GOLD":("0xad75ce6354f87f3135ce10621d385d8d1e2562c2",25883381),
"USDG_PENDLE":("0x956d8e0a89cfa3744428c4641b5a53b56167a7f9",25094394),
"ETHERFI_ESPOKE":("0xbf10bdfe177de0336afd7fccf80a904e15386219",24720905),
"KELP_ESPOKE":("0x3131fe68c4722e726fe6b2819ed68e514395b9a4",24720908),
"LIDO_ESPOKE":("0xe1900480ac69f0b296841cd01cc37546d92f35cd",24720902),
"USDG_MAPLE_ESPOKE":("0x774b9655413c34809c1f1b16b654465a89ebe989",25594472),
}
TOPIC="0x"+Web3.keccak(text="Borrow(uint256,address,address,uint256,uint256)").hex().replace("0x","").lower()

UAD_ABI=[{"type":"function","name":"getUserAccountData","stateMutability":"view",
 "inputs":[{"type":"address"}],"outputs":[{"type":"tuple","components":[
 {"name":"riskPremium","type":"uint256"},{"name":"avgCollateralFactor","type":"uint256"},
 {"name":"healthFactor","type":"uint256"},{"name":"totalCollateralValue","type":"uint256"},
 {"name":"totalDebtValueRay","type":"uint256"},{"name":"activeCollateralCount","type":"uint256"},
 {"name":"borrowCount","type":"uint256"}]}]}]

def post(url,payload,timeout=120,retries=5):
    raw=json.dumps(payload).encode()
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,data=raw,headers={
             "Content-Type":"application/json","Accept":"application/json",
             "User-Agent":"CryptoLab-LCOD-BorrowCensus/0.3"},method="POST")
            with urllib.request.urlopen(req,timeout=timeout) as r:return r.read()
        except Exception as e:
            last=e
            if i+1==retries:raise
            time.sleep(2*(i+1))
    raise last

def mcp_rpc(method,params):
    x=json.loads(post(MCP,{"jsonrpc":"2.0","id":1,"method":method,"params":params},60).decode())
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

def parse_stream(raw):
    t=raw.decode("utf-8","replace").strip()
    if not t:return []
    try:return json.loads(t)
    except Exception:return [json.loads(x) for x in t.splitlines() if x.strip()]

def decode_reserve_id(s):
    try:
        raw=base64.b64decode(s+"="*((-len(s))%4)).decode()
        chain,spoke,rid=raw.split("::")
        if chain!="1":return None
        return spoke.lower(),int(rid),s
    except Exception:return None

def holder_addresses(x):
    out=set()
    for d in walk(x):
        for k in ("user","address","wallet"):
            v=d.get(k)
            if isinstance(v,str) and re.fullmatch(r"0x[a-fA-F0-9]{40}",v):out.add(v.lower())
    return out

w3=Web3(Web3.HTTPProvider(RPC,request_kwargs={"timeout":60}))
final=w3.eth.get_block("finalized")
N=int(final["number"]);BH=final["hash"].hex()

event_pairs=set();log_counts={};transport={};decode_errors=[];query_errors=[]
addr_to_name={v[0]:k for k,v in SPOKES.items()}

for name,(addr,start) in SPOKES.items():
    q={"type":"evm","fromBlock":start,"toBlock":N,
       "fields":{"block":{"number":True},"log":{"address":True,"topics":True,"transactionHash":True,"logIndex":True}},
       "logs":[{"address":[addr],"topic0":[TOPIC]}]}
    try:
        raw=post(SQD,q,180)
        obj=parse_stream(raw)
        counter=[0]
        def scan(v):
            if isinstance(v,dict):
                a=str(v.get("address") or "").lower()
                ts=v.get("topics")
                if a==addr and isinstance(ts,list) and ts and str(ts[0]).lower()==TOPIC:
                    counter[0]+=1
                    if len(ts)<4:
                        decode_errors.append(f"{name}:TOPIC_COUNT")
                    else:
                        user="0x"+str(ts[3]).lower().replace("0x","")[-40:]
                        if re.fullmatch(r"0x[a-f0-9]{40}",user):event_pairs.add(addr+"::"+user)
                        else:decode_errors.append(f"{name}:BAD_USER")
                for z in v.values():scan(z)
            elif isinstance(v,list):
                for z in v:scan(z)
        scan(obj)
        count=counter[0]
        log_counts[name]=count
        transport[name]={"from_block":start,"to_block":N,"raw_bytes":len(raw),"raw_sha256":hashlib.sha256(raw).hexdigest()}
    except Exception as e:
        query_errors.append(f"{name}:{type(e).__name__}:{str(e)[:300]}")
        log_counts[name]=0

# Current MCP contradiction check.
markets=tool("get_markets",{"version":"v4","chainId":1})
valid_addrs=set(addr_to_name)
opaque=sorted({str(d.get("reserveId")) for d in walk(markets) if isinstance(d.get("reserveId"),str)})
decoded=[x for x in (decode_reserve_id(s) for s in opaque) if x and x[0] in valid_addrs]
current_pairs=set();mcp_errors=[]
for spoke,rid,opaque_id in decoded:
    cursor=None;seen=set()
    for _ in range(200):
        args={"reserveId":opaque_id,"side":"borrow","limit":50,"version":"v4"}
        if cursor:args["cursor"]=cursor
        try:page=tool("get_reserve_holders",args)
        except Exception as e:
            mcp_errors.append(f"{spoke}:{rid}:{type(e).__name__}");break
        for u in holder_addresses(page):current_pairs.add(spoke+"::"+u)
        curs=[]
        for d in walk(page):
            z=d.get("nextCursor") or d.get("next_cursor")
            if isinstance(z,str) and z.strip():curs.append(z.strip())
        curs=list(dict.fromkeys(curs))
        if not curs:break
        if len(curs)!=1 or curs[0] in seen:
            mcp_errors.append(f"{spoke}:{rid}:CURSOR");break
        seen.add(curs[0]);cursor=curs[0]

missing=current_pairs-event_pairs
coverage=len(current_pairs & event_pairs)/len(current_pairs) if current_pairs else 0.0

# Block-N active debt filter.
active=set();call_errors=[]
contracts={a:w3.eth.contract(address=Web3.to_checksum_address(a),abi=UAD_ABI) for a in valid_addrs}
for i,key in enumerate(sorted(event_pairs)):
    spoke,user=key.split("::")
    try:
        uad=contracts[spoke].functions.getUserAccountData(Web3.to_checksum_address(user)).call(block_identifier=N)
        if int(uad[4])>0:active.add(key)
    except Exception as e:
        call_errors.append(hashlib.sha256(key.encode()).hexdigest()+":"+type(e).__name__)
    if (i+1)%250==0:print(f"active-filter {i+1}/{len(event_pairs)}",flush=True)

passed=(len(query_errors)==0 and sum(log_counts.values())>0 and len(decode_errors)==0
        and not mcp_errors and coverage==1.0 and not call_errors and len(active)>0)
receipt={
 "lab_id":"LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001",
 "stage":"BORROW_EVENT_BLOCK_CENSUS_V0.3",
 "captured_at_utc":datetime.now(timezone.utc).isoformat(),
 "classification":"BORROW_EVENT_BLOCK_CENSUS_PASS_V03" if passed else "BORROW_EVENT_BLOCK_CENSUS_BLOCKED_V03",
 "finalized_block_number":N,"finalized_block_hash":BH,
 "official_spoke_count":13,"query_error_count":len(query_errors),"query_errors":query_errors,
 "borrow_log_count":sum(log_counts.values()),"borrow_log_count_by_spoke":log_counts,
 "unique_event_pair_count":len(event_pairs),"event_decode_error_count":len(decode_errors),
 "event_decode_errors":decode_errors[:50],"transport":transport,
 "current_mcp_pair_count":len(current_pairs),"mcp_error_count":len(mcp_errors),"mcp_errors":mcp_errors,
 "current_mcp_covered_count":len(current_pairs & event_pairs),"current_mcp_coverage":coverage,
 "missing_current_mcp_pair_count":len(missing),
 "missing_current_mcp_pair_sha256":[hashlib.sha256(x.encode()).hexdigest() for x in sorted(missing)[:100]],
 "active_debt_pairs_at_finalized":len(active),
 "active_pair_set_sha256":hashlib.sha256("\n".join(sorted(hashlib.sha256(x.encode()).hexdigest() for x in active)).encode()).hexdigest(),
 "block_call_error_count":len(call_errors),"block_call_errors":call_errors[:100],
 "raw_wallet_addresses_retained":False,"curve_computed":False,
 "market_returns_opened":False,"liquidation_outcomes_opened":False,"pnl_opened":False,"mutation":False
}
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({k:v for k,v in receipt.items() if k not in ("transport","missing_current_mcp_pair_sha256","block_call_errors")},indent=2))
if not passed:raise SystemExit(2)

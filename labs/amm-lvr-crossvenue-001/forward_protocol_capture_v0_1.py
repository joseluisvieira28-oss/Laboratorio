from __future__ import annotations

import asyncio
import json
import pathlib
import statistics
import time
import urllib.request
from collections import defaultdict, deque
from datetime import datetime, timezone

import websockets

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(parents=True,exist_ok=True)

RPC="https://eth.drpc.org"
TRACE_RPC="https://eth.drpc.org"
V3_FACTORY="0x1f98431c8ad98523631ae4a59f267346ea31f984"
V2_FACTORY="0x5c69bee701ef814a2b6a3edd4b1652cb9cc5aa6f"
SEL_GETPOOL=None  # resolved dynamically from canonical signature at startup
SEL_GETPAIR="e6a43905"
SEL_TOKEN0="0x0dfe1681"
SEL_TOKEN1="0xd21220a7"
V3_SWAP_TOPIC="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"

TOKENS={
"WETH":{"address":"0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2","decimals":18,"cex":"ETHUSDT"},
"USDC":{"address":"0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48","decimals":6,"cex":"USDCUSDT"},
"USDT":{"address":"0xdac17f958d2ee523a2206206994597c13d831ec7","decimals":6,"cex":None},
"WBTC":{"address":"0x2260fac5e5542a773aa44fbcfedf7c193bc2c599","decimals":8,"cex":"BTCUSDT"},
"LINK":{"address":"0x514910771af9ca656af840dff83e8264ecf986ca","decimals":18,"cex":"LINKUSDT"},
"PEPE":{"address":"0x6982508145454ce325ddbe47a25d4ec3d2311933","decimals":18,"cex":"PEPEUSDT"},
"SHIB":{"address":"0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce","decimals":18,"cex":"SHIBUSDT"},
}
ADDR_TO_SYMBOL={v["address"].lower():k for k,v in TOKENS.items()}
PAIRS=[("WETH","USDC"),("WETH","USDT"),("WBTC","WETH"),("LINK","WETH"),("PEPE","WETH"),("SHIB","WETH")]
V3_FEES=[100,500,3000,10000]
CEX_SYMBOLS=["ETHUSDT","BTCUSDT","LINKUSDT","PEPEUSDT","SHIBUSDT","USDCUSDT"]
LATENCY_MS=[0,250,1000,3000]
DURATION_SEC=240
MAX_EVENTS=60

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def rpc(url,method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(url,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-protocol/0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        body=json.loads(r.read().decode())
    if body.get("error"):
        raise RuntimeError(str(body["error"]))
    return body.get("result")

async def arpc(url,method,params):
    return await asyncio.to_thread(rpc,url,method,params)

async def get_logs_resilient(block_hex, addresses, v2_topic):
    """Transport-only fallback. Scientific filter is unchanged."""
    merged=[]
    seen=set()
    # Small chunks avoid public-provider address-array policy limits.
    chunks=[addresses[i:i+8] for i in range(0,len(addresses),8)]
    for chunk in chunks:
        filt={
            "fromBlock":block_hex,
            "toBlock":block_hex,
            "address":chunk,
            "topics":[V3_SWAP_TOPIC],
        }
        last_error=None
        for url in [RPC, TRACE_RPC]:
            try:
                rows=await arpc(url,"eth_getLogs",[filt])
                for lg in rows or []:
                    key=(lg.get("transactionHash"),lg.get("logIndex"))
                    if key not in seen:
                        seen.add(key)
                        merged.append(lg)
                last_error=None
                break
            except Exception as e:
                last_error=e
        if last_error is not None:
            # Final transport fallback: exact same filter, one pool at a time.
            for addr in chunk:
                one={
                    "fromBlock":block_hex,
                    "toBlock":block_hex,
                    "address":addr,
                    "topics":[V3_SWAP_TOPIC],
                }
                ok=False
                err=None
                for url in [TRACE_RPC,RPC]:
                    try:
                        rows=await arpc(url,"eth_getLogs",[one])
                        for lg in rows or []:
                            key=(lg.get("transactionHash"),lg.get("logIndex"))
                            if key not in seen:
                                seen.add(key)
                                merged.append(lg)
                        ok=True
                        break
                    except Exception as e:
                        err=e
                if not ok:
                    raise err if err is not None else RuntimeError("eth_getLogs transport failed")
    return merged

def word_addr(a): return a[2:].lower().rjust(64,"0")
def word_uint(x): return hex(int(x))[2:].rjust(64,"0")
def decode_addr(x):
    if not x or x=="0x": return None
    return "0x"+x[-40:].lower()

def signed256(x):
    n=int(x,16)
    return n-(1<<256) if n>=(1<<255) else n

async def build_pool_registry():
    # Resolve canonical selectors from signatures exactly as the source gate that passed.
    getpool_hash=await arpc(RPC,"web3_sha3",["0x"+"getPool(address,address,uint24)".encode().hex()])
    getpool_sel=getpool_hash[2:10]
    pools={}
    for a,b in PAIRS:
        aa=TOKENS[a]["address"]; bb=TOKENS[b]["address"]
        for fee in V3_FEES:
            data=getpool_sel+word_addr(aa)+word_addr(bb)+word_uint(fee)
            try:
                out=await arpc(RPC,"eth_call",[{"to":V3_FACTORY,"data":"0x"+data},"latest"])
                addr=decode_addr(out)
                if addr and int(addr,16)!=0:
                    pools[addr]={"dex":"UNISWAP_V3","pair":f"{a}-{b}","fee":fee}
            except Exception:
                pass
    # Resolve token order for every pool.
    for addr,meta in pools.items():
        try:
            t0=decode_addr(await arpc(RPC,"eth_call",[{"to":addr,"data":SEL_TOKEN0},"latest"]))
            t1=decode_addr(await arpc(RPC,"eth_call",[{"to":addr,"data":SEL_TOKEN1},"latest"]))
            meta["token0"]=ADDR_TO_SYMBOL.get((t0 or "").lower())
            meta["token1"]=ADDR_TO_SYMBOL.get((t1 or "").lower())
        except Exception:
            meta["token0"]=None; meta["token1"]=None
    return pools,None

def decode_swap(log,meta):
    data=(log.get("data") or "0x")[2:]
    if meta["dex"]=="UNISWAP_V3":
        if len(data)<64*5: return None
        a0=signed256(data[0:64]); a1=signed256(data[64:128])
        if a0>0 and a1<0:
            token_in,raw_in=meta["token0"],a0
            token_out,raw_out=meta["token1"],-a1
        elif a1>0 and a0<0:
            token_in,raw_in=meta["token1"],a1
            token_out,raw_out=meta["token0"],-a0
        else:
            return None
    else:
        if len(data)<64*4: return None
        a0in=int(data[0:64],16); a1in=int(data[64:128],16)
        a0out=int(data[128:192],16); a1out=int(data[192:256],16)
        if a0in>0 and a1out>0 and a1in==0 and a0out==0:
            token_in,raw_in=meta["token0"],a0in
            token_out,raw_out=meta["token1"],a1out
        elif a1in>0 and a0out>0 and a0in==0 and a1out==0:
            token_in,raw_in=meta["token1"],a1in
            token_out,raw_out=meta["token0"],a0out
        else:
            return None
    if token_in not in TOKENS or token_out not in TOKENS:
        return None
    return {
        "token_in":token_in,
        "token_out":token_out,
        "raw_in":str(raw_in),
        "raw_out":str(raw_out),
        "qty_in":str(raw_in/(10**TOKENS[token_in]["decimals"])),
        "qty_out":str(raw_out/(10**TOKENS[token_out]["decimals"])),
    }

def flatten_calls(node):
    if not isinstance(node,dict): return []
    out=[node]
    for c in node.get("calls",[]) or []: out.extend(flatten_calls(c))
    return out

async def builder_cost(tx_hash,block,receipt):
    try:
        trace=await arpc(TRACE_RPC,"debug_traceTransaction",[tx_hash,{"tracer":"callTracer","timeout":"15s"}])
    except Exception as e:
        return {"trace_pass":False,"trace_error":type(e).__name__+":"+str(e)[:300]}
    fee_recipient=(block.get("miner") or "").lower()
    base_fee=int(block.get("baseFeePerGas","0x0"),16)
    gas_used=int(receipt.get("gasUsed","0x0"),16)
    effective=int(receipt.get("effectiveGasPrice","0x0"),16)
    priority=max(effective-base_fee,0)
    priority_payment=gas_used*priority
    direct=0
    for c in flatten_calls(trace):
        if (c.get("to") or "").lower()==fee_recipient:
            try: direct+=int(c.get("value","0x0"),16)
            except Exception: pass
    return {
        "trace_pass":True,
        "fee_recipient":fee_recipient,
        "gas_used":gas_used,
        "base_fee_per_gas_wei":base_fee,
        "effective_gas_price_wei":effective,
        "priority_payment_wei":priority_payment,
        "direct_fee_recipient_transfer_wei":direct,
        "observable_builder_payment_wei":priority_payment+direct,
    }

async def main():
    pools,v2_topic=await build_pool_registry()
    if not pools:
        raise SystemExit("no frozen pools")
    ring={s:deque(maxlen=10000) for s in CEX_SYMBOLS}
    ws_errors=[]
    events=[]
    stop=asyncio.Event()

    streams="/".join(f"{s.lower()}@depth20@100ms" for s in CEX_SYMBOLS)
    ws_url=f"wss://data-stream.binance.vision/stream?streams={streams}"

    async def ws_task():
        try:
            async with websockets.connect(ws_url,ping_interval=120,ping_timeout=30,max_size=4_000_000) as ws:
                while not stop.is_set():
                    msg=await asyncio.wait_for(ws.recv(),timeout=5)
                    mono=time.monotonic_ns()
                    utc=now_iso()
                    body=json.loads(msg)
                    stream=body.get("stream","")
                    sym=stream.split("@",1)[0].upper()
                    data=body.get("data",{})
                    if sym in ring:
                        ring[sym].append({
                            "received_at_utc":utc,
                            "mono_ns":mono,
                            "lastUpdateId":data.get("lastUpdateId"),
                            "bids":data.get("bids",[]),
                            "asks":data.get("asks",[]),
                        })
        except Exception as e:
            ws_errors.append(type(e).__name__+":"+str(e)[:500])
            stop.set()

    async def first_snapshot_at(sym,target_ns,timeout=5.0):
        end=time.monotonic()+timeout
        while time.monotonic()<end:
            for x in ring[sym]:
                if x["mono_ns"]>=target_ns:
                    return x
            await asyncio.sleep(0.02)
        return None

    async def process_tx(txh,logs,block):
        detect_ns=time.monotonic_ns()
        detect_utc=now_iso()
        receipt=await arpc(RPC,"eth_getTransactionReceipt",[txh])
        swap_rows=[]
        for lg in logs:
            addr=(lg.get("address") or "").lower()
            meta=pools.get(addr)
            if not meta: continue
            dec=decode_swap(lg,meta)
            if dec:
                swap_rows.append({
                    "pool":addr,
                    "dex":meta["dex"],
                    "pair":meta["pair"],
                    "fee":meta["fee"],
                    "log_index":int(lg.get("logIndex","0x0"),16),
                    **dec,
                })
        if not swap_rows: return
        symbols=set()
        for sw in swap_rows:
            for tok in [sw["token_in"],sw["token_out"]]:
                c=TOKENS[tok]["cex"]
                if c: symbols.add(c)
        hedge_obs={}
        for delay in LATENCY_MS:
            target=detect_ns+delay*1_000_000
            per={}
            for sym in sorted(symbols):
                per[sym]=await first_snapshot_at(sym,target)
            hedge_obs[str(delay)]=per
        costs=await builder_cost(txh,block,receipt)
        events.append({
            "tx_hash":txh,
            "block_number":int(receipt.get("blockNumber","0x0"),16),
            "transaction_index":int(receipt.get("transactionIndex","0x0"),16),
            "block_timestamp":int(block.get("timestamp","0x0"),16),
            "detected_at_utc":detect_utc,
            "detected_mono_ns":detect_ns,
            "swaps":swap_rows,
            "hedge_depth_by_latency_ms":hedge_obs,
            "builder_cost":costs,
            "economic_outcome_computed":False,
        })

    async def eth_task():
        last=None
        deadline=time.monotonic()+DURATION_SEC
        addresses=list(pools.keys())
        while time.monotonic()<deadline and len(events)<MAX_EVENTS and not stop.is_set():
            try:
                head=int(await arpc(RPC,"eth_blockNumber",[]),16)
                if last is None: last=head-1
                for n in range(last+1,head+1):
                    block=await arpc(RPC,"eth_getBlockByNumber",[hex(n),False])
                    logs=await get_logs_resilient(hex(n),addresses,v2_topic)
                    bytx=defaultdict(list)
                    for lg in logs or []: bytx[lg.get("transactionHash")].append(lg)
                    for txh,lgs in bytx.items():
                        if txh and len(events)<MAX_EVENTS:
                            await process_tx(txh,lgs,block)
                    last=n
                await asyncio.sleep(0.25)
            except Exception as e:
                ws_errors.append("ETH:"+type(e).__name__+":"+str(e)[:500])
                await asyncio.sleep(1)
        stop.set()

    t1=asyncio.create_task(ws_task())
    t2=asyncio.create_task(eth_task())
    await asyncio.gather(t1,t2,return_exceptions=True)

    latency_coverage={}
    for d in LATENCY_MS:
        total=0; good=0
        for ev in events:
            for sym,snap in ev["hedge_depth_by_latency_ms"][str(d)].items():
                total+=1
                if snap is not None: good+=1
        latency_coverage[str(d)]={"required":total,"present":good,"ratio":(good/total if total else None)}

    receipt={
        "lab_id":"AMM-LVR-CROSSVENUE-001",
        "phase":"FORWARD_PROTOCOL_RAW_CAPTURE_V0.1",
        "duration_sec":DURATION_SEC,
        "max_events":MAX_EVENTS,
        "pool_count":len(pools),
        "v3_pool_count":sum(1 for x in pools.values() if x["dex"]=="UNISWAP_V3"),
        "v2_pool_count":sum(1 for x in pools.values() if x["dex"]=="UNISWAP_V2"),
        "captured_transaction_events":len(events),
        "captured_swap_logs":sum(len(x["swaps"]) for x in events),
        "trace_pass_events":sum(1 for x in events if x["builder_cost"].get("trace_pass")),
        "direct_builder_payment_positive_events":sum(1 for x in events if x["builder_cost"].get("direct_fee_recipient_transfer_wei",0)>0),
        "latency_depth_coverage":latency_coverage,
        "websocket_or_chain_errors":ws_errors,
        "economic_outcomes_opened":False,
        "pnl_computed":False,
        "scientific_verdict":"SOURCE_IMPLEMENTATION_ONLY",
        "note":"Protocol-compliant raw capture only. No economic event count or edge verdict is opened."
    }
    (OUT/"forward_protocol_capture_v0_1.json").write_text(json.dumps(events,indent=2,sort_keys=True),encoding="utf-8")
    (OUT/"forward_protocol_capture_v0_1_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    if len(events)==0:
        raise SystemExit(2)

if __name__=="__main__":
    asyncio.run(main())

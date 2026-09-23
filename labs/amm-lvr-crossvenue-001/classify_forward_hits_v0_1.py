from __future__ import annotations

import json
import pathlib
import urllib.request
import urllib.error
from collections import Counter

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(parents=True,exist_ok=True)

HITS=json.loads((ROOT/"forward_hit_registry_v0_2.json").read_text(encoding="utf-8"))["hits"]
RPC="https://eth.drpc.org"
FACTORY="0x1f98431c8ad98523631ae4a59f267346ea31f984"
SWAP_TOPIC="0xc42079f94a6350d7e6235f29174924f928cc2ac818eb64fed8004e115fbcca67"

FROZEN_POOLS={
"0xe0554a476a092703abdb3ef35c80e0d76d32939f":"WETH-USDC-100",
"0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640":"WETH-USDC-500",
"0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8":"WETH-USDC-3000",
"0x7bea39867e4169dbe237d55c8242a8f2fcdcc387":"WETH-USDC-10000",
"0xc7bbec68d12a0d1830360f8ec58fa599ba1b0e9b":"WETH-USDT-100",
"0x11b815efb8f581194ae79006d24e0d814b7697f6":"WETH-USDT-500",
"0x4e68ccd3e89f51c3074ca5072bbac773960dfa36":"WETH-USDT-3000",
"0xc5af84701f98fa483ece78af83f11b6c38aca71d":"WETH-USDT-10000",
"0xe6ff8b9a37b0fab776134636d9981aa778c4e718":"WBTC-WETH-100",
"0x4585fe77225b41b697c938b018e2ac67ac5a20c0":"WBTC-WETH-500",
"0xcbcdf9626bc03e24f779434178a73a0b4bad62ed":"WBTC-WETH-3000",
"0x6ab3bba2f41e7eaa262fa5a1a9b3932fa161526f":"WBTC-WETH-10000",
"0x4ea16ae82145731390d77485db5cfb616a9582a6":"LINK-WETH-100",
"0x5d4f3c6fa16908609bac31ff148bd002aa6b8c83":"LINK-WETH-500",
"0xa6cc3c2531fdaa6ae1a3ca84c2855806728693e8":"LINK-WETH-3000",
"0x3a0f221ea8b150f3d3d27de8928851ab5264bb65":"LINK-WETH-10000",
"0xa786568aa87ffb8aafd1e532b66909eeb8d79399":"PEPE-WETH-100",
"0x6e5c0b204d8c5311687513f0e71c10cb9e114b6b":"PEPE-WETH-500",
"0x11950d141ecb863f01007add7d1a342041227b58":"PEPE-WETH-3000",
"0xf239009a101b6b930a527deaab6961b6e7dec8a6":"PEPE-WETH-10000",
"0x94e4b2e24523cf9b3e631a6943c346df9687c723":"SHIB-WETH-500",
"0x2f62f2b4c5fcd7570a709dec05d68ea19c82a9ec":"SHIB-WETH-3000",
"0x5764a6f2212d502bc5970f9f129ffcd61e5d7563":"SHIB-WETH-10000",
}

def rpc(method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-classifier/0.1"})
    try:
        with urllib.request.urlopen(req,timeout=35) as resp:
            body=json.loads(resp.read().decode())
        if body.get("error"):
            return None,body["error"]
        return body.get("result"),None
    except Exception as e:
        return None,{"local":type(e).__name__+":"+str(e)[:500]}

def sha3_selector(sig):
    out,err=rpc("web3_sha3",["0x"+sig.encode().hex()])
    if not out: raise RuntimeError(err)
    return out[:10]

SEL_TOKEN0=sha3_selector("token0()")
SEL_TOKEN1=sha3_selector("token1()")
SEL_FEE=sha3_selector("fee()")
SEL_GETPOOL=sha3_selector("getPool(address,address,uint24)")

def eth_call(to,data,block="latest"):
    return rpc("eth_call",[{"to":to,"data":data},block])

def decode_address_word(x):
    if not x or x=="0x" or len(x)<42: return None
    return "0x"+x[-40:].lower()

def decode_uint_word(x):
    if not x or x=="0x": return None
    try: return int(x,16)
    except Exception: return None

def word_address(a): return a[2:].lower().rjust(64,"0")
def word_uint(x): return hex(int(x))[2:].rjust(64,"0")

pool_cache={}
def validate_v3_pool(addr, block_hex):
    addr=addr.lower()
    key=(addr,block_hex)
    if key in pool_cache: return pool_cache[key]
    t0,_=eth_call(addr,SEL_TOKEN0,block_hex)
    t1,_=eth_call(addr,SEL_TOKEN1,block_hex)
    fee,_=eth_call(addr,SEL_FEE,block_hex)
    token0=decode_address_word(t0)
    token1=decode_address_word(t1)
    fee_int=decode_uint_word(fee)
    valid=False
    factory_pool=None
    if token0 and token1 and fee_int is not None:
        data=SEL_GETPOOL+word_address(token0)+word_address(token1)+word_uint(fee_int)
        gp,_=eth_call(FACTORY,data,block_hex)
        factory_pool=decode_address_word(gp)
        valid=(factory_pool==addr)
    obj={"address":addr,"token0":token0,"token1":token1,"fee":fee_int,"factory_pool":factory_pool,"validated_uniswap_v3_pool":valid}
    pool_cache[key]=obj
    return obj

def flatten_calls(node):
    if not isinstance(node,dict): return []
    out=[node]
    for c in node.get("calls",[]) or []:
        out.extend(flatten_calls(c))
    return out

classified=[]
errors=[]
for h in HITS:
    txh=h["tx_hash"]
    receipt,er=rpc("eth_getTransactionReceipt",[txh])
    if not isinstance(receipt,dict):
        errors.append({"tx_hash":txh,"stage":"receipt","error":er}); continue
    block_hex=receipt.get("blockNumber")
    block,er=rpc("eth_getBlockByNumber",[block_hex,False])
    if not isinstance(block,dict):
        errors.append({"tx_hash":txh,"stage":"block","error":er}); continue
    trace,trace_err=rpc("debug_traceTransaction",[txh,{"tracer":"callTracer","timeout":"15s"}])
    calls=flatten_calls(trace) if isinstance(trace,dict) else []
    fee_recipient=(block.get("miner") or "").lower()
    base_fee=int(block.get("baseFeePerGas","0x0"),16)
    gas_used=int(receipt.get("gasUsed","0x0"),16)
    effective=int(receipt.get("effectiveGasPrice","0x0"),16)
    priority_per_gas=max(effective-base_fee,0)
    priority_payment=gas_used*priority_per_gas
    direct_to_fee_recipient=0
    fee_recipient_call_count=0
    for c in calls:
        to=(c.get("to") or "").lower()
        if fee_recipient and to==fee_recipient:
            try: val=int(c.get("value","0x0"),16)
            except Exception: val=0
            if val>0:
                direct_to_fee_recipient+=val
                fee_recipient_call_count+=1

    swap_logs=[]
    validated=[]
    frozen=[]
    for lg in receipt.get("logs",[]) or []:
        topics=lg.get("topics") or []
        if topics and topics[0].lower()==SWAP_TOPIC:
            addr=(lg.get("address") or "").lower()
            swap_logs.append(addr)
            v=validate_v3_pool(addr,block_hex)
            if v["validated_uniswap_v3_pool"]:
                validated.append(v)
                if addr in FROZEN_POOLS:
                    frozen.append(FROZEN_POOLS[addr])

    classification=(
        "FROZEN_MVE_DEX_ACTIVITY_OBSERVED" if frozen else
        "UNISWAP_V3_ACTIVITY_OUTSIDE_FROZEN_MVE" if validated else
        "REGISTRY_TOUCH_NO_VALIDATED_UNISWAP_V3_SWAP"
    )
    classified.append({
        "label":h["label"],
        "tx_hash":txh,
        "block_number":int(block_hex,16),
        "registry_match_side":"to",
        "fee_recipient":fee_recipient,
        "gas_used":gas_used,
        "effective_gas_price_wei":effective,
        "base_fee_per_gas_wei":base_fee,
        "priority_fee_per_gas_wei":priority_per_gas,
        "priority_payment_wei":priority_payment,
        "direct_fee_recipient_transfer_wei":direct_to_fee_recipient,
        "direct_fee_recipient_transfer_calls":fee_recipient_call_count,
        "observable_builder_payment_wei":priority_payment+direct_to_fee_recipient,
        "receipt_log_count":len(receipt.get("logs",[]) or []),
        "swap_topic_log_count":len(swap_logs),
        "validated_uniswap_v3_pool_count":len(validated),
        "validated_v3_pools":validated,
        "frozen_pool_swaps":frozen,
        "trace_pass":isinstance(trace,dict),
        "trace_error":trace_err,
        "classification":classification,
        "cex_hedge_observed":False,
        "cex_dex_arbitrage_claim":False,
    })

counts=Counter(x["classification"] for x in classified)
labels=Counter(x["label"] for x in classified if x["classification"]=="FROZEN_MVE_DEX_ACTIVITY_OBSERVED")
builder_nonzero=sum(1 for x in classified if x["direct_fee_recipient_transfer_wei"]>0)
trace_pass=sum(1 for x in classified if x["trace_pass"])

receipt_out={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"FORWARD_HIT_CLASSIFICATION_V0.1",
    "frozen_hit_count":len(HITS),
    "classified_count":len(classified),
    "error_count":len(errors),
    "classification_counts":dict(counts),
    "frozen_mve_dex_activity_labels":dict(labels),
    "trace_pass_count":trace_pass,
    "direct_fee_recipient_transfer_positive_count":builder_nonzero,
    "economic_outcomes_opened":False,
    "pnl_computed":False,
    "cex_dex_arbitrage_confirmed_count":0,
    "verdict":"FORWARD_HIT_CLASSIFICATION_PASS" if len(classified)==len(HITS) and trace_pass==len(HITS) else "FORWARD_HIT_CLASSIFICATION_INCOMPLETE",
    "note":"DEX activity is classified from receipt logs validated against the canonical Uniswap V3 factory. CEX-DEx arbitrage is deliberately NOT claimed because the CEX hedge leg is not observed.",
    "errors":errors,
    "transactions":classified,
}
(OUT/"forward_hit_classification_v0_1_receipt.json").write_text(json.dumps(receipt_out,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt_out,indent=2,sort_keys=True))

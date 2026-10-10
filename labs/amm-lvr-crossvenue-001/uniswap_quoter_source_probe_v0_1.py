from __future__ import annotations

import json
import pathlib
import urllib.request
import urllib.error

OUT=pathlib.Path(__file__).resolve().parent/"evidence"
OUT.mkdir(parents=True,exist_ok=True)
RPC="https://ethereum-rpc.publicnode.com"
FACTORY="0x1f98431c8ad98523631ae4a59f267346ea31f984"
QUOTER="0x61ffe014ba17989e743c5f6cb21bf9697530b21e"

TOKENS={
    "WETH":("0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2",18,10**17),
    "USDC":("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",6,100*10**6),
    "USDT":("0xdac17f958d2ee523a2206206994597c13d831ec7",6,100*10**6),
    "WBTC":("0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",8,10**5),
    "LINK":("0x514910771af9ca656af840dff83e8264ecf986ca",18,10*10**18),
    "PEPE":("0x6982508145454ce325ddbe47a25d4ec3d2311933",18,1_000_000*10**18),
    "SHIB":("0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",18,10_000_000*10**18),
}
PAIRS=[("WETH","USDC"),("WETH","USDT"),("WBTC","WETH"),("LINK","WETH"),("PEPE","WETH"),("SHIB","WETH")]
FEES=[100,500,3000,10000]
CEX_SYMBOLS=["ETHUSDT","BTCUSDT","LINKUSDT","PEPEUSDT","SHIBUSDT","USDCUSDT"]

def rpc(method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(RPC,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-AMM-LVR-001-quoter/0.1"})
    try:
        with urllib.request.urlopen(req,timeout=25) as r:
            body=json.loads(r.read().decode())
        return body.get("result"),body.get("error")
    except Exception as e:
        return None,{"local":type(e).__name__+":"+str(e)[:300]}

def selector(signature):
    h,err=rpc("web3_sha3",["0x"+signature.encode().hex()])
    if not h:
        raise RuntimeError(err)
    return h[2:10]

def word_address(a): return a[2:].lower().rjust(64,"0")
def word_uint(x): return hex(int(x))[2:].rjust(64,"0")

GETPOOL_SEL=selector("getPool(address,address,uint24)")
QUOTE_SEL=selector("quoteExactInputSingle((address,address,uint256,uint24,uint160))")

def eth_call(to,data):
    return rpc("eth_call",[{"to":to,"data":"0x"+data},"latest"])

def get_pool(a,b,fee):
    data=GETPOOL_SEL+word_address(a)+word_address(b)+word_uint(fee)
    out,err=eth_call(FACTORY,data)
    if not out or out=="0x":
        return None,err
    addr="0x"+out[-40:]
    if int(addr,16)==0:
        return None,None
    return addr.lower(),None

def quote_ok(a,b,amount,fee):
    data=QUOTE_SEL+word_address(a)+word_address(b)+word_uint(amount)+word_uint(fee)+word_uint(0)
    out,err=eth_call(QUOTER,data)
    if not out or out=="0x":
        return False,err
    # Do NOT persist amountOut in this source-only probe.
    return len(out)>=2+64*4,err

routes=[]
for left,right in PAIRS:
    a=TOKENS[left][0]; b=TOKENS[right][0]
    for fee in FEES:
        pool,perr=get_pool(a,b,fee)
        q1=q2=False
        e1=e2=None
        if pool:
            q1,e1=quote_ok(a,b,TOKENS[left][2],fee)
            q2,e2=quote_ok(b,a,TOKENS[right][2],fee)
        routes.append({
            "pair":f"{left}-{right}","fee":fee,
            "pool_exists":bool(pool),"pool_address":pool,
            "quote_left_to_right_pass":q1,
            "quote_right_to_left_pass":q2,
            "pool_error":perr,"quote_errors":[e1,e2]
        })

cex={}
for sym in CEX_SYMBOLS:
    url=f"https://data-api.binance.vision/api/v3/ticker/bookTicker?symbol={sym}"
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-AMM-LVR-001-quoter/0.1"})
        with urllib.request.urlopen(req,timeout=20) as r:
            body=json.loads(r.read().decode())
        cex[sym]={"status":r.status,"bbo_fields_present":all(k in body for k in ["bidPrice","bidQty","askPrice","askQty"])}
    except urllib.error.HTTPError as e:
        cex[sym]={"status":e.code,"bbo_fields_present":False}
    except Exception as e:
        cex[sym]={"status":None,"bbo_fields_present":False,"error":type(e).__name__+":"+str(e)[:200]}

fee_hist,fee_err=rpc("eth_feeHistory",[hex(20),"latest",[50,90]])
fee_history_pass=isinstance(fee_hist,dict) and "baseFeePerGas" in fee_hist and "reward" in fee_hist

pair_summary={}
for p in PAIRS:
    key=f"{p[0]}-{p[1]}"
    rows=[x for x in routes if x["pair"]==key]
    pair_summary[key]={
        "pools_found":sum(x["pool_exists"] for x in rows),
        "bidirectional_quote_tiers":sum(x["quote_left_to_right_pass"] and x["quote_right_to_left_pass"] for x in rows),
        "any_bidirectional_quote":any(x["quote_left_to_right_pass"] and x["quote_right_to_left_pass"] for x in rows)
    }

verdict=(
    "EXECUTABLE_QUOTE_SOURCE_PASS"
    if all(v["any_bidirectional_quote"] for v in pair_summary.values())
       and all(v.get("status")==200 and v.get("bbo_fields_present") for v in cex.values())
       and fee_history_pass
    else "EXECUTABLE_QUOTE_SOURCE_INCOMPLETE"
)

receipt={
    "lab_id":"AMM-LVR-CROSSVENUE-001",
    "phase":"UNISWAP_QUOTER_SOURCE_PROBE_V0.1",
    "verdict":verdict,
    "pair_summary":pair_summary,
    "cex_route_summary":cex,
    "fee_history_pass":fee_history_pass,
    "fee_history_error":fee_err,
    "routes":routes,
    "economic_outcomes_opened":False,
    "quote_amounts_persisted":False,
    "pnl_computed":False,
    "note":"Source-only: proves pools and executable Quoter paths without persisting quote amounts."
}
(OUT/"uniswap_quoter_source_probe_v0_1_receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
print(json.dumps(receipt,indent=2,sort_keys=True))
# Incomplete is a scientific source classification, not a CI failure; preserve all evidence.

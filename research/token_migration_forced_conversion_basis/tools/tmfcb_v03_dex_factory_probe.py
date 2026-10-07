#!/usr/bin/env python3
"""TMFCB V0.3 DEX factory metadata probe.

NO PRICE DATA. Uses only eth_getCode, eth_getBlockByNumber and eth_getLogs
against Uniswap V2 PairCreated factory events. Does NOT read reserves,
Swap events, balances, prices, TVL, amounts, or implied prices.
"""
import json, urllib.request, time

RPCS=["https://ethereum-rpc.publicnode.com","https://cloudflare-eth.com"]
UPPER=24000000
FACTORY="0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f"
PAIR_CREATED="0x0d3648bd0f6ba80134a33ba9275ac585d9d315f0ad8355cddefde31afa28d0e9"
QUOTES={
"WETH":"0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
"USDC":"0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
"USDT":"0xdAC17F958D2ee523a2206206994597C13D831ec7",
"DAI":"0x6B175474E89094C44Da98b954EedeAC495271d0F",
}
TOKENS={
"OGV":"0x9c354503C38481a7A7a51629142963F98eCC12D0",
"OGN":"0x8207c1FfC5B6804F6024322CcF34F29c3541Ae26",
"MPL":"0x33349B282065b0284d756F0577FB39c158F935e6",
"SYRUP":"0x643C4E15d7d62Ad0aBeC4a9BD4b001aA3Ef52d66",
"LBR_V1":"0xf1182229b71e79e504b1d2bf076c15a277311e05",
"LBR_V2":"0xed1167b6Dc64E8a366DB86F2E952A482D0981ebd",
"MATIC":"0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
"POL":"0x455e53CBB86018Ac2B8092FdCD39d8444aFFc3F6",
"GAL":"0x5fAa989Af96Af85384b8a938c2EdE4A7378D9875",
"G":"0x9C7BEBa8F6eF6643aBd725e45a4E8387eF260649",
"MFT":"0xdf2c7238198ad8b389666574f2d8bc411a4b7428",
"HIFI":"0x4b9278b94a1112cAD404048903b8d343a810B07e",
"TBTC_V1":"0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa",
"TBTC_V2":"0x18084fbA666a33d37592fA2633fD49a74DD93a88",
"NU":"0x4fE83213D56308330EC302a8BD641f1d0113A4Cc",
"KEEP":"0x85eee30c52b0b379b046fb0f85f4f3dc3009afec",
"T":"0xCdF7028ceAB81fA0C6971208e83fa7872994beE5",
}

def rpc(method,params):
    payload=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    last=None
    for ep in RPCS:
        try:
            req=urllib.request.Request(ep,data=payload,headers={"Content-Type":"application/json","User-Agent":"CryptoLab-TMFCB-V03-DEX/1.0"})
            with urllib.request.urlopen(req,timeout=30) as r: out=json.load(r)
            if "error" in out:
                last=RuntimeError(str(out["error"])); continue
            return out.get("result")
        except Exception as e: last=e
    raise RuntimeError(f"{method}: {last}")

def pad(a): return "0x"+"0"*24+a.lower().replace("0x","")

def code_at(a,b):
    return rpc("eth_getCode",[a,hex(b)]) not in (None,"0x","0x0")

def first_code(a):
    if not code_at(a,UPPER): return None
    lo,hi=0,UPPER
    while lo<hi:
        m=(lo+hi)//2
        if code_at(a,m): hi=m
        else: lo=m+1
    return lo

def block_meta(n):
    b=rpc("eth_getBlockByNumber",[hex(n),False])
    return {"block":n,"timestamp_unix":int(b["timestamp"],16),"hash":b["hash"]} if b else None

def query_pair(token,quote,start):
    # Probe in 1,000,000-block chunks. PairCreated only; no swap/state reads.
    chunk=1_000_000
    tt,qq=pad(token),pad(quote)
    for a in range(start,UPPER+1,chunk):
        z=min(a+chunk-1,UPPER)
        for topics in ([PAIR_CREATED,tt,qq],[PAIR_CREATED,qq,tt]):
            try:
                logs=rpc("eth_getLogs",[{"address":FACTORY,"fromBlock":hex(a),"toBlock":hex(z),"topics":topics}])
            except Exception:
                # Fail closed for this range/source.
                return {"status":"RPC_RANGE_BLOCKED","range":[a,z]}
            if logs:
                lg=logs[0]
                data=lg.get("data","0x")[2:]
                pair=("0x"+data[24:64]) if len(data)>=64 else None
                bn=int(lg["blockNumber"],16)
                return {"status":"FOUND","pair":pair,"creation":block_meta(bn),"factory":FACTORY}
        time.sleep(0.02)
    return {"status":"NOT_FOUND"}

out={"probe":"TMFCB_V0.3_UNISWAP_V2_FACTORY_METADATA","upper_block":UPPER,"tokens":{}}
for label,token in TOKENS.items():
    try:
        fb=first_code(token)
        rec={"address":token,"first_code_block":fb,"first_code_meta":block_meta(fb) if fb is not None else None,"common_quote_pairs":{}}
        if fb is not None:
            for ql,qa in QUOTES.items():
                p=query_pair(token,qa,fb)
                rec["common_quote_pairs"][ql]=p
                if p.get("status")=="FOUND":
                    break
        out["tokens"][label]=rec
    except Exception as e:
        out["tokens"][label]={"address":token,"error":str(e)}
print(json.dumps(out,indent=2,sort_keys=True))

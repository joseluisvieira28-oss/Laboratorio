#!/usr/bin/env python3
"""TMFCB V0.3 Ethereum metadata-only provenance probe.

STRICTLY NO PRICE DATA.
Allowed RPC methods used:
- eth_getCode
- eth_getTransactionReceipt (only for tx hashes pre-identified in first-party deployment manifests)
- eth_getBlockByNumber (timestamp / transaction-hash metadata only)

No eth_call, no balances, no logs containing swaps, no market endpoints.
"""
import json, sys, urllib.request, time

RPCS = [
    "https://eth.llamarpc.com",
    "https://1rpc.io/eth",
    "https://rpc.flashbots.net",
    "https://ethereum-rpc.publicnode.com",
    "https://cloudflare-eth.com",
]

CONTRACTS = {
    "OGV_OLD": "0x9c354503C38481a7A7a51629142963F98eCC12D0",
    "OGN_NEW": "0x8207c1FfC5B6804F6024322CcF34F29c3541Ae26",
    "OGV_OGN_MIGRATOR": "0x95c347D6214614A780847b8aAF4f96Eb84f4da6d",

    "MPL_OLD": "0x33349B282065b0284d756F0577FB39c158F935e6",
    "SYRUP_NEW": "0x643C4E15d7d62Ad0aBeC4a9BD4b001aA3Ef52d66",
    "MPL_SYRUP_MIGRATOR": "0x9c9499edD0cd2dCBc3C9Dd5070bAf54777AD8F2C",

    "LBR_V1": "0xf1182229b71e79e504b1d2bf076c15a277311e05",
    "LBR_V2": "0xed1167b6Dc64E8a366DB86F2E952A482D0981ebd",

    "MATIC_OLD": "0x7d1afa7b718fb893db30a3abc0cfc608aacfebb0",
    "POL_NEW": "0x455e53CBB86018Ac2B8092FdCD39d8444aFFc3F6",

    "GAL_OLD": "0x5fAa989Af96Af85384b8a938c2EdE4A7378D9875",
    "G_NEW": "0x9C7BEBa8F6eF6643aBd725e45a4E8387eF260649",

    "MFT_OLD": "0xdf2c7238198ad8b389666574f2d8bc411a4b7428",
    "HIFI_NEW": "0x4b9278b94a1112cAD404048903b8d343a810B07e",

    "TBTC_V1": "0x8dAEBADE922dF735c38C80C7eBD708Af50815fAa",
    "TBTC_V2": "0x18084fbA666a33d37592fA2633fD49a74DD93a88",
    "TBTC_VENDING_MACHINE_V2": "0xcE1F983c29f7A6C0C0dFA78C4D8Fe7bdfe026d4B",

    "NU_OLD": "0x4fE83213D56308330EC302a8BD641f1d0113A4Cc",
    "KEEP_OLD": "0x85eee30c52b0b379b046fb0f85f4f3dc3009afec",
    "T_NEW": "0xCdF7028ceAB81fA0C6971208e83fa7872994beE5",
    "NU_VENDING_MACHINE": "0x1CCA7E410eE41739792eA0A24e00349Dd247680e",
    "KEEP_VENDING_MACHINE": "0xE47c80e8c23f6B4A1aE41c34837a0599D5D16bb0",
}

PREIDENTIFIED_TXS = {
    # threshold-network/tbtc-v2 first-party deployment JSON
    "TBTC_V2_DEPLOY": "0x52538ac60ce0a5672aa77991e9f030ca6eed76db0bf027821ed5170b29971ba2",
    "TBTC_VENDING_MACHINE_V2_DEPLOY": "0x5bc28acae7868f6d7a954c5d193f19bd72ee04fade07d616c8d6ed89091e8750",
    # threshold-network/solidity-contracts first-party deployment JSON
    "T_DEPLOY": "0xdfc479f92a88c0a7a2148227c0d4c07db077df75ced4b0409465459a6b1a2454",
    "NU_VENDING_MACHINE_DEPLOY": "0x448ce43a7b3b1bdae0abfc60f7325e41a456fd47b3eecd66c873ab92baf14b31",
}

_counter = 0

def rpc(method, params):
    global _counter
    last = None
    payload = json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    for endpoint in RPCS:
        try:
            req = urllib.request.Request(endpoint, data=payload, headers={
                "Content-Type":"application/json",
                "User-Agent":"CryptoLab-TMFCB-V03/1.0"
            })
            with urllib.request.urlopen(req, timeout=25) as r:
                out=json.load(r)
            if "error" in out:
                last=RuntimeError(str(out["error"]))
                continue
            _counter += 1
            if _counter % 20 == 0:
                time.sleep(0.2)
            return out.get("result")
        except Exception as e:
            last=e
    raise RuntimeError(f"RPC_FAIL {method}: {type(last).__name__}: {last}")

def latest_block_number():
    b=rpc("eth_getBlockByNumber", ["latest", False])
    if not b or not b.get("number"):
        raise RuntimeError("LATEST_BLOCK_UNAVAILABLE")
    return int(b["number"],16)

def code_at(addr, block):
    tag = hex(block) if isinstance(block,int) else block
    return rpc("eth_getCode", [addr, tag]) not in (None, "0x", "0x0")

def first_code_block(addr, upper):
    if not code_at(addr, upper):
        return None
    lo, hi = 0, upper
    while lo < hi:
        mid = (lo + hi) // 2
        if code_at(addr, mid):
            hi = mid
        else:
            lo = mid + 1
    return lo

def block_meta(block):
    b=rpc("eth_getBlockByNumber", [hex(block), False])
    if not b:
        return None
    return {
        "block": block,
        "hash": b.get("hash"),
        "timestamp_unix": int(b["timestamp"],16) if b.get("timestamp") else None,
    }

def receipt_meta(tx):
    r=rpc("eth_getTransactionReceipt",[tx])
    if not r:
        return None
    block=int(r["blockNumber"],16)
    return {
        "transactionHash": r.get("transactionHash"),
        "blockNumber": block,
        "blockHash": r.get("blockHash"),
        "status": int(r["status"],16) if r.get("status") else None,
        "contractAddress": r.get("contractAddress"),
        "blockMeta": block_meta(block),
    }

UPPER_BLOCK=latest_block_number()
result={"probe_version":"TMFCB_V0.3","upper_block":UPPER_BLOCK,"contracts":{},"preidentified_receipts":{}}
for label,addr in CONTRACTS.items():
    try:
        fb=first_code_block(addr, UPPER_BLOCK)
        result["contracts"][label]={
            "address":addr,
            "first_code_block":fb,
            "first_code_block_meta": block_meta(fb) if fb is not None else None,
        }
    except Exception as e:
        result["contracts"][label]={"address":addr,"error":str(e)}

for label,tx in PREIDENTIFIED_TXS.items():
    try:
        result["preidentified_receipts"][label]=receipt_meta(tx)
    except Exception as e:
        result["preidentified_receipts"][label]={"tx":tx,"error":str(e)}

print(json.dumps(result, indent=2, sort_keys=True))

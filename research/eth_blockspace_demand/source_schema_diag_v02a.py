#!/usr/bin/env python3
from __future__ import annotations
import json, requests, sys
BLOCKS=[13_158_400,13_756_000,20_941_600]
EPS=["https://eth.drpc.org","https://rpc.flashbots.net"]
def rpc(ep,b):
    r=requests.post(ep,json={"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":[hex(b),False]},timeout=(8,25))
    r.raise_for_status(); o=r.json(); return o["result"]
def qi(x): return int(x,16)
out={"classification":"SOURCE_SCHEMA_DIAGNOSTIC","market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"blocks":{}}
for b in BLOCKS:
    out["blocks"][str(b)]={}
    for ep in EPS:
        try:
            x=rpc(ep,b)
            gl=qi(x["gasLimit"]); gu=qi(x["gasUsed"]); bf=qi(x["baseFeePerGas"])
            out["blocks"][str(b)][ep]={"number_match":qi(x["number"])==b,"gas_limit_positive":gl>0,
                "gas_used_zero":gu==0,"gas_used_nonnegative":gu>=0,"gas_used_le_limit":gu<=gl,
                "base_fee_positive":bf>0,"timestamp_pre_2025":qi(x["timestamp"])<1735689600,
                "block_hash":x["hash"].lower()}
        except Exception as e:
            out["blocks"][str(b)][ep]={"error":f"{type(e).__name__}:{str(e)[:120]}"}
print(json.dumps(out,sort_keys=True))
open("ETH_BLOCKSPACE_SCHEMA_DIAGNOSTIC_V0_2A.json","w").write(json.dumps(out,indent=2,sort_keys=True))

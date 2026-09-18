#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
import requests

ENDPOINTS=[
 "https://eth.leorpc.com/?api_key=FREE",
 "https://ethereum-rpc.polkachu.com",
 "https://g.w.lavanet.xyz:443/gateway/eth/rpc-http/f7ee0000000000000000000000000000",
 "https://eth-mainnet-public.unifra.io",
 "https://api.blockeden.xyz/eth/67nCBdZQSH9z3YqDDjdm",
 "https://eth.rpc.hypersync.xyz/",
 "https://eth.rpc.thirdweb.com/",
 "https://eth.croswap.com/rpc",
 "https://cloudflare-eth.com",
 "https://rpc.mevblocker.io",
 "https://eth.meowrpc.com",
 "https://ethereum.blinklabs.xyz/",
 "https://api.edennetwork.io/v1/rocket",
 "https://ethereum-api.flare.network/",
 "https://api.noderpc.xyz/rpc-mainnet/public",
 "https://public-eth.nownodes.io/",
]
BLOCKS=[17748972,19007945,20266917,21525890]
TO="0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
DATA="0x313ce567"

def opaque_hash(result): return hashlib.sha256(result.encode()).hexdigest()

def single(session,ep,bn,idx):
    payload={"jsonrpc":"2.0","id":idx,"method":"eth_call","params":[{"to":TO,"data":DATA},hex(bn)]}
    t=time.time()
    try:
        r=session.post(ep,json=payload,headers={"content-type":"application/json","user-agent":"AAVE-R1-archive-feas-v02c"},timeout=(8,25))
        ms=round((time.time()-t)*1000,1); status=r.status_code
        try: obj=r.json()
        except Exception: obj=None
        r.close()
        if status!=200 or not isinstance(obj,dict) or obj.get("error") is not None:
            return {"ok":False,"http_status":status,"latency_ms":ms,"error_code":(obj.get("error") or {}).get("code") if isinstance(obj,dict) else None}
        res=obj.get("result")
        if not isinstance(res,str) or not res.startswith("0x"):
            return {"ok":False,"http_status":status,"latency_ms":ms,"error_code":"invalid_result"}
        return {"ok":True,"http_status":status,"latency_ms":ms,"result_len":len(res),"result_sha256":opaque_hash(res)}
    except Exception as exc:
        return {"ok":False,"http_status":None,"latency_ms":None,"error_code":type(exc).__name__}

def batch(session,ep):
    payload=[{"jsonrpc":"2.0","id":i,"method":"eth_call","params":[{"to":TO,"data":DATA},hex(b)]} for i,b in enumerate(BLOCKS)]
    t=time.time()
    try:
        r=session.post(ep,json=payload,headers={"content-type":"application/json","user-agent":"AAVE-R1-archive-feas-v02c"},timeout=(8,30))
        ms=round((time.time()-t)*1000,1); status=r.status_code
        try: obj=r.json()
        except Exception: obj=None
        r.close()
        if status!=200 or not isinstance(obj,list):
            return {"ok":False,"http_status":status,"latency_ms":ms,"shape":type(obj).__name__,"items":[]}
        byid={x.get("id"):x for x in obj if isinstance(x,dict)}
        items=[]
        for i,b in enumerate(BLOCKS):
            x=byid.get(i)
            if not x or x.get("error") is not None:
                items.append({"block":b,"ok":False,"error_code":(x.get("error") or {}).get("code") if isinstance(x,dict) else "missing"})
            else:
                res=x.get("result")
                if isinstance(res,str) and res.startswith("0x"):
                    items.append({"block":b,"ok":True,"result_len":len(res),"result_sha256":opaque_hash(res)})
                else:
                    items.append({"block":b,"ok":False,"error_code":"invalid_result"})
        return {"ok":all(x["ok"] for x in items),"http_status":status,"latency_ms":ms,"shape":"list","items":items}
    except Exception as exc:
        return {"ok":False,"http_status":None,"latency_ms":None,"shape":None,"items":[],"error_code":type(exc).__name__}

def main():
    results={}; passing=[]
    for ep in ENDPOINTS:
        s=requests.Session()
        singles=[single(s,ep,b,i) for i,b in enumerate(BLOCKS)]
        bat=batch(s,ep); s.close()
        agree=False
        if all(x.get("ok") for x in singles) and bat.get("ok"):
            bi={x["block"]:x for x in bat["items"]}
            agree=all(singles[i]["result_sha256"]==bi[b]["result_sha256"] for i,b in enumerate(BLOCKS))
        ep_pass=all(x.get("ok") for x in singles) and bat.get("ok") and agree
        if ep_pass: passing.append(ep)
        results[ep]={"endpoint_pass":ep_pass,"single_calls":[{"block":b,**x} for b,x in zip(BLOCKS,singles)],"batch":bat,"single_batch_hash_agreement":agree}
    classification="ARCHIVE_RPC_PUBLIC_EXPANSION_PASS" if len(passing)>=2 else "ARCHIVE_RPC_PUBLIC_EXPANSION_INSUFFICIENT"
    receipt={"classification":classification,"passing_endpoint_count":len(passing),"passing_endpoints":passing,"endpoint_results":results,
      "safety":{"scaled_balance_target_calls_made":False,"health_factor_computed":False,"overhang_computed":False,"market_prices_opened":False,"returns_opened":False,"pnl_opened":False,"accessed_2025_or_2026":False,"live_trading":False,"exchange_mutation":False}}
    Path("archive_rpc_expansion_output").mkdir(exist_ok=True)
    Path("archive_rpc_expansion_output/AAVE_ARCHIVE_RPC_PUBLIC_EXPANSION_V0_2C.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"passing_endpoint_count":len(passing),"passing_endpoints":passing,"scaled_balance_target_calls_made":False},sort_keys=True))
    raise SystemExit(0 if classification=="ARCHIVE_RPC_PUBLIC_EXPANSION_PASS" else 2)
if __name__=="__main__": main()

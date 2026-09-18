#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, time
from pathlib import Path
import requests

ENDPOINTS=[
 "https://ethereum.rpc.subquery.network/public",
 "https://eth.merkle.io",
 "https://eth-mainnet.public.blastapi.io",
 "https://ethereum.blockpi.network/v1/rpc/public",
 "https://eth.api.onfinality.io/public",
 "https://endpoints.omniatech.io/v1/eth/mainnet/public",
 "https://rpc.flashbots.net",
]
BLOCKS=[17748972,19007945,20266917,21525890]
TO="0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48"
DATA="0x313ce567"

def opaque_hash(result:str)->str:
    return hashlib.sha256(result.encode("ascii","strict")).hexdigest()

def call_one(session,ep,bn,idx):
    payload={"jsonrpc":"2.0","id":idx,"method":"eth_call","params":[{"to":TO,"data":DATA},hex(bn)]}
    t=time.time()
    try:
        r=session.post(ep,json=payload,headers={"content-type":"application/json","user-agent":"AAVE-R1-archive-feas-v02b"},timeout=(10,35))
        ms=round((time.time()-t)*1000,1)
        status=r.status_code
        try: obj=r.json()
        except Exception: obj=None
        r.close()
        if status!=200 or not isinstance(obj,dict) or obj.get("error") is not None:
            return {"ok":False,"http_status":status,"latency_ms":ms,"shape":type(obj).__name__,
                    "error_code":(obj.get("error") or {}).get("code") if isinstance(obj,dict) else None}
        res=obj.get("result")
        if not isinstance(res,str) or not res.startswith("0x"):
            return {"ok":False,"http_status":status,"latency_ms":ms,"shape":"dict","error_code":"invalid_result"}
        return {"ok":True,"http_status":status,"latency_ms":ms,"shape":"dict","result_len":len(res),"result_sha256":opaque_hash(res)}
    except Exception as exc:
        return {"ok":False,"http_status":None,"latency_ms":None,"shape":None,"error_code":type(exc).__name__}

def call_batch(session,ep):
    payload=[{"jsonrpc":"2.0","id":i,"method":"eth_call","params":[{"to":TO,"data":DATA},hex(b)]} for i,b in enumerate(BLOCKS)]
    t=time.time()
    try:
        r=session.post(ep,json=payload,headers={"content-type":"application/json","user-agent":"AAVE-R1-archive-feas-v02b"},timeout=(10,45))
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
                items.append({"block":b,"ok":False,"error_code":(x.get("error") or {}).get("code") if isinstance(x,dict) else "missing_id"})
                continue
            res=x.get("result")
            if not isinstance(res,str) or not res.startswith("0x"):
                items.append({"block":b,"ok":False,"error_code":"invalid_result"}); continue
            items.append({"block":b,"ok":True,"result_len":len(res),"result_sha256":opaque_hash(res)})
        return {"ok":all(x["ok"] for x in items),"http_status":status,"latency_ms":ms,"shape":"list","items":items}
    except Exception as exc:
        return {"ok":False,"http_status":None,"latency_ms":None,"shape":None,"items":[],"error_code":type(exc).__name__}

def main():
    results={}
    passing=[]
    for ep in ENDPOINTS:
        s=requests.Session()
        singles=[call_one(s,ep,b,i) for i,b in enumerate(BLOCKS)]
        batch=call_batch(s,ep)
        s.close()
        agree=False
        if all(x.get("ok") for x in singles) and batch.get("ok"):
            bitems={x["block"]:x for x in batch["items"]}
            agree=all(singles[i]["result_sha256"]==bitems[b]["result_sha256"] for i,b in enumerate(BLOCKS))
        ep_pass=all(x.get("ok") for x in singles) and batch.get("ok") and agree
        if ep_pass: passing.append(ep)
        results[ep]={
          "endpoint_pass":ep_pass,
          "single_calls":[{"block":b,**x} for b,x in zip(BLOCKS,singles)],
          "batch":batch,
          "single_batch_hash_agreement":agree
        }
    classification="ARCHIVE_RPC_REPLACEMENT_SOURCE_PASS" if len(passing)>=3 else "ARCHIVE_RPC_REPLACEMENT_SOURCE_INSUFFICIENT"
    receipt={
      "classification":classification,
      "frozen_blocks":BLOCKS,
      "candidate_endpoint_count":len(ENDPOINTS),
      "passing_endpoint_count":len(passing),
      "passing_endpoints":passing,
      "endpoint_results":results,
      "safety":{
        "scaled_balance_target_calls_made":False,
        "health_factor_computed":False,
        "overhang_computed":False,
        "market_prices_opened":False,
        "returns_opened":False,
        "pnl_opened":False,
        "accessed_2025_or_2026":False,
        "live_trading":False,
        "exchange_mutation":False
      }
    }
    Path("archive_rpc_feas_output").mkdir(exist_ok=True)
    Path("archive_rpc_feas_output/AAVE_ARCHIVE_RPC_REPLACEMENT_SOURCE_FEASIBILITY_V0_2B.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":classification,"passing_endpoint_count":len(passing),"passing_endpoints":passing,"scaled_balance_target_calls_made":False},sort_keys=True))
    raise SystemExit(0 if classification=="ARCHIVE_RPC_REPLACEMENT_SOURCE_PASS" else 2)

if __name__=="__main__":
    main()

#!/usr/bin/env python3
import json, urllib.request, time, hashlib, sys
EPS=["https://eth.drpc.org","https://rpc.flashbots.net"]
REQ=["number","hash","timestamp","gasLimit","gasUsed","baseFeePerGas","blobGasUsed","excessBlobGas"]
def rpc(ep,method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(ep,data=body,headers={"Content-Type":"application/json","User-Agent":"EBST-source-probe-v0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        o=json.loads(r.read().decode())
    if o.get("error") is not None: raise RuntimeError(str(o["error"]))
    return o.get("result")
def qi(x): return int(x,16)
def fetch(ep,tag):
    o=rpc(ep,"eth_getBlockByNumber",[tag,False])
    if not isinstance(o,dict): raise RuntimeError("null block")
    miss=[k for k in REQ if o.get(k) is None]
    if miss: raise RuntimeError("missing:"+",".join(miss))
    return o
def main():
    out={"lab_id":"ETH-BLOCKSPACE-STATE-TRANSITION-001","classification":"SOURCE_SCHEMA_FAILURE","providers":{},"samples":[],"market_outcomes_opened":False}
    try:
        for ep in EPS:
            cid=rpc(ep,"eth_chainId",[])
            out["providers"][ep]={"chain_id":cid,"ok":cid=="0x1"}
            if cid!="0x1": raise RuntimeError("wrong chain")
        tip=fetch(EPS[0],"finalized")
        n=qi(tip["number"])
        # audit one exact finalized height on both providers
        exact=[]
        for ep in EPS:
            b=fetch(ep,hex(n)); exact.append(b)
        if len({b["hash"].lower() for b in exact})!=1: raise RuntimeError("provider hash disagreement")
        # bounded ~7 day historical source-only sample, ~12 samples/day
        start=max(0,n-50400)
        heights=list(range(start,n+1,600))
        if heights[-1]!=n: heights.append(n)
        for i,h in enumerate(heights):
            b=fetch(EPS[i%2],hex(h))
            gl=qi(b["gasLimit"]); gu=qi(b["gasUsed"]); bg=qi(b["blobGasUsed"]); ex=qi(b["excessBlobGas"])
            if gl<=0 or gu<0 or gu>gl or bg<0 or ex<0: raise RuntimeError("header sanity")
            out["samples"].append({"number":h,"hash":b["hash"].lower(),"timestamp":qi(b["timestamp"]),"gas_utilization":gu/gl,"blob_gas_used":bg,"excess_blob_gas":ex})
            time.sleep(0.03)
        out["classification"]="SOURCE_SCHEMA_PASS"
        out["sample_count"]=len(out["samples"])
        out["latest_finalized_number"]=n
        out["required_fields"]=REQ
    except Exception as e:
        out["failure"]=f"{type(e).__name__}:{e}"
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    out["receipt_sha256"]=hashlib.sha256(raw).hexdigest()
    open("EBST_SOURCE_PROBE_V0_1.json","w",encoding="utf-8").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"classification":out["classification"],"sample_count":out.get("sample_count",0),"failure":out.get("failure")},sort_keys=True))
    return 0 if out["classification"]=="SOURCE_SCHEMA_PASS" else 2
if __name__=="__main__": sys.exit(main())

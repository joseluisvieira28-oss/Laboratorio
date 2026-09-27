#!/usr/bin/env python3
import json, urllib.request, hashlib, sys
EP="https://public.1rpc.io/eth"
REQ=["number","hash","timestamp","gasLimit","gasUsed","baseFeePerGas","blobGasUsed","excessBlobGas"]
def rpc(method,params):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(EP,data=body,headers={"Content-Type":"application/json","User-Agent":"EBST-provider-qual-v0.1a"})
    with urllib.request.urlopen(req,timeout=30) as r:
        o=json.loads(r.read().decode())
    if o.get("error") is not None: raise RuntimeError(str(o["error"]))
    return o.get("result")
def main():
    out={"provider":EP,"classification":"PROVIDER_QUAL_FAIL","market_prices_opened":False}
    try:
        if rpc("eth_chainId",[])!="0x1": raise RuntimeError("wrong chain")
        b=rpc("eth_getBlockByNumber",["finalized",False])
        miss=[k for k in REQ if not isinstance(b,dict) or b.get(k) is None]
        if miss: raise RuntimeError("missing:"+",".join(miss))
        out["classification"]="PROVIDER_QUAL_PASS"
        out["block_number"]=int(b["number"],16)
        out["block_hash"]=b["hash"].lower()
    except Exception as e:
        out["failure"]=f"{type(e).__name__}:{e}"
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    out["receipt_sha256"]=hashlib.sha256(raw).hexdigest()
    open("EBST_PROVIDER_QUAL_V0_1A.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0 if out["classification"]=="PROVIDER_QUAL_PASS" else 2
if __name__=="__main__": sys.exit(main())

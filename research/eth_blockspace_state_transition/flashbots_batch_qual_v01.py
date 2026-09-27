#!/usr/bin/env python3
import json, urllib.request, hashlib, sys
EP="https://rpc.flashbots.net"
def post(payload):
    body=json.dumps(payload).encode()
    req=urllib.request.Request(EP,data=body,headers={"Content-Type":"application/json","User-Agent":"EBST-flashbots-batch-qual-v0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode())
def main():
    out={"provider":EP,"classification":"BATCH_QUAL_FAIL","market_prices_opened":False}
    try:
        tip=post({"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":["finalized",False]})
        n=int(tip["result"]["number"],16)
        reqs=[{"jsonrpc":"2.0","id":i,"method":"eth_getBlockByNumber","params":[hex(n-i),False]} for i in range(2)]
        res=post(reqs)
        if not isinstance(res,list) or len(res)!=2: raise RuntimeError("batch response invalid")
        if any(x.get("error") is not None or not isinstance(x.get("result"),dict) for x in res):
            raise RuntimeError("batch item failure")
        out["classification"]="BATCH_QUAL_PASS"
        out["heights"]=[n,n-1]
    except Exception as e:
        out["failure"]=f"{type(e).__name__}:{e}"
    raw=json.dumps(out,sort_keys=True,separators=(",",":")).encode()
    out["receipt_sha256"]=hashlib.sha256(raw).hexdigest()
    open("EBST_FLASHBOTS_BATCH_QUAL_V0_1.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0 if out["classification"]=="BATCH_QUAL_PASS" else 2
if __name__=="__main__": sys.exit(main())

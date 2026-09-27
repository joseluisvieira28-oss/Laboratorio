#!/usr/bin/env python3
import json, urllib.request, sys
HEIGHTS=[25851639,25851640,25851641]
EPS=["https://rpc.flashbots.net","https://public.1rpc.io/eth","https://eth.drpc.org"]
def call(ep,h):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":[hex(h),False]}).encode()
    req=urllib.request.Request(ep,data=body,headers={"Content-Type":"application/json","User-Agent":"EBST-depth-probe-v0.1"})
    try:
        with urllib.request.urlopen(req,timeout=30) as r: o=json.loads(r.read().decode())
        x=o.get("result") if isinstance(o,dict) else None
        return {"http":"ok","rpc_error":o.get("error") if isinstance(o,dict) else "non-dict",
                "has_block":isinstance(x,dict),"hash":x.get("hash") if isinstance(x,dict) else None,
                "timestamp":x.get("timestamp") if isinstance(x,dict) else None}
    except Exception as e:
        return {"http":"fail","error":f"{type(e).__name__}:{e}"}
def main():
    out={"classification":"DEPTH_PROBE","market_prices_opened":False,"heights":{}}
    for h in HEIGHTS:
        out["heights"][str(h)]={ep:call(ep,h) for ep in EPS}
    print(json.dumps(out,sort_keys=True))
    open("EBST_DEPTH_PROBE_V0_1.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
    return 0
if __name__=="__main__": sys.exit(main())

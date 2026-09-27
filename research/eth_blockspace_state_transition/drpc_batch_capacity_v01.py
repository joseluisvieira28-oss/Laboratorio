#!/usr/bin/env python3
import json, urllib.request, sys
EP="https://eth.drpc.org"
SIZES=[2,5,10]
def post(payload):
    body=json.dumps(payload).encode()
    req=urllib.request.Request(EP,data=body,headers={"Content-Type":"application/json","User-Agent":"EBST-drpc-batch-cap-v0.1"})
    with urllib.request.urlopen(req,timeout=30) as r:
        return json.loads(r.read().decode())
def main():
    out={"provider":EP,"classification":"BATCH_CAPACITY_FAIL","sizes":{},"market_prices_opened":False}
    try:
        tip=post({"jsonrpc":"2.0","id":1,"method":"eth_getBlockByNumber","params":["finalized",False]})
        n=int(tip["result"]["number"],16)
        for sz in SIZES:
            try:
                reqs=[{"jsonrpc":"2.0","id":i,"method":"eth_getBlockByNumber","params":[hex(n-i),False]} for i in range(sz)]
                res=post(reqs)
                ok=isinstance(res,list) and len(res)==sz and all(isinstance(x,dict) and x.get("error") is None and isinstance(x.get("result"),dict) for x in res)
                out["sizes"][str(sz)]={"pass":bool(ok),"response_type":type(res).__name__,"response_len":len(res) if isinstance(res,list) else None}
            except Exception as e:
                out["sizes"][str(sz)]={"pass":False,"failure":f"{type(e).__name__}:{e}"}
        passed=[int(k) for k,v in out["sizes"].items() if v.get("pass")]
        out["max_tested_passing_batch"]=max(passed) if passed else None
        out["classification"]="BATCH_CAPACITY_PASS" if passed else "BATCH_CAPACITY_FAIL"
    except Exception as e:
        out["failure"]=f"{type(e).__name__}:{e}"
    open("EBST_DRPC_BATCH_CAPACITY_V0_1.json","w").write(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,sort_keys=True))
    return 0 if out["classification"]=="BATCH_CAPACITY_PASS" else 2
if __name__=="__main__": sys.exit(main())

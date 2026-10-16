#!/usr/bin/env python3
import json,time,urllib.request
from pathlib import Path

URL="https://api.hyperliquid.xyz/info"

def main():
    body=json.dumps({"type":"metaAndAssetCtxs"}).encode()
    req=urllib.request.Request(URL,data=body,headers={"Content-Type":"application/json","User-Agent":"Crypto-Lab-LICP-OI/0.1"},method="POST")
    with urllib.request.urlopen(req,timeout=15) as r:
        j=json.loads(r.read().decode())
    meta,ctxs=j
    out={"purpose":"HYPERLIQUID OI SOURCE ONLY","assets":{}}
    for i,u in enumerate(meta["universe"]):
        name=u.get("name")
        if name in ("BTC","ETH","SOL"):
            c=ctxs[i]
            out["assets"][name]={"openInterest":c.get("openInterest"),"markPx":c.get("markPx")}
    out["gate"]="PASS_SAMPLE" if all(out["assets"].get(x,{}).get("openInterest") is not None for x in ("BTC","ETH","SOL")) else "BLOCKED"
    out["checked_unix_ms"]=int(time.time()*1000)
    p=Path("research/liquidation_cascade/receipts");p.mkdir(parents=True,exist_ok=True)
    (p/"licp001_hl_oi_probe_v01.json").write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out["gate"]=="PASS_SAMPLE" else 2)

if __name__=="__main__":main()

#!/usr/bin/env python3
import asyncio,json,time
from pathlib import Path
import websockets

URL="wss://ws.okx.com:8443/ws/v5/public"
SUB={"op":"subscribe","args":[{"channel":"liquidation-orders","instType":"SWAP"}]}

async def main():
    result={"source":"OKX","channel":"liquidation-orders","instType":"SWAP",
            "endpoint":URL,"subscription_ack":False,"error":None,
            "messages":0,"data_rows":0,"btc_rows":0,"seconds":120,
            "role":"ROBUSTNESS_ONLY_NOT_PRIMARY_TRIGGER"}
    try:
        async with websockets.connect(URL,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
            await ws.send(json.dumps(SUB))
            end=time.monotonic()+120
            while time.monotonic()<end:
                try:raw=await asyncio.wait_for(ws.recv(),timeout=5)
                except asyncio.TimeoutError:continue
                result["messages"]+=1
                m=json.loads(raw)
                if m.get("event")=="subscribe":
                    result["subscription_ack"]=True
                if m.get("event")=="error":
                    result["error"]={"code":m.get("code"),"msg":m.get("msg")}
                    break
                rows=m.get("data")
                if isinstance(rows,list):
                    result["data_rows"]+=len(rows)
                    for r in rows:
                        if "BTC" in str(r.get("instId","")): result["btc_rows"]+=1
    except Exception as e:
        result["error"]={"exception":repr(e)}
    result["decision"]="PASS_SAMPLE" if result["subscription_ack"] and result["error"] is None else "SOURCE_BLOCKED"
    out=Path("research/liquidation_cascade/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"licp_okx_liquidation_source_probe_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["decision"]=="SOURCE_BLOCKED": raise SystemExit(2)

if __name__=="__main__":asyncio.run(main())

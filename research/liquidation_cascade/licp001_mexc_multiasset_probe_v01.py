#!/usr/bin/env python3
import asyncio,json,time
from pathlib import Path
import websockets

URL="wss://contract.mexc.com/edge"
SYMS=("BTC_USDT","ETH_USDT","SOL_USDT")
SECONDS=30

async def one(sym):
    out={"symbol":sym,"ack":False,"messages":0,"depth_updates":0,"crossed":0,
         "clock_regressions":0,"version_regressions":0,"heartbeats":0}
    bids={};asks={};last_local=None;last_v=None
    async with websockets.connect(URL,ping_interval=None,max_size=8_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":sym}}))
        next_ping=time.monotonic()+10
        deadline=time.monotonic()+SECONDS
        while time.monotonic()<deadline:
            timeout=max(.1,min(2,next_ping-time.monotonic(),deadline-time.monotonic()))
            try:raw=await asyncio.wait_for(ws.recv(),timeout)
            except asyncio.TimeoutError:
                if time.monotonic()>=next_ping:
                    await ws.send(json.dumps({"method":"ping"}));out["heartbeats"]+=1;next_ping=time.monotonic()+10
                continue
            if time.monotonic()>=next_ping:
                await ws.send(json.dumps({"method":"ping"}));out["heartbeats"]+=1;next_ping=time.monotonic()+10
            now=time.monotonic_ns()
            if last_local is not None and now<last_local:out["clock_regressions"]+=1
            last_local=now;out["messages"]+=1
            m=json.loads(raw)
            if m.get("channel")=="rs.sub.depth" and m.get("data")=="success":
                out["ack"]=True;continue
            if m.get("channel")!="push.depth":continue
            d=m.get("data") or {};v=d.get("version")
            if v is not None:
                v=int(v)
                if last_v is not None and v<=last_v:out["version_regressions"]+=1
                last_v=v
            for p,q,*_ in d.get("bids",[]):
                p=float(p);q=float(q)
                if q==0:bids.pop(p,None)
                else:bids[p]=q
            for p,q,*_ in d.get("asks",[]):
                p=float(p);q=float(q)
                if q==0:asks.pop(p,None)
                else:asks[p]=q
            if bids and asks:
                out["depth_updates"]+=1
                if max(bids)>=min(asks):out["crossed"]+=1
    out["gate"]="PASS_SAMPLE" if (
        out["ack"] and out["depth_updates"]>=20 and out["crossed"]==0 and
        out["clock_regressions"]==0 and out["version_regressions"]==0
    ) else "BLOCKED"
    return out

async def main_async():
    rows=await asyncio.gather(*(one(s) for s in SYMS),return_exceptions=True)
    norm=[{"error":repr(x)} if isinstance(x,Exception) else x for x in rows]
    result={"purpose":"MEXC MULTI-ASSET SOURCE ONLY","seconds":SECONDS,"symbols":norm}
    result["gate"]="PASS_SAMPLE" if all(x.get("gate")=="PASS_SAMPLE" for x in norm) else "BLOCKED"
    out=Path("research/liquidation_cascade/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"licp001_mexc_multiasset_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))
    raise SystemExit(0 if result["gate"]=="PASS_SAMPLE" else 2)

if __name__=="__main__":asyncio.run(main_async())

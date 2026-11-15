#!/usr/bin/env python3
import asyncio
import json
import time
from pathlib import Path
import websockets

SECONDS=90
BINANCE_MARKET="wss://fstream.binance.com/market/stream"
BINANCE_BBO="wss://fstream.binance.com/ws/btcusdt@bookTicker"
BYBIT="wss://stream.bybit.com/v5/public/linear"
MEXC="wss://contract.mexc.com/edge"

async def binance_liquidations(stop):
    out={"subscription_ack":False,"messages":0,"liquidation_events":0,
         "malformed_liquidations":0,"clock_regressions":0}
    last=None
    async with websockets.connect(BINANCE_MARKET,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1}))
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError: continue
            now=time.monotonic_ns()
            if last is not None and now<last: out["clock_regressions"]+=1
            last=now; out["messages"]+=1
            msg=json.loads(raw)
            if msg.get("id")==1 and msg.get("result") is None:
                out["subscription_ack"]=True; continue
            data=msg.get("data",msg)
            if data.get("e")!="forceOrder": continue
            try:
                o=data["o"]
                required=("s","S","q","p","ap","l","z","T")
                if any(k not in o for k in required): raise ValueError("missing_field")
                out["liquidation_events"]+=1
            except Exception:
                out["malformed_liquidations"]+=1
    return out

async def binance_bbo(stop):
    out={"connected":False,"updates":0,"crossed_bbo":0,"clock_regressions":0}
    last=None
    async with websockets.connect(BINANCE_BBO,ping_interval=20,ping_timeout=20,max_size=2_000_000) as ws:
        out["connected"]=True
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError: continue
            now=time.monotonic_ns()
            if last is not None and now<last: out["clock_regressions"]+=1
            last=now
            m=json.loads(raw)
            try:
                bid=float(m["b"]); ask=float(m["a"])
                out["updates"]+=1
                if bid>=ask: out["crossed_bbo"]+=1
            except Exception:
                pass
    return out

async def bybit_probe(stop):
    out={"subscription_ack":False,"messages":0,"liquidation_events":0,
         "malformed_liquidations":0,"clock_regressions":0}
    last=None
    async with websockets.connect(BYBIT,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"op":"subscribe","args":[
            "allLiquidation.BTCUSDT","allLiquidation.ETHUSDT","allLiquidation.SOLUSDT"
        ]}))
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),timeout=2)
            except asyncio.TimeoutError: continue
            now=time.monotonic_ns()
            if last is not None and now<last: out["clock_regressions"]+=1
            last=now; out["messages"]+=1
            msg=json.loads(raw)
            if msg.get("op")=="subscribe" and msg.get("success") is True:
                out["subscription_ack"]=True; continue
            if not msg.get("topic","").startswith("allLiquidation."): continue
            rows=msg.get("data")
            if not isinstance(rows,list):
                out["malformed_liquidations"]+=1; continue
            for row in rows:
                try:
                    for k in ("T","s","S","v","p"):
                        if k not in row: raise ValueError("missing_field")
                    out["liquidation_events"]+=1
                except Exception:
                    out["malformed_liquidations"]+=1
    return out

async def mexc_probe(stop):
    out={"subscription_ack":False,"messages":0,"depth_updates":0,
         "crossed_bbo":0,"clock_regressions":0,"version_regressions":0,
         "heartbeats_sent":0}
    bids={}; asks={}; last=None; last_version=None
    async with websockets.connect(MEXC,ping_interval=None,max_size=8_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":"BTC_USDT"}}))
        next_ping=time.monotonic()+10
        while not stop.is_set():
            timeout=max(0.1,min(2.0,next_ping-time.monotonic()))
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
            except asyncio.TimeoutError:
                if time.monotonic()>=next_ping:
                    await ws.send(json.dumps({"method":"ping"}))
                    out["heartbeats_sent"]+=1
                    next_ping=time.monotonic()+10
                continue
            if time.monotonic()>=next_ping:
                await ws.send(json.dumps({"method":"ping"}))
                out["heartbeats_sent"]+=1
                next_ping=time.monotonic()+10

            now=time.monotonic_ns()
            if last is not None and now<last: out["clock_regressions"]+=1
            last=now; out["messages"]+=1
            msg=json.loads(raw)
            if msg.get("channel")=="rs.sub.depth" and msg.get("data")=="success":
                out["subscription_ack"]=True; continue
            if msg.get("channel")!="push.depth": continue
            d=msg.get("data") or {}
            v=d.get("version")
            if v is not None:
                v=int(v)
                if last_version is not None and v<=last_version:
                    out["version_regressions"]+=1
                last_version=v
            for p,q,*_ in d.get("bids",[]):
                p=float(p); q=float(q)
                if q==0:bids.pop(p,None)
                else:bids[p]=q
            for p,q,*_ in d.get("asks",[]):
                p=float(p); q=float(q)
                if q==0:asks.pop(p,None)
                else:asks[p]=q
            if bids and asks:
                out["depth_updates"]+=1
                if max(bids)>=min(asks): out["crossed_bbo"]+=1
    return out

async def main_async():
    stop=asyncio.Event()
    tasks=[
        asyncio.create_task(binance_liquidations(stop)),
        asyncio.create_task(binance_bbo(stop)),
        asyncio.create_task(bybit_probe(stop)),
        asyncio.create_task(mexc_probe(stop)),
    ]
    await asyncio.sleep(SECONDS)
    stop.set()
    results=await asyncio.gather(*tasks,return_exceptions=True)
    def norm(x): return {"error":repr(x)} if isinstance(x,Exception) else x
    bl,bb,y,m=map(norm,results)
    receipt={"purpose":"LICP-001 SOURCE GATE ONLY — NO OUTCOMES / NO ORDERS",
             "seconds":SECONDS,"binance_liquidations":bl,"binance_bbo":bb,
             "bybit":y,"mexc":m}
    good=(
        bl.get("subscription_ack") is True and
        bb.get("connected") is True and bb.get("updates",0)>=10 and
        y.get("subscription_ack") is True and
        m.get("subscription_ack") is True and m.get("depth_updates",0)>=10 and
        bb.get("crossed_bbo",1)==0 and m.get("crossed_bbo",1)==0 and
        bl.get("clock_regressions",1)==0 and bb.get("clock_regressions",1)==0 and
        y.get("clock_regressions",1)==0 and m.get("clock_regressions",1)==0 and
        bl.get("malformed_liquidations",1)==0 and y.get("malformed_liquidations",1)==0
    )
    receipt["gate"]="PASS_SAMPLE" if good else "BLOCKED"
    out=Path("research/liquidation_cascade/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"licp001_source_gate_v01.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    return 0 if good else 2

def main():
    raise SystemExit(asyncio.run(main_async()))

if __name__=="__main__":
    main()

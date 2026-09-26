#!/usr/bin/env python3
"""LICP-001 outcome-blind forward liquidation collector.

Public data only. No auth, no orders, no future-return labels.
Writes append-only JSONL events and a health receipt.
"""
import argparse, asyncio, hashlib, json, os, signal, time
from datetime import datetime, timezone
from pathlib import Path
import websockets

BYBIT="wss://stream.bybit.com/v5/public/linear"
BINANCE="wss://fstream.binance.com/market/stream"
MEXC="wss://contract.mexc.com/edge"
SYMS={"BTCUSDT","ETHUSDT","SOLUSDT"}

def utc_ms(): return int(time.time()*1000)
def iso(): return datetime.now(timezone.utc).isoformat()
def append_jsonl(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open("a",encoding="utf-8") as f:
        f.write(json.dumps(obj,separators=(",",":"),sort_keys=True)+"\n")
        f.flush(); os.fsync(f.fileno())
def sha256(path):
    h=hashlib.sha256()
    if path.exists():
        with path.open("rb") as f:
            for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

async def bybit(stop,events,health):
    backoff=1
    while not stop.is_set():
        start=utc_ms()
        try:
            async with websockets.connect(BYBIT,ping_interval=20,ping_timeout=20,max_size=8_000_000) as ws:
                await ws.send(json.dumps({"op":"subscribe","args":[f"allLiquidation.{s}" for s in sorted(SYMS)]}))
                health["bybit"]["connects"]+=1; backoff=1
                while not stop.is_set():
                    raw=await asyncio.wait_for(ws.recv(),timeout=30)
                    recv=utc_ms(); mono=time.monotonic_ns(); msg=json.loads(raw)
                    if msg.get("op")=="subscribe":
                        health["bybit"]["acks"]+=int(msg.get("success") is True); continue
                    if not msg.get("topic","").startswith("allLiquidation."): continue
                    for r in msg.get("data") or []:
                        if r.get("s") not in SYMS: continue
                        try:
                            px=float(r["p"]); qty=float(r["v"])
                            e={"schema":"licp001.liq.v1","venue":"BYBIT","symbol":r["s"],
                               "exchange_ts_ms":int(r["T"]),"recv_ts_ms":recv,"recv_mono_ns":mono,
                               "liquidated_side":r["S"],"qty":qty,"price":px,
                               "notional_proxy":qty*px}
                            append_jsonl(events,e); health["bybit"]["events"]+=1
                        except Exception:
                            health["bybit"]["malformed"]+=1
        except Exception as e:
            health["bybit"]["disconnects"]+=1
            append_jsonl(events.parent/"gaps.jsonl",{"venue":"BYBIT","start_ms":start,"end_ms":utc_ms(),"error":repr(e)})
            await asyncio.sleep(backoff); backoff=min(backoff*2,30)

async def binance(stop,events,health):
    backoff=1
    while not stop.is_set():
        start=utc_ms()
        try:
            async with websockets.connect(BINANCE,ping_interval=20,ping_timeout=20,max_size=8_000_000) as ws:
                await ws.send(json.dumps({"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1}))
                health["binance"]["connects"]+=1; backoff=1
                while not stop.is_set():
                    raw=await asyncio.wait_for(ws.recv(),timeout=30)
                    recv=utc_ms(); mono=time.monotonic_ns(); msg=json.loads(raw)
                    if msg.get("id")==1:
                        health["binance"]["acks"]+=int(msg.get("result") is None); continue
                    d=msg.get("data",msg)
                    if d.get("e")!="forceOrder": continue
                    o=d.get("o") or {}
                    if o.get("s") not in SYMS: continue
                    try:
                        px=float(o["ap"] or o["p"]); qty=float(o["z"] or o["q"])
                        e={"schema":"licp001.liq.v1","venue":"BINANCE_SNAPSHOT","symbol":o["s"],
                           "exchange_ts_ms":int(o["T"]),"recv_ts_ms":recv,"recv_mono_ns":mono,
                           "liquidated_side":o["S"],"qty":qty,"price":px,
                           "notional_proxy":qty*px}
                        append_jsonl(events,e); health["binance"]["events"]+=1
                    except Exception:
                        health["binance"]["malformed"]+=1
        except Exception as e:
            health["binance"]["disconnects"]+=1
            append_jsonl(events.parent/"gaps.jsonl",{"venue":"BINANCE","start_ms":start,"end_ms":utc_ms(),"error":repr(e)})
            await asyncio.sleep(backoff); backoff=min(backoff*2,30)

async def mexc_health(stop,health):
    backoff=1
    while not stop.is_set():
        start=utc_ms()
        try:
            async with websockets.connect(MEXC,ping_interval=None,max_size=8_000_000) as ws:
                await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":"BTC_USDT"}}))
                health["mexc"]["connects"]+=1; backoff=1; next_ping=time.monotonic()+10
                while not stop.is_set():
                    timeout=max(.1,min(2,next_ping-time.monotonic()))
                    try: raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
                    except asyncio.TimeoutError:
                        raw=None
                    if time.monotonic()>=next_ping:
                        await ws.send(json.dumps({"method":"ping"})); next_ping=time.monotonic()+10
                    if not raw: continue
                    m=json.loads(raw)
                    if m.get("channel")=="rs.sub.depth" and m.get("data")=="success":
                        health["mexc"]["acks"]+=1
                    elif m.get("channel")=="push.depth":
                        health["mexc"]["depth_updates"]+=1
        except Exception as e:
            health["mexc"]["disconnects"]+=1
            health["mexc"]["last_error"]=repr(e)
            await asyncio.sleep(backoff); backoff=min(backoff*2,30)

async def run(seconds,outdir):
    outdir=Path(outdir); events=outdir/"liquidations.jsonl"
    stop=asyncio.Event()
    health={k:{"connects":0,"acks":0,"events":0,"malformed":0,"disconnects":0} for k in ("bybit","binance")}
    health["mexc"]={"connects":0,"acks":0,"depth_updates":0,"disconnects":0}
    loop=asyncio.get_running_loop()
    for s in (signal.SIGINT,signal.SIGTERM):
        try: loop.add_signal_handler(s,stop.set)
        except NotImplementedError: pass
    tasks=[asyncio.create_task(bybit(stop,events,health)),asyncio.create_task(binance(stop,events,health)),asyncio.create_task(mexc_health(stop,health))]
    try:
        await asyncio.wait_for(stop.wait(),timeout=seconds)
    except asyncio.TimeoutError:
        stop.set()
    await asyncio.gather(*tasks,return_exceptions=True)
    receipt={"schema":"licp001.health.v1","ended_at":iso(),"scheduled_seconds":seconds,
             "event_log":str(events),"event_log_sha256":sha256(events),"health":health,
             "outcome_blind":True}
    (outdir/"health.json").write_text(json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seconds",type=int,default=3600)
    p.add_argument("--outdir",default="research/liquidation_cascade/runtime_data")
    a=p.parse_args()
    asyncio.run(run(a.seconds,a.outdir))
if __name__=="__main__": main()

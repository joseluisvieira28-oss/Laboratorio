#!/usr/bin/env python3
"""LICP-FWD-XALT-004 locked forward transfer observer.

Refuses to initialize unless LICP-001 trigger config is FROZEN.
Research only: no orders/auth/exchange mutation.
"""
import asyncio, collections, json, time
from datetime import datetime, timezone
from pathlib import Path
import websockets

from research.liquidation_cascade.licp001_trigger_engine_v01 import (
    load_config, btc_ignition, aggregate_burst
)

CONFIG="research/liquidation_cascade/LICP_001_TRIGGER_CONFIG_V0_1.json"
BYBIT="wss://stream.bybit.com/v5/public/linear"
BINANCE="wss://fstream.binance.com/market/stream"
MEXC="wss://contract.mexc.com/edge"
ENTRY_DELAY_MS=60_000
HORIZON_MS=3_600_000
STALE_MS=1000
COOLDOWN_NS=120*1_000_000_000
FEE_BPS=16.0
SECONDS=300

def iso_ms(ms):
    return datetime.fromtimestamp(ms/1000,tz=timezone.utc).isoformat()

def bybit_event(r,local_ns):
    pressure="SELL" if r["S"]=="Buy" else ("BUY" if r["S"]=="Sell" else None)
    if pressure is None: raise ValueError("BAD_BYBIT_SIDE")
    return {"source":"bybit","symbol":r["s"],"venue_ts":int(r["T"]),
            "local_ns":local_ns,"pressure":pressure,
            "notional":float(r["v"])*float(r["p"])}

def binance_event(o,local_ns):
    pressure=o["S"]
    if pressure not in ("BUY","SELL"): raise ValueError("BAD_BINANCE_SIDE")
    z=float(o.get("z",0) or 0); ap=float(o.get("ap",0) or 0)
    notional=z*ap if z>0 and ap>0 else float(o.get("q",0) or 0)*float(o.get("p",0) or 0)
    return {"source":"binance","symbol":o["s"],"venue_ts":int(o["T"]),
            "local_ns":local_ns,"pressure":pressure,"notional":notional}

async def bybit_stream(stop,q,health):
    health.update({"ack":False,"events":0,"malformed":0})
    async with websockets.connect(BYBIT,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"op":"subscribe","args":["allLiquidation.BTCUSDT"]}))
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),2)
            except asyncio.TimeoutError: continue
            now=time.monotonic_ns(); m=json.loads(raw)
            if m.get("op")=="subscribe" and m.get("success") is True:
                health["ack"]=True; continue
            if m.get("topic")!="allLiquidation.BTCUSDT": continue
            rows=m.get("data")
            if not isinstance(rows,list):
                health["malformed"]+=1; continue
            for r in rows:
                try:
                    e=bybit_event(r,now); health["events"]+=1; await q.put(("liq",e))
                except Exception: health["malformed"]+=1

async def binance_stream(stop,q,health):
    health.update({"ack":False,"events":0,"malformed":0})
    async with websockets.connect(BINANCE,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1}))
        while not stop.is_set():
            try: raw=await asyncio.wait_for(ws.recv(),2)
            except asyncio.TimeoutError: continue
            now=time.monotonic_ns(); m=json.loads(raw)
            if m.get("id")==1 and m.get("result") is None:
                health["ack"]=True; continue
            d=m.get("data",m)
            if d.get("e")!="forceOrder": continue
            try:
                e=binance_event(d["o"],now)
                if e["symbol"]=="BTCUSDT":
                    health["events"]+=1; await q.put(("liq",e))
            except Exception: health["malformed"]+=1

async def mexc_sol(stop,q,health):
    health.update({"ack":False,"updates":0,"crossed":0,"version_regressions":0})
    bids={};asks={};last_v=None
    async with websockets.connect(MEXC,ping_interval=None,max_size=8_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":"SOL_USDT"}}))
        next_ping=time.monotonic()+10
        while not stop.is_set():
            timeout=max(.1,min(2,next_ping-time.monotonic()))
            try: raw=await asyncio.wait_for(ws.recv(),timeout)
            except asyncio.TimeoutError:
                if time.monotonic()>=next_ping:
                    await ws.send(json.dumps({"method":"ping"}));next_ping=time.monotonic()+10
                continue
            if time.monotonic()>=next_ping:
                await ws.send(json.dumps({"method":"ping"}));next_ping=time.monotonic()+10
            now=time.monotonic_ns();m=json.loads(raw)
            if m.get("channel")=="rs.sub.depth" and m.get("data")=="success":
                health["ack"]=True;continue
            if m.get("channel")!="push.depth":continue
            d=m.get("data") or {};v=d.get("version")
            if v is not None:
                v=int(v)
                if last_v is not None and v<=last_v:health["version_regressions"]+=1
                last_v=v
            for p,s,*_ in d.get("bids",[]):
                p=float(p);s=float(s)
                if s==0:bids.pop(p,None)
                else:bids[p]=s
            for p,s,*_ in d.get("asks",[]):
                p=float(p);s=float(s)
                if s==0:asks.pop(p,None)
                else:asks[p]=s
            if bids and asks:
                bid=max(bids);ask=min(asks)
                if bid>=ask:health["crossed"]+=1
                health["updates"]+=1
                await q.put(("bbo",{"local_ns":now,"wall_ms":int(time.time()*1000),"bid":bid,"ask":ask}))

async def coordinator(q,stop,cfg):
    liq=collections.deque();latest=None;pending=None;last_episode=None;records=[]
    while not stop.is_set() or not q.empty():
        try:kind,x=await asyncio.wait_for(q.get(),.2)
        except asyncio.TimeoutError:continue
        now=time.monotonic_ns()
        if kind=="bbo":
            latest=x
            for r in records:
                if r.get("entry") is None and now-r["event_local_ns"]>=ENTRY_DELAY_MS*1_000_000:
                    age=(now-x["local_ns"])/1e6
                    if age<=STALE_MS and x["bid"]<x["ask"]:
                        r["entry"]=dict(x);r["entry"]["entry_bid"]=x["bid"]
                elif r.get("entry") is not None and r.get("exit") is None:
                    if now-r["entry"]["local_ns"]>=HORIZON_MS*1_000_000:
                        age=(now-x["local_ns"])/1e6
                        if age<=STALE_MS and x["bid"]<x["ask"]:
                            r["exit"]=dict(x)
                            entry=r["entry"]["entry_bid"];exit_ask=x["ask"]
                            gross=(entry-exit_ask)/entry*10000.0
                            r["gross_bps"]=gross;r["net_taker_bps"]=gross-FEE_BPS
            continue

        liq.append(x)
        while liq and x["venue_ts"]-liq[0]["venue_ts"]>120_000:liq.popleft()
        events=list(liq)

        if x["source"]=="bybit":
            if last_episode is None or now-last_episode>=COOLDOWN_NS:
                ok,b=btc_ignition(events,x["venue_ts"],cfg)
                if ok and b.pressure=="SELL":
                    pending={"pressure":"SELL","bybit":b.__dict__,
                             "venue_ts":x["venue_ts"],"local_ns":now}
                    bc=aggregate_burst(events,"binance","BTCUSDT",x["venue_ts"],
                                       cfg["binance_confirmation"]["window_ms"])
                    if (bc.pressure=="SELL" and
                        bc.total_notional>=cfg["binance_confirmation"]["notional_threshold"]):
                        records.append({"family":"FWD_XALT_004","pressure":"SELL",
                                        "event_local_ns":now,"event_wall_ms":int(time.time()*1000),
                                        "bybit_burst":b.__dict__,"binance_burst":bc.__dict__,
                                        "entry":None,"exit":None})
                        last_episode=now;pending=None

        elif x["source"]=="binance" and pending:
            if (now-pending["local_ns"])/1e9<=5:
                bc=aggregate_burst(events,"binance","BTCUSDT",x["venue_ts"],
                                   cfg["binance_confirmation"]["window_ms"])
                if (bc.pressure=="SELL" and
                    bc.total_notional>=cfg["binance_confirmation"]["notional_threshold"]):
                    records.append({"family":"FWD_XALT_004","pressure":"SELL",
                                    "event_local_ns":now,"event_wall_ms":int(time.time()*1000),
                                    "bybit_burst":pending["bybit"],"binance_burst":bc.__dict__,
                                    "entry":None,"exit":None})
                    last_episode=now;pending=None
            else: pending=None
    return records

async def main_async():
    cfg=load_config(CONFIG)  # hard fail if UNFROZEN
    q=asyncio.Queue();stop=asyncio.Event()
    health={"bybit":{},"binance":{},"mexc":{}}
    tasks=[asyncio.create_task(bybit_stream(stop,q,health["bybit"])),
           asyncio.create_task(binance_stream(stop,q,health["binance"])),
           asyncio.create_task(mexc_sol(stop,q,health["mexc"]))]
    coord=asyncio.create_task(coordinator(q,stop,cfg))
    await asyncio.sleep(SECONDS);stop.set()
    await asyncio.gather(*tasks,return_exceptions=True)
    records=await coord
    result={"status":"FWD_XALT_004_FORWARD_OBSERVATION","seconds":SECONDS,
            "config_version":cfg["version"],"health":health,
            "record_count":len(records),"records":records,
            "entry_delay_ms":ENTRY_DELAY_MS,"horizon_ms":HORIZON_MS,
            "fee_bps":FEE_BPS,"live_trading":False}
    out=Path("research/liquidation_cascade/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"licp_fwd_xalt_004_observation_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True))
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":asyncio.run(main_async())

#!/usr/bin/env python3
"""LICP-FWD-XALT-004 locked forward transfer observer.

Research/shadow only. Refuses UNFROZEN trigger config. Persistent state survives
process restarts; due entry/exit points crossed while offline are marked missing
rather than backfilled.
"""
import argparse, asyncio, collections, json, time
from pathlib import Path
import websockets

from research.liquidation_cascade.licp001_trigger_engine_v01 import load_config, btc_ignition, aggregate_burst
from research.liquidation_cascade.licp_fwd_xalt_004_state_v01 import (
    ENTRY_DELAY_MS,HORIZON_MS,STALE_MS,COOLDOWN_MS,FEE_BPS,
    make_record,add_episode,apply_bbo,load_records,save_records,
    mark_restart_gaps,state_sha256,evaluate_forward
)

CONFIG="research/liquidation_cascade/LICP_001_TRIGGER_CONFIG_V0_1.json"
BYBIT="wss://stream.bybit.com/v5/public/linear"
BINANCE="wss://fstream.binance.com/market/stream"
MEXC="wss://contract.mexc.com/edge"
DEFAULT_SECONDS=20_700
DEFAULT_STATE="research/liquidation_cascade/runtime_data/licp_fwd_xalt_004_state_v01.json"
DEFAULT_RECEIPT="research/liquidation_cascade/receipts/licp_fwd_xalt_004_observation_v01.json"

def wall_ms():return int(time.time()*1000)

def bybit_event(r,local_ns):
    pressure="SELL" if r["S"]=="Buy" else ("BUY" if r["S"]=="Sell" else None)
    if pressure is None:raise ValueError("BAD_BYBIT_SIDE")
    return {"source":"bybit","symbol":r["s"],"venue_ts":int(r["T"]),
            "local_ns":local_ns,"pressure":pressure,
            "notional":float(r["v"])*float(r["p"])}

def binance_event(o,local_ns):
    pressure=o["S"]
    if pressure not in ("BUY","SELL"):raise ValueError("BAD_BINANCE_SIDE")
    z=float(o.get("z",0) or 0);ap=float(o.get("ap",0) or 0)
    notional=z*ap if z>0 and ap>0 else float(o.get("q",0) or 0)*float(o.get("p",0) or 0)
    return {"source":"binance","symbol":o["s"],"venue_ts":int(o["T"]),
            "local_ns":local_ns,"pressure":pressure,"notional":notional}

async def bybit_stream(stop,q,health):
    health.update({"ack":False,"events":0,"malformed":0,"connects":0,"disconnects":0})
    backoff=1
    while not stop.is_set():
        try:
            async with websockets.connect(BYBIT,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
                health["connects"]+=1;backoff=1
                await ws.send(json.dumps({"op":"subscribe","args":["allLiquidation.BTCUSDT"]}))
                while not stop.is_set():
                    try:raw=await asyncio.wait_for(ws.recv(),30)
                    except asyncio.TimeoutError:continue
                    now=time.monotonic_ns();m=json.loads(raw)
                    if m.get("op")=="subscribe" and m.get("success") is True:
                        health["ack"]=True;continue
                    if m.get("topic")!="allLiquidation.BTCUSDT":continue
                    rows=m.get("data")
                    if not isinstance(rows,list):health["malformed"]+=1;continue
                    for r in rows:
                        try:
                            e=bybit_event(r,now);health["events"]+=1;await q.put(("liq",e))
                        except Exception:health["malformed"]+=1
        except Exception:
            health["disconnects"]+=1
            if stop.is_set():break
            await asyncio.sleep(backoff);backoff=min(backoff*2,30)

async def binance_stream(stop,q,health):
    health.update({"ack":False,"events":0,"malformed":0,"connects":0,"disconnects":0})
    backoff=1
    while not stop.is_set():
        try:
            async with websockets.connect(BINANCE,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
                health["connects"]+=1;backoff=1
                await ws.send(json.dumps({"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1}))
                while not stop.is_set():
                    try:raw=await asyncio.wait_for(ws.recv(),30)
                    except asyncio.TimeoutError:continue
                    now=time.monotonic_ns();m=json.loads(raw)
                    if m.get("id")==1 and m.get("result") is None:
                        health["ack"]=True;continue
                    d=m.get("data",m)
                    if d.get("e")!="forceOrder":continue
                    try:
                        e=binance_event(d["o"],now)
                        if e["symbol"]=="BTCUSDT":
                            health["events"]+=1;await q.put(("liq",e))
                    except Exception:health["malformed"]+=1
        except Exception:
            health["disconnects"]+=1
            if stop.is_set():break
            await asyncio.sleep(backoff);backoff=min(backoff*2,30)

async def mexc_sol(stop,q,health):
    health.update({"ack":False,"updates":0,"crossed":0,"version_regressions":0,
                   "connects":0,"disconnects":0})
    backoff=1
    while not stop.is_set():
        bids={};asks={};last_v=None
        try:
            async with websockets.connect(MEXC,ping_interval=None,max_size=8_000_000) as ws:
                health["connects"]+=1;backoff=1
                await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":"SOL_USDT"}}))
                next_ping=time.monotonic()+10
                while not stop.is_set():
                    timeout=max(.1,min(2,next_ping-time.monotonic()))
                    try:raw=await asyncio.wait_for(ws.recv(),timeout)
                    except asyncio.TimeoutError:raw=None
                    if time.monotonic()>=next_ping:
                        await ws.send(json.dumps({"method":"ping"}));next_ping=time.monotonic()+10
                    if not raw:continue
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
                        await q.put(("bbo",{"local_ns":now,"wall_ms":wall_ms(),"bid":bid,"ask":ask}))
        except Exception:
            health["disconnects"]+=1
            if stop.is_set():break
            await asyncio.sleep(backoff);backoff=min(backoff*2,30)

async def coordinator(q,stop,cfg,state_path):
    liq=collections.deque()
    pending=None
    records=load_records(state_path)
    start_wall=wall_ms()
    if mark_restart_gaps(records,start_wall):save_records(state_path,records)
    last_episode_wall=max((int(r["event_wall_ms"]) for r in records),default=None)

    def persist():save_records(state_path,records)

    while not stop.is_set() or not q.empty():
        try:kind,x=await asyncio.wait_for(q.get(),.2)
        except asyncio.TimeoutError:continue
        now_ns=time.monotonic_ns();now_wall=wall_ms()

        if kind=="bbo":
            if apply_bbo(records,x,now_ns):persist()
            continue

        liq.append(x)
        while liq and x["venue_ts"]-liq[0]["venue_ts"]>120_000:liq.popleft()
        events=list(liq)

        if x["source"]=="bybit":
            if last_episode_wall is not None and now_wall-last_episode_wall<COOLDOWN_MS:
                continue
            ok,b=btc_ignition(events,x["venue_ts"],cfg)
            if ok and b.pressure=="SELL":
                pending={"pressure":"SELL","bybit":b.__dict__,"local_ns":now_ns}
                bc=aggregate_burst(events,"binance","BTCUSDT",x["venue_ts"],
                                   cfg["binance_confirmation"]["window_ms"])
                if (bc.pressure=="SELL" and
                    bc.total_notional>=float(cfg["binance_confirmation"]["notional_threshold"])):
                    rec=make_record("SELL",b.__dict__,bc.__dict__,now_wall)
                    if add_episode(records,rec):
                        persist();last_episode_wall=now_wall
                    pending=None

        elif x["source"]=="binance" and pending:
            age_s=(now_ns-pending["local_ns"])/1e9
            if age_s<=5:
                bc=aggregate_burst(events,"binance","BTCUSDT",x["venue_ts"],
                                   cfg["binance_confirmation"]["window_ms"])
                if (bc.pressure=="SELL" and
                    bc.total_notional>=float(cfg["binance_confirmation"]["notional_threshold"])):
                    rec=make_record("SELL",pending["bybit"],bc.__dict__,now_wall)
                    if add_episode(records,rec):
                        persist();last_episode_wall=now_wall
                    pending=None
            else:
                pending=None
    persist()
    return records

async def run(seconds,state_path,receipt_path):
    cfg=load_config(CONFIG)  # fail closed BEFORE network/outcomes
    q=asyncio.Queue();stop=asyncio.Event()
    health={"bybit":{},"binance":{},"mexc":{}}
    tasks=[
      asyncio.create_task(bybit_stream(stop,q,health["bybit"])),
      asyncio.create_task(binance_stream(stop,q,health["binance"])),
      asyncio.create_task(mexc_sol(stop,q,health["mexc"]))
    ]
    coord=asyncio.create_task(coordinator(q,stop,cfg,state_path))
    await asyncio.sleep(seconds);stop.set()
    await asyncio.gather(*tasks,return_exceptions=True)
    records=await coord
    result={
      "status":"FWD_XALT_004_FORWARD_OBSERVATION",
      "seconds":seconds,"config_version":cfg["version"],"health":health,
      "record_count":len(records),"records":records,
      "entry_delay_ms":ENTRY_DELAY_MS,"horizon_ms":HORIZON_MS,
      "stale_ms":STALE_MS,"fee_bps":FEE_BPS,
      "evidence":evaluate_forward(records,wall_ms()),
      "state_sha256":state_sha256(state_path),
      "persistent_state":True,"live_trading":False
    }
    p=Path(receipt_path);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps(result,indent=2,sort_keys=True))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=int,default=DEFAULT_SECONDS)
    ap.add_argument("--state",default=DEFAULT_STATE)
    ap.add_argument("--receipt",default=DEFAULT_RECEIPT)
    a=ap.parse_args()
    if not (60<=a.seconds<=20_700):raise SystemExit("SECONDS_OUT_OF_BOUNDS")
    asyncio.run(run(a.seconds,a.state,a.receipt))

if __name__=="__main__":main()

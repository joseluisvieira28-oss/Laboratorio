#!/usr/bin/env python3
import asyncio, collections, json, time, urllib.parse, urllib.request
from pathlib import Path
import websockets

from research.liquidation_cascade.licp001_trigger_engine_v01 import (
    load_config, btc_ignition, aggregate_burst
)
from research.liquidation_cascade.licp001_execution_math_v01 import executable_returns

CONFIG="research/liquidation_cascade/LICP_001_TRIGGER_CONFIG_V0_1.json"
SECONDS=600
STALE_MS=1000
COOLDOWN_NS=120*1_000_000_000
BINANCE_WS="wss://fstream.binance.com/market/stream"
BYBIT_WS="wss://stream.bybit.com/v5/public/linear"
MEXC_WS="wss://contract.mexc.com/edge"
OI_URL="https://api.hyperliquid.xyz/info"

def binance_notional(o):
    z=float(o.get("z",0) or 0); ap=float(o.get("ap",0) or 0)
    if z>0 and ap>0:return z*ap
    return float(o.get("q",0) or 0)*float(o.get("p",0) or 0)

def bybit_event(r,local_ns):
    pos=r["S"]
    pressure="SELL" if pos=="Buy" else ("BUY" if pos=="Sell" else None)
    if pressure is None:raise ValueError("bad_bybit_side")
    return {"source":"bybit","symbol":r["s"],"venue_ts":int(r["T"]),"local_ns":local_ns,
            "venue_side":pos,"pressure":pressure,"notional":float(r["v"])*float(r["p"])}

def binance_event(o,local_ns):
    pressure=o["S"]
    if pressure not in ("BUY","SELL"):raise ValueError("bad_binance_side")
    return {"source":"binance","symbol":o["s"],"venue_ts":int(o["T"]),"local_ns":local_ns,
            "venue_side":pressure,"pressure":pressure,"notional":binance_notional(o)}

def calc_returns(entry,future,pressure):
    return executable_returns(entry["bid"],entry["ask"],future["bid"],future["ask"],pressure)

def fetch_btc_oi():
    body=json.dumps({"type":"metaAndAssetCtxs"}).encode("utf-8")
    req=urllib.request.Request(
        OI_URL,data=body,
        headers={"User-Agent":"Crypto-Lab-LICP-Forward/0.1","Content-Type":"application/json"},
        method="POST")
    with urllib.request.urlopen(req,timeout=10) as r:
        meta,ctxs=json.loads(r.read().decode())
    for i,u in enumerate(meta["universe"]):
        if u.get("name")=="BTC" and i<len(ctxs):
            oi=ctxs[i].get("openInterest")
            if oi is None:break
            return {"value":float(oi),"venue_ts":int(time.time()*1000),
                    "local_ns":time.monotonic_ns(),"source":"hyperliquid_metaAndAssetCtxs"}
    raise RuntimeError("BTC_OI_NOT_FOUND")

async def binance_stream(stop,q,health):
    health.update({"ack":False,"events":0,"malformed":0})
    async with websockets.connect(BINANCE_WS,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1}))
        while not stop.is_set():
            try:raw=await asyncio.wait_for(ws.recv(),2)
            except asyncio.TimeoutError:continue
            now=time.monotonic_ns();m=json.loads(raw)
            if m.get("id")==1 and m.get("result") is None:
                health["ack"]=True;continue
            d=m.get("data",m)
            if d.get("e")!="forceOrder":continue
            try:
                e=binance_event(d["o"],now)
                if e["symbol"] in ("BTCUSDT","ETHUSDT","SOLUSDT"):
                    health["events"]+=1;await q.put(("liq",e))
            except Exception:health["malformed"]+=1

async def bybit_stream(stop,q,health):
    health.update({"ack":False,"events":0,"malformed":0})
    async with websockets.connect(BYBIT_WS,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"op":"subscribe","args":[
          "allLiquidation.BTCUSDT","allLiquidation.ETHUSDT","allLiquidation.SOLUSDT"]}))
        while not stop.is_set():
            try:raw=await asyncio.wait_for(ws.recv(),2)
            except asyncio.TimeoutError:continue
            now=time.monotonic_ns();m=json.loads(raw)
            if m.get("op")=="subscribe" and m.get("success") is True:
                health["ack"]=True;continue
            if not m.get("topic","").startswith("allLiquidation."):continue
            rows=m.get("data")
            if not isinstance(rows,list):health["malformed"]+=1;continue
            for r in rows:
                try:
                    e=bybit_event(r,now)
                    health["events"]+=1;await q.put(("liq",e))
                except Exception:health["malformed"]+=1

async def mexc_stream(sym,stop,q,health):
    health[sym]={"ack":False,"updates":0,"crossed":0,"version_regressions":0}
    bids={};asks={};last_v=None
    async with websockets.connect(MEXC_WS,ping_interval=None,max_size=8_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":sym}}))
        next_ping=time.monotonic()+10
        while not stop.is_set():
            timeout=max(.1,min(2,next_ping-time.monotonic()))
            try:raw=await asyncio.wait_for(ws.recv(),timeout)
            except asyncio.TimeoutError:
                if time.monotonic()>=next_ping:
                    await ws.send(json.dumps({"method":"ping"}));next_ping=time.monotonic()+10
                continue
            if time.monotonic()>=next_ping:
                await ws.send(json.dumps({"method":"ping"}));next_ping=time.monotonic()+10
            m=json.loads(raw);now=time.monotonic_ns()
            if m.get("channel")=="rs.sub.depth" and m.get("data")=="success":
                health[sym]["ack"]=True;continue
            if m.get("channel")!="push.depth":continue
            d=m.get("data") or {};v=d.get("version")
            if v is not None:
                v=int(v)
                if last_v is not None and v<=last_v:health[sym]["version_regressions"]+=1
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
                if bid>=ask:health[sym]["crossed"]+=1
                health[sym]["updates"]+=1
                await q.put(("bbo",{"symbol":sym,"local_ns":now,"bid":bid,"ask":ask}))

async def oi_poller(stop,q,health):
    health.update({"rounds":0,"errors":0,"source":"hyperliquid_metaAndAssetCtxs"})
    while not stop.is_set():
        try:
            x=await asyncio.to_thread(fetch_btc_oi)
            await q.put(("oi",x))
        except Exception:health["errors"]+=1
        health["rounds"]+=1
        try:await asyncio.wait_for(stop.wait(),5)
        except asyncio.TimeoutError:pass

def fresh_bbo(latest,sym,now):
    x=latest.get(sym)
    if not x:return None
    if (now-x["local_ns"])/1e6>STALE_MS:return None
    if x["bid"]>=x["ask"]:return None
    return dict(x)

async def coordinator(q,stop,cfg):
    liq=collections.deque()
    oi=collections.deque()
    latest={}
    pending_ignition=None
    episode=None
    last_episode_ns=None
    records=[]
    horizons=tuple(cfg["outcome_horizons_ms"])

    def trim(now_ms):
        while liq and liq[0]["venue_ts"]<now_ms-120_000:liq.popleft()

    def start_record(family,asset,pressure,now_ns,meta):
        targets={}
        for sym in cfg["mexc_targets"]:
            b=fresh_bbo(latest,sym,now_ns)
            if b:
                targets[sym]={"entry":b,"outcomes":{}}
        if not targets:return None
        rec={"family":family,"propagation_asset":asset,"pressure":pressure,
             "event_local_ns":now_ns,"meta":meta,"targets":targets}
        records.append(rec);return rec

    while not stop.is_set() or not q.empty():
        try:kind,x=await asyncio.wait_for(q.get(),.2)
        except asyncio.TimeoutError:
            continue
        now=time.monotonic_ns()
        if kind=="bbo":
            latest[x["symbol"]]=x
            # resolve due horizons for this target
            for rec in records:
                target=rec["targets"].get(x["symbol"])
                if not target:continue
                elapsed_ms=(x["local_ns"]-rec["event_local_ns"])/1e6
                for h in horizons:
                    key=str(h)
                    if key not in target["outcomes"] and elapsed_ms>=h:
                        target["outcomes"][key]={"bbo":dict(x),**calc_returns(target["entry"],x,rec["pressure"])}
        elif kind=="oi":
            oi.append(x)
            while oi and now-oi[0]["local_ns"]>120*1_000_000_000:oi.popleft()
        elif kind=="liq":
            liq.append(x);trim(x["venue_ts"])
            events=list(liq)

            if x["source"]=="bybit" and x["symbol"]=="BTCUSDT":
                if last_episode_ns is None or now-last_episode_ns>=COOLDOWN_NS:
                    ok,b=btc_ignition(events,x["venue_ts"],cfg)
                    if ok:
                        pending_ignition={"pressure":b.pressure,"ignition_venue_ts":x["venue_ts"],
                                          "ignition_local_ns":now,"bybit_burst":b.__dict__}
                        # allow already-observed Binance burst to confirm immediately
                        bc=aggregate_burst(events,"binance","BTCUSDT",x["venue_ts"],cfg["binance_confirmation"]["window_ms"])
                        if (bc.total_notional>=cfg["binance_confirmation"]["notional_threshold"] and bc.pressure==b.pressure):
                            episode={"pressure":b.pressure,"confirmed_local_ns":now,
                                     "ignition":pending_ignition,"binance_burst":bc.__dict__}
                            last_episode_ns=now
                            start_record("BTC_CONFIRMED","BTCUSDT",b.pressure,now,episode)
                            pending_ignition=None

            if pending_ignition and x["source"]=="binance" and x["symbol"]=="BTCUSDT":
                age=(now-pending_ignition["ignition_local_ns"])/1e9
                if age<=5:
                    bc=aggregate_burst(events,"binance","BTCUSDT",x["venue_ts"],cfg["binance_confirmation"]["window_ms"])
                    if (bc.total_notional>=cfg["binance_confirmation"]["notional_threshold"] and
                        bc.pressure==pending_ignition["pressure"]):
                        episode={"pressure":pending_ignition["pressure"],"confirmed_local_ns":now,
                                 "ignition":pending_ignition,"binance_burst":bc.__dict__}
                        last_episode_ns=now
                        start_record("BTC_CONFIRMED","BTCUSDT",episode["pressure"],now,episode)
                        pending_ignition=None
                else:
                    pending_ignition=None

            if episode and x["source"]=="bybit" and x["symbol"] in ("ETHUSDT","SOLUSDT"):
                age=(now-episode["confirmed_local_ns"])/1e9
                if 0<=age<=30:
                    c=cfg["alt_propagation"]
                    b=aggregate_burst(events,"bybit",x["symbol"],x["venue_ts"],c["burst_window_ms"])
                    thr=c["notional_thresholds"][x["symbol"]]
                    if b.total_notional>=thr and b.pressure==episode["pressure"]:
                        if not any(r["family"]=="ALT_SECOND_WAVE" and r["propagation_asset"]==x["symbol"]
                                   and r["event_local_ns"]>=episode["confirmed_local_ns"] for r in records):
                            start_record("ALT_SECOND_WAVE",x["symbol"],episode["pressure"],now,
                                         {"btc_episode":episode,"alt_burst":b.__dict__})
                elif age>30:
                    episode=None

    # attach causal OI context nearest at/before each record
    oi_rows=list(oi)
    for rec in records:
        eligible=[z for z in oi_rows if z["local_ns"]<=rec["event_local_ns"]]
        if eligible:rec["oi_at_event"]=eligible[-1]
    return records

async def main_async():
    cfg=load_config(CONFIG)
    q=asyncio.Queue();stop=asyncio.Event()
    health={"binance":{},"bybit":{},"mexc":{},"oi":{}}
    tasks=[
      asyncio.create_task(binance_stream(stop,q,health["binance"])),
      asyncio.create_task(bybit_stream(stop,q,health["bybit"])),
      asyncio.create_task(oi_poller(stop,q,health["oi"])),
      *[asyncio.create_task(mexc_stream(s,stop,q,health["mexc"])) for s in cfg["mexc_targets"]]
    ]
    coord=asyncio.create_task(coordinator(q,stop,cfg))
    await asyncio.sleep(SECONDS);stop.set()
    await asyncio.gather(*tasks,return_exceptions=True)
    records=await coord
    completed=[]
    for r in records:
        rr=dict(r)
        for sym,t in rr["targets"].items():
            t["complete_horizons"]=len(t["outcomes"])
        completed.append(rr)
    result={"status":"FORWARD_OBSERVATION","seconds":SECONDS,"config_version":cfg["version"],
            "health":health,"records":completed,"record_count":len(completed),
            "live_trading":False}
    result["evidence_state"]="FORWARD_INSUFFICIENT"
    out=Path("research/liquidation_cascade/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"licp001_forward_observation_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":asyncio.run(main_async())

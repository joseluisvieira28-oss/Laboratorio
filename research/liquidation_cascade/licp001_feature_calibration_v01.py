#!/usr/bin/env python3
import asyncio, bisect, json, statistics, time, urllib.parse, urllib.request
from collections import defaultdict
from pathlib import Path
import websockets

SECONDS=300
SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT")
BINANCE_WS="wss://fstream.binance.com/market/stream"
BYBIT_WS="wss://stream.bybit.com/v5/public/linear"
OI_URL="https://fapi.binance.com/fapi/v1/openInterest"
PCTS=(.50,.75,.90,.95,.99)


def qtile(xs,p):
    if not xs:return None
    s=sorted(xs)
    return s[int((len(s)-1)*p)]


def dist(xs):
    if not xs:return {"n":0}
    return {"n":len(xs),"mean":statistics.fmean(xs),"median":statistics.median(xs),
            **{f"p{int(p*100)}":qtile(xs,p) for p in PCTS},"max":max(xs)}


def floor_bin(ts_ms,width):
    return (int(ts_ms)//width)*width


def event_notional_binance(o):
    z=float(o.get("z",0) or 0); ap=float(o.get("ap",0) or 0)
    if z>0 and ap>0:return z*ap
    q=float(o.get("q",0) or 0); p=float(o.get("p",0) or 0)
    return q*p


async def binance_collector(stop,events,health):
    health.update({"subscription_ack":False,"messages":0,"events":0,"malformed":0})
    async with websockets.connect(BINANCE_WS,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"method":"SUBSCRIBE","params":["!forceOrder@arr"],"id":1}))
        while not stop.is_set():
            try:raw=await asyncio.wait_for(ws.recv(),2)
            except asyncio.TimeoutError:continue
            health["messages"]+=1
            m=json.loads(raw)
            if m.get("id")==1 and m.get("result") is None:
                health["subscription_ack"]=True;continue
            d=m.get("data",m)
            if d.get("e")!="forceOrder":continue
            try:
                o=d["o"];sym=o["s"]
                if sym not in SYMBOLS:continue
                side=o["S"]
                if side not in ("BUY","SELL"):raise ValueError("bad_side")
                ev={"source":"binance","symbol":sym,"venue_ts":int(o["T"]),
                    "local_ns":time.monotonic_ns(),"venue_side":side,
                    "pressure":side,"notional":event_notional_binance(o)}
                events.append(ev);health["events"]+=1
            except Exception:
                health["malformed"]+=1


async def bybit_collector(stop,events,health):
    health.update({"subscription_ack":False,"messages":0,"events":0,"malformed":0})
    async with websockets.connect(BYBIT_WS,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
        await ws.send(json.dumps({"op":"subscribe","args":[f"allLiquidation.{s}" for s in SYMBOLS]}))
        while not stop.is_set():
            try:raw=await asyncio.wait_for(ws.recv(),2)
            except asyncio.TimeoutError:continue
            health["messages"]+=1
            m=json.loads(raw)
            if m.get("op")=="subscribe" and m.get("success") is True:
                health["subscription_ack"]=True;continue
            if not m.get("topic","").startswith("allLiquidation."):continue
            rows=m.get("data")
            if not isinstance(rows,list):
                health["malformed"]+=1;continue
            for r in rows:
                try:
                    sym=r["s"];pos=r["S"]
                    if sym not in SYMBOLS:continue
                    if pos not in ("Buy","Sell"):raise ValueError("bad_position_side")
                    pressure="SELL" if pos=="Buy" else "BUY"
                    ev={"source":"bybit","symbol":sym,"venue_ts":int(r["T"]),
                        "local_ns":time.monotonic_ns(),"venue_side":pos,
                        "pressure":pressure,"notional":float(r["v"])*float(r["p"])}
                    events.append(ev);health["events"]+=1
                except Exception:
                    health["malformed"]+=1


def fetch_oi(symbol):
    url=OI_URL+"?"+urllib.parse.urlencode({"symbol":symbol})
    req=urllib.request.Request(url,headers={"User-Agent":"Crypto-Lab-LICP/0.1"})
    with urllib.request.urlopen(req,timeout=10) as r:
        j=json.loads(r.read().decode())
    return {"symbol":symbol,"openInterest":float(j["openInterest"]),
            "venue_ts":int(j["time"]),"local_ns":time.monotonic_ns()}


async def oi_poller(stop,snaps,health):
    health.update({"poll_rounds":0,"errors":0})
    while not stop.is_set():
        for s in SYMBOLS:
            try:snaps[s].append(await asyncio.to_thread(fetch_oi,s))
            except Exception:health["errors"]+=1
        health["poll_rounds"]+=1
        try:await asyncio.wait_for(stop.wait(),timeout=5)
        except asyncio.TimeoutError:pass


def burst_report(events):
    out={}
    for source in ("binance","bybit"):
        out[source]={}
        for sym in SYMBOLS:
            es=sorted([e for e in events if e["source"]==source and e["symbol"]==sym],key=lambda x:x["venue_ts"])
            rec={"event_count":len(es),"notional":dist([e["notional"] for e in es])}
            rec["forced_sell_notional"]=sum(e["notional"] for e in es if e["pressure"]=="SELL")
            rec["forced_buy_notional"]=sum(e["notional"] for e in es if e["pressure"]=="BUY")
            total=rec["forced_sell_notional"]+rec["forced_buy_notional"]
            rec["side_concentration"]=abs(rec["forced_sell_notional"]-rec["forced_buy_notional"])/total if total else None
            rec["bursts"]={}
            for w in (1000,5000):
                bins=defaultdict(lambda:{"notional":0.0,"count":0,"sell":0.0,"buy":0.0})
                for e in es:
                    b=bins[floor_bin(e["venue_ts"],w)]
                    b["notional"]+=e["notional"];b["count"]+=1;b[e["pressure"].lower()]+=e["notional"]
                vals=list(bins.values())
                rec["bursts"][str(w)]={
                    "active_bins":len(vals),
                    "notional":dist([x["notional"] for x in vals]),
                    "count":dist([x["count"] for x in vals]),
                    "side_concentration":dist([
                        abs(x["sell"]-x["buy"])/(x["sell"]+x["buy"])
                        for x in vals if x["sell"]+x["buy"]>0])
                }
            out[source][sym]=rec
    return out


def cross_venue(events):
    out={}
    for sym in SYMBOLS:
        a=sorted(e["venue_ts"] for e in events if e["source"]=="binance" and e["symbol"]==sym)
        b=sorted(e["venue_ts"] for e in events if e["source"]=="bybit" and e["symbol"]==sym)
        rec={}
        for w in (1000,5000):
            n=0
            for t in a:
                i=bisect.bisect_left(b,t-w)
                if i<len(b) and b[i]<=t+w:n+=1
            rec[str(w)]={"binance_events_with_bybit_match":n,"binance_events":len(a),"bybit_events":len(b)}
        out[sym]=rec
    return out


def oi_report(snaps):
    out={}
    for s,rows in snaps.items():
        vals=[x["openInterest"] for x in rows]
        if not vals:out[s]={"n":0};continue
        peak=vals[0];maxdd=0.0
        for v in vals:
            peak=max(peak,v)
            if peak>0:maxdd=min(maxdd,(v-peak)/peak*100.0)
        out[s]={"n":len(vals),"first":vals[0],"last":vals[-1],
                "first_to_last_pct":(vals[-1]-vals[0])/vals[0]*100.0 if vals[0] else None,
                "max_drawdown_pct":maxdd}
    return out


async def main_async():
    events=[];snaps={s:[] for s in SYMBOLS}
    bh={};yh={};oh={}
    stop=asyncio.Event()
    tasks=[
        asyncio.create_task(binance_collector(stop,events,bh)),
        asyncio.create_task(bybit_collector(stop,events,yh)),
        asyncio.create_task(oi_poller(stop,snaps,oh))
    ]
    await asyncio.sleep(SECONDS);stop.set()
    await asyncio.gather(*tasks,return_exceptions=True)
    result={
      "status":"OUTCOME_BLIND_FEATURE_CALIBRATION",
      "seconds":SECONDS,
      "health":{"binance":bh,"bybit":yh,"oi":oh},
      "total_liquidation_events":len(events),
      "bursts":burst_report(events),
      "cross_venue_confirmation":cross_venue(events),
      "open_interest":oi_report(snaps),
      "mexc_price_outcomes_opened":False,
      "events_sample":events[:20],
    }
    healthy=(bh.get("subscription_ack") and yh.get("subscription_ack")
             and bh.get("malformed",1)==0 and yh.get("malformed",1)==0
             and oh.get("poll_rounds",0)>=20)
    result["decision"]="CALIBRATION_SAMPLE" if healthy and len(events)>=20 else ("CALIBRATION_SPARSE" if healthy else "BLOCKED")
    out=Path("research/liquidation_cascade/receipts");out.mkdir(parents=True,exist_ok=True)
    (out/"licp001_feature_calibration_v01.json").write_text(json.dumps(result,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(result,indent=2,sort_keys=True))

if __name__=="__main__":asyncio.run(main_async())

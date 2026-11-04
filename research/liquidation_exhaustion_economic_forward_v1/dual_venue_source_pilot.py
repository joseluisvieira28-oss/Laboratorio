#!/usr/bin/env python3
"""240s one-shot source-only cross-venue BTC liquidation + quote PILOT.
No forecast, entry, exit, PnL, account, order or authenticated requests.
"""
import argparse
import asyncio
import datetime as dt
import hashlib
import json
import pathlib
import time
from collections import defaultdict
from decimal import Decimal, InvalidOperation

BYBIT_URL = "wss://stream.bybit.com/v5/public/linear"
MEXC_URL = "wss://contract.mexc.com/edge"
DURATION = 240
OUT = pathlib.Path("artifacts/liquidation_exhaustion_economic_forward_v1")
TOPICS = ["allLiquidation.BTCUSDT", "orderbook.50.BTCUSDT", "publicTrade.BTCUSDT"]

def utc_ms():
    return int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)

def positive(x):
    try:
        d=Decimal(str(x))
        if d.is_finite() and d>0:return d
    except (ValueError,TypeError,InvalidOperation):
        pass
    raise ValueError("BAD_POSITIVE_DECIMAL")

def clock_age(received, stamp, max_age=1500):
    if isinstance(stamp, bool):raise ValueError("BAD_TIME")
    try: t=int(stamp)
    except (ValueError,TypeError):raise ValueError("BAD_TIME")
    if t<=0 or t>received+250 or received-t>max_age:
        raise ValueError("STALE_OR_FUTURE_TIMESTAMP")
    return received-t

def new_state(name):
    return dict(venue=name, connected=False, subscription=False, completed=False,
                pings=0, pongs=0, disconnects=0, errors=[],
                topic_counts={}, liquidation_children=0,
                best_bid_ask_samples=0, ticker_fresh_messages=0,
                ticker_quarantine_complete=False, ticker_stale_samples=0,
                book_snapshots=0, book_contiguous_deltas=0,
                bybit_trade_children=0, book_max_lag_ms=None,
                liquidation_max_lag_ms=None, ticker_max_lag_ms=None,
                receive_monotonic_regression=False)

def capture_line(fh, h, venue, received, monotonic, raw):
    obj={"venue":venue,"received_utc_ms":received,
         "received_monotonic_ns":monotonic,"raw":raw}
    encoded=json.dumps(obj,separators=(",",":"),ensure_ascii=False)+"\n"
    fh.write(encoded);h.update(encoded.encode())
    return obj

def handle_bybit(msg, received, state, memory):
    if not isinstance(msg, dict):raise ValueError("BYBIT_NOT_DICT")
    if msg.get("op")=="subscribe":
        if msg.get("success") is not True:raise ValueError("SUBSCRIBE_FAIL")
        state["subscription"]=True
        return
    if msg.get("op")=="pong" or msg.get("ret_msg")=="pong":
        state["pongs"]+=1
        return
    topic=msg.get("topic")
    if topic not in TOPICS:
        return
    state["topic_counts"][topic]=state["topic_counts"].get(topic,0)+1
    data=msg.get("data")
    if topic.startswith("orderbook."):
        if not isinstance(data,dict) or data.get("s")!="BTCUSDT":
            raise ValueError("BAD_BOOK_SCHEMA")
        u=data.get("u")
        if type(u)!=int:raise ValueError("BAD_BOOK_UPDATE_ID")
        k=msg.get("type")
        if k not in ("snapshot","delta"):raise ValueError("BAD_BOOK_TYPE")
        lag=clock_age(received,msg.get("ts"),1500)
        state["book_max_lag_ms"]=max(lag,state["book_max_lag_ms"] or 0)
        if k=="snapshot":
            state["book_snapshots"]+=1
            memory["last_u"]=u
        else:
            if memory.get("last_u") is None or u!=memory["last_u"]+1:
                raise ValueError("BOOK_GAP_OR_NO_SNAPSHOT")
            memory["last_u"]=u;state["book_contiguous_deltas"]+=1
        # Forward source pilot does NOT interpret book snapshots as future outcomes.
    elif topic.startswith("publicTrade."):
        if not isinstance(data,list):raise ValueError("BAD_TRADE_LIST")
        for x in data:
            if not isinstance(x,dict) or x.get("s")!="BTCUSDT" or x.get("S") not in ("Buy","Sell"):
                raise ValueError("BAD_TRADE_CHILD")
            positive(x.get("p"));positive(x.get("v"))
            clock_age(received,x.get("T"),1500)
            state["bybit_trade_children"]+=1
    else:
        if not isinstance(data,list):raise ValueError("BAD_LIQ_LIST")
        for x in data:
            if not isinstance(x,dict) or x.get("s")!="BTCUSDT" or x.get("S") not in ("Buy","Sell"):
                raise ValueError("BAD_LIQ_CHILD")
            positive(x.get("p"));positive(x.get("v"))
            lag=clock_age(received,x.get("T"),1500)
            state["liquidation_children"]+=1
            state["liquidation_max_lag_ms"]=max(lag,state["liquidation_max_lag_ms"] or 0)

def handle_mexc(msg, received, state, memory):
    if not isinstance(msg,dict):raise ValueError("MEXC_NOT_DICT")
    channel=msg.get("channel","")
    if channel=="rs.error":raise ValueError("MEXC_REJECTED_SUBSCRIPTION")
    if channel.startswith("rs.sub.ticker"):
        if msg.get("data")=="success":state["subscription"]=True
        return
    if channel=="pong":
        state["pongs"]+=1;return
    if channel!="push.ticker":return
    data=msg.get("data")
    if not isinstance(data,dict) or (msg.get("symbol") or data.get("symbol"))!="BTC_USDT":
        raise ValueError("MEXC_SYMBOL_SCHEMA")
    bid=positive(data.get("bid1"));ask=positive(data.get("ask1"))
    if bid>=ask:raise ValueError("MEXC_CROSSED_OR_EQUAL_BBO")
    # Initial delayed ticker messages are explicitly quarantined, never backfilled.
    try:lag=clock_age(received,msg.get("ts"),1500)
    except ValueError:
        state["ticker_stale_samples"]+=1
        memory["consecutive_valid"]=0
        return
    state["ticker_fresh_messages"]+=1
    state["ticker_max_lag_ms"]=max(lag,state["ticker_max_lag_ms"] or 0)
    memory["consecutive_valid"]+=1
    if memory["consecutive_valid"]>=3:state["ticker_quarantine_complete"]=True
    if state["ticker_quarantine_complete"]:
        state["best_bid_ask_samples"]+=1

async def source_task(venue,url,subs,started,fh,digest):
    import websockets
    st=new_state(venue)
    memory={} if venue=="BYBIT" else {"consecutive_valid":0}
    try:
        async with websockets.connect(url,open_timeout=18,close_timeout=4,
                                      ping_interval=None,max_size=12*1024*1024) as ws:
            st["connected"]=True
            for sub in subs:
                await ws.send(json.dumps(sub,separators=(",",":")))
            next_ping=time.monotonic()
            last_mono=None
            while time.monotonic()-started<DURATION:
                now=time.monotonic()
                if now>=next_ping:
                    await ws.send(json.dumps({"op":"ping"} if venue=="BYBIT" else {"method":"ping"}))
                    st["pings"]+=1;next_ping=now+15
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=0.8)
                except asyncio.TimeoutError:continue
                mono=time.monotonic_ns()
                recv=utc_ms()
                if not isinstance(raw,str):raise ValueError("BINARY_FRAME_UNEXPECTED")
                capture_line(fh,digest,venue,recv,mono,raw)
                if last_mono is not None and mono<last_mono:
                    st["receive_monotonic_regression"]=True
                    raise ValueError("MONOTONIC_RECEIVE_REGRESSION")
                last_mono=mono
                try:
                    obj=json.loads(raw)
                    if venue=="BYBIT":handle_bybit(obj,recv,st,memory)
                    else:handle_mexc(obj,recv,st,memory)
                except (ValueError,KeyError,TypeError,InvalidOperation) as ex:
                    if len(st["errors"])<30:st["errors"].append(type(ex).__name__+":"+str(ex)[:130])
            st["completed"]=True
    except Exception as ex:
        st["disconnects"]+=1
        st["errors"].append("TRANSPORT_"+type(ex).__name__+":"+str(ex)[:140])
    return st

def source_verdict(b,m):
    if b["disconnects"] or m["disconnects"] or b["errors"] or m["errors"]:
        return "SOURCE_BLOCKED"
    if not b["completed"] or not m["completed"] or not b["subscription"] or not m["subscription"]:
        return "SOURCE_BLOCKED"
    if b["book_snapshots"]==0 or b["book_contiguous_deltas"]==0 or b["bybit_trade_children"]==0:
        return "SOURCE_BLOCKED"
    if not m["ticker_quarantine_complete"] or m["best_bid_ask_samples"]<20:
        return "MEXC_EXECUTABLE_QUOTE_SOURCE_BLOCKED"
    if b["liquidation_children"]==0:
        return "SOURCE_INSUFFICIENT_POSITIVE_EVENTS"
    return "DUAL_VENUE_SOURCE_WINDOW_PASS_LIMITED"

async def collect():
    OUT.mkdir(parents=True,exist_ok=True)
    digest=hashlib.sha256()
    started=time.monotonic()
    rawfile=OUT/"pilot_raw_public_frames.ndjson"
    with rawfile.open("w",encoding="utf-8") as fh:
        results=await asyncio.gather(
           source_task("BYBIT",BYBIT_URL,[{"op":"subscribe","args":TOPICS}],started,fh,digest),
           source_task("MEXC",MEXC_URL,[{"method":"sub.ticker","param":{"symbol":"BTC_USDT"}}],started,fh,digest))
    b,m=results
    evidence={
      "study":"LIQUIDATION_EXHAUSTION_ECONOMIC_FORWARD_V1_SOURCE_PILOT",
      "frozen_protocol_commit":"88e7632c77c2d0fccc856d59d621caaf5f590658",
      "duration_seconds":DURATION,"source":"public_bybit_linear_plus_mexc_futures",
      "bybit":b,"mexc":m,"pilot_verdict":source_verdict(b,m),
      "raw_sha256":digest.hexdigest(),"raw_file":str(rawfile),
      "economic_signals_generated":0,"outcomes_opened":0,"pnl_calculated":False,
      "trades_placed":0,"account_calls":0,"private_api_calls":0,
      "all_exchange_liquidations_captured_certified":False,
      "source_window_not_market_census":True,
      "manual_execution_route_verified":False,
    }
    (OUT/"pilot_receipt.json").write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    if evidence["pilot_verdict"] in ("SOURCE_BLOCKED","MEXC_EXECUTABLE_QUOTE_SOURCE_BLOCKED"):
        raise SystemExit(2)

def self_test():
    r=new_state("BYBIT");m={}
    recv=1790000000123
    msg={"topic":"allLiquidation.BTCUSDT","data":[{"s":"BTCUSDT","S":"Buy","p":"70000","v":"1","T":recv-42}]}
    handle_bybit(msg,recv,r,m)
    assert r["liquidation_children"]==1
    assert r["liquidation_max_lag_ms"]==42
    s=new_state("MEXC");mem={"consecutive_valid":0}
    for j in range(3):
        handle_mexc({"channel":"push.ticker","symbol":"BTC_USDT","ts":recv,
          "data":{"bid1":"70000","ask1":"70001"}},recv,s,mem)
    assert s["ticker_quarantine_complete"] and s["best_bid_ask_samples"]==1
    handle_mexc({"channel":"push.ticker","symbol":"BTC_USDT","ts":recv-20000,
      "data":{"bid1":"70000","ask1":"70001"}},recv,s,mem)
    assert s["ticker_stale_samples"]==1
    assert source_verdict(r,s)=="SOURCE_BLOCKED"
    try: clock_age(recv,recv+500)
    except ValueError:pass
    else:raise AssertionError("future timestamp accepted")
    print("SYNTHETIC_DUAL_VENUE_SCHEMA_GUARDS_PASS_NOT_MARKET_OR_ECONOMIC_EVIDENCE")

if __name__=="__main__":
    arg=argparse.ArgumentParser();arg.add_argument("--self-test",action="store_true")
    opts=arg.parse_args()
    if opts.self_test:self_test()
    else:asyncio.run(collect())

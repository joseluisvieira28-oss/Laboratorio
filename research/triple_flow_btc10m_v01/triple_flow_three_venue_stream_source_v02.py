#!/usr/bin/env python3
"""ONE 120s BTC 3-venue public WEBSOCKET source gate. NO predictions or outcomes."""
import asyncio,datetime as dt,json,pathlib,time
import websockets
from triple_flow_public_joint_source_v01 import Writer,ms,pos,age,validate_bybit_trade,validate_liquidation

OUT=pathlib.Path("artifacts/triple_flow_btc10m_three_venue_ws_v02")
DURATION=120
URLS={"BYBIT":"wss://stream.bybit.com/v5/public/linear",
      "OKX":"wss://ws.okx.com/ws/v5/public",
      "MEXC":"wss://futures.mexc.com/edge"}
def make(venue):
    return {"venue":venue,"connected":False,"subscription_ack":False,"pings_sent":0,
            "pongs_received":0,"trade_messages":0,"trade_children":0,
            "index_messages":0,"liquidation_messages":0,"liquidation_children":0,
            "long_liquidated":0,"short_liquidated":0,"buy_trade_children":0,
            "sell_trade_children":0,"last_trade_source_age_ms":None,
            "last_index_source_age_ms":None,"max_age_ms":0,"errors":[],
            "min_event_server_ts":None,"max_event_server_ts":None,
            "completed_window":False}
def event_stamp(s,x,limit=2000):
    elapsed=age(s,x,limit)
    return elapsed
def classify_msg(venue,raw,recv,state):
    if raw=="pong":
        state["pongs_received"]+=1
        return
    msg=json.loads(raw)
    if not isinstance(msg,dict):raise ValueError("PUBLIC_WS_NON_OBJECT")
    if venue=="BYBIT":
        if msg.get("op")=="subscribe":
            if msg.get("success") is not True:raise ValueError("BYBIT_SUBSCRIPTION_REJECTED")
            state["subscription_ack"]=True
        if msg.get("op")=="pong" or msg.get("ret_msg")=="pong":
            state["pongs_received"]+=1
        topic=msg.get("topic")
        if topic=="publicTrade.BTCUSDT":
            data=msg.get("data")
            if not isinstance(data,list):raise ValueError("BYBIT_TRADES_NOT_LIST")
            state["trade_messages"]+=1
            for x in data:
                ev=validate_bybit_trade(x,recv)
                state["trade_children"]+=1
                state["buy_trade_children" if ev["side"]=="Buy" else "sell_trade_children"]+=1
                state["last_trade_source_age_ms"]=recv-ev["source_ms"]
                state["max_age_ms"]=max(state["max_age_ms"],recv-ev["source_ms"])
                record_event_ts(state,ev["source_ms"])
        elif topic=="allLiquidation.BTCUSDT":
            data=msg.get("data")
            if not isinstance(data,list):raise ValueError("BYBIT_LIQUIDATIONS_NOT_LIST")
            state["liquidation_messages"]+=1
            for x in data:
                ev=validate_liquidation(x,recv)
                state["liquidation_children"]+=1
                state["long_liquidated" if ev["liquidated_position"]=="LONG" else "short_liquidated"]+=1
                record_event_ts(state,ev["source_ms"])
        return
    if venue=="OKX":
        if msg.get("event")=="subscribe":
            a=msg.get("arg") or {}
            if a.get("channel")=="trades" and a.get("instId")=="BTC-USDT":
                state["subscription_ack"]=True
            return
        if msg.get("event")=="error":raise ValueError("OKX_SUBSCRIBE_ERROR")
        a=msg.get("arg") or {}
        if a.get("channel")!="trades" or a.get("instId")!="BTC-USDT":return
        data=msg.get("data")
        if not isinstance(data,list):raise ValueError("OKX_TRADE_DATA_NOT_LIST")
        state["trade_messages"]+=1
        for x in data:
            if x.get("instId")!="BTC-USDT" or x.get("side") not in ("buy","sell") or not x.get("tradeId"):
                raise ValueError("OKX_TRADE_BAD_SCHEMA")
            pos(x.get("px"));pos(x.get("sz"))
            timestamp=int(x["ts"]);lag=event_stamp(recv,timestamp)
            state["trade_children"]+=1
            state["buy_trade_children" if x["side"]=="buy" else "sell_trade_children"]+=1
            state["last_trade_source_age_ms"]=lag
            state["max_age_ms"]=max(state["max_age_ms"],lag)
            record_event_ts(state,timestamp)
        return
    if venue=="MEXC":
        channel=msg.get("channel","")
        if channel=="rs.error":raise ValueError("MEXC_PUBLIC_SUBSCRIPTION_ERROR")
        if channel in ("rs.sub.deal","rs.sub.index.price") and msg.get("data")=="success":
            state["subscription_ack"]=True
        if channel=="push.deal":
            if msg.get("symbol")!="BTC_USDT":raise ValueError("MEXC_DEAL_BAD_SYMBOL")
            data=msg.get("data")
            if isinstance(data,dict):data=[data]
            if not isinstance(data,list):raise ValueError("MEXC_DEAL_DATA_MALFORMED")
            state["trade_messages"]+=1
            for x in data:
                if x.get("T") not in (1,2):raise ValueError("MEXC_DEAL_NOT_BUY_SELL")
                pos(x.get("p"));pos(x.get("v"))
                timestamp=x.get("t");lag=event_stamp(recv,timestamp)
                state["trade_children"]+=1
                state["buy_trade_children" if x["T"]==1 else "sell_trade_children"]+=1
                state["last_trade_source_age_ms"]=lag
                state["max_age_ms"]=max(state["max_age_ms"],lag)
                record_event_ts(state,timestamp)
        elif channel=="push.index.price":
            data=msg.get("data") or {}
            if (msg.get("symbol") or data.get("symbol"))!="BTC_USDT":
                raise ValueError("MEXC_INDEX_BAD_SYMBOL")
            pos(data.get("price"))
            timestamp=msg.get("ts");lag=event_stamp(recv,timestamp)
            state["index_messages"]+=1
            state["last_index_source_age_ms"]=lag
            state["max_age_ms"]=max(state["max_age_ms"],lag)
            record_event_ts(state,timestamp)
        return
    raise ValueError("UNEXPECTED_VENUE")
def record_event_ts(state,t):
    v=state["min_event_server_ts"];w=state["max_event_server_ts"]
    state["min_event_server_ts"]=t if v is None else min(v,t)
    state["max_event_server_ts"]=t if w is None else max(w,t)
async def stream(venue,end,writer):
    s=make(venue)
    try:
        async with websockets.connect(URLS[venue],open_timeout=18,
               ping_interval=15,ping_timeout=12,max_size=4_000_000) as ws:
            s["connected"]=True
            if venue=="BYBIT":
                await ws.send('{"op":"subscribe","args":["publicTrade.BTCUSDT","allLiquidation.BTCUSDT"]}')
                await ws.send('{"op":"ping"}');s["pings_sent"]+=1
            elif venue=="OKX":
                await ws.send('{"op":"subscribe","args":[{"channel":"trades","instId":"BTC-USDT"}]}')
            else:
                await ws.send('{"method":"sub.deal","param":{"symbol":"BTC_USDT"}}')
                await ws.send('{"method":"sub.index.price","param":{"symbol":"BTC_USDT"}}')
            next_ping=asyncio.get_running_loop().time()+16
            while asyncio.get_running_loop().time()<end:
                now=asyncio.get_running_loop().time()
                if now>=next_ping:
                    if venue=="BYBIT":
                        await ws.send('{"op":"ping"}');s["pings_sent"]+=1
                    elif venue=="OKX":
                        await ws.send("ping");s["pings_sent"]+=1
                    else:
                        await ws.send('{"method":"ping"}');s["pings_sent"]+=1
                    next_ping=now+16
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=min(1,max(.05,end-now)))
                except asyncio.TimeoutError:continue
                if not isinstance(raw,str):
                    s["errors"].append("NON_UTF8_WS_RAW")
                    continue
                recv=ms()
                writer.write(venue,raw,recv)
                try:classify_msg(venue,raw,recv,s)
                except Exception as e:
                    if len(s["errors"])<12:s["errors"].append(type(e).__name__+":"+str(e)[:120])
            s["completed_window"]=True
    except Exception as e:
        s["errors"].append("TRANSPORT:"+type(e).__name__+":"+str(e)[:180])
    return s
def judge(states):
    if not states or len(states)!=3:return "SOURCE_BLOCKED"
    for name in ("BYBIT","OKX","MEXC"):
        s=states[name]
        if not s["connected"] or not s["completed_window"] or s["errors"]:
            return "SOURCE_BLOCKED"
        if s["trade_children"]<1:return "SOURCE_INCOMPLETE_NO_REAL_TRADES"
    if not states["BYBIT"]["subscription_ack"] or states["BYBIT"]["pongs_received"]<2:
        return "SOURCE_BLOCKED"
    if not states["OKX"]["subscription_ack"] or states["MEXC"]["index_messages"]<1:
        return "SOURCE_BLOCKED"
    return "THREE_PUBLIC_WS_SCHEMA_SOURCE_PASS"
async def main(seconds):
    if seconds!=DURATION:raise ValueError("DURATION_MUST_BE_FROZEN_120_SECONDS")
    OUT.mkdir(exist_ok=True,parents=True)
    # Override shared writer location before first use, never use source V0.1 artifact path.
    import triple_flow_public_joint_source_v01 as old
    old.ROOT=OUT
    writers={v:Writer(v.lower()+"_source_ws.ndjson") for v in URLS}
    start=dt.datetime.now(dt.timezone.utc).isoformat();startms=ms()
    end=asyncio.get_running_loop().time()+DURATION
    values=await asyncio.gather(*(stream(n,end,writers[n]) for n in URLS))
    states=dict(zip(URLS,values))
    archive=[writers[n].finish() for n in URLS]
    verdict=judge(states)
    by=states["BYBIT"]
    liq="LIQUIDATION_SEMANTICS_OBSERVED" if by["liquidation_children"]>0 else "NO_LIQUIDATION_EVENT_OBSERVED"
    obj={"study":"TRIPLE_FLOW_BTC10M_THREE_PUBLIC_WEBSOCKETS_V02",
         "status":verdict,"liquidation_status":liq,"utc_start":start,
         "started_ms":startms,"completed_ms":ms(),"duration_seconds_frozen":DURATION,
         "streams":states,"raw_manifest":archive,
         "model_predictions_issued":0,"market_10m_outcomes_opened":0,
         "event_futures_fill_parity_proven":False,"economic_edge_proven":False,
         "perpetual_contract_size_verified":False,"liquidation_zero_true_market_events_proven":False,
         "authenticated_private_calls":0,"orders":0,"account_reads":0}
    (OUT/"source_receipt.json").write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
    print(json.dumps({k:v for k,v in obj.items() if k!="raw_manifest"},indent=2,sort_keys=True))
    if verdict!="THREE_PUBLIC_WS_SCHEMA_SOURCE_PASS":raise SystemExit(2)
if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("--seconds",type=int,default=DURATION)
    args=p.parse_args();asyncio.run(main(args.seconds))

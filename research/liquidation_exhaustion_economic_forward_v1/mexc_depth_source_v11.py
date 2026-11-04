#!/usr/bin/env python3
"""MEXC public depth-vs-ticker 120s source-only comparison, no economics."""
import asyncio,datetime as dt,hashlib,json,pathlib,time,argparse
from decimal import Decimal,InvalidOperation
from collections import Counter
URL="wss://contract.mexc.com/edge"
DURATION=120
OUT=pathlib.Path("artifacts/liquidation_exhaustion_depth_v11")

def utc_ms():return int(dt.datetime.now(dt.timezone.utc).timestamp()*1000)
def positive(v):
    try:d=Decimal(str(v))
    except (InvalidOperation,ValueError,TypeError):raise ValueError("NON_DECIMAL")
    if not d.is_finite() or d<=0:raise ValueError("NON_POSITIVE")
    return d
def parse_book(message):
    d=message.get("data")
    if not isinstance(d,dict) or (message.get("symbol") or d.get("symbol"))!="BTC_USDT":
        raise ValueError("SYMBOL_MISMATCH")
    a=d.get("asks");b=d.get("bids")
    if not isinstance(a,list) or not a or not isinstance(b,list) or not b:
        raise ValueError("MISSING_DEPTH_SIDES")
    asks=[(positive(x[0]),positive(x[1])) for x in a]
    bids=[(positive(x[0]),positive(x[1])) for x in b]
    best_bid=max(x[0] for x in bids);best_ask=min(x[0] for x in asks)
    if best_bid>=best_ask:raise ValueError("CROSSED_BOOK")
    return best_bid,best_ask
def lag(recv,msg):
    try:ts=int(msg.get("ts"))
    except (TypeError,ValueError):return None
    return recv-ts

async def collect():
    import websockets
    OUT.mkdir(parents=True,exist_ok=True)
    out=OUT/"raw_depth_and_ticker.ndjson"
    sha=hashlib.sha256()
    s={"study":"LIQUIDATION_EXHAUSTION_MEXC_DEPTH_SOURCE_ALTERNATIVE_V11",
       "frozen_amendment_commit":"f3f3ef4cba6a702657166a4d6daa14bd9a63e0af",
       "errors":[],"connect":False,"completed":False,
       "subscriptions":[],"pings":0,"pongs":0,"depth_frames":0,"ticker_frames":0,
       "depth_fresh":0,"depth_stale":0,"depth_eligible":0,
       "ticker_fresh":0,"ticker_stale":0,"depth_max_fresh_age_ms":None,
       "depth_sample_lags":[],"ticker_sample_lags":[],"unrecognized_channels":Counter(),
       "orders":0,"account_calls":0,"economic_outcomes_opened":0}
    consecutive=0;warm=False;stale_after_warm=0
    start=time.monotonic()
    try:
      async with websockets.connect(URL,open_timeout=20,ping_interval=None,
                                    max_size=5*1024*1024) as ws:
        s["connect"]=True
        await ws.send('{"method":"sub.depth.full","param":{"symbol":"BTC_USDT","limit":5}}')
        await ws.send('{"method":"sub.ticker","param":{"symbol":"BTC_USDT"}}')
        next_ping=start
        with out.open("w",encoding="utf-8") as file:
          while time.monotonic()-start<DURATION:
            if time.monotonic()>=next_ping:
                await ws.send('{"method":"ping"}');s["pings"]+=1
                next_ping=time.monotonic()+15
            try:raw=await asyncio.wait_for(ws.recv(),timeout=.8)
            except asyncio.TimeoutError:continue
            recv=utc_ms()
            if not isinstance(raw,str):s["errors"].append("NON_TEXT");continue
            line=json.dumps({"received_ms":recv,"monotonic_ns":time.monotonic_ns(),"raw":raw},separators=(",",":"))+"\n"
            file.write(line);sha.update(line.encode())
            try:
                o=json.loads(raw);c=o.get("channel","")
                if c=="pong":s["pongs"]+=1;continue
                if c=="rs.error":s["errors"].append("SUBSCRIPTION_REJECTED:"+str(o.get("data"))[:100]);continue
                if c.startswith("rs.sub."):
                    s["subscriptions"].append([c,o.get("data")]);continue
                if c=="push.ticker":
                    s["ticker_frames"]+=1
                    d=o.get("data")
                    if not isinstance(d,dict) or (o.get("symbol") or d.get("symbol"))!="BTC_USDT":
                        raise ValueError("TICKER_BAD_SYMBOL")
                    bid=positive(d.get("bid1"));ask=positive(d.get("ask1"))
                    if bid>=ask:raise ValueError("TICKER_CROSSED")
                    age=lag(recv,o);s["ticker_sample_lags"].append(age)
                    if age is not None and -250<=age<=1500:s["ticker_fresh"]+=1
                    else:s["ticker_stale"]+=1
                    continue
                if c=="push.depth.full":
                    s["depth_frames"]+=1
                    parse_book(o)
                    age=lag(recv,o);s["depth_sample_lags"].append(age)
                    if age is not None and -250<=age<=1500:
                        s["depth_fresh"]+=1;consecutive+=1
                        s["depth_max_fresh_age_ms"]=max(age,s["depth_max_fresh_age_ms"] or 0)
                        if consecutive>=3:warm=True
                        if warm:s["depth_eligible"]+=1
                    else:
                        s["depth_stale"]+=1;consecutive=0
                        if warm:stale_after_warm+=1
                    continue
                s["unrecognized_channels"][c]+=1
            except (ValueError,TypeError,KeyError,InvalidOperation) as ex:
                if len(s["errors"])<25:s["errors"].append(type(ex).__name__+":"+str(ex)[:140])
        s["completed"]=True
    except Exception as ex:
        s["errors"].append("TRANSPORT_"+type(ex).__name__+":"+str(ex)[:140])
    s["raw_sha256"]=sha.hexdigest()
    s["stale_depth_after_warm"]=stale_after_warm
    s["elapsed_seconds"]=round(time.monotonic()-start,3)
    s["unrecognized_channels"]=dict(s["unrecognized_channels"])
    s["depth_lag_summary_ms"]={
      "min":min((v for v in s["depth_sample_lags"] if v is not None),default=None),
      "max":max((v for v in s["depth_sample_lags"] if v is not None),default=None)}
    s["ticker_lag_summary_ms"]={
      "min":min((v for v in s["ticker_sample_lags"] if v is not None),default=None),
      "max":max((v for v in s["ticker_sample_lags"] if v is not None),default=None)}
    # Preserve a succinct receipt; raw holds all sample-level timestamps.
    del s["depth_sample_lags"];del s["ticker_sample_lags"]
    if s["errors"] or not s["connect"] or not s["completed"] or s["pongs"]<2:
        result="MEXC_DEPTH_SOURCE_BLOCKED"
    elif s["depth_eligible"]<30:
        result="SOURCE_INSUFFICIENT_DEPTH"
    elif s["stale_depth_after_warm"]>0:
        result="MEXC_DEPTH_SOURCE_BLOCKED_STALE"
    else:result="MEXC_DEPTH_SOURCE_WINDOW_TECHNICAL_PASS"
    s["verdict"]=result
    s["economic_edge_certified"]=False
    (OUT/"depth_source_receipt.json").write_text(json.dumps(s,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(s,indent=2,sort_keys=True))
    if result!="MEXC_DEPTH_SOURCE_WINDOW_TECHNICAL_PASS":raise SystemExit(2)
def selftest():
    good={"channel":"push.depth.full","symbol":"BTC_USDT","ts":1790000000000,
          "data":{"bids":[["80500","10"],["80499","9"]],"asks":[["80501","8"],["80502","4"]]}}
    assert parse_book(good)==(Decimal("80500"),Decimal("80501"))
    try:parse_book({**good,"data":{"bids":[["80502","1"]],"asks":[["80501","1"]]}})
    except ValueError:pass
    else:raise AssertionError("crossed depth accepted")
    assert lag(1790000000100,good)==100
    print("SYNTHETIC_MEXC_DEPTH_SOURCE_GUARDS_PASS_NOT_MARKET_PASS")
if __name__=="__main__":
    a=argparse.ArgumentParser();a.add_argument("--self-test",action="store_true")
    args=a.parse_args()
    if args.self_test:selftest()
    else:asyncio.run(collect())

#!/usr/bin/env python3
"""Public source-only 180-second Bybit BTC/ETH capture. No signals, PnL or orders."""
import argparse
import asyncio
import datetime as dt
import hashlib
import json
import pathlib
import time

URL = "wss://stream.bybit.com/v5/public/linear"
SYMBOLS = ("BTCUSDT", "ETHUSDT")
KINDS = ("publicTrade", "orderbook.50", "allLiquidation")
TOPICS = tuple(f"{kind}.{symbol}" for symbol in SYMBOLS for kind in KINDS)
OUT = pathlib.Path("artifacts/liquidation_exhaustion_v1")
SECONDS = 180

def ms():
    return int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)

def validate(msg, received):
    if not isinstance(msg, dict) or msg.get("topic") not in TOPICS:
        return None
    topic = msg["topic"]
    kind, symbol = topic.rsplit(".", 1)
    data = msg.get("data")
    if kind in ("publicTrade", "allLiquidation"):
        if not isinstance(data, list):
            raise ValueError("EXPECTED_LIST")
        for row in data:
            if not isinstance(row, dict) or row.get("s") != symbol:
                raise ValueError("BAD_SYMBOL_OR_CHILD")
            stamp = row.get("T") if kind == "publicTrade" else row.get("T")
            if type(stamp) is not int:
                raise ValueError("MISSING_EVENT_TIMESTAMP")
            if stamp > received + 3000 or received - stamp > 3000:
                raise ValueError("STALE_OR_FUTURE_CHILD")
            if kind == "allLiquidation":
                if row.get("S") not in ("Buy", "Sell"):
                    raise ValueError("INVALID_LIQUIDATION_SIDE")
                if float(row.get("v", 0)) <= 0 or float(row.get("p", 0)) <= 0:
                    raise ValueError("INVALID_LIQUIDATION_SIZE_PRICE")
        return kind, symbol, len(data)
    if not isinstance(data, dict) or data.get("s") != symbol:
        raise ValueError("BAD_BOOK_SYMBOL")
    if msg.get("type") not in ("snapshot", "delta"):
        raise ValueError("BAD_BOOK_TYPE")
    if type(data.get("u")) is not int:
        raise ValueError("BOOK_UPDATE_ID_MISSING")
    return kind, symbol, 1

def verdict(r):
    if r["errors"] or r["disconnects"] or r["bad_messages"]:
        return "SOURCE_BLOCKED"
    if r["subscribe_ack"] < 1 or r["pong"] < 5:
        return "SOURCE_BLOCKED"
    if any(r["book_snapshots"][s] == 0 for s in SYMBOLS):
        return "SOURCE_BLOCKED"
    if any(r["counts"][f"{kind}.{s}"] == 0 for s in SYMBOLS for kind in ("publicTrade", "orderbook.50")):
        return "SOURCE_BLOCKED"
    if r["liquidation_children"] == 0:
        return "SOURCE_INSUFFICIENT_POSITIVE_EVENTS"
    # A single short capture cannot establish full exchange liquidation census or
    # future before/after episode continuity, and cannot prove economic edge.
    return "SOURCE_PARTIAL_POSITIVE_EVENT_OBSERVED"

async def collect():
    import websockets
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "raw_public_frames.ndjson"
    r = dict(study="LIQUIDATION_EXHAUSTION_V1",source="BYBIT_PUBLIC_LINEAR",
             utc_started=dt.datetime.now(dt.timezone.utc).isoformat(),
             duration_seconds=SECONDS, topics=list(TOPICS), counts={t:0 for t in TOPICS},
             book_snapshots={s:0 for s in SYMBOLS}, liquidation_children=0,
             subscribe_ack=0,ping=0,pong=0,disconnects=0,bad_messages=0,errors=[],
             trade_book_continuity_certified=False,
             true_liquidation_zero_certified=False, pnl_measured=False,
             orders=0,auth_calls=0,protected_holdout_accessed=False)
    checksum=hashlib.sha256()
    last_book_u={}
    try:
        async with websockets.connect(URL,open_timeout=20,ping_interval=None,max_size=12*1024*1024) as ws:
            await ws.send(json.dumps({"op":"subscribe","args":TOPICS}))
            await ws.send(json.dumps({"op":"ping"}));r["ping"]+=1
            start=time.monotonic()
            next_ping=start+15
            with path.open("w",encoding="utf-8") as fh:
                while time.monotonic()-start < SECONDS:
                    now=time.monotonic()
                    if now>=next_ping:
                        await ws.send(json.dumps({"op":"ping"}));r["ping"]+=1
                        next_ping=now+15
                    try:
                        raw=await asyncio.wait_for(ws.recv(), timeout=0.7)
                    except asyncio.TimeoutError:
                        continue
                    received=ms()
                    if not isinstance(raw,str):
                        r["bad_messages"]+=1
                        continue
                    envelope={"received_utc_ms":received,"raw":raw}
                    encoded=json.dumps(envelope,separators=(",",":"),ensure_ascii=False)+"\n"
                    fh.write(encoded)
                    checksum.update(encoded.encode("utf-8"))
                    try:
                        msg=json.loads(raw)
                        if msg.get("op")=="subscribe":
                            if msg.get("success") is True:r["subscribe_ack"]+=1
                            else:r["errors"].append("SUBSCRIBE_REJECTED")
                            continue
                        if msg.get("op")=="pong" or msg.get("ret_msg")=="pong":
                            r["pong"]+=1
                            continue
                        value=validate(msg,received)
                        if value is None:
                            r["bad_messages"]+=1
                            continue
                        kind,symbol,size=value
                        r["counts"][msg["topic"]]+=1
                        if kind=="allLiquidation":r["liquidation_children"]+=size
                        if kind=="orderbook":
                            if msg["type"]=="snapshot":r["book_snapshots"][symbol]+=1
                            u=msg["data"]["u"]
                            prev=last_book_u.get(symbol)
                            if prev is not None and u < prev and u != 1 and msg["type"]!="snapshot":
                                r["errors"].append("BOOK_UPDATE_REGRESSION_"+symbol)
                            last_book_u[symbol]=u
                    except (ValueError,KeyError,TypeError,AttributeError,OverflowError) as exc:
                        if len(r["errors"])<30:r["errors"].append(type(exc).__name__+":"+str(exc)[:140])
            r["elapsed_seconds"]=round(time.monotonic()-start,3)
    except Exception as exc:
        r["disconnects"]+=1
        r["errors"].append("SOCKET_"+type(exc).__name__+":"+str(exc)[:160])
    r["raw_sha256"]=checksum.hexdigest()
    r["utc_ended"]=dt.datetime.now(dt.timezone.utc).isoformat()
    r["verdict"]=verdict(r)
    (OUT/"source_receipt.json").write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(r,indent=2,sort_keys=True))
    # Source-only status is scientific evidence even without any liquidation.
    # Raise on transport defects; positive events are NOT a pass for full custody.
    if r["verdict"]=="SOURCE_BLOCKED":raise SystemExit(2)

def self_test():
    now=1790000000000
    assert validate({"topic":"allLiquidation.BTCUSDT","data":[{"s":"BTCUSDT","S":"Sell","p":"60000","v":"1","T":now}]},now)==("allLiquidation","BTCUSDT",1)
    assert validate({"topic":"orderbook.50.ETHUSDT","type":"snapshot","data":{"s":"ETHUSDT","u":1,"b":[],"a":[]}},now)==("orderbook","ETHUSDT",1)
    try:
        validate({"topic":"allLiquidation.BTCUSDT","data":[{"s":"ETHUSDT","S":"Sell","p":"1","v":"1","T":now}]},now)
        raise AssertionError("should reject mismatch")
    except ValueError:pass
    assert verdict(dict(errors=[],disconnects=0,bad_messages=0,subscribe_ack=1,pong=5,
       book_snapshots={s:1 for s in SYMBOLS},counts={f"{k}.{s}":1 for s in SYMBOLS for k in ("publicTrade","orderbook.50")},liquidation_children=0))=="SOURCE_INSUFFICIENT_POSITIVE_EVENTS"
    print("SYNTHETIC_SOURCE_GUARDS_PASS_NOT_ECONOMIC_EVIDENCE")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:self_test()
    else:asyncio.run(collect())

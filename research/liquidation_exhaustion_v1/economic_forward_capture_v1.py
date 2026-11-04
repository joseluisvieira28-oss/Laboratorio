#!/usr/bin/env python3
"""One bounded PUBLIC-only forward window, Bybit sensor + MEXC quote proxy.
No credentials, accounts, wallet, orders, signals, schedule or commercial API.
Do not silently retry a failed source window.
"""
import asyncio
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.request import Request, urlopen

import websockets

URL_BYBIT="wss://stream.bybit.com/v5/public/linear"
URL_MEXC="https://api.mexc.com/api/v1/contract/depth/BTC_USDT?limit=5"
TOPICS=("publicTrade.BTCUSDT","orderbook.50.BTCUSDT","allLiquidation.BTCUSDT")
SECONDS=420
OUT=Path("artifacts/liquidation_exhaustion_economic_forward_v1")

def utc_ms():
    return int(datetime.now(timezone.utc).timestamp()*1000)

class Recorder:
    def __init__(self):
        OUT.mkdir(exist_ok=True,parents=True)
        self.file=(OUT/"raw_forward_public.ndjson").open("w",encoding="utf-8")
        self.hash=hashlib.sha256()
        self.counts=Counter()
        self.errors=[]
        self.lock=asyncio.Lock()
        self.started=utc_ms()
        self.heartbeat_sent=0;self.heartbeat_recv=0
        self.subscribed=False
        self.bybit_completed=False;self.mexc_completed=False
        self.first_bybit_book=False
        self.last_u=None;self.last_seq=None
    async def write(self,venue,payload):
        async with self.lock:
            recv=utc_ms()
            obj={"received_utc_ms":recv,"venue":venue,"payload":payload}
            encoded=json.dumps(obj,ensure_ascii=False,separators=(",",":"))+"\n"
            self.file.write(encoded)
            self.hash.update(encoded.encode("utf-8"))
            self.counts["raw_frames"]+=1
            return recv
    def error(self,message):
        if len(self.errors)<50:self.errors.append(str(message)[:190])
    def save(self):
        self.file.flush();self.file.close()
        obj={"study":"LIQUIDATION_EXHAUSTION_ECONOMIC_FORWARD_V1",
             "utc_started_ms":self.started,"utc_ended_ms":utc_ms(),
             "duration_frozen_seconds":SECONDS,"bybit_public":URL_BYBIT,
             "mexc_public_rest":URL_MEXC,
             "counts":dict(self.counts),"raw_sha256":self.hash.hexdigest(),
             "errors":self.errors,"bybit_completed":self.bybit_completed,
             "mexc_completed":self.mexc_completed,
             "bybit_subscribed":self.subscribed,
             "bybit_pings":self.heartbeat_sent,"bybit_pongs":self.heartbeat_recv,
             "orders":0,"account_auth":0,"private_calls":0,
             "protected_old_outcomes_opened":False,"real_fills":0,
             "economics_pre_registered":True}
        obj["source_verdict"]="SOURCE_WINDOW_COLLECTED" if (
            not self.errors and self.bybit_completed and self.mexc_completed
            and self.subscribed and self.heartbeat_recv>=6
            and self.counts["mexc_quote_success"]>=60
            and self.counts["bybit_book"]>20
            and self.counts["bybit_trade"]>20
            and self.first_bybit_book
        ) else "SOURCE_BLOCKED"
        (OUT/"collector_receipt.json").write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n")
        print(json.dumps(obj,indent=2,sort_keys=True))
        return obj

def public_mexc_depth():
    # Public information only; fixed 1.1s throttle, no auth, no retries.
    req=Request(URL_MEXC,headers={"User-Agent":"CryptoLabSourceResearch/1.0",
                               "Accept":"application/json"})
    with urlopen(req,timeout=4) as resp:
        if resp.status!=200:raise ValueError("MEXC_NON_200")
        raw=resp.read(120000)
    return json.loads(raw)

def validate_mexc(obj,now):
    d=obj.get("data") if isinstance(obj,dict) else None
    if obj.get("success") is not True or not isinstance(d,dict):
        raise ValueError("MEXC_DEPTH_SCHEMA")
    if not isinstance(d.get("timestamp"),int) or not d.get("bids") or not d.get("asks"):
        raise ValueError("MEXC_DEPTH_MISSING_TIMESTAMP_OR_BBO")
    lag=now-d["timestamp"]
    if lag<0 or lag>2000:raise ValueError("MEXC_DEPTH_STALE")
    bid=max(float(x[0]) for x in d["bids"])
    ask=min(float(x[0]) for x in d["asks"])
    if bid<=0 or ask<=bid:raise ValueError("MEXC_BBO_CROSSED")

async def bybit_task(rec,stop):
    try:
        async with websockets.connect(URL_BYBIT,open_timeout=15,ping_interval=None,
                                      max_size=12*1024*1024) as ws:
            await ws.send(json.dumps({"op":"subscribe","args":list(TOPICS)}))
            await ws.send('{"op":"ping"}');rec.heartbeat_sent+=1
            next_ping=time.monotonic()+15
            while time.monotonic()<stop:
                if time.monotonic()>=next_ping:
                    await ws.send('{"op":"ping"}')
                    rec.heartbeat_sent+=1
                    next_ping=time.monotonic()+15
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=0.7)
                except asyncio.TimeoutError:
                    continue
                if not isinstance(raw,str):raise ValueError("BYBIT_NON_TEXT")
                msg=json.loads(raw)
                recv=await rec.write("BYBIT",msg)
                if msg.get("op")=="subscribe":
                    if msg.get("success") is not True:raise ValueError("BYBIT_SUBSCRIBE_ERROR")
                    rec.subscribed=True
                elif msg.get("op")=="pong" or msg.get("ret_msg")=="pong":
                    rec.heartbeat_recv+=1
                else:
                    topic=msg.get("topic")
                    if topic not in TOPICS:raise ValueError("UNKNOWN_BYBIT_TOPIC")
                    if topic=="orderbook.50.BTCUSDT":
                        d=msg.get("data") or {}
                        u=d.get("u");seq=d.get("seq")
                        if not isinstance(u,int) or not isinstance(seq,int):
                            raise ValueError("BYBIT_BOOK_ID_MISSING")
                        if msg.get("type")=="snapshot":
                            rec.first_bybit_book=True
                        elif (not rec.first_bybit_book or rec.last_u is None or
                              u!=rec.last_u+1 or seq<rec.last_seq):
                            raise ValueError("BYBIT_BOOK_SEQUENCE_GAP")
                        rec.last_u=u;rec.last_seq=seq
                        if abs(recv-msg["ts"])>2000:raise ValueError("BYBIT_BOOK_STALE")
                        rec.counts["bybit_book"]+=1
                    else:
                        if not isinstance(msg.get("data"),list):
                            raise ValueError("BYBIT_CHILDREN_MALFORMED")
                        for x in msg["data"]:
                            if x.get("s")!="BTCUSDT" or type(x.get("T")) is not int:
                                raise ValueError("BYBIT_CHILD_SCHEMA")
                            if recv-x["T"]<0 or recv-x["T"]>2000:
                                raise ValueError("BYBIT_CHILD_STALE")
                        rec.counts["bybit_trade" if topic.startswith("publicTrade") else "bybit_liquidation"]+=len(msg["data"])
            rec.bybit_completed=True
    except Exception as ex:rec.error("BYBIT:"+type(ex).__name__+":"+str(ex))

async def mexc_task(rec,stop):
    try:
        while time.monotonic()<stop:
            started=time.monotonic()
            result=await asyncio.to_thread(public_mexc_depth)
            received=await rec.write("MEXC",result)
            validate_mexc(result,received)
            rec.counts["mexc_quote_success"]+=1
            await asyncio.sleep(max(0,1.1-(time.monotonic()-started)))
        rec.mexc_completed=True
    except Exception as ex:rec.error("MEXC:"+type(ex).__name__+":"+str(ex))

async def collect():
    rec=Recorder()
    stop=time.monotonic()+SECONDS
    await asyncio.gather(bybit_task(rec,stop),mexc_task(rec,stop))
    result=rec.save()
    if result["source_verdict"]=="SOURCE_BLOCKED":raise SystemExit(2)

def synthetic_test():
    sample={"success":True,"data":{"timestamp":1790000000000,
              "bids":[[100,1]],"asks":[[101,1]]}}
    validate_mexc(sample,1790000000100)
    try:validate_mexc(sample,1790000010000)
    except ValueError:pass
    else:raise AssertionError("STALE_REST_SNAPSHOT_ACCEPTED")
    print("SYNTHETIC_SOURCE_VALIDATION_PASS_NOT_ECONOMIC_EVIDENCE")

if __name__=="__main__":
    import sys
    if "--self-test" in sys.argv:synthetic_test()
    else:asyncio.run(collect())

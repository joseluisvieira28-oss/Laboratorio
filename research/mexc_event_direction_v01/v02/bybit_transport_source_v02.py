#!/usr/bin/env python3
"""95-second read-only Bybit public websocket transport/custody smoke.

No MEXC price/payout, no outcomes, no signals, no orders, accounts, auth or private API.
A healthy websocket is NOT proof of zero missing liquidation events.
"""
import argparse
import asyncio
from collections import defaultdict
from datetime import datetime,timezone
import hashlib
import json
import math
from pathlib import Path
import time

URL="wss://stream.bybit.com/v5/public/linear"
SYMBOLS=("BTCUSDT","ETHUSDT")
TOPICS=tuple(f"{type_}.{s}" for s in SYMBOLS
              for type_ in ("publicTrade","orderbook.50","allLiquidation"))
TOTAL_SEC=95
PING_EVERY=15
WINDOW_SEC=5
OUT=Path("artifacts/triple_flow_v02")

def utc_ms():
    return int(datetime.now(timezone.utc).timestamp()*1000)

def label(topic):
    if topic.startswith("publicTrade."):return "trade"
    if topic.startswith("orderbook.50."):return "book"
    if topic.startswith("allLiquidation."):return "liquidation"
    return None

def safe_data(msg):
    topic=msg.get("topic")
    if topic not in TOPICS:return None
    body=msg.get("data")
    if not isinstance(body,(list,dict)):return None
    symbol=topic.rsplit(".",1)[-1]
    if isinstance(body,dict) and body.get("s")!=symbol:return None
    if isinstance(body,list):
        if not all(isinstance(x,dict) and x.get("s")==symbol for x in body):
            return None
    return label(topic),symbol,len(body) if isinstance(body,list) else 1

async def collect(seconds=TOTAL_SEC):
    import websockets
    OUT.mkdir(parents=True,exist_ok=True)
    started=utc_ms()
    evidence={
        "lab":"TRIPLE_FLOW_V02_PUBLIC_TRANSPORT",
        "started_at_utc_ms":started,
        "duration_target_seconds":seconds,
        "websocket":URL,"topics":list(TOPICS),
        "auth_or_private":False,"orders":0,"outcome_joins":0,
        "protected_holdout_2026_09_accessed":False,
        "counts":{t:0 for t in TOPICS},
        "event_records":{s:0 for s in SYMBOLS},
        "last_message_utc_ms":{},
        "first_message_utc_ms":{},
        "book_snapshots":{s:0 for s in SYMBOLS},
        "book_restart_or_sequence_regressions":{s:0 for s in SYMBOLS},
        "subscribe_acks":0, "pong_received":0, "ping_sent":0,
        "reconnects":0, "bad_messages":0, "parse_errors":0,
        "errors":[],"raw_message_stream_hash":None,
        "transport_status":"STARTING",
        "liquidation_empty_windows":"UNKNOWN_NOT_ZERO",
        "census_complete_proven":False,
        "historical_tardis_continuity_proven":False,
    }
    buckets=defaultdict(set)
    rolling=hashlib.sha256()
    last_u={}
    target=set(TOPICS)
    try:
        async with websockets.connect(
                URL,open_timeout=20,close_timeout=5,
                ping_interval=None,max_size=12*1024*1024) as ws:
            t0=time.monotonic()
            await ws.send(json.dumps({"op":"subscribe","args":list(TOPICS)},separators=(",",":")))
            last_ping=t0
            await ws.send(json.dumps({"op":"ping"}))
            evidence["ping_sent"]+=1
            while time.monotonic()-t0<seconds:
                now=time.monotonic()
                if now-last_ping>=PING_EVERY:
                    await ws.send(json.dumps({"op":"ping"}))
                    evidence["ping_sent"]+=1
                    last_ping=now
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=0.75)
                except asyncio.TimeoutError:
                    continue
                if not isinstance(raw,str):
                    evidence["bad_messages"]+=1
                    continue
                recv=utc_ms()
                rolling.update(raw.encode("utf-8"))
                try:
                    msg=json.loads(raw)
                except json.JSONDecodeError:
                    evidence["parse_errors"]+=1
                    continue
                if not isinstance(msg,dict):
                    evidence["bad_messages"]+=1
                    continue
                if msg.get("op")=="pong" or msg.get("ret_msg")=="pong":
                    evidence["pong_received"]+=1
                    continue
                if msg.get("op")=="subscribe":
                    if msg.get("success") is True:
                        evidence["subscribe_acks"]+=1
                    else:
                        evidence["errors"].append("SUBSCRIPTION_REJECTED")
                    continue
                parsed=safe_data(msg)
                if parsed is None:
                    evidence["bad_messages"]+=1
                    continue
                kind,sym,size=parsed
                topic=msg["topic"]
                evidence["counts"][topic]+=1
                evidence["last_message_utc_ms"][topic]=recv
                evidence["first_message_utc_ms"].setdefault(topic,recv)
                buckets[topic].add((recv-started)//(WINDOW_SEC*1000))
                if kind=="liquidation":
                    evidence["event_records"][sym]+=size
                if kind=="book":
                    if msg.get("type")=="snapshot":
                        evidence["book_snapshots"][sym]+=1
                    u=(msg.get("data") or {}).get("u")
                    if type(u) is int:
                        old=last_u.get(sym)
                        if old is not None and u<old and u!=1 and msg.get("type")!="snapshot":
                            evidence["book_restart_or_sequence_regressions"][sym]+=1
                        last_u[sym]=u
            evidence["duration_seconds"]=round(time.monotonic()-t0,3)
    except Exception as e:
        evidence["errors"].append(type(e).__name__+":"+str(e)[:200])
        evidence["duration_seconds"]=0.0
    evidence["finished_at_utc_ms"]=utc_ms()
    evidence["raw_message_stream_hash"]=rolling.hexdigest()
    buckets_total=max(1,math.floor(evidence.get("duration_seconds",0)/WINDOW_SEC))
    evidence["coverage_buckets_5s"]={
        t:sum(i in buckets[t] for i in range(buckets_total)) for t in TOPICS}
    evidence["coverage_denominator_5s"]=buckets_total
    trades_books=all(
       evidence["coverage_buckets_5s"][t]/buckets_total>=0.70
       for t in TOPICS if not t.startswith("allLiquidation."))
    snapshots=all(evidence["book_snapshots"][s]>=1 for s in SYMBOLS)
    if (evidence.get("duration_seconds",0)>=90
        and evidence["subscribe_acks"]>=1
        and evidence["pong_received"]>=4
        and trades_books and snapshots and not evidence["errors"]
        and not any(evidence["book_restart_or_sequence_regressions"].values())):
        evidence["transport_status"]="PUBLIC_TRANSPORT_WINDOW_PASS"
    else:
        evidence["transport_status"]="TRANSPORT_INCOMPLETE"
    evidence["joint_source_verdict"]="SOURCE_INCOMPLETE__LIQUIDATION_CENSUS_UNPROVEN"
    evidence["can_open_outcomes"]=False
    path=OUT/"live_transport_receipt.json"
    path.write_text(json.dumps(evidence,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(evidence,indent=2,sort_keys=True))
    if evidence["transport_status"]!="PUBLIC_TRANSPORT_WINDOW_PASS":
        raise SystemExit(2)

def test():
    sample={"topic":"allLiquidation.BTCUSDT","data":[{"s":"BTCUSDT","S":"Buy","p":"60000","v":"1"}]}
    assert safe_data(sample)==("liquidation","BTCUSDT",1)
    assert safe_data({"topic":"allLiquidation.BTCUSDT","data":[]})==("liquidation","BTCUSDT",0)
    assert safe_data({"topic":"allLiquidation.BTCUSDT","data":[{"s":"ETHUSDT"}]}) is None
    assert safe_data({"topic":"allLiquidation.BTCUSDT","data":{} }) is None
    print("SYNTHETIC_SOURCE_VALIDATION_PASS; no real market claim")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:test()
    else:asyncio.run(collect())

#!/usr/bin/env python3
"""Public-market-data-only MEXC Futures depth integrity probe.

No authentication. No orders. No exchange mutation.
Checks whether incremental depth versions are contiguous in a short forward sample.
"""
import argparse
import asyncio
import json
import time
import urllib.request
from pathlib import Path

WS_URL="wss://contract.mexc.com/edge"
REST_DEPTH="https://contract.mexc.com/api/v1/contract/depth/{symbol}?limit=20"

def rest_snapshot(symbol):
    req=urllib.request.Request(
        REST_DEPTH.format(symbol=symbol),
        headers={"User-Agent":"Crypto-Lab-Forward-Depth/0.1"})
    with urllib.request.urlopen(req,timeout=15) as r:
        payload=json.loads(r.read().decode("utf-8"))
    d=payload["data"]
    return {"version":int(d["version"]),"timestamp":int(d["timestamp"]),
            "bids":d["bids"],"asks":d["asks"]}

async def capture(symbol, seconds):
    import websockets
    receipt={
      "purpose":"PUBLIC FORWARD MARKET DATA ONLY — NO ORDERS",
      "symbol":symbol,"seconds":seconds,"ws_url":WS_URL,
      "started_unix_ms":int(time.time()*1000),
      "events":0,"depth_events":0,"version_gaps":0,
      "nonmonotonic_versions":0,"first_version":None,"last_version":None,
      "subscription_ack":False
    }
    snapshot=await asyncio.to_thread(rest_snapshot,symbol)
    receipt["rest_snapshot_version"]=snapshot["version"]
    receipt["rest_snapshot_timestamp"]=snapshot["timestamp"]

    deadline=time.monotonic()+seconds
    prev=None
    async with websockets.connect(WS_URL,ping_interval=None,close_timeout=5,max_size=8_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":symbol,"compress":False}}))
        last_ping=time.monotonic()
        while time.monotonic()<deadline:
            if time.monotonic()-last_ping>10:
                await ws.send(json.dumps({"method":"ping"}))
                last_ping=time.monotonic()
            try:
                raw=await asyncio.wait_for(ws.recv(),timeout=5)
            except asyncio.TimeoutError:
                continue
            if isinstance(raw,bytes):
                raw=raw.decode("utf-8","replace")
            msg=json.loads(raw)
            receipt["events"]+=1
            if msg.get("channel")=="rs.sub.depth" and msg.get("data")=="success":
                receipt["subscription_ack"]=True
            if msg.get("channel")!="push.depth":
                continue
            data=msg.get("data") or {}
            if "version" not in data:
                continue
            v=int(data["version"])
            receipt["depth_events"]+=1
            if receipt["first_version"] is None:
                receipt["first_version"]=v
            if prev is not None:
                if v <= prev:
                    receipt["nonmonotonic_versions"]+=1
                elif v != prev+1:
                    receipt["version_gaps"]+=1
            prev=v
            receipt["last_version"]=v

    receipt["ended_unix_ms"]=int(time.time()*1000)
    hard_fail = (
      not receipt["subscription_ack"] or
      receipt["depth_events"] < 10 or
      receipt["version_gaps"] > 0 or
      receipt["nonmonotonic_versions"] > 0
    )
    receipt["gate"]="PASS_SAMPLE" if not hard_fail else "BLOCKED"
    return receipt

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--symbol",default="BTC_USDT")
    ap.add_argument("--seconds",type=int,default=20)
    args=ap.parse_args()
    receipt=asyncio.run(capture(args.symbol,args.seconds))
    out=Path("research/microstructure_scalping/receipts")
    out.mkdir(parents=True,exist_ok=True)
    (out/"mexc_forward_depth_v01.json").write_text(
      json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    raise SystemExit(0 if receipt["gate"]=="PASS_SAMPLE" else 2)

if __name__=="__main__":
    main()

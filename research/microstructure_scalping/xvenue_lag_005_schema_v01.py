#!/usr/bin/env python3
import asyncio, json, time, urllib.request
from pathlib import Path

BINANCE="wss://fstream.binance.com/ws/btcusdt@bookTicker"
MEXC="wss://contract.mexc.com/edge"
MEXC_REST="https://contract.mexc.com/api/v1/contract/depth/BTC_USDT?limit=20"

def mexc_snapshot():
    req=urllib.request.Request(MEXC_REST,headers={"User-Agent":"Crypto-Lab-XVenue/0.1"})
    with urllib.request.urlopen(req,timeout=15) as r:
        payload=json.loads(r.read().decode("utf-8"))
    return payload["data"]

async def binance_probe():
    import websockets
    out={"url":BINANCE,"messages":[]}
    async with websockets.connect(BINANCE,ping_interval=20,close_timeout=5,max_size=2_000_000) as ws:
        while len(out["messages"])<3:
            raw=await asyncio.wait_for(ws.recv(),timeout=10)
            recv_ns=time.time_ns()
            if isinstance(raw,bytes): raw=raw.decode()
            m=json.loads(raw)
            out["messages"].append({
              "recv_unix_ns":recv_ns,
              "keys":sorted(m.keys()),
              "sample":{k:m.get(k) for k in ("e","u","s","b","B","a","A","T","E") if k in m}
            })
    return out

async def mexc_probe():
    import websockets
    snap=await asyncio.to_thread(mexc_snapshot)
    out={
      "url":MEXC,
      "rest_snapshot":{
        "keys":sorted(snap.keys()),
        "version":snap.get("version"),
        "timestamp":snap.get("timestamp"),
        "bids_sample":(snap.get("bids") or [])[:2],
        "asks_sample":(snap.get("asks") or [])[:2],
      },
      "subscription_ack":False,
      "messages":[]
    }
    async with websockets.connect(MEXC,ping_interval=None,close_timeout=5,max_size=8_000_000) as ws:
        await ws.send(json.dumps({"method":"sub.depth","param":{"symbol":"BTC_USDT","compress":False}}))
        deadline=time.monotonic()+15
        while time.monotonic()<deadline and len(out["messages"])<3:
            raw=await asyncio.wait_for(ws.recv(),timeout=5)
            recv_ns=time.time_ns()
            if isinstance(raw,bytes): raw=raw.decode("utf-8","replace")
            m=json.loads(raw)
            if m.get("channel")=="rs.sub.depth" and m.get("data")=="success":
                out["subscription_ack"]=True
                continue
            if m.get("channel")!="push.depth":
                continue
            d=m.get("data") or {}
            out["messages"].append({
              "recv_unix_ns":recv_ns,
              "message_keys":sorted(m.keys()),
              "data_keys":sorted(d.keys()),
              "version":d.get("version"),
              "timestamp":d.get("timestamp"),
              "bids_sample":(d.get("bids") or [])[:2],
              "asks_sample":(d.get("asks") or [])[:2],
            })
    return out

async def main_async():
    b,m=await asyncio.gather(binance_probe(),mexc_probe())
    return {"purpose":"XVENUE SOURCE/SCHEMA ONLY — NO OUTCOMES","binance":b,"mexc":m}

def main():
    try:
        r=asyncio.run(main_async())
        ok=(len(r["binance"]["messages"])>=3 and r["mexc"]["subscription_ack"] and len(r["mexc"]["messages"])>=3)
        r["gate"]="PASS" if ok else "BLOCKED"
    except Exception as e:
        r={"purpose":"XVENUE SOURCE/SCHEMA ONLY — NO OUTCOMES","gate":"BLOCKED","error":repr(e)}
    out=Path("research/microstructure_scalping/receipts"); out.mkdir(parents=True,exist_ok=True)
    (out/"xvenue_lag_005_schema_v01.json").write_text(json.dumps(r,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps(r,indent=2,sort_keys=True))
    raise SystemExit(0 if r["gate"]=="PASS" else 2)

if __name__=="__main__":
    main()

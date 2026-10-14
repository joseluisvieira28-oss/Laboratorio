from __future__ import annotations

import argparse
import asyncio
import json
import pathlib
import time
from datetime import datetime, timezone

import websockets

URL="wss://stream.bybit.com/v5/public/linear"
SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","BNBUSDT"]
TOPICS=[f"allLiquidation.{s}" for s in SYMBOLS]
ROOT=pathlib.Path(__file__).resolve().parent
CAL=ROOT/"calibration"
CAL.mkdir(parents=True,exist_ok=True)
LEDGER=CAL/"liquidation_records_v0_1.jsonl"

def utc_now():
    return datetime.now(timezone.utc).isoformat()

def key_for(x):
    return (
        str(x.get("s","")),
        str(x.get("T","")),
        str(x.get("S","")),
        str(x.get("v","")),
        str(x.get("p","")),
    )

def load_seen():
    seen=set()
    if not LEDGER.exists():
        return seen
    with LEDGER.open("r",encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                env=json.loads(line)
                data=(env.get("message") or {}).get("data") or []
                if not isinstance(data,list):
                    data=[data]
                for x in data:
                    if isinstance(x,dict):
                        seen.add(key_for(x))
            except Exception:
                continue
    return seen

async def collect(seconds:int):
    seen=load_seen()
    starting=len(seen)
    new_records=0
    duplicate_records=0
    reconnects=0
    errors=[]
    deadline=time.monotonic()+seconds

    with LEDGER.open("a",encoding="utf-8") as fh:
        while time.monotonic()<deadline:
            try:
                async with websockets.connect(
                    URL,ping_interval=20,ping_timeout=20,close_timeout=5,max_size=2**22
                ) as ws:
                    await ws.send(json.dumps({"op":"subscribe","args":TOPICS}))
                    while time.monotonic()<deadline:
                        timeout=max(0.1,min(5.0,deadline-time.monotonic()))
                        try:
                            raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
                        except asyncio.TimeoutError:
                            continue
                        obj=json.loads(raw)
                        topic=str(obj.get("topic",""))
                        if not topic.startswith("allLiquidation."):
                            continue
                        data=obj.get("data") or []
                        if not isinstance(data,list):
                            data=[data]
                        for x in data:
                            if not isinstance(x,dict):
                                continue
                            k=key_for(x)
                            if k in seen:
                                duplicate_records+=1
                                continue
                            seen.add(k)
                            env={
                                "received_at_utc":utc_now(),
                                "message":{
                                    "topic":topic,
                                    "type":obj.get("type"),
                                    "ts":obj.get("ts"),
                                    "data":[x],
                                },
                            }
                            fh.write(json.dumps(env,separators=(",",":"),sort_keys=True)+"\n")
                            fh.flush()
                            new_records+=1
            except Exception as e:
                errors.append({"at":utc_now(),"error":type(e).__name__+":"+str(e)[:300]})
                reconnects+=1
                await asyncio.sleep(min(5.0,0.5*(2**min(reconnects,4))))

    summary={
        "lab_id":"LIQUIDATION-PRESSURE-002-FORWARD",
        "phase":"SOURCE_ONLY_CALIBRATION_CAPTURE_V0.1",
        "seconds":seconds,
        "symbols":SYMBOLS,
        "starting_unique_records":starting,
        "new_unique_records":new_records,
        "ending_unique_records":len(seen),
        "duplicates_ignored":duplicate_records,
        "reconnects":reconnects,
        "error_count":len(errors),
        "errors":errors,
        "orders_submitted":0,
        "authenticated_endpoints_used":False,
        "wallet_mutations":0,
        "economic_outcomes_opened":False,
        "pnl_computed":False,
        "ended_at_utc":utc_now(),
    }
    (CAL/"last_capture_summary_v0_1.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8"
    )
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=int,default=3000)
    args=ap.parse_args()
    asyncio.run(collect(args.seconds))

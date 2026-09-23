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
TOPICS=(
    [f"allLiquidation.{s}" for s in SYMBOLS]
    + [f"orderbook.50.{s}" for s in SYMBOLS]
    + [f"publicTrade.{s}" for s in SYMBOLS]
)
ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(parents=True,exist_ok=True)

def utc_now():
    return datetime.now(timezone.utc).isoformat()

async def run(seconds:int, outfile:pathlib.Path):
    started=time.monotonic()
    deadline=started+seconds
    reconnects=0
    msg_count=0
    liq_records=0
    errors=[]
    with outfile.open("a",encoding="utf-8") as fh:
        while time.monotonic()<deadline:
            try:
                async with websockets.connect(
                    URL,ping_interval=20,ping_timeout=20,close_timeout=5,max_size=2**24
                ) as ws:
                    await ws.send(json.dumps({"op":"subscribe","args":TOPICS}))
                    while time.monotonic()<deadline:
                        timeout=max(0.1,min(5.0,deadline-time.monotonic()))
                        try:
                            raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
                        except asyncio.TimeoutError:
                            continue
                        recv_utc=utc_now()
                        recv_mono_ns=time.monotonic_ns()
                        obj=json.loads(raw)
                        rec={
                            "received_at_utc":recv_utc,
                            "received_monotonic_ns":recv_mono_ns,
                            "message":obj,
                        }
                        fh.write(json.dumps(rec,separators=(",",":"),sort_keys=True)+"\n")
                        fh.flush()
                        msg_count+=1
                        topic=obj.get("topic","")
                        if topic.startswith("allLiquidation."):
                            data=obj.get("data") or []
                            liq_records+=len(data) if isinstance(data,list) else 1
            except Exception as e:
                errors.append({"at":utc_now(),"error":type(e).__name__+":"+str(e)[:300]})
                reconnects+=1
                await asyncio.sleep(min(5.0,0.5*(2**min(reconnects,4))))

    summary={
        "lab_id":"LIQUIDATION-PRESSURE-002-FORWARD",
        "phase":"FORWARD_COLLECTOR_V0.1",
        "seconds":seconds,
        "symbols":SYMBOLS,
        "topics":TOPICS,
        "message_count":msg_count,
        "liquidation_records":liq_records,
        "reconnects":reconnects,
        "error_count":len(errors),
        "errors":errors,
        "orders_submitted":0,
        "authenticated_endpoints_used":False,
        "wallet_mutations":0,
        "pnl_computed":False,
        "ended_at_utc":utc_now(),
    }
    (OUT/"forward_collector_v0_1_summary.json").write_text(
        json.dumps(summary,indent=2,sort_keys=True),encoding="utf-8"
    )
    print(json.dumps(summary,indent=2,sort_keys=True))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=int,default=120)
    ap.add_argument("--outfile",default=str(OUT/"forward_raw_v0_1.jsonl"))
    args=ap.parse_args()
    asyncio.run(run(args.seconds,pathlib.Path(args.outfile)))

from __future__ import annotations

import asyncio
import json
import pathlib
import time
from datetime import datetime, timezone

import websockets

ROOT=pathlib.Path(__file__).resolve().parent
OUT=ROOT/"evidence"
OUT.mkdir(parents=True,exist_ok=True)
SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","XRPUSDT","DOGEUSDT","BNBUSDT"]
URL="wss://stream.bybit.com/v5/public/linear"
TOPICS=[f"tickers.{s}" for s in SYMBOLS]

def utc_now():
    return datetime.now(timezone.utc).isoformat()

async def main():
    rows={}
    errors=[]
    ack=False
    deadline=time.monotonic()+30
    try:
        async with websockets.connect(URL,ping_interval=20,ping_timeout=20,close_timeout=5,max_size=2**20) as ws:
            await ws.send(json.dumps({"op":"subscribe","args":TOPICS}))
            while time.monotonic()<deadline and len(rows)<len(SYMBOLS):
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=5)
                except asyncio.TimeoutError:
                    continue
                msg=json.loads(raw)
                if msg.get("success") is True and msg.get("op")=="subscribe":
                    ack=True
                    continue
                topic=msg.get("topic","")
                if not topic.startswith("tickers."):
                    continue
                d=msg.get("data") or {}
                sym=d.get("symbol") or topic.split(".",1)[1]
                nxt=d.get("nextFundingTime")
                interval=d.get("fundingIntervalHour")
                if sym in SYMBOLS and nxt and interval:
                    rows[sym]={
                        "symbol":sym,
                        "next_funding_time_ms":int(nxt),
                        "funding_interval_hours":int(interval),
                        "funding_rate":d.get("fundingRate"),
                        "received_at_utc":utc_now(),
                        "type":msg.get("type"),
                        "exchange_ts_ms":msg.get("ts"),
                    }
    except Exception as e:
        errors.append(type(e).__name__+":"+str(e)[:400])

    ordered=[rows[s] for s in SYMBOLS if s in rows]
    passed=ack and len(ordered)==len(SYMBOLS) and not errors
    receipt={
        "lab_id":"LIQUIDATION-PRESSURE-002-FORWARD",
        "phase":"FUNDING_SCHEDULE_SOURCE_PROBE_V0.1",
        "source":"Bybit public linear ticker WebSocket",
        "subscription_ack":ack,
        "symbols_requested":SYMBOLS,
        "symbols_observed":[x["symbol"] for x in ordered],
        "rows":ordered,
        "error_count":len(errors),
        "errors":errors,
        "verdict":"FUNDING_SCHEDULE_SOURCE_PASS" if passed else "FUNDING_SCHEDULE_SOURCE_FAIL_CLOSED",
        "economic_outcomes_opened":False,
        "pnl_computed":False,
        "generated_at_utc":utc_now(),
        "note":"Public ticker metadata only; used prospectively to exclude 30s holds crossing scheduled funding."
    }
    (OUT/"funding_schedule_source_probe_v0_1.json").write_text(
        json.dumps(receipt,indent=2,sort_keys=True),encoding="utf-8"
    )
    print(json.dumps(receipt,indent=2,sort_keys=True))
    if not passed:
        raise SystemExit(2)

asyncio.run(main())

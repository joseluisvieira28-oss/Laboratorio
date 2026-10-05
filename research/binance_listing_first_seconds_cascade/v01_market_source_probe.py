#!/usr/bin/env python3
# Source-only connectivity/timestamp probe for forward first-seconds cascade.
# No trading, no authentication, no account data.

import asyncio, json, time
import websockets

URL="wss://ws.bitget.com/v2/ws/public"
SYMBOL="BTCUSDT"

async def main():
    counts={"trade":0,"books1":0}
    exchange_ts=[]
    local_ns=[]
    async with websockets.connect(URL,ping_interval=20,ping_timeout=20,close_timeout=5) as ws:
        sub={
          "op":"subscribe",
          "args":[
            {"instType":"SPOT","channel":"trade","instId":SYMBOL},
            {"instType":"SPOT","channel":"books1","instId":SYMBOL},
          ]
        }
        await ws.send(json.dumps(sub))
        deadline=time.monotonic()+12
        while time.monotonic()<deadline and (counts["trade"]<3 or counts["books1"]<3):
            raw=await asyncio.wait_for(ws.recv(),timeout=5)
            recv=time.monotonic_ns()
            if isinstance(raw,bytes):
                raw=raw.decode("utf-8","replace")
            try: msg=json.loads(raw)
            except Exception: continue
            arg=msg.get("arg") or {}
            ch=arg.get("channel")
            if ch not in counts: continue
            data=msg.get("data") or []
            if not data: continue
            counts[ch]+=len(data)
            local_ns.append(recv)
            for x in data:
                ts=x.get("ts") or msg.get("ts")
                if ts is not None:
                    try: exchange_ts.append(int(ts))
                    except Exception: pass
    res={
      "public_ws_connected":True,
      "trade_messages_positive":counts["trade"]>0,
      "books1_messages_positive":counts["books1"]>0,
      "trade_records":counts["trade"],
      "books1_records":counts["books1"],
      "exchange_timestamps_present":len(exchange_ts)>0,
      "local_monotonic_timestamps_present":len(local_ns)>0,
      "source_gate_pass":counts["trade"]>0 and counts["books1"]>0 and len(exchange_ts)>0 and len(local_ns)>0,
    }
    print("FIRST_SECONDS_V01_MARKET_SOURCE_BEGIN")
    print(json.dumps(res,indent=2,sort_keys=True))
    print("FIRST_SECONDS_V01_MARKET_SOURCE_END")
    if not res["source_gate_pass"]:
        raise SystemExit(2)

asyncio.run(main())

# trigger after workflow registration

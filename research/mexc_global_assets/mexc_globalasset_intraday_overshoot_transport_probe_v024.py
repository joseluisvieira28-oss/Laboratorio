#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from pathlib import Path
from websockets.sync.client import connect as ws_connect

HERE = Path(__file__).resolve().parent
B = json.loads((HERE / "MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SOURCE_BINDING_V1.0.json").read_text())

MEXC_WS = "wss://contract.mexc.com/edge"
BITGET_V3_WS = "wss://ws.bitget.com/v3/ws/public"


def mexc_probe():
    symbols = [x["target"] for x in B["candidates"]]
    seen = set()
    channels = set()
    with ws_connect(MEXC_WS, open_timeout=10, close_timeout=3, max_size=2**22) as ws:
        for i, symbol in enumerate(symbols):
            ws.send(json.dumps({"method": "sub.kline", "param": {"symbol": symbol, "interval": "Min1"}}))
            if i and i % 8 == 0:
                ws.send(json.dumps({"method": "ping"}))
            time.sleep(0.05)
        ws.send(json.dumps({"method": "ping"}))
        deadline = time.time() + 25
        while time.time() < deadline:
            try:
                raw = ws.recv(timeout=3)
            except TimeoutError:
                ws.send(json.dumps({"method": "ping"}))
                continue
            j = json.loads(raw)
            ch = j.get("channel")
            if ch:
                channels.add(ch)
            if ch == "push.kline":
                sym = j.get("symbol") or (j.get("data") or {}).get("symbol")
                if sym:
                    seen.add(sym)
            if len(seen) >= 3:
                break
    if "push.kline" not in channels:
        raise SystemExit("MEXC_WS_NO_KLINE_PUSH")
    return {"subscriptions_sent": len(symbols), "symbols_with_push": len(seen), "channels_seen": sorted(channels)}


def bitget_v3_probe():
    symbols = sorted({x["external_bitget"] for x in B["candidates"]})
    args = [
        {"instType": "usdt-futures", "topic": "kline", "symbol": s, "interval": "1m"}
        for s in symbols
    ]
    seen = set()
    events = []
    shapes = []
    with ws_connect(BITGET_V3_WS, open_timeout=10, close_timeout=3, max_size=2**22) as ws:
        ws.send(json.dumps({"op": "subscribe", "args": args}))
        deadline = time.time() + 25
        next_ping = time.time() + 10
        while time.time() < deadline:
            if time.time() >= next_ping:
                ws.send("ping")
                next_ping = time.time() + 10
            try:
                raw = ws.recv(timeout=3)
            except TimeoutError:
                continue
            if raw == "pong":
                events.append("pong")
                continue
            j = json.loads(raw)
            if j.get("event"):
                events.append(str(j.get("event")) + ":" + str(j.get("code", "")))
                if j.get("event") == "error" or (j.get("code") not in (None, "", "0", "00000")):
                    raise SystemExit("BITGET_V3_SUBSCRIBE_ERROR:" + json.dumps(j, sort_keys=True))
            data = j.get("data")
            if data:
                arg = j.get("arg") or {}
                sym = arg.get("symbol") or arg.get("instId")
                if sym:
                    seen.add(sym)
                if len(shapes) < 3:
                    first = data[0] if isinstance(data, list) and data else data
                    shapes.append({
                        "top_keys": sorted(j.keys()),
                        "arg_keys": sorted(arg.keys()),
                        "data_type": type(first).__name__,
                        "row_len": len(first) if isinstance(first, list) else None,
                        "row_keys": sorted(first.keys()) if isinstance(first, dict) else None,
                    })
            if len(seen) >= 3:
                break
    if not seen:
        raise SystemExit("BITGET_V3_NO_KLINE_DATA")
    return {"subscriptions_sent": len(symbols), "symbols_with_data": len(seen), "events": events[:10], "shapes": shapes}


def main():
    assert len(B["candidates"]) == 35
    m = mexc_probe()
    b = bitget_v3_probe()
    print(json.dumps({
        "verdict": "TRANSPORT_PROBE_PASS",
        "economic_outcomes_scored": False,
        "mexc": m,
        "bitget_v3": b,
    }, sort_keys=True))


if __name__ == "__main__":
    main()

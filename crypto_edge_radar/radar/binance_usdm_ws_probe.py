from __future__ import annotations

import json
import time
from typing import Any

SYMBOLS=("BTCUSDT","ETHUSDT","SOLUSDT","BNBUSDT","XRPUSDT","DOGEUSDT")
WS_BASE="wss://fstream.binance.com/market"


class BinanceUSDMWebSocketError(RuntimeError):
    pass


def public_ws_source_probe(timeout_seconds:float=12.0)->dict[str,Any]:
    try:
        from websockets.sync.client import connect
    except Exception as exc:
        raise BinanceUSDMWebSocketError("websockets dependency unavailable") from exc

    streams=[]
    for symbol in SYMBOLS:
        s=symbol.lower()
        streams.append(f"{s}@kline_15m")
        streams.append(f"{s}@markPrice@1s")
    url=f"{WS_BASE}/stream?streams={'/'.join(streams)}"

    seen_kline=set()
    seen_mark=set()
    latest={}
    deadline=time.monotonic()+timeout_seconds
    try:
        with connect(url,open_timeout=8,close_timeout=2) as ws:
            while time.monotonic()<deadline and (
                len(seen_kline)<len(SYMBOLS) or len(seen_mark)<len(SYMBOLS)
            ):
                remaining=max(0.1,deadline-time.monotonic())
                raw=ws.recv(timeout=remaining)
                obj=json.loads(raw)
                if not isinstance(obj,dict) or "data" not in obj:
                    continue
                data=obj["data"]
                if not isinstance(data,dict):
                    continue
                event=str(data.get("e",""))
                symbol=str(data.get("s","")).upper()
                if symbol not in SYMBOLS:
                    continue
                if event=="kline":
                    k=data.get("k")
                    if not isinstance(k,dict):
                        raise BinanceUSDMWebSocketError("kline event missing k payload")
                    required=("t","T","i","o","h","l","c","x")
                    if any(field not in k for field in required):
                        raise BinanceUSDMWebSocketError(f"kline missing field:{symbol}")
                    if k["i"]!="15m":
                        raise BinanceUSDMWebSocketError(f"unexpected kline interval:{symbol}:{k['i']}")
                    seen_kline.add(symbol)
                    latest.setdefault(symbol,{})["kline_open_ms"]=int(k["t"])
                    latest[symbol]["kline_closed"]=bool(k["x"])
                elif event=="markPriceUpdate":
                    for field in ("p","r","T"):
                        if field not in data:
                            raise BinanceUSDMWebSocketError(f"mark price missing {field}:{symbol}")
                    seen_mark.add(symbol)
                    latest.setdefault(symbol,{})["mark_price"]=float(data["p"])
                    latest[symbol]["funding_rate"]=float(data["r"])
                    latest[symbol]["next_funding_ms"]=int(data["T"])
    except Exception as exc:
        if isinstance(exc,BinanceUSDMWebSocketError):
            raise
        raise BinanceUSDMWebSocketError(
            f"public websocket unavailable:{type(exc).__name__}:{exc}"
        ) from exc

    missing_kline=sorted(set(SYMBOLS)-seen_kline)
    missing_mark=sorted(set(SYMBOLS)-seen_mark)
    if missing_kline or missing_mark:
        raise BinanceUSDMWebSocketError(
            f"incomplete websocket coverage:kline={missing_kline}:mark={missing_mark}"
        )
    return {
        "status":"PASS_PUBLIC_WEBSOCKET_SOURCE",
        "provider":"BINANCE_USDM_PUBLIC_WEBSOCKET",
        "base_url":WS_BASE,
        "symbols":latest,
        "kline_symbols":len(seen_kline),
        "mark_price_funding_symbols":len(seen_mark),
        "authenticated_api_used":False,
        "orders_created":False,
        "exchange_mutation_performed":False,
        "used_as_forward_evidence":False,
    }

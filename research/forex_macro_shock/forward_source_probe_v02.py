#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone

import requests
from websockets.sync.client import connect as ws_connect

MEXC_WS="wss://contract.mexc.com/edge"
BINANCE_WS="wss://data-stream.binance.vision/ws/eurusdt@bookTicker"
ECB_DECISIONS="https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html"
ECB_CALENDAR="https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html"


def now():
    return datetime.now(timezone.utc).isoformat()


def probe_mexc():
    with ws_connect(MEXC_WS, open_timeout=10, close_timeout=3, max_size=2**22) as ws:
        ws.send(json.dumps({"method":"sub.kline","param":{"symbol":"EUR_USDT","interval":"Min1"}}))
        ws.send(json.dumps({"method":"ping"}))
        deadline=time.time()+15
        channels=set()
        schema=None
        while time.time()<deadline:
            try:
                raw=ws.recv(timeout=3)
            except TimeoutError:
                ws.send(json.dumps({"method":"ping"}))
                continue
            j=json.loads(raw)
            if j.get("channel"):
                channels.add(str(j.get("channel")))
            if j.get("channel")=="push.kline":
                d=j.get("data") or {}
                # Never report economic price values; source/schema only.
                required=("t","c","interval")
                if all(k in d for k in required):
                    schema={
                        "channel":"push.kline",
                        "has_start":True,
                        "has_close":True,
                        "interval":d.get("interval"),
                        "has_exchange_ts":j.get("ts") is not None,
                        "received_utc":now(),
                        "raw_sha256":hashlib.sha256(raw.encode()).hexdigest(),
                    }
                    break
        if schema is None:
            raise RuntimeError("MEXC_EUR_USDT_KLINE_NOT_OBSERVED")
        return {"ok":True,"channels_seen":sorted(channels),"schema":schema}


def probe_binance():
    with ws_connect(BINANCE_WS, open_timeout=10, close_timeout=3, max_size=2**22) as ws:
        raw=ws.recv(timeout=12)
        j=json.loads(raw)
        required=("s","b","B","a","A")
        if not all(k in j for k in required):
            raise RuntimeError("BINANCE_EURUSDT_BOOKTICKER_SCHEMA")
        if str(j.get("s","")).upper()!="EURUSDT":
            raise RuntimeError("BINANCE_WRONG_SYMBOL")
        # Never report bid/ask values; schema only.
        return {
            "ok":True,
            "symbol":"EURUSDT",
            "has_bid":True,
            "has_ask":True,
            "received_utc":now(),
            "raw_sha256":hashlib.sha256(raw.encode()).hexdigest(),
        }


def probe_ecb(url,label):
    t0=time.perf_counter()
    r=requests.get(url,timeout=20,headers={"User-Agent":"CryptoLab-Forex-Forward-Source/0.2"})
    latency=(time.perf_counter()-t0)*1000
    if r.status_code!=200 or not r.content:
        raise RuntimeError(f"{label}_HTTP_{r.status_code}")
    return {
        "ok":True,
        "status":r.status_code,
        "latency_ms":round(latency,2),
        "received_utc":now(),
        "body_sha256":hashlib.sha256(r.content).hexdigest(),
        "bytes":len(r.content),
    }


def main():
    out={
        "candidate":"FOREX-MACRO-SHOCK-001/EUR-ECB-FWD-V0.2",
        "phase":"SOURCE_ONLY",
        "economic_outcomes_opened":False,
        "prices_printed":False,
        "basis_calculated":False,
        "pnl_calculated":False,
        "mexc":probe_mexc(),
        "binance":probe_binance(),
        "ecb_decisions":probe_ecb(ECB_DECISIONS,"ECB_DECISIONS"),
        "ecb_calendar":probe_ecb(ECB_CALENDAR,"ECB_CALENDAR"),
    }
    out["verdict"]="FORWARD_SOURCE_PROBE_PASS"
    print(json.dumps(out,sort_keys=True))


if __name__=="__main__":
    main()

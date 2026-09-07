from __future__ import annotations

import asyncio
import json
import os
import socket
import ssl
import time
import urllib.parse
import urllib.request

import websockets


HOSTS = ["api.mexc.com", "contract.mexc.com", "wbs-api.mexc.com"]
REST = {"spot": "https://api.mexc.com/api/v3/time", "futures": "https://contract.mexc.com/api/v1/contract/ping"}
WS = {"spot": "wss://wbs-api.mexc.com/ws", "futures": "wss://contract.mexc.com/edge"}


def check() -> dict:
    out = {"timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "proxy": {}, "dns": {}, "tls": {}, "rest": {}, "websocket": {}}
    for key in ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY"):
        value = os.getenv(key)
        if value and key != "NO_PROXY":
            parsed = urllib.parse.urlsplit(value); value = f"{parsed.scheme}://{parsed.hostname}:{parsed.port or 'default'}"
        out["proxy"][key] = value
    for host in HOSTS:
        try: out["dns"][host] = {"status": "PASS", "addresses": sorted({x[4][0] for x in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})}
        except Exception as exc: out["dns"][host] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    for host in HOSTS[:2]:
        started = time.perf_counter()
        try:
            with socket.create_connection((host, 443), timeout=5) as sock:
                with ssl.create_default_context().wrap_socket(sock, server_hostname=host) as secured:
                    out["tls"][host] = {"status": "PASS", "version": secured.version(), "latency_ms": round((time.perf_counter()-started)*1000, 2)}
        except Exception as exc: out["tls"][host] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    for name, url in REST.items():
        started = time.perf_counter()
        try:
            with urllib.request.urlopen(url, timeout=8) as response:
                out["rest"][name] = {"status": "PASS", "http": response.status, "latency_ms": round((time.perf_counter()-started)*1000, 2)}
        except Exception as exc: out["rest"][name] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}
    return out


async def ws_checks(out: dict) -> None:
    for name, uri in WS.items():
        started = time.perf_counter()
        try:
            async with websockets.connect(uri, open_timeout=8, close_timeout=2):
                out["websocket"][name] = {"status": "PASS", "latency_ms": round((time.perf_counter()-started)*1000, 2)}
        except Exception as exc: out["websocket"][name] = {"status": "FAIL", "error": f"{type(exc).__name__}: {exc}"}


if __name__ == "__main__":
    result = check(); asyncio.run(ws_checks(result)); print(json.dumps(result, indent=2, sort_keys=True))

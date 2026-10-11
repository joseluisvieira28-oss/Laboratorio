#!/usr/bin/env python3
"""Public-only MEXC Futures BBO snapshot source probe. No orders, auth or PnL."""
import argparse
import datetime as dt
import json
import math
import time
import urllib.request
from pathlib import Path

BASE = "https://contract.mexc.com/api/v1/contract/depth/"
SYMBOLS = ("BTC_USDT", "SOL_USDT")
MAX_AGE_MS = 10_000


def check(payload, observed_ms):
    if not isinstance(payload, dict) or payload.get("success") is not True or payload.get("code") != 0:
        raise ValueError("API_STATUS_FAIL")
    d = payload.get("data")
    if not isinstance(d, dict):
        raise ValueError("NO_DATA")
    ts = d.get("timestamp")
    if isinstance(ts, bool) or not isinstance(ts, int) or ts < 1_500_000_000_000:
        raise ValueError("BAD_EXCHANGE_TIMESTAMP_MS")
    age = observed_ms - ts
    if age < -5_000 or age > MAX_AGE_MS:
        raise ValueError("STALE_OR_FUTURE_QUOTE")
    if not isinstance(d.get("version"), int) or d["version"] <= 0:
        raise ValueError("BAD_VERSION")
    def best(side, high):
        rows = d.get(side)
        if not isinstance(rows, list) or not rows:
            raise ValueError("MISSING_" + side.upper())
        prices = []
        for row in rows:
            if not isinstance(row, list) or len(row) < 2:
                raise ValueError("BAD_LEVEL")
            p, q = float(row[0]), float(row[1])
            if not all(math.isfinite(x) for x in (p, q)) or p <= 0 or q <= 0:
                raise ValueError("BAD_PRICE_OR_SIZE")
            prices.append(p)
        return (max if high else min)(prices)
    bid, ask = best("bids", True), best("asks", False)
    if bid >= ask:
        raise ValueError("CROSSED_BBO")
    return {
        "exchange_timestamp_ms": ts, "observation_timestamp_ms": observed_ms,
        "exchange_age_ms": age, "version": d["version"], "bid": bid,
        "ask": ask, "spread_bps": (ask - bid) / ((ask + bid) / 2) * 10_000,
        "bid_levels": len(d["bids"]), "ask_levels": len(d["asks"])
    }


def probe(symbol):
    if symbol not in SYMBOLS:
        raise ValueError("SYMBOL_NOT_ALLOWLISTED")
    req = urllib.request.Request(BASE + symbol, headers={"User-Agent": "CryptoLabSourceGate/1.0", "Accept": "application/json"})
    t0 = time.monotonic()
    with urllib.request.urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise ValueError("NON_200_RESPONSE")
        payload = json.loads(response.read(1_000_000))
    t1 = time.monotonic()
    observed_ms = int(time.time() * 1000)
    valid = check(payload, observed_ms)
    return {"symbol": symbol, "rtt_ms": round((t1 - t0) * 1000, 2), **valid}


def run():
    result = {
        "schema": "asym_shock_bbo_public_source_gate.v1",
        "checked_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "trading_authority": "NONE", "live_trading": False,
        "source": "MEXC Futures public GET /api/v1/contract/depth/{symbol}",
        "symbols": [], "status": "SOURCE_GATE_BLOCKED"
    }
    for symbol in SYMBOLS:
        try:
            result["symbols"].append({"status": "PASS_ONE_SNAPSHOT_ONLY", **probe(symbol)})
        except Exception as exc:
            result["symbols"].append({"symbol": symbol, "status": "BLOCKED", "reason": type(exc).__name__, "detail": str(exc)[:180]})
    if all(s["status"] == "PASS_ONE_SNAPSHOT_ONLY" for s in result["symbols"]):
        result["status"] = "SOURCE_GATE_PARTIAL_BBO_REACHABLE"
    result["limitations"] = [
        "One snapshot cannot prove longitudinal uptime, fillability, execution slippage or historical BBO completeness.",
        "No official shock event source bound, no causal signal, no pre-outcome freeze, no outcomes scored.",
        "No authentication, trading, or capital."
    ]
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    a = p.parse_args()
    result = run()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()

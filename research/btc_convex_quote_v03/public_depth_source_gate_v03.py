#!/usr/bin/env python3
"""BTC Convex V0.3: isolated public Binance USD-M bid/ask DEPTH source gate.
One-shot and research-only. NO trading, orders, keys, accounts or private endpoints.
This is a quote SOURCE sample, not a strategy economic or fill validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from decimal import Decimal, ROUND_DOWN
from pathlib import Path

BASE = "https://fapi.binance.com"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT")
SIZES_USDT = ("10", "25", "50", "100")
MAX_LATENCY_MS = 2000
MAX_QUOTE_AGE_MS = 2000
MAX_CLOCK_OFFSET_MS = 1000
ROUNDTRIP_FEE_BPS = Decimal("20")
ROUNDTRIP_ADVERSE_SLIP_BPS = Decimal("4")
OUTFILE = Path(__file__).resolve().parent / "V03_QUOTE_SOURCE_GATE_RECEIPT.json"


def now_ms():
    return time.time_ns() // 1_000_000


def err(code, detail=""):
    raise ValueError(code + (":" + str(detail) if detail else ""))


def public_get(endpoint: str, params=None):
    assert endpoint in ("/fapi/v1/time", "/fapi/v1/exchangeInfo", "/fapi/v1/depth")
    url = BASE + endpoint
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url, method="GET",
        headers={"User-Agent": "CryptoLabQuoteSourceProbe/0.3", "Accept": "application/json"},
    )
    t0 = now_ms()
    with urllib.request.urlopen(req, timeout=10) as response:
        raw = response.read()
    t1 = now_ms()
    data = json.loads(raw)
    return data, {
        "path": endpoint,
        "parameters": params or {},
        "request_at_ms": t0,
        "received_at_ms": t1,
        "elapsed_ms": t1 - t0,
        "response_sha256": hashlib.sha256(raw).hexdigest(),
        "raw_bytes": len(raw),
    }


def positive_decimal(s, name):
    try:
        x = Decimal(str(s))
    except Exception as e:
        err("BAD_DECIMAL_" + name, type(e).__name__)
    if not x.is_finite() or x <= 0:
        err("NONPOSITIVE_" + name)
    return x


def filters_from_info(info, symbol):
    if not isinstance(info, dict) or not isinstance(info.get("symbols"), list):
        err("INVALID_EXCHANGE_INFO")
    matches = [x for x in info["symbols"] if x.get("symbol") == symbol]
    if len(matches) != 1:
        err("MISSING_SYMBOL", symbol)
    x = matches[0]
    if (x.get("status"), x.get("contractType"), x.get("quoteAsset")) != ("TRADING", "PERPETUAL", "USDT"):
        err("NOT_TRADING_USDM_PERPETUAL", symbol)
    filt = {z.get("filterType"): z for z in x.get("filters", [])}
    lot = filt.get("MARKET_LOT_SIZE")
    if lot is None:
        err("MISSING_MARKET_LOT_SIZE")
    min_qty = positive_decimal(lot.get("minQty"), "MIN_QTY")
    step = positive_decimal(lot.get("stepSize"), "STEP")
    max_qty = positive_decimal(lot.get("maxQty"), "MAX_QTY")
    nf = filt.get("MIN_NOTIONAL") or filt.get("NOTIONAL")
    if nf is None:
        err("MISSING_MIN_NOTIONAL")
    val = nf.get("notional") if "notional" in nf else nf.get("minNotional")
    minimum_notional = positive_decimal(val, "MIN_NOTIONAL")
    return {"min_qty": min_qty, "max_qty": max_qty, "step": step,
            "min_notional": minimum_notional, "status": x["status"]}


def parse_levels(arr, side):
    if not isinstance(arr, list) or not 1 <= len(arr) <= 20:
        err("DEPTH_LEVEL_COUNT_INVALID_" + side)
    out = []
    for level in arr:
        if not isinstance(level, list) or len(level) != 2:
            err("BAD_LEVEL_SHAPE_" + side)
        p = positive_decimal(level[0], side + "_PRICE")
        q = positive_decimal(level[1], side + "_QUANTITY")
        out.append((p, q))
    if side == "BIDS" and any(out[i][0] <= out[i + 1][0] for i in range(len(out) - 1)):
        err("BID_NOT_DESCENDING")
    if side == "ASKS" and any(out[i][0] >= out[i + 1][0] for i in range(len(out) - 1)):
        err("ASK_NOT_ASCENDING")
    return out


def sweep(levels, quantity):
    todo = quantity
    notion = Decimal(0)
    for price, avail in levels:
        matched = min(todo, avail)
        notion += matched * price
        todo -= matched
        if todo <= 0:
            return notion / quantity
    err("INSUFFICIENT_BOOK_DEPTH")


def validate_book(book, timing, symbol, filters):
    if timing["elapsed_ms"] < 0 or timing["elapsed_ms"] > MAX_LATENCY_MS:
        err("SOURCE_LATENCY_EXCEEDED")
    if not isinstance(book, dict):
        err("NON_OBJECT_DEPTH")
    event_ms = int(book["E"])
    trade_ms = int(book["T"])
    recv_ms = timing["received_at_ms"]
    if trade_ms > event_ms:
        err("TRANSACTION_AFTER_EVENT")
    if not 0 <= recv_ms - event_ms <= MAX_QUOTE_AGE_MS:
        err("STALE_OR_FUTURE_EVENT")
    if not 0 <= recv_ms - trade_ms <= MAX_QUOTE_AGE_MS:
        err("STALE_OR_FUTURE_TRANSACTION")
    if int(book.get("lastUpdateId", 0)) <= 0:
        err("INVALID_BOOK_UPDATE_ID")
    bids = parse_levels(book.get("bids"), "BIDS")
    asks = parse_levels(book.get("asks"), "ASKS")
    bid, ask = bids[0][0], asks[0][0]
    if bid >= ask:
        err("CROSSED_OR_LOCKED_MARKET")
    mid = (bid + ask) / 2
    spread_bps = (ask - bid) / mid * 10000
    scenarios = {}
    for amount in SIZES_USDT:
        nominal = Decimal(amount)
        qty = (nominal / ask / filters["step"]).to_integral_value(rounding=ROUND_DOWN) * filters["step"]
        if qty <= 0 or qty < filters["min_qty"] or qty > filters["max_qty"]:
            scenarios[amount] = {"status": "BLOCKED_LOT_SIZE", "qty": str(qty)}
            continue
        if qty * ask < filters["min_notional"]:
            scenarios[amount] = {"status": "BLOCKED_MIN_NOTIONAL", "qty": str(qty)}
            continue
        try:
            buy_vwap, sell_vwap = sweep(asks, qty), sweep(bids, qty)
            book_cost = (buy_vwap - sell_vwap) / buy_vwap * 10000
            scenarios[amount] = {
                "status": "SAMPLE_DEPTH_SUFFICIENT",
                "base_qty": str(qty),
                "actual_buy_notional_usdt": str(qty * buy_vwap),
                "buy_ask_vwap": str(buy_vwap), "sell_bid_vwap": str(sell_vwap),
                "book_roundtrip_cost_bps": float(book_cost),
                "assumed_fee_slip_adjusted_same_snapshot_cost_bps": float(
                    book_cost + ROUNDTRIP_FEE_BPS + ROUNDTRIP_ADVERSE_SLIP_BPS),
            }
        except ValueError as exc:
            scenarios[amount] = {"status": "BLOCKED_DEPTH", "reason": str(exc)}
    return {
        "symbol": symbol, "status": (
            "SOURCE_SAMPLE_PASS" if all(
                x["status"] == "SAMPLE_DEPTH_SUFFICIENT" for x in scenarios.values()
            ) else "SIZE_FEASIBILITY_BLOCKED"
        ),
        "book": {"E": event_ms, "T": trade_ms,
                 "lastUpdateId": int(book["lastUpdateId"]),
                 "best_bid": str(bid), "best_ask": str(ask),
                 "spread_bps": float(spread_bps),
                 "event_age_at_receipt_ms": recv_ms - event_ms,
                 "transaction_age_at_receipt_ms": recv_ms - trade_ms},
        "trading_filters": {k: str(v) for k, v in filters.items()},
        "scenarios_usdt": scenarios,
    }


def synthetic_tests():
    info = {"symbols": [{"symbol": "BTCUSDT", "status": "TRADING",
                          "contractType": "PERPETUAL", "quoteAsset": "USDT",
                          "filters": [
                              {"filterType": "MARKET_LOT_SIZE", "minQty": "0.001",
                               "maxQty": "100", "stepSize": "0.001"},
                              {"filterType": "MIN_NOTIONAL", "notional": "5"}]}]}
    f = filters_from_info(info, "BTCUSDT")
    ts = 100_000
    t = {"received_at_ms": ts, "elapsed_ms": 50}
    b = {"E": ts - 50, "T": ts - 50, "lastUpdateId": 42,
         "bids": [["10.0", "100"], ["9.9", "100"]],
         "asks": [["10.1", "100"], ["10.2", "100"]]}
    assert validate_book(b, t, "BTCUSDT", f)["status"] == "SOURCE_SAMPLE_PASS"
    for key, altered in (
        ("STALE_OR_FUTURE_EVENT", {**b, "E": ts - 2500, "T": ts - 2500}),
        ("TRANSACTION_AFTER_EVENT", {**b, "T": ts}),
        ("CROSSED_OR_LOCKED_MARKET", {**b, "bids": [["10.1", "100"]]}),
        ("BID_NOT_DESCENDING", {**b, "bids": [["9", "100"], ["10", "100"]]}),
    ):
        try:
            validate_book(altered, t, "BTCUSDT", f)
        except ValueError as exc:
            assert str(exc).startswith(key), (key, exc)
        else:
            raise AssertionError("MISSING_FAIL_CLOSED_" + key)
    too_small = {**f, "min_notional": Decimal("1000")}
    assert validate_book(b, t, "BTCUSDT", too_small)["status"] == "SIZE_FEASIBILITY_BLOCKED"
    print("SYNTHETIC_SOURCE_GATE_TESTS_PASS 6 cases")


def live():
    started = datetime.now(timezone.utc).isoformat()
    out = {"experiment_id": "BTC-CONVEX-QUOTE-V03-SOURCE-ONLY",
           "authority": "V03_QUOTE_SOURCE_PREFREEZE_2026_10_09",
           "mode": "PUBLIC_READ_ONLY_NO_TRADES",
           "started_utc": started,
           "runner_commit_sha": __import__("os").environ.get("GITHUB_SHA", "UNKNOWN_LOCAL"),
           "venue": "BINANCE_USDM_PERPETUAL",
           "source_base_url": BASE,
           "scenarios_usdt": list(SIZES_USDT),
           "assumed_roundtrip_fee_bps": float(ROUNDTRIP_FEE_BPS),
           "assumed_roundtrip_adverse_slip_bps": float(ROUNDTRIP_ADVERSE_SLIP_BPS),
           "source_calls": {}, "symbols": {}, "blockers": [],
           "scientific_caution": "One-shot source sample only. No strategy signal, position, outcome, or executable fill is proven."}
    try:
        tm, tr = public_get("/fapi/v1/time")
        out["source_calls"]["server_time"] = tr
        if tr["elapsed_ms"] > MAX_LATENCY_MS:
            err("SERVER_TIME_LATENCY")
        mid = (tr["request_at_ms"] + tr["received_at_ms"]) // 2
        out["server_clock_midpoint_offset_ms"] = int(tm["serverTime"]) - mid
        if abs(out["server_clock_midpoint_offset_ms"]) > MAX_CLOCK_OFFSET_MS:
            err("SERVER_CLOCK_SKEW")
        info, im = public_get("/fapi/v1/exchangeInfo")
        out["source_calls"]["exchange_info"] = im
        for sym in SYMBOLS:
            try:
                flt = filters_from_info(info, sym)
                book, meta = public_get("/fapi/v1/depth", {"symbol": sym, "limit": 20})
                out["source_calls"][sym] = meta
                val = validate_book(book, meta, sym, flt)
                out["symbols"][sym] = val
                if val["status"] != "SOURCE_SAMPLE_PASS":
                    out["blockers"].append(sym + ":" + val["status"])
            except Exception as e:
                out["symbols"][sym] = {"symbol": sym, "status": "SOURCE_BLOCKED", "reason": str(e)}
                out["blockers"].append(sym + ":" + str(e))
    except Exception as e:
        out["blockers"].append("GLOBAL_SOURCE:" + str(e))
    out["completed_utc"] = datetime.now(timezone.utc).isoformat()
    out["classification"] = (
        "SOURCE_SAMPLE_PASS_NOT_EXECUTION_PROOF" if not out["blockers"] and len(out["symbols"]) == 4
        else "SOURCE_BLOCKED_NO_TRADING")
    OUTFILE.parent.mkdir(parents=True, exist_ok=True)
    OUTFILE.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"classification": out["classification"], "blockers": out["blockers"],
                      "started_utc": out["started_utc"], "completed_utc": out["completed_utc"],
                      "symbols": {k: {"status": v["status"],
                                      "spread_bps": (v.get("book") or {}).get("spread_bps"),
                                      "scenarios": {x: q["status"] for x, q in v.get("scenarios_usdt", {}).items()}}
                                  for k, v in out["symbols"].items()}}, indent=2))
    if out["classification"] != "SOURCE_SAMPLE_PASS_NOT_EXECUTION_PROOF":
        raise SystemExit("SOURCE_BLOCKED_NO_TRADING")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        synthetic_tests()
    elif args.live:
        live()
    else:
        raise SystemExit("Pass --self-test or --live; never an order.")

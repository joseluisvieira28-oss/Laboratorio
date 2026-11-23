#!/usr/bin/env python3
"""BINANCE-DIAMANTE-002: six anonymous public Binance Spot GETs, no trading."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path

getcontext().prec = 34
HOST = "https://data-api.binance.vision"
SYMBOLS = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
NOTIONALS = (Decimal("100"), Decimal("1000"))
FEES_BPS_PER_LEG = (Decimal("0"), Decimal("10"))
D = Decimal
OUT = Path("binance002-evidence")
MAX_BYTES = 512_000

def canonical_url(symbol: str, kind: str) -> str:
    if symbol not in SYMBOLS or kind not in ("depth", "aggTrades"):
        raise ValueError("unauthorized symbol or endpoint")
    if kind == "depth":
        return f"{HOST}/api/v3/depth?symbol={symbol}&limit=100"
    return f"{HOST}/api/v3/aggTrades?symbol={symbol}&limit=100"

def positive_number(x, field: str) -> Decimal:
    try:
        y = D(str(x))
    except (InvalidOperation, TypeError, ValueError) as e:
        raise ValueError("invalid " + field) from e
    if not y.is_finite() or y <= 0:
        raise ValueError("non-positive or nonfinite " + field)
    return y

def parse_side(levels, *, side: str):
    if not isinstance(levels, list) or not (1 <= len(levels) <= 100):
        raise ValueError("unexpected " + side + " depth length")
    result = []
    last = None
    for item in levels:
        if not isinstance(item, list) or len(item) != 2:
            raise ValueError("bad depth level")
        price = positive_number(item[0], "level price")
        qty = positive_number(item[1], "level qty")
        if last is not None:
            if side == "bid" and price >= last:
                raise ValueError("bid levels not strictly descending")
            if side == "ask" and price <= last:
                raise ValueError("ask levels not strictly ascending")
        last = price
        result.append((price, qty))
    return result

def parse_depth(obj) -> dict:
    if not isinstance(obj, dict) or type(obj.get("lastUpdateId")) is not int or obj["lastUpdateId"] <= 0:
        raise ValueError("missing positive depth lastUpdateId")
    bids = parse_side(obj.get("bids"), side="bid")
    asks = parse_side(obj.get("asks"), side="ask")
    if bids[0][0] >= asks[0][0]:
        raise ValueError("crossed or locked book")
    mid = (bids[0][0] + asks[0][0]) / 2
    return {
        "last_update_id": obj["lastUpdateId"],
        "bids": bids, "asks": asks,
        "best_bid": bids[0][0], "best_ask": asks[0][0],
        "spread_bps": ((asks[0][0] - bids[0][0]) / mid) * D(10000),
        "visible_bid_quote": sum((p*q for p, q in bids), D(0)),
        "visible_ask_quote": sum((p*q for p, q in asks), D(0)),
        "note": "single static REST snapshot, no sequence-continuity evidence",
    }

def parse_trades(obj, receive_ms: int) -> dict:
    if not isinstance(obj, list) or not (1 <= len(obj) <= 100):
        raise ValueError("bad aggTrades array length")
    rows = []
    previous = None
    for item in obj:
        if not isinstance(item, dict) or any(k not in item for k in ("a", "p", "q", "f", "l", "T", "m")):
            raise ValueError("bad aggTrades fields")
        if any(type(item[k]) is not int for k in ("a", "f", "l", "T")):
            raise ValueError("bad aggTrades integers")
        if item["a"] < 0 or item["f"] < 0 or item["l"] < item["f"]:
            raise ValueError("invalid aggregate id/range")
        if previous is not None and item["a"] <= previous:
            raise ValueError("unsorted/duplicate aggregate ids")
        previous = item["a"]
        positive_number(item["p"], "trade price")
        positive_number(item["q"], "trade qty")
        if type(item["m"]) is not bool:
            raise ValueError("bad buyer-maker side flag")
        ts = item["T"]
        if ts < 1_500_000_000_000 or ts > receive_ms + 10_000:
            raise ValueError("invalid or future aggTrades millisecond timestamp")
        rows.append((ts, item["m"]))
    if receive_ms - max(t for t,_ in rows) > 300_000:
        raise ValueError("latest trade older than 5 minutes")
    if any(rows[i][0] > rows[i+1][0] for i in range(len(rows)-1)):
        raise ValueError("trade timestamp reversal")
    return {
        "n_aggregated_trades": len(rows),
        "first_agg_trade_ms": rows[0][0],
        "last_agg_trade_ms": rows[-1][0],
        "aggressive_buy_aggregates": sum(1 for _,buyer_maker in rows if not buyer_maker),
        "aggressive_sell_aggregates": sum(1 for _,buyer_maker in rows if buyer_maker),
        "warning": "100 aggregates are not 100 independent orders, nor a fixed-duration sample",
    }

def walk_buy_quote(asks, quote: Decimal):
    remaining = quote
    base = D(0)
    for price, quantity in asks:
        quote_available = price * quantity
        take_quote = min(remaining, quote_available)
        base += take_quote / price
        remaining -= take_quote
        if remaining <= D("0.00000000000000000000001"):
            return base
    return None

def walk_sell_base(bids, base: Decimal):
    remaining = base
    proceeds = D(0)
    for price, quantity in bids:
        take_base = min(remaining, quantity)
        proceeds += take_base * price
        remaining -= take_base
        if remaining <= D("0.00000000000000000000001"):
            return proceeds
    return None

def friction_matrix(book: dict):
    reports = []
    for notional in NOTIONALS:
        base = walk_buy_quote(book["asks"], notional)
        sold = walk_sell_base(book["bids"], base) if base is not None else None
        for bps in FEES_BPS_PER_LEG:
            report = {"quote_entry_usdt": str(notional), "fee_bps_each_leg": str(bps)}
            if sold is None:
                report["status"] = "INSUFFICIENT_DEPTH"
            else:
                fee = bps / D(10000)
                entry_cost = notional * (D(1) + fee)
                exit_net = sold * (D(1) - fee)
                loss = entry_cost - exit_net
                report.update({
                    "status": "HYPOTHETICAL_SAME_BOOK_ONLY",
                    "entry_base_units": str(base),
                    "gross_exit_usdt": str(sold),
                    "quote_fee_assumption": True,
                    "cost_usdt": str(loss.quantize(D("0.000001"))),
                    "cost_bps": str((D(10000) * loss / entry_cost).quantize(D("0.0001"))),
                    "actual_fills": False,
                })
            reports.append(report)
    return reports

def public_get(url: str) -> tuple:
    if not url.startswith(HOST + "/api/v3/") or not any(url == canonical_url(s, k) for s in SYMBOLS for k in ("depth", "aggTrades")):
        raise ValueError("endpoint not whitelisted")
    start = dt.datetime.now(dt.timezone.utc)
    mono = time.monotonic_ns()
    req = urllib.request.Request(url, headers={"User-Agent": "CryptoLab-Binance002/0.1-SOURCE_ONLY"})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                raise ValueError("unexpected HTTP " + str(response.status))
            raw = response.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        raise ValueError(f"HTTP_{e.code}_SOURCE_BLOCKED") from e
    receive = dt.datetime.now(dt.timezone.utc)
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("empty/oversized public response")
    return raw, {
        "url": url, "utc_request_start": start.isoformat(),
        "utc_received": receive.isoformat(),
        "receive_unix_ms": int(receive.timestamp() * 1000),
        "local_elapsed_ms": round((time.monotonic_ns() - mono) / 1e6, 3),
        "sha256_raw": hashlib.sha256(raw).hexdigest(),
        "n_bytes": len(raw)
    }

def run() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = {
        "study": "BINANCE-DIAMANTE-002", "scope": "SPOT_ONE_OFF_STATIC_SOURCE_ONLY",
        "status": "SOURCE_BLOCKED", "records": {}, "source_http_requests_max": 6,
        "executed_orders": 0, "real_fills": 0, "account_auth": False,
        "api_keys": False, "strategy_armed": False, "economic_edge_claim": False,
        "fee_assumptions_bps_each_leg": ["0", "10"],
        "no_retries": True, "orderbook_sequence_coverage": False,
        "scope_limit": "One REST book per symbol; no historical L2, no future returns, no executable account confirmation"
    }
    for symbol in SYMBOLS:
        records = {}
        try:
            # Always both GET attempts per asset unless blocked at transport level; no retry.
            for kind in ("depth", "aggTrades"):
                url = canonical_url(symbol, kind)
                try:
                    raw, receipt = public_get(url)
                    receipt["raw_file"] = f"{symbol}-{kind}.json"
                    (OUT / receipt["raw_file"]).write_bytes(raw)
                    data = json.loads(raw)
                    if kind == "depth":
                        book = parse_depth(data)
                        record = {k: str(v) for k,v in book.items() if k not in ("bids", "asks")}
                        record["friction"] = friction_matrix(book)
                    else:
                        record = parse_trades(data, receipt["receive_unix_ms"])
                    receipt["validation"] = record
                    receipt["status"] = "SOURCE_PASS"
                    records[kind] = receipt
                except Exception as e:
                    records[kind] = {
                        "url": url, "status": "SOURCE_BLOCKED",
                        "error_type": type(e).__name__, "error": str(e)[:250]
                    }
            report["records"][symbol] = records
        except Exception as e:
            report["records"][symbol] = {"fatal": str(e)[:250]}
    if all(
        report["records"].get(s, {}).get(k, {}).get("status") == "SOURCE_PASS"
        for s in SYMBOLS for k in ("depth", "aggTrades")
    ):
        report["status"] = "SOURCE_AND_COST_SNAPSHOT_PASS_ONLY"
    manifest = OUT / "manifest.json"
    manifest.write_text(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True) + "\n")
    (OUT / "manifest.sha256").write_text(hashlib.sha256(manifest.read_bytes()).hexdigest() + "  manifest.json\n")
    print(json.dumps(report, indent=2, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "SOURCE_AND_COST_SNAPSHOT_PASS_ONLY" else 2

if __name__ == "__main__":
    sys.exit(run())

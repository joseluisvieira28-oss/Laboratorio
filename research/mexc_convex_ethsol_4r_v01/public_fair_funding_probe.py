#!/usr/bin/env python3
"""SOURCE ONLY: MEXC public fair price/current funding/history for frozen ETH/SOL.

No private risk, accounts, orders, wallet, trade results, user credentials or live bot.
Never infer user margin tier or liquidation level from a public fairPrice observation.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://contract.mexc.com"
SYMBOLS = ("ETH_USDT", "SOL_USDT")
RESULT = Path("research/mexc_convex_ethsol_4r_v01/PUBLIC_FAIR_FUNDING_SOURCE_RECEIPT.json")
MAX_RESPONSE_BYTES = 1_000_000


def now_ms():
    return time.time_ns() // 1_000_000


def allowed(path):
    if path == "/api/v1/contract/ping":
        return True
    for sym in SYMBOLS:
        if path in ("/api/v1/contract/fair_price/" + sym,
                    "/api/v1/contract/funding_rate/" + sym):
            return True
    if path == "/api/v1/contract/funding_rate/history":
        return True
    return False


def req_json(path, query=None):
    if not allowed(path):
        raise ValueError("ENDPOINT_NOT_ALLOWLISTED")
    if path.endswith("/history"):
        if not isinstance(query, dict) or query != {
            "symbol": query.get("symbol"), "page_num": 1, "page_size": 1000
        } or query.get("symbol") not in SYMBOLS:
            raise ValueError("HISTORY_QUERY_NOT_ALLOWLISTED")
    elif query:
        raise ValueError("QUERY_NOT_ALLOWLISTED")
    url = BASE + path + ("?" + urllib.parse.urlencode(query) if query else "")
    start = now_ms()
    with urllib.request.urlopen(urllib.request.Request(
            url, method="GET",
            headers={"User-Agent": "CryptoLab-ETHSOL-4R-PUBLIC-SOURCE-ONLY/0.1"}),
            timeout=10) as r:
        raw = r.read(MAX_RESPONSE_BYTES + 1)
        http = r.status
    end = now_ms()
    if http != 200 or len(raw) > MAX_RESPONSE_BYTES or end - start > 2000:
        raise ValueError("HTTP_SIZE_OR_LATENCY_SOURCE_BLOCKED")
    body = json.loads(raw)
    if not isinstance(body, dict) or body.get("success") is not True or             body.get("code") not in (0, "0") or "data" not in body:
        raise ValueError("MEXC_PUBLIC_JSON_UNEXPECTED")
    return body["data"], {"endpoint": path, "query": query or {}, "http": http,
                          "request_ms": start, "receipt_ms": end,
                          "latency_ms": end - start,
                          "raw_sha256": hashlib.sha256(raw).hexdigest()}


def current_price_or_rate(data, expected_symbol, kind, receipt_ms):
    if not isinstance(data, dict) or data.get("symbol") != expected_symbol:
        raise ValueError("SYMBOL_OR_SCHEMA_MISMATCH")
    at = int(data["timestamp"])
    if not 0 <= receipt_ms - at <= 2000:
        raise ValueError("STALE_OR_FUTURE_PRICE_FUNDING_SOURCE")
    if kind == "fair":
        price = float(data["fairPrice"])
        if not math.isfinite(price) or price <= 0:
            raise ValueError("INVALID_FAIR_PRICE")
        return {"source_timestamp_ms": at, "source_age_ms": receipt_ms - at,
                "fair_price": str(data["fairPrice"])}
    r = float(data["fundingRate"])
    collect_cycle = int(data["collectCycle"])
    next_settle = int(data["nextSettleTime"])
    if not math.isfinite(r) or abs(r) > 1 or collect_cycle <= 0 or next_settle <= 0:
        raise ValueError("INVALID_FUNDING_RATE_META")
    return {"source_timestamp_ms": at, "source_age_ms": receipt_ms - at,
            "current_funding_rate_NOT_SETTLED": str(data["fundingRate"]),
            "collection_cycle_hours_unverified": collect_cycle,
            "next_settle_ms": next_settle}


def history_coverage(data, now):
    if not isinstance(data, dict):
        raise ValueError("HISTORY_SCHEMA_BAD")
    rows = data.get("resultList")
    if not isinstance(rows, list) or not rows:
        raise ValueError("EMPTY_PUBLIC_FUNDING_HISTORY_PAGE")
    times = []
    for row in rows:
        t = int(row["settleTime"])
        if t <= 0 or t > now + 1000:
            raise ValueError("FUTURE_OR_BAD_SETTLED_TIMESTAMP")
        times.append(t)
    if len(set(times)) != len(times):
        raise ValueError("DUPLICATE_HISTORY_TIMESTAMP")
    return {"rows": len(rows), "oldest_ms": min(times), "newest_ms": max(times),
            "pagination_not_proven_complete": True,
            "full_hold_funding_cashflow_proven": False}


def main():
    out = {
        "experiment": "MEXC-CONVEX-ETHSOL-4R-001",
        "gate": "PUBLIC_FAIR_FUNDING_SOURCE_V0_1",
        "run_commit": os.environ.get("GITHUB_SHA"),
        "source_only": True, "public_only": True,
        "private_account_risk_tiers": "BLOCKED_NOT_AUTHORIZED",
        "true_liquidation_price": "NOT_IDENTIFIABLE_FROM_THIS_PUBLIC_GATE",
        "full_funding_cashflows": "NOT_PROVEN",
        "forward_entries_scored": 0, "trades": 0, "orders": 0,
        "symbols": {}, "errors": [], "started_ms": now_ms(),
    }
    try:
        server, meta = req_json("/api/v1/contract/ping")
        out["server_ping_receipt"] = meta
        delta = int(server) - (meta["request_ms"] + meta["receipt_ms"]) // 2
        out["clock_skew_ms"] = delta
        if abs(delta) > 1000:
            raise ValueError("MEXC_SERVER_CLOCK_SKEW")
        for sym in SYMBOLS:
            d = {"public_receipts": [], "state": "SOURCE_BLOCKED"}
            out["symbols"][sym] = d
            try:
                fair, m = req_json("/api/v1/contract/fair_price/" + sym)
                d["public_receipts"].append(m)
                d["fair_price"] = current_price_or_rate(
                    fair, sym, "fair", m["receipt_ms"])
                current, m = req_json("/api/v1/contract/funding_rate/" + sym)
                d["public_receipts"].append(m)
                d["funding_now"] = current_price_or_rate(
                    current, sym, "funding", m["receipt_ms"])
                history, m = req_json("/api/v1/contract/funding_rate/history",
                                      {"symbol": sym, "page_num": 1,
                                       "page_size": 1000})
                d["public_receipts"].append(m)
                d["funding_history_page"] = history_coverage(
                    history, m["receipt_ms"])
                d["state"] = "FAIR_FUNDING_PUBLIC_SOURCE_PASS"
            except Exception as exc:
                d["reason"] = type(exc).__name__ + ":" + str(exc)
                out["errors"].append(sym + ":" + d["reason"])
    except Exception as exc:
        out["errors"].append("GLOBAL:" + type(exc).__name__ + ":" + str(exc))
    out["finished_ms"] = now_ms()
    out["classification"] = (
        "PUBLIC_FAIR_FUNDING_SOURCE_PASS_DIAGNOSTIC"
        if not out["errors"] and len(out["symbols"]) == len(SYMBOLS)
           and all(z["state"] == "FAIR_FUNDING_PUBLIC_SOURCE_PASS"
                   for z in out["symbols"].values())
        else "PUBLIC_FAIR_FUNDING_SOURCE_BLOCKED"
    )
    RESULT.write_text(json.dumps(out, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps({"classification": out["classification"],
                      "errors": out["errors"],
                      "symbols": {k: {"state": v["state"],
                          "reason": v.get("reason"),
                          "fair_quote_age_ms": v.get("fair_price", {}).get("source_age_ms"),
                          "funding_quote_age_ms": v.get("funding_now", {}).get("source_age_ms"),
                          "history_rows": v.get("funding_history_page", {}).get("rows")}
                          for k, v in out["symbols"].items()},
                      "full_funding_cashflows": "NOT_PROVEN",
                      "risk_tiers": "BLOCKED_PRIVATE",
                      "trades": 0, "orders": 0}, indent=2))
    if out["errors"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

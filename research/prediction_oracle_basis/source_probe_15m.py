#!/usr/bin/env python3
"""POB-15M-CHAINLINK-CFRTI-001 public source probe.

Research-only. This script inspects public metadata/rules/quote schemas.
It deliberately computes NO PnL, expected returns, win rates, or trade signals.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

UA = "CryptoLab-POB-SourceProbe/0.1 research-only"
OUT = Path("artifacts/prediction_oracle_basis")
POLY_EVENTS = "https://gamma-api.polymarket.com/events/keyset"
KALSHI_BASE = "https://external-api.kalshi.com/trade-api/v2"
MAX_POLY_PAGES = 30
PAGE_SIZE = 100


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url: str, params: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any]]:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    started = utc_now()
    with urllib.request.urlopen(req, timeout=25) as resp:
        raw = resp.read()
        status = int(resp.status)
        content_type = resp.headers.get("content-type", "")
    finished = utc_now()
    obj = json.loads(raw.decode("utf-8"))
    meta = {
        "url": url,
        "status": status,
        "content_type": content_type,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "raw_sha256": hashlib.sha256(raw).hexdigest(),
        "bytes": len(raw),
    }
    return obj, meta


def text_blob(x: dict[str, Any]) -> str:
    keys = [
        "title", "question", "description", "rules_primary", "rules_secondary",
        "subtitle", "yes_sub_title", "no_sub_title", "slug",
    ]
    return "\n".join(str(x.get(k) or "") for k in keys)


def poly_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    after = None
    found: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    seen = set()

    for _ in range(MAX_POLY_PAGES):
        params: dict[str, Any] = {"closed": "false", "limit": PAGE_SIZE}
        if after:
            params["after_cursor"] = after
        payload, meta = get_json(POLY_EVENTS, params)
        fetches.append(meta)
        events = payload.get("events", payload if isinstance(payload, list) else [])
        if not isinstance(events, list):
            raise RuntimeError("Unexpected Polymarket events schema")

        for event in events:
            if not isinstance(event, dict):
                continue
            markets = event.get("markets") or []
            for market in markets:
                if not isinstance(market, dict):
                    continue
                combined = (text_blob(event) + "\n" + text_blob(market)).lower()
                if "bitcoin up or down" not in combined:
                    continue
                # Current 15m family is distinguished from hourly by rule/source semantics
                # and/or 15-minute interval language. We keep broad candidates and fail
                # closed later rather than dropping a possible market by price/outcome.
                ruleish = combined
                source_shape = (
                    ("chainlink" in ruleish and "btc/usd" in ruleish)
                    or ("15 min" in ruleish)
                    or ("15-minute" in ruleish)
                    or ("15m" in ruleish)
                )
                if not source_shape:
                    continue
                mid = str(market.get("id") or market.get("conditionId") or market.get("slug") or "")
                if mid in seen:
                    continue
                seen.add(mid)
                clob = market.get("clobTokenIds")
                if isinstance(clob, str):
                    try:
                        clob = json.loads(clob)
                    except json.JSONDecodeError:
                        pass
                found.append({
                    "event_id": event.get("id"),
                    "event_slug": event.get("slug"),
                    "event_title": event.get("title"),
                    "market_id": market.get("id"),
                    "market_slug": market.get("slug"),
                    "question": market.get("question"),
                    "description": market.get("description"),
                    "start_date": market.get("startDate") or event.get("startDate"),
                    "end_date": market.get("endDate") or event.get("endDate"),
                    "condition_id": market.get("conditionId"),
                    "clob_token_ids": clob,
                    "rules_text_sha256": sha256_obj({"event": text_blob(event), "market": text_blob(market)}),
                    "mentions_chainlink": "chainlink" in ruleish,
                    "mentions_btc_usd": "btc/usd" in ruleish,
                    "raw_market_sha256": sha256_obj(market),
                })
        after = payload.get("next_cursor") if isinstance(payload, dict) else None
        if not after or not events:
            break

    return found, fetches


def kalshi_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    fetches: list[dict[str, Any]] = []
    markets: list[dict[str, Any]] = []
    cursor = None
    while True:
        params: dict[str, Any] = {
            "series_ticker": "KXBTC15M",
            "status": "open",
            "limit": 1000,
        }
        if cursor:
            params["cursor"] = cursor
        payload, meta = get_json(f"{KALSHI_BASE}/markets", params)
        fetches.append(meta)
        rows = payload.get("markets", [])
        if not isinstance(rows, list):
            raise RuntimeError("Unexpected Kalshi markets schema")
        markets.extend(rows)
        cursor = payload.get("cursor")
        if not cursor:
            break

    series = None
    try:
        series_payload, series_meta = get_json(f"{KALSHI_BASE}/series/KXBTC15M")
        fetches.append(series_meta)
        series = series_payload.get("series", series_payload)
    except Exception as exc:  # retain fail-closed evidence instead of hiding it
        fetches.append({"series_fetch_error": type(exc).__name__ + ": " + str(exc)})

    shaped: list[dict[str, Any]] = []
    for m in markets:
        rules = text_blob(m)
        lower = rules.lower()
        target_mentions_benchmark = bool(
            re.search(r"target.{0,160}(brti|cf benchmarks|real[- ]time index)", lower, re.S)
            or re.search(r"(brti|cf benchmarks|real[- ]time index).{0,160}target", lower, re.S)
        )
        shaped.append({
            "ticker": m.get("ticker"),
            "event_ticker": m.get("event_ticker"),
            "title": m.get("title"),
            "subtitle": m.get("subtitle"),
            "open_time": m.get("open_time"),
            "close_time": m.get("close_time"),
            "latest_expiration_time": m.get("latest_expiration_time"),
            "yes_bid_dollars": m.get("yes_bid_dollars"),
            "yes_bid_size_fp": m.get("yes_bid_size_fp"),
            "yes_ask_dollars": m.get("yes_ask_dollars"),
            "yes_ask_size_fp": m.get("yes_ask_size_fp"),
            "no_bid_dollars": m.get("no_bid_dollars"),
            "no_ask_dollars": m.get("no_ask_dollars"),
            "rules_primary": m.get("rules_primary"),
            "rules_secondary": m.get("rules_secondary"),
            "target_reference_proven_in_rules": target_mentions_benchmark,
            "rules_text_sha256": sha256_obj({"rules_primary": m.get("rules_primary"), "rules_secondary": m.get("rules_secondary")}),
            "raw_market_sha256": sha256_obj(m),
        })
    return shaped, fetches, series if isinstance(series, dict) else None


def classify(poly: list[dict[str, Any]], kalshi: list[dict[str, Any]]) -> dict[str, Any]:
    quote_fields = ("yes_bid_dollars", "yes_ask_dollars", "yes_bid_size_fp", "yes_ask_size_fp")
    kalshi_quote_ready = sum(all(m.get(k) is not None for k in quote_fields) for m in kalshi)
    target_proven = sum(bool(m.get("target_reference_proven_in_rules")) for m in kalshi)

    if not poly or not kalshi:
        state = "SOURCE_POPULATION_UNAVAILABLE"
    elif target_proven == 0:
        state = "TARGET_INITIALIZATION_UNPROVEN"
    else:
        # Even when the target reference is explicit, exact time/tie/payoff equivalence
        # needs pair-level proof. This probe intentionally does not auto-promote.
        state = "PAIRWISE_EQUIVALENCE_REVIEW_REQUIRED"

    return {
        "classification": state,
        "polymarket_candidate_count": len(poly),
        "kalshi_open_kxbtc15m_count": len(kalshi),
        "kalshi_quote_schema_complete_count": kalshi_quote_ready,
        "kalshi_target_reference_proven_count": target_proven,
        "exact_except_oracle_count": 0,
        "economic_outputs_computed": False,
        "future_nearest_joins": 0,
        "silent_imputations": 0,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "schema": "POB_15M_SOURCE_PROBE_V0.1",
        "generated_at_utc": utc_now(),
        "research_only": True,
        "economic_outputs_allowed": False,
    }
    try:
        poly, poly_fetch = poly_candidates()
        kalshi, kalshi_fetch, series = kalshi_candidates()
        receipt.update({
            "polymarket_candidates": poly,
            "kalshi_candidates": kalshi,
            "kalshi_series": series,
            "source_fetches": {"polymarket": poly_fetch, "kalshi": kalshi_fetch},
            "adjudication": classify(poly, kalshi),
        })
        receipt["receipt_sha256"] = sha256_obj(receipt)
        (OUT / "source_probe_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        receipt["adjudication"] = {
            "classification": "SOURCE_PROBE_TECHNICAL_FAILURE",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "economic_outputs_computed": False,
        }
        receipt["receipt_sha256"] = sha256_obj(receipt)
        (OUT / "source_probe_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt["adjudication"], indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

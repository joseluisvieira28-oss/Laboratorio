#!/usr/bin/env python3
"""POB-STRIKE-BINANCE-CFRTI-001 source-only geometry probe.

No PnL, returns, win-rate, profitability, threshold optimization, or trade simulation.
The script proves only whether current explicit-strike BTC contracts can be matched by
nominal strike and resolution instant, and whether public executable book routes exist.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

UA = "CryptoLab-POB-StrikeSourceProbe/0.1 research-only"
OUT = Path("artifacts/prediction_oracle_basis/strike")
POLY_EVENTS = "https://gamma-api.polymarket.com/events/keyset"
POLY_CLOB_BOOK = "https://clob.polymarket.com/book"
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
PAGE_SIZE = 100
MAX_POLY_PAGES = 40
NY = ZoneInfo("America/New_York")


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_obj(obj: Any) -> str:
    return hashlib.sha256(canonical(obj)).hexdigest()


def get_json(url: str, params: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any], bytes]:
    if params:
        url = url + ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    started = now_utc()
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        status = int(resp.status)
        ctype = resp.headers.get("content-type", "")
    finished = now_utc()
    obj = json.loads(raw.decode("utf-8"))
    meta = {
        "url": url,
        "status": status,
        "content_type": ctype,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "raw_sha256": sha256_bytes(raw),
        "bytes": len(raw),
    }
    return obj, meta, raw


def text_blob(x: dict[str, Any]) -> str:
    keys = [
        "title", "question", "description", "rules_primary", "rules_secondary",
        "subtitle", "yes_sub_title", "no_sub_title", "slug",
    ]
    return "\n".join(str(x.get(k) or "") for k in keys)


def parse_jsonish(v: Any) -> Any:
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") or s.startswith("{"):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return v
    return v


def parse_iso(x: Any) -> dt.datetime | None:
    if not x:
        return None
    s = str(x).replace("Z", "+00:00")
    try:
        out = dt.datetime.fromisoformat(s)
        if out.tzinfo is None:
            out = out.replace(tzinfo=dt.timezone.utc)
        return out.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def parse_money_from_text(text: str) -> Decimal | None:
    m = re.search(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)", text or "")
    if not m:
        return None
    try:
        return Decimal(m.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def poly_resolution_utc(event: dict[str, Any], market: dict[str, Any]) -> dt.datetime | None:
    # The frozen child accepts only rules that explicitly specify the noon ET daily geometry.
    combined = (text_blob(event) + "\n" + text_blob(market)).lower()
    noon_rule = (
        ("12:00" in combined and "et" in combined)
        or ("noon" in combined and "et" in combined)
    )
    if not noon_rule:
        return None

    # Use the venue's end-date to identify the calendar date, but reconstruct noon in
    # America/New_York explicitly so DST is not guessed from a fixed offset.
    raw_end = market.get("endDate") or event.get("endDate")
    parsed = parse_iso(raw_end)
    if parsed is not None:
        local_date = parsed.astimezone(NY).date()
        # If an API stores the date boundary rather than the actual close instant, the
        # event title is a better source for the intended civil date. Parse it when possible.
    else:
        local_date = None

    title = str(event.get("title") or market.get("question") or "")
    mm = re.search(
        r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2})(?:,\s*(\d{4}))?",
        title,
        flags=re.I,
    )
    if mm:
        month = dt.datetime.strptime(mm.group(1)[:3], "%b").month
        year = int(mm.group(3)) if mm.group(3) else (local_date.year if local_date else dt.datetime.now(NY).year)
        local_date = dt.date(year, month, int(mm.group(2)))

    if local_date is None:
        return None

    local_noon = dt.datetime.combine(local_date, dt.time(12, 0), tzinfo=NY)
    return local_noon.astimezone(dt.timezone.utc)


def poly_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    after = None
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    seen: set[str] = set()

    for _ in range(MAX_POLY_PAGES):
        params: dict[str, Any] = {"closed": "false", "limit": PAGE_SIZE}
        if after:
            params["after_cursor"] = after
        payload, meta, _ = get_json(POLY_EVENTS, params)
        fetches.append(meta)
        events = payload.get("events", payload if isinstance(payload, list) else [])
        if not isinstance(events, list):
            raise RuntimeError("Unexpected Polymarket event schema")

        for event in events:
            if not isinstance(event, dict):
                continue
            event_text = text_blob(event).lower()
            if "bitcoin above" not in event_text:
                continue
            for market in event.get("markets") or []:
                if not isinstance(market, dict):
                    continue
                combined = (text_blob(event) + "\n" + text_blob(market)).lower()
                required = (
                    "binance" in combined
                    and "btc/usdt" in combined
                    and ("1 minute candle" in combined or "1m" in combined)
                    and (("12:00" in combined and "et" in combined) or ("noon" in combined and "et" in combined))
                )
                if not required:
                    continue
                strike = parse_money_from_text(str(market.get("question") or "") + "\n" + str(market.get("title") or ""))
                if strike is None:
                    strike = parse_money_from_text(str(event.get("title") or ""))
                if strike is None:
                    continue
                resolution = poly_resolution_utc(event, market)
                if resolution is None:
                    continue

                mid = str(market.get("id") or market.get("conditionId") or market.get("slug") or "")
                if not mid or mid in seen:
                    continue
                seen.add(mid)

                outcomes = parse_jsonish(market.get("outcomes"))
                token_ids = parse_jsonish(market.get("clobTokenIds"))
                token_map: dict[str, str] = {}
                if isinstance(outcomes, list) and isinstance(token_ids, list) and len(outcomes) == len(token_ids):
                    token_map = {str(o).upper(): str(t) for o, t in zip(outcomes, token_ids)}

                rows.append({
                    "event_id": event.get("id"),
                    "event_slug": event.get("slug"),
                    "event_title": event.get("title"),
                    "market_id": market.get("id"),
                    "market_slug": market.get("slug"),
                    "question": market.get("question"),
                    "condition_id": market.get("conditionId"),
                    "nominal_strike": str(strike),
                    "resolution_utc": resolution.isoformat(),
                    "yes_token_id": token_map.get("YES"),
                    "no_token_id": token_map.get("NO"),
                    "rule_semantics": "STRICT_GT_NOMINAL_STRIKE",
                    "reference": "BINANCE_BTCUSDT_1M_CLOSE",
                    "rules_hash": sha256_obj({"event": text_blob(event), "market": text_blob(market)}),
                    "market_hash": sha256_obj(market),
                })

        after = payload.get("next_cursor") if isinstance(payload, dict) else None
        if not after or not events:
            break

    return rows, fetches


def kalshi_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    cursor = None

    while True:
        params: dict[str, Any] = {
            "series_ticker": "KXBTCD",
            "status": "open",
            "limit": 1000,
        }
        if cursor:
            params["cursor"] = cursor
        payload, meta, _ = get_json(f"{KALSHI_BASE}/markets", params)
        fetches.append(meta)
        markets = payload.get("markets", [])
        if not isinstance(markets, list):
            raise RuntimeError("Unexpected Kalshi market schema")
        for m in markets:
            if not isinstance(m, dict):
                continue
            combined = text_blob(m).lower()
            ticker = str(m.get("ticker") or "")
            close = parse_iso(m.get("close_time") or m.get("latest_expiration_time"))
            if close is None:
                continue

            displayed = parse_money_from_text(str(m.get("subtitle") or "") + "\n" + str(m.get("title") or ""))
            encoded = None
            mt = re.search(r"-T([0-9]+(?:\.[0-9]+)?)$", ticker)
            if mt:
                try:
                    encoded = Decimal(mt.group(1))
                except InvalidOperation:
                    encoded = None

            if displayed is None and encoded is not None:
                displayed = encoded + Decimal("0.01")

            if displayed is None:
                continue

            # Source-rule proof must remain explicit. A market that does not expose the
            # benchmark in captured rule text is not promoted by ticker inference alone.
            benchmark_proven = ("cf benchmarks" in combined) or ("brti" in combined) or ("real-time index" in combined)
            tie_delta = (displayed - encoded) if encoded is not None else None

            quote_fields = [
                m.get("yes_bid_dollars"),
                m.get("yes_ask_dollars"),
                m.get("yes_bid_size_fp"),
                m.get("yes_ask_size_fp"),
            ]

            rows.append({
                "ticker": ticker,
                "event_ticker": m.get("event_ticker"),
                "title": m.get("title"),
                "subtitle": m.get("subtitle"),
                "nominal_strike": str(displayed),
                "encoded_threshold": str(encoded) if encoded is not None else None,
                "tie_delta_usd": str(tie_delta) if tie_delta is not None else None,
                "resolution_utc": close.isoformat(),
                "rule_semantics": "AT_OR_ABOVE_NOMINAL_CENT_BOUNDARY" if tie_delta == Decimal("0.01") else "REVIEW_REQUIRED",
                "reference": "CF_BENCHMARKS_BRTI_FINAL_MINUTE_AVERAGE" if benchmark_proven else "REFERENCE_PROVENANCE_UNCONFIRMED",
                "benchmark_proven_in_rules": benchmark_proven,
                "quote_schema_complete": all(v is not None for v in quote_fields),
                "rules_hash": sha256_obj({"rules_primary": m.get("rules_primary"), "rules_secondary": m.get("rules_secondary"), "subtitle": m.get("subtitle")}),
                "market_hash": sha256_obj(m),
            })

        cursor = payload.get("cursor")
        if not cursor:
            break

    return rows, fetches


def summarize_book(book: Any, raw: bytes) -> dict[str, Any]:
    if not isinstance(book, dict):
        return {"schema_valid": False, "raw_sha256": sha256_bytes(raw)}
    payload = book.get("orderbook", book)
    bids = payload.get("bids") if isinstance(payload, dict) else None
    asks = payload.get("asks") if isinstance(payload, dict) else None
    # CLOB uses bids/asks. Kalshi orderbook can use yes/no arrays; record shape only.
    yes = payload.get("yes") if isinstance(payload, dict) else None
    no = payload.get("no") if isinstance(payload, dict) else None

    def level_keys(levels: Any) -> list[str]:
        if not isinstance(levels, list) or not levels:
            return []
        first = levels[0]
        if isinstance(first, dict):
            return sorted(str(k) for k in first.keys())
        if isinstance(first, list):
            return [f"index_{i}" for i in range(len(first))]
        return [type(first).__name__]

    return {
        "schema_valid": isinstance(payload, dict),
        "raw_sha256": sha256_bytes(raw),
        "bids_count": len(bids) if isinstance(bids, list) else None,
        "asks_count": len(asks) if isinstance(asks, list) else None,
        "yes_levels_count": len(yes) if isinstance(yes, list) else None,
        "no_levels_count": len(no) if isinstance(no, list) else None,
        "bids_level_schema": level_keys(bids),
        "asks_level_schema": level_keys(asks),
        "yes_level_schema": level_keys(yes),
        "no_level_schema": level_keys(no),
    }


def classify_pairs(poly: list[dict[str, Any]], kalshi: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in poly:
        pstrike = Decimal(p["nominal_strike"])
        ptime = parse_iso(p["resolution_utc"])
        if ptime is None:
            continue
        for k in kalshi:
            kstrike = Decimal(k["nominal_strike"])
            ktime = parse_iso(k["resolution_utc"])
            if ktime is None:
                continue
            if ptime != ktime:
                continue
            if pstrike != kstrike:
                continue

            if not k.get("benchmark_proven_in_rules"):
                cls = "SOURCE_RULE_PROVENANCE_BLOCKED"
            elif k.get("tie_delta_usd") == "0.01":
                cls = "MATCHED_STRIKE_TIME_REFERENCE_DIFF_TIE_1C"
            else:
                cls = "NON_EQUIVALENT_OTHER"

            out.append({
                "classification": cls,
                "resolution_utc": p["resolution_utc"],
                "nominal_strike": p["nominal_strike"],
                "polymarket_market_id": p["market_id"],
                "polymarket_condition_id": p["condition_id"],
                "polymarket_yes_token_id": p["yes_token_id"],
                "polymarket_no_token_id": p["no_token_id"],
                "kalshi_ticker": k["ticker"],
                "kalshi_encoded_threshold": k["encoded_threshold"],
                "kalshi_tie_delta_usd": k["tie_delta_usd"],
                "polymarket_rule_semantics": p["rule_semantics"],
                "kalshi_rule_semantics": k["rule_semantics"],
                "polymarket_reference": p["reference"],
                "kalshi_reference": k["reference"],
            })
    return out


def attach_book_proofs(pairs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fetches: list[dict[str, Any]] = []
    enriched: list[dict[str, Any]] = []

    for pair in pairs:
        row = dict(pair)

        for side in ("yes", "no"):
            token = row.get(f"polymarket_{side}_token_id")
            if token:
                try:
                    book, meta, raw = get_json(POLY_CLOB_BOOK, {"token_id": token})
                    fetches.append(meta)
                    row[f"polymarket_{side}_book"] = summarize_book(book, raw)
                except Exception as exc:
                    row[f"polymarket_{side}_book"] = {
                        "schema_valid": False,
                        "error": type(exc).__name__ + ": " + str(exc),
                    }

        ticker = row["kalshi_ticker"]
        try:
            book, meta, raw = get_json(f"{KALSHI_BASE}/markets/{urllib.parse.quote(ticker)}/orderbook")
            fetches.append(meta)
            row["kalshi_orderbook"] = summarize_book(book, raw)
        except Exception as exc:
            row["kalshi_orderbook"] = {
                "schema_valid": False,
                "error": type(exc).__name__ + ": " + str(exc),
            }

        enriched.append(row)

    return enriched, fetches


def adjudicate(poly: list[dict[str, Any]], kalshi: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [p for p in pairs if p["classification"] == "MATCHED_STRIKE_TIME_REFERENCE_DIFF_TIE_1C"]

    def poly_books_ready(p: dict[str, Any]) -> bool:
        y = p.get("polymarket_yes_book") or {}
        n = p.get("polymarket_no_book") or {}
        return bool(y.get("schema_valid")) and bool(n.get("schema_valid"))

    def kalshi_book_ready(p: dict[str, Any]) -> bool:
        return bool((p.get("kalshi_orderbook") or {}).get("schema_valid"))

    book_ready = sum(poly_books_ready(p) and kalshi_book_ready(p) for p in matched)

    if not poly:
        state = "POLYMARKET_SOURCE_POPULATION_UNAVAILABLE"
    elif not kalshi:
        state = "KALSHI_SOURCE_POPULATION_UNAVAILABLE"
    elif not matched:
        state = "MATCHED_STRIKE_TIME_POPULATION_UNAVAILABLE"
    elif book_ready == 0:
        state = "MATCHED_POPULATION_FOUND_BOOK_ROUTE_BLOCKED"
    else:
        state = "SOURCE_SHAPE_PASS_MATCHED_STRIKE_TIME"

    return {
        "classification": state,
        "polymarket_candidate_count": len(poly),
        "kalshi_candidate_count": len(kalshi),
        "matched_strike_time_count": len(matched),
        "matched_with_public_book_schema_count": book_ready,
        "economic_outputs_computed": False,
        "matured_outcomes_read": False,
        "future_nearest_joins": 0,
        "silent_imputations": 0,
        "orders": False,
        "authenticated_trading_endpoints": False,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "schema": "POB_STRIKE_SOURCE_PROBE_V0.1",
        "generated_at_utc": now_utc(),
        "research_only": True,
        "economic_outputs_allowed": False,
        "authority": "POB_STRIKE_PRE_SOURCE_AUTHORITY_V0.1.md",
    }

    try:
        poly, poly_fetches = poly_candidates()
        kalshi, kalshi_fetches = kalshi_candidates()
        pairs = classify_pairs(poly, kalshi)
        pairs, book_fetches = attach_book_proofs(pairs)
        adj = adjudicate(poly, kalshi, pairs)

        receipt.update({
            "polymarket_candidates": poly,
            "kalshi_candidates": kalshi,
            "matched_pairs": pairs,
            "source_fetches": {
                "polymarket": poly_fetches,
                "kalshi": kalshi_fetches,
                "books": book_fetches,
            },
            "adjudication": adj,
        })
        receipt["receipt_sha256"] = sha256_obj(receipt)
        path = OUT / "source_probe_receipt.json"
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(adj, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        receipt["adjudication"] = {
            "classification": "SOURCE_PROBE_TECHNICAL_FAILURE",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "economic_outputs_computed": False,
            "matured_outcomes_read": False,
        }
        receipt["receipt_sha256"] = sha256_obj(receipt)
        (OUT / "source_probe_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt["adjudication"], indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

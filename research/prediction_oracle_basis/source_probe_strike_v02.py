#!/usr/bin/env python3
"""POB explicit-strike source probe V0.2 — deterministic forward slug transport.

Source/data feasibility only. No matured outcomes, PnL, returns, win-rate,
profitability, trade simulation, or parameter optimization.
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

UA = "CryptoLab-POB-StrikeProbe/0.2 research-only"
OUT = Path("artifacts/prediction_oracle_basis/strike_v02")
POLY_EVENTS = "https://gamma-api.polymarket.com/events"
POLY_BOOK = "https://clob.polymarket.com/book"
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
NY = ZoneInfo("America/New_York")
WINDOW_DAYS = 7


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(x: dt.datetime) -> str:
    return x.astimezone(dt.timezone.utc).isoformat()


def canon(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_obj(obj: Any) -> str:
    return hashlib.sha256(canon(obj)).hexdigest()


def get_json(url: str, params: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any], bytes]:
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    start = iso(now_utc())
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        status = int(resp.status)
        ctype = resp.headers.get("content-type", "")
    end = iso(now_utc())
    obj = json.loads(raw.decode("utf-8"))
    return obj, {
        "url": url,
        "status": status,
        "content_type": ctype,
        "started_at_utc": start,
        "finished_at_utc": end,
        "raw_sha256": sha(raw),
        "bytes": len(raw),
    }, raw


def parse_jsonish(v: Any) -> Any:
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("[") or s.startswith("{"):
            try:
                return json.loads(s)
            except json.JSONDecodeError:
                return v
    return v


def text_blob(x: dict[str, Any]) -> str:
    keys = ["title", "question", "description", "rules_primary", "rules_secondary", "subtitle", "slug"]
    return "\n".join(str(x.get(k) or "") for k in keys)


def money(text: str) -> Decimal | None:
    m = re.search(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)", text or "")
    if not m:
        return None
    try:
        return Decimal(m.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def parse_iso(s: Any) -> dt.datetime | None:
    if not s:
        return None
    try:
        x = dt.datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        if x.tzinfo is None:
            x = x.replace(tzinfo=dt.timezone.utc)
        return x.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def slug_for(day: dt.date) -> str:
    return f"bitcoin-above-on-{day.strftime('%B').lower()}-{day.day}-{day.year}"


def future_poly_candidates(probe_now: dt.datetime) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    local_today = probe_now.astimezone(NY).date()
    candidates: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []

    for offset in range(1, WINDOW_DAYS + 1):
        day = local_today + dt.timedelta(days=offset)
        slug = slug_for(day)
        try:
            payload, meta, _ = get_json(POLY_EVENTS, {"slug": slug})
            fetches.append(meta)
        except Exception as exc:
            fetches.append({
                "slug": slug,
                "fetch_error": type(exc).__name__ + ": " + str(exc),
            })
            continue

        events = payload if isinstance(payload, list) else payload.get("events", [])
        if not isinstance(events, list):
            continue

        resolution_local = dt.datetime.combine(day, dt.time(12, 0), tzinfo=NY)
        resolution_utc = resolution_local.astimezone(dt.timezone.utc)
        if resolution_utc <= probe_now:
            continue

        for event in events:
            if not isinstance(event, dict):
                continue
            for market in event.get("markets") or []:
                if not isinstance(market, dict):
                    continue
                combined = (text_blob(event) + "\n" + text_blob(market)).lower()
                rule_ok = (
                    "binance" in combined
                    and "btc/usdt" in combined
                    and ("1 minute candle" in combined or "1m" in combined)
                    and (("12:00" in combined and "et" in combined) or ("noon" in combined and "et" in combined))
                )
                strike = money(str(market.get("question") or "") + "\n" + str(market.get("title") or ""))
                if strike is None:
                    continue

                outcomes = parse_jsonish(market.get("outcomes"))
                token_ids = parse_jsonish(market.get("clobTokenIds"))
                token_map: dict[str, str] = {}
                if isinstance(outcomes, list) and isinstance(token_ids, list) and len(outcomes) == len(token_ids):
                    token_map = {str(o).upper(): str(t) for o, t in zip(outcomes, token_ids)}

                candidates.append({
                    "source_slug": slug,
                    "event_id": event.get("id"),
                    "event_slug": event.get("slug"),
                    "market_id": market.get("id"),
                    "market_slug": market.get("slug"),
                    "question": market.get("question"),
                    "condition_id": market.get("conditionId"),
                    "nominal_strike": str(strike),
                    "resolution_utc": iso(resolution_utc),
                    "rule_proven": rule_ok,
                    "rule_semantics": "STRICT_GT_NOMINAL_STRIKE" if rule_ok else "RULE_PROVENANCE_UNCONFIRMED",
                    "reference": "BINANCE_BTCUSDT_1M_CLOSE" if rule_ok else "REFERENCE_UNCONFIRMED",
                    "yes_token_id": token_map.get("YES"),
                    "no_token_id": token_map.get("NO"),
                    "rules_sha256": sha_obj({"event": text_blob(event), "market": text_blob(market)}),
                    "market_sha256": sha_obj(market),
                })

    return candidates, fetches


def kalshi_candidates() -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
    fetches: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    cursor = None

    series = None
    try:
        payload, meta, _ = get_json(f"{KALSHI_BASE}/series/KXBTCD")
        fetches.append(meta)
        series = payload.get("series", payload)
    except Exception as exc:
        fetches.append({"series_fetch_error": type(exc).__name__ + ": " + str(exc)})

    series_blob = text_blob(series) if isinstance(series, dict) else ""
    series_benchmark_proven = (
        "cf benchmarks" in series_blob.lower()
        or "brti" in series_blob.lower()
        or "real-time index" in series_blob.lower()
    )

    while True:
        params: dict[str, Any] = {"series_ticker": "KXBTCD", "status": "open", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        payload, meta, _ = get_json(f"{KALSHI_BASE}/markets", params)
        fetches.append(meta)
        markets = payload.get("markets", [])
        if not isinstance(markets, list):
            raise RuntimeError("Unexpected Kalshi markets schema")

        for m in markets:
            if not isinstance(m, dict):
                continue
            ticker = str(m.get("ticker") or "")
            close = parse_iso(m.get("close_time") or m.get("latest_expiration_time"))
            if not ticker or close is None:
                continue

            displayed = money(str(m.get("subtitle") or "") + "\n" + str(m.get("title") or ""))
            mt = re.search(r"-T([0-9]+(?:\.[0-9]+)?)$", ticker)
            encoded = None
            if mt:
                try:
                    encoded = Decimal(mt.group(1))
                except InvalidOperation:
                    encoded = None
            if displayed is None and encoded is not None:
                displayed = encoded + Decimal("0.01")
            if displayed is None:
                continue

            lower = text_blob(m).lower()
            benchmark_proven = series_benchmark_proven or ("cf benchmarks" in lower) or ("brti" in lower)
            tie_delta = displayed - encoded if encoded is not None else None

            quote_presence = {
                "yes_bid_dollars": m.get("yes_bid_dollars") is not None,
                "yes_ask_dollars": m.get("yes_ask_dollars") is not None,
                "yes_bid_size_fp": m.get("yes_bid_size_fp") is not None,
                "yes_ask_size_fp": m.get("yes_ask_size_fp") is not None,
            }

            rows.append({
                "ticker": ticker,
                "event_ticker": m.get("event_ticker"),
                "nominal_strike": str(displayed),
                "encoded_threshold": str(encoded) if encoded is not None else None,
                "tie_delta_usd": str(tie_delta) if tie_delta is not None else None,
                "resolution_utc": iso(close),
                "benchmark_proven": benchmark_proven,
                "reference": "CF_BENCHMARKS_BRTI" if benchmark_proven else "REFERENCE_PROVENANCE_UNCONFIRMED",
                "quote_field_presence": quote_presence,
                "market_sha256": sha_obj(m),
                "rules_sha256": sha_obj({"rules_primary": m.get("rules_primary"), "rules_secondary": m.get("rules_secondary"), "subtitle": m.get("subtitle")}),
            })

        cursor = payload.get("cursor")
        if not cursor:
            break

    return rows, fetches, series if isinstance(series, dict) else None


def book_shape(url: str, params: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    obj, meta, raw = get_json(url, params)
    payload = obj.get("orderbook", obj) if isinstance(obj, dict) else {}

    def arr(name: str) -> Any:
        return payload.get(name) if isinstance(payload, dict) else None

    def schema(levels: Any) -> list[str]:
        if not isinstance(levels, list) or not levels:
            return []
        first = levels[0]
        if isinstance(first, dict):
            return sorted(str(k) for k in first.keys())
        if isinstance(first, list):
            return [f"index_{i}" for i in range(len(first))]
        return [type(first).__name__]

    out = {
        "raw_sha256": sha(raw),
        "bids_count": len(arr("bids")) if isinstance(arr("bids"), list) else None,
        "asks_count": len(arr("asks")) if isinstance(arr("asks"), list) else None,
        "yes_count": len(arr("yes")) if isinstance(arr("yes"), list) else None,
        "no_count": len(arr("no")) if isinstance(arr("no"), list) else None,
        "bids_schema": schema(arr("bids")),
        "asks_schema": schema(arr("asks")),
        "yes_schema": schema(arr("yes")),
        "no_schema": schema(arr("no")),
    }
    return out, meta


def match_pairs(poly: list[dict[str, Any]], kalshi: list[dict[str, Any]]) -> list[dict[str, Any]]:
    pairs: list[dict[str, Any]] = []
    for p in poly:
        pt = parse_iso(p["resolution_utc"])
        ps = Decimal(p["nominal_strike"])
        if pt is None:
            continue
        for k in kalshi:
            kt = parse_iso(k["resolution_utc"])
            ks = Decimal(k["nominal_strike"])
            if kt != pt or ks != ps:
                continue

            if not p.get("rule_proven"):
                cls = "POLY_RULE_PROVENANCE_BLOCKED"
            elif not k.get("benchmark_proven"):
                cls = "KALSHI_REFERENCE_PROVENANCE_BLOCKED"
            elif k.get("tie_delta_usd") == "0.01":
                cls = "MATCHED_STRIKE_TIME_REFERENCE_DIFF_TIE_1C"
            else:
                cls = "NON_EQUIVALENT_OTHER"

            pairs.append({
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
                "polymarket_reference": p["reference"],
                "kalshi_reference": k["reference"],
            })
    return pairs


def add_book_proofs(pairs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    fetches: list[dict[str, Any]] = []
    out: list[dict[str, Any]] = []

    for base in pairs:
        row = dict(base)
        for side in ("yes", "no"):
            token = row.get(f"polymarket_{side}_token_id")
            if not token:
                row[f"polymarket_{side}_book"] = {"source_ready": False, "reason": "TOKEN_ID_MISSING"}
                continue
            try:
                shape, meta = book_shape(POLY_BOOK, {"token_id": token})
                fetches.append(meta)
                row[f"polymarket_{side}_book"] = {"source_ready": True, **shape}
            except Exception as exc:
                row[f"polymarket_{side}_book"] = {"source_ready": False, "error": type(exc).__name__ + ": " + str(exc)}

        try:
            ticker = urllib.parse.quote(str(row["kalshi_ticker"]))
            shape, meta = book_shape(f"{KALSHI_BASE}/markets/{ticker}/orderbook")
            fetches.append(meta)
            row["kalshi_book"] = {"source_ready": True, **shape}
        except Exception as exc:
            row["kalshi_book"] = {"source_ready": False, "error": type(exc).__name__ + ": " + str(exc)}

        out.append(row)

    return out, fetches


def adjudicate(poly: list[dict[str, Any]], kalshi: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [p for p in pairs if p["classification"] == "MATCHED_STRIKE_TIME_REFERENCE_DIFF_TIE_1C"]

    def ready(p: dict[str, Any]) -> bool:
        return bool(
            (p.get("polymarket_yes_book") or {}).get("source_ready")
            and (p.get("polymarket_no_book") or {}).get("source_ready")
            and (p.get("kalshi_book") or {}).get("source_ready")
        )

    book_ready = sum(ready(p) for p in matched)

    if not poly:
        state = "POLYMARKET_DIRECT_SLUG_POPULATION_UNAVAILABLE"
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
        "polymarket_future_candidate_count": len(poly),
        "kalshi_open_candidate_count": len(kalshi),
        "matched_strike_time_count": len(matched),
        "matched_with_public_book_routes_count": book_ready,
        "economic_outputs_computed": False,
        "matured_outcomes_read": False,
        "future_nearest_joins": 0,
        "silent_imputations": 0,
        "orders": False,
        "authenticated_trading_endpoints": False,
    }


def main() -> int:
    probe_now = now_utc()
    OUT.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "schema": "POB_STRIKE_SOURCE_PROBE_V0.2",
        "generated_at_utc": iso(probe_now),
        "research_only": True,
        "forward_calendar_days": WINDOW_DAYS,
        "transport_authority": "POB_STRIKE_SOURCE_TRANSPORT_REMEDIATION_V0.2.md",
    }

    try:
        poly, pf = future_poly_candidates(probe_now)
        kalshi, kf, series = kalshi_candidates()
        pairs = match_pairs(poly, kalshi)
        pairs, bf = add_book_proofs(pairs)
        adj = adjudicate(poly, kalshi, pairs)

        receipt.update({
            "polymarket_candidates": poly,
            "kalshi_candidates": kalshi,
            "kalshi_series": series,
            "matched_pairs": pairs,
            "source_fetches": {"polymarket": pf, "kalshi": kf, "books": bf},
            "adjudication": adj,
        })
        receipt["receipt_sha256"] = sha_obj(receipt)
        (OUT / "source_probe_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
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
        receipt["receipt_sha256"] = sha_obj(receipt)
        (OUT / "source_probe_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt["adjudication"], indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

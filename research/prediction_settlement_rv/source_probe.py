#!/usr/bin/env python3
"""POB-HOURLY-STRIKE-BINANCE-CFRTI-001 source-only probe.

Enumerates future Kalshi KXBTCD resolution instants, deterministically queries the
matching Polymarket hourly slug, and tests exact time + nominal strike source geometry.
No matured outcomes or economic outputs are computed.
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

UA = "CryptoLab-PSRV-SourceProbe/0.1 research-only"
OUT = Path("artifacts/prediction_settlement_rv/source_gate")
POLY_EVENTS = "https://gamma-api.polymarket.com/events"
POLY_BOOK = "https://clob.polymarket.com/book"
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
NY = ZoneInfo("America/New_York")
FORWARD_HOURS = 12


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(x: dt.datetime) -> str:
    return x.astimezone(dt.timezone.utc).isoformat()


def canon(x: Any) -> bytes:
    return json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_obj(x: Any) -> str:
    return sha(canon(x))


def get_json(url: str, params: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any], bytes]:
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    started = iso(utcnow())
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
        status = int(resp.status)
        ctype = resp.headers.get("content-type", "")
    finished = iso(utcnow())
    return json.loads(raw.decode("utf-8")), {
        "url": url,
        "status": status,
        "content_type": ctype,
        "started_at_utc": started,
        "finished_at_utc": finished,
        "raw_sha256": sha(raw),
        "bytes": len(raw),
    }, raw


def parse_iso(v: Any) -> dt.datetime | None:
    if not v:
        return None
    try:
        x = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        if x.tzinfo is None:
            x = x.replace(tzinfo=dt.timezone.utc)
        return x.astimezone(dt.timezone.utc)
    except ValueError:
        return None


def text_blob(x: dict[str, Any]) -> str:
    return "\n".join(str(x.get(k) or "") for k in (
        "title", "question", "description", "rules_primary", "rules_secondary", "subtitle", "slug"
    ))


def parse_jsonish(v: Any) -> Any:
    if isinstance(v, str) and v.strip().startswith(("[", "{")):
        try:
            return json.loads(v)
        except json.JSONDecodeError:
            return v
    return v


def money(text: str) -> Decimal | None:
    m = re.search(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)", text or "")
    if not m:
        return None
    try:
        return Decimal(m.group(1).replace(",", ""))
    except InvalidOperation:
        return None


def hourly_slug(t_utc: dt.datetime) -> str:
    local = t_utc.astimezone(NY)
    hour = local.hour
    suffix = "am" if hour < 12 else "pm"
    h12 = hour % 12 or 12
    month = local.strftime("%B").lower()
    return f"bitcoin-above-on-{month}-{local.day}-{local.year}-{h12}{suffix}-et"


def fetch_kalshi(probe_now: dt.datetime) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any] | None]:
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

    sblob = text_blob(series) if isinstance(series, dict) else ""
    series_ref = ("cf benchmarks" in sblob.lower()) or ("brti" in sblob.lower()) or ("real-time index" in sblob.lower())

    end = probe_now + dt.timedelta(hours=FORWARD_HOURS)

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
            close = parse_iso(m.get("close_time") or m.get("latest_expiration_time"))
            if close is None or not (probe_now < close <= end):
                continue

            ticker = str(m.get("ticker") or "")
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
            ref_ok = series_ref or ("cf benchmarks" in lower) or ("brti" in lower)
            tie_delta = displayed - encoded if encoded is not None else None

            rows.append({
                "ticker": ticker,
                "event_ticker": m.get("event_ticker"),
                "resolution_utc": iso(close),
                "nominal_strike": str(displayed),
                "encoded_threshold": str(encoded) if encoded is not None else None,
                "tie_delta_usd": str(tie_delta) if tie_delta is not None else None,
                "reference_proven": ref_ok,
                "reference": "CF_BENCHMARKS_BRTI" if ref_ok else "REFERENCE_PROVENANCE_UNCONFIRMED",
                "market_sha256": sha_obj(m),
                "rules_sha256": sha_obj({"primary": m.get("rules_primary"), "secondary": m.get("rules_secondary"), "subtitle": m.get("subtitle")}),
            })
        cursor = payload.get("cursor")
        if not cursor:
            break

    return rows, fetches, series if isinstance(series, dict) else None


def fetch_poly_for_times(times: list[dt.datetime], probe_now: dt.datetime) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []
    seen: set[str] = set()

    for t in sorted(set(times)):
        if t <= probe_now:
            continue
        slug = hourly_slug(t)
        try:
            payload, meta, _ = get_json(POLY_EVENTS, {"slug": slug})
            fetches.append(meta)
        except Exception as exc:
            fetches.append({"slug": slug, "fetch_error": type(exc).__name__ + ": " + str(exc)})
            continue

        events = payload if isinstance(payload, list) else payload.get("events", [])
        if not isinstance(events, list):
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
                    and ("1 hour candle" in combined or "1h" in combined)
                    and "close" in combined
                )
                strike = None
                raw_group = str(market.get("groupItemTitle") or "").strip().replace(",", "")
                if raw_group:
                    try:
                        strike = Decimal(raw_group)
                    except InvalidOperation:
                        strike = None
                if strike is None:
                    strike = money(str(market.get("question") or "") + "\n" + str(market.get("title") or ""))
                if strike is None:
                    # Last-resort source parser for questions that expose the integer
                    # strike without a currency symbol. This is parsing only, not selection.
                    mq = re.search(r"bitcoin\s+above\s+([0-9][0-9,]*(?:\.[0-9]+)?)", str(market.get("question") or ""), re.I)
                    if mq:
                        try:
                            strike = Decimal(mq.group(1).replace(",", ""))
                        except InvalidOperation:
                            strike = None
                if strike is None:
                    continue
                mid = str(market.get("id") or market.get("conditionId") or market.get("slug") or "")
                if not mid or mid in seen:
                    continue
                seen.add(mid)

                outcomes = parse_jsonish(market.get("outcomes"))
                tokens = parse_jsonish(market.get("clobTokenIds"))
                token_map: dict[str, str] = {}
                if isinstance(outcomes, list) and isinstance(tokens, list) and len(outcomes) == len(tokens):
                    token_map = {str(o).upper(): str(tok) for o, tok in zip(outcomes, tokens)}

                rows.append({
                    "source_slug": slug,
                    "event_id": event.get("id"),
                    "event_slug": event.get("slug"),
                    "market_id": market.get("id"),
                    "market_slug": market.get("slug"),
                    "condition_id": market.get("conditionId"),
                    "question": market.get("question"),
                    "resolution_utc": iso(t),
                    "nominal_strike": str(strike),
                    "rule_proven": rule_ok,
                    "reference": "BINANCE_BTCUSDT_1H_CLOSE" if rule_ok else "REFERENCE_PROVENANCE_UNCONFIRMED",
                    "yes_token_id": token_map.get("YES"),
                    "no_token_id": token_map.get("NO"),
                    "market_sha256": sha_obj(market),
                    "rules_sha256": sha_obj({"event": text_blob(event), "market": text_blob(market)}),
                })

    return rows, fetches


def match(poly: list[dict[str, Any]], kalshi: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in poly:
        pt = parse_iso(p["resolution_utc"])
        ps = Decimal(p["nominal_strike"])
        for k in kalshi:
            kt = parse_iso(k["resolution_utc"])
            ks = Decimal(k["nominal_strike"])
            if pt != kt or ps != ks:
                continue
            if not p.get("rule_proven"):
                cls = "POLY_RULE_PROVENANCE_BLOCKED"
            elif not k.get("reference_proven"):
                cls = "KALSHI_REFERENCE_PROVENANCE_BLOCKED"
            elif k.get("tie_delta_usd") == "0.01":
                cls = "MATCHED_SETTLEMENT_BASIS_PAIR"
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
                "tie_delta_usd": k["tie_delta_usd"],
                "polymarket_reference": p["reference"],
                "kalshi_reference": k["reference"],
            })
    return out


def book_shape(url: str, params: dict[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    obj, meta, raw = get_json(url, params)

    provider_shape = "UNKNOWN"
    payload: Any = obj
    if isinstance(obj, dict) and isinstance(obj.get("orderbook_fp"), dict):
        provider_shape = "KALSHI_ORDERBOOK_FP"
        payload = obj["orderbook_fp"]
    elif isinstance(obj, dict):
        provider_shape = "POLYMARKET_CLOB"

    def arr(k: str) -> Any:
        return payload.get(k) if isinstance(payload, dict) else None

    def schema(levels: Any) -> list[str]:
        if not isinstance(levels, list) or not levels:
            return []
        first = levels[0]
        if isinstance(first, dict):
            return sorted(str(k) for k in first.keys())
        if isinstance(first, list):
            return [f"index_{i}" for i in range(len(first))]
        return [type(first).__name__]

    if provider_shape == "KALSHI_ORDERBOOK_FP":
        yes = arr("yes_dollars")
        no = arr("no_dollars")
        schema_valid = isinstance(yes, list) and isinstance(no, list)
        return {
            "provider_shape": provider_shape,
            "schema_valid": schema_valid,
            "raw_sha256": sha(raw),
            "yes_dollars_count": len(yes) if isinstance(yes, list) else None,
            "no_dollars_count": len(no) if isinstance(no, list) else None,
            "yes_dollars_schema": schema(yes),
            "no_dollars_schema": schema(no),
            "has_any_levels": bool((isinstance(yes, list) and yes) or (isinstance(no, list) and no)),
        }, meta

    bids = arr("bids")
    asks = arr("asks")
    schema_valid = isinstance(bids, list) and isinstance(asks, list)
    return {
        "provider_shape": provider_shape,
        "schema_valid": schema_valid,
        "raw_sha256": sha(raw),
        "bids_count": len(bids) if isinstance(bids, list) else None,
        "asks_count": len(asks) if isinstance(asks, list) else None,
        "bids_schema": schema(bids),
        "asks_schema": schema(asks),
        "has_any_levels": bool((isinstance(bids, list) and bids) or (isinstance(asks, list) and asks)),
    }, meta


def add_books(pairs: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    fetches: list[dict[str, Any]] = []

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
                row[f"polymarket_{side}_book"] = {"source_ready": bool(shape.get("schema_valid")), **shape}
            except Exception as exc:
                row[f"polymarket_{side}_book"] = {"source_ready": False, "error": type(exc).__name__ + ": " + str(exc)}

        try:
            ticker = urllib.parse.quote(str(row["kalshi_ticker"]))
            shape, meta = book_shape(f"{KALSHI_BASE}/markets/{ticker}/orderbook")
            fetches.append(meta)
            row["kalshi_book"] = {"source_ready": bool(shape.get("schema_valid")), **shape}
        except Exception as exc:
            row["kalshi_book"] = {"source_ready": False, "error": type(exc).__name__ + ": " + str(exc)}

        rows.append(row)

    return rows, fetches


def adjudicate(poly: list[dict[str, Any]], kalshi: list[dict[str, Any]], pairs: list[dict[str, Any]]) -> dict[str, Any]:
    matched = [p for p in pairs if p["classification"] == "MATCHED_SETTLEMENT_BASIS_PAIR"]

    def ready(p: dict[str, Any]) -> bool:
        return bool(
            (p.get("polymarket_yes_book") or {}).get("source_ready")
            and (p.get("polymarket_no_book") or {}).get("source_ready")
            and (p.get("kalshi_book") or {}).get("source_ready")
        )

    ready_count = sum(ready(p) for p in matched)

    if not kalshi:
        state = "NO_FUTURE_KALSHI_KXBTCD_IN_WINDOW"
    elif not poly:
        state = "POLYMARKET_HOURLY_SOURCE_POPULATION_UNAVAILABLE"
    elif not matched:
        state = "MATCHED_HOURLY_STRIKE_TIME_POPULATION_UNAVAILABLE"
    elif ready_count == 0:
        state = "MATCHED_HOURLY_POPULATION_FOUND_BOOK_ROUTE_BLOCKED"
    else:
        state = "SOURCE_ROUTE_PAIR_PASS"

    return {
        "classification": state,
        "forward_window_hours": FORWARD_HOURS,
        "kalshi_future_candidate_count": len(kalshi),
        "kalshi_future_unique_resolution_times": len({k["resolution_utc"] for k in kalshi}),
        "polymarket_hourly_candidate_count": len(poly),
        "matched_hourly_strike_time_count": len(matched),
        "matched_with_public_book_routes_count": ready_count,
        "economic_outputs_computed": False,
        "matured_outcomes_read": False,
        "future_nearest_joins": 0,
        "silent_imputations": 0,
        "orders": False,
        "authenticated_trading_endpoints": False,
        "source_data_pass": False,
        "fees_proven": False,
        "usdtusd_basis_proven": False,
        "synchronized_capture_gate_completed": False,
    }


def main() -> int:
    probe_now = utcnow()
    OUT.mkdir(parents=True, exist_ok=True)
    receipt: dict[str, Any] = {
        "schema": "PSRV_SOURCE_PROBE_V0.1",
        "generated_at_utc": iso(probe_now),
        "research_only": True,
        "authority": "PRE_SOURCE_AUTHORITY_V0.1.md",
    }

    try:
        kalshi, kfetch, series = fetch_kalshi(probe_now)
        times = [parse_iso(k["resolution_utc"]) for k in kalshi]
        times = [t for t in times if t is not None]
        poly, pfetch = fetch_poly_for_times(times, probe_now)
        pairs = match(poly, kalshi)
        pairs, bfetch = add_books(pairs)
        adj = adjudicate(poly, kalshi, pairs)

        receipt.update({
            "kalshi_candidates": kalshi,
            "polymarket_candidates": poly,
            "kalshi_series": series,
            "matched_pairs": pairs,
            "source_fetches": {"kalshi": kfetch, "polymarket": pfetch, "books": bfetch},
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

#!/usr/bin/env python3
"""POB-HOURLY-SYNC-CAPTURE-001 prospective source-transport capture.

Source-only. Captures three deterministically selected matched hourly strike pairs
for ten synchronized bundles. No matured outcomes or economic outputs are computed.
"""

from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

UA = "CryptoLab-POB-HourlySync/0.1 research-only"
OUT = Path("artifacts/prediction_oracle_basis/hourly_sync")
POLY_EVENTS = "https://gamma-api.polymarket.com/events"
POLY_BOOK = "https://clob.polymarket.com/book"
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
BINANCE_BOOK = "https://data-api.binance.vision/api/v3/ticker/bookTicker"
BRTI_ROUTE = "https://www.cfbenchmarks.com/api/v1/values?id=BRTI"
NY = ZoneInfo("America/New_York")
FORWARD_HOURS = 12
SNAPSHOT_COUNT = 10
INTERVAL_SECONDS = 15
MAX_BUNDLE_SPAN_MS = 3000


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(x: dt.datetime) -> str:
    return x.astimezone(dt.timezone.utc).isoformat()


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha_obj(x: Any) -> str:
    return sha(json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())


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
    suffix = "am" if local.hour < 12 else "pm"
    h12 = local.hour % 12 or 12
    return f"bitcoin-above-on-{local.strftime('%B').lower()}-{local.day}-{local.year}-{h12}{suffix}-et"


def request_bytes(url: str, params: dict[str, Any] | None = None, timeout: int = 20) -> dict[str, Any]:
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    started = now_utc()
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json,text/plain,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            status = int(resp.status)
            ctype = resp.headers.get("content-type", "")
        finished = now_utc()
        parsed: Any = None
        if raw:
            try:
                parsed = json.loads(raw.decode("utf-8"))
            except Exception:
                parsed = None
        return {
            "ok": 200 <= status < 300,
            "url": url,
            "status": status,
            "content_type": ctype,
            "started_at_utc": iso(started),
            "finished_at_utc": iso(finished),
            "elapsed_ms": int((finished - started).total_seconds() * 1000),
            "bytes": len(raw),
            "raw_sha256": sha(raw),
            "payload": parsed,
        }
    except urllib.error.HTTPError as exc:
        raw = exc.read() if exc.fp else b""
        finished = now_utc()
        return {
            "ok": False,
            "url": url,
            "status": int(exc.code),
            "content_type": exc.headers.get("content-type", "") if exc.headers else "",
            "started_at_utc": iso(started),
            "finished_at_utc": iso(finished),
            "elapsed_ms": int((finished - started).total_seconds() * 1000),
            "bytes": len(raw),
            "raw_sha256": sha(raw),
            "payload": None,
            "error": "HTTPError",
        }
    except Exception as exc:
        finished = now_utc()
        return {
            "ok": False,
            "url": url,
            "status": None,
            "started_at_utc": iso(started),
            "finished_at_utc": iso(finished),
            "elapsed_ms": int((finished - started).total_seconds() * 1000),
            "bytes": 0,
            "raw_sha256": None,
            "payload": None,
            "error": type(exc).__name__ + ": " + str(exc),
        }


def get_json(url: str, params: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any]]:
    r = request_bytes(url, params)
    if not r["ok"] or r["payload"] is None:
        raise RuntimeError(f"source request failed status={r.get('status')} url={r.get('url')}")
    return r["payload"], {k: v for k, v in r.items() if k != "payload"}


def fetch_kalshi(probe_now: dt.datetime) -> list[dict[str, Any]]:
    series_payload, _ = get_json(f"{KALSHI_BASE}/series/KXBTCD")
    series = series_payload.get("series", series_payload) if isinstance(series_payload, dict) else {}
    sblob = text_blob(series) if isinstance(series, dict) else ""
    series_ref = ("cf benchmarks" in sblob.lower()) or ("brti" in sblob.lower()) or ("real-time index" in sblob.lower())

    rows: list[dict[str, Any]] = []
    cursor = None
    end = probe_now + dt.timedelta(hours=FORWARD_HOURS)
    while True:
        params: dict[str, Any] = {"series_ticker": "KXBTCD", "status": "open", "limit": 1000}
        if cursor:
            params["cursor"] = cursor
        payload, _ = get_json(f"{KALSHI_BASE}/markets", params)
        markets = payload.get("markets", []) if isinstance(payload, dict) else []
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
                "resolution_utc": iso(close),
                "nominal_strike": str(displayed),
                "encoded_threshold": str(encoded) if encoded is not None else None,
                "tie_delta_usd": str(tie_delta) if tie_delta is not None else None,
                "reference_proven": bool(ref_ok),
                "market_sha256": sha_obj(m),
            })
        cursor = payload.get("cursor") if isinstance(payload, dict) else None
        if not cursor:
            break
    return rows


def fetch_poly_for_times(times: list[dt.datetime], probe_now: dt.datetime) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for t in sorted(set(times)):
        if t <= probe_now:
            continue
        slug = hourly_slug(t)
        payload, _ = get_json(POLY_EVENTS, {"slug": slug})
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
                    "market_id": market.get("id"),
                    "condition_id": market.get("conditionId"),
                    "resolution_utc": iso(t),
                    "nominal_strike": str(strike),
                    "rule_proven": bool(rule_ok),
                    "yes_token_id": token_map.get("YES"),
                    "no_token_id": token_map.get("NO"),
                    "rules_sha256": sha_obj({"event": text_blob(event), "market": text_blob(market)}),
                })
    return rows


def matched_pairs(probe_now: dt.datetime) -> list[dict[str, Any]]:
    kalshi = fetch_kalshi(probe_now)
    times = [parse_iso(k["resolution_utc"]) for k in kalshi]
    poly = fetch_poly_for_times([t for t in times if t is not None], probe_now)
    pairs: list[dict[str, Any]] = []
    for p in poly:
        pt = parse_iso(p["resolution_utc"])
        ps = Decimal(p["nominal_strike"])
        for k in kalshi:
            kt = parse_iso(k["resolution_utc"])
            ks = Decimal(k["nominal_strike"])
            if pt != kt or ps != ks:
                continue
            if not (p.get("rule_proven") and k.get("reference_proven") and k.get("tie_delta_usd") == "0.01"):
                continue
            if not p.get("yes_token_id") or not p.get("no_token_id"):
                continue
            pairs.append({
                "resolution_utc": p["resolution_utc"],
                "nominal_strike": p["nominal_strike"],
                "polymarket_market_id": p["market_id"],
                "polymarket_condition_id": p["condition_id"],
                "polymarket_yes_token_id": p["yes_token_id"],
                "polymarket_no_token_id": p["no_token_id"],
                "polymarket_rules_sha256": p["rules_sha256"],
                "kalshi_ticker": k["ticker"],
                "kalshi_encoded_threshold": k["encoded_threshold"],
                "tie_delta_usd": k["tie_delta_usd"],
            })
    pairs.sort(key=lambda x: (x["resolution_utc"], Decimal(x["nominal_strike"])))
    return pairs


def choose_three(pairs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not pairs:
        return []
    first_time = pairs[0]["resolution_utc"]
    same = [p for p in pairs if p["resolution_utc"] == first_time]
    dedup: dict[str, dict[str, Any]] = {p["nominal_strike"]: p for p in same}
    ordered = [dedup[k] for k in sorted(dedup, key=Decimal)]
    if len(ordered) <= 3:
        return ordered
    idx = [0, (len(ordered) - 1) // 2, len(ordered) - 1]
    return [ordered[i] for i in idx]


def capture_bundle(bundle_no: int, selected: list[dict[str, Any]]) -> dict[str, Any]:
    started = now_utc()
    tasks: dict[str, tuple[str, dict[str, Any] | None]] = {
        "binance_btcusdt_bookticker": (BINANCE_BOOK, {"symbol": "BTCUSDT"}),
    }
    for i, p in enumerate(selected):
        tasks[f"pair_{i}_poly_yes"] = (POLY_BOOK, {"token_id": p["polymarket_yes_token_id"]})
        tasks[f"pair_{i}_poly_no"] = (POLY_BOOK, {"token_id": p["polymarket_no_token_id"]})
        ticker = urllib.parse.quote(str(p["kalshi_ticker"]))
        tasks[f"pair_{i}_kalshi"] = (f"{KALSHI_BASE}/markets/{ticker}/orderbook", None)

    results: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=len(tasks)) as ex:
        futs = {ex.submit(request_bytes, url, params): name for name, (url, params) in tasks.items()}
        for fut in cf.as_completed(futs):
            name = futs[fut]
            try:
                results[name] = fut.result()
            except Exception as exc:
                results[name] = {"ok": False, "error": type(exc).__name__ + ": " + str(exc)}

    finished = now_utc()
    complete = all(bool(v.get("ok")) for v in results.values())
    return {
        "bundle_no": bundle_no,
        "bundle_started_at_utc": iso(started),
        "bundle_finished_at_utc": iso(finished),
        "bundle_span_ms": int((finished - started).total_seconds() * 1000),
        "complete": complete,
        "sources": results,
    }


def brti_diagnostic() -> dict[str, Any]:
    r = request_bytes(BRTI_ROUTE, None)
    payload = r.get("payload")
    machine = bool(r.get("ok") and isinstance(payload, dict) and isinstance(payload.get("payload"), list))
    if machine:
        state = "BRTI_MACHINE_FEED_PUBLIC_PASS"
    elif r.get("status") in (401, 403):
        state = "BRTI_MACHINE_FEED_AUTH_REQUIRED"
    else:
        state = "BRTI_MACHINE_FEED_TECHNICAL_FAILURE"
    return {
        "classification": state,
        "request": {k: v for k, v in r.items() if k != "payload"},
        "machine_readable_payload_returned": machine,
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    generated = now_utc()
    pairs = matched_pairs(generated)
    selected = choose_three(pairs)

    receipt: dict[str, Any] = {
        "schema": "POB_HOURLY_SYNC_CAPTURE_V0.1",
        "generated_at_utc": iso(generated),
        "authority": "POB_HOURLY_SYNC_CAPTURE_AUTHORITY_V0.1.md",
        "research_only": True,
        "selection": {
            "all_matched_pair_count": len(pairs),
            "selected_pair_count": len(selected),
            "selected_pairs": selected,
            "selection_rule": "earliest future resolution; minimum/median_floor/maximum nominal strike",
        },
        "schedule": {
            "snapshot_count": SNAPSHOT_COUNT,
            "interval_seconds": INTERVAL_SECONDS,
            "max_bundle_span_ms": MAX_BUNDLE_SPAN_MS,
        },
        "bundles": [],
        "brti_route": None,
        "adjudication": {},
    }

    if len(selected) < 3:
        receipt["brti_route"] = brti_diagnostic()
        receipt["adjudication"] = {
            "classification": "SOURCE_TRANSPORT_BLOCKED",
            "reason": "SAMPLE_SHAPE_INSUFFICIENT_FOR_3_STRIKE_GATE",
            "sync_capture_pass": False,
            "economic_outputs_computed": False,
            "matured_outcomes_read": False,
            "future_nearest_joins": 0,
            "silent_imputations": 0,
            "orders": False,
            "authenticated_trading_endpoints": False,
        }
        receipt["receipt_sha256"] = sha_obj(receipt)
        (OUT / "capture_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True))
        return 2

    for i in range(SNAPSHOT_COUNT):
        target = time.monotonic()
        bundle = capture_bundle(i + 1, selected)
        receipt["bundles"].append(bundle)
        if i < SNAPSHOT_COUNT - 1:
            target += INTERVAL_SECONDS
            delay = target - time.monotonic()
            if delay > 0:
                time.sleep(delay)

    brti = brti_diagnostic()
    receipt["brti_route"] = brti

    complete = sum(1 for b in receipt["bundles"] if b["complete"])
    max_span = max((int(b["bundle_span_ms"]) for b in receipt["bundles"]), default=10**9)
    sync_pass = (
        len(selected) >= 3
        and complete == SNAPSHOT_COUNT
        and max_span <= MAX_BUNDLE_SPAN_MS
    )

    if sync_pass and brti["classification"] == "BRTI_MACHINE_FEED_PUBLIC_PASS":
        state = "SOURCE_TRANSPORT_READY"
    elif sync_pass and brti["classification"] == "BRTI_MACHINE_FEED_AUTH_REQUIRED":
        state = "SOURCE_TRANSPORT_READY_BRTI_AUTH_BLOCKED"
    elif sync_pass:
        state = "SOURCE_TRANSPORT_READY_BRTI_ROUTE_UNRESOLVED"
    else:
        state = "SOURCE_TRANSPORT_BLOCKED"

    receipt["adjudication"] = {
        "classification": state,
        "sync_capture_pass": sync_pass,
        "complete_bundles": complete,
        "required_bundles": SNAPSHOT_COUNT,
        "max_bundle_span_ms_observed": max_span,
        "max_bundle_span_ms_allowed": MAX_BUNDLE_SPAN_MS,
        "brti_classification": brti["classification"],
        "economic_outputs_computed": False,
        "matured_outcomes_read": False,
        "future_nearest_joins": 0,
        "silent_imputations": 0,
        "orders": False,
        "authenticated_trading_endpoints": False,
    }
    receipt["receipt_sha256"] = sha_obj(receipt)
    (OUT / "capture_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

    print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True))
    return 0 if sync_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""CBLL Source Recovery V0.3 — source/provenance-only probe.

Hard firewall:
- Coinbase BTC-USDT / ETH-USDT only.
- Requests only two frozen 2022-2023 historical windows.
- No candle construction, returns, lead-lag, correlation, direction, PnL or outcomes.
- No Authorization header and no secrets.
- Raw trade price/size values are never written to the receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://api.coinbase.com/api/v3/brokerage/market/products/{product_id}/ticker"
PRODUCTS = ("BTC-USDT", "ETH-USDT")
LIMIT = 1000
ALLOWED_START = "2022-01-01T00:00:00Z"
ALLOWED_END = "2023-12-31T23:59:59Z"
WINDOWS = (
    ("EARLY_2022", "2022-01-01T00:00:00Z", "2022-01-01T00:05:00Z"),
    ("LATE_2023", "2023-12-31T23:54:59Z", "2023-12-31T23:59:59Z"),
)
REQUIRED_FIELDS = {"trade_id", "product_id", "price", "size", "time"}
USER_AGENT = "CryptoLab-CBLL-SourceProbe/0.3 (+source-only; no-auth)"


def epoch(iso: str) -> float:
    text = iso.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    return datetime.fromisoformat(text).timestamp()


def iso_from_epoch(value: float) -> str:
    return datetime.fromtimestamp(value, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(product: str, start_iso: str, end_iso: str) -> dict:
    start = int(epoch(start_iso))
    end = int(epoch(end_iso))
    params = urllib.parse.urlencode({"limit": LIMIT, "start": str(start), "end": str(end)})
    url = BASE.format(product_id=urllib.parse.quote(product, safe="-")) + "?" + params
    req = urllib.request.Request(
        url,
        method="GET",
        headers={
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )

    started = time.monotonic()
    status = None
    headers = {}
    body = b""
    error_kind = None

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            status = int(resp.status)
            headers = {k.lower(): v for k, v in resp.headers.items()}
            body = resp.read()
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        headers = {k.lower(): v for k, v in exc.headers.items()} if exc.headers else {}
        body = exc.read() if hasattr(exc, "read") else b""
        error_kind = "HTTP_ERROR"
    except Exception as exc:  # transport/DNS/TLS fail closed
        error_kind = type(exc).__name__

    elapsed_ms = round((time.monotonic() - started) * 1000, 3)
    receipt = {
        "request": {
            "host": "api.coinbase.com",
            "path_template": "/api/v3/brokerage/market/products/{product_id}/ticker",
            "product_id": product,
            "start": start_iso,
            "end": end_iso,
            "limit": LIMIT,
            "authorization_header_sent": False,
        },
        "http_status": status,
        "elapsed_ms": elapsed_ms,
        "response_sha256": sha256_bytes(body),
        "content_type": headers.get("content-type"),
        "error_kind": error_kind,
        "trade_count": 0,
        "schema_fields": [],
        "schema_missing_count": 0,
        "product_mismatch_count": 0,
        "duplicate_trade_id_count": 0,
        "out_of_requested_window_count": 0,
        "outside_frozen_period_count": 0,
        "invalid_timestamp_count": 0,
        "min_timestamp": None,
        "max_timestamp": None,
        "limit_saturated": False,
    }

    if status != 200:
        return receipt

    try:
        obj = json.loads(body.decode("utf-8"))
    except Exception:
        receipt["error_kind"] = "INVALID_JSON"
        return receipt

    trades = obj.get("trades")
    if not isinstance(trades, list):
        receipt["error_kind"] = "TRADES_NOT_LIST"
        return receipt

    receipt["trade_count"] = len(trades)
    receipt["limit_saturated"] = len(trades) >= LIMIT

    all_fields = set()
    seen_ids = set()
    timestamps = []
    start_e = epoch(start_iso)
    end_e = epoch(end_iso)
    allowed_start_e = epoch(ALLOWED_START)
    allowed_end_e = epoch(ALLOWED_END)

    for trade in trades:
        if not isinstance(trade, dict):
            receipt["schema_missing_count"] += 1
            continue

        all_fields.update(str(k) for k in trade.keys())
        if not REQUIRED_FIELDS.issubset(trade.keys()):
            receipt["schema_missing_count"] += 1

        if trade.get("product_id") != product:
            receipt["product_mismatch_count"] += 1

        trade_id = str(trade.get("trade_id", ""))
        if trade_id:
            if trade_id in seen_ids:
                receipt["duplicate_trade_id_count"] += 1
            seen_ids.add(trade_id)

        try:
            ts = epoch(str(trade.get("time")))
            timestamps.append(ts)
            if ts < start_e or ts > end_e:
                receipt["out_of_requested_window_count"] += 1
            if ts < allowed_start_e or ts > allowed_end_e:
                receipt["outside_frozen_period_count"] += 1
        except Exception:
            receipt["invalid_timestamp_count"] += 1

    receipt["schema_fields"] = sorted(all_fields)
    if timestamps:
        receipt["min_timestamp"] = iso_from_epoch(min(timestamps))
        receipt["max_timestamp"] = iso_from_epoch(max(timestamps))
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        default="SOURCE_RECOVERY_PROBE_V0.3_RECEIPT.json",
        help="Receipt path; source-only metadata, never raw trade values.",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve()
    authority_path = here.with_name("SOURCE_RECOVERY_AUTHORITY_V0.3.json")
    if not authority_path.exists():
        raise SystemExit("FAIL_CLOSED: missing frozen SOURCE_RECOVERY_AUTHORITY_V0.3.json")

    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    if authority.get("authority_id") != "CBLL-SOURCE-RECOVERY-V0.3":
        raise SystemExit("FAIL_CLOSED: wrong authority_id")
    if authority.get("hard_firewalls", {}).get("year_2025_access") is not False:
        raise SystemExit("FAIL_CLOSED: 2025 firewall not closed")
    if authority.get("hard_firewalls", {}).get("year_2026_access") is not False:
        raise SystemExit("FAIL_CLOSED: 2026 firewall not closed")
    if authority.get("hard_firewalls", {}).get("paid_purchase_authorized") is not False:
        raise SystemExit("FAIL_CLOSED: paid purchase unexpectedly authorized")

    requests_receipts = []
    for product in PRODUCTS:
        for window_id, start_iso, end_iso in WINDOWS:
            item = fetch(product, start_iso, end_iso)
            item["window_id"] = window_id
            requests_receipts.append(item)

    status_codes = [r["http_status"] for r in requests_receipts]
    all_200 = all(code == 200 for code in status_codes)
    auth_block = any(code in (401, 403) for code in status_codes)
    transport_or_http_failure = any(code != 200 for code in status_codes)
    provenance_failure = any(
        r["schema_missing_count"] > 0
        or r["product_mismatch_count"] > 0
        or r["duplicate_trade_id_count"] > 0
        or r["out_of_requested_window_count"] > 0
        or r["outside_frozen_period_count"] > 0
        or r["invalid_timestamp_count"] > 0
        for r in requests_receipts
        if r["http_status"] == 200
    )
    historical_nonempty_by_product = {
        p: any(r["trade_count"] > 0 for r in requests_receipts if r["request"]["product_id"] == p and r["http_status"] == 200)
        for p in PRODUCTS
    }
    historical_depth_proven = all(historical_nonempty_by_product.values())
    saturation_seen = any(r["limit_saturated"] for r in requests_receipts)

    if auth_block or transport_or_http_failure:
        classification = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
    elif provenance_failure:
        classification = "PROVENANCE_FAILURE"
    elif not historical_depth_proven:
        classification = "SOURCE_DATA_INSUFFICIENT"
    else:
        classification = "SOURCE_RECOVERY_ROUTE_FEASIBLE"

    receipt = {
        "lab_id": "COINBASE-BINANCE-LEADLAG-001",
        "authority_id": "CBLL-SOURCE-RECOVERY-V0.3",
        "probe_id": "CBLL-ADVANCED-PUBLIC-TRADES-PROBE-V0.3",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "scope": "SOURCE_PROVENANCE_ONLY",
        "parent_scientific_classification_preserved": "DATA_FAILURE",
        "source_data_pass": False,
        "classification": classification,
        "route": "Coinbase Advanced Trade Public Market Trades",
        "authentication_mode": "NONE",
        "all_requests_http_200": all_200,
        "auth_block_observed": auth_block,
        "historical_nonempty_by_product": historical_nonempty_by_product,
        "historical_depth_proven_on_frozen_samples": historical_depth_proven,
        "limit_saturation_seen": saturation_seen,
        "full_2022_2023_coverage_tested": False,
        "full_99_5pct_gate_tested": False,
        "economic_outcomes_opened": False,
        "year_2024_outcomes_opened": False,
        "year_2025_access": False,
        "year_2026_access": False,
        "raw_trade_values_persisted": False,
        "script_sha256": sha256_bytes(here.read_bytes()),
        "authority_sha256": sha256_bytes(authority_path.read_bytes()),
        "requests": requests_receipts,
        "next_gate": (
            "Freeze and execute bounded adaptive time-splitting/full-acquisition source runner for 2022-2023 only; "
            "reconstruct 5m candles only under frozen V0.3 semantics; compare synchronized coverage to unchanged 99.5% gates."
            if classification == "SOURCE_RECOVERY_ROUTE_FEASIBLE"
            else "Do not open outcomes. Preserve DATA_FAILURE and continue source recovery/fallback audit."
        ),
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "classification": classification,
        "all_requests_http_200": all_200,
        "historical_depth_proven_on_frozen_samples": historical_depth_proven,
        "limit_saturation_seen": saturation_seen,
        "source_data_pass": False,
        "economic_outcomes_opened": False,
        "year_2025_access": False,
        "year_2026_access": False,
        "receipt": str(out),
    }, sort_keys=True))

    return 0 if classification == "SOURCE_RECOVERY_ROUTE_FEASIBLE" else 2


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Public, read-only Deribit BTC options forward BBO collector.

Scientific boundary:
- source capture only;
- no returns, PnL, expectancy, signals or trading;
- no API key/authentication;
- append-only JSONL output.

The capture envelope is frozen in FORWARD_BBO_COLLECTOR_AUTHORITY_V0.1.json.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE_URL = "https://www.deribit.com/api/v2"
DTE_MIN = 20.0
DTE_MAX = 45.0
MAX_STRIKE_DISTANCE_FRAC = 0.25
DEPTH = 1


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def api_get(method: str, params: dict) -> dict:
    url = f"{BASE_URL}/{method}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "CryptoLab-SourceOnly-BBO-Collector/0.1"},
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if "error" in payload:
        raise RuntimeError(f"Deribit public API error: {payload['error']}")
    if "result" not in payload:
        raise RuntimeError("Deribit response missing result")
    return payload["result"]


def first_level(book: dict, side: str) -> tuple[float | None, float | None]:
    rows = book.get(side) or []
    if not rows:
        return None, None
    row = rows[0]
    if not isinstance(row, list) or len(row) < 2:
        return None, None
    return float(row[0]), float(row[1])


def select_instruments(instruments: list[dict], index_price: float, now_ms: int) -> list[dict]:
    out = []
    for inst in instruments:
        if inst.get("kind") != "option" or not inst.get("is_active", True):
            continue
        expiry_ms = inst.get("expiration_timestamp")
        strike = inst.get("strike")
        if expiry_ms is None or strike is None:
            continue
        dte = (float(expiry_ms) - now_ms) / 86_400_000.0
        if not (DTE_MIN <= dte <= DTE_MAX):
            continue
        strike = float(strike)
        if index_price <= 0:
            continue
        distance = abs(strike - index_price) / index_price
        if distance > MAX_STRIKE_DISTANCE_FRAC:
            continue
        out.append({
            "instrument_name": inst["instrument_name"],
            "expiration_timestamp": int(expiry_ms),
            "strike": strike,
            "option_type": inst.get("option_type"),
            "dte_days": dte,
            "strike_distance_fraction": distance,
        })
    out.sort(key=lambda x: (x["expiration_timestamp"], x["strike"], x["option_type"] or "", x["instrument_name"]))
    return out


def normalize_book(inst: dict, book: dict, snapshot_time: str, snapshot_hour: str) -> dict:
    bid_price, bid_amount = first_level(book, "bids")
    ask_price, ask_amount = first_level(book, "asks")
    return {
        "snapshot_time_utc": snapshot_time,
        "snapshot_hour_utc": snapshot_hour,
        "instrument_name": inst["instrument_name"],
        "expiration_timestamp": inst["expiration_timestamp"],
        "strike": inst["strike"],
        "option_type": inst["option_type"],
        "dte_days": inst["dte_days"],
        "strike_distance_fraction": inst["strike_distance_fraction"],
        "bid_price": bid_price,
        "bid_amount": bid_amount,
        "ask_price": ask_price,
        "ask_amount": ask_amount,
        "mark_price": book.get("mark_price"),
        "mark_iv": book.get("mark_iv"),
        "index_price": book.get("index_price"),
        "underlying_price": book.get("underlying_price"),
        "open_interest": book.get("open_interest"),
        "greeks": book.get("greeks"),
        "source_timestamp_ms": book.get("timestamp"),
        "source": "deribit_public_get_order_book",
        "source_only": True,
    }


def capture() -> dict:
    now = utc_now()
    now_ms = int(now.timestamp() * 1000)
    snapshot_time = now.isoformat()
    snapshot_hour = now.replace(minute=0, second=0, microsecond=0).isoformat()

    index = api_get("public/get_index_price", {"index_name": "btc_usd"})
    index_price = float(index["index_price"])
    instruments = api_get(
        "public/get_instruments",
        {"currency": "BTC", "kind": "option", "expired": "false"},
    )
    selected = select_instruments(instruments, index_price=index_price, now_ms=now_ms)

    rows = []
    failures = []
    for inst in selected:
        try:
            book = api_get(
                "public/get_order_book",
                {"instrument_name": inst["instrument_name"], "depth": DEPTH},
            )
            rows.append(normalize_book(inst, book, snapshot_time, snapshot_hour))
        except Exception as exc:
            failures.append({"instrument_name": inst["instrument_name"], "error": str(exc)})
        finally:
            # Conservative public-IP pacing. Deribit documents public access as
            # per-IP limited and recommends subscriptions for sustained traffic.
            # This source collector is intentionally low-rate and hourly-scale.
            time.sleep(0.12)

    perp = None
    try:
        pbook = api_get("public/get_order_book", {"instrument_name": "BTC-PERPETUAL", "depth": DEPTH})
        pbid, pbid_amt = first_level(pbook, "bids")
        pask, pask_amt = first_level(pbook, "asks")
        perp = {
            "instrument_name": "BTC-PERPETUAL",
            "bid_price": pbid,
            "bid_amount": pbid_amt,
            "ask_price": pask,
            "ask_amount": pask_amt,
            "mark_price": pbook.get("mark_price"),
            "index_price": pbook.get("index_price"),
            "source_timestamp_ms": pbook.get("timestamp"),
        }
    except Exception as exc:
        failures.append({"instrument_name": "BTC-PERPETUAL", "error": str(exc)})

    return {
        "schema_version": "OVRP_FORWARD_BBO_V0.1",
        "snapshot_time_utc": snapshot_time,
        "snapshot_hour_utc": snapshot_hour,
        "index_price_btc_usd": index_price,
        "capture_envelope": {
            "dte_min_days": DTE_MIN,
            "dte_max_days": DTE_MAX,
            "max_abs_strike_distance_from_index_fraction": MAX_STRIKE_DISTANCE_FRAC,
            "order_book_depth": DEPTH,
        },
        "selected_instrument_count": len(selected),
        "captured_instrument_count": len(rows),
        "failure_count": len(failures),
        "options": rows,
        "btc_perpetual": perp,
        "failures": failures,
        "safety": {
            "authenticated": False,
            "orders": False,
            "wallets": False,
            "returns_computed": False,
            "pnl_computed": False,
        },
    }


def append_jsonl(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    key = payload["snapshot_hour_utc"]
    # Fail closed on duplicate hour: an external scheduler may retry, but the
    # collector must not silently create duplicate scientific observations.
    if path.exists():
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                try:
                    existing = json.loads(line)
                except json.JSONDecodeError:
                    raise RuntimeError("Existing JSONL is malformed; refusing append")
                if existing.get("snapshot_hour_utc") == key:
                    raise RuntimeError(f"Duplicate snapshot hour already present: {key}")
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="data/vrp_forward/deribit_btc_options_bbo.jsonl")
    parser.add_argument("--stdout-only", action="store_true")
    args = parser.parse_args()

    payload = capture()
    if args.stdout_only:
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    append_jsonl(Path(args.output), payload)
    print(json.dumps({
        "status": "SOURCE_CAPTURED",
        "output": args.output,
        "snapshot_hour_utc": payload["snapshot_hour_utc"],
        "captured_instrument_count": payload["captured_instrument_count"],
        "failure_count": payload["failure_count"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

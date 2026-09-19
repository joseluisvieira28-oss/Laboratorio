#!/usr/bin/env python3
"""Outcome-blind Tardis liquidation source feasibility probe V0.2.

This script proves only historical source/schema feasibility for Binance USDT
Futures liquidation events. It does not load market-price outcomes and does not
compute returns, continuation/reversal labels, PnL, hit rate, Sharpe,
expectancy, drawdown or any strategy-performance metric.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
AUTH_PATH = ROOT / "TARDIS_SOURCE_PROBE_AUTHORITY_V0.2.json"
OUT = Path("artifacts/liquidation_pressure_tardis_source_probe_v02")
OUT.mkdir(parents=True, exist_ok=True)

VALID_SIDES = {"buy", "sell", "unknown", ""}


class RouteInsufficient(RuntimeError):
    pass


class AcquisitionFailure(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_sha(obj: object) -> str:
    raw = json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(raw)


def fetch_sample(auth: dict, sample_date: str) -> dict:
    url = f"{auth['source']['base_url']}/{sample_date}/PERPETUALS.csv.gz"
    try:
        r = requests.get(url, timeout=(20, 120))
    except requests.RequestException as exc:
        raise AcquisitionFailure(f"{sample_date}: request failed: {exc}") from exc
    if r.status_code != 200:
        raise AcquisitionFailure(f"{sample_date}: HTTP {r.status_code}")
    payload = r.content
    if not payload:
        raise RouteInsufficient(f"{sample_date}: empty payload")

    try:
        raw = gzip.decompress(payload).decode("utf-8")
    except Exception as exc:
        raise RouteInsufficient(f"{sample_date}: invalid gzip/csv payload: {exc}") from exc

    reader = csv.DictReader(io.StringIO(raw))
    fieldnames = reader.fieldnames or []
    missing = [c for c in auth["required_columns"] if c not in fieldnames]
    if missing:
        raise RouteInsufficient(f"{sample_date}: missing required columns {missing}")

    total_rows = 0
    btc_rows = 0
    bad_required = 0
    bad_side = 0
    first_ts = None
    last_ts = None
    symbols = set()

    for row in reader:
        total_rows += 1
        symbol = (row.get("symbol") or "").upper()
        if symbol:
            symbols.add(symbol)
        if symbol != auth["target_symbol"]:
            continue
        btc_rows += 1
        ts = (row.get("timestamp") or "").strip()
        price = (row.get("price") or "").strip()
        amount = (row.get("amount") or "").strip()
        side = (row.get("side") or "").strip().lower()
        if not ts or not price or not amount:
            bad_required += 1
        if side not in VALID_SIDES:
            bad_side += 1
        if ts:
            try:
                tsi = int(ts)
                first_ts = tsi if first_ts is None else min(first_ts, tsi)
                last_ts = tsi if last_ts is None else max(last_ts, tsi)
            except ValueError:
                bad_required += 1

    if total_rows == 0:
        raise RouteInsufficient(f"{sample_date}: zero liquidation rows")
    if btc_rows == 0:
        raise RouteInsufficient(f"{sample_date}: BTCUSDT absent")
    if bad_required:
        raise RouteInsufficient(f"{sample_date}: {bad_required} BTCUSDT rows have invalid required fields")
    if bad_side:
        raise RouteInsufficient(f"{sample_date}: {bad_side} BTCUSDT rows have invalid side values")

    return {
        "date": sample_date,
        "url": url,
        "http_status": r.status_code,
        "compressed_bytes": len(payload),
        "compressed_sha256": sha256_bytes(payload),
        "total_liquidation_rows": total_rows,
        "btc_liquidation_rows": btc_rows,
        "distinct_symbols": len(symbols),
        "first_btc_timestamp_us": first_ts,
        "last_btc_timestamp_us": last_ts,
        "schema": fieldnames,
        "target_symbol": auth["target_symbol"],
        "outcomes_opened": False,
    }


def main() -> int:
    auth = json.loads(AUTH_PATH.read_text())
    receipt = {
        "lab_id": auth["lab_id"],
        "probe_id": auth["probe_id"],
        "authority_sha256": sha256_bytes(AUTH_PATH.read_bytes()),
        "classification": None,
        "dates": [],
        "failure": None,
        "safety": auth["safety"],
    }

    try:
        assert auth["status"] == "FROZEN_SOURCE_ONLY_OUTCOME_BLIND"
        assert all(int(d[:4]) < 2025 for d in auth["sample_dates"])
        assert all(v is False for k, v in auth["safety"].items() if k.endswith("_authorized"))
        for sample_date in auth["sample_dates"]:
            receipt["dates"].append(fetch_sample(auth, sample_date))
        receipt["classification"] = "HISTORICAL_LIQUIDATION_SOURCE_ROUTE_FEASIBLE"
    except RouteInsufficient as exc:
        receipt["classification"] = "SOURCE_ROUTE_SCHEMA_INSUFFICIENT"
        receipt["failure"] = f"{type(exc).__name__}: {exc}"
    except AcquisitionFailure as exc:
        receipt["classification"] = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {exc}"
    except Exception as exc:
        receipt["classification"] = "PROVENANCE_FAILURE"
        receipt["failure"] = f"{type(exc).__name__}: {exc}"

    receipt["receipt_sha256"] = stable_sha({k: v for k, v in receipt.items() if k != "receipt_sha256"})
    path = OUT / "LIQUIDATION_PRESSURE_001_TARDIS_SOURCE_PROBE_RECEIPT_V0_2.json"
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    print(json.dumps({
        "classification": receipt["classification"],
        "dates_completed": len(receipt["dates"]),
        "date_summaries": [
            {
                "date": d["date"],
                "rows": d["total_liquidation_rows"],
                "btc_rows": d["btc_liquidation_rows"],
                "symbols": d["distinct_symbols"],
            }
            for d in receipt["dates"]
        ],
        "failure": receipt["failure"],
        "receipt_sha256": receipt["receipt_sha256"],
        "safety": receipt["safety"],
    }, sort_keys=True))

    return 0 if receipt["classification"] in {
        "HISTORICAL_LIQUIDATION_SOURCE_ROUTE_FEASIBLE",
        "SOURCE_ROUTE_SCHEMA_INSUFFICIENT",
    } else 2


if __name__ == "__main__":
    raise SystemExit(main())

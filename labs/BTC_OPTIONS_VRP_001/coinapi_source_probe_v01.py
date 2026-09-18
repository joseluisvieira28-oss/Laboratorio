#!/usr/bin/env python3
"""BTC-OPTIONS-VRP-001 CoinAPI historical BBO source probe V0.1.

SOURCE-ONLY / OUTCOME-BLIND / FAIL-CLOSED.

This probe:
- resolves eight prospectively frozen expired Deribit option contracts;
- requests at most one historical quote row per contract in a frozen 08:00-12:00 UTC window;
- records only schema/presence metadata and cryptographic hashes;
- never emits bid/ask prices, returns, PnL, expectancy, or strategy performance.

Credential:
  COINAPI_KEY environment variable only. Never commit or print it.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://rest.coinapi.io"
AUTH_PATH = pathlib.Path("labs/BTC_OPTIONS_VRP_001/COINAPI_SOURCE_PROBE_AUTHORITY_V0.1.json")
OUT = pathlib.Path("artifacts/btc_options_vrp_coinapi_source_probe_v01")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def get_json(path: str, key: str):
    req = urllib.request.Request(
        BASE + path,
        headers={
            "X-CoinAPI-Key": key,
            "Accept": "application/json",
            "User-Agent": "SRC-Crypto-Lab/1.0",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            raw = resp.read()
            code = int(resp.status)
    except urllib.error.HTTPError as e:
        body = e.read()
        return {"_http_error": int(e.code), "_body_sha256": sha256_bytes(body)}, int(e.code), body
    obj = json.loads(raw.decode("utf-8"))
    return obj, code, raw


def iso_window(date_text: str):
    d = datetime.strptime(date_text, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start = d.replace(hour=8).isoformat().replace("+00:00", "Z")
    end = d.replace(hour=12).isoformat().replace("+00:00", "Z")
    return start, end


def load_historical_symbols(key: str, wanted: set[str]):
    found = {}
    receipts = []
    page = 1
    while wanted - set(found):
        path = f"/v1/symbols/DERIBIT/history?page={page}&limit=1000"
        obj, code, raw = get_json(path, key)
        receipts.append({"page": page, "http": code, "sha256": sha256_bytes(raw)})
        if code in (401, 403):
            return found, receipts, "SOURCE_ACCESS_CREDENTIAL_REQUIRED"
        if code in (402, 429):
            return found, receipts, "SOURCE_ACCESS_PLAN_RESTRICTED"
        if code != 200:
            return found, receipts, "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
        if not isinstance(obj, list):
            return found, receipts, "PROVENANCE_FAILURE"
        for row in obj:
            ex = str(row.get("symbol_id_exchange") or "")
            if ex in wanted:
                found[ex] = {
                    "symbol_id": row.get("symbol_id"),
                    "symbol_type": row.get("symbol_type"),
                    "option_type_is_call_present": "option_type_is_call" in row,
                    "option_strike_price_present": "option_strike_price" in row,
                    "option_expiration_time_present": "option_expiration_time" in row,
                }
        if len(obj) < 1000:
            break
        page += 1
        if page > 100:
            return found, receipts, "PROVENANCE_FAILURE"
    return found, receipts, None


def main():
    auth = json.loads(AUTH_PATH.read_text(encoding="utf-8"))
    assert auth["status"] == "FROZEN_SOURCE_ONLY_CREDENTIAL_GATED_NO_PURCHASE"
    assert auth["safety"]["performance_outcomes_authorized"] is False
    assert auth["safety"]["purchase_authorized"] is False
    assert auth["safety"]["access_2025_authorized"] is False
    assert auth["safety"]["access_2026_authorized"] is False

    key = os.environ.get("COINAPI_KEY", "").strip()
    if not key:
        print(json.dumps({
            "classification": "SOURCE_ACCESS_CREDENTIAL_REQUIRED",
            "credential_env": "COINAPI_KEY",
            "api_key_printed": False,
            "outcomes_opened": False,
        }, indent=2))
        return 2

    samples = auth["cross_provider_fixed_samples"]
    wanted = {x[k] for x in samples for k in ("call", "put")}
    resolved, metadata_receipts, failure = load_historical_symbols(key, wanted)

    result = {
        "lab_id": auth["lab_id"],
        "probe_id": auth["probe_id"],
        "classification": None,
        "resolved_contracts": len(resolved),
        "expected_contracts": len(wanted),
        "metadata_receipts": metadata_receipts,
        "quote_checks": [],
        "prices_emitted": False,
        "returns_computed": False,
        "pnl_computed": False,
        "access_2025": False,
        "access_2026": False,
        "purchase_executed": False,
        "paid_overage_authorized": False,
    }

    if failure:
        result["classification"] = failure
    elif set(resolved) != wanted:
        result["classification"] = "SOURCE_ROUTE_SCHEMA_INSUFFICIENT"
        result["missing_contracts"] = sorted(wanted - set(resolved))
    else:
        schema_fail = False
        access_fail = None
        for sample in samples:
            start, end = iso_window(sample["date"])
            for side in ("call", "put"):
                ex_name = sample[side]
                symbol_id = resolved[ex_name]["symbol_id"]
                if not symbol_id:
                    schema_fail = True
                    continue
                sid = urllib.parse.quote(str(symbol_id), safe="")
                qs = urllib.parse.urlencode({
                    "time_start": start,
                    "time_end": end,
                    "limit": 1,
                })
                obj, code, raw = get_json(f"/v1/quotes/{sid}/history?{qs}", key)
                rec = {
                    "date": sample["date"],
                    "exchange_symbol": ex_name,
                    "http": code,
                    "response_sha256": sha256_bytes(raw),
                    "row_count_capped_at_one": 0,
                    "bid_price_field_present": False,
                    "ask_price_field_present": False,
                    "bid_size_field_present": False,
                    "ask_size_field_present": False,
                }
                if code in (401, 403):
                    access_fail = "SOURCE_ACCESS_CREDENTIAL_REQUIRED"
                elif code in (402, 429):
                    access_fail = "SOURCE_ACCESS_PLAN_RESTRICTED"
                elif code != 200:
                    access_fail = "SOURCE_ACQUISITION_TECHNICAL_FAILURE"
                elif not isinstance(obj, list):
                    access_fail = "PROVENANCE_FAILURE"
                elif obj:
                    row = obj[0]
                    rec["row_count_capped_at_one"] = 1
                    rec["bid_price_field_present"] = row.get("bid_price") is not None
                    rec["ask_price_field_present"] = row.get("ask_price") is not None
                    rec["bid_size_field_present"] = row.get("bid_size") is not None
                    rec["ask_size_field_present"] = row.get("ask_size") is not None
                    if not all([
                        rec["bid_price_field_present"],
                        rec["ask_price_field_present"],
                        rec["bid_size_field_present"],
                        rec["ask_size_field_present"],
                    ]):
                        schema_fail = True
                else:
                    schema_fail = True
                result["quote_checks"].append(rec)
                if access_fail:
                    break
            if access_fail:
                break

        if access_fail:
            result["classification"] = access_fail
        elif schema_fail or len(result["quote_checks"]) != 8:
            result["classification"] = "SOURCE_ROUTE_SCHEMA_INSUFFICIENT"
        else:
            result["classification"] = "COINAPI_BBO_SOURCE_ROUTE_FEASIBLE"

    OUT.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    (OUT / "COINAPI_SOURCE_PROBE_RECEIPT_V0.1.json").write_text(payload, encoding="utf-8")
    print(payload)
    return 0 if result["classification"] == "COINAPI_BBO_SOURCE_ROUTE_FEASIBLE" else 2


if __name__ == "__main__":
    sys.exit(main())

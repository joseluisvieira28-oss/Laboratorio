#!/usr/bin/env python3
"""PSRV synchronized prospective source-capture smoke.

Raw public quote/depth bytes are stored in the artifact but economic values are
never printed or summarized. This script proves transport timing and schema only.
"""

from __future__ import annotations

import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import source_probe as sp  # noqa: E402

UA = "CryptoLab-PSRV-SyncSmoke/0.1 source-only"
OUT = Path("artifacts/prediction_settlement_rv/sync_smoke")
RAW = OUT / "sealed_raw"
POLY_BOOK = "https://clob.polymarket.com/book"
KALSHI_BASE = "https://api.elections.kalshi.com/trade-api/v2"
COINBASE_TICKER = "https://api.exchange.coinbase.com/products/USDT-USD/ticker"

MIN_LEAD_MIN = 5
MAX_LEAD_MIN = 120
MAX_MIDPOINT_SKEW_S = 2.0
MAX_REQUEST_ELAPSED_S = 5.0


def utcnow() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso(x: dt.datetime) -> str:
    return x.astimezone(dt.timezone.utc).isoformat()


def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", s)[:180]


def request_raw(name: str, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if params:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    started = utcnow()
    status = None
    ctype = ""
    raw = b""
    err = None
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
            status = int(resp.status)
            ctype = resp.headers.get("content-type", "")
    except Exception as exc:
        err = f"{type(exc).__name__}: {exc}"
    finished = utcnow()
    midpoint = started + (finished - started) / 2
    return {
        "name": name,
        "url": url,
        "status": status,
        "content_type": ctype,
        "started_at_utc": iso(started),
        "finished_at_utc": iso(finished),
        "midpoint_utc": iso(midpoint),
        "elapsed_seconds": (finished - started).total_seconds(),
        "raw": raw,
        "raw_sha256": hashlib.sha256(raw).hexdigest() if raw else None,
        "bytes": len(raw),
        "error": err,
    }


def schema_summary(leg: str, raw: bytes) -> dict[str, Any]:
    try:
        obj = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        return {"schema_valid": False, "error": f"{type(exc).__name__}: {exc}"}

    if leg in {"poly_yes", "poly_no"}:
        valid = isinstance(obj, dict) and isinstance(obj.get("bids"), list) and isinstance(obj.get("asks"), list)
        return {
            "schema_valid": bool(valid),
            "bids_count": len(obj.get("bids", [])) if isinstance(obj, dict) and isinstance(obj.get("bids"), list) else None,
            "asks_count": len(obj.get("asks", [])) if isinstance(obj, dict) and isinstance(obj.get("asks"), list) else None,
        }

    if leg == "kalshi":
        ob = obj.get("orderbook_fp") if isinstance(obj, dict) else None
        valid = isinstance(ob, dict) and isinstance(ob.get("yes_dollars"), list) and isinstance(ob.get("no_dollars"), list)
        return {
            "schema_valid": bool(valid),
            "yes_levels_count": len(ob.get("yes_dollars", [])) if isinstance(ob, dict) and isinstance(ob.get("yes_dollars"), list) else None,
            "no_levels_count": len(ob.get("no_dollars", [])) if isinstance(ob, dict) and isinstance(ob.get("no_dollars"), list) else None,
        }

    if leg == "coinbase":
        keys = set(obj.keys()) if isinstance(obj, dict) else set()
        required = {"bid", "ask", "time"}
        return {
            "schema_valid": required.issubset(keys),
            "required_fields_present": sorted(required.intersection(keys)),
        }

    return {"schema_valid": False, "error": "UNKNOWN_LEG"}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    run_start = utcnow()

    receipt: dict[str, Any] = {
        "schema": "PSRV_SYNC_CAPTURE_SMOKE_V0.1",
        "generated_at_utc": iso(run_start),
        "authority": "SYNC_CAPTURE_SMOKE_AUTHORITY_V0.1.md",
        "frozen_limits": {
            "min_lead_minutes": MIN_LEAD_MIN,
            "max_lead_minutes": MAX_LEAD_MIN,
            "max_midpoint_skew_seconds": MAX_MIDPOINT_SKEW_S,
            "max_request_elapsed_seconds": MAX_REQUEST_ELAPSED_S,
        },
        "economic_values_reported": False,
        "economic_outputs_computed": False,
        "matured_outcomes_read": False,
        "orders": False,
        "authenticated_trading_endpoints": False,
        "future_nearest_joins": 0,
        "silent_imputations": 0,
        "source_data_pass": False,
        "stale_detector_completed": False,
    }

    try:
        kalshi, _, _ = sp.fetch_kalshi(run_start)
        times = [sp.parse_iso(k["resolution_utc"]) for k in kalshi]
        times = [t for t in times if t is not None]
        poly, _ = sp.fetch_poly_for_times(times, run_start)
        pairs = sp.match(poly, kalshi)

        groups: dict[str, list[dict[str, Any]]] = {}
        for pair in pairs:
            t = sp.parse_iso(pair["resolution_utc"])
            if t is None:
                continue
            lead_min = (t - run_start).total_seconds() / 60.0
            if MIN_LEAD_MIN <= lead_min <= MAX_LEAD_MIN:
                groups.setdefault(pair["resolution_utc"], []).append(pair)

        if not groups:
            receipt["adjudication"] = {
                "classification": "WAITING_ELIGIBLE_EXPIRY",
                "matched_pair_count": len(pairs),
                "captured_pair_count": 0,
                "sync_smoke_pass": False,
            }
            (OUT / "sync_smoke_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
            print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True))
            return 0

        selected_resolution = min(groups.keys(), key=lambda x: sp.parse_iso(x))
        selected = sorted(groups[selected_resolution], key=lambda x: float(x["nominal_strike"]))
        receipt["selected_resolution_utc"] = selected_resolution
        receipt["selected_pair_count"] = len(selected)

        pair_receipts: list[dict[str, Any]] = []
        all_ok = True

        for idx, pair in enumerate(selected):
            pair_key = f"{idx:03d}_{safe_name(pair['nominal_strike'])}_{safe_name(pair['kalshi_ticker'])}"
            pair_dir = RAW / pair_key
            pair_dir.mkdir(parents=True, exist_ok=True)

            endpoints = {
                "poly_yes": (POLY_BOOK, {"token_id": pair["polymarket_yes_token_id"]}),
                "poly_no": (POLY_BOOK, {"token_id": pair["polymarket_no_token_id"]}),
                "kalshi": (f"{KALSHI_BASE}/markets/{urllib.parse.quote(str(pair['kalshi_ticker']))}/orderbook", None),
                "coinbase": (COINBASE_TICKER, None),
            }

            with cf.ThreadPoolExecutor(max_workers=4) as ex:
                futures = {
                    leg: ex.submit(request_raw, leg, url, params)
                    for leg, (url, params) in endpoints.items()
                }
                results = {leg: fut.result() for leg, fut in futures.items()}

            mids: list[dt.datetime] = []
            legs_summary: dict[str, Any] = {}
            pair_ok = True

            for leg, result in results.items():
                raw = result.pop("raw")
                raw_path = pair_dir / f"{leg}.json"
                raw_path.write_bytes(raw)
                ss = schema_summary(leg, raw)

                if result["status"] != 200 or result["error"] is not None:
                    pair_ok = False
                if result["elapsed_seconds"] > MAX_REQUEST_ELAPSED_S:
                    pair_ok = False
                if not ss.get("schema_valid"):
                    pair_ok = False

                if result["midpoint_utc"]:
                    mids.append(dt.datetime.fromisoformat(result["midpoint_utc"]))

                legs_summary[leg] = {
                    "status": result["status"],
                    "content_type": result["content_type"],
                    "started_at_utc": result["started_at_utc"],
                    "finished_at_utc": result["finished_at_utc"],
                    "midpoint_utc": result["midpoint_utc"],
                    "elapsed_seconds": result["elapsed_seconds"],
                    "raw_sha256": result["raw_sha256"],
                    "bytes": result["bytes"],
                    "error": result["error"],
                    "schema": ss,
                    "sealed_raw_path": str(raw_path),
                }

            skew = (max(mids) - min(mids)).total_seconds() if len(mids) == 4 else None
            if skew is None or skew > MAX_MIDPOINT_SKEW_S:
                pair_ok = False

            pair_receipts.append({
                "nominal_strike": pair["nominal_strike"],
                "resolution_utc": pair["resolution_utc"],
                "polymarket_market_id": pair["polymarket_market_id"],
                "kalshi_ticker": pair["kalshi_ticker"],
                "midpoint_skew_seconds": skew,
                "transport_pass": pair_ok,
                "legs": legs_summary,
            })
            all_ok = all_ok and pair_ok

        receipt["pairs"] = pair_receipts
        receipt["adjudication"] = {
            "classification": "SYNCHRONIZED_CAPTURE_SMOKE_PASS" if all_ok and pair_receipts else "SYNCHRONIZED_CAPTURE_SMOKE_FAIL",
            "captured_pair_count": len(pair_receipts),
            "all_pairs_transport_pass": all_ok,
            "max_observed_midpoint_skew_seconds": max(
                (p["midpoint_skew_seconds"] for p in pair_receipts if p["midpoint_skew_seconds"] is not None),
                default=None,
            ),
            "sync_smoke_pass": bool(all_ok and pair_receipts),
            "source_data_pass": False,
        }

        # Hash only the public receipt structure; sealed raw hashes are already included.
        receipt_for_hash = dict(receipt)
        receipt["receipt_sha256"] = hashlib.sha256(
            json.dumps(receipt_for_hash, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()

        (OUT / "sync_smoke_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")

        # Keep logs outcome-blind and quote-value-blind.
        print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True))
        print("QUOTE_VALUES_SEALED_IN_ARTIFACT_NOT_PRINTED")
        return 0

    except Exception as exc:
        receipt["adjudication"] = {
            "classification": "SYNC_CAPTURE_TECHNICAL_FAILURE",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "sync_smoke_pass": False,
            "source_data_pass": False,
        }
        (OUT / "sync_smoke_receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(receipt["adjudication"], indent=2, sort_keys=True), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

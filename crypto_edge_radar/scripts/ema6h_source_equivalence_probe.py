from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from radar.ema6h_source_resilience import OFFICIAL_BINANCE_SPOT_ENDPOINTS
from radar.strategies.ema6h_50x200_regime_forward import (
    BinanceSpotKlineFeed,
    FROZEN_UNIVERSE,
)

OUT = Path("artifacts/ema6h_source_equivalence_v01.json")


def ms(text: str) -> int:
    return int(
        datetime.fromisoformat(text.replace("Z", "+00:00"))
        .astimezone(timezone.utc)
        .timestamp()
        * 1000
    )


CASES = [
    *[
        {
            "symbol": symbol,
            "interval": "15m",
            "start_ms": ms("2026-09-25T00:00:00Z"),
            "end_ms": ms("2026-09-25T06:00:00Z"),
            "expected_rows": 24,
        }
        for symbol in FROZEN_UNIVERSE
    ],
    {
        "symbol": "BTCUSDT",
        "interval": "1d",
        "start_ms": ms("2026-09-01T00:00:00Z"),
        "end_ms": ms("2026-09-11T00:00:00Z"),
        "expected_rows": 10,
    },
]
NOW_MS = ms("2026-09-26T12:00:00Z")


def canonical_rows(rows):
    return [
        [
            row.open_time,
            row.open,
            row.high,
            row.low,
            row.close,
            row.volume,
            row.close_time,
        ]
        for row in rows
    ]


def digest(rows) -> str:
    raw = json.dumps(
        canonical_rows(rows),
        sort_keys=False,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def fetch_case(base_url: str, case: dict) -> dict:
    feed = BinanceSpotKlineFeed(
        timeout=15,
        max_attempts=1,
        retry_backoff_seconds=0,
    )
    feed.base_url = base_url
    rows = feed.klines(
        case["symbol"],
        case["interval"],
        start_ms=case["start_ms"],
        end_ms=case["end_ms"],
        now_ms=NOW_MS,
    )
    if len(rows) != case["expected_rows"]:
        raise AssertionError(
            f"{base_url} {case['symbol']} {case['interval']}: "
            f"expected {case['expected_rows']} rows, got {len(rows)}"
        )
    return {
        "row_count": len(rows),
        "sha256": digest(rows),
        "first_open_ms": rows[0].open_time if rows else None,
        "last_open_ms": rows[-1].open_time if rows else None,
    }


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    endpoint_results = {}
    for label, base_url in OFFICIAL_BINANCE_SPOT_ENDPOINTS:
        item = {
            "label": label,
            "base_url": base_url,
            "status": "UNKNOWN",
            "cases": {},
        }
        try:
            for case in CASES:
                key = f"{case['symbol']}:{case['interval']}"
                item["cases"][key] = fetch_case(base_url, case)
            item["status"] = "PASS_FETCH"
        except Exception as exc:
            item["status"] = "UNAVAILABLE"
            item["error"] = f"{type(exc).__name__}:{exc}"
        endpoint_results[label] = item

    baseline = endpoint_results["MARKET_DATA_ONLY"]
    if baseline["status"] != "PASS_FETCH":
        classification = "SOURCE_GATE_FAIL_PRIMARY_UNAVAILABLE"
        receipt = {
            "schema_version": "EMA6H_SOURCE_EQUIVALENCE_PROBE_V0.1",
            "classification": classification,
            "primary": "MARKET_DATA_ONLY",
            "endpoints": endpoint_results,
            "minimum_equivalent_endpoints": 2,
            "science_changed": False,
            "authenticated_exchange_api_used": False,
            "orders_created": False,
            "exchange_mutation_performed": False,
            "live_capital_enabled": False,
        }
        OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        print(json.dumps(receipt, sort_keys=True))
        return 2

    available = [
        row for row in endpoint_results.values()
        if row["status"] == "PASS_FETCH"
    ]
    mismatches = []
    baseline_cases = baseline["cases"]
    for row in available:
        for key, base_case in baseline_cases.items():
            candidate = row["cases"].get(key)
            if candidate is None or candidate["sha256"] != base_case["sha256"]:
                mismatches.append(
                    {
                        "endpoint": row["label"],
                        "case": key,
                        "baseline_sha256": base_case["sha256"],
                        "candidate_sha256": (
                            None if candidate is None else candidate["sha256"]
                        ),
                    }
                )

    equivalent_alternates = [
        row["label"]
        for row in available
        if row["label"] != "MARKET_DATA_ONLY"
        and all(
            row["cases"][key]["sha256"] == baseline_cases[key]["sha256"]
            for key in baseline_cases
        )
    ]

    passed = not mismatches and len(equivalent_alternates) >= 1
    receipt = {
        "schema_version": "EMA6H_SOURCE_EQUIVALENCE_PROBE_V0.1",
        "classification": (
            "PASS_OFFICIAL_ENDPOINT_CANDLE_EQUIVALENCE"
            if passed
            else "FAIL_CLOSED_ENDPOINT_EQUIVALENCE"
        ),
        "primary": "MARKET_DATA_ONLY",
        "available_endpoint_count": len(available),
        "equivalent_alternates": equivalent_alternates,
        "mismatches": mismatches,
        "cases": [
            {
                "symbol": case["symbol"],
                "interval": case["interval"],
                "expected_rows": case["expected_rows"],
                "start_ms": case["start_ms"],
                "end_ms": case["end_ms"],
            }
            for case in CASES
        ],
        "endpoints": endpoint_results,
        "science_changed": False,
        "authenticated_exchange_api_used": False,
        "orders_created": False,
        "exchange_mutation_performed": False,
        "live_capital_enabled": False,
    }
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, sort_keys=True))
    return 0 if passed else 3


if __name__ == "__main__":
    raise SystemExit(main())

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from radar.ema6h_source_resilience import (
    BinanceSpotWebSocketKlineFeed,
    OFFICIAL_BINANCE_SPOT_TRANSPORTS,
)
from radar.strategies.ema6h_50x200_regime_forward import (
    BinanceSpotKlineFeed,
    FROZEN_UNIVERSE,
)

OUT = Path("artifacts/ema6h_source_equivalence_v02.json")


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


def feed_for(kind: str, url: str):
    if kind == "REST":
        feed = BinanceSpotKlineFeed(
            timeout=15,
            max_attempts=1,
            retry_backoff_seconds=0,
        )
        feed.base_url = url
        return feed
    if kind == "WEBSOCKET_API":
        feed = BinanceSpotWebSocketKlineFeed(timeout=15)
        feed.endpoint_url = url
        return feed
    raise ValueError(f"unsupported transport kind {kind}")


def fetch_case(kind: str, url: str, case: dict) -> dict:
    feed = feed_for(kind, url)
    rows = feed.klines(
        case["symbol"],
        case["interval"],
        start_ms=case["start_ms"],
        end_ms=case["end_ms"],
        now_ms=NOW_MS,
    )
    if len(rows) != case["expected_rows"]:
        raise AssertionError(
            f"{kind} {url} {case['symbol']} {case['interval']}: "
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
    transport_results = {}

    for label, kind, url in OFFICIAL_BINANCE_SPOT_TRANSPORTS:
        item = {
            "label": label,
            "kind": kind,
            "url": url,
            "status": "UNKNOWN",
            "cases": {},
        }
        try:
            for case in CASES:
                key = f"{case['symbol']}:{case['interval']}"
                item["cases"][key] = fetch_case(kind, url, case)
            item["status"] = "PASS_FETCH"
        except Exception as exc:
            item["status"] = "UNAVAILABLE"
            item["error"] = f"{type(exc).__name__}:{exc}"
        transport_results[label] = item

    baseline = transport_results["MARKET_DATA_ONLY"]
    websocket = transport_results["WS_API"]

    if baseline["status"] != "PASS_FETCH":
        classification = "SOURCE_GATE_FAIL_PRIMARY_MARKET_DATA_UNAVAILABLE"
        passed = False
        mismatches = []
    else:
        baseline_cases = baseline["cases"]
        mismatches = []
        for row in transport_results.values():
            if row["status"] != "PASS_FETCH":
                continue
            for key, base_case in baseline_cases.items():
                candidate = row["cases"].get(key)
                if candidate is None or candidate["sha256"] != base_case["sha256"]:
                    mismatches.append(
                        {
                            "transport": row["label"],
                            "kind": row["kind"],
                            "case": key,
                            "baseline_sha256": base_case["sha256"],
                            "candidate_sha256": (
                                None if candidate is None else candidate["sha256"]
                            ),
                        }
                    )

        ws_equivalent = bool(
            websocket["status"] == "PASS_FETCH"
            and all(
                websocket["cases"].get(key, {}).get("sha256")
                == baseline_cases[key]["sha256"]
                for key in baseline_cases
            )
        )
        passed = not mismatches and ws_equivalent
        if passed:
            classification = "PASS_REST_WSAPI_CANDLE_EQUIVALENCE"
        elif websocket["status"] != "PASS_FETCH":
            classification = "SOURCE_GATE_FAIL_WSAPI_UNAVAILABLE"
        else:
            classification = "FAIL_CLOSED_TRANSPORT_CANDLE_DIVERGENCE"

    available = [
        row["label"]
        for row in transport_results.values()
        if row["status"] == "PASS_FETCH"
    ]
    unavailable = [
        {
            "transport": row["label"],
            "kind": row["kind"],
            "error": row.get("error"),
        }
        for row in transport_results.values()
        if row["status"] != "PASS_FETCH"
    ]

    receipt = {
        "schema_version": "EMA6H_SOURCE_EQUIVALENCE_PROBE_V0.2",
        "classification": classification,
        "pass": passed,
        "primary": "MARKET_DATA_ONLY",
        "required_fallback": "WS_API",
        "available_transports": available,
        "unavailable_transports": unavailable,
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
        "transports": transport_results,
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
